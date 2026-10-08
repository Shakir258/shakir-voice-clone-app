"""
These tests exercise the voice-profile API without needing real model
weights installed: they monkeypatch the embedding-extraction step,
which is the only part of voice_profile_service that touches the
actual OpenVoice model.
"""
import io

from fastapi.testclient import TestClient

from app.main import app
from app.services import voice_profile_service

client = TestClient(app)


def _fake_extract(reference_wav, se_out_path):
    # Avoids requiring torch/openvoice to be installed just to test the
    # HTTP/file-lifecycle layer. The real implementation saves a torch
    # tensor here; a placeholder file is enough to exercise everything
    # around it (metadata, listing, rename, delete).
    se_out_path.write_bytes(b"fake-embedding")


def test_list_voices_empty():
    resp = client.get("/api/voices?include_presets=false")
    assert resp.status_code == 200
    assert resp.json() == {"voices": []}


def test_list_100_hindi_presets():
    resp = client.get("/api/voices")
    assert resp.status_code == 200
    all_voices = resp.json()["voices"]
    assert len(all_voices) >= 100
    ids = [v["id"] for v in all_voices]
    assert "hi-male-news-anchor-01" in ids
    assert "hi-female-news-anchor-02" in ids
    assert "hi-male-char-village-elder-100" in ids


def test_create_list_rename_delete_voice(monkeypatch, tmp_path):
    monkeypatch.setattr(voice_profile_service, "_extract_and_save_embedding", _fake_extract)
    monkeypatch.setattr(
        voice_profile_service,
        "convert_to_reference_wav",
        lambda src, dst: (dst.parent.mkdir(parents=True, exist_ok=True), dst.write_bytes(b"RIFF....WAVEfmt "), 5.0)[-1],
    )

    fake_wav = io.BytesIO(b"not-real-audio-but-fine-for-this-mock")
    resp = client.post(
        "/api/voices",
        data={"name": "My Voice"},
        files={"file": ("test.wav", fake_wav, "audio/wav")},
    )
    assert resp.status_code == 201, resp.text
    voice = resp.json()
    assert voice["name"] == "My Voice"
    assert voice["ready"] is True
    voice_id = voice["id"]

    resp = client.get("/api/voices?include_presets=false")
    assert len(resp.json()["voices"]) == 1

    resp = client.patch(f"/api/voices/{voice_id}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"

    resp = client.delete(f"/api/voices/{voice_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/voices/{voice_id}")
    assert resp.status_code == 404


def test_create_voice_missing_name_rejected():
    fake_wav = io.BytesIO(b"data")
    resp = client.post(
        "/api/voices",
        data={"name": " "},
        files={"file": ("test.wav", fake_wav, "audio/wav")},
    )
    assert resp.status_code == 400


def test_create_voice_bad_content_type_rejected():
    fake = io.BytesIO(b"data")
    resp = client.post(
        "/api/voices",
        data={"name": "X"},
        files={"file": ("test.exe", fake, "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_get_unknown_voice_404():
    resp = client.get("/api/voices/voice_doesnotexist")
    assert resp.status_code == 404


def test_unsafe_voice_id_rejected():
    resp = client.get("/api/voices/../../etc/passwd")
    # FastAPI/Starlette normalizes the path, so this either 404s via
    # routing or is caught by assert_safe_id -> both are acceptable,
    # the important thing is it's never a 200 or a 500.
    assert resp.status_code in (400, 404)
