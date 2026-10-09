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
    monkeypatch.setenv("FISH_VOICE_MOTIVATION", "ref_motivation_123")
    monkeypatch.setenv("FISH_VOICE_NEWS", "ref_news_456")
    monkeypatch.setenv("FISH_VOICE_HINDI_YUVA", "d4d1b40efad24801a84d1e78517866f8")
    monkeypatch.setenv("FISH_VOICE_HINDI_ENERGETIC", "e68315c9dd2f498aab485b813e3fda6d")
    monkeypatch.setenv("FISH_VOICE_ADRIAN", "bf322df2096a46f18c579d0baa36f41d")

    assert resolve_voice_id("motivation") == "ref_motivation_123"
    assert resolve_voice_id("news") == "ref_news_456"
    assert resolve_voice_id("hindi_yuva") == "d4d1b40efad24801a84d1e78517866f8"
    assert resolve_voice_id("hindi_energetic") == "e68315c9dd2f498aab485b813e3fda6d"
    assert resolve_voice_id("adrian") == "bf322df2096a46f18c579d0baa36f41d"
    # Direct 32-character hex ID
    assert resolve_voice_id("d4d1b40efad24801a84d1e78517866f8") == "d4d1b40efad24801a84d1e78517866f8"


def test_resolve_voice_id_default_fallback(monkeypatch):
    monkeypatch.setenv("FISH_VOICE_MOTIVATION", "ref_motivation_123")
    # None or unknown voice key falls back to default ("motivation")
    assert resolve_voice_id(None) == "ref_motivation_123"
    assert resolve_voice_id("unknown_voice") == "ref_motivation_123"


def test_resolve_voice_id_missing_env(monkeypatch):
    monkeypatch.delenv("FISH_VOICE_MOTIVATION", raising=False)
    monkeypatch.setattr(settings, "FISH_VOICE_MOTIVATION", "")

    with pytest.raises(EnvironmentError) as exc_info:
        resolve_voice_id("motivation")
    assert FISH_TTS_VOICE_NOT_CONFIGURED.format(voice_key="motivation") in str(exc_info.value)


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
    monkeypatch.setenv("FISH_VOICE_NEWS", "ref_news_789")
    monkeypatch.setattr(settings, "FISH_API_KEY", "test_key")
    monkeypatch.setattr(settings, "FISH_TTS_MODEL", "s2.1-pro-free")
    monkeypatch.setattr(settings, "FISH_VOICE_NEWS", "ref_news_789")

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b"fake-mp3-bytes"

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await generate_speech("Hello world", voice_key="news")
        assert result == b"fake-mp3-bytes"

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"] == {
            "text": "Hello world",
            "reference_id": "ref_news_789",
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
        response = client.post("/api/tts", json={"text": "Hello, world!", "voice": "news"})
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
