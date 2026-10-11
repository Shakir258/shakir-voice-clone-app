"""
Fish Audio TTS client.

Server-only — never import from frontend code.
Uses httpx (already a project dependency) for async HTTP with timeout.
"""
from __future__ import annotations

import logging
import os
import re

import httpx

from app.config import settings
from app.messages import (
    FISH_TTS_ENV_MISSING,
    FISH_TTS_TIMEOUT,
    FISH_TTS_UPSTREAM_ERROR,
    FISH_TTS_VOICE_NOT_CONFIGURED,
)

logger = logging.getLogger(__name__)

FISH_TTS_URL = "https://api.fish.audio/v1/tts"
_TIMEOUT_SECONDS = 30.0


class FishTTSError(RuntimeError):
    """Raised when the Fish Audio API returns a non-2xx response."""


class FishTTSTimeoutError(FishTTSError):
    """Raised when the request to Fish Audio times out."""


def resolve_voice_id(voice_key: str | None = None) -> str:
    """Map a voice key to the Fish reference_id.

    Defaults to settings.TTS_DEFAULT_VOICE_KEY if voice_key is missing or unknown.
    """
    from app.fish_voices import (
        DEFAULT_FISH_VOICE_ID,
        FISH_VOICES_BY_ID,
        resolve_fish_reference_id,
    )

    if voice_key and re.fullmatch(r"[0-9a-fA-F]{32}", voice_key.strip()):
        return voice_key.strip()

    cleaned = voice_key.strip() if voice_key else None

    # Check specific env override first (e.g. during testing or explicit env variable)
    if cleaned:
        env_val = os.getenv(f"FISH_VOICE_{cleaned.upper()}")
        if env_val:
            return env_val

    # Direct catalog lookup by slug or id
    if cleaned and cleaned in FISH_VOICES_BY_ID:
        return FISH_VOICES_BY_ID[cleaned]["reference_id"]

    if cleaned and cleaned.startswith("preset_fish_"):
        candidate = cleaned[len("preset_fish_"):]
        if re.fullmatch(r"[0-9a-fA-F]{32}", candidate):
            return candidate

    # Fallback to default key
    key = cleaned if (cleaned and cleaned in settings.TTS_VOICE_KEYS) else settings.TTS_DEFAULT_VOICE_KEY

    env_val = os.getenv(f"FISH_VOICE_{key.upper()}")
    if env_val:
        return env_val

    if key in FISH_VOICES_BY_ID:
        return FISH_VOICES_BY_ID[key]["reference_id"]

    if key == settings.TTS_DEFAULT_VOICE_KEY:
        return DEFAULT_FISH_VOICE_ID

    raise EnvironmentError(FISH_TTS_VOICE_NOT_CONFIGURED.format(voice_key=key))


async def generate_speech(text: str, voice_key: str | None = None) -> bytes:
    """Call Fish Audio /v1/tts and return raw MP3 bytes.

    Raises:
        EnvironmentError: if any required env var is missing or voice is not configured.
        FishTTSTimeoutError: if the request exceeds _TIMEOUT_SECONDS.
        FishTTSError: if the API returns a non-2xx status.
    """
    api_key = os.getenv("FISH_API_KEY") or settings.FISH_API_KEY
    model = os.getenv("FISH_TTS_MODEL") or settings.FISH_TTS_MODEL

    if not api_key or not model:
        raise EnvironmentError(FISH_TTS_ENV_MISSING)

    voice_id = resolve_voice_id(voice_key)

    # Never log api_key, full headers, or reference_id.
    logger.debug("Fish TTS request: model=%s chars=%d", model, len(text))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
    }
    payload = {
        "text": text,
        "reference_id": voice_id,
        "format": "mp3",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.post(FISH_TTS_URL, json=payload, headers=headers)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Fish TTS non-2xx status=%d", resp.status_code)
            raise FishTTSError(FISH_TTS_UPSTREAM_ERROR)

        return resp.content

    except httpx.TimeoutException as exc:
        logger.warning("Fish TTS request timed out after %ds", int(_TIMEOUT_SECONDS))
        raise FishTTSTimeoutError(FISH_TTS_TIMEOUT) from exc
