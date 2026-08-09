from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
FIXTURES_ROOT = DOCUMENTATION_ROOT / "fixtures/json-editor"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SECTION_ID = "work-with-json-and-interchange"

TASK_TOPICS = {
    "ug-task-use-json-editor": ["CAP-JSON-001"],
    "ug-task-edit-raw-policies-json": ["CAP-JSON-002"],
    "ug-task-format-json-document": ["CAP-JSON-003"],
    "ug-task-validate-json-document": ["CAP-JSON-004"],
    "ug-task-save-json-document": ["CAP-JSON-005"],
}
CONCEPT_TOPICS = {
    "ug-concept-when-to-use-json-editor": ["CAP-JSON-007"],
}
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


def test_json_editor_fixtures_cover_valid_syntax_and_policy_errors() -> None:
    valid = json.loads((FIXTURES_ROOT / "valid-policies-json.example.json").read_text())
    schema_invalid = json.loads((FIXTURES_ROOT / "invalid-policy-value.example.json").read_text())
    syntax_invalid = (FIXTURES_ROOT / "invalid-json-syntax.example.json").read_text()

    assert set(valid) == {"policies"}
    assert valid["policies"]["DisableTelemetry"] is True
    assert "Preferences" in valid["policies"]
    assert schema_invalid == {"policies": {"DisableTelemetry": "yes"}}
    with pytest.raises(json.JSONDecodeError):
        json.loads(syntax_invalid)
    assert "example.invalid" in json.dumps(valid, sort_keys=True)


def test_json_editor_topics_exist_in_every_locale_with_stable_metadata() -> None:
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


def test_json_editor_task_topics_have_action_warning_recovery_and_links() -> None:
    for locale in LOCALES:
        for topic_id in TASK_TOPICS:
            root = _topic_root(locale, topic_id)
            taskbody = root.find("taskbody")
            assert taskbody is not None
            assert taskbody.find("prereq") is not None
            assert taskbody.find("context") is not None
            assert len(taskbody.findall("./steps/step")) == 4
            assert taskbody.find("result") is not None
            assert taskbody.find("postreq") is not None
            assert taskbody.find(".//note[@type='warning']") is not None
            assert len(root.findall("./related-links/link")) >= 2


def test_json_editor_topics_are_case_mapped_keyed_and_reachable() -> None:
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


def test_english_json_editor_topics_cover_valid_and_invalid_end_to_end_examples() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "policies.json",
        "top-level policies",
        "Monaco",
        "Format",
        "Validate",
        "Save",
        "Download",
        "valid JSON syntax",
        "malformed JSON",
        "trailing commas",
        "missing braces",
        "schema-invalid policy values",
        "string where a boolean is required",
        "DisableTelemetry",
        "Preferences",
        "locked",
        "normalized profile model",
        "All Settings",
        "raw values",
        "migration checks",
    ):
        assert required.casefold() in text.casefold()
