from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _workflow_source(filename: str) -> str:
    return (WORKFLOWS_DIR / filename).read_text(encoding="utf-8")


def _workflow_jobs(filename: str = "ci.yml") -> dict[str, dict[str, object]]:
    document = yaml.safe_load(_workflow_source(filename))
    assert isinstance(document, dict)
    jobs = document.get("jobs")
    assert isinstance(jobs, dict)
    assert all(isinstance(name, str) and isinstance(job, dict) for name, job in jobs.items())
    return jobs


def _run_commands(job: dict[str, object]) -> tuple[str, ...]:
    steps = job.get("steps", [])
    assert isinstance(steps, list)
    return tuple(
        command
        for step in steps
        if isinstance(step, dict)
        for command in (step.get("run"),)
        if isinstance(command, str)
    )


def _joined_run_commands(job: dict[str, object]) -> str:
    return "\n".join(_run_commands(job))


def _needs(job: dict[str, object]) -> set[str]:
    value = job.get("needs", [])
    if isinstance(value, str):
        return {value}
    assert isinstance(value, list)
    assert all(isinstance(item, str) for item in value)
    return set(value)


def _count_command(commands: Iterable[str], command: str) -> int:
    return sum(line.strip() == command for block in commands for line in block.splitlines())


def test_ci_workflow_has_one_normal_owner_for_every_required_test_partition() -> None:
    jobs = _workflow_jobs()
    expected_jobs = {
        "lint",
        "base-runtime",
        "unit-tests",
        "integration-tests",
        "postgres-integration",
        "ai-incubation-tests",
        "release-implementation-coverage",
        "contract-tests",
        "documentation-coverage",
        "frontend-tests",
        "chromium-tests",
        "coverage",
        "required-gates",
    }
    assert expected_jobs <= set(jobs)

    owner_commands = {
        "unit-tests": ("make test-unit",),
        "integration-tests": ("make test-integration",),
        "postgres-integration": ("make test-postgres-integration",),
        "ai-incubation-tests": ("make test-ai-incubation-coverage",),
        "release-implementation-coverage": ("make coverage-release-implementation",),
        "contract-tests": ("make test-contract",),
        "documentation-coverage": ("make docs-coverage", "make test-docs"),
        "frontend-tests": ("make test-frontend-coverage",),
        "chromium-tests": ("make test-browser", "make test-docs-browser"),
    }
    all_commands = tuple(command for job in jobs.values() for command in _run_commands(job))
    for owner, commands in owner_commands.items():
        joined = _joined_run_commands(jobs[owner])
        for command in commands:
            assert command in joined
            assert _count_command(all_commands, command) == 1

    assert "pytest " not in "\n".join(all_commands)
    assert "make test-fast" not in "\n".join(all_commands)
    assert "make test-release" not in "\n".join(all_commands)
    assert "make test-live" not in "\n".join(all_commands)
    assert "make test-firefox-live" not in "\n".join(all_commands)
    assert "make test-firefox-live-amo" not in "\n".join(all_commands)


def test_ci_workflow_has_visible_dependency_and_artifact_flow() -> None:
    jobs = _workflow_jobs()

    for owner in (
        "base-runtime",
        "unit-tests",
        "integration-tests",
        "postgres-integration",
        "ai-incubation-tests",
        "release-implementation-coverage",
        "contract-tests",
        "documentation-coverage",
        "frontend-tests",
        "chromium-tests",
    ):
        assert _needs(jobs[owner]) == {"lint"}

    assert _needs(jobs["coverage"]) == {
        "unit-tests",
        "integration-tests",
        "postgres-integration",
        "ai-incubation-tests",
        "release-implementation-coverage",
        "contract-tests",
    }
    assert _needs(jobs["required-gates"]) == {
        "base-runtime",
        "dependency-audit",
        "documentation-coverage",
        "frontend-tests",
        "chromium-tests",
        "coverage",
    }

    source = _workflow_source("ci.yml")
    for artifact in (
        "python-coverage-ai-incubation",
        "python-coverage-release-implementation",
    ):
        assert artifact in source
    assert "pattern: python-coverage-*" in source
    assert "actions/download-artifact@v8" in source
    assert "make coverage-report" in _joined_run_commands(jobs["coverage"])
    assert "pytest" not in _joined_run_commands(jobs["coverage"])


def test_ci_proves_clean_package_artifacts_without_ai_dependencies() -> None:
    source = _workflow_source("ci.yml")

    assert "base-runtime:" in source
    assert "name: Package distribution and extras smoke" in source
    assert 'pip install -e ".[dev]"' in source
    assert 'pip install -e ".[dev,ai]"' in source
    assert "make release-boundary" in source
    assert "make package-smoke" in source


def test_ci_workflow_keeps_static_quality_gates_in_their_own_owner() -> None:
    jobs = _workflow_jobs()
    source = _joined_run_commands(jobs["lint"])

    assert "make lint" in source
    assert "make typecheck" in source
    assert "make architecture" in source
    assert "make verify-frontend-vendor" not in source
    assert "ruff check ." not in source
    assert "mypy app" not in source


def test_ci_workflow_does_not_enable_xdist_in_mandatory_jobs() -> None:
    source = _workflow_source("ci.yml")

    assert " -n " not in source
    assert "pytest-xdist" not in source


def test_ci_workflow_runs_native_frontend_coverage_on_pinned_node() -> None:
    source = _workflow_source("ci.yml")

    assert "frontend-tests:" in source
    assert "name: Native JavaScript layer and coverage" in source
    assert 'node-version: "22.22.1"' in source
    assert "npm ci" in source
    assert "make test-frontend-coverage" in source
    assert "frontend-coverage-artifacts" in source
    assert "artifacts/coverage/frontend/" in source


def test_ci_workflow_runs_the_real_postgresql_service_contract() -> None:
    source = _workflow_source("ci.yml")

    assert "postgres-integration:" in source
    assert "image: postgres:17-alpine" in source
    assert "POSTGRES_DB: bpm_m4_05" in source
    assert 'pip install -e ".[dev,postgres]"' in source
    assert "BPM_POSTGRES_TEST_URL: postgresql+asyncpg://" in source
    assert "make test-postgres-integration" in source
    assert "make postgres-ci-evidence" in source
    assert "Report PostgreSQL service and migration evidence" in source


def test_ci_workflow_fails_closed_on_resolved_dependency_audits_and_keeps_sboms_transient() -> None:
    jobs = _workflow_jobs()
    source = _workflow_source("ci.yml")

    assert _needs(jobs["dependency-audit"]) == {"lint"}
    assert jobs["dependency-audit"]["timeout-minutes"] == 15
    commands = _joined_run_commands(jobs["dependency-audit"])
    assert 'pip install -e ".[dev,postgres,ai]"' in commands
    assert "npm ci" in commands
    assert "make dependency-audit" in commands
    assert "dependency-audit-evidence" in source
    assert "artifacts/dependency-audit/" in source


def test_ci_workflow_makes_chromium_a_required_owned_layer() -> None:
    source = _workflow_source("ci.yml")

    assert "chromium-tests:" in source
    assert "browser-actions/setup-chrome@v2" in source
    assert "install-chromedriver: true" in source
    assert "BPM_CHROMIUM_BINARY: ${{ steps.chrome.outputs.chrome-path }}" in source
    assert "BPM_CHROMEDRIVER_BINARY: ${{ steps.chrome.outputs.chromedriver-path }}" in source
    assert "make test-browser" in source
    assert "make test-docs-browser" in source
    assert "chromium-failure-artifacts" in source


def test_xdist_pilot_workflow_is_manual_and_narrow() -> None:
    source = _workflow_source("xdist-pilot.yml")

    assert "workflow_dispatch:" in source
    assert "pull_request:" not in source
    assert "push:" not in source
    assert "schedule:" not in source
    assert "make test-unit-xdist XDIST_WORKERS=2" in source
    assert "make test-fast" not in source
    assert "make test-contract" not in source
    assert "make test-ui" not in source
    assert "make test-live" not in source


def test_firefox_deterministic_live_workflow_is_scheduled_and_manually_guarded() -> None:
    source = _workflow_source("firefox-live.yml")

    assert "workflow_dispatch:" in source
    assert "schedule:" in source
    assert 'cron: "17 3 * * 2"' in source
    assert "github.event_name == 'schedule' || inputs.run_live_tests == 'RUN'" in source
    assert "pull_request:" not in source
    assert "push:" not in source


def test_firefox_amo_canary_stays_manual_and_guarded() -> None:
    source = _workflow_source("firefox-live-amo.yml")

    assert "workflow_dispatch:" in source
    assert "run_live_tests:" in source
    assert "inputs.run_live_tests == 'RUN'" in source
    assert "schedule:" not in source
    assert "pull_request:" not in source
    assert "push:" not in source


def test_firefox_amo_canary_retains_external_failure_evidence_without_joining_live_gate() -> None:
    source = _workflow_source("firefox-live-amo.yml")

    assert "timeout-minutes: 30" in source
    assert "actions/cache@v5" in source
    assert "make verify-firefox-live-browsers" in source
    assert "actions/upload-artifact@v6" in source
    assert "artifacts/firefox-live-amo/${{ matrix.channel }}" in source
    assert "firefox-live.yml" not in source


def test_firefox_live_workflows_use_make_targets() -> None:
    live_source = _workflow_source("firefox-live.yml")
    amo_source = _workflow_source("firefox-live-amo.yml")

    assert 'make setup-firefox-live-browsers FIREFOX_CHANNEL="${{ matrix.channel }}"' in live_source
    assert "make firefox-live-workflow" in live_source
    assert "tools/setup_firefox_live_browsers.sh" not in live_source
    assert "test_policy_activation.py" not in live_source

    assert 'make setup-firefox-live-browsers FIREFOX_CHANNEL="${{ matrix.channel }}"' in amo_source
    assert "make test-firefox-live-amo" in amo_source
    assert "tools/setup_firefox_live_browsers.sh" not in amo_source
    assert "test_extension_settings_amo.py" not in amo_source


def test_firefox_deterministic_live_workflow_retains_channel_evidence_and_timeout() -> None:
    source = _workflow_source("firefox-live.yml")

    assert "timeout-minutes: 30" in source
    assert "actions/cache@v5" in source
    assert ".bpm-test-browsers/cache" in source
    assert "make verify-firefox-live-browsers" in source
    assert "make firefox-live-workflow" in source
    assert "actions/upload-artifact@v6" in source
    assert "artifacts/firefox-live/${{ matrix.channel }}" in source
