import pytest


@pytest.mark.anyio
async def test_create_list_get_update_delete(client):
    # Create
    r = await client.post(
        "/api/profiles",
        json={
            "name": "Default",
            "description": "Base profile",
            "schema_version": "esr-140.9",
            "flags": {"DisableTelemetry": True},
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()
    pid = created["id"]

    # List
    r = await client.get("/api/profiles")
    assert r.status_code == 200
    items = r.json()

    # We no longer assume the database is empty, only that our item is present.
    assert any(p["id"] == pid for p in items)
    assert any(p["id"] == pid and p["name"] == "Default" for p in items)

    # Get
    r = await client.get(f"/api/profiles/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid

    # Update
    r = await client.patch(f"/api/profiles/{pid}", json={"description": "Updated"})
    assert r.status_code == 200
    assert r.json()["description"] == "Updated"

    # Explicit null clears nullable fields instead of silently keeping stale values.
    r = await client.patch(f"/api/profiles/{pid}", json={"description": None})
    assert r.status_code == 200
    assert r.json()["description"] is None

    # Delete (soft delete)
    r = await client.delete(f"/api/profiles/{pid}")
    assert r.status_code == 204

    # Deleted profiles are hidden from the default GET route.
    r = await client.get(f"/api/profiles/{pid}")
    assert r.status_code == 404
