# tests/test_api.py
import uuid

from app.main import app
from tests.support import make_test_client


def test_profiles_crud_and_export():
    """Create -> list -> export roundtrip on a fresh unique profile."""
    client = make_test_client(app)

    unique = uuid.uuid4().hex[:8]
    body = {
        "name": f"Default-{unique}",
        "description": "Base profile",
        "schema_version": "esr-140",
        "flags": {"DisableTelemetry": True, "DisablePrivateBrowsing": True},
    }

    # Create
    r = client.post("/api/profiles", json=body)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # List
    r = client.get("/api/profiles")
    assert r.status_code == 200
    items = r.json()
    assert any(p["id"] == pid for p in items)

    # Export JSON for this profile (endpoint kept in app/api/export.py)
    r = client.get(f"/api/export/profiles/{pid}.json")
    assert r.status_code == 200
