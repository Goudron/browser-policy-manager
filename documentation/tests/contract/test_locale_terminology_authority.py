from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
AUTHORITY = DOC_ROOT / "config" / "locale-terminology-authority-0.9.1.json"
INVENTORY = DOC_ROOT / "config" / "locale-visible-english-inventory-0.9.1.json"

LOCALES = ("ru", "de", "zh-CN", "fr", "es-ES")
AUTHORITY_KINDS = {"mozilla_pontoon", "mozilla_sumo", "maintainer_fallback"}
ALLOWLIST_CATEGORIES = {
    "brand",
    "abbreviation",
    "identifier",
    "command/path/API",
    "placeholder",
}
REQUIRED_CONCEPTS = {
    "profile",
    "profile_name",
    "settings",
    "all_settings",
    "guided_mode",
    "search",
    "filter",
    "sort_ascending",
    "validation_results",
    "updated",
    "import",
    "create",
    "json_editor",
    "no_matches",
}
ORDINARY_ENGLISH_FRAGMENTS = (
    "Open profile",
    "Save changes",
    "Updated",
    "Importered",
    "Filtrered",
    "Guided-covered",
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_locale_terminology_authority_declares_source_policy() -> None:
    authority = _json(AUTHORITY)

    assert authority["schema_version"] == 1
    assert authority["backlog_item"] == "BPM091-M7-02"
    assert authority["target_bpm_version"] == "0.9.1"
    assert authority["status"] == "accepted"
    assert (
        "documentation/config/locale-visible-english-inventory-0.9.1.json"
        in authority["inherits_from"]
    )
    assert authority["locales"] == list(LOCALES)

    policy = authority["authority_policy"]
    assert policy["priority_order"] == [
        "mozilla_pontoon",
        "mozilla_sumo",
        "maintainer_fallback",
    ]
    assert "not untranslated English leaked by machine translation" in policy["mozilla_sumo"]
    assert "Brands" in policy["do_not_translate"]

    sources = authority["authority_sources"]
    assert "pontoon.mozilla.org/{locale}/firefox" in sources["pontoon_lookup_template"]
    assert "support.mozilla.org/{locale}/kb" in sources["sumo_lookup_template"]
    assert {example["locale"] for example in sources["verified_sumo_examples"]} >= {
        "de",
        "es-ES",
    }


def test_locale_terminology_authority_covers_required_concepts_for_every_locale() -> None:
    authority = _json(AUTHORITY)
    concepts = authority["concepts"]

    assert set(concepts) >= REQUIRED_CONCEPTS
    for concept_id, concept in concepts.items():
        assert concept["source_terms"]
        assert set(concept["terms"]) == set(LOCALES), concept_id
        for locale, localized in concept["terms"].items():
            assert localized["term"], (concept_id, locale)
            assert localized["authority"] in AUTHORITY_KINDS
            assert localized["note"], (concept_id, locale)


def test_locale_terminology_authority_has_ready_plan_for_each_replace_finding() -> None:
    authority = _json(AUTHORITY)
    inventory = _json(INVENTORY)

    replace_findings = {
        finding["id"]: finding
        for finding in inventory["findings"]
        if finding["classification"] == "replace"
    }
    plans = {plan["finding_id"]: plan for plan in authority["replacement_plan"]}

    assert set(plans) == set(replace_findings)
    for finding_id, plan in plans.items():
        assert plan["locale"] == replace_findings[finding_id]["locale"]
        assert plan["status"] == "ready_for_M7-03"
        assert plan["concept_refs"]
        for concept_ref in plan["concept_refs"]:
            assert concept_ref in authority["concepts"], (finding_id, concept_ref)
            assert plan["locale"] in authority["concepts"][concept_ref]["terms"]


def test_locale_terminology_allowlist_contains_only_stable_technical_english() -> None:
    authority = _json(AUTHORITY)
    allowlist = authority["allowlist"]

    assert set(allowlist) == ALLOWLIST_CATEGORIES
    examples_text = "\n".join(
        example for category in allowlist.values() for example in category["examples"]
    )
    for ordinary_fragment in ORDINARY_ENGLISH_FRAGMENTS:
        assert ordinary_fragment not in examples_text

    assert "Firefox" in allowlist["brand"]["examples"]
    assert "JSON" in allowlist["abbreviation"]["examples"]
    assert "browser.startup.homepage" in allowlist["identifier"]["examples"]
    assert "policies.json" in allowlist["command/path/API"]["examples"]
    assert "{name}" in allowlist["placeholder"]["examples"]
