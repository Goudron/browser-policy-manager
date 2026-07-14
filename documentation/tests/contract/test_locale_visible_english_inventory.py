from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
INVENTORY = DOC_ROOT / "config" / "locale-visible-english-inventory-0.9.1.json"
VISUAL_QA = DOC_ROOT / "config" / "user-guide-screenshot-visual-qa-0.9.1.json"

LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
CLASSIFICATIONS = {
    "replace",
    "allowlist",
    "brand",
    "identifier",
    "command/path/API",
    "abbreviation",
    "false positive",
}
SURFACES = {
    "product_ui_catalogs",
    "documentation_topics",
    "documentation_search_ui",
    "documentation_navigation",
    "screenshots",
    "captions_alt_text",
}
KEEP_CLASSIFICATIONS = {
    "allowlist",
    "brand",
    "identifier",
    "command/path/API",
    "abbreviation",
}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_locale_visible_english_inventory_covers_required_scope() -> None:
    inventory = _json(INVENTORY)

    assert inventory["schema_version"] == 1
    assert inventory["backlog_item"] == "BPM091-M7-01"
    assert inventory["target_bpm_version"] == "0.9.1"
    assert inventory["status"] == "accepted"
    assert set(inventory["classification_values"]) == CLASSIFICATIONS
    assert inventory["scope"]["locales"] == list(LOCALES)
    assert set(inventory["scope"]["surfaces"]) == SURFACES

    source_roots = "\n".join(inventory["scope"]["source_roots"])
    for required_root in (
        "app/i18n_src/{locale}/",
        "app/i18n/{locale}.json",
        "documentation/src/dita/{locale}/",
        "documentation/tools/build_docs.py",
        "documentation/config/search-facets-filters-0.9.0.json",
        "documentation/config/search-ui-filter-contract-0.9.1.json",
        "documentation/config/user-guide-screenshot-matrix-0.9.1.json",
        "documentation/config/user-guide-screenshot-visual-qa-0.9.1.json",
        "documentation/assets/screenshots/{locale}/",
    ):
        assert required_root in source_roots


def test_locale_visible_english_inventory_classifies_every_finding() -> None:
    inventory = _json(INVENTORY)
    findings = inventory["findings"]

    assert findings
    assert {finding["locale"] for finding in findings} == set(LOCALES)
    assert {finding["surface"] for finding in findings} >= SURFACES

    for finding in findings:
        assert finding["id"]
        assert finding["locale"] in LOCALES
        assert finding["surface"] in SURFACES
        assert finding["classification"] in CLASSIFICATIONS
        assert finding["terms"]
        assert finding["source_refs"]
        assert finding["rationale"]

        classification = finding["classification"]
        if classification == "replace":
            assert finding["decision"] == "fix in M7-03"
            source_refs = "\n".join(finding["source_refs"])
            assert (
                "app/i18n_src/" in source_refs
                or "documentation/src/dita/" in source_refs
                or "documentation/config/user-guide-screenshot-visual-qa-0.9.1.json"
                in source_refs
            )
        elif classification == "false positive":
            assert finding["decision"] == "ignore"
        elif classification in KEEP_CLASSIFICATIONS:
            assert finding["decision"] == "keep"


def test_locale_visible_english_inventory_matches_summary_counts() -> None:
    inventory = _json(INVENTORY)
    expected = inventory["summary_by_locale"]

    actual: dict[str, Counter[str]] = {locale: Counter() for locale in LOCALES}
    for finding in inventory["findings"]:
        actual[finding["locale"]][finding["classification"]] += 1

    assert {
        locale: {classification: actual[locale][classification] for classification in CLASSIFICATIONS}
        for locale in LOCALES
    } == expected


def test_locale_visible_english_inventory_links_screenshot_visual_qa_blockers() -> None:
    inventory = _json(INVENTORY)
    visual_qa = _json(VISUAL_QA)

    blocker_ids_by_locale = {
        blocker["locale"]: blocker["id"] for blocker in visual_qa["release_blockers"]
    }
    replace_findings_by_locale = {
        finding["locale"]: finding
        for finding in inventory["findings"]
        if finding["surface"] == "screenshots" and finding["classification"] == "replace"
    }

    assert set(blocker_ids_by_locale) <= set(replace_findings_by_locale)
    for locale, blocker_id in blocker_ids_by_locale.items():
        assert blocker_id in replace_findings_by_locale[locale].get("related_blockers", [])
