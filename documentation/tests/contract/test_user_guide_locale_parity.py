from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
COMPACT_STUB_MARKERS = (
    "Выполните сценарий Guided Editor",
    "Guided Editor 场景",
    "Führen Sie den Guided-Editor-Fall aus",
    "Exécutez le cas Guided Editor",
    "Ejecute el caso de Guided Editor",
    "Open the corresponding Guided Editor step",
    "English source",
    "английский источник",
    "englische Quelle",
    "source anglaise",
    "fuente inglesa",
    "英文源",
)

pytestmark = pytest.mark.docs_contract


def _root(locale: str, topic_name: str) -> ET.Element:
    return ET.fromstring((DITA_ROOT / locale / "user" / topic_name).read_text(encoding="utf-8"))


def _normalized_text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


def _task_signature(root: ET.Element) -> dict[str, object]:
    steps = root.findall("./taskbody/steps/step")
    return {
        "steps": len(steps),
        "step_notes": [step.find(".//note") is not None for step in steps],
        "related": [link.attrib["keyref"] for link in root.findall("./related-links/link")],
    }


def _section_signature(root: ET.Element) -> dict[str, object]:
    body = root.find("refbody") if root.tag == "reference" else root.find("conbody")
    return {
        "sections": [section.attrib.get("id") for section in body.findall("section")] if body is not None else [],
        "related": [link.attrib["keyref"] for link in root.findall("./related-links/link")],
    }


def test_user_guide_topic_files_are_parallel_in_every_locale() -> None:
    expected = {path.name for path in (DITA_ROOT / "en/user").glob("*.dita")}
    for locale in LOCALIZED_LOCALES:
        assert {path.name for path in (DITA_ROOT / locale / "user").glob("*.dita")} == expected


def test_user_guide_localized_topics_preserve_dita_structure_and_links() -> None:
    for english_topic in sorted((DITA_ROOT / "en/user").glob("*.dita")):
        english_root = _root("en", english_topic.name)
        english_signature = (
            _task_signature(english_root) if english_root.tag == "task" else _section_signature(english_root)
        )

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic.name)
            assert localized_root.tag == english_root.tag
            assert localized_root.attrib == {
                "id": english_root.attrib["id"],
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            localized_signature = (
                _task_signature(localized_root)
                if localized_root.tag == "task"
                else _section_signature(localized_root)
            )
            assert localized_signature == english_signature


def test_user_guide_localized_topics_are_not_compact_or_english_fallbacks() -> None:
    for english_topic in sorted((DITA_ROOT / "en/user").glob("*.dita")):
        english_text = _normalized_text(_root("en", english_topic.name))
        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic.name)
            localized_text = _normalized_text(localized_root)
            assert localized_text != english_text
            assert all(marker not in localized_text for marker in COMPACT_STUB_MARKERS)
            assert localized_root.findtext("title") != _root("en", english_topic.name).findtext("title")
