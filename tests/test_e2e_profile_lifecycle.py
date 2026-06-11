from __future__ import annotations

import uuid

from app.main import app
from tests.support import make_test_client


def _make_profile_payload() -> dict:
    unique = uuid.uuid4().hex[:8]
    return {
        "name": f"E2E-{unique}",
        "description": "End-to-end lifecycle profile",
        "schema_version": "esr-140.11",
        "flags": {
            "DisableTelemetry": True,
            "DisablePrivateBrowsing": True,
        },
    }


def test_profile_lifecycle_create_validate_save_export_delete_restore():
    client = make_test_client(app)

    payload = _make_profile_payload()

    # Validate the draft payload before creation.
    validate_before = client.post(
        f"/api/validate/{payload['schema_version']}",
        json={"document": payload["flags"]},
    )
    assert validate_before.status_code == 200, validate_before.text
    assert validate_before.json()["ok"] is True

    # Create the profile through the canonical API.
    created_response = client.post("/api/profiles", json=payload)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    profile_id = created["id"]
    assert created["name"] == payload["name"]
    assert created["is_deleted"] is False

    # Update metadata and flags. PATCH replaces flags so UI removals persist.
    patch_payload = {
        "description": "Updated in lifecycle flow",
        "flags": {
            "DisableTelemetry": False,
        },
    }
    updated_response = client.patch(f"/api/profiles/{profile_id}", json=patch_payload)
    assert updated_response.status_code == 200, updated_response.text
    updated = updated_response.json()
    assert updated["description"] == "Updated in lifecycle flow"
    assert updated["flags"] == {
        "DisableTelemetry": False,
    }

    # Validate the updated profile payload via the public validation endpoint.
    validate_after = client.post(
        "/api/validate/esr-140.11",
        json={"document": updated["flags"]},
    )
    assert validate_after.status_code == 200, validate_after.text
    assert validate_after.json()["ok"] is True

    # Export the current profile as Firefox policies.json.
    export_firefox = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert export_firefox.status_code == 200, export_firefox.text
    assert export_firefox.json() == {
        "policies": {
            "DisableTelemetry": False,
        }
    }

    # Soft-delete the profile and ensure normal reads/exports hide it.
    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/profiles/{profile_id}")
    assert get_deleted.status_code == 404

    export_hidden = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert export_hidden.status_code == 404

    export_deleted = client.get(
        f"/api/export/profiles/{profile_id}/firefox/policies.json?include_deleted=true"
    )
    assert export_deleted.status_code == 200, export_deleted.text
    assert export_deleted.json() == {
        "policies": {
            "DisableTelemetry": False,
        }
    }

    # Restore and verify the profile becomes active again.
    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200, restore_response.text
    restored = restore_response.json()
    assert restored["id"] == profile_id
    assert restored["is_deleted"] is False

    get_restored = client.get(f"/api/profiles/{profile_id}")
    assert get_restored.status_code == 200, get_restored.text
    restored_profile = get_restored.json()
    assert restored_profile["is_deleted"] is False

    # Final list read confirms the restored profile participates in the library.
    list_response = client.get("/api/profiles", params={"q": payload["name"]})
    assert list_response.status_code == 200, list_response.text
    items = list_response.json()
    assert any(item["id"] == profile_id and item["is_deleted"] is False for item in items)
