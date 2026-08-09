from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
COVERAGE_POLICY = DOCUMENTATION_ROOT / "config/coverage-policy-0.9.4.json"

EXPECTED_LIBRARY_MODULES = {
    "documentation/buildlib/artifacts.py",
    "documentation/buildlib/catalog.py",
    "documentation/buildlib/lifecycle.py",
    "documentation/buildlib/portal.py",
    "documentation/buildlib/shared.py",
    "documentation/buildlib/sources.py",
    "documentation/buildlib/validation.py",
    "documentation/tools/validate_metadata.py",
}
EXPECTED_EXECUTION_LAYERS = {
    "documentation/buildlib/pdf.py",
    "documentation/buildlib/publishing.py",
}

pytestmark = pytest.mark.docs_contract


def test_documentation_coverage_policy_is_explicit_and_separate_from_app_coverage() -> None:
    policy = json.loads(COVERAGE_POLICY.read_text(encoding="utf-8"))
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert policy["schema_version"] == 3
    assert policy["backlog_item"] == "BPM094-M7-04"
    assert policy["target_bpm_version"] == "0.9.4"
    assert policy["status"] == "accepted"
    assert policy["release_gate"]["covered_scope_must_be_100_percent"] is True
    assert policy["release_gate"]["shortfall_is_not_known_debt"] is True
    assert policy["release_gate"]["branch_coverage_required"] is True
    assert policy["release_gate"]["mandatory_ci_job"] == "documentation-coverage"

    included = policy["deterministic_library_surfaces"]
    assert {module["path"] for module in included} == EXPECTED_LIBRARY_MODULES
    for module in included:
        assert module["coverage_target_percent"] == 100
        assert (REPOSITORY_ROOT / module["path"]).is_file()
    assert policy["test_command"] == "make docs-coverage"
    assert all(path in makefile for path in policy["test_paths"])
    for module in EXPECTED_LIBRARY_MODULES - {"documentation/tools/validate_metadata.py"}:
        dotted = module.removesuffix(".py").replace("/", ".")
        assert f"--cov={dotted}" in makefile
    assert "--cov=documentation.buildlib " not in makefile
    assert "--cov=validate_metadata" in makefile
    assert "COVERAGE_FILE=$(DOCS_COVERAGE_DATA_FILE)" in makefile

    assert "docs-coverage:" in makefile
    assert "--cov-fail-under=100" in makefile
    assert "--cov-report=xml:$(DOCS_COVERAGE_REPORT_DIR)/docs-coverage.xml" in makefile
    assert "--cov-report=html:$(DOCS_COVERAGE_REPORT_DIR)/html" in makefile
    assert 'source = ["app"]' in pyproject


def test_execution_layers_are_explicit_command_contracts_not_silent_omissions() -> None:
    policy = json.loads(COVERAGE_POLICY.read_text(encoding="utf-8"))
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    layers = policy["execution_layer_contracts"]
    assert {layer["path"] for layer in layers} == EXPECTED_EXECUTION_LAYERS
    for layer in layers:
        assert (REPOSITORY_ROOT / layer["path"]).is_file()
        assert "orchestration" in layer["reason"]
        assert layer["commands"]
        assert layer["focused_tests"]
        assert layer["mandatory_ci_job"] == "documentation-coverage"
        for command in layer["commands"]:
            assert f"{command.removeprefix('make ')}:" in makefile
        for test in layer["focused_tests"]:
            assert test in makefile


def test_documentation_coverage_outputs_stay_inside_ignored_reports_boundary() -> None:
    policy = json.loads(COVERAGE_POLICY.read_text(encoding="utf-8"))
    outputs = policy["report_outputs"]

    assert outputs["terminal"] is True
    assert outputs["xml"] == "documentation/reports/coverage/docs-coverage.xml"
    assert outputs["html"] == "documentation/reports/coverage/html/index.html"
    assert outputs["data_file"] == "documentation/reports/coverage/.coverage-docs"
    for output in (outputs["xml"], outputs["html"], outputs["data_file"]):
        assert output.startswith("documentation/reports/coverage/")


def test_documentation_coverage_is_a_mandatory_dedicated_ci_job() -> None:
    workflow = (REPOSITORY_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "documentation-coverage:" in workflow
    assert "name: Documentation tooling coverage" in workflow
    assert "make docs-coverage" in workflow
    assert "documentation-coverage-artifacts" in workflow
