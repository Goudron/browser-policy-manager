from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_validate_profile_ok_and_fail():
    client = TestClient(app)

    good = {"document": {"DisableTelemetry": True}}
    bad = {"document": 123}  # should produce ok=False

    # ESR 140
    r1 = client.post("/api/validate/esr-140", json=good)
    assert r1.status_code == 200, r1.text
    assert r1.json()["ok"] is True

    r2 = client.post("/api/validate/esr-140", json=bad)
    assert r2.status_code == 200
    assert r2.json()["ok"] is False

    # Release 144
    r3 = client.post("/api/validate/release-144", json=good)
    assert r3.status_code == 200
    assert r3.json()["ok"] is True

    r4 = client.post("/api/validate/release-144", json=bad)
    assert r4.status_code == 200
    assert r4.json()["ok"] is False

    # Unsupported profile -> 400/404
    r5 = client.post("/api/validate/beta", json=good)
    assert r5.status_code in (400, 404)
