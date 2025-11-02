from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk_body(prefix: str = "Edge"):
    """Generate a simple policy profile body for CRUD edge tests."""
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{prefix}-{u}",
        "description": "Edge cases",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True},
    }


def test_soft_delete_twice_and_restore_twice_and_update_flags_merge():
    """Covers soft delete/restore and PATCH flag updates."""
    client = TestClient(app)

    # Create a policy profile
    r = client.post("/api/policies", json=_mk_body())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # First delete (soft)
    rdel1 = client.delete(f"/api/policies/{pid}")
    assert rdel1.status_code in (204, 200)

    # Second delete on already deleted: must not crash
    rdel2 = client.delete(f"/api/policies/{pid}")
    assert rdel2.status_code in (200, 204, 404, 409)

    # Restore back
    rres1 = client.post(f"/api/policies/{pid}/restore")
    assert rres1.status_code in (200, 204)

    # Second restore when already active: allow 404 as "not found among deleted"
    rres2 = client.post(f"/api/policies/{pid}/restore")
    assert rres2.status_code in (200, 204, 400, 404, 409)

    # Update flags: merge/overwrite behavior shouldn't crash
    patch = {"flags": {"DisableTelemetry": False, "DisablePocket": True}}
    rupd = client.patch(f"/api/policies/{pid}", json=patch)
    assert rupd.status_code in (200, 204)

    # Read back and verify flags structure
    rget = client.get(f"/api/policies/{pid}")
    assert rget.status_code == 200
    obj = rget.json()
    assert isinstance(obj.get("flags"), dict)
    assert "DisableTelemetry" in obj["flags"]
    assert "DisablePocket" in obj["flags"]


def test_ordering_query_params_do_not_break():
    """Ensure ordering and filtering query params do not raise errors."""
    client = TestClient(app)

    # Ensure at least one item exists
    client.post("/api/policies", json=_mk_body(prefix="Sort"))

    # Test various parameter combinations
    combos = (
        {"order_by": "name", "order": "asc"},
        {"order_by": "created_at", "order": "desc"},
        {"order_by": "updated_at"},
        {"order": "asc"},
    )
    for params in combos:
        r = client.get("/api/policies", params=params)
        assert r.status_code == 200
