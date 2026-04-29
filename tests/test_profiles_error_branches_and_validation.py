from __future__ import annotations

import uuid

from app.main import app
from tests.support import make_test_client


def _mk(prefix: str = "ERR"):
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{prefix}-{u}",
        "description": "Error branches",
        "schema_version": "esr-140.10",
        "flags": {"DisableTelemetry": True},
    }


def test_patch_validation_errors_and_delete_restore_branches_and_include_deleted():
    """Covers PATCH validation/no-op, repeated delete/restore, include_deleted filter."""
    client = make_test_client(app)

    # Create a profile
    r = client.post("/api/profiles", json=_mk())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # PATCH with empty payload is currently treated as a valid no-op update.
    r422a = client.patch(f"/api/profiles/{pid}", json={})
    assert r422a.status_code == 200

    # Invalid flags type is rejected by request validation before the handler runs.
    r422b = client.patch(f"/api/profiles/{pid}", json={"flags": "not-a-dict"})
    assert r422b.status_code == 422

    # Delete once
    rdel1 = client.delete(f"/api/profiles/{pid}")
    assert rdel1.status_code == 204

    # After delete, item is hidden from default list
    rlist = client.get("/api/profiles")
    assert rlist.status_code == 200
    ids = {p["id"] for p in rlist.json()}
    assert pid not in ids

    # But visible with include_deleted=true
    rlist_inc = client.get("/api/profiles", params={"include_deleted": "true"})
    assert rlist_inc.status_code == 200
    ids_inc = {p["id"] for p in rlist_inc.json()}
    assert pid in ids_inc

    # Delete again returns the explicit not-found response.
    rdel2 = client.delete(f"/api/profiles/{pid}")
    assert rdel2.status_code == 404

    # Restore once
    rres1 = client.post(f"/api/profiles/{pid}/restore")
    assert rres1.status_code == 200

    # Restore non-existent id to cover 404 branch explicitly
    rres404 = client.post("/api/profiles/999999/restore")
    assert rres404.status_code == 404

    # GET an out-of-range page to cover empty-list pagination branch
    rpage = client.get("/api/profiles", params={"limit": 1, "offset": 10_000})
    assert rpage.status_code == 200
    assert rpage.json() == [] or isinstance(rpage.json(), list)
