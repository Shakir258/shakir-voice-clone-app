"""
Text -> speech-in-your-voice generation with multi-engine Hindi support,
deterministic caching, and Devanagari-aware chunking.

Architecture:
1. Deterministic cache check (sha256 of text, voice_id, speed, pitch, format).
   If cached, returns immediately without re-running models.
2. If voice is a studio preset (including 100 Hindi voices):
   - Computes prosody (pitch and rate).
   - Chunks text at natural Hindi / English sentence boundaries.
   - Synthesizes each chunk with high-fidelity neural audio.
   - Concatenates chunks and stores in cache.
3. If voice is a custom cloned voice:
   - Uses OpenVoice ToneColorConverter + target embedding (se.pth).
   - Generates base speech (Hindi neural base if Devanagari, MeloTTS if English).
   - Converts timbre to custom user voice.
   - Concatenates chunks and stores in cache.
"""
from __future__ import annotations

import asyncio
import gc
import logging
import re
import shutil
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.audio_service import concat_wavs, convert_audio_file, get_duration_seconds
from app.services.cache_service import get_cached_audio, store_cached_audio
from app.services.hindi_chunker import has_hindi_script, split_hindi_text
from app.services.model_service import model_service
from app.services.voice_profile_service import get_embedding_path, get_preset_voice

logger = logging.getLogger(__name__)


class TextTooLongError(ValueError):
    pass


def split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split text at sentence boundaries, never mid-word, keeping each
    chunk under max_chars. Backwards-compatible alias to split_hindi_text."""
    return split_hindi_text(text, max_chars)


async def _run_edge_tts_async(voice: str, text: str, rate_str: str, pitch_str: str, out_file: Path) -> None:
    import edge_tts

    kwargs: dict[str, Any] = {"rate": rate_str}
    if pitch_str and pitch_str != "+0Hz" and pitch_str != "+0%":
        kwargs["pitch"] = pitch_str

    comm = edge_tts.Communicate(text, voice, **kwargs)
    await comm.save(str(out_file))


def _synthesize_edge_tts(voice: str, text: str, speed: float, pitch_offset: float, out_wav_path: Path) -> float:
    temp_dir = settings.TEMP_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)
    tmp_mp3 = temp_dir / f"edge_{out_wav_path.stem}.mp3"

    rate_pct = int(round((speed - 1.0) * 100))
    rate_str = f"{rate_pct:+d}%"

    pitch_val = int(round(pitch_offset))
    pitch_str = f"{pitch_val:+d}Hz" if pitch_val != 0 else "+0Hz"

    try:
        asyncio.run(_run_edge_tts_async(voice, text, rate_str, pitch_str, tmp_mp3))
        duration = convert_audio_file(tmp_mp3, out_wav_path)
        return duration
    finally:
        tmp_mp3.unlink(missing_ok=True)


def _synthesize_fish_tts(text: str, out_wav_path: Path, voice_id: str | None = None) -> float:
    """Call Fish Audio API and convert the returned audio to WAV.
    Returns duration in seconds.
    """
    from app.services import fish_tts as _fish_tts

    temp_dir = settings.TEMP_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)
    tmp_mp3 = temp_dir / f"fish_{out_wav_path.stem}.mp3"

    try:
        mp3_bytes = asyncio.run(_fish_tts.generate_speech(text, voice_key=voice_id))
        tmp_mp3.write_bytes(mp3_bytes)
        duration = convert_audio_file(tmp_mp3, out_wav_path)
        return duration
    finally:
        tmp_mp3.unlink(missing_ok=True)

def generate_speech(
    voice_id: str,
    text: str,
    speed: float = 1.0,
    out_path: Path | None = None,
    pitch: float = 0.0,
    format: str = "wav",
) -> tuple[float, int]:
    """Generate speech for `text` in the given voice profile, writing the
    final audio to `out_path`. Returns (duration_seconds, chunk_count).

    Leverages deterministic caching to avoid duplicate inference.
    """
    text = text.strip()
    if not text:
        raise ValueError("Text must not be empty.")
    if len(text) > settings.MAX_TOTAL_CHARS:
        raise TextTooLongError(
            f"Text is {len(text)} characters, which exceeds the "
            f"{settings.MAX_TOTAL_CHARS}-character limit for a single "
            "generation. Please shorten it or split it into multiple generations."
        )

    if out_path is None:
        from app.utils.ids import new_id

        out_path = settings.GENERATED_DIR / f"{new_id('gen')}.wav"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Deterministic Cache Lookup
    cached_path = get_cached_audio(text, voice_id, speed, pitch, format)
    if cached_path is not None and cached_path.exists():
        shutil.copyfile(cached_path, out_path)
        try:
            dur = get_duration_seconds(out_path)
        except Exception:
            dur = 1.0
        return dur, 1

    # 2. Preset / Studio voices (including all 100 Hindi voices)
    preset = get_preset_voice(voice_id)
    if preset:
        # Calculate combined speed and pitch from preset definition and user overrides
        # Rate can be float (1.05) or string ("+0%") — parse safely
        _raw_rate = preset.get("rate", 1.0)
        try:
            _rate_str = str(_raw_rate).strip()
            if "%" in _rate_str:
                preset_rate = 1.0  # percentage strings are not supported as rate multipliers
            else:
                preset_rate = float(_rate_str)
        except (ValueError, TypeError):
            preset_rate = 1.0
        effective_speed = speed * preset_rate

        # Parse preset pitch offset if defined (e.g. "+3%", "-5%")
        preset_pitch_str = str(preset.get("pitch", "+0%")).strip()
        preset_pitch_offset = 0.0
        try:
            clean_p = preset_pitch_str.rstrip("%Hz")
            preset_pitch_offset = float(clean_p)
        except Exception:
            preset_pitch_offset = 0.0

        effective_pitch = pitch + preset_pitch_offset
        base_voice = preset.get("base_speaker") or preset.get("voice", "hi-IN-MadhurNeural")
        preset_engine = preset.get("engine", "edge")

        chunks = split_hindi_text(text, settings.MAX_CHARS_PER_CHUNK)
        temp_dir = settings.TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        chunk_paths: list[Path] = []
        req_id = out_path.stem

        try:
            for i, chunk in enumerate(chunks):
                chunk_file = temp_dir / f"chunk_{req_id}_{i}.wav"
                if preset_engine == "fish":
                    _synthesize_fish_tts(chunk, chunk_file, voice_id=base_voice)
                else:
                    _synthesize_edge_tts(base_voice, chunk, effective_speed, effective_pitch, chunk_file)
                chunk_paths.append(chunk_file)

            if len(chunk_paths) == 1:
                shutil.copyfile(chunk_paths[0], out_path)
            else:
                concat_wavs(chunk_paths, out_path)

            duration = get_duration_seconds(out_path)
            # Store result in cache
            store_cached_audio(out_path, text, voice_id, speed, pitch, format)
            return duration, len(chunks)
        finally:
            for cp in chunk_paths:
                cp.unlink(missing_ok=True)

    # 3. Custom Cloned Voice (OpenVoice V2 pipeline)
    model_service.require_ready()
    chunks = split_hindi_text(text, settings.MAX_CHARS_PER_CHUNK)

    import torch

    target_se = torch.load(get_embedding_path(voice_id), map_location=model_service.device, weights_only=True)

    temp_dir = settings.TEMP_DIR
    temp_dir.mkdir(parents=True, exist_ok=True)
    chunk_paths = []
    has_deva = has_hindi_script(text)
    req_id = out_path.stem

    try:
        for i, chunk in enumerate(chunks):
            base_wav = temp_dir / f"base_{req_id}_{i}.wav"
            converted_wav = temp_dir / f"conv_{req_id}_{i}.wav"

            if has_deva:
                # Use Hindi neural base audio for accurate Hindi pronunciation
                _synthesize_edge_tts("hi-IN-MadhurNeural", chunk, speed, pitch, base_wav)
            else:
                try:
                    model_service.base_speaker_tts.tts_to_file(
                        chunk,
                        model_service.base_speaker_tts.hps.data.spk2id[settings.MELO_SPEAKER],
                        str(base_wav),
                        speed=speed,
                    )
                except Exception as melo_err:
                    logger.warning("MeloTTS failed (%s), falling back to neural base audio", melo_err)
                    _synthesize_edge_tts("en-IN-PrabhatNeural", chunk, speed, pitch, base_wav)

            model_service.tone_color_converter.convert(
                audio_src_path=str(base_wav),
                src_se=model_service.default_source_se,
                tgt_se=target_se,
                output_path=str(converted_wav),
                message="@MyShell",
            )
            chunk_paths.append(converted_wav)

        if len(chunk_paths) == 1:
            shutil.copyfile(chunk_paths[0], out_path)
        else:
            concat_wavs(chunk_paths, out_path)

        duration = get_duration_seconds(out_path)
        # Store result in cache
        store_cached_audio(out_path, text, voice_id, speed, pitch, format)
        return duration, len(chunks)
    finally:
        for p in chunk_paths:
            p.unlink(missing_ok=True)
        for i in range(len(chunks)):
            (temp_dir / f"base_{req_id}_{i}.wav").unlink(missing_ok=True)
        gc.collect()
