from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tests.support import make_test_client

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
REVIEW = REPOSITORY_ROOT / "docs/architecture/administrator-devops-guide-sufficiency-review-0.9.1.json"
PROTOCOL = DOCUMENTATION_ROOT / "config/documentation-sufficiency-review-protocol-0.9.1.json"
TAXONOMY = DOCUMENTATION_ROOT / "config/topic-section-taxonomy-0.9.1.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
TEST_NODE_RE = re.compile(r"(?P<path>[A-Za-z0-9_./-]+\.py)::(?P<test>test_[A-Za-z0-9_]+)")
POST_091_ASSISTANT_TOPICS = {
    "admin-reference-minimum-system-requirements",
    "admin-task-operate-local-documentation-assistant",
    "admin-task-maintain-local-documentation-assistant",
}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _admin_taxonomy() -> dict:
    return next(
        document
        for document in _json(TAXONOMY)["documents"]
        if document["guide_id"] == "administrator-guide"
    )


def _source(locale: str, topic_id: str) -> str:
    return (DITA_ROOT / locale / "admin" / f"{topic_id}.dita").read_text(encoding="utf-8")


def _sections() -> dict[str, dict]:
    return {item["section_id"]: item for item in _json(REVIEW)["section_reviews"]}


def test_review_declares_closed_scope_with_honest_conditional_wsl_boundary() -> None:
    review = _json(REVIEW)

    assert review["schema_version"] == 1
    assert review["review_id"] == "bpm-0.9.1-administrator-devops-guide-sufficiency-review"
    assert review["target_bpm_version"] == "0.9.1"
    assert review["backlog_item"] == "BPM091-M6-03"
    assert review["guide_id"] == "administrator-guide"
    assert review["status"] == "accepted"
    assert review["last_reconciled_by"] == "BPM091-M12-05"
    assert review["summary"] == {
        "section_review_count": 10,
        "reviewed_topic_count": 49,
        "task_topic_count": 45,
        "concept_topic_count": 4,
        "procedure_pass_topic_count": 41,
        "procedure_deferred_non_goal_topic_count": 4,
        "procedure_blocked_topic_count": 0,
        "release_blocker_count": 0,
        "result": (
            "Linux userspace source installation and current operations, update, health, "
            "troubleshooting, integration, production-boundary, and current-version documentation "
            "have sufficient bounded evidence. Windows 10/11 WSL execution remains an explicit "
            "unverified conditional non-goal without a validation claim or release blocker."
        ),
    }
    assert review["release_blockers"] == []
    assert [item["finding_id"] for item in review["resolved_findings"]] == [
        "ADMIN091-VERSION-DRIFT",
        "ADMIN091-SOURCE-INSTALL-EVIDENCE",
    ]


def test_review_normalization_resolves_protocol_fields_and_evidence() -> None:
    review = _json(REVIEW)
    protocol = _json(PROTOCOL)
    resolution = review["normalization"]["field_resolution"]
    allowed_evidence = set(protocol["evidence_types"])

    assert set(resolution) == set(protocol["review_item_template"]["required_fields"])
    for section in review["section_reviews"]:
        assert section["guide_id"] == "administrator-guide"
        assert section["review_disposition"] in {"pass", "deferred-non-goal"}
        assert set(section["evidence_type"]) <= allowed_evidence
        assert section["evidence_type"]
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
            assert section[field], (section["review_id"], field)
        for artifact in section["evidence_artifact"]:
            assert (REPOSITORY_ROOT / artifact).is_file(), artifact
        for command in section["focused_verification"]:
            for node in TEST_NODE_RE.finditer(command):
                path = REPOSITORY_ROOT / node["path"]
                assert path.is_file(), node.group(0)
                assert f"def {node['test']}(" in path.read_text(encoding="utf-8")


def test_historical_review_covers_its_0_9_1_administrator_topic_inventory() -> None:
    taxonomy = _admin_taxonomy()
    reviews = _sections()
    reviewed = [topic for section in reviews.values() for topic in section["topic_ids"]]

    current_topics = [
        topic_id
        for section in taxonomy["sections"]
        for topic_id in section["topics"]
        if topic_id not in POST_091_ASSISTANT_TOPICS
    ]
    assert set(reviewed) == set(current_topics)
    assert not (POST_091_ASSISTANT_TOPICS & set(reviewed))
    assert len(reviewed) == len(set(reviewed)) == len(current_topics) == 49
    assert sum("-concept-" in topic_id for topic_id in reviewed) == 4


@pytest.mark.parametrize("locale", LOCALES)
def test_all_localized_administrator_topics_have_executable_or_claim_structure(locale: str) -> None:
    topic_ids = [
        topic_id
        for section in _json(REVIEW)["section_reviews"]
        for topic_id in section["topic_ids"]
    ]
    for topic_id in topic_ids:
        root = ET.fromstring(_source(locale, topic_id))
        assert root.attrib["id"] == topic_id
        assert root.findtext("title", "").strip()
        assert root.findtext("shortdesc", "").strip()
        related = [link.attrib.get("keyref") for link in root.findall("./related-links/link")]
        assert related and all(related), (locale, topic_id, "related-links")
        if root.tag == "task":
            taskbody = root.find("taskbody")
            assert taskbody is not None
            assert "".join(taskbody.find("prereq").itertext()).strip()
            commands = taskbody.findall("./steps/step/cmd")
            assert commands and all("".join(command.itertext()).strip() for command in commands)
            assert "".join(taskbody.find("result").itertext()).strip()
            assert "".join(taskbody.find("postreq").itertext()).strip()
        else:
            assert root.tag == "concept"
            conbody = root.find("conbody")
            assert conbody is not None and "".join(conbody.itertext()).strip()


def test_linux_source_install_passes_while_wsl_remains_unverified_non_goal() -> None:
    review = _json(REVIEW)
    sections = _sections()
    resolved = next(
        item for item in review["resolved_findings"]
        if item["finding_id"] == "ADMIN091-SOURCE-INSTALL-EVIDENCE"
    )
    source_install_topics = sections["linux-source-deployment"]["topic_ids"]
    current_source = "\n".join(_source("en", topic_id) for topic_id in source_install_topics)

    assert sections["linux-source-deployment"]["review_disposition"] == "pass"
    assert sections["linux-source-deployment"]["blocking_finding_ids"] == []
    assert "hands_on_command_transcript" in sections["linux-source-deployment"]["evidence_type"]
    assert sections["windows-wsl-source-deployment"]["review_disposition"] == "deferred-non-goal"
    assert sections["windows-wsl-source-deployment"]["blocking_finding_ids"] == []
    assert "unverified-no-actual-host-supplied" in sections["windows-wsl-source-deployment"][
        "expected_result"
    ]
    assert resolved["affected_topic_count"] == 4
    assert resolved["resolved_by"] == "BPM091-M12-05"
    assert resolved["closure_evidence"].endswith("m11-14-evidence-closure-20260715/closure.json")
    assert "<approved-0.9.1-ref>" in current_source
    assert "make dev" in current_source
    assert "Fedora Linux 44" in current_source
    assert "Manjaro stable branch" in current_source
    boundaries = " ".join(review["unverified_boundaries"])
    assert "Five clean Linux userspace-container installations" in boundaries
    assert "No Windows 10/11 WSL installation" in boundaries
    assert "unverified-no-actual-host-supplied" in boundaries


def test_version_drift_is_closed_for_every_current_administrator_topic() -> None:
    review = _json(REVIEW)
    blocker = next(
        item for item in review["resolved_findings"]
        if item["finding_id"] == "ADMIN091-VERSION-DRIFT"
    )
    topic_ids = [
        topic_id
        for section in review["section_reviews"]
        for topic_id in section["topic_ids"]
        if not topic_id.startswith("admin-task-install-")
    ]

    assert blocker["affected_topic_count"] == 44
    assert blocker["resolved_by"] == "BPM091-M12-02"
    assert len(topic_ids) == 44
    for locale in LOCALES:
        for topic_id in topic_ids:
            source = _source(locale, topic_id)
            assert 'product="bpm-0-9-1"' in source
            assert "0.9.0" not in " ".join(ET.fromstring(source).itertext())


def test_current_health_validation_import_and_export_results_execute() -> None:
    with make_test_client() as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready", "ready": True}

        validation = client.post(
            "/api/validate/release-153",
            json={"document": {"policies": {"DisableTelemetry": True}}},
        )
        assert validation.status_code == 200
        assert validation.json() == {"ok": True, "profile": "release-153"}

        imported = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": "m6-03-admin-sufficiency",
                "schema_version": "release-153",
                "document": {"policies": {"DisableTelemetry": True}},
            },
        )
        assert imported.status_code == 201
        exported = client.get(
            f"/api/export/profiles/{imported.json()['id']}/firefox/policies.json"
        )
        assert exported.status_code == 200
        assert exported.json() == {"policies": {"DisableTelemetry": True}}


def test_review_keeps_production_and_recovery_claims_bounded() -> None:
    review = _json(REVIEW)
    boundaries = " ".join(review["unverified_boundaries"])

    assert "production reverse proxy" in boundaries
    assert "HA cluster" in boundaries
    assert "Database downgrade safety is not guaranteed" in boundaries
    assert all(
        section["review_disposition"] == "pass"
        for section_id, section in _sections().items()
        if section_id != "windows-wsl-source-deployment"
    )
