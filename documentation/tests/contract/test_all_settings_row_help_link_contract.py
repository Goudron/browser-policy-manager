from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONTRACT_PATH = DOCUMENTATION_ROOT / "config/all-settings-row-help-link-contract-0.9.1.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_all_settings_row_help_contract_is_scoped_and_manifest_owned() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-all-settings-row-help-link-contract-0.9.1"
    assert contract["backlog_item"] == "BPM091-M2-08"
    assert contract["target_bpm_version"] == "0.9.1"
    assert contract["status"] == "accepted"
    assert "every visible All Settings policy or setting row" in contract["purpose"]
    assert contract["audit_evidence"] == (
        "documentation/config/all-settings-documentation-target-audit-0.9.1.json"
    )

    inherited = set(contract["inherits_from"])
    assert {
        "docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md",
        "documentation/config/firefox-policy-context-targets-0.9.0.json",
        "documentation/config/navigation-tree-contract-0.9.1.json",
        "documentation/config/documentation-sufficiency-review-protocol-0.9.1.json",
    } <= inherited

    source_surfaces = set(contract["source_surfaces"])
    assert {
        "app/static/profiles_all_settings_list.js",
        "app/static/profiles_settings_inventory.js",
        "app/static/profiles_settings_search.js",
        "app/templates/profiles/_context_help_icon.html",
        "app/documentation/manifest.py",
        "documentation/tools/build_docs.py",
    } <= source_surfaces


def test_all_settings_contract_covers_visible_rows_locales_and_dispositions() -> None:
    contract = _contract()

    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]

    row_scope = contract["row_scope"]
    visible = " ".join(row_scope["visible_surfaces"])
    for expected in (
        "review rows",
        "configured rows",
        "catalog rows",
        "search-result rows",
        "long localized labels",
    ):
        assert expected in visible

    must_cover = " ".join(row_scope["must_cover"])
    for expected in (
        "Firefox policy rows",
        "known managed-preference rows",
        "raw fallback rows",
        "unknown imported rows",
        "invalid rows",
        "deprecated rows",
        "unavailable, stale, incomplete, or incompatible",
        "missing from the manifest ui-target-map",
    ):
        assert expected in must_cover

    dispositions = set(contract["target_resolution"]["valid_dispositions"])
    assert {
        "linked",
        "not_applicable_raw",
        "unsupported_unknown",
        "missing_documentation",
        "artifact_unavailable",
        "artifact_stale",
        "artifact_incomplete",
        "artifact_incompatible",
    } == dispositions


def test_all_settings_contract_maps_policy_preferences_raw_and_unknown_entries() -> None:
    contract = _contract()
    rules = {rule["entry_kind"]: rule for rule in contract["target_resolution"]["rules"]}

    assert rules["firefox_policy"]["target_id"] == "policy:{exact_policy_id}"
    assert rules["firefox_policy"]["fallback_disposition"] == "missing_documentation"
    assert (
        rules["known_managed_preference"]["target_id"] == "known-preference:{exact.preference.id}"
    )
    assert rules["known_managed_preference"]["fallback_disposition"] == "missing_documentation"
    assert "policy:{exact_policy_id}" in rules["generated_policy_or_preference"]["target_id"]
    assert (
        "known-preference:{exact.preference.id}"
        in rules["generated_policy_or_preference"]["target_id"]
    )
    assert rules["raw_fallback"]["target_id"] is None
    assert rules["raw_fallback"]["fallback_disposition"] == "not_applicable_raw"
    assert rules["unknown_imported"]["target_id"] is None
    assert rules["unknown_imported"]["fallback_disposition"] == "unsupported_unknown"

    resolution = contract["target_resolution"]
    assert "must not imply that the setting value is valid" in resolution["invalid_rows"]
    assert (
        "Deprecated rows still link when a manifest target exists" in resolution["deprecated_rows"]
    )
    assert "must not emit broken anchors" in resolution["missing_docs"]
    assert "unavailable, stale, incomplete, or incompatible" in resolution["unavailable_artifacts"]


def test_all_settings_contract_defines_safe_row_layout_and_link_markup() -> None:
    contract = _contract()
    ui = contract["ui_contract"]

    assert "circled letter i" in ui["control"]
    assert ui["class_name"] == "all-settings-row-help-link"
    assert ui["style_source"] == ".context-help-icon-link"
    assert "right side" in ui["placement"]
    assert "must not be nested inside an all-settings row button" in ui["interactive_markup"]
    assert "sibling interactive controls" in ui["interactive_markup"]

    linked = ui["linked_state"]
    assert linked["element"] == "a"
    assert linked["target"] == "_blank"
    assert linked["rel"] == "noopener noreferrer"
    assert linked["text"] == "i"
    assert {
        "data-documentation-links",
        "data-all-settings-help-target",
        "data-settings-entry-id",
        "data-settings-entry-kind",
        "data-settings-entry-help-disposition",
    } <= set(linked["data_attributes"])

    no_link = ui["no_link_state"]
    assert "button-free status indicator" in no_link["element"]
    assert "localized unavailable or not-applicable description" in no_link["aria"]

    layout = " ".join(ui["layout_stability"])
    for expected in ("row height", "light, dark, system", "Long localized labels", "overlapping"):
        assert expected in layout


def test_all_settings_contract_requires_localized_accessible_keyboard_behavior() -> None:
    contract = _contract()
    accessibility = contract["accessibility"]

    assert {
        "profiles.all_settings.row_help.open",
        "profiles.all_settings.row_help.missing",
        "profiles.all_settings.row_help.unavailable",
        "profiles.all_settings.row_help.raw_not_applicable",
        "profiles.all_settings.row_help.unknown_not_supported",
    } <= set(accessibility["localized_accessible_names"])

    keyboard = " ".join(accessibility["keyboard"])
    for expected in (
        "separate controls",
        "selects the row",
        "opens the manifest-resolved documentation URL",
        "must not steal selection focus",
        "forced-colors",
    ):
        assert expected in keyboard

    screen_reader = " ".join(accessibility["screen_reader"])
    assert "localized row label or exact policy/preference ID" in screen_reader
    assert "without exposing raw target-map internals" in screen_reader
    assert "aria-hidden" in screen_reader


def test_all_settings_contract_validates_manifest_targets_and_future_tasks() -> None:
    contract = _contract()
    validation = contract["manifest_validation"]

    assert validation["target_namespaces"] == ["policy:", "known-preference:"]
    requirements = " ".join(validation["requirements"])
    for expected in (
        "Every linked row target ID must exist",
        "not translated labels or generated URLs",
        "one of the valid no-link dispositions",
        "active locale output",
        "fail closed for broken target IDs",
    ):
        assert expected in requirements

    assert contract["implementation_tasks"] == [
        "BPM091-M9-01",
        "BPM091-M9-02",
        "BPM091-M9-03",
        "BPM091-M9-04",
        "BPM091-M9-05",
        "BPM091-M9-06",
        "BPM091-M13-06",
    ]
    m9_05 = contract["implementation_evidence"]["BPM091-M9-05"]
    assert m9_05["status"] == "accepted"
    assert set(m9_05["no_link_dispositions"]) == {
        "not_applicable_raw",
        "unsupported_unknown",
        "missing_documentation",
        "artifact_unavailable",
        "artifact_stale",
        "artifact_incomplete",
        "artifact_incompatible",
    }
    m9_06 = contract["implementation_evidence"]["BPM091-M9-06"]
    assert m9_06["status"] == "accepted"
    assert "Review, Configured, and Catalog modes" in m9_06["browser_coverage"]
    assert "unknown and raw no-link rows" in m9_06["browser_coverage"]
    assert "separate keyboard focus and Enter activation" in m9_06["browser_coverage"]
    assert m9_06["browser_test"].endswith(
        "::test_all_settings_row_help_links_cover_modes_locales_search_and_keyboard"
    )
    assert "make test-docs-browser" in contract["verification"]["release_gates"]
    assert (
        "This contract does not implement the All Settings row help-link UI."
        in contract["non_goals"]
    )
