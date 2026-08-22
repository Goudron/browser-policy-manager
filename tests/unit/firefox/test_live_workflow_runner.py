from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import tools.run_firefox_live_workflow as live_runner


def test_safe_log_removes_repo_temp_paths_and_sensitive_query_values() -> None:
    source = f"{live_runner.REPO_ROOT}/tests /tmp/bpm-run token=abc password=xyz"

    safe = live_runner._safe_log(source)

    assert str(live_runner.REPO_ROOT) not in safe
    assert "/tmp/bpm-run" not in safe
    assert "token=<redacted>" in safe
    assert "password=<redacted>" in safe


def test_failed_scenarios_reads_only_junit_failure_or_error_cases(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """<testsuite>
        <testcase classname="tests.live.firefox.test_policy_scenarios" name="test_ok" />
        <testcase classname="tests.live.firefox.test_policy_scenarios" name="test_failed"><failure /></testcase>
        <testcase classname="tests.live.firefox.test_persisted_profile_e2e" name="test_error"><error /></testcase>
        </testsuite>""",
        encoding="utf-8",
    )

    assert live_runner._failed_scenarios(report) == [
        "tests.live.firefox.test_policy_scenarios::test_failed",
        "tests.live.firefox.test_persisted_profile_e2e::test_error",
    ]
    assert live_runner._junit_result_counts(report) == {
        "total": 3,
        "passed": 1,
        "failed": 1,
        "errors": 1,
        "skipped": 0,
    }


def test_junit_result_counts_records_explicit_skips(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """<testsuite>
        <testcase name="test_ok" />
        <testcase name="test_skipped"><skipped /></testcase>
        </testsuite>""",
        encoding="utf-8",
    )

    assert live_runner._junit_result_counts(report) == {
        "total": 2,
        "passed": 1,
        "failed": 0,
        "errors": 0,
        "skipped": 1,
    }


def test_runner_writes_terminal_channel_summary_without_external_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    versions = {
        "firefox": {"actual_version": "Mozilla Firefox 153.0.1"},
        "geckodriver": {"actual_version": "geckodriver 0.37.1"},
    }
    monkeypatch.setattr(live_runner, "host_platform", lambda: "linux-x86_64")
    monkeypatch.setattr(live_runner, "load_spec", lambda *args, **kwargs: object())
    monkeypatch.setattr(live_runner, "verify_installation", lambda *args, **kwargs: versions)

    def fake_run(
        command: list[str],
        *,
        timeout_seconds: int,
        log_path: Path,
        progress_label: str,
        environment: dict[str, str],
    ) -> tuple[int, bool]:
        assert command[-1].startswith("--junitxml=")
        assert any(argument.startswith("--basetemp=") for argument in command)
        assert timeout_seconds == 12
        assert progress_label == "release"
        assert environment == {
            "BPM_FIREFOX_CHANNEL": "release",
            "BPM_FIREFOX_LIVE_SCHEMA_ARTIFACT": "release-153",
        }
        log_path.write_text("safe local log\n", encoding="utf-8")
        return 0, False

    monkeypatch.setattr(live_runner, "_run_streamed", fake_run)
    artifacts = tmp_path / "artifacts"

    assert (
        live_runner.run_channel(
            channel="release",
            artifact_dir=artifacts,
            timeout_seconds=12,
            provision_root=tmp_path / "provisioned",
            manifest_path=tmp_path / "manifest.json",
        )
        == 0
    )

    summary = json.loads((artifacts / "run-summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "passed"
    assert summary["channel"] == "release"
    assert summary["matrix_position"] == {"current": 1, "total": 1}
    assert summary["result_counts"] == {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
    }
    assert (
        summary["network_scope"]
        == "local loopback policy fixtures after provisioning; AMO excluded"
    )
    assert summary["schema_artifact"]["artifact_id"] == "release-153"
    assert len(summary["schema_artifact"]["sha256"]) == 64
    assert summary["unsupported_cases"] == []
    assert (artifacts / "versions.json").is_file()


def test_runner_retains_preflight_failure_diagnostic_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(live_runner, "host_platform", lambda: "linux-x86_64")
    monkeypatch.setattr(live_runner, "load_spec", lambda *args, **kwargs: object())

    def fail_verify(*_args, **_kwargs):
        raise live_runner.ProvisioningError("missing verified esr115 installation")

    monkeypatch.setattr(live_runner, "verify_installation", fail_verify)
    artifacts = tmp_path / "artifacts"

    assert (
        live_runner.run_channel(
            channel="esr115",
            artifact_dir=artifacts,
            timeout_seconds=12,
            provision_root=tmp_path / "provisioned",
            manifest_path=tmp_path / "manifest.json",
            matrix_position=(4, 4),
        )
        == 1
    )

    summary = json.loads((artifacts / "run-summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "provisioning_failed"
    assert summary["matrix_position"] == {"current": 4, "total": 4}
    assert "missing verified esr115 installation" in summary["diagnostic"]
    assert (artifacts / "pytest.log").is_file()


def test_four_channel_runner_continues_after_a_failed_channel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, tuple[int, int]]] = []

    def fake_run_channel(*, channel: str, artifact_dir: Path, matrix_position, **_kwargs) -> int:
        calls.append((channel, matrix_position))
        artifact_dir.mkdir(parents=True)
        status = "failed" if channel == "esr140" else "passed"
        (artifact_dir / "run-summary.json").write_text(
            json.dumps({"status": status}), encoding="utf-8"
        )
        return 1 if status == "failed" else 0

    monkeypatch.setattr(live_runner, "run_channel", fake_run_channel)
    artifacts = tmp_path / "matrix"

    assert (
        live_runner.run_channels(
            channels=live_runner.CHANNELS,
            artifact_dir=artifacts,
            timeout_seconds=12,
        )
        == 1
    )

    assert calls == [
        ("release", (1, 4)),
        ("esr153", (2, 4)),
        ("esr140", (3, 4)),
        ("esr115", (4, 4)),
    ]
    matrix = json.loads((artifacts / "matrix-summary.json").read_text(encoding="utf-8"))
    assert matrix["completed_channels"] == 4
    assert matrix["status"] == "failed"


def test_runner_rejects_unknown_channel_before_writing_artifacts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported Firefox live channel"):
        live_runner.run_channel(
            channel="nightly",
            artifact_dir=tmp_path / "artifacts",
            timeout_seconds=1,
        )


def test_make_target_runs_the_timeout_bounded_workflow_runner() -> None:
    source = (live_runner.REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "firefox-live-workflow:" in source
    assert "tools/run_firefox_live_workflow.py $(FIREFOX_CHANNEL)" in source
    assert "--timeout-seconds $(FIREFOX_LIVE_TIMEOUT_SECONDS)" in source
    assert "firefox-live-four-channel-workflow:" in source
    assert "tools/provision_firefox_live_browsers.py all" in source
    assert "tools/run_firefox_live_workflow.py all" in source


def test_streamed_runner_enforces_timeout_when_pytest_writes_no_output(tmp_path: Path) -> None:
    return_code, timed_out = live_runner._run_streamed(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout_seconds=1,
        log_path=tmp_path / "pytest.log",
        progress_label="release",
        environment={"BPM_FIREFOX_CHANNEL": "release"},
    )

    assert timed_out is True
    assert return_code != 0
    assert (tmp_path / "pytest.log").read_text(encoding="utf-8") == ""
