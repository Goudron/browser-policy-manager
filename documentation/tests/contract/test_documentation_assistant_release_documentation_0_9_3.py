"""Six-locale release documentation guard for the floating BPM assistant."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from app.documentation.training_notice import training_notice

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation/src/dita"
UI_CONTRACT = ROOT / "documentation/config/documentation-assistant-floating-ui-contract-0.9.3.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
OVERVIEW = "ug-concept-browser-policy-manager-overview"
SEARCH_BOUNDARY = "ug-concept-documentation-search-boundary"
ASSISTANT_USE = "ug-task-use-local-documentation-assistant"
ADMIN_AVAILABILITY = "admin-task-gate-control-product-startup"


def _topic(locale: str, guide: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / guide / f"{topic_id}.dita"
    root = ET.parse(path).getroot()
    assert root.attrib["id"] == topic_id
    assert root.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == locale
    return root


def _text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


def test_floating_assistant_overview_is_complete_and_locale_owned() -> None:
    ui = json.loads(UI_CONTRACT.read_text(encoding="utf-8"))
    titles = ui["copy_authority"]["collapsed_titles"]
    required_sections = {
        "purpose",
        "documentation",
        "assistant",
        "assistant-panel",
        "assistant-ready",
        "assistant-installation",
    }

    for locale in LOCALES:
        root = _topic(locale, "user", OVERVIEW)
        sections = {section.attrib["id"] for section in root.findall(".//section")}
        assert sections >= required_sections
        assert "assistant-external" not in sections
        text = _text(root)
        assert titles[locale] in text
        assert "90" in text


def test_deterministic_search_boundary_stays_separate_from_chat() -> None:
    for locale in LOCALES:
        root = _topic(locale, "user", SEARCH_BOUNDARY)
        sections = {section.attrib["id"] for section in root.findall(".//section")}
        assert {"a-not-ai", "a-product-ai-policies"} <= sections
        text = _text(root).casefold()
        assert "rag" in text
        assert "bpm" in text


def test_administrator_guide_records_the_separate_assistant_availability_boundary() -> None:
    for locale in LOCALES:
        root = _topic(locale, "admin", ADMIN_AVAILABILITY)
        context = root.find("./taskbody/context[@id='a-documentation-assistant-availability']")
        assert context is not None
        text = _text(root).casefold()
        assert "bpm" in text


def test_existing_user_guide_maps_keep_the_two_updated_topics_reachable() -> None:
    expected = {f"topic.{OVERVIEW}", f"topic.{SEARCH_BOUNDARY}", f"topic.{ASSISTANT_USE}"}
    for locale in LOCALES:
        map_root = ET.parse(DITA_ROOT / locale / "maps" / "user-guide.ditamap").getroot()
        keyrefs = {element.attrib.get("keyref") for element in map_root.findall(".//topicref")}
        assert expected <= keyrefs


def test_local_assistant_use_topic_covers_the_released_training_notice() -> None:
    for locale in LOCALES:
        root = _topic(locale, "user", ASSISTANT_USE)
        assert root.tag == "task"
        text = _text(root).casefold()
        assert "bpm" in text
        assert "90" in text
        assert training_notice(locale).casefold() in text
        assert len(root.findall("./taskbody/steps/step")) == 5


def test_existing_administrator_guide_maps_keep_the_availability_boundary_reachable() -> None:
    expected = f"topic.{ADMIN_AVAILABILITY}"
    for locale in LOCALES:
        map_root = ET.parse(DITA_ROOT / locale / "maps" / "administrator-guide.ditamap").getroot()
        keyrefs = {element.attrib.get("keyref") for element in map_root.findall(".//topicref")}
        assert expected in keyrefs
