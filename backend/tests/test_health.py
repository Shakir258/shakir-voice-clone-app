from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_model_status_shape():
    resp = client.get("/api/model/status")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"status", "device", "detail"}
    assert body["status"] in ("not_started", "loading", "ready", "error")
