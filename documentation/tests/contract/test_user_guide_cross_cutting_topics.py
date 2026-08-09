from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

ORIENT_TOPICS = {
    "ug-task-change-interface-language": ["CAP-GLOBAL-005"],
    "ug-concept-language-detection-fallback": ["CAP-GLOBAL-006"],
    "ug-task-change-interface-theme": ["CAP-GLOBAL-007"],
    "ug-concept-accessible-product-operation": ["CAP-GLOBAL-015"],
    "ug-task-work-across-editor-tabs": ["CAP-GLOBAL-003"],
}
REVIEW_TOPICS = {
    "ug-task-save-profile": ["CAP-GLOBAL-010"],
    "ug-task-validate-profile": ["CAP-GLOBAL-011"],
    "ug-task-switch-editor-mode": ["CAP-GLOBAL-012"],
    "ug-task-review-profile-context": ["CAP-GLOBAL-014"],
}
RECOVERY_TOPICS = {
    "ug-task-manage-destructive-actions": ["CAP-RECOVERY-010"],
    "ug-troubleshoot-unsaved-changes": ["CAP-RECOVERY-011"],
}
CONCEPT_TOPICS = {
    "ug-concept-language-detection-fallback",
    "ug-concept-accessible-product-operation",
}
TOPIC_SECTIONS = {
    "orient-and-plan": ORIENT_TOPICS,
    "review-validate-and-finish": REVIEW_TOPICS,
    "recover-safely": RECOVERY_TOPICS,
}
TOPICS = {**ORIENT_TOPICS, **REVIEW_TOPICS, **RECOVERY_TOPICS}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    if topic_id in CONCEPT_TOPICS:
        assert '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">' in source
    else:
        assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source
    return ET.fromstring(source)


def _case_topics() -> dict[str, dict[str, object]]:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    return {
        topic["topic_id"]: topic for section in case_map["sections"] for topic in section["topics"]
    }


def _section_keyrefs(locale: str, intent_id: str) -> list[str]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8")
    )
    for topichead in root.findall("topichead"):
        intent = topichead.find("./topicmeta/data[@name='intent-id']")
        if intent is not None and intent.attrib["value"] == intent_id:
            return [
                topicref.attrib["keyref"].removeprefix("topic.")
                for topicref in topichead.findall("topicref")
            ]
    raise AssertionError(f"Missing {intent_id}")


def test_cross_cutting_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            root = _topic_root(locale, topic_id)
            expected_tag = "concept" if topic_id in CONCEPT_TOPICS else "task"
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


def test_cross_cutting_tasks_have_action_warning_recovery_and_links() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            if topic_id in CONCEPT_TOPICS:
                continue
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


def test_cross_cutting_concepts_have_complete_sections_and_links() -> None:
    expected_sections = {
        "ug-concept-language-detection-fallback": {
            "a-supported-locales",
            "a-system-language",
            "a-fallback",
            "a-content-parity",
        },
        "ug-concept-accessible-product-operation": {
            "a-keyboard",
            "a-focus",
            "a-status-feedback",
            "a-responsive-layouts",
        },
    }
    for locale in LOCALES:
        for topic_id, sections in expected_sections.items():
            root = _topic_root(locale, topic_id)
            assert {
                section.attrib["id"] for section in root.findall("./conbody/section")
            } == sections
            assert len(root.findall("./related-links/link")) == 2


def test_cross_cutting_topics_are_case_mapped_keyed_and_reachable() -> None:
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
        for intent_id, topics in TOPIC_SECTIONS.items():
            section_keyrefs = _section_keyrefs(locale, intent_id)
            for topic_id in topics:
                assert keydefs[f"topic.{topic_id}"] == f"../user/{topic_id}.dita"
                assert topic_id in section_keyrefs


def test_english_cross_cutting_topics_cover_required_behaviors() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "en, ru, de, zh-CN, fr, and es-ES",
        "System language",
        "fallback",
        "content-equivalent",
        "system, light, or dark theme",
        "product documentation portal",
        "light-gray primary surfaces",
        "Keyboard behavior",
        "Focus indicators",
        "responsive layouts",
        "separate browser tabs",
        "unsaved changes",
        "Save",
        "schema channel",
        "validation",
        "source attribution",
        "permanent delete",
        "irreversible action",
        "draft",
    ):
        assert required.casefold() in text.casefold()
