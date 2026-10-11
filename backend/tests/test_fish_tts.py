import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.messages import (
    FISH_TTS_ENV_MISSING,
    FISH_TTS_INVALID_VOICE_KEY,
    FISH_TTS_TEXT_EMPTY,
    FISH_TTS_TEXT_TOO_LONG,
    FISH_TTS_TIMEOUT,
    FISH_TTS_UPSTREAM_ERROR,
    FISH_TTS_VOICE_NOT_CONFIGURED,
)
from app.services.fish_tts import (
    FishTTSError,
    FishTTSTimeoutError,
    generate_speech,
    resolve_voice_id,
)

client = TestClient(app)


def test_resolve_voice_id_known_keys(monkeypatch):
    assert resolve_voice_id("shakir_1") == "706b83690d4048b6a66f344c113c09cd"
    assert resolve_voice_id("shakir_2") == "7676ea89342c438b9e894c2798292c23"
    assert resolve_voice_id("dynamic_finance_coach") == "ef077e1438254791b72b0376c358841d"
    assert resolve_voice_id("preset_fish_ef077e1438254791b72b0376c358841d") == "ef077e1438254791b72b0376c358841d"
    # Direct 32-character hex IDs
    assert resolve_voice_id("ef077e1438254791b72b0376c358841d") == "ef077e1438254791b72b0376c358841d"
    assert resolve_voice_id("536d3a5e000945adb7038665781a4aca") == "536d3a5e000945adb7038665781a4aca"


def test_resolve_voice_id_default_fallback(monkeypatch):
    # None or unknown voice key falls back to default ("shakir_1")
    assert resolve_voice_id(None) == "706b83690d4048b6a66f344c113c09cd"
    assert resolve_voice_id("unknown_voice") == "706b83690d4048b6a66f344c113c09cd"


def test_resolve_voice_id_env_override(monkeypatch):
    monkeypatch.setenv("FISH_VOICE_SHAKIR_1", "custom_override_123")
    assert resolve_voice_id("shakir_1") == "custom_override_123"


@pytest.mark.anyio
async def test_generate_speech_missing_api_key(monkeypatch):
    monkeypatch.setenv("FISH_API_KEY", "")
    monkeypatch.setattr(settings, "FISH_API_KEY", "")

    with pytest.raises(EnvironmentError) as exc_info:
        await generate_speech("Test text")
    assert str(exc_info.value) == FISH_TTS_ENV_MISSING


@pytest.mark.anyio
async def test_generate_speech_success(monkeypatch):
    monkeypatch.setenv("FISH_API_KEY", "test_key")
    monkeypatch.setenv("FISH_TTS_MODEL", "s2.1-pro-free")
    monkeypatch.setattr(settings, "FISH_API_KEY", "test_key")
    monkeypatch.setattr(settings, "FISH_TTS_MODEL", "s2.1-pro-free")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b"fake-mp3-bytes"

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await generate_speech("Hello world", voice_key="dynamic_finance_coach")
        assert result == b"fake-mp3-bytes"

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"] == {
            "text": "Hello world",
            "reference_id": "ef077e1438254791b72b0376c358841d",
            "format": "mp3",
        }
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"
        assert kwargs["headers"]["model"] == "s2.1-pro-free"


def test_api_tts_empty_text():
    response = client.post("/api/tts", json={"text": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == FISH_TTS_TEXT_EMPTY


def test_api_tts_too_long_text():
    long_text = "a" * (settings.TTS_MAX_TEXT_LENGTH + 1)
    response = client.post("/api/tts", json={"text": long_text})
    assert response.status_code == 400
    assert response.json()["detail"] == FISH_TTS_TEXT_TOO_LONG


def test_api_tts_invalid_voice_key():
    response = client.post("/api/tts", json={"text": "Valid text", "voice": "unknown_key"})
    assert response.status_code == 400
    assert FISH_TTS_INVALID_VOICE_KEY.format(valid_keys=", ".join(settings.TTS_VOICE_KEYS)) in response.json()["detail"]


def test_api_tts_success():
    with patch("app.api.routes_tts.generate_speech", new=AsyncMock(return_value=b"audio-bytes")):
        response = client.post("/api/tts", json={"text": "Hello, world!", "voice": "dynamic_finance_coach"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.content == b"audio-bytes"


def test_api_tts_upstream_error():
    with patch("app.api.routes_tts.generate_speech", side_effect=FishTTSError("Upstream failed")):
        response = client.post("/api/tts", json={"text": "Hello, world!"})
        assert response.status_code == 502
        assert response.json()["detail"] == FISH_TTS_UPSTREAM_ERROR


def test_api_tts_timeout():
    with patch("app.api.routes_tts.generate_speech", side_effect=FishTTSTimeoutError("Timed out")):
        response = client.post("/api/tts", json={"text": "Hello, world!"})
        assert response.status_code == 504
        assert response.json()["detail"] == FISH_TTS_TIMEOUT
