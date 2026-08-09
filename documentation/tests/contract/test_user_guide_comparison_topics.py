from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

TASK_TOPICS = {
    "ug-task-compare-profiles",
    "ug-task-select-comparison-profiles",
    "ug-task-interpret-profile-comparison",
}
CONCEPT_TOPICS = {"ug-concept-comparison-workflow"}
REFERENCE_TOPICS = {"ug-reference-comparison-states"}
TOPICS = {
    "ug-task-compare-profiles": ["CAP-LIB-014", "CAP-CMP-001"],
    "ug-concept-comparison-workflow": ["CAP-CMP-006"],
    "ug-task-select-comparison-profiles": ["CAP-CMP-002", "CAP-CMP-003"],
    "ug-task-interpret-profile-comparison": ["CAP-CMP-004"],
    "ug-reference-comparison-states": ["CAP-CMP-005"],
}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    if topic_id in TASK_TOPICS:
        assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source
    elif topic_id in CONCEPT_TOPICS:
        assert '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">' in source
    else:
        assert (
            '<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">'
            in source
        )
    return ET.fromstring(source)


def _section_keyrefs(locale: str) -> dict[str, list[str]]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8")
    )
    sections = {}
    for topichead in root.findall("topichead"):
        intent = topichead.find("./topicmeta/data[@name='intent-id']")
        assert intent is not None
        sections[intent.attrib["value"]] = [
            topicref.attrib["keyref"].removeprefix("topic.")
            for topicref in topichead.findall("topicref")
        ]
    return sections


def _case_topics() -> dict[str, dict[str, object]]:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    return {
        topic["topic_id"]: topic for section in case_map["sections"] for topic in section["topics"]
    }


def test_comparison_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            root = _topic_root(locale, topic_id)
            expected_tag = (
                "task"
                if topic_id in TASK_TOPICS
                else "concept"
                if topic_id in CONCEPT_TOPICS
                else "reference"
            )
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


def test_comparison_task_topics_have_action_result_warning_recovery_and_links() -> None:
    for locale in LOCALES:
        for topic_id in TASK_TOPICS:
            root = _topic_root(locale, topic_id)
            taskbody = root.find("taskbody")
            assert taskbody is not None
            assert taskbody.find("prereq") is not None
            assert taskbody.find("context") is not None
            assert taskbody.findall("./steps/step")
            assert taskbody.find("result") is not None
            assert taskbody.find("postreq") is not None
            assert taskbody.find(".//note[@type='warning']") is not None
            assert len(root.findall("./related-links/link")) >= 2


def test_comparison_reference_states_are_complete() -> None:
    for locale in LOCALES:
        root = _topic_root(locale, "ug-reference-comparison-states")
        sections = {section.attrib["id"] for section in root.findall("./refbody/section")}
        assert sections == {
            "a-comparison-row-types",
            "a-comparison-equal",
            "a-comparison-changed",
            "a-comparison-missing",
            "a-comparison-recovery",
        }


def test_comparison_topics_are_case_mapped_keyed_and_reachable() -> None:
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
        section_keyrefs = _section_keyrefs(locale)["find-organize-and-compare-profiles"]
        for topic_id in TOPICS:
            assert keydefs[f"topic.{topic_id}"] == f"../user/{topic_id}.dita"
            assert topic_id in section_keyrefs


def test_english_comparison_topics_explain_workflow_states_and_row_types() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "new tab",
        "Profile A",
        "Profile B",
        "independently",
        "selected profile summary",
        "union",
        "policy",
        "managed preference",
        "equal",
        "changed",
        "missing",
        "read-only",
        "does not merge",
    ):
        assert required.casefold() in text.casefold()
