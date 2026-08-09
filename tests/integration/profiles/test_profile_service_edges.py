from __future__ import annotations

from app.main import app
from tests.support import build_profile_payload, make_test_client


def _mk_body(prefix: str = "Edge"):
    return build_profile_payload(name_prefix=prefix, description="Edge cases")


def test_soft_delete_twice_and_restore_twice_and_update_flags_merge():
    """Covers soft delete/restore and PATCH flag updates."""
    client = make_test_client(app)

    # Create a profile
    r = client.post("/api/profiles", json=_mk_body())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # First delete (soft)
    rdel1 = client.delete(f"/api/profiles/{pid}")
    assert rdel1.status_code == 204

    # Second delete on already deleted returns the explicit not-found response.
    rdel2 = client.delete(f"/api/profiles/{pid}")
    assert rdel2.status_code == 404

    # Restore back
    rres1 = client.post(f"/api/profiles/{pid}/restore")
    assert rres1.status_code == 200

    # Second restore when already active returns 404 because the profile is no
    # longer in the deleted set.
    rres2 = client.post(f"/api/profiles/{pid}/restore")
    assert rres2.status_code == 404

    # Update flags: merge/overwrite behavior shouldn't crash
    patch = {"flags": {"DisableTelemetry": False, "DisablePrivateBrowsing": True}}
    rupd = client.patch(f"/api/profiles/{pid}", json=patch)
    assert rupd.status_code == 200

    # Read back and verify flags structure
    rget = client.get(f"/api/profiles/{pid}")
    assert rget.status_code == 200
    obj = rget.json()
    assert isinstance(obj.get("flags"), dict)
    assert "DisableTelemetry" in obj["flags"]
    assert "DisablePrivateBrowsing" in obj["flags"]


def test_ordering_query_params_do_not_break():
    """Ensure ordering and filtering query params do not raise errors."""
    client = make_test_client(app)

    # Ensure at least one item exists
    client.post("/api/profiles", json=_mk_body(prefix="Sort"))

    # Test various parameter combinations
    combos = (
        {"order_by": "name", "order": "asc"},
        {"order_by": "created_at", "order": "desc"},
        {"order_by": "updated_at"},
        {"order": "asc"},
    )
    for params in combos:
        r = client.get("/api/profiles", params=params)
        assert r.status_code == 200
