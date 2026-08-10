from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
AUDIT = DOCUMENTATION_ROOT / "config" / "topic-section-hierarchy-audit-0.9.1.json"
DITA_ROOT = DOCUMENTATION_ROOT / "src" / "dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _map_root(locale: str, filename: str) -> ET.Element:
    return ET.fromstring((DITA_ROOT / locale / "maps" / filename).read_text(encoding="utf-8"))


def _topicrefs(root: ET.Element) -> list[ET.Element]:
    return root.findall(".//topicref")


def _direct_topicrefs(root: ET.Element) -> list[ET.Element]:
    return root.findall("topicref")


def _topicheads(root: ET.Element) -> list[ET.Element]:
    return root.findall("topichead")


def test_topic_section_hierarchy_audit_declares_bounded_scope() -> None:
    audit = _json(AUDIT)

    assert audit["schema_version"] == 1
    assert audit["audit_id"] == "bpm-0.9.1-topic-section-hierarchy-audit"
    assert audit["backlog_item"] == "BPM091-M8-01"
    assert audit["target_bpm_version"] == "0.9.1"
    assert audit["status"] == "accepted"
    assert audit["source_authority"]["canonical_locale"] == "en"
    assert audit["source_authority"]["locale_matrix"] == list(LOCALES)
    assert audit["thresholds"]["max_flat_topics_without_sections"] == 12
    assert audit["thresholds"]["max_topics_per_section_target"] == 12
    assert "Do not change topic IDs" in audit["global_invariants_for_follow_up"][0]


def test_topic_section_hierarchy_audit_matches_canonical_map_counts() -> None:
    audit = _json(AUDIT)

    for document in audit["documents"]:
        map_path = DITA_ROOT / "en" / "maps" / document["map_filename"]
        if not map_path.is_file():
            assert document["guide_id"] == "api-integration-guide"
            continue
        root = _map_root("en", document["map_filename"])
        topic_count = len(_topicrefs(root))
        source_section_count = len(_topicheads(root))
        section_counts = [len(_direct_topicrefs(section)) for section in _topicheads(root)]
        largest_count = max(section_counts, default=len(_direct_topicrefs(root)))

        assert document["topic_count"] == topic_count, document["guide_id"]
        assert document["current_source_section_count"] == source_section_count
        assert document["largest_current_source_section_count"] == largest_count


def test_topic_section_hierarchy_audit_matches_all_locale_map_shapes() -> None:
    audit = _json(AUDIT)

    for document in audit["documents"]:
        map_path = DITA_ROOT / "en" / "maps" / document["map_filename"]
        if not map_path.is_file():
            assert document["guide_id"] == "api-integration-guide"
            continue
        canonical = _map_root("en", document["map_filename"])
        canonical_topicrefs = [topicref.attrib["keyref"] for topicref in _topicrefs(canonical)]
        canonical_section_counts = [
            len(_direct_topicrefs(section)) for section in _topicheads(canonical)
        ]

        for locale in LOCALES:
            root = _map_root(locale, document["map_filename"])
            assert [
                topicref.attrib["keyref"] for topicref in _topicrefs(root)
            ] == canonical_topicrefs
            assert [
                len(_direct_topicrefs(section)) for section in _topicheads(root)
            ] == canonical_section_counts


def test_topic_section_hierarchy_audit_names_required_and_excluded_documents() -> None:
    audit = _json(AUDIT)
    threshold = audit["thresholds"]["max_flat_topics_without_sections"]
    by_id = {document["guide_id"]: document for document in audit["documents"]}

    assert audit["summary"]["documents_reviewed"] == len(audit["documents"])
    assert audit["summary"]["documents_requiring_section_grouping"] == [
        "user-guide",
        "administrator-guide",
    ]
    assert audit["summary"]["documents_excluded_as_short_enough"] == [
        "cis-settings-guide",
        "firefox-policy-guide",
        "api-integration-guide",
    ]

    for guide_id in audit["summary"]["documents_requiring_section_grouping"]:
        document = by_id[guide_id]
        assert document["status"] == "needs_section_grouping"
        assert (
            document["topic_count"] > threshold
            or document["largest_current_source_section_count"] > threshold
        )
        assert document["reasoning"]

    for guide_id in audit["summary"]["documents_excluded_as_short_enough"]:
        document = by_id[guide_id]
        assert document["status"] == "short_enough"
        assert document["topic_count"] <= threshold
        assert document["largest_current_source_section_count"] <= threshold
        assert document["reasoning"]


def test_topic_section_hierarchy_audit_preserves_user_guide_source_sections() -> None:
    audit = _json(AUDIT)
    user_guide = next(
        document for document in audit["documents"] if document["guide_id"] == "user-guide"
    )
    sections = user_guide["source_sections"]

    assert user_guide["current_shape"] == (
        "source_has_topicheads_but_portal_tree_needs_section_nodes"
    )
    assert len(sections) == user_guide["current_source_section_count"] == 8
    assert sum(section["topic_count"] for section in sections) == user_guide["topic_count"]
    assert {
        section["section_id"]
        for section in sections
        if section["disposition"] == "split_or_subgroup_in_m8_02"
    } == {
        "inspect-and-edit-complete-settings",
        "find-organize-and-compare-profiles",
    }


def test_topic_section_hierarchy_audit_keeps_implementation_for_follow_up() -> None:
    audit = _json(AUDIT)

    assert audit["summary"]["next_backlog_item"] == "BPM091-M8-02"
    for invariant in audit["global_invariants_for_follow_up"]:
        assert "URL" in invariant or "Section" in invariant or "root" in invariant
