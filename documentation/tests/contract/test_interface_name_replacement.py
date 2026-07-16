from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
EVIDENCE = DOC_ROOT / "config/interface-name-replacement-0.9.1.json"
AUTHORITY = DOC_ROOT / "config/interface-name-authority-0.9.1.json"
LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
VISIBLE_TAGS = {
    "title",
    "navtitle",
    "shortdesc",
    "p",
    "cmd",
    "li",
    "entry",
    "note",
    "figdesc",
    "alt",
}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _visible_text(path: Path) -> str:
    root = ET.parse(path).getroot()
    return "\n".join(
        " ".join("".join(element.itertext()).split())
        for element in root.iter()
        if element.tag in VISIBLE_TAGS
    )


def test_replacement_evidence_closes_the_exact_authority_alias_baseline() -> None:
    evidence = _json(EVIDENCE)

    assert evidence["schema_version"] == 1
    assert evidence["evidence_id"] == "bpm-0.9.1-interface-name-replacement"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["backlog_item"] == "BPM091-M10-05"
    assert evidence["status"] == "accepted"
    assert evidence["authority"] == (
        "documentation/config/interface-name-authority-0.9.1.json"
    )
    assert evidence["locales"] == list(LOCALES)
    assert evidence["baseline"]["affected_file_count"] == 234
    assert evidence["baseline"]["occurrences_by_locale"] == {
        "ru": 403,
        "de": 255,
        "zh-CN": 403,
        "fr": 401,
        "es-ES": 402,
    }
    assert sum(evidence["baseline"]["occurrences_by_locale"].values()) == 1864
    assert evidence["baseline"]["total_occurrences"] == 1864
    assert evidence["late_discovered_contextual_baseline"] == {
        "profile_comparison_occurrences": 5,
        "contextual_export_action_occurrences": 5,
        "disposition": "resolved_through_runtime_catalog_keys",
    }
    assert evidence["english_source_baseline"] == {
        "primary_affected_file_count": 68,
        "primary_authority_alias_occurrences": 203,
        "additional_compare_alias_occurrences": 1,
        "lowercase_profile_library_occurrences": 2,
        "total_occurrences": 206,
        "disposition": "resolved_to_exact_runtime_casing_and_labels",
    }
    assert evidence["closure"]["total_ui_name_replacements"] == 2080


def test_no_localized_visible_dita_text_contains_a_forbidden_ui_alias() -> None:
    evidence = _json(EVIDENCE)
    forbidden = evidence["forbidden_source_terms"]
    findings: list[tuple[str, str, str]] = []

    for locale in LOCALES:
        source_root = DOC_ROOT / f"src/dita/{locale}"
        paths = sorted(source_root.rglob("*.dita")) + sorted(source_root.rglob("*.ditamap"))
        for path in paths:
            text = _visible_text(path)
            findings.extend(
                (locale, path.relative_to(ROOT).as_posix(), term)
                for term in forbidden
                if term in text
            )

    assert findings == []
    assert evidence["closure"]["forbidden_source_term_occurrences"] == 0
    assert evidence["closure"]["dita_xml_parse_failures"] == 0

    english_text = "\n".join(
        _visible_text(path)
        for path in (
            sorted((DOC_ROOT / "src/dita/en").rglob("*.dita"))
            + sorted((DOC_ROOT / "src/dita/en").rglob("*.ditamap"))
        )
    )
    assert all(term not in english_text for term in evidence["english_forbidden_source_terms"])


def test_all_authority_catalog_findings_and_additional_corrections_are_resolved() -> None:
    authority = _json(AUTHORITY)
    evidence = _json(EVIDENCE)

    assert len(authority["catalog_quality_findings"]) == evidence["catalog_corrections"][
        "authority_findings_resolved"
    ]
    assert len(authority["additional_catalog_corrections"]) == evidence[
        "catalog_corrections"
    ]["additional_malformed_values_resolved"]
    for finding in authority["catalog_quality_findings"]:
        assert finding["status"] == "resolved"
        actual = [
            _json(ROOT / f"app/i18n/{locale}.json")[finding["catalog_key"]]
            for locale in finding["affected_locales"]
        ]
        assert actual == finding["resolved_values"]
    for correction in authority["additional_catalog_corrections"]:
        actual = _json(ROOT / f"app/i18n/{correction['locale']}.json")[
            correction["catalog_key"]
        ]
        assert actual == correction["resolved"]

    assert evidence["closure"]["unresolved_authority_catalog_findings"] == 0
    assert evidence["closure"]["runtime_catalogs_reproducible"] is True
    assert evidence["closure"]["remaining_visible_english_owner"] == "BPM091-M10-06"
    assert evidence["closure"]["drift_gate_owner"] == "BPM091-M10-08"


def test_historical_search_alias_is_query_only_not_visible_document_copy() -> None:
    evidence = _json(EVIDENCE)
    boundary = evidence["search_alias_boundary"]

    assert boundary["allowed_historical_query"] == "profile library"
    assert boundary["allowed_locations"] == ["normalization alias", "quality query fixture"]
    assert set(boundary["forbidden_locations"]) >= {
        "search document title",
        "search document body",
        "navigation label",
        "breadcrumb",
        "topic heading",
    }
