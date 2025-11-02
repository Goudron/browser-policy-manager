from fastapi.testclient import TestClient

from app.main import app


def test_health_and_ready():
    """Covers /health and /health/ready endpoints (app/api/health.py)."""
    client = TestClient(app)

    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json() == {"status": "ok"}

    r2 = client.get("/health/ready")
    assert r2.status_code == 200
    data = r2.json()
    assert isinstance(data, dict) and data.get("ready") is True
