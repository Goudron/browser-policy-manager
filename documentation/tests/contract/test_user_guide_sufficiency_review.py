from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
REVIEW = REPOSITORY_ROOT / "docs/architecture/user-guide-sufficiency-review-0.9.1.json"
PROTOCOL = DOCUMENTATION_ROOT / "config/documentation-sufficiency-review-protocol-0.9.1.json"
TAXONOMY = DOCUMENTATION_ROOT / "config/topic-section-taxonomy-0.9.1.json"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
TEST_NODE_RE = re.compile(r"(?P<path>[A-Za-z0-9_./-]+\.py)::(?P<test>test_[A-Za-z0-9_]+)")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _workflow_by_section() -> dict[str, dict]:
    return {item["section_id"]: item for item in _json(REVIEW)["workflow_reviews"]}


def _reviewed_topic_ids() -> list[str]:
    return [
        topic_id
        for workflow in _json(REVIEW)["workflow_reviews"]
        for topic_id in workflow["topic_ids"]
    ]


def _taxonomy_action_topics() -> dict[str, list[str]]:
    user_guide = next(
        document
        for document in _json(TAXONOMY)["documents"]
        if document["guide_id"] == "user-guide"
    )
    return {
        section["section_id"]: [
            topic_id
            for topic_id in section["topics"]
            if topic_id.startswith(("ug-task-", "ug-troubleshoot-"))
        ]
        for section in user_guide["sections"]
    }


def _topic_contract(
    locale: str, topic_id: str
) -> tuple[str, list[str], str, str, list[str]]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "user" / f"{topic_id}.dita").read_text(encoding="utf-8")
    )
    prereq = " ".join("".join(root.find("./taskbody/prereq").itertext()).split())
    steps = [
        " ".join("".join(command.itertext()).split())
        for command in root.findall("./taskbody/steps/step/cmd")
    ]
    result = " ".join("".join(root.find("./taskbody/result").itertext()).split())
    postreq = " ".join("".join(root.find("./taskbody/postreq").itertext()).split())
    related = [
        link.attrib["keyref"]
        for link in root.findall("./related-links/link")
        if link.attrib.get("keyref")
    ]
    return prereq, steps, result, postreq, related


def test_user_guide_sufficiency_review_declares_m6_01_scope_and_result() -> None:
    review = _json(REVIEW)

    assert review["schema_version"] == 1
    assert review["review_id"] == "bpm-0.9.1-user-guide-sufficiency-review"
    assert review["target_bpm_version"] == "0.9.1"
    assert review["backlog_item"] == "BPM091-M6-01"
    assert review["guide_id"] == "user-guide"
    assert review["status"] == "accepted"
    assert review["scope"]["locale_scope"] == "source-locale-plus-parity"
    assert review["scope"]["parity_locales"] == list(LOCALES[1:])
    assert review["summary"] == {
        "workflow_review_count": 11,
        "task_topic_count": 62,
        "troubleshooting_topic_count": 10,
        "reviewed_topic_count": 72,
        "pass_count": 72,
        "blocked_count": 0,
        "deferred_non_goal_count": 0,
        "release_blockers": [],
        "result": (
            "Every User Guide task and troubleshooting topic resolves to explicit prerequisites, "
            "ordered commands, an observable result, a recovery path, drift sources, focused "
            "verification, and successful browser or deterministic simulation evidence."
        ),
    }


def test_review_normalization_resolves_every_protocol_field() -> None:
    review = _json(REVIEW)
    protocol = _json(PROTOCOL)
    field_resolution = review["normalization"]["field_resolution"]

    assert set(field_resolution) == set(protocol["review_item_template"]["required_fields"])
    assert "one protocol review item for every topic_id" in review["normalization"]["rule"]
    allowed_scopes = set(protocol["review_item_template"]["locale_scope_values"])
    allowed_dispositions = set(
        protocol["review_item_template"]["review_disposition_values"]
    )
    allowed_evidence = set(protocol["evidence_types"])
    for workflow in review["workflow_reviews"]:
        assert workflow["guide_id"] == "user-guide"
        assert review["scope"]["locale_scope"] in allowed_scopes
        assert workflow["review_disposition"] in allowed_dispositions
        assert set(workflow["evidence_type"]) <= allowed_evidence
        assert "browser_smoke" in workflow["evidence_type"]
        for field in (
            "task_or_claim",
            "prerequisites",
            "exact_steps",
            "expected_result",
            "recovery_path",
            "drift_source",
            "focused_verification",
            "evidence_artifact",
        ):
            assert workflow[field], (workflow["review_id"], field)


def test_review_covers_every_user_action_topic_once_in_taxonomy_order() -> None:
    expected_by_section = _taxonomy_action_topics()
    workflow_by_section = _workflow_by_section()
    reviewed = _reviewed_topic_ids()

    assert list(workflow_by_section) == list(expected_by_section)
    for section_id, expected_topics in expected_by_section.items():
        assert workflow_by_section[section_id]["topic_ids"] == expected_topics
    assert len(reviewed) == len(set(reviewed)) == 72
    assert sum(topic_id.startswith("ug-task-") for topic_id in reviewed) == 62
    assert sum(topic_id.startswith("ug-troubleshoot-") for topic_id in reviewed) == 10


@pytest.mark.parametrize("locale", LOCALES)
def test_every_reviewed_topic_has_executable_localized_task_fields(locale: str) -> None:
    for topic_id in _reviewed_topic_ids():
        prereq, steps, result, postreq, related = _topic_contract(locale, topic_id)
        assert prereq, (locale, topic_id, "prereq")
        assert len(steps) >= 2, (locale, topic_id, "steps")
        assert all(steps), (locale, topic_id, "cmd")
        assert result, (locale, topic_id, "result")
        assert postreq, (locale, topic_id, "postreq")
        assert related, (locale, topic_id, "related-links")
        assert all("configure as needed" not in step.casefold() for step in steps)


def test_localized_task_structure_preserves_source_execution_order() -> None:
    for topic_id in _reviewed_topic_ids():
        source_contract = _topic_contract("en", topic_id)
        source_step_count = len(source_contract[1])
        for locale in LOCALES[1:]:
            localized_contract = _topic_contract(locale, topic_id)
            assert len(localized_contract[1]) == source_step_count, (locale, topic_id)


def test_review_evidence_paths_and_pytest_nodes_exist() -> None:
    review = _json(REVIEW)

    for workflow in review["workflow_reviews"]:
        for artifact in workflow["evidence_artifact"]:
            assert (REPOSITORY_ROOT / artifact).is_file(), artifact
        commands = workflow["focused_verification"]
        assert any("-m browser_ui" in command for command in commands)
        for command in commands:
            for node in TEST_NODE_RE.finditer(command):
                path = REPOSITORY_ROOT / node["path"]
                assert path.is_file(), node.group(0)
                assert f"def {node['test']}(" in path.read_text(encoding="utf-8")


def test_review_records_recovery_and_honest_unverified_boundaries() -> None:
    review = _json(REVIEW)

    assert all(workflow["recovery_path"] for workflow in review["workflow_reviews"])
    boundaries = " ".join(review["unverified_boundaries"])
    assert "live Firefox deployment" in boundaries
    assert "file picker" in boundaries
    assert "administrator decisions" in boundaries
    assert review["summary"]["release_blockers"] == []


def test_review_records_successful_execution_results() -> None:
    execution = _json(REVIEW)["execution_record"]

    assert execution["browser_smoke"]["result"] == "pass"
    assert execution["browser_smoke"]["result_summary"] == "8 passed in 164.89s"
    assert execution["api_and_source_simulation"]["result"] == "pass"
    assert execution["api_and_source_simulation"]["result_summary"] == "4 passed"
    assert execution["per_topic_contract"]["result"] == "pass"
    assert execution["per_topic_contract"]["result_summary"] == "24 passed"
