from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
AUTHORITY = DOC_ROOT / "config/interface-name-authority-0.9.1.json"
M10_AUDIT = DOC_ROOT / "config/documentation-navigation-locale-completion-audit-0.9.1.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_interface_name_authority_is_scoped_owned_and_complete() -> None:
    authority = _json(AUTHORITY)

    assert authority["schema_version"] == 1
    assert authority["authority_id"] == "bpm-0.9.1-interface-name-authority"
    assert authority["target_bpm_version"] == "0.9.1"
    assert authority["backlog_item"] == "BPM091-M10-04"
    assert authority["status"] == "accepted"
    assert authority["locales"] == list(LOCALES)
    assert authority["surface_scope"] == [
        "topic_title",
        "section_heading",
        "navigation_label",
        "breadcrumb",
        "search_result_title",
        "caption",
        "alt_text",
        "prose",
    ]
    assert authority["summary"] == {
        "interface_family_count": 5,
        "catalog_key_count": 39,
        "documentation_alias_count": 11,
        "reviewed_non_ui_class_count": 5,
        "catalog_quality_finding_count": 3,
        "additional_catalog_correction_count": 7,
        "unowned_interface_names": 0,
    }


def test_every_interface_name_resolves_from_the_same_runtime_key_in_every_locale() -> None:
    authority = _json(AUTHORITY)
    catalogs = {locale: _json(ROOT / f"app/i18n/{locale}.json") for locale in LOCALES}
    families = authority["interface_families"]
    keys = [key for family in families.values() for key in family]

    assert len(families) == authority["summary"]["interface_family_count"]
    assert len(keys) == authority["summary"]["catalog_key_count"]
    assert len(keys) == len(set(keys))
    for key in keys:
        assert key.startswith("profiles.")
        values = {locale: catalogs[locale][key] for locale in LOCALES}
        assert all(isinstance(value, str) and value.strip() for value in values.values())


def test_m10_candidate_names_and_historical_documentation_aliases_are_owned() -> None:
    authority = _json(AUTHORITY)
    audit = _json(M10_AUDIT)["interface_name_authority_audit"]
    aliases = authority["documentation_aliases"]
    alias_terms = {term for alias in aliases for term in alias["source_terms"]}
    alias_keys = {alias["catalog_key"] for alias in aliases}
    family_keys = {key for family in authority["interface_families"].values() for key in family}

    assert len(aliases) == authority["summary"]["documentation_alias_count"]
    assert alias_keys <= family_keys
    for alias in aliases:
        assert alias["source_terms"]
        assert alias["decision"]

    assert {
        "Profile Library",
        "Guided Editor",
        "All Settings",
        "JSON Editor",
        "Review mode",
        "Configured mode",
        "Catalog mode",
        "Profile Comparison",
        "Export",
    } <= alias_terms
    for candidate in audit["candidate_runtime_authority"].values():
        assert candidate["catalog_key"] in alias_keys
        for locale, expected in candidate["values"].items():
            assert _json(ROOT / f"app/i18n/{locale}.json")[candidate["catalog_key"]] == expected


def test_non_ui_terms_are_explicitly_classified_and_do_not_claim_runtime_keys() -> None:
    authority = _json(AUTHORITY)
    reviewed = authority["reviewed_non_ui_terms"]
    terms = {term for item in reviewed for term in item["terms"]}

    assert len(reviewed) == authority["summary"]["reviewed_non_ui_class_count"]
    assert {"Browser Policy Manager", "Firefox", "API", "JSON", "policies.json"} <= terms
    assert {"detail panel", "sidebar", "tree", "topic", "section"} <= terms
    for item in reviewed:
        assert item["classification"]
        assert item["authority"]
        assert "catalog_key" not in item


def test_catalog_quality_findings_are_resolved_by_replacement_task() -> None:
    authority = _json(AUTHORITY)
    findings = authority["catalog_quality_findings"]

    assert len(findings) == authority["summary"]["catalog_quality_finding_count"]
    assert authority["downstream_contract"]["replacement_task"] == "BPM091-M10-05"
    assert authority["downstream_contract"]["drift_gate_task"] == "BPM091-M10-08"
    for finding in findings:
        actual = [
            _json(ROOT / f"app/i18n/{locale}.json")[finding["catalog_key"]]
            for locale in finding["affected_locales"]
        ]
        assert actual == finding["resolved_values"]
        assert finding["baseline_values"] != finding["resolved_values"]
        assert finding["status"] == "resolved"
        assert finding["resolution_task"] == "BPM091-M10-05"

    corrections = authority["additional_catalog_corrections"]
    assert len(corrections) == authority["summary"]["additional_catalog_correction_count"]
    for correction in corrections:
        assert correction["baseline"] != correction["resolved"]
        assert (
            _json(ROOT / f"app/i18n/{correction['locale']}.json")[correction["catalog_key"]]
            == correction["resolved"]
        )
