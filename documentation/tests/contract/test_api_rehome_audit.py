from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
AUDIT_JSON = REPOSITORY_ROOT / "docs/architecture/api-integration-rehome-audit-0.9.0.json"
AUDIT_MD = REPOSITORY_ROOT / "docs/architecture/api-integration-rehome-audit-0.9.0.md"

EXPECTED_API_TOPICS = {
    "admin-concept-integration-audience",
    "admin-concept-supported-integration-patterns",
    "admin-concept-api-conventions",
    "admin-concept-api-limitations",
    "admin-task-sync-profile-lifecycle",
    "admin-task-manage-profile-retirement",
    "admin-task-import-firefox-policies-json",
    "admin-task-export-firefox-policies-json",
    "admin-task-validate-firefox-policies-json",
    "admin-task-check-health-readiness",
    "admin-task-run-pull-compare-update-scenario",
    "admin-task-run-import-review-export-scenario",
    "admin-task-use-reusable-api-examples",
}
EXPECTED_USER_TOPICS = {
    "ug-task-import-policies-json",
    "ug-task-export-policies-json",
    "ug-task-validate-profile",
    "ug-troubleshoot-import-failure",
    "ug-troubleshoot-policy-validation",
    "ug-troubleshoot-schema-mismatch",
    "ug-troubleshoot-product-connection",
}

pytestmark = pytest.mark.docs_contract


def _audit() -> dict[str, object]:
    return json.loads(AUDIT_JSON.read_text(encoding="utf-8"))


def _topicrefs(map_name: str) -> list[str]:
    root = ET.parse(DITA_ROOT / f"en/maps/{map_name}").getroot()
    return [
        element.attrib["keyref"].removeprefix("topic.")
        for element in root.iter("topicref")
        if "keyref" in element.attrib
    ]


def _keydefs() -> dict[str, str]:
    root = ET.parse(DITA_ROOT / "en/maps/keys.ditamap").getroot()
    return {
        element.attrib["keys"]: element.attrib["href"]
        for element in root.findall("keydef")
        if element.attrib["keys"].startswith("topic.")
    }


def _localized_source_exists(pattern: str, locale: str = "en") -> bool:
    return (DOCUMENTATION_ROOT / pattern.format(locale=locale).removeprefix("documentation/")).is_file()


def test_api_rehome_audit_declares_completed_m12_07_scope_and_decisions() -> None:
    audit = _audit()
    decision = audit["decision"]
    summary = AUDIT_MD.read_text(encoding="utf-8")

    assert audit["schema_version"] == 1
    assert audit["backlog_item"] == "BPM090-M12-07"
    assert audit["status"] == "rehome-completed"
    assert decision["administrator_guide_becomes_integration_owner"] is True
    assert decision["administrator_guide_contains_migrated_api_corpus"] is True
    assert decision["api_integration_guide_is_thin_compatibility_landing_after_m12_07"] is True
    assert decision["api_integration_guide_is_temporary_source_until_m12_07"] is False
    assert decision["user_guide_retains_only_ui_workflows_and_user_visible_recovery"] is True
    assert decision["no_dita_topic_moves_in_this_task"] is False
    assert "no-lost-procedure rule" in summary
    assert "thin compatibility" in summary


def test_every_migrated_api_topic_has_one_current_admin_destination() -> None:
    audit = _audit()
    keydefs = _keydefs()
    api_map_topics = set(_topicrefs("api-integration-guide.ditamap"))
    admin_map_topics = set(_topicrefs("administrator-guide.ditamap"))
    entries = audit["api_topics_to_rehome"]
    future_topic_ids = [entry["future_topic_id"] for entry in entries]

    assert api_map_topics == {"api-concept-administrator-integration-landing"}
    assert set(future_topic_ids) == EXPECTED_API_TOPICS
    assert set(future_topic_ids) <= admin_map_topics
    assert len(future_topic_ids) == len(set(future_topic_ids))
    assert all(topic_id.startswith("admin-") for topic_id in future_topic_ids)

    for entry in entries:
        assert entry["current_key"] == f"topic.{entry['current_topic_id']}"
        assert entry["future_key"] == f"topic.{entry['future_topic_id']}"
        assert keydefs[entry["future_key"]] == f"../admin/{entry['future_topic_id']}.dita"
        assert _localized_source_exists(entry["future_source"])
        assert "/admin/" in entry["future_source"]
        assert entry["disposition"] == "moved_to_administrator_guide_in_m12_07"


def test_user_guide_api_adjacent_topics_keep_ui_ownership_with_admin_cross_links() -> None:
    audit = _audit()
    keydefs = _keydefs()
    user_map_topics = set(_topicrefs("user-guide.ditamap"))
    entries = audit["user_guide_api_adjacent_topics"]

    assert {entry["topic_id"] for entry in entries} == EXPECTED_USER_TOPICS
    for entry in entries:
        assert entry["keep_in_user_guide"] is True
        assert entry["topic_id"] in user_map_topics
        assert entry["current_key"] == f"topic.{entry['topic_id']}"
        assert keydefs[entry["current_key"]] == f"../user/{entry['topic_id']}.dita"
        assert _localized_source_exists(entry["current_source"])
        assert entry["retained_scope"]
        assert entry["future_cross_links"]
        assert all(key.startswith("topic.admin-") for key in entry["future_cross_links"])

    procedural_fragments = {
        entry["topic_id"]: entry["api_procedure_fragments_to_rehome"]
        for entry in entries
    }
    assert procedural_fragments["ug-task-import-policies-json"]
    assert procedural_fragments["ug-task-export-policies-json"]
    assert procedural_fragments["ug-troubleshoot-product-connection"]
    assert procedural_fragments["ug-task-validate-profile"] == []


def test_api_rehome_audit_preserves_fixtures_tests_and_redirect_plan() -> None:
    audit = _audit()
    fixtures = audit["fixtures_to_preserve"]
    tests = audit["tests_to_update_or_preserve"]
    plan = audit["redirect_and_cross_link_plan"]

    assert len(fixtures) == 9
    assert all((REPOSITORY_ROOT / path).is_file() for path in fixtures)
    assert {
        "documentation/tests/contract/test_api_integration_topics.py",
        "documentation/tests/contract/test_api_openapi_drift.py",
        "documentation/tests/contract/test_api_locale_parity.py",
        "documentation/tests/contract/test_user_guide_import_export_topics.py",
        "documentation/tests/contract/test_guide_maps.py",
        "documentation/tests/contract/test_api_rehome_audit.py",
    } == {entry["path"] for entry in tests}
    assert all((REPOSITORY_ROOT / entry["path"]).is_file() for entry in tests)

    assert "thin API Integration Guide landing page" in plan["api_guide_topic_urls"]
    assert "compatibility landing page" in plan["api_guide_landing"]
    assert "endpoint, request, response, health, retry, and automation details" in plan["user_guide_links"]
    assert "exactly one future admin topic" in plan["no_lost_procedure_rule"]
