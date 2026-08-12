from __future__ import annotations

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = REPOSITORY_ROOT / "tests" / "coverage-ownership-0.9.4.json"
RELEASE_BOUNDARY_PATH = REPOSITORY_ROOT / "tools" / "release_boundary_manifest_0_9_5.json"


def _policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def test_coverage_ownership_policy_is_complete_and_fail_closed() -> None:
    policy = _policy()
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert policy["schema_version"] == 1
    assert policy["backlog_item"] == "BPM094-M10-06"
    application = policy["python_application"]
    scopes = application["coverage_scopes"]
    assert {scope["id"] for scope in scopes} == {
        "release-implementation-boundary",
        "optional-ai-incubation",
    }
    assert application["line_threshold_percent"] == 100
    assert application["branch_threshold_percent"] == 100
    assert application["coverage_omit"] is False

    release_boundary = json.loads(RELEASE_BOUNDARY_PATH.read_text(encoding="utf-8"))
    release_modules = set(release_boundary["categories"]["default_release"]["modules"])
    incubation_modules = set(release_boundary["categories"]["optional_incubation"]["modules"])
    scope_by_id = {scope["id"]: scope for scope in scopes}
    release_scope = scope_by_id["release-implementation-boundary"]
    incubation_scope = scope_by_id["optional-ai-incubation"]
    assert (
        set(path.removesuffix(".py").replace("/", ".") for path in release_scope["modules"])
        <= release_modules
    )
    assert (
        set(path.removesuffix(".py").replace("/", ".") for path in incubation_scope["modules"])
        == incubation_modules
    )
    assert all((REPOSITORY_ROOT / path).is_file() for scope in scopes for path in scope["modules"])
    assert {scope["make_target"] for scope in scopes} == {
        "coverage-release-implementation",
        "test-ai-incubation-coverage",
    }

    semantic_owners = application["semantic_owners"]
    assert {owner["release_boundary_category"] for owner in semantic_owners} == {
        "default_release",
        "optional_incubation",
    }
    assert all(
        "coverage configuration" in owner["boundary"]
        or "strict coverage scope" in owner["boundary"]
        for owner in semantic_owners
    )
    assert 'source = ["app"]' in pyproject
    assert "[tool.coverage.report]" in pyproject
    assert "omit =" not in pyproject
    assert "COVERAGE_FAIL_UNDER ?= 100" in makefile
    assert "--cov-fail-under=$(COVERAGE_FAIL_UNDER)" in makefile
    assert "coverage report --show-missing --fail-under=$(COVERAGE_FAIL_UNDER)" in makefile
    assert "AI_INCUBATION_COVERAGE_TARGETS" in makefile
    assert "RELEASE_IMPLEMENTATION_COVERAGE_TARGETS" in makefile
    assert "test-ai-incubation-coverage" in makefile
    assert "coverage-release-implementation" in makefile


def test_documentation_and_pure_javascript_scopes_are_explicit_and_complete() -> None:
    policy = _policy()
    package = json.loads((REPOSITORY_ROOT / "package.json").read_text(encoding="utf-8"))
    documentation = policy["documentation_library"]
    javascript = policy["javascript_pure_modules"]

    assert documentation["policy"] == "documentation/config/coverage-policy-0.9.4.json"
    assert documentation["line_threshold_percent"] == 100
    assert documentation["branch_threshold_percent"] == 100
    assert set(documentation["execution_layers"]) == {
        "documentation/buildlib/pdf.py",
        "documentation/buildlib/publishing.py",
    }
    assert javascript["include_glob"] == "app/static/profiles_modules/**"
    assert javascript["line_threshold_percent"] == 100
    assert javascript["branch_threshold_percent"] == 100
    assert javascript["function_threshold_percent"] == 100
    declared_modules = set(javascript["modules"])
    actual_modules = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "app" / "static" / "profiles_modules").glob("*.mjs")
    }
    assert declared_modules == actual_modules
    assert "semantic Node and Chromium owners" in javascript["boundary"]

    command = package["scripts"]["test:frontend:coverage"]
    assert "--test-coverage-include=app/static/profiles_modules/**" in command
    for threshold in ("lines", "branches", "functions"):
        assert f"--test-coverage-{threshold}=100" in command
    assert "test-coverage-exclude" not in command


def test_coverage_artifacts_are_isolated_and_uploaded_by_their_owners() -> None:
    policy = _policy()
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert policy["artifacts"] == {
        "python": "artifacts/coverage/python/",
        "documentation": "documentation/reports/coverage/",
        "javascript": "artifacts/coverage/frontend/",
    }
    assert "COVERAGE_REPORT_DIR ?= artifacts/coverage/python" in makefile
    assert "FRONTEND_COVERAGE_REPORT_DIR ?= artifacts/coverage/frontend" in makefile
    assert "COVERAGE_FILE=$(COVERAGE_DATA_FILE)" in makefile
    assert "frontend-coverage-artifacts" in workflow
    assert "artifacts/coverage/frontend/" in workflow
    assert "artifacts/coverage/python/coverage.xml" in workflow
    assert "artifacts/coverage/python/html/" in workflow
    assert "PYTEST_COVERAGE_ARGS: --cov=app" not in workflow
    assert "python-coverage-ai-incubation" in workflow
    assert "python-coverage-release-implementation" in workflow
    assert workflow.count("include-hidden-files: true") >= 2
    assert workflow.count("if-no-files-found: error") >= 2
    assert "release-implementation-coverage" in workflow
