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
SECTION_ID = "recover-safely"

TROUBLESHOOTING_TOPICS = {
    "ug-troubleshoot-save-conflict": ["CAP-GLOBAL-013", "CAP-RECOVERY-007"],
    "ug-troubleshoot-library-operation": ["CAP-LIB-021"],
    "ug-troubleshoot-malformed-json": ["CAP-RECOVERY-001"],
    "ug-troubleshoot-import-failure": ["CAP-RECOVERY-002"],
    "ug-troubleshoot-policy-validation": ["CAP-RECOVERY-003"],
    "ug-troubleshoot-schema-mismatch": ["CAP-RECOVERY-004"],
    "ug-troubleshoot-profile-name": ["CAP-RECOVERY-006"],
    "ug-troubleshoot-missing-profile": ["CAP-RECOVERY-008"],
    "ug-troubleshoot-product-connection": ["CAP-RECOVERY-009"],
    "ug-troubleshoot-unsaved-changes": ["CAP-RECOVERY-011"],
}
TASK_TOPICS = {
    "ug-task-manage-destructive-actions": ["CAP-RECOVERY-010"],
}
TOPICS = {**TROUBLESHOOTING_TOPICS, **TASK_TOPICS}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source
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


def test_recovery_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            root = _topic_root(locale, topic_id)
            assert root.tag == "task"
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert root.find("title") is not None
            assert root.find("shortdesc") is not None


def test_recovery_topics_have_diagnosis_steps_warning_recovery_and_links() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
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


def test_recovery_topics_are_case_mapped_keyed_and_reachable() -> None:
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


def test_english_recovery_topics_cover_required_error_families_without_internal_edits() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "schema mismatch",
        "malformed JSON",
        "unsupported policy",
        "raw fallback",
        "failed import",
        "validation errors",
        "Profile not found",
        "stale tab",
        "Connection failures can result from",
        "network",
        "BPM API operation failure",
        "save-conflict",
        "duplicate",
        "permanent delete",
        "unsaved changes",
        "Retry only from the BPM interface",
    ):
        assert required.casefold() in text.casefold()
