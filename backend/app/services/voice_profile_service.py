"""
Voice profile lifecycle.

WHAT A "VOICE PROFILE" ACTUALLY IS HERE (see also README "Voice profile"
and CONFIGURATION.md):

  1. What is extracted from your recording?
     A "tone color embedding" (OpenVoice calls this an "SE") - a small
     tensor produced by `ToneColorConverter.extract_se()` that captures
     the timbre of your voice, not the words you said.

  2. What is stored, where?
     Per profile, under backend/data/voices/<voice_id>/:
       - reference.wav   the cleaned-up recording you provided
       - se.pth          the extracted tone color embedding (PyTorch tensor)
       - metadata.json   id, name, created_at, duration, ready flag

  3. How is it loaded later?
     `torch.load(se.pth)` - fast, no re-processing of the original
     recording needed.

  4. Does it survive an application restart?
     Yes - it's a plain file on disk, loaded fresh from `se.pth` each
     time you generate, independent of any server process state.

  5. What happens if the profile file (se.pth) is deleted?
     Generation for that profile stops working ("ready" becomes false
     the next time it's checked). If reference.wav is still present,
     you can recreate se.pth by re-running extraction on it (see
     `recompute_embedding` below) with no need to re-record.

  6. Can I back up a profile?
     Yes - copy the whole `<voice_id>/` folder. See README "Backup/restore".

  7. Does generation need the original reference.wav every time?
     No. Only se.pth is needed at generation time. reference.wav is kept
     only so you can re-derive se.pth later (model upgrades, accidental
     deletion) without re-recording.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.services.audio_service import convert_to_reference_wav, AudioValidationError
from app.services.model_service import model_service
from app.utils.files import assert_safe_id
from app.utils.ids import new_id


class VoiceNotFoundError(LookupError):
    pass


def _voice_dir(voice_id: str) -> Path:
    assert_safe_id(voice_id)
    return settings.VOICES_DIR / voice_id


def _metadata_path(voice_id: str) -> Path:
    return _voice_dir(voice_id) / "metadata.json"


def _read_metadata(voice_id: str) -> dict:
    path = _metadata_path(voice_id)
    if not path.exists():
        raise VoiceNotFoundError(voice_id)
    return json.loads(path.read_text())


def _write_metadata(voice_id: str, data: dict) -> None:
    _metadata_path(voice_id).write_text(json.dumps(data, indent=2))


PRESET_VOICES: dict[str, dict] = {
    "preset_hi_madhur": {
        "id": "preset_hi_madhur",
        "name": "Madhur (Hindi Male - Indian Voice)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "male",
        "category": "News & Broadcast",
        "style": "Authoritative & Crisp",
        "description": "Clear and confident Hindi male neural voice.",
        "engine": "edge",
        "base_speaker": "hi-IN-MadhurNeural",
        "voice": "hi-IN-MadhurNeural",
        "preview_text": "नमस्कार, आज के मुख्य समाचारों में आपका स्वागत है।",
    },
    "preset_hi_swara": {
        "id": "preset_hi_swara",
        "name": "Swara (Hindi Female - Indian Voice)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "female",
        "category": "News & Broadcast",
        "style": "Formal & Confident",
        "description": "Polished and natural Hindi female neural voice.",
        "engine": "edge",
        "base_speaker": "hi-IN-SwaraNeural",
        "voice": "hi-IN-SwaraNeural",
        "preview_text": "दिनभर की बड़ी ख़बरों के विशेष बुलेटिन में आपका स्वागत है।",
    },
    "preset_en_in_prabhat": {
        "id": "preset_en_in_prabhat",
        "name": "Prabhat (Indian English - Male)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "male",
        "category": "Educational",
        "style": "Academic & Clear",
        "description": "Natural Indian English male accent.",
        "engine": "edge",
        "base_speaker": "en-IN-PrabhatNeural",
        "voice": "en-IN-PrabhatNeural",
        "preview_text": "Hello, welcome to our interactive audio tutorial.",
    },
    "preset_en_in_neerja": {
        "id": "preset_en_in_neerja",
        "name": "Neerja (Indian English - Female)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "female",
        "category": "Corporate",
        "style": "Welcoming & Professional",
        "description": "Natural Indian English female accent.",
        "engine": "edge",
        "base_speaker": "en-IN-NeerjaNeural",
        "voice": "en-IN-NeerjaNeural",
        "preview_text": "Welcome to our customer experience briefing.",
    },
    "preset_en_us_jenny": {
        "id": "preset_en_us_jenny",
        "name": "Jenny (US English - Female)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "female",
        "category": "Conversational",
        "style": "Friendly",
        "description": "Clear US English female voice.",
        "engine": "edge",
        "base_speaker": "en-US-JennyNeural",
        "voice": "en-US-JennyNeural",
        "preview_text": "Hi there! I am ready to convert your text to speech.",
    },
    "preset_en_us_guy": {
        "id": "preset_en_us_guy",
        "name": "Guy (US English - Male)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "male",
        "category": "Conversational",
        "style": "Casual",
        "description": "Clear US English male voice.",
        "engine": "edge",
        "base_speaker": "en-US-GuyNeural",
        "voice": "en-US-GuyNeural",
        "preview_text": "Good morning, all systems are operational.",
    },
}

# Import 100 Hindi voices
from app.hindi_voices import HINDI_VOICES

ALL_PRESET_VOICES: dict[str, dict] = dict(PRESET_VOICES)

for _hv in HINDI_VOICES:
    ALL_PRESET_VOICES[_hv["id"]] = {
        "id": _hv["id"],
        "name": _hv["name"],
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": _hv["gender"],
        "category": _hv["category"],
        "style": _hv["style"],
        "description": _hv["description"],
        "engine": _hv["engine"],
        "base_speaker": _hv["base_speaker"],
        "prompt": _hv["prompt"],
        "pitch": _hv["pitch"],
        "rate": _hv["rate"],
        "tags": _hv["tags"],
        "preview_text": _hv["preview_text"],
        "voice": _hv["base_speaker"],
    }

# Dynamically inject Fish Audio preset if credentials are configured in .env
if settings.FISH_API_KEY and settings.FISH_VOICE_ID:
    ALL_PRESET_VOICES["preset_fish_clone"] = {
        "id": "preset_fish_clone",
        "name": "🎙️ Shakir (Fish Audio Clone)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "male",
        "category": "Voice Clone",
        "style": "Natural & Expressive",
        "description": f"Fish Audio cloned voice — Model: {settings.FISH_TTS_MODEL}",
        "engine": "fish",
        "base_speaker": settings.FISH_VOICE_ID,
        "voice": settings.FISH_VOICE_ID,
        "preview_text": "नमस्ते! यह मेरी असली आवाज़ का एक नमूना है।",
        "tags": ["fish-audio", "clone", "custom"],
        "prompt": None,
        "pitch": 0,
        "rate": "+0%",
    }


def is_preset_voice(voice_id: str) -> bool:
    return voice_id in ALL_PRESET_VOICES


def get_preset_voice(voice_id: str) -> dict | None:
    return ALL_PRESET_VOICES.get(voice_id)


def list_voices(
    include_presets: bool = True,
    category: str | None = None,
    gender: str | None = None,
) -> list[dict]:
    presets: list[dict] = []
    if include_presets:
        for v in ALL_PRESET_VOICES.values():
            if category and v.get("category", "").lower() != category.lower():
                continue
            if gender and v.get("gender", "").lower() != gender.lower():
                continue
            presets.append(dict(v))

    if not settings.VOICES_DIR.exists():
        return presets

    custom_voices: list[dict] = []
    for child in sorted(settings.VOICES_DIR.iterdir()):
        meta_path = child / "metadata.json"
        if meta_path.exists():
            data = json.loads(meta_path.read_text())
            data.setdefault("is_preset", False)
            if category and data.get("category", "").lower() != category.lower():
                continue
            if gender and data.get("gender", "").lower() != gender.lower():
                continue
            custom_voices.append(data)
    custom_voices.sort(key=lambda v: v["created_at"], reverse=True)
    return presets + custom_voices


def get_voice(voice_id: str) -> dict:
    if voice_id in ALL_PRESET_VOICES:
        return dict(ALL_PRESET_VOICES[voice_id])
    return _read_metadata(voice_id)



def create_voice(name: str, upload_path: Path) -> dict:
    """Create a new voice profile from an uploaded/recorded audio file.

    Steps: preprocess audio -> save reference.wav -> extract tone color
    embedding -> save se.pth -> write metadata.json.
    """
    voice_id = new_id("voice")
    voice_dir = _voice_dir(voice_id)
    voice_dir.mkdir(parents=True, exist_ok=True)

    reference_path = voice_dir / "reference.wav"
    try:
        duration = convert_to_reference_wav(upload_path, reference_path)
        se_path = voice_dir / "se.pth"
        _extract_and_save_embedding(reference_path, se_path)
    except Exception:
        shutil.rmtree(voice_dir, ignore_errors=True)
        raise

    metadata = {
        "id": voice_id,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ready": True,
        "duration_seconds": duration,
    }
    _write_metadata(voice_id, metadata)
    return metadata


def _extract_and_save_embedding(reference_wav: Path, se_out_path: Path) -> None:
    model_service.require_ready()
    try:
        from openvoice import se_extractor

        target_se, _ = se_extractor.get_se(
            str(reference_wav), model_service.tone_color_converter, vad=True
        )
        import torch

        torch.save(target_se.cpu(), se_out_path)
    except Exception:
        # Direct extraction via OpenVoice ref_enc without requiring faster_whisper
        model_service.tone_color_converter.extract_se(
            str(reference_wav), se_save_path=str(se_out_path)
        )


def recompute_embedding(voice_id: str) -> dict:
    """Recreate se.pth from the stored reference.wav, e.g. after a model
    upgrade or if se.pth was deleted. Does not require re-recording."""
    voice_dir = _voice_dir(voice_id)
    reference_path = voice_dir / "reference.wav"
    if not reference_path.exists():
        raise AudioValidationError(
            "No reference recording is stored for this profile, so the "
            "embedding cannot be recreated - please create a new profile."
        )
    se_path = voice_dir / "se.pth"
    _extract_and_save_embedding(reference_path, se_path)
    metadata = _read_metadata(voice_id)
    metadata["ready"] = True
    _write_metadata(voice_id, metadata)
    return metadata


def rename_voice(voice_id: str, new_name: str) -> dict:
    if voice_id in PRESET_VOICES:
        raise ValueError("Cannot rename a built-in preset voice.")
    metadata = _read_metadata(voice_id)
    metadata["name"] = new_name
    _write_metadata(voice_id, metadata)
    return metadata


def delete_voice(voice_id: str) -> None:
    if voice_id in PRESET_VOICES:
        raise ValueError("Cannot delete a built-in preset voice.")
    voice_dir = _voice_dir(voice_id)
    if not voice_dir.exists():
        raise VoiceNotFoundError(voice_id)
    shutil.rmtree(voice_dir)



def get_embedding_path(voice_id: str) -> Path:
    path = _voice_dir(voice_id) / "se.pth"
    if not path.exists():
        raise VoiceNotFoundError(
            f"No tone color embedding found for voice {voice_id}. It may "
            "need to be recreated - see the 'Recompute' option on this profile."
        )
    return path
