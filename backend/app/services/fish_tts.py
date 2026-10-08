"""
Fish Audio TTS client.

Server-only — never import from frontend code.
Uses httpx (already a project dependency) for async HTTP with timeout.
"""
from __future__ import annotations

import logging
import os

import httpx

from app.messages import FISH_TTS_ENV_MISSING, FISH_TTS_TIMEOUT, FISH_TTS_UPSTREAM_ERROR

logger = logging.getLogger(__name__)

FISH_TTS_URL = "https://api.fish.audio/v1/tts"
_TIMEOUT_SECONDS = 30


class FishTTSError(RuntimeError):
    """Raised when the Fish Audio API returns a non-2xx response."""


class FishTTSTimeoutError(FishTTSError):
    """Raised when the request to Fish Audio times out."""


async def generate_speech(text: str) -> bytes:
    """Call Fish Audio /v1/tts and return raw MP3 bytes.

    Raises:
        EnvironmentError: if any required env var is missing.
        FishTTSTimeoutError: if the request exceeds _TIMEOUT_SECONDS.
        FishTTSError: if the API returns a non-2xx status.
    """
    from dotenv import load_dotenv
    from pathlib import Path
    from app.config import settings

    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)

    api_key = os.getenv("FISH_API_KEY") or settings.FISH_API_KEY
    voice_id = os.getenv("FISH_VOICE_ID") or settings.FISH_VOICE_ID
    model = os.getenv("FISH_TTS_MODEL") or settings.FISH_TTS_MODEL

    if not api_key or not voice_id or not model:
        raise EnvironmentError(FISH_TTS_ENV_MISSING)

    # Never log api_key or full headers.
    logger.debug("Fish TTS request: model=%s chars=%d", model, len(text))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
    }
    payload = {"text": text, "reference_id": voice_id}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.post(FISH_TTS_URL, json=payload, headers=headers)

        if resp.status_code < 200 or resp.status_code >= 300:
            logger.warning("Fish TTS non-2xx: status=%d error=%s", resp.status_code, resp.text[:200])
            raise FishTTSError(FISH_TTS_UPSTREAM_ERROR)

        return resp.content

    except httpx.TimeoutException as exc:
        logger.warning("Fish TTS request timed out after %ds", _TIMEOUT_SECONDS)
        raise FishTTSTimeoutError(FISH_TTS_TIMEOUT) from exc
