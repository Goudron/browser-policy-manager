from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.core.policy_validation import validate_profile_policies_for_channel

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
FIXTURES_ROOT = DOCUMENTATION_ROOT / "fixtures/schema-validation"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SECTION_ID = "create-and-start"

TASK_TOPICS = {"ug-task-choose-firefox-schema": ["CAP-BOUNDARY-001"]}
CONCEPT_TOPICS = {"ug-concept-schema-aware-behavior": ["CAP-BOUNDARY-002"]}
TOPICS = {**TASK_TOPICS, **CONCEPT_TOPICS}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    if topic_id in TASK_TOPICS:
        assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source
    else:
        assert '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">' in source
    return ET.fromstring(source)


def _policies_fixture(name: str) -> dict[str, object]:
    document = json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))
    assert set(document) == {"policies"}
    return document["policies"]


def _case_topics() -> dict[str, dict[str, object]]:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    return {
        topic["topic_id"]: topic for section in case_map["sections"] for topic in section["topics"]
    }


def _section_keyrefs(locale: str) -> list[str]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8")
    )
    for topichead in root.findall("topichead"):
        intent = topichead.find("./topicmeta/data[@name='intent-id']")
        if intent is not None and intent.attrib["value"] == SECTION_ID:
            return [
                topicref.attrib["keyref"].removeprefix("topic.")
                for topicref in topichead.findall("topicref")
            ]
    raise AssertionError(f"Missing {SECTION_ID}")


def test_schema_validation_fixtures_match_supported_release_and_esr_boundaries() -> None:
    common_valid = _policies_fixture("common-valid-policies.example.json")
    release_only_valid = _policies_fixture("release-only-ai-valid.example.json")
    esr_unsupported_ai = _policies_fixture("esr-unsupported-ai.example.json")
    invalid_value = _policies_fixture("invalid-policy-value.example.json")

    for channel in ("esr-140.13", "esr-153.0", "release-153"):
        assert validate_profile_policies_for_channel(common_valid, channel) == []
    for channel in ("esr-153.0", "release-153"):
        assert validate_profile_policies_for_channel(release_only_valid, channel) == []

    esr_issues = validate_profile_policies_for_channel(esr_unsupported_ai, "esr-140.13")
    assert {issue.policy for issue in esr_issues} == {"AIControls"}
    for channel in ("esr-140.13", "esr-153.0", "release-153"):
        assert validate_profile_policies_for_channel(invalid_value, channel)


def test_schema_validation_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            root = _topic_root(locale, topic_id)
            expected_tag = "task" if topic_id in TASK_TOPICS else "concept"
            assert root.tag == expected_tag
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert root.find("title") is not None
            assert root.find("shortdesc") is not None


def test_choose_schema_task_has_action_warning_recovery_and_links() -> None:
    for locale in LOCALES:
        root = _topic_root(locale, "ug-task-choose-firefox-schema")
        taskbody = root.find("taskbody")
        assert taskbody is not None
        assert taskbody.find("prereq") is not None
        assert taskbody.find("context") is not None
        assert len(taskbody.findall("./steps/step")) == 4
        assert taskbody.find("result") is not None
        assert taskbody.find("postreq") is not None
        assert taskbody.find(".//note[@type='warning']") is not None
        assert len(root.findall("./related-links/link")) >= 2


def test_schema_concept_sections_are_complete() -> None:
    expected_sections = {
        "a-channel-choice",
        "a-validation",
        "a-release-esr-differences",
        "a-state-meanings",
        "a-migration-expectations",
        "a-example-boundary",
        "a-recovery",
    }
    for locale in LOCALES:
        root = _topic_root(locale, "ug-concept-schema-aware-behavior")
        assert {
            section.attrib["id"] for section in root.findall("./conbody/section")
        } == expected_sections
        assert len(root.findall("./related-links/link")) >= 2


def test_schema_validation_topics_are_case_mapped_keyed_and_reachable() -> None:
    case_topics = _case_topics()
    for topic_id, capability_ids in TOPICS.items():
        assert case_topics[topic_id]["capability_ids"] == capability_ids

    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"].startswith("topic.")
        }
        section_keyrefs = _section_keyrefs(locale)
        for topic_id in TOPICS:
            assert keydefs[f"topic.{topic_id}"] == f"../user/{topic_id}.dita"
            assert topic_id in section_keyrefs


def test_english_schema_topics_cover_validation_states_and_migration_expectations() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "ESR 140.13",
        "ESR 153.0",
        "Release 153",
        "DisableTelemetry",
        "AIControls",
        "VisualSearchEnabled",
        "supported",
        "unavailable",
        "deprecated",
        "unknown",
        "imported",
        "raw",
        "validation messages",
        "schema channel",
        "migration",
        "revalidate",
        "wrong value types",
        "unsupported",
        "affected policy path",
    ):
        assert required.casefold() in text.casefold()
