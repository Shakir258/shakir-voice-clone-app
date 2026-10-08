"""
Deterministic audio cache for text-to-speech requests.

Avoids duplicate model inference when the same text, voice profile,
speed, pitch, and output format are requested again.
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


def make_cache_key(
    text: str,
    voice_id: str,
    speed: float,
    pitch: float = 0.0,
    format: str = "wav",
    extra: dict[str, Any] | None = None,
) -> str:
    """Generate a deterministic SHA-256 hash key representing the exact
    synthesis parameters."""
    normalized_text = " ".join(text.strip().split())
    payload = {
        "text": normalized_text,
        "voice_id": voice_id,
        "speed": round(float(speed), 3),
        "pitch": round(float(pitch), 2),
        "format": format.lower().strip(),
        "extra": extra or {},
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_cached_audio(
    text: str,
    voice_id: str,
    speed: float,
    pitch: float = 0.0,
    format: str = "wav",
    extra: dict[str, Any] | None = None,
) -> Path | None:
    """Return the cached audio Path if already generated and non-empty,
    else None."""
    key = make_cache_key(text, voice_id, speed, pitch, format, extra)
    ext = format.lower().strip().lstrip(".") or "wav"
    cached_file = settings.CACHE_DIR / f"{key}.{ext}"

    if cached_file.exists() and cached_file.stat().st_size > 512:
        logger.info("Audio cache HIT for key=%s (voice=%s)", key[:12], voice_id)
        return cached_file
    return None


def store_cached_audio(
    src_audio_path: Path,
    text: str,
    voice_id: str,
    speed: float,
    pitch: float = 0.0,
    format: str = "wav",
    extra: dict[str, Any] | None = None,
) -> Path:
    """Store generated audio in the cache directory under its deterministic
    key."""
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = make_cache_key(text, voice_id, speed, pitch, format, extra)
    ext = format.lower().strip().lstrip(".") or "wav"
    cached_file = settings.CACHE_DIR / f"{key}.{ext}"

    try:
        shutil.copyfile(src_audio_path, cached_file)
        logger.info("Stored audio cache for key=%s (voice=%s)", key[:12], voice_id)
    except Exception as exc:
        logger.warning("Failed to store audio in cache: %s", exc)

    return cached_file
