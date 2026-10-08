"""
Audio preprocessing.

Browsers record WebM/Opus (MediaRecorder default); OpenVoice's tone
color extractor expects a WAV it can decode with librosa at the
model's sampling rate. So every reference recording goes through:

    browser upload (webm/mp3/wav/...)
      -> ffmpeg decode + convert
      -> mono, 22050 Hz, 16-bit PCM WAV
      -> saved as reference.wav in the voice profile folder

We do NOT do aggressive normalization/denoising by default - OpenVoice's
extractor is reasonably robust to raw recordings, and heavy processing
can distort the very tone color we're trying to capture. We only fix
container/codec/channel/sample-rate so the model can read the file.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 22050

# Ensure ffmpeg in PATH even if the shell was not restarted after winget install
if shutil.which("ffmpeg") is None:
    _localappdata = os.environ.get("LOCALAPPDATA", "")
    if _localappdata:
        _winget_pkgs = Path(_localappdata) / "Microsoft" / "WinGet" / "Packages"
        if _winget_pkgs.exists():
            _found = list(_winget_pkgs.glob("**/ffmpeg.exe"))
            if _found:
                os.environ["PATH"] = str(_found[0].parent) + os.pathsep + os.environ.get("PATH", "")


class AudioValidationError(ValueError):
    pass


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg was not found on PATH. Install it (see README 'Install "
            "prerequisites') and restart the backend."
        )


def convert_audio_file(src_path: Path, dst_path: Path) -> float:
    """Convert any audio file into a clean mono WAV at TARGET_SAMPLE_RATE.
    Returns duration in seconds.
    """
    ensure_ffmpeg_available()

    if not src_path.exists() or src_path.stat().st_size == 0:
        raise AudioValidationError("The audio file is empty or missing.")

    dst_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src_path),
        "-ac",
        "1",  # mono
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-c:a",
        "pcm_s16le",
        str(dst_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not dst_path.exists():
        logger.error("ffmpeg failed: %s", result.stderr[-2000:])
        raise AudioValidationError(
            "This recording could not be processed. The file may be corrupted "
            "or in an unsupported format. Try recording again or uploading a "
            "WAV/MP3 file."
        )

    return get_duration_seconds(dst_path)


def convert_to_reference_wav(src_path: Path, dst_path: Path) -> float:
    """Convert any browser-recorded/uploaded audio file into a clean mono
    WAV at TARGET_SAMPLE_RATE. Returns duration in seconds.

    Raises AudioValidationError with a user-facing message on failure -
    never lets a raw ffmpeg stack trace reach the API layer.
    """
    duration = convert_audio_file(src_path, dst_path)

    if duration < settings.MIN_REFERENCE_SECONDS:
        dst_path.unlink(missing_ok=True)
        raise AudioValidationError(
            f"Recording is too short ({duration:.1f}s). Please provide at "
            f"least {settings.MIN_REFERENCE_SECONDS:.0f} seconds of clear speech."
        )
    if duration > settings.MAX_REFERENCE_SECONDS:
        dst_path.unlink(missing_ok=True)
        raise AudioValidationError(
            f"Recording is too long ({duration:.1f}s). Please keep reference "
            f"recordings under {settings.MAX_REFERENCE_SECONDS:.0f} seconds."
        )
    return duration


def get_duration_seconds(wav_path: Path) -> float:
    import wave

    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def concat_wavs(paths: list[Path], out_path: Path) -> None:
    """Concatenate multiple WAV chunks (same format) into one file,
    used when long text is split into several generation chunks."""
    import wave

    if not paths:
        raise ValueError("No audio chunks to concatenate.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(paths[0]), "rb") as first:
        params = first.getparams()

    with wave.open(str(out_path), "wb") as out:
        out.setparams(params)
        for p in paths:
            with wave.open(str(p), "rb") as wf:
                out.writeframes(wf.readframes(wf.getnframes()))
