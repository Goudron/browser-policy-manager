from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = DOCUMENTATION_ROOT / "config" / "topic-section-taxonomy-0.9.1.json"
AUDIT = DOCUMENTATION_ROOT / "config" / "topic-section-hierarchy-audit-0.9.1.json"
DITA_ROOT = DOCUMENTATION_ROOT / "src" / "dita" / "en" / "maps"

SECTION_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _map_topic_ids(filename: str) -> list[str]:
    root = ET.fromstring((DITA_ROOT / filename).read_text(encoding="utf-8"))
    return [
        topicref.attrib["keyref"].removeprefix("topic.")
        for topicref in root.findall(".//topicref")
    ]


def _taxonomy_documents() -> dict[str, dict]:
    return {document["guide_id"]: document for document in _json(TAXONOMY)["documents"]}


def _section_topics(document: dict) -> list[str]:
    topics: list[str] = []
    for section in document["sections"]:
        topics.extend(section["topics"])
    return topics


def test_topic_section_taxonomy_declares_scope_and_invariants() -> None:
    taxonomy = _json(TAXONOMY)

    assert taxonomy["schema_version"] == 1
    assert taxonomy["taxonomy_id"] == "bpm-0.9.1-topic-section-taxonomy"
    assert taxonomy["backlog_item"] == "BPM091-M8-02"
    assert taxonomy["target_bpm_version"] == "0.9.1"
    assert taxonomy["status"] == "accepted"
    assert taxonomy["inherits_from"] == [
        "documentation/config/topic-section-hierarchy-audit-0.9.1.json",
        "documentation/config/navigation-tree-contract-0.9.1.json",
    ]
    assert taxonomy["scope"]["affected_documents"] == ["user-guide", "administrator-guide"]
    assert taxonomy["scope"]["excluded_documents"] == [
        "cis-settings-guide",
        "firefox-policy-guide",
        "api-integration-guide",
    ]
    assert "does not edit DITA maps" in taxonomy["scope"]["implementation_boundary"]
    assert "canonical URLs" in taxonomy["section_rules"]["url_policy"]


def test_topic_section_taxonomy_uses_a_stable_localizable_label_key_shape() -> None:
    taxonomy = _json(TAXONOMY)

    assert taxonomy["section_rules"]["section_id_pattern"] == SECTION_ID_RE.pattern
    assert taxonomy["section_rules"]["label_key_pattern"] == (
        "navigation.section.{guide_id}.{section_id}"
    )
    assert "M8-04 provides locale-owned labels" in taxonomy["section_rules"][
        "localization_policy"
    ]
    assert "topic-section-labels-0.9.1.json" in taxonomy["section_rules"][
        "localization_policy"
    ]

    label_keys: list[str] = []
    for document in taxonomy["documents"]:
        guide_id = document["guide_id"]
        for section in document["sections"]:
            section_id = section["section_id"]
            assert SECTION_ID_RE.fullmatch(section_id)
            assert section["label_key"] == f"navigation.section.{guide_id}.{section_id}"
            assert section["canonical_label"]
            label_keys.append(section["label_key"])

    assert len(label_keys) == len(set(label_keys))


def test_topic_section_taxonomy_matches_audit_required_documents() -> None:
    taxonomy = _json(TAXONOMY)
    audit = _json(AUDIT)

    assert taxonomy["scope"]["affected_documents"] == audit["summary"][
        "documents_requiring_section_grouping"
    ]
    assert taxonomy["scope"]["excluded_documents"] == audit["summary"][
        "documents_excluded_as_short_enough"
    ]
    assert taxonomy["section_rules"]["max_topics_per_section"] == audit["thresholds"][
        "max_topics_per_section_target"
    ]


@pytest.mark.parametrize("guide_id", ["user-guide", "administrator-guide"])
def test_topic_section_taxonomy_assigns_every_affected_topic_once(guide_id: str) -> None:
    taxonomy = _json(TAXONOMY)
    document = _taxonomy_documents()[guide_id]
    source_topic_ids = _map_topic_ids(document["map_filename"])
    assigned_topic_ids = _section_topics(document)

    assert assigned_topic_ids == source_topic_ids
    assert len(assigned_topic_ids) == document["topic_count"]
    assert Counter(assigned_topic_ids) == Counter(source_topic_ids)
    assert all(count == 1 for count in Counter(assigned_topic_ids).values())
    assert taxonomy["summary"]["topic_counts"][guide_id] == len(source_topic_ids)


@pytest.mark.parametrize("guide_id", ["user-guide", "administrator-guide"])
def test_topic_section_taxonomy_keeps_sections_within_target_size(guide_id: str) -> None:
    taxonomy = _json(TAXONOMY)
    document = _taxonomy_documents()[guide_id]
    max_topics = taxonomy["section_rules"]["max_topics_per_section"]

    assert taxonomy["summary"]["section_counts"][guide_id] == len(document["sections"])
    for section in document["sections"]:
        assert 1 <= len(section["topics"]) <= max_topics
        assert section["source_relation"] in {
            "existing_topichead",
            "split_from_inspect-and-edit-complete-settings",
            "split_from_find-organize-and-compare-profiles",
            "derived_from_flat_map",
        }


def test_topic_section_taxonomy_splits_only_the_oversized_user_guide_groups() -> None:
    user_guide = _taxonomy_documents()["user-guide"]
    by_relation = {section["section_id"]: section["source_relation"] for section in user_guide["sections"]}

    assert {
        section_id
        for section_id, relation in by_relation.items()
        if relation == "split_from_inspect-and-edit-complete-settings"
    } == {
        "all-settings-review-filters",
        "all-settings-editing",
        "all-settings-advanced-sources",
    }
    assert {
        section_id
        for section_id, relation in by_relation.items()
        if relation == "split_from_find-organize-and-compare-profiles"
    } == {
        "profile-library-operations",
        "profile-comparison",
    }


def test_topic_section_taxonomy_derives_admin_workflow_sections_from_flat_map() -> None:
    admin = _taxonomy_documents()["administrator-guide"]

    assert admin["source_strategy"] == "derive_workflow_sections_from_flat_admin_map"
    assert [section["section_id"] for section in admin["sections"]] == [
        "linux-source-deployment",
        "windows-wsl-source-deployment",
        "devops-operations",
        "source-update",
        "api-integration-foundations",
        "profile-api-lifecycle",
        "api-health-and-scenarios",
        "control-product-workflows",
        "troubleshooting",
        "production-readiness",
    ]


def test_topic_section_taxonomy_keeps_implementation_for_m8_03() -> None:
    taxonomy = _json(TAXONOMY)

    assert taxonomy["summary"]["next_backlog_item"] == "BPM091-M8-03"
    assert taxonomy["summary"]["largest_section_topic_count"] == max(
        len(section["topics"])
        for document in taxonomy["documents"]
        for section in document["sections"]
    )
