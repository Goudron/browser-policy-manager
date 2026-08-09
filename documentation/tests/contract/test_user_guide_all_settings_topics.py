from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
CAPABILITY_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/product-user-capability-inventory-0.9.0.md"
)
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

TASK_TOPICS = {
    "ug-task-use-all-settings": ["CAP-SET-001"],
    "ug-task-review-attention-items": ["CAP-SET-002", "CAP-SET-003"],
    "ug-task-inspect-configured-settings": ["CAP-SET-005", "CAP-SET-006"],
    "ug-task-filter-settings-by-source": ["CAP-SET-007"],
    "ug-task-browse-settings-catalog": ["CAP-SET-008"],
    "ug-task-search-all-settings": ["CAP-SET-009"],
    "ug-task-filter-all-settings": ["CAP-SET-010"],
    "ug-task-inspect-setting-details": ["CAP-SET-012"],
    "ug-task-edit-setting-detail": ["CAP-SET-013"],
    "ug-task-remove-reset-setting": ["CAP-SET-014"],
    "ug-task-add-managed-preference": ["CAP-SET-015"],
    "ug-task-navigate-settings-categories": ["CAP-SET-016"],
    "ug-task-use-advanced-schema-controls": ["CAP-SET-017"],
    "ug-task-handle-raw-unknown-settings": ["CAP-SET-018", "CAP-RECOVERY-005"],
    "ug-task-follow-setting-deep-link": ["CAP-SET-019", "CAP-JSON-008"],
    "ug-task-trace-setting-source": ["CAP-CIS-004"],
    "ug-task-resolve-cis-manual-review": ["CAP-CIS-005"],
}
REFERENCE_TOPICS = {
    "ug-reference-all-settings-review-states": ["CAP-SET-004"],
    "ug-reference-large-settings-inventories": ["CAP-SET-011"],
}
TOPICS = {**TASK_TOPICS, **REFERENCE_TOPICS}
SECTION_ID = "inspect-and-edit-complete-settings"

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    if topic_id in TASK_TOPICS:
        assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source
    else:
        assert (
            '<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">'
            in source
        )
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


def test_all_settings_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            root = _topic_root(locale, topic_id)
            expected_tag = "task" if topic_id in TASK_TOPICS else "reference"
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


def test_all_settings_task_topics_have_action_warning_recovery_and_links() -> None:
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


def test_all_settings_reference_states_are_complete() -> None:
    expected_sections = {
        "ug-reference-all-settings-review-states": {
            "a-overview",
            "a-clean-profile",
            "a-invalid-items",
            "a-cis-manual-review",
            "a-raw-unknown-imported",
            "a-deprecated-items",
            "a-recovery",
        },
        "ug-reference-large-settings-inventories": {
            "a-overview",
            "a-list-budget",
            "a-narrowing-tools",
            "a-performance-boundary",
            "a-recovery",
        },
    }
    for locale in LOCALES:
        for topic_id, sections in expected_sections.items():
            root = _topic_root(locale, topic_id)
            assert {
                section.attrib["id"] for section in root.findall("./refbody/section")
            } == sections
            assert len(root.findall("./related-links/link")) >= 2


def test_all_settings_topics_are_inventory_case_mapped_keyed_and_reachable() -> None:
    case_topics = _case_topics()
    set_topic_ids = set()
    for line in CAPABILITY_INVENTORY.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `CAP-SET-"):
            match = re.search(r"\| `(ug-[a-z0-9-]+)` \|", line)
            assert match is not None
            set_topic_ids.add(match.group(1))

    assert set_topic_ids <= set(TOPICS)
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


def test_english_all_settings_topics_cover_modes_states_sources_and_advanced_controls() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "Review",
        "Configured",
        "Catalog",
        "invalid",
        "CIS manual-review",
        "raw",
        "unknown",
        "deprecated",
        "imported",
        "clean profile",
        "baseline",
        "CIS",
        "manual",
        "available",
        "Guided-covered",
        "All-Settings-only",
        "bounded",
        "detail panel",
        "validation",
        "product location",
        "apply",
        "edit",
        "remove",
        "reset",
        "managed preference",
        "category",
        "advanced schema",
        "preference controls",
        "deep link",
        "circled-information control",
        "new tab",
        "Documents",
        "noninteractive state",
        "JSON Editor",
    ):
        assert required.casefold() in text.casefold()
