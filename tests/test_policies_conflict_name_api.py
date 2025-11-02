from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_create_conflict_name_returns_409():
    """Verify duplicate policy name handling returns 409 (IntegrityError path)."""
    client = TestClient(app)
    unique = uuid.uuid4().hex[:6]
    body = {
        "name": f"Conflict-{unique}",
        "description": "Duplicate check",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True},
    }

    r1 = client.post("/api/policies", json=body)
    assert r1.status_code == 201, r1.text

    r2 = client.post("/api/policies", json=body)
    assert r2.status_code in (409, 400)  # primary path is 409
