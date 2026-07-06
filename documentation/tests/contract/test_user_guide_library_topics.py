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
    "ug-task-create-first-profile": "create-and-start",
    "ug-task-open-saved-profile": "create-and-start",
    "ug-task-use-profile-library": "find-organize-and-compare-profiles",
    "ug-task-find-profile": "find-organize-and-compare-profiles",
    "ug-task-filter-profile-library": "find-organize-and-compare-profiles",
    "ug-task-sort-profile-library": "find-organize-and-compare-profiles",
    "ug-task-refresh-profile-library": "find-organize-and-compare-profiles",
    "ug-task-duplicate-profile": "find-organize-and-compare-profiles",
    "ug-task-archive-profile": "find-organize-and-compare-profiles",
    "ug-task-restore-profile": "find-organize-and-compare-profiles",
    "ug-task-permanently-delete-profile": "find-organize-and-compare-profiles",
    "ug-troubleshoot-library-operation": "recover-safely",
}
REFERENCE_TOPICS = {
    "ug-reference-library-profile-row": "find-organize-and-compare-profiles",
    "ug-reference-archived-profile-behavior": "find-organize-and-compare-profiles",
}
LIBRARY_TOPICS = {**TASK_TOPICS, **REFERENCE_TOPICS}
M4_04_LIBRARY_HANDOFF_TOPICS = {
    "ug-task-import-policies-json",
    "ug-task-export-policies-json",
}
M4_05_LIBRARY_HANDOFF_TOPICS = {
    "ug-task-compare-profiles",
}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    expected_kind = "Task" if topic_id in TASK_TOPICS else "Reference"
    expected_dtd = "task.dtd" if topic_id in TASK_TOPICS else "reference.dtd"
    assert f'<!DOCTYPE {expected_kind.lower()} PUBLIC "-//OASIS//DTD DITA {expected_kind}//EN" "{expected_dtd}">' in source
    return ET.fromstring(source)


def _section_keyrefs(locale: str) -> dict[str, list[str]]:
    root = ET.fromstring((DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8"))
    sections: dict[str, list[str]] = {}
    for topichead in root.findall("topichead"):
        intent = topichead.find("./topicmeta/data[@name='intent-id']")
        assert intent is not None
        sections[intent.attrib["value"]] = [
            topicref.attrib["keyref"].removeprefix("topic.")
            for topicref in topichead.findall("topicref")
        ]
    return sections


def _case_topic_map() -> dict[str, dict[str, object]]:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    return {
        topic["topic_id"]: topic
        for section in case_map["sections"]
        for topic in section["topics"]
    }


def test_library_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in LIBRARY_TOPICS:
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


def test_library_task_topics_have_action_result_warning_recovery_and_related_links() -> None:
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


def test_library_reference_topics_have_state_warning_recovery_and_related_links() -> None:
    for locale in LOCALES:
        for topic_id in REFERENCE_TOPICS:
            root = _topic_root(locale, topic_id)
            sections = {
                section.attrib["id"]
                for section in root.findall("./refbody/section")
            }
            if topic_id == "ug-reference-library-profile-row":
                assert sections == {"a-row-identity", "a-row-state", "a-row-warning", "a-row-recovery"}
            else:
                assert sections == {
                    "a-archived-purpose",
                    "a-archived-limits",
                    "a-archived-warning",
                    "a-archived-recovery",
                }
            assert len(root.findall("./related-links/link")) >= 2


def test_library_topics_are_keyed_and_reachable_from_user_guide_maps() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"].startswith("topic.")
        }
        sections = _section_keyrefs(locale)

        for topic_id, section_id in LIBRARY_TOPICS.items():
            key = f"topic.{topic_id}"
            assert keydefs[key] == f"../user/{topic_id}.dita"
            assert topic_id in sections[section_id]


def test_library_topics_cover_current_m4_03_capability_boundary() -> None:
    case_topics = _case_topic_map()
    inventory_topic_ids = set()
    for line in CAPABILITY_INVENTORY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `CAP-LIB-"):
            continue
        match = re.search(r"\| `(ug-[a-z0-9-]+)` \|", line)
        assert match is not None
        inventory_topic_ids.add(match.group(1))

    assert set(LIBRARY_TOPICS) <= set(case_topics)
    assert inventory_topic_ids - set(LIBRARY_TOPICS) - M4_04_LIBRARY_HANDOFF_TOPICS - M4_05_LIBRARY_HANDOFF_TOPICS == set()
    assert case_topics["ug-task-import-policies-json"]["kind"] == "task"
    assert case_topics["ug-task-export-policies-json"]["kind"] == "task"
    assert case_topics["ug-task-compare-profiles"]["kind"] == "task"


def test_english_library_topics_explain_the_required_library_actions_and_states() -> None:
    text = "\n".join(
        "".join(_topic_root("en", topic_id).itertext())
        for topic_id in LIBRARY_TOPICS
    )

    for required_term in (
        "Library",
        "filtered",
        "total",
        "Search",
        "schema",
        "lifecycle",
        "validation",
        "Sort",
        "Refresh",
        "Guided Editor",
        "All Settings",
        "JSON Editor",
        "Duplicate",
        "Archive",
        "Restore",
        "Permanent delete",
        "archived",
        "Recovery",
    ):
        assert required_term.casefold() in text.casefold()
