"""Executable M11-01 inventory for documentation completeness and PDF remediation."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
INVENTORY_PATH = ROOT / "documentation/config/documentation-gap-inventory-0.9.4.json"
DITA_ROOT = ROOT / "documentation/src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _findings() -> dict[str, dict[str, object]]:
    return {finding["finding_id"]: finding for finding in _inventory()["findings"]}


def test_gap_inventory_has_stable_scope_and_owned_dispositions() -> None:
    inventory = _inventory()

    assert inventory["schema_version"] == 1
    assert inventory["inventory_id"] == "bpm-0.9.4-documentation-gap-inventory"
    assert inventory["backlog_item"] == "BPM094-M11-01"
    assert inventory["target_bpm_version"] == "0.9.4"
    assert inventory["status"] == "accepted-for-owned-remediation"
    assert inventory["scope"]["locales"] == list(LOCALES)
    assert inventory["scope"]["guide_families"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]

    findings = _findings()
    assert set(findings) == {f"DOC094-GAP-00{number}" for number in range(1, 10)}
    for finding in findings.values():
        assert finding["classification"] in {
            "deferred-with-safe-boundary",
            "out-of-scope",
        }
        assert finding["owner"].startswith("BPM094-M11-")
        assert finding["locations"]
        assert finding["locale_impact"]
        assert finding["safe_boundary_until_remediated"]


def test_gap_inventory_keeps_literal_placeholder_markers_absent() -> None:
    marker = re.compile(r"\\b(?:TODO|TBD|FIXME)\\b", re.IGNORECASE)
    matches = []
    for locale in LOCALES:
        for path in (DITA_ROOT / locale).rglob("*.dita"):
            if marker.search(path.read_text(encoding="utf-8")):
                matches.append(path.relative_to(ROOT).as_posix())
        for path in (DITA_ROOT / locale / "maps").glob("*.ditamap"):
            if marker.search(path.read_text(encoding="utf-8")):
                matches.append(path.relative_to(ROOT).as_posix())
    assert matches == []


def test_gap_inventory_declares_only_maintained_source_and_safe_exclusions() -> None:
    scope = _inventory()["scope"]

    assert scope["maintained_source_roots"] == [
        "documentation/src/dita",
        "documentation/buildlib/pdf.py",
        "documentation/assets/pdf/bpm-guide-print.css",
        "documentation/config/pdf-generation-contract-0.9.3.json",
    ]
    assert scope["excluded_generated_roots"] == [
        "documentation/build",
        "documentation/dist",
        "documentation/reports",
        "documentation/.cache",
        "app/documentation/site",
    ]


def test_locale_selection_gap_has_authoritative_runtime_behavior_before_authoring() -> None:
    finding = _findings()["DOC094-GAP-001"]
    authority = finding["authoritative_behavior"]

    assert finding["owner"] == "BPM094-M11-02"
    assert finding["locale_impact"] == "all-locales"
    assert authority["product_owner"] == "app/core/locales.py"
    assert authority["client_owner"] == "app/static/profiles_platform.js"
    assert authority["application_owner"] == "app/static/profiles_library_bootstrap.js"
    assert authority["verification"] == "tests/integration/locale/test_locale_matrix.py"
    assert len(authority["rules"]) == 4
    for locale in LOCALES:
        topic = DITA_ROOT / locale / "user/ug-concept-language-detection-fallback.dita"
        assert topic.is_file()
        assert "a-system-language" in topic.read_text(encoding="utf-8")


def test_full_policies_document_and_pdf_findings_have_their_required_owners() -> None:
    findings = _findings()

    assert findings["DOC094-GAP-002"]["owner"] == "BPM094-M11-02"
    assert findings["DOC094-GAP-002"]["authoritative_behavior"]["boundary_shape"] == (
        '{"policies": {...}}'
    )
    for finding_id, owner in (
        ("DOC094-GAP-004", "BPM094-M11-03"),
        ("DOC094-GAP-005", "BPM094-M11-04"),
        ("DOC094-GAP-006", "BPM094-M11-05"),
        ("DOC094-GAP-007", "BPM094-M11-06"),
    ):
        assert findings[finding_id]["owner"] == owner
        assert findings[finding_id]["locale_impact"] == "all-locales"
