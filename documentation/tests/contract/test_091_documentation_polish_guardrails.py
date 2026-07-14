from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONFIG_ROOT = DOCUMENTATION_ROOT / "config"
GUARDRAILS = CONFIG_ROOT / "documentation-polish-guardrails-0.9.1.json"
SCREENSHOT_MATRIX = CONFIG_ROOT / "user-guide-screenshot-matrix-0.9.1.json"
SEARCH_UI_CONTRACT = CONFIG_ROOT / "search-ui-filter-contract-0.9.1.json"
SEARCH_FACETS_CONTRACT = CONFIG_ROOT / "search-facets-filters-0.9.0.json"
NAVIGATION_CONTRACT = CONFIG_ROOT / "navigation-tree-contract-0.9.1.json"
ALL_SETTINGS_CONTRACT = CONFIG_ROOT / "all-settings-row-help-link-contract-0.9.1.json"
THEME_CONTRACT = REPOSITORY_ROOT / "docs/architecture/product-documentation-visual-theme-contract-0.9.1.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_text(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _guard(guard_id: str) -> dict[str, object]:
    guards = {guard["id"]: guard for guard in _json(GUARDRAILS)["guards"]}
    return guards[guard_id]


def test_guardrail_fixture_declares_every_accepted_failure_mode() -> None:
    guardrails = _json(GUARDRAILS)

    assert guardrails["schema_version"] == 1
    assert guardrails["guardrail_id"] == "bpm-0.9.1-documentation-polish-guardrails"
    assert guardrails["backlog_item"] == "BPM091-M2-09"
    assert guardrails["target_bpm_version"] == "0.9.1"
    assert guardrails["status"] == "accepted"

    expected = {
        "user-guide-screenshot-matrix-complete",
        "localized-search-filter-labels",
        "navigation-tree-no-duplicate-guide-titles",
        "light-theme-no-pure-white-primary-surfaces",
        "all-settings-row-help-disposition",
    }
    guards = {guard["id"]: guard for guard in guardrails["guards"]}
    assert set(guards) == expected

    for guard in guards.values():
        assert guard["failure_mode"]
        assert guard["fails_when"]
        assert guard["current_check"].startswith(
            "documentation/tests/contract/test_091_documentation_polish_guardrails.py::"
        )
        assert guard["source_files"]
        assert guard["implementation_tasks"]
        assert "make test-release" in guard["release_gates"]


def test_guardrail_fails_for_missing_screenshot_matrix_rows() -> None:
    guard = _guard("user-guide-screenshot-matrix-complete")
    matrix = _json(SCREENSHOT_MATRIX)
    scenarios = {scenario["scenario_id"]: scenario for scenario in matrix["scenarios"]}
    rows = matrix["matrix"]

    assert guard["failure_mode"] == "missing screenshot matrix rows"
    assert matrix["locales"] == list(LOCALES)
    assert set(guard["source_files"]) == {
        "documentation/config/user-guide-screenshot-matrix-0.9.1.json"
    }

    expected_pairs = {(scenario_id, locale) for scenario_id in scenarios for locale in LOCALES}
    actual_pairs = {(row["scenario_id"], row["locale"]) for row in rows}
    assert actual_pairs == expected_pairs

    for row in rows:
        scenario = scenarios[row["scenario_id"]]
        assert row["id"] == f"{row['scenario_id']}-{row['locale']}"
        assert row["guide_id"] == "user-guide"
        assert row["topic_id"] == scenario["topic_id"]
        assert row["route"] == scenario["route"]
        assert row["fixture_state"] == scenario["fixture_state"]
        assert row["asset_path"] == (
            f"documentation/assets/screenshots/{row['locale']}/{row['filename']}"
        )
        assert row["caption_key"] == scenario["caption_key"]
        assert row["alt_text_key"] == scenario["alt_text_key"]


def test_guardrail_fails_for_localized_search_filter_english_fallback() -> None:
    guard = _guard("localized-search-filter-labels")
    search = _json(SEARCH_UI_CONTRACT)
    facets = _json(SEARCH_FACETS_CONTRACT)["facet_fields"]
    labels = search["localized_labels"]
    examples = search["label_examples"]
    visible = set(labels["visible_facets"])

    assert guard["failure_mode"] == "English filter labels in localized search"
    assert "English fallback is not allowed in non-English locales" in labels["fallback_policy"]
    assert visible == set(facets) - {"locale", "bpm_version"}

    english_labels = examples["en"]["field_labels"]
    assert set(english_labels) == visible
    for locale in LOCALES:
        assert set(examples[locale]["field_labels"]) == visible
    for locale in LOCALES:
        if locale == "en":
            continue
        for field in visible:
            localized = examples[locale]["field_labels"][field]
            assert localized
            assert localized != field
            assert localized != facets[field]["label"]
            assert localized != english_labels[field]


def test_guardrail_fails_for_duplicate_titles_and_broken_root_return() -> None:
    guard = _guard("navigation-tree-no-duplicate-guide-titles")
    navigation = _json(NAVIGATION_CONTRACT)

    assert guard["failure_mode"] == "duplicate guide titles and broken root return"
    assert navigation["tree_model"]["root_node"]["href"] == "/help/{locale}/"
    assert navigation["display_rules"]["primary_left_navigation"].startswith(
        "The left navigation is the authoritative place"
    )
    assert "must not be repeated" in navigation["display_rules"]["no_duplicate_guide_title"]
    assert "topic title or documentation home title" in navigation["display_rules"]["topic_heading_rule"]

    active = navigation["active_state"]
    assert active["root_page"]["current_node"] == "documentation-root"
    assert "derive current state from translated labels" in active["must_not"]
    assert "collapse the current topic's ancestors" in active["must_not"]

    returns = navigation["return_behavior"]
    assert "locale documentation root" in returns["root_link"]
    assert "guide's landing topic" in returns["guide_link"]
    assert "direct topic URL expands" in returns["direct_url"]


def test_guardrail_registers_pure_white_source_checks_for_theme_implementation() -> None:
    guard = _guard("light-theme-no-pure-white-primary-surfaces")
    contract = _normalized_text(THEME_CONTRACT)

    assert guard["failure_mode"] == "pure-white light theme surfaces"
    assert guard["current_mode"] == "contract-fixture-before-m3-source-scan"
    assert {"#ffffff", "white", "rgb(255, 255, 255)"} <= set(
        guard["forbidden_primary_surface_tokens"]
    )
    assert {
        "page background",
        "shell header",
        "sidebar",
        "main content surface",
        "search surface",
        "form controls",
    } <= set(guard["primary_surface_scope"])
    assert {"BPM091-M3-01", "BPM091-M3-02", "BPM091-M3-03", "BPM091-M3-05"} <= set(
        guard["implementation_tasks"]
    )

    assert "Light theme must not use pure white as a primary surface." in contract
    assert "`#ffffff`, `white`, or equivalent pure-white primary backgrounds" in contract
    assert "Page background, shell header, sidebar, main content surface, search surface" in contract


def test_guardrail_fails_for_all_settings_rows_without_valid_help_disposition() -> None:
    guard = _guard("all-settings-row-help-disposition")
    contract = _json(ALL_SETTINGS_CONTRACT)
    resolution = contract["target_resolution"]
    ui = contract["ui_contract"]

    assert guard["failure_mode"] == "All Settings rows without valid help-link disposition"
    assert {
        "linked",
        "not_applicable_raw",
        "unsupported_unknown",
        "missing_documentation",
        "artifact_unavailable",
        "artifact_stale",
        "artifact_incomplete",
        "artifact_incompatible",
    } == set(resolution["valid_dispositions"])

    assert "Rows with no valid target must still expose one of the valid no-link dispositions." in (
        resolution_text := " ".join(contract["manifest_validation"]["requirements"])
    )
    assert "fail closed for broken target IDs" in resolution_text
    assert "data-settings-entry-help-disposition" in ui["linked_state"]["data_attributes"]
    assert "data-settings-entry-help-disposition" in ui["no_link_state"]["data_attributes"]
    assert "must not be nested inside an all-settings row button" in ui["interactive_markup"]

    rules = {rule["entry_kind"]: rule for rule in resolution["rules"]}
    assert rules["firefox_policy"]["target_id"] == "policy:{exact_policy_id}"
    assert rules["known_managed_preference"]["target_id"] == "known-preference:{exact.preference.id}"
    assert rules["raw_fallback"]["fallback_disposition"] == "not_applicable_raw"
    assert rules["unknown_imported"]["fallback_disposition"] == "unsupported_unknown"
