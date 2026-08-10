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

CORE_TOPICS = {
    "ug-concept-profile-model": "orient-and-plan",
    "ug-concept-choose-editor-surface": "orient-and-plan",
    "ug-concept-schema-aware-behavior": "create-and-start",
    "ug-concept-cis-layer-merge": "create-and-start",
    "ug-concept-policies-and-managed-preferences": "review-validate-and-finish",
}


pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    assert '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">' in source
    return ET.fromstring(source)


def _section_keyrefs(locale: str) -> dict[str, list[str]]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8")
    )
    sections: dict[str, list[str]] = {}
    for topichead in root.findall("topichead"):
        intent = topichead.find("./topicmeta/data[@name='intent-id']")
        assert intent is not None
        sections[intent.attrib["value"]] = [
            topicref.attrib["keyref"].removeprefix("topic.")
            for topicref in topichead.findall("topicref")
        ]
    return sections


def test_core_orientation_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in CORE_TOPICS:
            root = _topic_root(locale, topic_id)
            assert root.tag == "concept"
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert root.find("title") is not None
            assert root.find("shortdesc") is not None
            assert root.find("conbody") is not None


def test_core_orientation_topics_are_keyed_and_reachable_from_user_guide_maps() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"].startswith("topic.")
        }
        sections = _section_keyrefs(locale)

        for topic_id, section_id in CORE_TOPICS.items():
            key = f"topic.{topic_id}"
            assert keydefs[key] == f"../user/{topic_id}.dita"
            assert topic_id in sections[section_id]


def test_core_topics_are_registered_in_the_case_oriented_user_guide_plan() -> None:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    planned_topics = {
        topic["topic_id"]: topic["kind"]
        for section in case_map["sections"]
        for topic in section["topics"]
    }

    assert {topic_id: planned_topics[topic_id] for topic_id in CORE_TOPICS} == {
        topic_id: "concept" for topic_id in CORE_TOPICS
    }


def test_english_core_topics_cover_first_time_user_decision_concepts() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in CORE_TOPICS)

    catalog = json.loads(
        (DOCUMENTATION_ROOT.parent / "app/i18n/en.json").read_text(encoding="utf-8")
    )
    for required_term in (
        catalog["profiles.nav_library"],
        catalog["profiles.editor_chrome_title"],
        catalog["profiles.editor_chrome_settings_link"],
        catalog["profiles.editor_chrome_json_link"],
        "Firefox Release",
        "ESR",
        "Validation",
        "policies",
        "managed preferences",
        "starter preset",
        "CIS",
    ):
        assert required_term in text

    forbidden_scope_terms = ("administrator", "deployment", "distribution", "installer")
    assert not any(term in text.lower() for term in forbidden_scope_terms)
