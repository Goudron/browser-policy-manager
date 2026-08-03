"""Tree and content guard for BPM093-M14 user and administrator guide additions."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation/src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
OVERVIEW = "ug-concept-browser-policy-manager-overview"
REQUIREMENTS = "admin-reference-minimum-system-requirements"
ASSISTANT_USE = "ug-task-use-local-documentation-assistant"
ASSISTANT_OPERATION = "admin-task-operate-local-documentation-assistant"
ASSISTANT_MAINTENANCE = "admin-task-maintain-local-documentation-assistant"

pytestmark = pytest.mark.docs_contract


def _keyrefs(locale: str, guide: str) -> set[str]:
    root = ET.parse(DITA_ROOT / locale / "maps" / f"{guide}.ditamap").getroot()
    return {element.attrib["keyref"] for element in root.findall(".//topicref")}


def _topic(locale: str, guide: str, topic_id: str) -> ET.Element:
    root = ET.parse(DITA_ROOT / locale / guide / f"{topic_id}.dita").getroot()
    assert root.attrib["id"] == topic_id
    assert root.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == locale
    return root


def test_m14_01_m14_02_m14_04_and_m14_05_are_present_in_every_documentation_tree() -> None:
    for locale in LOCALES:
        assert f"topic.{OVERVIEW}" in _keyrefs(locale, "user-guide")
        assert f"topic.{ASSISTANT_USE}" in _keyrefs(locale, "user-guide")
        assert f"topic.{REQUIREMENTS}" in _keyrefs(locale, "administrator-guide")
        assert f"topic.{ASSISTANT_OPERATION}" in _keyrefs(locale, "administrator-guide")
        assert f"topic.{ASSISTANT_MAINTENANCE}" in _keyrefs(locale, "administrator-guide")

        overview = _topic(locale, "user", OVERVIEW)
        assistant_use = _topic(locale, "user", ASSISTANT_USE)
        requirements = _topic(locale, "admin", REQUIREMENTS)
        operation = _topic(locale, "admin", ASSISTANT_OPERATION)
        maintenance = _topic(locale, "admin", ASSISTANT_MAINTENANCE)
        assert "BPM" in " ".join(overview.itertext())
        assert assistant_use.tag == "task"
        assert assistant_use.find("./taskbody/prereq") is not None
        assert len(assistant_use.findall("./taskbody/steps/step")) == 5
        assert assistant_use.find("./taskbody/result") is not None
        assert assistant_use.find("./taskbody/postreq") is not None
        assistant_text = " ".join(assistant_use.itertext()).casefold()
        for marker in ("bpm", "90"):
            assert marker in assistant_text
        requirement_sections = {section.attrib["id"] for section in requirements.findall(".//section")}
        assert requirement_sections == {
            "base-platform",
            "browser-network-and-access",
            "local-assistant",
        }
        requirement_text = " ".join(requirements.itertext()).casefold()
        for marker in ("cpython 3.14", "4", "8", "3"):
            assert marker in requirement_text
        for topic, expected_steps in ((operation, 5), (maintenance, 5)):
            assert topic.tag == "task"
            assert topic.find("./taskbody/prereq") is not None
            assert len(topic.findall("./taskbody/steps/step")) == expected_steps
            assert topic.find("./taskbody/result") is not None
            assert topic.find("./taskbody/postreq") is not None
        operation_text = " ".join(operation.itertext()).casefold()
        maintenance_text = " ".join(maintenance.itertext()).casefold()
        for marker in ("bpm", "0.9.3"):
            assert marker in operation_text
        for marker in ("bpm", "0.9.3"):
            assert marker in maintenance_text
        for released_text in (operation_text, maintenance_text):
            assert "ai-rag-install-dev" not in released_text
            assert "model_installation" not in released_text
            assert "data/ai" not in released_text
