from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONTRACT = DOCUMENTATION_ROOT / "config/wsl-source-install-validation-contract-0.9.1.json"
RUNNER = DOCUMENTATION_ROOT / "tools/wsl_source_install_validation.ps1"
FEASIBILITY = (
    REPOSITORY_ROOT
    / "docs/architecture/wsl-source-install-validation-feasibility-0.9.1.md"
)
PRIVILEGED = (
    DOCUMENTATION_ROOT
    / "config/live-source-install-privileged-validation-contract-0.9.1.json"
)
EDITORIAL_RECONCILIATION = (
    REPOSITORY_ROOT / "documentation/config/linux-source-install-editorial-reconciliation-0.9.2.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _contract() -> dict:
    return _json(CONTRACT)


def _runner() -> str:
    return RUNNER.read_text(encoding="utf-8")


def test_contract_declares_prepared_runner_without_claiming_windows_evidence() -> None:
    contract = _contract()
    privileged = _json(PRIVILEGED)

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-0.9.1-wsl-source-install-validation"
    assert contract["backlog_item"] == "BPM091-M11-10"
    assert contract["target_bpm_version"] == "0.9.1"
    assert contract["status"] == "runner-prepared-awaiting-actual-windows-hosts"
    assert contract["runner"] == RUNNER.relative_to(REPOSITORY_ROOT).as_posix()
    assert contract["feasibility_record"] == FEASIBILITY.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    assert contract["privileged_contract"] == PRIVILEGED.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    assert privileged["wsl_boundary"]["actual_windows_host_required"] is True
    assert contract["actual_host_gate"]["current_linux_host_can_satisfy_gate"] is False
    assert contract["actual_host_gate"]["container_substitution_allowed"] is False
    assert contract["conditional_outcomes"] == {
        "Windows10": {
            "owner_task": "BPM091-M11-11",
            "current_status": "unverified-no-actual-host-supplied",
            "validation_claimed": False,
            "evidence": (
                "documentation/evidence/live-source-install/0.9.1/"
                "m11-11-windows10-wsl-20260715/run-manifest.json"
            ),
        },
        "Windows11": {
            "owner_task": "BPM091-M11-12",
            "current_status": "unverified-no-actual-host-supplied",
            "validation_claimed": False,
            "evidence": (
                "documentation/evidence/live-source-install/0.9.1/"
                "m11-12-windows11-wsl-20260715/run-manifest.json"
            ),
        },
    }


def test_runner_reuses_the_reconciled_ubuntu_source_install_contract() -> None:
    reuse = _contract()["source_install_reuse"]
    source = REPOSITORY_ROOT / reuse["source_topic"]
    historical = _json(REPOSITORY_ROOT / reuse["reconciliation_report"])
    current = next(
        target
        for target in _json(EDITORIAL_RECONCILIATION)["current_source_contract"]["targets"]
        if target["id"] == reuse["target_id"]
    )

    assert reuse["target_id"] == "ubuntu-26-04"
    assert reuse["command_contract"] == (
        "documentation/config/linux-source-install-command-contract-0.9.1.json"
    )
    assert reuse["reconciliation_report"] == (
        "docs/architecture/linux-source-install-validation-0.9.1.json"
    )
    assert reuse["validated_source_sha256"] == next(
        target["reconciled_source_sha256"]
        for target in historical["targets"]
        if target["target_id"] == reuse["target_id"]
    )
    assert reuse["validated_source_sha256"] != hashlib.sha256(source.read_bytes()).hexdigest()
    command_contract = _json(REPOSITORY_ROOT / reuse["command_contract"])
    ubuntu = next(target for target in command_contract["targets"] if target["id"] == "ubuntu-26-04")
    assert ubuntu["topic_id"] in source.name
    assert current["topic_id"] == ubuntu["topic_id"]
    assert "exact documented Linux userspace procedure" in reuse["rule"]
    assert "0.0.0.0" in reuse["wsl_runtime_adapter"]
    assert "does not change" in reuse["wsl_runtime_adapter"]


def test_contract_covers_every_required_actual_host_check_once() -> None:
    checks = _contract()["checks"]
    expected = [
        "windows-build",
        "wsl-version",
        "distribution-identity",
        "systemd-mode",
        "filesystem-location",
        "installed-source-assertions",
        "localhost-behavior",
        "browser-access",
        "shutdown",
        "wsl-restart",
        "evidence-capture",
    ]

    assert [check["id"] for check in checks] == expected
    assert len(checks) == len({check["id"] for check in checks})
    for check in checks:
        assert check["owner"]
        assert check["required_evidence"]
        assert check["pass_rule"]


def test_runner_fails_closed_on_host_wsl_identity_and_filesystem() -> None:
    runner = _runner()

    for parameter in (
        "[string]$WindowsTarget",
        "[string]$Distro",
        "[string]$BpmRef",
        "[string]$CheckoutPath",
        "[switch]$PreflightOnly",
    ):
        assert parameter in runner
    for token in (
        "[PlatformID]::Win32NT",
        "Get-CimInstance Win32_OperatingSystem",
        '"wsl.exe"',
        '@("--version")',
        '@("--status")',
        '@("--list", "--verbose")',
        '"\\s+2\\s*$"',
        "/etc/os-release",
        "/proc/version",
        "systemctl is-system-running",
        "/etc/wsl.conf",
        "wslpath -w",
        "stat -f -c %T",
        "^/home/",
        "^/(mnt|media)/",
        "^[0-9a-f]{40}$",
    ):
        assert token in runner
    assert _contract()["actual_host_gate"]["required_distribution"] == {
        "ID": "ubuntu",
        "VERSION_ID": "26.04",
    }
    assert _contract()["actual_host_gate"]["required_wsl_generation"] == 2


def test_runner_checks_installed_source_docs_and_two_runtime_cycles() -> None:
    runner = _runner()

    for token in (
        "git rev-parse HEAD",
        "git status --short",
        "sys.version_info >= (3, 14)",
        "alembic upgrade head",
        "alembic current",
        "make docs-validate",
        "make docs-build",
        "make docs-install-dev",
        "Invoke-RuntimeCycle -Cycle 1",
        "Invoke-RuntimeCycle -Cycle 2",
        "BPM_HOST='0.0.0.0'",
        "BPM_RELOAD='true'",
        "make dev",
    ):
        assert token in runner
    workflow = _contract()["workflow"]
    assert len(workflow["full_validation"]) == 9
    assert "closes no Windows 10/11" in workflow["success_claim"]


def test_runner_checks_wsl_windows_edge_shutdown_and_restart_boundaries() -> None:
    runner = _runner()

    for token in (
        "curl -fsS --max-time 5",
        "Invoke-WebRequest",
        "/health",
        "/health/ready",
        "/profiles",
        "msedge.exe",
        "--headless=new",
        "--dump-dom",
        "(?i)<html",
        "kill -TERM",
        "cycle-$Cycle-wsl-post-stop",
        "cycle-$Cycle-windows-post-stop",
        '@("--terminate", $Distro)',
        "wsl-restart-identity",
        "wsl-restart-old-runtime-absent",
    ):
        assert token in runner
    assert runner.count("Invoke-RuntimeCycle -Cycle") == 2
    assert runner.count("Assert-BrowserAccess -Cycle $Cycle") == 1
    assert "connection-refused" in runner


def test_runner_captures_bounded_hashed_evidence_and_blocked_summaries() -> None:
    runner = _runner()
    evidence = _contract()["evidence"]
    required_evidence = " ".join(
        item
        for check in _contract()["checks"]
        for item in check["required_evidence"]
    )

    for filename in (
        "events.jsonl",
        "host.json",
        "wsl.json",
        "source-assertions.txt",
        "probes.json",
        "summary.json",
        "sha256.json",
    ):
        assert filename in runner
        assert filename in required_evidence
    for template in (
        '"browser-cycle-$Cycle.html"',
        '"runtime-cycle-$Cycle.log"',
    ):
        assert template in runner
    for field in evidence["command_record_fields"]:
        assert field in runner
    assert 'status = "blocked"' in runner
    assert '"preflight-pass-not-windows-validation"' in runner
    assert '"accepted-actual-windows-wsl-validation-candidate"' in runner
    assert "Get-FileHash" in runner
    assert "sha256" in runner.casefold()
    assert evidence["status_values"] == ["pass", "blocked"]


def test_runner_contains_no_install_network_service_docker_or_destructive_path() -> None:
    runner = _runner().casefold()
    forbidden = (
        "wsl --install",
        "wsl.exe --install",
        "--unregister",
        "new-netfirewallrule",
        "set-netfirewallprofile",
        "netsh ",
        "portproxy",
        "set-itemproperty",
        "new-service",
        "sc.exe",
        "docker.exe",
        "docker run",
        "docker create",
        "remove-item",
        "rm -rf",
        "shutdown.exe",
        "restart-computer",
    )

    assert all(token not in runner for token in forbidden)
    safety = _contract()["safety"]
    assert any("terminate and restart only" in item for item in safety["runner_may"])
    assert any("install, update, unregister" in item for item in safety["runner_must_not"])
    assert any("change Windows Firewall" in item for item in safety["runner_must_not"])
    assert any("run Docker" in item for item in safety["runner_must_not"])


def test_powershell_structure_and_feasibility_handoff_are_reviewable() -> None:
    runner = _runner()
    feasibility = FEASIBILITY.read_text(encoding="utf-8")

    assert runner.count("@'") == runner.count("'@") == 8
    assert runner.count("function ") >= 14
    assert "try {" in runner
    assert "} finally {" in runner
    assert runner.rstrip().endswith(
        'Write-Output "WSL validation $status. Evidence: $script:EvidenceDirectory"'
    )
    for token in (
            "Runner prepared; actual Windows hosts required",
            "BPM091-M11-11",
            "BPM091-M11-12",
            "unverified-no-actual-host-supplied",
            "Current Linux host: unsuitable",
        "cannot turn this preparation task into Windows/WSL execution evidence",
    ):
        assert token in feasibility
