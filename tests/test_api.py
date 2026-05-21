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
        "schema_version": "esr-140.10",
        "flags": {"DisableTelemetry": True, "DisablePrivateBrowsing": True},
        "compliance": {"framework": "cis", "layer": "cis_l2"},
    }

    # Create
    r = client.post("/api/profiles", json=body)
    assert r.status_code == 201, r.text
    created = r.json()
    pid = created["id"]
    assert created["compliance"] == {"framework": "cis", "layer": "cis_l2"}
    assert created["revision"] == 1

    # List
    r = client.get("/api/profiles")
    assert r.status_code == 200
    items = r.json()
    assert any(p["id"] == pid for p in items)
    assert next(p for p in items if p["id"] == pid)["revision"] == 1

    # Export Firefox policies.json for this profile.
    r = client.get(f"/api/export/profiles/{pid}/firefox/policies.json")
    assert r.status_code == 200
    assert r.json() == {
        "policies": {
            "DisableTelemetry": True,
            "DisablePrivateBrowsing": True,
        }
    }

    # Download mode sends the same deployment document as an attachment.
    r_download = client.get(f"/api/export/profiles/{pid}/firefox/policies.json?download=1")
    assert r_download.status_code == 200
    assert r_download.headers["content-disposition"] == f'attachment; filename="profile-{pid}-policies.json"'
    assert r_download.json() == r.json()
