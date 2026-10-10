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
    """Map a voice key to the Fish reference_id from environment.

    Defaults to settings.TTS_DEFAULT_VOICE_KEY if voice_key is missing or unknown.
    """
    if voice_key and re.fullmatch(r"[0-9a-fA-F]{32}", voice_key.strip()):
        return voice_key.strip()

    key = voice_key if (voice_key and voice_key in settings.TTS_VOICE_KEYS) else settings.TTS_DEFAULT_VOICE_KEY

    voice_id_map: dict[str, str] = {
        "motivation": os.getenv("FISH_VOICE_MOTIVATION") or settings.FISH_VOICE_MOTIVATION,
        "news": os.getenv("FISH_VOICE_NEWS") or settings.FISH_VOICE_NEWS,
        "hindi_yuva": os.getenv("FISH_VOICE_HINDI_YUVA") or settings.FISH_VOICE_HINDI_YUVA,
        "hindi_energetic": os.getenv("FISH_VOICE_HINDI_ENERGETIC") or settings.FISH_VOICE_HINDI_ENERGETIC,
        "adrian": os.getenv("FISH_VOICE_ADRIAN") or settings.FISH_VOICE_ADRIAN,
        "ethan": os.getenv("FISH_VOICE_ETHAN") or settings.FISH_VOICE_ETHAN,
    }
    voice_id = voice_id_map.get(key)
    if not voice_id:
        raise EnvironmentError(FISH_TTS_VOICE_NOT_CONFIGURED.format(voice_key=key))
    return voice_id


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
