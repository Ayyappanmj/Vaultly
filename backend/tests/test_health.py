from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_status_keys():
    body = TestClient(app).get("/health").json()
    assert body["status"] in {"ok", "degraded"}
    assert "postgres" in body and "redis" in body
