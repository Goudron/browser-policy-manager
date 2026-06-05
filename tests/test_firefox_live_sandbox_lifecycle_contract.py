from __future__ import annotations

from pathlib import Path

import tools.repo_health_report as repo_health_report

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_firefox_live_sandbox_is_ignored_local_state():
    gitignore = _read(".gitignore")

    assert ".bpm-test-browsers/" in gitignore


def test_firefox_live_sandbox_is_part_of_explicit_cleanup_target():
    makefile = _read("Makefile")

    assert ".bpm-test-browsers \\" in makefile
    assert "clean-local-artifacts:" in makefile
    assert "rm -rf $(LOCAL_ARTIFACT_DIRS) $(LOCAL_ARTIFACT_FILES)" in makefile


def test_firefox_live_sandbox_is_reported_by_repo_health():
    assert ".bpm-test-browsers" in repo_health_report.KNOWN_ARTIFACT_PATHS


def test_firefox_live_runbook_documents_sandbox_lifecycle():
    runbook = _read("docs/firefox-live-testing.md")

    required_phrases = {
        "## Sandbox lifecycle",
        "Treat `.bpm-test-browsers/` as disposable local state",
        "it is intentionally ignored by git",
        "it can be several hundred megabytes",
        "it is safe to remove",
        "make clean-local-artifacts",
        "make repo-health",
        "Ignored Local Artifacts",
        "make setup-firefox-live-browsers",
    }
    for phrase in required_phrases:
        assert phrase in runbook
