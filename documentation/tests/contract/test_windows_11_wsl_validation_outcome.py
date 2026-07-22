from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/"
    "m11-12-windows11-wsl-20260715/run-manifest.json"
)
CONTRACT = (
    REPOSITORY_ROOT
    / "documentation/config/wsl-source-install-validation-contract-0.9.1.json"
)
EDITORIAL_RECONCILIATION = (
    REPOSITORY_ROOT / "documentation/config/linux-source-install-editorial-reconciliation-0.9.2.json"
)
RUNNER = REPOSITORY_ROOT / "documentation/tools/wsl_source_install_validation.ps1"
SOURCE_TOPIC = (
    REPOSITORY_ROOT
    / "documentation/src/dita/en/admin/admin-task-install-ubuntu-26-04-source.dita"
)
FEASIBILITY = (
    REPOSITORY_ROOT
    / "docs/architecture/wsl-source-install-validation-feasibility-0.9.1.md"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_windows_11_outcome_is_an_accepted_unverified_boundary() -> None:
    evidence = _json(EVIDENCE)

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-12"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == "accepted-unverified-boundary"
    assert evidence["result"] == "not-run"
    assert evidence["target"]["windows_target"] == "Windows11"
    assert evidence["target"]["actual_windows_host_required"] is True
    assert evidence["target"]["actual_windows_host_supplied"] is False
    assert evidence["target"]["windows_installation_media_supplied"] is False
    assert evidence["disposition"]["windows_11"] == (
        "unverified-no-actual-host-supplied"
    )
    assert evidence["disposition"]["actual_host_evidence_present"] is False


def test_linux_executor_without_iso_cannot_be_windows_or_wsl_evidence() -> None:
    evidence = _json(EVIDENCE)
    executor = evidence["observed_executor"]

    assert executor["suitability"] == "unsuitable-non-windows-host"
    assert executor["os_family"] == "Linux"
    assert executor["distribution"]["ID"] == "ubuntu"
    assert executor["distribution"]["VERSION_ID"] == "26.04"
    assert set(executor["command_availability"].values()) == {"absent"}
    assert evidence["runner"]["preflight_attempted"] is False
    assert evidence["runner"]["full_validation_attempted"] is False
    assert evidence["source_install_reference"]["execution_reused"] is False


def test_every_actual_host_check_remains_explicitly_not_run() -> None:
    evidence = _json(EVIDENCE)
    contract = _json(CONTRACT)

    assert [outcome["id"] for outcome in evidence["check_outcomes"]] == [
        check["id"] for check in contract["checks"]
    ]
    assert {outcome["status"] for outcome in evidence["check_outcomes"]} == {
        "not-run-no-actual-host"
    }


def test_outcome_makes_no_windows_wsl_browser_or_production_claim() -> None:
    evidence = _json(EVIDENCE)

    assert set(evidence["claims"].values()) == {False}
    serialized = json.dumps(evidence)
    for field in ("Caption", "BuildNumber", "OSArchitecture", "wsl_version"):
        assert field not in serialized
    assert evidence["disposition"]["release_interpretation"] == (
        "conditional-outcome-recorded-without-validation-claim"
    )


def test_outcome_is_bound_to_the_prepared_runner_and_source_topic() -> None:
    evidence = _json(EVIDENCE)
    current = next(
        target
        for target in _json(EDITORIAL_RECONCILIATION)["current_source_contract"]["targets"]
        if target["id"] == "ubuntu-26-04"
    )

    assert evidence["runner"]["path"] == RUNNER.relative_to(REPOSITORY_ROOT).as_posix()
    assert evidence["runner"]["sha256"] == hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert evidence["source_install_reference"]["topic"] == SOURCE_TOPIC.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    assert evidence["source_install_reference"]["sha256"] != hashlib.sha256(
        SOURCE_TOPIC.read_bytes()
    ).hexdigest()
    assert current["topic_id"] in SOURCE_TOPIC.name


def test_contract_and_feasibility_record_the_closed_windows_11_boundary() -> None:
    evidence = _json(EVIDENCE)
    contract = _json(CONTRACT)
    feasibility = FEASIBILITY.read_text(encoding="utf-8")
    outcome = contract["conditional_outcomes"]["Windows11"]

    assert outcome == {
        "owner_task": "BPM091-M11-12",
        "current_status": "unverified-no-actual-host-supplied",
        "validation_claimed": False,
        "evidence": EVIDENCE.relative_to(REPOSITORY_ROOT).as_posix(),
    }
    assert contract["conditional_outcomes"]["Windows10"]["current_status"] == (
        "unverified-no-actual-host-supplied"
    )
    assert evidence["disposition"]["next_backlog_item"] == "BPM091-M11-13"
    assert "Windows 11: unverified-no-actual-host-supplied" in feasibility
    assert "makes no Windows 11 validation claim" in feasibility


def test_boundary_record_did_not_start_or_modify_runtime_resources() -> None:
    evidence = _json(EVIDENCE)

    assert set(evidence["safety"].values()) == {False}
    assert evidence["verification"] == {
        "focused_contract": "pass-23",
        "full_documentation_contract": "pass-725-with-4-deselected",
        "docs_snapshot": "pass",
        "docs_validate": "pass-six-locales",
        "docs_install_dev": "pass",
        "dev_server_started": False,
    }
