from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DIAGNOSTICS_POLICY = DOCUMENTATION_ROOT / "config/diagnostics-policy-0.9.0.json"

pytestmark = pytest.mark.docs_contract


def test_documentation_diagnostics_policy_names_required_failure_context() -> None:
    policy = json.loads(DIAGNOSTICS_POLICY.read_text(encoding="utf-8"))

    assert policy["schema_version"] == 1
    assert policy["backlog_item"] == "BPM090-M11-06"
    assert policy["target_bpm_version"] == "0.9.0"
    assert policy["status"] == "accepted"
    assert policy["artifact_root"] == "documentation/reports/diagnostics/"
    assert set(policy["required_fields"]) == {
        "topic_id",
        "locale",
        "guide",
        "source_line",
        "target_url",
        "query",
        "screenshot_state",
        "focused_rerun",
    }
    assert policy["focused_entry_points"] == [
        "make docs-fast-check",
        "make test-docs-contract",
        "make docs-validate",
    ]


def test_documentation_diagnostic_artifacts_stay_in_ignored_reports_boundary() -> None:
    policy = json.loads(DIAGNOSTICS_POLICY.read_text(encoding="utf-8"))
    artifact_root = policy["artifact_root"]
    retention = policy["retention_rules"]

    assert retention["ignored_by_git"] is True
    assert retention["source_controlled"] is False
    assert retention["must_not_contain_secrets_or_customer_data"] is True
    assert artifact_root.startswith("documentation/reports/")
    completed = subprocess.run(
        ["git", "check-ignore", "--quiet", artifact_root],
        cwd=REPOSITORY_ROOT,
        check=False,
    )
    assert completed.returncode == 0


def test_documentation_diagnostics_policy_is_registered_in_suite_boundary_contract() -> None:
    boundaries = json.loads(
        (DOCUMENTATION_ROOT / "tests/suite-boundaries-0.9.0.json").read_text(encoding="utf-8")
    )
    diagnostics = boundaries["domains"]["diagnostics"]

    assert diagnostics["primary_suite"] == "contract"
    assert (
        "documentation/tests/contract/test_documentation_diagnostics_policy.py"
        in diagnostics["path_globs"]
    )
    assert "documentation/config/diagnostics-policy-0.9.0.json" in diagnostics["fixtures"]
    assert diagnostics["focused_rerun"] == (
        "./.venv/bin/pytest -q -m docs_contract "
        "documentation/tests/contract/test_documentation_diagnostics_policy.py"
    )
