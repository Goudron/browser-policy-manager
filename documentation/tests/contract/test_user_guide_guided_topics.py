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
    "ug-task-choose-profile-identity-schema": ("create-and-start", ["CAP-GUIDED-003"]),
    "ug-task-choose-guided-scenario": ("create-and-start", ["CAP-GUIDED-004"]),
    "ug-task-apply-starter-preset": ("create-and-start", ["CAP-GUIDED-005", "CAP-CIS-001"]),
    "ug-task-apply-cis-layer": ("create-and-start", ["CAP-GUIDED-006", "CAP-CIS-002"]),
    "ug-task-use-guided-editor": ("configure-with-guidance", ["CAP-GUIDED-001"]),
    "ug-task-search-guided-settings": ("configure-with-guidance", ["CAP-GUIDED-002"]),
    "ug-task-configure-browser-access-defaults": (
        "configure-with-guidance",
        ["CAP-GUIDED-007"],
    ),
    "ug-task-configure-home-search-navigation": (
        "configure-with-guidance",
        ["CAP-GUIDED-008"],
    ),
    "ug-task-configure-security-privacy": ("configure-with-guidance", ["CAP-GUIDED-009"]),
    "ug-task-configure-users-addons-sites": (
        "configure-with-guidance",
        ["CAP-GUIDED-010"],
    ),
    "ug-task-configure-firefox-ai-policies": (
        "configure-with-guidance",
        ["CAP-GUIDED-011"],
    ),
    "ug-task-use-guided-fine-tuning": ("configure-with-guidance", ["CAP-GUIDED-013"]),
    "ug-task-review-guided-profile": ("configure-with-guidance", ["CAP-GUIDED-014"]),
    "ug-task-save-export-guided-profile": ("configure-with-guidance", ["CAP-GUIDED-015"]),
}
REFERENCE_TOPICS = {
    "ug-reference-schema-dependent-guided-controls": (
        "configure-with-guidance",
        ["CAP-GUIDED-012"],
    ),
}
TOPICS = {**TASK_TOPICS, **REFERENCE_TOPICS}

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


def _case_topics() -> dict[str, dict[str, object]]:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    return {
        topic["topic_id"]: topic
        for section in case_map["sections"]
        for topic in section["topics"]
    }


def test_guided_topics_exist_in_every_locale_with_stable_metadata() -> None:
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


def test_guided_task_topics_have_required_task_contract() -> None:
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


def test_schema_dependent_reference_sections_are_complete() -> None:
    for locale in LOCALES:
        root = _topic_root(locale, "ug-reference-schema-dependent-guided-controls")
        sections = {section.attrib["id"] for section in root.findall("./refbody/section")}
        assert sections == {
            "a-release-controls",
            "a-esr-unavailable",
            "a-no-documentation-ai",
            "a-recovery",
        }
        assert len(root.findall("./related-links/link")) >= 2


def test_guided_topics_are_inventory_case_mapped_keyed_and_reachable() -> None:
    case_topics = _case_topics()
    inventory_topic_ids = set()
    for line in CAPABILITY_INVENTORY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `CAP-GUIDED-"):
            continue
        match = re.search(r"\| `(ug-[a-z0-9-]+)` \|", line)
        assert match is not None
        inventory_topic_ids.add(match.group(1))

    assert inventory_topic_ids == set(TOPICS)
    for topic_id, (section_id, capability_ids) in TOPICS.items():
        assert case_topics[topic_id]["capability_ids"] == capability_ids

        for locale in LOCALES:
            keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
            keydefs = {
                keydef.attrib["keys"]: keydef.attrib["href"]
                for keydef in keys.findall("keydef")
                if keydef.attrib["keys"].startswith("topic.")
            }
            section_keyrefs = _section_keyrefs(locale)[section_id]
            assert keydefs[f"topic.{topic_id}"] == f"../user/{topic_id}.dita"
            assert topic_id in section_keyrefs


def test_english_guided_topics_cover_all_steps_control_families_and_ai_boundary() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "Profile & baseline",
        "Browser access & defaults",
        "Security & privacy",
        "Users, add-ons & sites",
        "AI & smart features",
        "Review & export",
        "search",
        "schema channel",
        "scenario",
        "starter preset",
        "CIS layer",
        "browser access",
        "home",
        "managed search",
        "permissions",
        "cookies",
        "DNS",
        "accounts",
        "extensions",
        "bookmarks",
        "language",
        "visual search",
        "Release 153",
        "ESR 140.13",
        "unsupported",
        "fine-tuning",
        "validate",
        "save",
        "download",
        "does not add AI functionality",
        "RAG",
        "embeddings",
        "generative search",
        "generative answers",
    ):
        assert required.casefold() in text.casefold()
