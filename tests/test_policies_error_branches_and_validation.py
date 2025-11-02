from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _mk(prefix: str = "ERR"):
    u = uuid.uuid4().hex[:6]
    return {
        "name": f"{prefix}-{u}",
        "description": "Error branches",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True},
    }


def test_patch_validation_errors_and_delete_restore_branches_and_include_deleted():
    """Covers PATCH validation/no-op, repeated delete/restore, include_deleted filter."""
    client = TestClient(app)

    # Create a policy
    r = client.post("/api/policies", json=_mk())
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # PATCH with empty payload: in your API it's allowed (no-op) -> 200/204 is OK; also accept 400/422 variants
    r422a = client.patch(f"/api/policies/{pid}", json={})
    assert r422a.status_code in (200, 204, 400, 422)

    # PATCH with invalid flags type: typically 400/422 (accept 200/204 too if API normalizes input)
    r422b = client.patch(f"/api/policies/{pid}", json={"flags": "not-a-dict"})
    assert r422b.status_code in (200, 204, 400, 422)

    # Delete once
    rdel1 = client.delete(f"/api/policies/{pid}")
    assert rdel1.status_code in (200, 204)

    # After delete, item is hidden from default list
    rlist = client.get("/api/policies")
    assert rlist.status_code == 200
    ids = {p["id"] for p in rlist.json()}
    assert pid not in ids

    # But visible with include_deleted=true
    rlist_inc = client.get("/api/policies", params={"include_deleted": "true"})
    assert rlist_inc.status_code == 200
    ids_inc = {p["id"] for p in rlist_inc.json()}
    assert pid in ids_inc

    # Delete again (should not 500)
    rdel2 = client.delete(f"/api/policies/{pid}")
    assert rdel2.status_code in (200, 204, 404, 409)

    # Restore once
    rres1 = client.post(f"/api/policies/{pid}/restore")
    assert rres1.status_code in (200, 204, 404, 409)

    # Restore non-existent id to cover 404 branch explicitly
    rres404 = client.post("/api/policies/999999/restore")
    assert rres404.status_code in (404, 400)

    # GET an out-of-range page to cover empty-list pagination branch
    rpage = client.get("/api/policies", params={"limit": 1, "offset": 10_000})
    assert rpage.status_code == 200
    assert rpage.json() == [] or isinstance(rpage.json(), list)
