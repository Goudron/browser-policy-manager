from app.main import app
from tests.support import make_test_client


def test_health_and_ready():
    """Covers /health and /health/ready endpoints (app/api/health.py)."""
    with make_test_client(app) as client:
        r1 = client.get("/health")
        r2 = client.get("/health/ready")

    assert r1.status_code == 200
    assert r1.json() == {"status": "ok"}

    assert r2.status_code == 200
    data = r2.json()
    assert isinstance(data, dict) and data.get("ready") is True
