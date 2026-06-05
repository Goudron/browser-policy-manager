from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_readme_points_routine_commands_to_make_targets():
    readme = _read("README.md")

    required_targets = {
        "make dev",
        "make quality",
        "make coverage",
        "make test-ui",
        "make test-firefox-live",
        "make test-firefox-live-amo",
        "make local-chromium-ui-audit",
    }
    for target in required_targets:
        assert target in readme

    stale_commands = {
        "uvicorn app.main:app --reload",
        "ruff check .\nmypy app\npytest",
        "pytest --cov=app --cov-branch --cov-report=term-missing",
        "./.venv/bin/python tools/run_local_chromium_ui_audit.py",
    }
    for command in stale_commands:
        assert command not in readme


def test_locale_runbook_uses_make_targets_for_repeatable_gates():
    runbook = _read("docs/locale_update_runbook_2026-06-01.md")

    for target in ("make test-locale-contract", "make quality", "make coverage"):
        assert target in runbook

    stale_commands = {
        ".venv/bin/pytest -q tests/test_locale_catalogs.py",
        ".venv/bin/mypy app",
        ".venv/bin/ruff check .",
        ".venv/bin/pytest -q --cov=app --cov-report=term-missing",
    }
    for command in stale_commands:
        assert command not in runbook


def test_firefox_schema_runbook_uses_make_targets_for_verification():
    runbook = _read("docs/firefox-schema-update-runbook.md")

    for target in (
        "make test-firefox-schema-contract",
        "make test-locale-contract",
        "make test-release",
    ):
        assert target in runbook

    assert ".venv/bin/pytest -q \\" not in runbook


def test_firefox_schema_runbook_matches_current_editor_surfaces_and_policy_triage():
    runbook = _read("docs/firefox-schema-update-runbook.md")
    normalized = " ".join(runbook.split())

    required_phrases = {
        "Current product surfaces are the profile library, Guided editor, All settings, and JSON editor.",
        "Do not reintroduce a separate advanced editor route, template, redirect, or JavaScript bundle",
        "All settings coverage is the default and must be present for every schema-backed policy.",
        "Guided editor promotion is opt-in and needs a product reason.",
        "Do not promote every new Firefox policy into Guided.",
        "make build-locale-catalogs",
        "make test-ui",
        "The browser smoke suite intentionally checks only Russian and Simplified Chinese locale rendering",
        "Do not expand it into a deep browser regression matrix",
    }
    for phrase in required_phrases:
        assert phrase in normalized


def test_epic_backlog_creation_runbook_defines_versioned_backlog_contract():
    runbook = _read("docs/epic-backlog-creation-runbook.md")
    normalized = " ".join(runbook.split())

    required_phrases = {
        "All new BPM epic backlogs must pass through this runbook.",
        "The user must provide that target version in the request",
        "compact epic id: `BPM086`",
        "<EPIC_ID>-M<milestone_number>-<two_digit_task_number>",
        "Every task must specify the minimum sufficient ChatGPT-5.5 reasoning level",
        "`low`",
        "`medium`",
        "`high`",
        "`extra high`",
        "Product source, UI copy, README, changelog, and maintained documentation use English as the primary product language.",
        "The working chat with the maintainer can be in Russian",
        "The first milestone must include the target-version transition.",
        "By the end of the backlog, the repository should not describe the new work as belonging to the previous target version",
        "Every epic backlog must include README and changelog work for the target version.",
        "README must be updated after the main backlog implementation is complete",
        "keep the maintainer copyright at the bottom",
        "keep the existing information about email topics / message themes",
        "CHANGELOG.md` must receive an entry for the target version.",
        "Preserve older version history",
        "Every backlog must end with a final quality milestone.",
        "Run `mypy`.",
        "Run `ruff`.",
        "Run `pytest -q`.",
        "Bring covered code surface to 100% if it is below 100%.",
        "Run Chromium/Selenium smoke tests for BPM product logic.",
        "Create a git commit for the completed epic.",
        "Provide the maintainer with the exact `git push` command to run manually.",
        "Do not push from the backlog execution step.",
        "Show exactly one next task with its ID, essence, acceptance, and minimal reasoning.",
        "Do not start executing a backlog task just because the backlog exists.",
    }
    for phrase in required_phrases:
        assert phrase in normalized


def test_firefox_live_runbook_uses_make_targets_for_sandbox_and_suites():
    runbook = _read("docs/firefox-live-testing.md")

    required_targets = {
        "make setup-firefox-live-browsers",
        "make setup-firefox-live-browsers FIREFOX_CHANNEL=esr",
        "make test-firefox-live",
        "make test-firefox-live-amo",
        "make clean-local-artifacts",
        "make repo-health",
    }
    for target in required_targets:
        assert target in runbook

    stale_commands = {
        "bash tools/setup_firefox_live_browsers.sh release",
        ".venv/bin/pytest -m firefox_live -q",
        ".venv/bin/pytest -m firefox_live_amo -q",
    }
    for command in stale_commands:
        assert command not in runbook
