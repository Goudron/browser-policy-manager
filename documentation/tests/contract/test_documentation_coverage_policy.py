from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
COVERAGE_POLICY = DOCUMENTATION_ROOT / "config/coverage-policy-0.9.0.json"

pytestmark = pytest.mark.docs_contract


def test_documentation_coverage_policy_is_explicit_and_separate_from_app_coverage() -> None:
    policy = json.loads(COVERAGE_POLICY.read_text(encoding="utf-8"))
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert policy["schema_version"] == 1
    assert policy["backlog_item"] == "BPM090-M11-04"
    assert policy["target_bpm_version"] == "0.9.0"
    assert policy["status"] == "accepted"
    assert policy["release_gate"]["covered_scope_must_be_100_percent"] is True
    assert policy["release_gate"]["shortfall_is_not_known_debt"] is True
    assert policy["release_gate"]["reported_uncovered_modules_must_be_named"] is True

    included = policy["included_modules"]
    assert included
    for module in included:
        assert module["coverage_target_percent"] == 100
        assert module["test_command"] == "make docs-coverage"
        assert (REPOSITORY_ROOT / module["path"]).is_file()
        assert module["path"] in makefile

    reported_uncovered = policy["reported_uncovered_modules"]
    assert "app/documentation/manifest.py" in reported_uncovered
    assert "app/documentation/router.py" in reported_uncovered
    assert all((REPOSITORY_ROOT / module).is_file() for module in reported_uncovered)

    assert "docs-coverage:" in makefile
    assert "--cov-fail-under=100" in makefile
    assert "--cov-report=xml:$(DOCS_COVERAGE_REPORT_DIR)/docs-coverage.xml" in makefile
    assert "--cov-report=html:$(DOCS_COVERAGE_REPORT_DIR)/html" in makefile
    assert 'source = ["app"]' in pyproject


def test_documentation_coverage_outputs_stay_inside_ignored_reports_boundary() -> None:
    policy = json.loads(COVERAGE_POLICY.read_text(encoding="utf-8"))
    outputs = policy["report_outputs"]

    assert outputs["terminal"] is True
    assert outputs["xml"] == "documentation/reports/coverage/docs-coverage.xml"
    assert outputs["html"] == "documentation/reports/coverage/html/index.html"
    for output in (outputs["xml"], outputs["html"]):
        assert output.startswith("documentation/reports/coverage/")
