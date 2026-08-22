from __future__ import annotations

import json
import uuid
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.locales import ACTIVE_CATALOG_LOCALES
from tests.support import build_profile_payload, make_test_client

PREPARE_NEW_PATH = "/api/profiles/prepare/new"
PREPARE_DUPLICATE_PATH = "/api/profiles/prepare/duplicate"
EDITOR_ROUTE_SUFFIXES = ("edit", "settings", "json")


def _prepared_payload(**overrides: object) -> dict[str, object]:
    return {
        "name": f"starter-chrome-{uuid.uuid4().hex}",
        "target_schema_id": "release-153",
        "starter_id": "basic_corporate",
        "cis_baseline_id": "none",
        "preparation_idempotency_key": uuid.uuid4().hex,
        **overrides,
    }


def _starter_fact(response):
    assert response.status_code == 200, response.text
    fact = BeautifulSoup(response.text, "html.parser").find(id="profile-starter-fact")
    assert fact is not None
    assert fact.name == "dd"
    return fact


def test_shared_chrome_renders_the_same_server_owned_starter_projection_on_all_editor_routes():
    with make_test_client() as client:
        created = client.post(PREPARE_NEW_PATH, json=_prepared_payload()).json()

        for suffix in EDITOR_ROUTE_SUFFIXES:
            fact = _starter_fact(client.get(f"/profiles/{created['id']}/{suffix}"))
            assert fact.get("data-saved-profile-starter-identity-state") == "catalog"
            assert fact.get("data-saved-profile-starter-id") == "basic_corporate"
            assert fact.get("data-saved-profile-starter-availability") == "unavailable"
            assert fact.get("data-saved-profile-starter-disposition") == "created"
            assert fact.get_text(" ", strip=True) == (
                "Saved starter preset unavailable · basic_corporate"
            )


def test_shared_chrome_renders_preserved_duplicate_provenance_as_keep_source_settings():
    with make_test_client() as client:
        source_response = client.post(PREPARE_NEW_PATH, json=_prepared_payload())
        assert source_response.status_code == 201, source_response.text
        source = source_response.json()
        duplicate_response = client.post(
            PREPARE_DUPLICATE_PATH,
            json={
                **_prepared_payload(name=f"preserved-starter-{uuid.uuid4().hex}"),
                "starter_id": "keep_current",
                "source_id": source["id"],
                "expected_source_revision": source["revision"],
            },
        )
        assert duplicate_response.status_code == 201, duplicate_response.text
        duplicate = duplicate_response.json()

        for suffix in EDITOR_ROUTE_SUFFIXES:
            fact = _starter_fact(client.get(f"/profiles/{duplicate['id']}/{suffix}"))
            assert fact.get("data-saved-profile-starter-id") == "basic_corporate"
            assert fact.get("data-saved-profile-starter-disposition") == "preserved"
            assert fact.get_text(" ", strip=True) == (
                "Keep source settings · Saved starter preset unavailable · basic_corporate"
            )


def test_shared_chrome_renders_custom_imported_state_without_flags_or_catalog_inference():
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json=build_profile_payload(
                name=f"custom-imported-starter-{uuid.uuid4().hex}",
                flags={"DisableTelemetry": True, "DisablePocket": True},
            ),
        )
        assert created_response.status_code == 201, created_response.text
        created = created_response.json()

        for suffix in EDITOR_ROUTE_SUFFIXES:
            fact = _starter_fact(client.get(f"/profiles/{created['id']}/{suffix}"))
            assert fact.get("data-saved-profile-starter-identity-state") == "custom-imported"
            assert fact.get("data-saved-profile-starter-id") is None
            assert fact.get_text(" ", strip=True) == "Custom/imported"


def test_shared_chrome_renders_firefox_import_as_custom_imported_on_a_direct_link():
    with make_test_client() as client:
        imported_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": f"imported-starter-{uuid.uuid4().hex}",
                "schema_version": "release-153",
                "document": {"policies": {"DisableTelemetry": True}},
            },
        )
        assert imported_response.status_code == 201, imported_response.text
        imported = imported_response.json()

        fact = _starter_fact(client.get(f"/profiles/{imported['id']}/settings"))
        assert fact.get("data-saved-profile-starter-identity-state") == "custom-imported"
        assert fact.get_text(" ", strip=True) == "Custom/imported"


def test_shared_chrome_starter_state_is_present_in_every_runtime_locale_without_fallback():
    with make_test_client() as client:
        created_response = client.post(
            "/api/profiles",
            json=build_profile_payload(name=f"localized-starter-{uuid.uuid4().hex}"),
        )
        assert created_response.status_code == 201, created_response.text
        profile_id = created_response.json()["id"]

        for locale in ACTIVE_CATALOG_LOCALES:
            response = client.get(
                f"/profiles/{profile_id}/edit",
                headers={"accept-language": locale},
            )
            fact = _starter_fact(response)
            catalog = json.loads(Path(f"app/i18n/{locale}.json").read_text(encoding="utf-8"))
            assert (
                fact.get_text(" ", strip=True)
                == catalog["profiles.editor_chrome_starter_custom_imported"]
            )


def test_starter_chrome_uses_only_baseline_display_and_never_reconstructs_from_flags():
    source = Path("app/templates/profiles/_page_editor_chrome.html").read_text(encoding="utf-8")

    assert 'initial_profile.get("baseline_display", {})' in source
    assert 'initial_starter_display.get("preset_id")' in source
    assert "initial_profile.flags" not in source
    assert "wizard_starter_catalog" not in source
