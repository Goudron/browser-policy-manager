from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, inspect

from app.main import app, create_app
from app.models.profile import Base, Profile
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from tests.support import build_profile_payload, make_test_client

REPO_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_runtime_profile_models_and_tables_do_not_expose_owner():
    engine = create_engine("sqlite:///:memory:", future=True)
    try:
        Base.metadata.create_all(engine)
        inspector = inspect(engine)

        assert "owner" not in Profile.__table__.columns
        assert "owner" not in ProfileCreate.model_fields
        assert "owner" not in ProfileUpdate.model_fields
        assert "owner" not in ProfileRead.model_fields

        columns = {column["name"] for column in inspector.get_columns("profiles")}
        indexes = {index["name"] for index in inspector.get_indexes("profiles")}

        assert "owner" not in columns
        assert "ix_profiles_owner" not in indexes
    finally:
        engine.dispose()


def test_profile_api_and_openapi_do_not_expose_owner():
    client = make_test_client(app)
    payload = build_profile_payload(name="Ownerless Contract")

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    profile_id = created["id"]

    get_response = client.get(f"/api/profiles/{profile_id}")
    list_response = client.get("/api/profiles", params={"q": payload["name"]})
    stats_response = client.get("/api/profiles/stats", params={"q": payload["name"]})
    patch_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={"description": "Ownerless update"},
    )

    assert "owner" not in payload
    assert "owner" not in created
    assert "owner" not in get_response.json()
    assert all("owner" not in item for item in list_response.json())
    assert "owner" not in patch_response.json()
    assert stats_response.status_code == 200, stats_response.text

    openapi = create_app().openapi()
    profile_paths = {
        path: operations
        for path, operations in openapi["paths"].items()
        if path.startswith("/api/profiles")
    }
    profile_components = {
        name: schema
        for name, schema in openapi.get("components", {}).get("schemas", {}).items()
        if name.startswith("Profile") or name.startswith("FirefoxPoliciesJsonImport")
    }
    profile_openapi_text = json.dumps(
        {
            "paths": profile_paths,
            "components": profile_components,
        },
        sort_keys=True,
    )

    assert '"owner"' not in profile_openapi_text
    assert "Filter by owner" not in profile_openapi_text


def test_active_profile_ui_templates_and_payload_code_do_not_expose_owner():
    template_paths = (
        "app/templates/profiles/_page_workspace.html",
        "app/templates/profiles/_page_json_workspace.html",
        "app/templates/profiles/_page_settings_workspace.html",
        "app/templates/profiles/_page_editor_chrome.html",
        "app/templates/profiles_compare.html",
    )
    static_paths = (
        "app/static/profiles_dom.js",
        "app/static/profiles_runtime.js",
        "app/static/profiles_workspace.js",
        "app/static/profiles_workspace_state.js",
        "app/static/profiles_wizard_flow.js",
        "app/static/profiles_library_bootstrap.js",
        "app/static/profiles_compare.js",
    )
    locale_paths = tuple(
        f"app/i18n/{locale}.json"
        for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES")
    )

    forbidden_fragments = (
        'id="profile-owner"',
        "profile-owner",
        "ownerInput",
        "form.owner",
        "payload.owner",
        "profile.owner",
        "profileOwner",
        "library-row-context-owner",
        "profiles.owner_label",
        "profiles.owner_placeholder",
        "profiles.owner_short",
        "profiles.library_owner_unassigned",
        "profiles.compare_metadata_owner",
    )

    for path in template_paths + static_paths + locale_paths:
        source = _text(path)
        for fragment in forbidden_fragments:
            assert fragment not in source, f"{fragment!r} unexpectedly found in {path}"
