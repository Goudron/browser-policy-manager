import pytest


@pytest.mark.anyio
async def test_create_list_get_update_delete(client):
    # Create
    r = await client.post(
        "/api/policies",
        json={
            "name": "Default",
            "description": "Base profile",
            "schema_version": "firefox-ESR",
            "flags": {"DisableTelemetry": True},
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()
    pid = created["id"]

    # List
    r = await client.get("/api/policies")
    assert r.status_code == 200
    items = r.json()

    # We no longer assume the database is empty, only that our item is present.
    assert any(p["id"] == pid for p in items)
    assert any(p["id"] == pid and p["name"] == "Default" for p in items)

    # Get
    r = await client.get(f"/api/policies/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid

    # Update
    r = await client.patch(f"/api/policies/{pid}", json={"description": "Updated"})
    assert r.status_code == 200
    assert r.json()["description"] == "Updated"

    # Delete (soft delete)
    r = await client.delete(f"/api/policies/{pid}")
    assert r.status_code in (204, 200)

    # Verify behavior after delete:
    # depending on API semantics this may be 404 or 200 with deleted=True.
    r = await client.get(f"/api/policies/{pid}")
    assert r.status_code in (404, 200)
    if r.status_code == 200:
        data = r.json()
        assert data["id"] == pid
        # current API exposes soft-delete flag as "deleted"
        assert data.get("deleted") is True
