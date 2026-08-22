"""M5-06 guard for the saved-profile facts shared by all editor chrome routes."""

from __future__ import annotations

import uuid
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.locales import ACTIVE_CATALOG_LOCALES
from tests.support import make_test_client

EDITOR_SUFFIXES = ("edit", "settings", "json")
FACT_IDS = ("profile-schema-fact", "profile-starter-fact", "profile-cis-fact")
FORBIDDEN_CONTROL_IDS = {
    "profile-type",
    "wizard-name",
    "wizard-schema",
    "wizard-mode",
    "wizard-starter",
    "wizard-cis",
}
FORBIDDEN_MUTATION_FIELDS = {
    "schema_version",
    "target_schema_id",
    "starter_id",
    "cis_baseline_id",
    "baseline_provenance",
    "baseline_display",
    "extension_provenance",
}


def _create_prepared_profile(client) -> dict[str, object]:
    response = client.post(
        "/api/profiles/prepare/new",
        json={
            "name": f"shared-chrome-{uuid.uuid4().hex}",
            "target_schema_id": "release-153",
            "starter_id": "basic_corporate",
            "cis_baseline_id": "cis_l2",
            "preparation_idempotency_key": uuid.uuid4().hex,
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


def _fact_snapshot(soup: BeautifulSoup) -> dict[str, dict[str, str | None]]:
    snapshot: dict[str, dict[str, str | None]] = {}
    for fact_id in FACT_IDS:
        fact = soup.find(id=fact_id)
        assert fact is not None
        assert fact.name == "dd"
        assert fact.parent is not None
        assert fact.parent.name == "div"
        assert fact.parent.find("dt") is not None
        snapshot[fact_id] = {
            "text": fact.get_text(" ", strip=True),
            "schema": fact.get("data-saved-profile-schema"),
            "starter_identity_state": fact.get("data-saved-profile-starter-identity-state"),
            "starter_id": fact.get("data-saved-profile-starter-id"),
            "starter_availability": fact.get("data-saved-profile-starter-availability"),
            "starter_disposition": fact.get("data-saved-profile-starter-disposition"),
            "cis_identity_state": fact.get("data-saved-profile-cis-identity-state"),
            "cis_status": fact.get("data-saved-profile-cis-display-status"),
            "cis_baseline_id": fact.get("data-saved-profile-cis-baseline-id"),
            "cis_current_claim": fact.get("data-saved-profile-cis-current-claim"),
            "cis_reason": fact.get("data-saved-profile-cis-reason-code"),
        }
    return snapshot


def test_shared_editor_chrome_has_api_to_dom_parity_without_mutable_baseline_controls() -> None:
    with make_test_client() as client:
        created = _create_prepared_profile(client)
        profile_id = created["id"]
        api = client.get(f"/api/profiles/{profile_id}")
        assert api.status_code == 200, api.text
        saved = api.json()

        baseline = saved["baseline_display"]
        starter = baseline["starter"]
        cis = baseline["cis"]
        expected = {
            "profile-schema-fact": {
                "schema": saved["schema_version"],
                "starter_identity_state": None,
                "starter_id": None,
                "starter_availability": None,
                "starter_disposition": None,
                "cis_identity_state": None,
                "cis_status": None,
                "cis_baseline_id": None,
                "cis_current_claim": None,
                "cis_reason": None,
            },
            "profile-starter-fact": {
                "schema": None,
                "starter_identity_state": starter["identity_state"],
                "starter_id": starter["preset_id"],
                "starter_availability": starter["availability"],
                "starter_disposition": starter["disposition"],
                "cis_identity_state": None,
                "cis_status": None,
                "cis_baseline_id": None,
                "cis_current_claim": None,
                "cis_reason": None,
            },
            "profile-cis-fact": {
                "schema": None,
                "starter_identity_state": None,
                "starter_id": None,
                "starter_availability": None,
                "starter_disposition": None,
                "cis_identity_state": cis["identity_state"],
                "cis_status": cis["display_status"],
                "cis_baseline_id": cis["baseline_id"],
                "cis_current_claim": str(cis["current_claim"]).lower(),
                "cis_reason": cis["reason_code"],
            },
        }

        route_snapshots: list[dict[str, dict[str, str | None]]] = []
        for suffix in EDITOR_SUFFIXES:
            response = client.get(f"/profiles/{profile_id}/{suffix}")
            assert response.status_code == 200, response.text
            soup = BeautifulSoup(response.text, "html.parser")
            route_snapshots.append(_fact_snapshot(soup))

            overview = soup.find(id="overview-panel")
            assert overview is not None
            assert overview.select("[contenteditable=true]") == []
            assert not {node.get("id") for node in overview.select("[id]")} & FORBIDDEN_CONTROL_IDS
            assert not overview.select(
                "#profile-type, #wizard-schema, #wizard-starter, #wizard-cis, "
                "input[name=schema_version], input[name=target_schema_id], "
                "input[name=starter_id], input[name=cis_baseline_id], "
                "input[name=baseline_provenance], input[name=baseline_display], "
                "input[name=extension_provenance]"
            )

            for fact_id, values in expected.items():
                actual = route_snapshots[-1][fact_id]
                for key, expected_value in values.items():
                    assert actual[key] == expected_value

        assert route_snapshots[1:] == [route_snapshots[0], route_snapshots[0]]


def test_shared_editor_chrome_uses_all_authored_locales_without_a_baseline_fallback() -> None:
    with make_test_client() as client:
        created = _create_prepared_profile(client)
        profile_id = created["id"]

        for locale in ACTIVE_CATALOG_LOCALES:
            catalog = client.get(f"/i18n/{locale}.json").json()
            route_snapshots = []
            for suffix in EDITOR_SUFFIXES:
                response = client.get(
                    f"/profiles/{profile_id}/{suffix}",
                    headers={"Accept-Language": locale},
                )
                assert response.status_code == 200, response.text
                soup = BeautifulSoup(response.text, "html.parser")
                assert soup.html is not None
                assert soup.html.get("lang") == locale
                route_snapshots.append(_fact_snapshot(soup))

                for key in (
                    "profiles.schema_label",
                    "profiles.editor_chrome_starter_label",
                    "profiles.editor_chrome_cis_label",
                ):
                    assert catalog[key] in response.text

            assert route_snapshots[1:] == [route_snapshots[0], route_snapshots[0]]


def test_editor_update_payload_and_authored_responsive_css_keep_baseline_read_only() -> None:
    workspace_state = Path("app/static/profiles_modules/workspace_state.mjs").read_text(
        encoding="utf-8"
    )
    workspace_css = Path("app/static/profiles_css/23-workspace-editor.css").read_text(
        encoding="utf-8"
    )
    responsive_css = Path("app/static/profiles_css/30-responsive.css").read_text(encoding="utf-8")

    update_function = workspace_state.split("export function buildUpdatePayload", 1)[1].split(
        "export function", 1
    )[0]
    assert not any(field in update_function for field in FORBIDDEN_MUTATION_FIELDS)
    assert "schema_version" not in update_function

    for declaration in (
        ".editor-chrome-fields {",
        "grid-template-columns: minmax(0, 1fr) minmax(180px, 0.62fr);",
        ".editor-chrome-facts {",
        "min-width: 0;",
        ".editor-chrome-fact-value {",
        "overflow-wrap: anywhere;",
    ):
        assert declaration in workspace_css

    assert "@media (max-width: 560px)" in responsive_css
    assert ".editor-chrome-fields" in responsive_css
    assert "grid-template-columns: 1fr;" in responsive_css
