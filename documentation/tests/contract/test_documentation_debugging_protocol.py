from __future__ import annotations

from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
RUNBOOK = DOCUMENTATION_ROOT / "runbooks/debugging-protocol.md"
SUITE_BOUNDARIES = DOCUMENTATION_ROOT / "tests/suite-boundaries-0.9.0.json"

pytestmark = pytest.mark.docs_contract


def _runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def test_debugging_protocol_names_ladder_commands_and_remaining_risk() -> None:
    runbook = _runbook()

    for command in (
        "make docs-fast-check",
        "make test-docs-contract",
        "make docs-validate",
        "make docs-build",
        "make docs-reproducibility-check",
        "make test-docs-ui-contract",
        "make test-docs-browser",
        "make docs-coverage",
        "make docs-release-check",
        "make docs-release-handoff",
        "make test-release",
    ):
        assert f"`{command}" in runbook

    for phrase in (
        "Still unverified",
        "Full DITA-OT output",
        "Real browser rendering",
        "Full screenshot capture/review",
        "Skipped release-only checks",
        "manual documentation QA",
        "live Firefox gates",
    ):
        assert phrase in runbook


def test_debugging_protocol_preserves_context_and_artifact_boundaries() -> None:
    runbook = _runbook()

    for phrase in (
        "read only the files named by that failure",
        "documentation/reports/diagnostics/",
        "Do not commit the report",
        "Do not scan all locale trees",
        "Never patch `documentation/build/`",
        "generated search indexes",
        "require immediate sandbox escalation",
        "does not replace `make test-docs-browser`",
    ):
        assert phrase in runbook


def test_debugging_protocol_is_registered_in_suite_boundary_contract() -> None:
    suite_boundaries = SUITE_BOUNDARIES.read_text(encoding="utf-8")

    assert "debugging_protocol" in suite_boundaries
    assert "documentation/runbooks/debugging-protocol.md" in suite_boundaries
    assert (
        "documentation/tests/contract/test_documentation_debugging_protocol.py" in suite_boundaries
    )
