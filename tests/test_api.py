# tests/test_api.py
import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_profiles_crud_and_export():
    """Create -> list -> export roundtrip on a fresh unique profile."""
    client = TestClient(app)

    unique = uuid.uuid4().hex[:8]
    body = {
        "name": f"Default-{unique}",
        "description": "Base profile",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True, "DisablePocket": True},
    }

    # Create
    r = client.post("/api/policies", json=body)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # List
    r = client.get("/api/policies")
    assert r.status_code == 200
    items = r.json()
    assert any(p["id"] == pid for p in items)

    # Export JSON for this profile (endpoint kept in app/api/export.py)
    r = client.get(f"/api/export/{pid}/policies.json")
    assert r.status_code == 200
