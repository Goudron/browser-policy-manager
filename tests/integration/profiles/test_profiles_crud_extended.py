import uuid

from app.main import app
from tests.support import build_profile_payload, make_test_client

PROFILE_READ_FIELDS = {
    "id",
    "name",
    "description",
    "schema_version",
    "flags",
    "compliance",
    "revision",
    "created_at",
    "updated_at",
    "deleted_at",
    "is_deleted",
    "validation_state",
    "recommendation",
}


def _mk(name: str, description: str = "Base profile") -> dict:
    return build_profile_payload(name=name, description=description)


def _make_client():
    return make_test_client(app)


def test_duplicate_name_conflict_and_restore_and_include_deleted():
    """Covers duplicate-name conflict, soft delete, and include_deleted flag."""
    client = _make_client()
    unique = uuid.uuid4().hex[:6]
    base_name = f"Conflict-{unique}"
    body = _mk(base_name)

    # Create #1
    r1 = client.post("/api/profiles", json=body)
    assert r1.status_code == 201, r1.text
    created = r1.json()
    assert set(created) == PROFILE_READ_FIELDS
    assert created["name"] == base_name
    assert created["is_deleted"] is False
    assert created["deleted_at"] is None
    pid = created["id"]
    revision_before_lifecycle_changes = created["revision"]

    # Create #2 with same name -> conflict
    r2 = client.post("/api/profiles", json=body)
    assert r2.status_code == 409

    # Soft delete
    rd = client.delete(f"/api/profiles/{pid}")
    assert rd.status_code == 204
    assert rd.content == b""

    hidden_get = client.get(f"/api/profiles/{pid}")
    assert hidden_get.status_code == 404

    hidden_export = client.get(f"/api/export/profiles/{pid}/firefox/policies.json")
    assert hidden_export.status_code == 404

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
    assert item["deleted_at"] is not None
    assert item["revision"] == revision_before_lifecycle_changes

    archived = client.get("/api/profiles", params={"lifecycle": "archived"})
    assert archived.status_code == 200
    assert any(item["id"] == pid and item["is_deleted"] for item in archived.json())

    deleted_get = client.get(f"/api/profiles/{pid}", params={"include_deleted": "true"})
    assert deleted_get.status_code == 200
    assert deleted_get.json()["is_deleted"] is True

    restored = client.post(f"/api/profiles/{pid}/restore")
    assert restored.status_code == 200, restored.text
    assert restored.json()["is_deleted"] is False
    assert restored.json()["deleted_at"] is None
    assert restored.json()["revision"] == revision_before_lifecycle_changes

    active_get = client.get(f"/api/profiles/{pid}")
    assert active_get.status_code == 200
    assert active_get.json()["name"] == base_name


def test_get_update_delete_404_paths():
    """Unknown profile id must produce 404 for read/update/delete operations."""
    client = _make_client()
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

    # Hard-delete unknown
    r = client.delete(f"/api/profiles/{unknown_id}/hard")
    assert r.status_code == 404


def test_hard_delete_profile_and_reset_library():
    client = _make_client()
    unique = uuid.uuid4().hex[:6]
    body_one = _mk(f"Hard-{unique}-1")
    body_two = _mk(f"Hard-{unique}-2")

    r1 = client.post("/api/profiles", json=body_one)
    r2 = client.post("/api/profiles", json=body_two)
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text
    pid = r1.json()["id"]

    rh = client.delete(f"/api/profiles/{pid}/hard")
    assert rh.status_code == 204

    rget = client.get(f"/api/profiles/{pid}")
    assert rget.status_code == 404

    rlist_inc = client.get("/api/profiles", params={"include_deleted": "true"})
    assert rlist_inc.status_code == 200
    ids_inc = {item["id"] for item in rlist_inc.json()}
    assert pid not in ids_inc

    rreset = client.delete("/api/profiles/reset")
    assert rreset.status_code == 200, rreset.text
    assert "deleted" in rreset.json()

    rlist = client.get("/api/profiles", params={"include_deleted": "true"})
    assert rlist.status_code == 200
    assert rlist.json() == []


def test_profile_library_stats_reports_filtered_and_total():
    client = _make_client()
    unique = uuid.uuid4().hex[:6]
    first = client.post(
        "/api/profiles", json=_mk(f"Stats-{unique}-Alpha", description="Visible alpha")
    )
    second = client.post(
        "/api/profiles", json=_mk(f"Stats-{unique}-Beta", description="Visible beta")
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    first_id = first.json()["id"]
    second_id = second.json()["id"]

    deleted = client.delete(f"/api/profiles/{second_id}")
    assert deleted.status_code == 204

    stats_active = client.get("/api/profiles/stats", params={"q": "Alpha"})
    assert stats_active.status_code == 200, stats_active.text
    assert stats_active.json()["filtered"] == 1
    assert stats_active.json()["total"] >= 1

    stats_with_deleted = client.get(
        "/api/profiles/stats",
        params={"q": unique, "include_deleted": "true"},
    )
    assert stats_with_deleted.status_code == 200, stats_with_deleted.text
    assert stats_with_deleted.json()["filtered"] >= 2
    assert stats_with_deleted.json()["total"] >= stats_with_deleted.json()["filtered"]

    stats_archived = client.get(
        "/api/profiles/stats",
        params={"q": unique, "lifecycle": "archived"},
    )
    assert stats_archived.status_code == 200, stats_archived.text
    assert stats_archived.json()["filtered"] == 1

    stats_valid = client.get(
        "/api/profiles/stats",
        params={"q": unique, "validation_state": "valid", "lifecycle": "all"},
    )
    assert stats_valid.status_code == 200, stats_valid.text
    assert stats_valid.json()["filtered"] >= 2

    cleanup_first = client.delete(f"/api/profiles/{first_id}/hard")
    cleanup_second = client.delete(f"/api/profiles/{second_id}/hard")
    assert cleanup_first.status_code == 204
    assert cleanup_second.status_code == 204


def test_profile_list_keeps_array_shape_and_carries_matching_summary_headers():
    client = _make_client()
    unique = uuid.uuid4().hex[:6]
    first = client.post("/api/profiles", json=_mk(f"Page-{unique}-Alpha"))
    second = client.post("/api/profiles", json=_mk(f"Page-{unique}-Beta"))
    assert first.status_code == second.status_code == 201

    archived = client.delete(f"/api/profiles/{second.json()['id']}")
    assert archived.status_code == 204

    response = client.get(
        "/api/profiles",
        params={"q": unique, "lifecycle": "all", "limit": 1, "offset": 1, "sort": "name"},
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1
    assert response.headers["X-BPM-Profile-Filtered"] == "2"
    assert response.headers["X-BPM-Profile-Total"] == "2"

    stats = client.get("/api/profiles/stats", params={"q": unique, "lifecycle": "all"})
    assert stats.status_code == 200, stats.text
    assert stats.json() == {"filtered": 2, "total": 2}
