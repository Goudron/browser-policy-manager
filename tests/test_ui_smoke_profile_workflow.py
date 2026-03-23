from __future__ import annotations

import uuid

from app.main import app
from tests.support import TestClient


def _make_payload() -> dict:
    unique = uuid.uuid4().hex[:8]
    return {
        "name": f"UI-{unique}",
        "description": "UI smoke lifecycle profile",
        "schema_version": "esr-140",
        "owner": "ops@example.org",
        "flags": {
            "DisableTelemetry": True,
            "DisablePrivateBrowsing": True,
        },
    }


def test_profiles_ui_shell_and_public_workflow_smoke():
    client = TestClient(app)

    # Load the actual UI shell first and verify the page exposes the hooks and
    # routes the browser depends on.
    page = client.get("/profiles")
    assert page.status_code == 200, page.text
    assert page.headers["content-type"].startswith("text/html")
    html = page.text

    for token in (
        'id="profile-name"',
        'id="profile-owner"',
        'id="profile-description"',
        'id="editor"',
        'id="save"',
        'id="validate"',
        'id="download-json"',
        'id="download-yaml"',
        'id="workspace-signal"',
        "/api/profiles",
        "/api/export/profiles",
        "/api/validate/",
        "/i18n/${lang}.json",
        "Ctrl/Cmd+S to save",
    ):
        assert token in html

    locale = client.get("/i18n/en.json")
    assert locale.status_code == 200, locale.text
    locale_json = locale.json()
    for key in (
        "profiles.title",
        "profiles.create_submit",
        "profiles.signal_dirty",
        "profiles.validation_ok",
    ):
        assert key in locale_json

    payload = _make_payload()

    # This is the same public flow the UI drives: validate draft -> create ->
    # patch/save -> export -> delete -> restore.
    validate_before = client.post(
        f"/api/validate/{payload['schema_version']}",
        json={"document": payload["flags"]},
    )
    assert validate_before.status_code == 200, validate_before.text
    assert validate_before.json()["ok"] is True

    created_response = client.post("/api/profiles", json=payload)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    profile_id = created["id"]

    updated_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved from UI smoke",
            "owner": "sec@example.org",
            "flags": {"DisableTelemetry": False},
        },
    )
    assert updated_response.status_code == 200, updated_response.text
    updated = updated_response.json()
    assert updated["description"] == "Saved from UI smoke"
    assert updated["flags"]["DisableTelemetry"] is False
    assert updated["flags"]["DisablePrivateBrowsing"] is True

    list_response = client.get("/api/profiles", params={"q": payload["name"]})
    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == profile_id for item in list_response.json())

    export_json = client.get(f"/api/export/profiles/{profile_id}.json")
    assert export_json.status_code == 200, export_json.text
    assert export_json.json()["id"] == profile_id

    export_yaml = client.get(f"/api/export/profiles/{profile_id}?fmt=yaml")
    assert export_yaml.status_code == 200, export_yaml.text
    assert "DisableTelemetry" in export_yaml.text

    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code in (200, 204)

    hidden_export = client.get(f"/api/export/profiles/{profile_id}?fmt=json")
    assert hidden_export.status_code == 404

    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200, restore_response.text
    restored = restore_response.json()
    assert restored["is_deleted"] is False

    restored_export = client.get(f"/api/export/profiles/{profile_id}.yaml")
    assert restored_export.status_code == 200, restored_export.text
    assert "DisablePrivateBrowsing" in restored_export.text
