from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_duplicate_name_conflict_and_restore_and_include_deleted():
    client = TestClient(app)
    unique = uuid.uuid4().hex[:6]
    body = {
        "name": f"Conflict-{unique}",
        "description": "Base profile",
        "schema_version": "firefox-ESR",
        "flags": {"DisableTelemetry": True},
    }

    # Create #1
    r1 = client.post("/api/policies", json=body)
    assert r1.status_code == 201, r1.text
    pid = r1.json()["id"]

    # Create #2 with same name -> 409
    r2 = client.post("/api/policies", json=body)
    assert r2.status_code in (409, 400)

    # Soft delete
    rd = client.delete(f"/api/policies/{pid}")
    assert rd.status_code == 204

    # By default deleted are hidden
    rlist = client.get("/api/policies")
    assert rlist.status_code == 200
    ids = [p["id"] for p in rlist.json()]
    assert pid not in ids

    # Include deleted -> item appears and has is_deleted = True
    rlist2 = client.get("/api/policies", params={"include_deleted": "true"})
    assert rlist2.status_code == 200
    items = rlist2.json()
    item = next((p for p in items if p["id"] == pid), None)
    assert item is not None and item["is_deleted"] is True

    # Restore
    rr = client.post(f"/api/policies/{pid}/restore")
    # 200 OK with restored entity
    assert rr.status_code == 200
    restored = rr.json()
    assert restored["id"] == pid and restored["is_deleted"] is False

    # Now list again (default) -> present
    rlist3 = client.get("/api/policies")
    assert rlist3.status_code == 200
    ids3 = [p["id"] for p in rlist3.json()]
    assert pid in ids3


def test_get_update_delete_404_paths():
    client = TestClient(app)

    # Get unknown
    r = client.get("/api/policies/9876543")
    assert r.status_code == 404

    # Update unknown
    r = client.patch("/api/policies/9876543", json={"description": "x"})
    assert r.status_code == 404

    # Delete unknown
    r = client.delete("/api/policies/9876543")
    assert r.status_code == 404
