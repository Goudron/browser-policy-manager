from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
CAPABILITY_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/product-user-capability-inventory-0.9.0.md"
)

pytestmark = pytest.mark.docs_contract

CAPABILITY_ROW_RE = re.compile(
    r"^\| `(?P<capability>CAP-[A-Z]+-[0-9]{3})` \| .* \| `(?P<topic>ug-[a-z0-9-]+)` \| "
    r"(?P<kind>task|concept|reference|troubleshooting) \|$"
)


def _inventory_rows() -> list[dict[str, str]]:
    rows = []
    for line in CAPABILITY_INVENTORY.read_text(encoding="utf-8").splitlines():
        if match := CAPABILITY_ROW_RE.match(line):
            rows.append(match.groupdict())
    return rows


def _case_map() -> dict[str, object]:
    return json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))


def _case_topics(case_map: dict[str, object]) -> list[dict[str, object]]:
    return [topic for section in case_map["sections"] for topic in section["topics"]]


def test_case_map_covers_every_capability_and_planned_user_topic_once() -> None:
    rows = _inventory_rows()
    case_map = _case_map()
    topics = _case_topics(case_map)

    assert case_map["navigation_model"] == "case-oriented-user-intent"
    assert case_map["source_inventory"] == (
        "docs/architecture/product-user-capability-inventory-0.9.0.md"
    )
    assert len(rows) == 106
    assert len({row["topic"] for row in rows}) == 89
    assert {topic["topic_id"] for topic in topics} == {row["topic"] for row in rows}
    assert len(topics) == len({topic["topic_id"] for topic in topics})

    mapped_capabilities = {capability for topic in topics for capability in topic["capability_ids"]}
    assert mapped_capabilities == {row["capability"] for row in rows}
    for row in rows:
        topic = next(topic for topic in topics if topic["topic_id"] == row["topic"])
        assert row["capability"] in topic["capability_ids"]
        assert topic["kind"] == row["kind"]


def test_case_map_is_organized_by_user_intent_not_product_surface_modules() -> None:
    case_map = _case_map()
    section_ids = [section["id"] for section in case_map["sections"]]

    assert section_ids == [
        "orient-and-plan",
        "create-and-start",
        "configure-with-guidance",
        "review-validate-and-finish",
        "inspect-and-edit-complete-settings",
        "work-with-json-and-interchange",
        "find-organize-and-compare-profiles",
        "recover-safely",
    ]
    assert not any(
        section_id in {"library", "guided", "all-settings", "json"} for section_id in section_ids
    )
    assert all(section["outcome"].startswith("A user can ") for section in case_map["sections"])


def test_localized_user_guide_maps_expose_the_same_case_oriented_sections() -> None:
    expected_ids = [section["id"] for section in _case_map()["sections"]]

    for locale in LOCALES:
        root = ET.fromstring((DITA_ROOT / locale / "maps/user-guide.ditamap").read_text())
        topicheads = root.findall("topichead")
        assert len(topicheads) == len(expected_ids)
        actual_ids = []
        for topichead in topicheads:
            navtitle = topichead.find("./topicmeta/navtitle")
            intent = topichead.find("./topicmeta/data[@name='intent-id']")
            assert navtitle is not None and navtitle.text and navtitle.text.strip()
            assert intent is not None
            actual_ids.append(intent.attrib["value"])
        assert actual_ids == expected_ids
