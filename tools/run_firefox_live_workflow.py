#!/usr/bin/env python3
"""Run one deterministic, provisioned Firefox live-test channel safely.

The GitHub workflow invokes this helper after provisioning.  It verifies the
immutable install again, streams pytest output, writes a small terminal
envelope, and leaves only reviewable failure evidence under ``artifacts/``.
The tested policy scenarios use only loopback servers; AMO is deliberately not
part of this runner.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as element_tree
from pathlib import Path
from typing import Any

try:  # Direct Make invocation has ``tools/`` rather than the repository on sys.path.
    from tools.provision_firefox_live_browsers import (
        DEFAULT_MANIFEST,
        DEFAULT_ROOT,
        ProvisioningError,
        host_platform,
        load_spec,
        verify_installation,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised by the Make command, not imports.
    from provision_firefox_live_browsers import (  # type: ignore[no-redef]
        DEFAULT_MANIFEST,
        DEFAULT_ROOT,
        ProvisioningError,
        host_platform,
        load_spec,
        verify_installation,
    )

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANNELS = ("release", "esr153", "esr140")
LIVE_TEST_PATHS = (
    "tests/live/firefox/test_policy_scenarios.py",
    "tests/live/firefox/test_persisted_profile_e2e.py",
)
DEFAULT_TIMEOUT_SECONDS = 1_200
_TMP_PATH = re.compile(r"/(?:tmp|var/folders)/[^\s\"']+")


def _progress(message: str) -> None:
    print(message, flush=True)


def _safe_log(text: str) -> str:
    """Keep a failure log useful without retaining workstation paths or tokens."""

    normalized = text.replace(str(REPO_ROOT), "<repo>")
    normalized = _TMP_PATH.sub("<tmp>", normalized)
    return re.sub(r"(?i)(token|password|secret)=([^\s&]+)", r"\1=<redacted>", normalized)


def _failed_scenarios(junit_path: Path) -> list[str]:
    if not junit_path.is_file():
        return []
    try:
        root = element_tree.parse(junit_path).getroot()
    except element_tree.ParseError:
        return []
    failed: list[str] = []
    for case in root.iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            classname = case.get("classname", "")
            name = case.get("name", "")
            failed.append("::".join(part for part in (classname, name) if part))
    return failed


def _junit_result_counts(junit_path: Path) -> dict[str, int]:
    """Return terminal scenario counts from the JUnit report.

    The human pytest log includes skipped scenarios only when there are any,
    but final release evidence also needs an explicit machine-readable zero.
    Count testcase nodes directly so nested JUnit suites remain accurate.
    """

    counts = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    if not junit_path.is_file():
        return counts
    try:
        root = element_tree.parse(junit_path).getroot()
    except element_tree.ParseError:
        return counts
    for case in root.iter("testcase"):
        counts["total"] += 1
        if case.find("failure") is not None:
            counts["failed"] += 1
        elif case.find("error") is not None:
            counts["errors"] += 1
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    return counts


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pytest_command(junit_path: Path, pytest_work_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-q",
        *LIVE_TEST_PATHS,
        "-m",
        "firefox_live",
        "-rs",
        f"--basetemp={pytest_work_dir}",
        f"--junitxml={junit_path}",
    ]


def _terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:  # pragma: no cover - GitHub workflow is Linux, retained for local use.
        process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:  # pragma: no cover - see above.
            process.kill()


def _run_streamed(
    command: list[str], *, timeout_seconds: int, log_path: Path, progress_label: str
) -> tuple[int, bool]:
    """Stream pytest output and enforce an end-to-end channel timeout."""

    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "BPM_FIREFOX_LIVE_LOCAL_ONLY": "1",
            "BPM_FIREFOX_LIVE_ARTIFACT_DIR": str(log_path.parent / "failures"),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    lines: list[str] = []
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    next_heartbeat = started + 30
    while True:
        if process.poll() is not None:
            break
        now = time.monotonic()
        elapsed = now - started
        if elapsed >= timeout_seconds:
            timed_out = True
            _progress(
                f"Firefox live timeout after {timeout_seconds}s; terminating test process group"
            )
            _terminate(process)
            break
        if now >= next_heartbeat:
            _progress(
                f"Firefox live [{progress_label}] pytest still running after {elapsed:.0f}s "
                f"of {timeout_seconds}s"
            )
            next_heartbeat += 30
        for key, _event in selector.select(timeout=min(1.0, timeout_seconds - elapsed)):
            line = key.fileobj.readline()
            if line:
                lines.append(line)
                _progress(line.rstrip())
    selector.close()
    remaining, _ = process.communicate()
    if remaining:
        lines.append(remaining)
        for line in remaining.splitlines():
            _progress(line)
    log_path.write_text(_safe_log("".join(lines)), encoding="utf-8")
    return process.returncode if process.returncode is not None else 1, timed_out


def _append_github_summary(summary: dict[str, Any]) -> None:
    target = os.getenv("GITHUB_STEP_SUMMARY")
    if not target:
        return
    status = summary["status"]
    failed = summary["failed_scenarios"]
    lines = [
        f"## Firefox deterministic live: `{summary['channel']}`",
        "",
        f"- Status: **{status}**",
        f"- Duration: {summary['duration_seconds']:.1f}s",
        f"- Firefox: `{summary['versions']['firefox']['actual_version']}`",
        f"- geckodriver: `{summary['versions']['geckodriver']['actual_version']}`",
        "- Scope: provisioned local Firefox policy tests only; AMO is excluded.",
    ]
    if failed:
        lines.extend(["- Failed scenarios:", *[f"  - `{scenario}`" for scenario in failed]])
    with Path(target).open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def run_channel(
    *,
    channel: str,
    artifact_dir: Path,
    timeout_seconds: int,
    provision_root: Path = DEFAULT_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> int:
    if channel not in CHANNELS:
        raise ValueError(
            f"Unsupported Firefox live channel {channel!r}; expected one of {', '.join(CHANNELS)}"
        )
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be positive")

    artifact_dir.mkdir(parents=True, exist_ok=True)
    junit_path = artifact_dir / "junit.xml"
    log_path = artifact_dir / "pytest.log"
    pytest_work_dir = artifact_dir / ".pytest-work"
    shutil.rmtree(pytest_work_dir, ignore_errors=True)
    _progress(f"Firefox live [{channel}] phase 1/3: verifying immutable provisioned install")
    spec = load_spec(manifest_path.resolve(), channel=channel, platform_name=host_platform())
    versions = verify_installation(provision_root.resolve(), spec)
    _write_json(artifact_dir / "versions.json", versions)

    _progress(f"Firefox live [{channel}] phase 2/3: running local deterministic scenarios")
    started = time.monotonic()
    try:
        return_code, timed_out = _run_streamed(
            _pytest_command(junit_path, pytest_work_dir),
            timeout_seconds=timeout_seconds,
            log_path=log_path,
            progress_label=channel,
        )
    finally:
        shutil.rmtree(pytest_work_dir, ignore_errors=True)
    duration = time.monotonic() - started
    failed = _failed_scenarios(junit_path)
    result_counts = _junit_result_counts(junit_path)
    status = (
        "passed" if return_code == 0 and not timed_out else "timed_out" if timed_out else "failed"
    )
    summary: dict[str, Any] = {
        "schema_version": 1,
        "channel": channel,
        "status": status,
        "exit_code": return_code,
        "timed_out": timed_out,
        "duration_seconds": round(duration, 3),
        "scenario_scope": list(LIVE_TEST_PATHS),
        "result_counts": result_counts,
        "failed_scenarios": failed,
        "versions": versions,
        "failure_artifacts": "failures",
        "network_scope": "local loopback policy fixtures after provisioning; AMO excluded",
    }
    _write_json(artifact_dir / "run-summary.json", summary)
    _append_github_summary(summary)
    _progress(
        f"Firefox live [{channel}] phase 3/3: {status}; "
        f"duration {duration:.1f}s; summary {artifact_dir / 'run-summary.json'}"
    )
    return 0 if status == "passed" else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channel", choices=CHANNELS)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--provision-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return run_channel(
            channel=args.channel,
            artifact_dir=args.artifact_dir.resolve(),
            timeout_seconds=args.timeout_seconds,
            provision_root=args.provision_root,
            manifest_path=args.manifest,
        )
    except (ProvisioningError, ValueError, OSError) as error:
        print(f"Firefox live workflow failed before pytest: {error}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
