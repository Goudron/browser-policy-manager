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
    assert len(items) == 1
    assert items[0]["name"] == "Default"

    # Get
    r = await client.get(f"/api/policies/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid

    # Update
    r = await client.patch(f"/api/policies/{pid}", json={"description": "Updated"})
    assert r.status_code == 200
    assert r.json()["description"] == "Updated"

    # Delete
    r = await client.delete(f"/api/policies/{pid}")
    assert r.status_code == 204

    # Ensure it's gone
    r = await client.get(f"/api/policies/{pid}")
    assert r.status_code == 404
