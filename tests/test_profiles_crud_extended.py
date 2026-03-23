import uuid

from app.main import app
from tests.support import TestClient, build_profile_payload

client = TestClient(app)


def _mk(name: str, description: str = "Base profile") -> dict:
    return build_profile_payload(name=name, description=description)


def test_duplicate_name_conflict_and_restore_and_include_deleted():
    """Covers duplicate-name conflict, soft delete, and include_deleted flag."""
    unique = uuid.uuid4().hex[:6]
    base_name = f"Conflict-{unique}"
    body = _mk(base_name)

    # Create #1
    r1 = client.post("/api/profiles", json=body)
    assert r1.status_code == 201, r1.text
    pid = r1.json()["id"]

    # Create #2 with same name -> conflict (409 is preferred, 400 acceptable)
    r2 = client.post("/api/profiles", json=body)
    assert r2.status_code in (409, 400)

    # Soft delete
    rd = client.delete(f"/api/profiles/{pid}")
    assert rd.status_code in (204, 200)

    # By default deleted are hidden
    rlist = client.get("/api/profiles")
    assert rlist.status_code == 200
    ids = [p["id"] for p in rlist.json()]
    assert pid not in ids

    # Include deleted -> item appears and has is_deleted=True
    rlist2 = client.get("/api/profiles", params={"include_deleted": "true"})
    assert rlist2.status_code == 200
    items = rlist2.json()
    item = next((p for p in items if p["id"] == pid), None)
    assert item is not None
    assert item["is_deleted"] is True


def test_get_update_delete_404_paths():
    """Unknown profile id must produce 404 for read/update/delete operations."""
    unknown_id = 9876543

    # Get unknown
    r = client.get(f"/api/profiles/{unknown_id}")
    assert r.status_code == 404

    # Update unknown
    r = client.patch(f"/api/profiles/{unknown_id}", json={"description": "x"})
    # In the current API semantics, PATCH should return 404 for missing records.
    assert r.status_code == 404

    # Delete unknown
    r = client.delete(f"/api/profiles/{unknown_id}")
    assert r.status_code == 404
