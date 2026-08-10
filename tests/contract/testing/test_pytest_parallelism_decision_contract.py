from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DECISION = REPO_ROOT / "docs" / "architecture" / "pytest-parallelism-decision-0.9.4.md"
MAKEFILE = REPO_ROOT / "Makefile"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PILOT_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "xdist-pilot.yml"


def _target_body(source: str, target: str) -> str:
    match = re.search(
        rf"^{re.escape(target)}:(?:[^\n]*)\n(?P<body>(?:\t.*\n)+)",
        source,
        re.M,
    )
    assert match, f"missing Make target: {target}"
    return match.group("body")


def test_current_parallelism_decision_records_reproducible_evidence_and_boundaries() -> None:
    source = DECISION.read_text(encoding="utf-8")

    for expected in (
        "BPM094-M8-08",
        "2026-08-05",
        "271",
        "50.61",
        "49.78",
        "53.02",
        "40.17",
        "1101",
        "2202",
        "3303",
        "No mandatory pytest parallel layer is selected",
    ):
        assert expected in source


def test_current_parallelism_decision_keeps_mandatory_ci_serial_and_the_pilot_explicit() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    ci = CI_WORKFLOW.read_text(encoding="utf-8")
    pilot = PILOT_WORKFLOW.read_text(encoding="utf-8")

    assert " -n " not in _target_body(makefile, "test-unit")
    assert "-n $(XDIST_WORKERS)" in _target_body(makefile, "test-unit-xdist")
    assert " -n " not in ci
    assert "workflow_dispatch:" in pilot
    assert "pull_request:" not in pilot
    assert "make test-unit-xdist XDIST_WORKERS=2" in pilot
