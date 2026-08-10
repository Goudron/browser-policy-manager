"""Fail closed on BPM094-M11A-05 documentation execution ownership."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/documentation-ci-handoff-ownership-0.9.4.json"
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
SCHEDULED_WORKFLOW = ROOT / ".github/workflows/documentation-audits.yml"

EXPECTED_LANES = {
    "fast-authoring",
    "required-ci-non-browser",
    "scheduled-audit",
    "chromium-browser",
    "manual-release-handoff",
}
EXPECTED_FAILURE_CLASSES = {
    "authoring-source",
    "deterministic-ci",
    "scheduled-review",
    "browser-runtime",
    "binary-delivery",
}

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _lane_by_id(contract: dict[str, object]) -> dict[str, dict[str, object]]:
    lanes = contract["lanes"]
    assert isinstance(lanes, list)
    return {lane["id"]: lane for lane in lanes}


def test_documentation_execution_lanes_have_one_complete_primary_owner() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["backlog_item"] == "BPM094-M11A-05"
    assert contract["target_bpm_version"] == "0.9.4"
    assert contract["status"] == "accepted"
    assert set(contract["failure_classes"]) == EXPECTED_FAILURE_CLASSES

    lanes = _lane_by_id(contract)
    assert set(lanes) == EXPECTED_LANES
    assert len(lanes) == len(contract["lanes"])
    for lane in lanes.values():
        assert lane["check_family"]
        assert lane["primary_owner"]
        assert lane["owner_kind"]
        assert lane["failure_class"] in EXPECTED_FAILURE_CLASSES
        assert lane["timing"]
        assert lane["command"]
        assert lane["progress_evidence"]
        assert lane["artifacts"]
        assert lane["escalation"]
        assert lane["excluded_contours"]


def test_required_ci_commands_are_nonoverlapping_and_release_heavy_work_stays_outside() -> None:
    contract = _contract()
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    lanes = _lane_by_id(contract)

    ownership = contract["nonoverlap"]["required_pr_ci_workflows"]
    assert ownership == {
        "documentation-coverage": ["required-ci-non-browser"],
        "chromium-tests": ["chromium-browser"],
    }
    for job, owned_lanes in ownership.items():
        assert f"  {job}:" in workflow
        assert len(owned_lanes) == 1

    assert len(re.findall(r"^\s*make docs-coverage$", workflow, re.M)) == 1
    assert len(re.findall(r"^\s*make test-docs$", workflow, re.M)) == 1
    assert len(re.findall(r"^\s*make test-docs-browser$", workflow, re.M)) == 1
    assert "make docs-release-handoff" not in workflow
    assert "make docs-pdf-build" not in workflow
    assert "make docs-reproducibility-check" not in workflow
    assert "make test-firefox-live" not in workflow
    assert lanes["required-ci-non-browser"]["primary_owner"] == "CI documentation-coverage job"
    assert lanes["chromium-browser"]["primary_owner"] == "CI chromium-tests job"


def test_required_ci_documentation_partition_installs_its_local_rag_contract_extra() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    documentation_job = workflow.split("  documentation-coverage:", 1)[1].split(
        "  frontend-tests:", 1
    )[0]

    assert "Install documentation and local-RAG contract dependencies" in documentation_job
    assert 'pip install -e ".[dev,ai]"' in documentation_job


def test_scheduled_audit_is_review_evidence_not_a_pull_request_requirement() -> None:
    contract = _contract()
    workflow = SCHEDULED_WORKFLOW.read_text(encoding="utf-8")
    ci_workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    lane = _lane_by_id(contract)["scheduled-audit"]

    assert lane["primary_owner"] == "documentation-audits scheduled workflow"
    assert lane["owner_kind"] == "scheduled-ci"
    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "  documentation-audits:" in workflow
    assert "make docs-snapshot" in workflow
    assert "test_documentation_subsystem_snapshot.py" in workflow
    assert "test_locale_*.py" in workflow
    assert "documentation-scheduled-audit-evidence" in workflow
    assert "documentation-audits:" not in ci_workflow


def test_fast_and_manual_release_lanes_have_truthful_boundaries_and_escalation() -> None:
    contract = _contract()
    lanes = _lane_by_id(contract)

    fast = lanes["fast-authoring"]
    assert fast["owner_kind"] == "manual-authoring"
    assert "30 seconds" in fast["timing"]
    assert "Skipped release-only checks" in fast["progress_evidence"]
    assert (
        fast["escalation"]
        == "make docs-release-handoff when the release scope or a release-only risk is affected"
    )

    release = lanes["manual-release-handoff"]
    assert release["owner_kind"] == "manual-release"
    assert release["command"] == "make docs-release-handoff"
    assert "binary PDF" in release["check_family"]
    assert "reproducibility" in release["check_family"]
    assert "ordinary scoped prose edits" in release["excluded_contours"]
    assert "phase/completed/total/terminal" in release["progress_evidence"]
