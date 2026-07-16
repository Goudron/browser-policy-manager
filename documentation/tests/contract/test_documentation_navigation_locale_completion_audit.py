from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = ROOT / "documentation"
AUDIT = DOCUMENTATION_ROOT / "config/documentation-navigation-locale-completion-audit-0.9.1.json"
CSS = DOCUMENTATION_ROOT / "assets/theme/bpm-docs.css"
LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
BLOCK_TAGS = {"title", "shortdesc", "p", "cmd", "li", "entry", "note", "figdesc"}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _visible_units(path: Path) -> list[tuple[str, str]]:
    root = ET.parse(path).getroot()
    return [
        (element.tag, " ".join("".join(element.itertext()).split()))
        for element in root.iter()
        if element.tag in BLOCK_TAGS and "".join(element.itertext()).strip()
    ]


def test_m10_audit_freezes_required_scope_and_closes_all_blockers() -> None:
    audit = _json(AUDIT)

    assert audit["schema_version"] == 1
    assert audit["backlog_item"] == "BPM091-M10-01"
    assert audit["target_bpm_version"] == "0.9.1"
    assert audit["status"] == "accepted"
    assert audit["scope"]["locales"] == ["en", *LOCALES]
    assert audit["scope"]["guide_ids"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "api-integration-guide",
        "administrator-guide",
    ]
    assert audit["summary"]["open_blockers"] == []
    assert audit["summary"]["closed_blockers"] == [
        "DOC091-M10-SIDEBAR-SCROLL",
        "DOC091-M10-OBSOLETE-API-GUIDE",
        "DOC091-M10-UI-NAME-MISMATCH",
        "DOC091-M10-VISIBLE-ENGLISH",
    ]
    assert audit["summary"]["next_backlog_item"] == "BPM091-M10-07"


def test_sidebar_baseline_and_closure_cover_both_viewports() -> None:
    audit = _json(AUDIT)
    sidebar = audit["sidebar_scroll_audit"]

    assert sidebar["status"] == "closed"
    assert sidebar["closure_task"] == "BPM091-M10-02"
    assert len(sidebar["baseline_measurements"]) == 2
    assert {item["viewport"]["width"] for item in sidebar["baseline_measurements"]} == {
        390,
        1366,
    }
    for measurement in sidebar["baseline_measurements"]:
        metrics = measurement["sidebar"]
        assert metrics["overflow_y"] == "visible"
        assert metrics["max_height"] == "none"
        assert metrics["attempted_scroll_top"] == 120
        assert metrics["resulting_scroll_top"] == 0
        assert metrics["height"] > measurement["viewport"]["height"] * 10
        assert measurement["tree_total_items"] == 183
        assert measurement["disposition"] == "no_independent_sidebar_scroll"

    css = CSS.read_text(encoding="utf-8")
    sidebar_rule = css.split(".bpm-docs-sidebar {", 1)[1].split("}", 1)[0]
    assert "position: sticky" in sidebar_rule
    assert "overflow-y: auto" in sidebar_rule
    assert "max-block-size: calc(100dvh - 2rem)" in sidebar_rule
    assert sidebar["closure_evidence"]["browser_test"].endswith(
        "::test_documentation_sidebar_scroll_is_independent_and_reveals_deep_topic"
    )


def test_obsolete_api_guide_has_complete_administrator_ownership_map() -> None:
    audit = _json(AUDIT)
    api = audit["standalone_api_guide_audit"]

    assert api["status"] == "closed"
    assert api["closure_task"] == "BPM091-M10-03"
    assert api["baseline_publication"]["locale_map_count"] == 6
    assert api["baseline_publication"]["topic_count_per_locale"] == 1
    assert api["baseline_publication"]["landing_topic_id"] == (
        "api-concept-administrator-integration-landing"
    )
    owners = api["administrator_ownership"]
    assert len(owners) == 13
    assert len({item["former_api_topic_id"] for item in owners}) == 13
    assert len({item["administrator_topic_id"] for item in owners}) == 13
    for owner in owners:
        assert owner["administrator_source_exists_in_all_locales"] is True
        for locale in ("en", *LOCALES):
            source = ROOT / owner["administrator_source"].format(locale=locale)
            assert source.is_file(), source

    for locale in ("en", *LOCALES):
        api_map = DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/api-integration-guide.ditamap"
        assert not api_map.exists()
        assert not (
            DOCUMENTATION_ROOT
            / f"src/dita/{locale}/api/api-concept-administrator-integration-landing.dita"
        ).exists()
    assert api["retirement_disposition"]["mode"] == "deliberately_retired"
    assert api["retirement_disposition"]["active_guide_ids"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]


def test_ui_name_authority_values_match_runtime_catalogs_and_sources() -> None:
    audit = _json(AUDIT)
    authority = audit["interface_name_authority_audit"]

    assert authority["status"] == "replacement_accepted"
    assert authority["authority_task"] == "BPM091-M10-04"
    assert authority["replacement_task"] == "BPM091-M10-05"
    assert authority["authority_contract"] == (
        "documentation/config/interface-name-authority-0.9.1.json"
    )
    assert authority["replacement_evidence"] == (
        "documentation/config/interface-name-replacement-0.9.1.json"
    )
    assert authority["authority_coverage"]["runtime_catalog_keys"] == 39
    assert authority["authority_coverage"]["unowned_interface_names"] == 0
    for item in authority["candidate_runtime_authority"].values():
        for locale, expected in item["values"].items():
            assert _json(ROOT / f"app/i18n/{locale}.json")[item["catalog_key"]] == expected

    assert authority["authority_coverage"]["forbidden_source_alias_occurrences"] == 0
    for locale in LOCALES:
        for finding in audit["locales"][locale]["ui_name_mismatches"]:
            assert (ROOT / finding["source"]).is_file()
            assert finding["term_occurrences"]


def test_every_recorded_english_carryover_baseline_keeps_current_sources_and_english_peers() -> None:
    audit = _json(AUDIT)
    total_files = 0
    total_affected = 0
    total_fragments = 0

    for locale in LOCALES:
        locale_root = DOCUMENTATION_ROOT / f"src/dita/{locale}"
        source_files = sorted(locale_root.rglob("*.dita")) + sorted(locale_root.rglob("*.ditamap"))
        locale_audit = audit["locales"][locale]
        assert locale_audit["source_file_count"] == 163
        assert len(source_files) == 161
        assert locale_audit["exact_english_carryover_file_count"] == len(
            locale_audit["exact_english_carryover"]
        )
        assert locale_audit["ui_name_mismatch_file_count"] == len(
            locale_audit["ui_name_mismatches"]
        )

        fragment_count = 0
        for finding in locale_audit["exact_english_carryover"]:
            localized_source = ROOT / finding["source"]
            relative = localized_source.relative_to(locale_root)
            english_source = DOCUMENTATION_ROOT / "src/dita/en" / relative
            localized_text = "\n".join(text for _tag, text in _visible_units(localized_source))
            english_text = "\n".join(text for _tag, text in _visible_units(english_source))
            assert localized_text
            assert english_text
            assert finding["fragments"]
            for fragment in finding["fragments"]:
                assert fragment
            fragment_count += len(finding["fragments"])

        assert locale_audit["exact_english_carryover_fragment_count"] == fragment_count
        total_files += locale_audit["source_file_count"]
        total_affected += locale_audit["exact_english_carryover_file_count"]
        total_fragments += fragment_count

    summary = audit["summary"]
    assert summary["non_english_source_files_scanned"] == total_files == 815
    assert summary["exact_english_carryover_affected_files"] == total_affected == 208
    assert summary["exact_english_carryover_fragments"] == total_fragments == 2893
    assert summary["ui_name_mismatch_affected_files"] == 225
    assert summary["api_topics_mapped_to_administrator_guide"] == 13
