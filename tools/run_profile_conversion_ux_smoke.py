#!/usr/bin/env python3
"""Run the focused M5 schema-conversion UX proof with retained safe evidence.

The test harness owns screenshots and sanitized browser logs for failures.  This
runner adds an intentionally compact command log, JUnit result, and value-free
summary so a maintainer can see the current phase and completed scenario count
without relying on chat progress.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_TESTS = (
    "tests/javascript/integration/profiles/profile_library_recommendation.test.js",
    "tests/javascript/integration/profiles/profile_conversion_review.test.js",
)
BROWSER_TEST = "tests/browser/profiles/test_schema_conversion_ux.py"


@dataclass(frozen=True, slots=True)
class PhaseResult:
    name: str
    returncode: int
    duration_seconds: float


def _progress(message: str) -> None:
    print(f"M5 schema-conversion UX: {message}", flush=True)


def _run_phase(
    name: str,
    command: list[str],
    *,
    environment: dict[str, str],
    log_path: Path,
) -> PhaseResult:
    started = time.monotonic()
    _progress(f"phase {name}: started")
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log_file.write(line)
        returncode = process.wait()
    duration = time.monotonic() - started
    _progress(f"phase {name}: {'passed' if returncode == 0 else 'failed'} after {duration:.1f}s")
    return PhaseResult(name=name, returncode=returncode, duration_seconds=round(duration, 3))


def _junit_counts(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
    root = element_tree.parse(path).getroot()
    cases = list(root.iter("testcase"))
    failed = sum(
        1 for case in cases if case.find("failure") is not None or case.find("error") is not None
    )
    skipped = sum(1 for case in cases if case.find("skipped") is not None)
    return {
        "total": len(cases),
        "passed": len(cases) - failed - skipped,
        "failed": failed,
        "skipped": skipped,
    }


def _write_summary(
    path: Path, *, phases: list[PhaseResult], browser_counts: dict[str, int]
) -> None:
    payload = {
        "kind": "profile-conversion-ux-smoke-v1",
        "phase_count": len(phases),
        "phases": [
            {
                "name": phase.name,
                "status": "passed" if phase.returncode == 0 else "failed",
                "duration_seconds": phase.duration_seconds,
            }
            for phase in phases
        ],
        "browser_scenarios": browser_counts,
        "failure_artifacts": "failures",
        "privacy": "no policy values, profile metadata, identifiers, or plan digests retained",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / "profile-conversion-ux",
        help="ignored local output directory for logs, JUnit, summary, and failed browser artifacts",
    )
    args = parser.parse_args(argv)
    artifact_dir = args.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    failures_dir = artifact_dir / "failures"
    junit_path = artifact_dir / "browser-junit.xml"
    environment = dict(os.environ)
    environment["BPM_BROWSER_ARTIFACT_DIR"] = str(failures_dir)

    _progress("phase 1/3: semantic module checks (0/2 complete)")
    module_result = _run_phase(
        "1/3 semantic-modules",
        ["node", "--test", "--test-timeout=10000", *MODULE_TESTS],
        environment=environment,
        log_path=artifact_dir / "semantic-modules.log",
    )
    _progress("phase 2/3: Chromium/Selenium scenarios (0/3 complete)")
    browser_result = _run_phase(
        "2/3 chromium-scenarios",
        [
            sys.executable,
            "-m",
            "pytest",
            "-o",
            "addopts=",
            "-q",
            "-s",
            "-rs",
            f"--junitxml={junit_path}",
            BROWSER_TEST,
        ],
        environment=environment,
        log_path=artifact_dir / "chromium-scenarios.log",
    )
    counts = _junit_counts(junit_path)
    _progress(
        "phase 3/3: browser scenarios "
        f"{counts['passed']}/{counts['total']} passed; "
        f"{counts['skipped']} skipped; {counts['failed']} failed"
    )
    all_passed = module_result.returncode == 0 and browser_result.returncode == 0
    summary_result = PhaseResult(
        name="3/3 retained-summary",
        returncode=0 if all_passed else 1,
        duration_seconds=0.0,
    )
    _write_summary(
        artifact_dir / "run-summary.json",
        phases=[module_result, browser_result, summary_result],
        browser_counts=counts,
    )
    _progress(
        f"terminal {'PASS' if all_passed else 'FAIL'}; summary {artifact_dir / 'run-summary.json'}"
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
