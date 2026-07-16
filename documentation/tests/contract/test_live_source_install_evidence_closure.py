from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CLOSURE = (
    ROOT
    / "documentation/evidence/live-source-install/0.9.1/"
    "m11-14-evidence-closure-20260715/closure.json"
)
COMMAND_CONTRACT = (
    ROOT / "documentation/config/linux-source-install-command-contract-0.9.1.json"
)
RECONCILIATION = ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
WSL_CONTRACT = (
    ROOT / "documentation/config/wsl-source-install-validation-contract-0.9.1.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _documented_command_count(path: Path) -> int:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    return sum(
        1
        for codeblock in root.findall(".//codeblock")
        for line in "".join(codeblock.itertext()).splitlines()
        if line.strip()
    )


def test_closure_accepts_only_the_complete_m11_live_install_scope() -> None:
    closure = _json(CLOSURE)
    decision = closure["decision"]

    assert closure["schema_version"] == 1
    assert closure["backlog_item"] == "BPM091-M11-14"
    assert closure["target_bpm_version"] == "0.9.1"
    assert closure["status"] == "accepted"
    assert closure["result"] == (
        "milestone-11-live-install-scope-ready-with-conditional-wsl-boundaries"
    )
    assert decision["mandatory_linux_target_count"] == 5
    assert decision["mandatory_linux_pass_count"] == 5
    assert decision["unresolved_mandatory_failures"] == []
    assert decision["conditional_wsl_outcome_count"] == 2
    assert decision["conditional_wsl_validation_claim_count"] == 0
    assert decision["environment_handoff_complete"] is True
    assert decision["milestone_11_live_install_scope_ready"] is True
    assert decision["overall_bpm_0_9_1_release_ready_claimed"] is False


def test_each_linux_target_links_current_commands_to_an_accepted_transcript() -> None:
    closure = _json(CLOSURE)
    expected_ids = [target["id"] for target in _json(COMMAND_CONTRACT)["targets"]]
    records = closure["linux_targets"]

    assert [record["target_id"] for record in records] == expected_ids
    assert len(records) == len({record["target_id"] for record in records}) == 5
    for record in records:
        source = ROOT / record["source_topic"]
        manifest = _json(ROOT / record["accepted_manifest"])
        attempt = next(
            item
            for item in manifest["attempts"]
            if item["attempt"] == record["accepted_attempt"]
        )
        command_evidence = record["command_evidence"]

        assert source.is_file()
        assert _sha256(source) == record["reconciled_source_sha256"]
        assert _documented_command_count(source) == command_evidence[
            "documented_command_count"
        ]
        assert manifest["status"] == "accepted"
        assert manifest["result"] == "pass"
        assert attempt["accepted_disposition"] == "accepted-clean-source-install-pass"
        assert attempt["documented_commands_completed"] == command_evidence[
            "documented_command_count"
        ]
        assert attempt["documented_command_failures"] == command_evidence[
            "documented_command_failures"
        ] == 0
        assert attempt["documented_stage_counts"] == command_evidence["stage_counts"]
        assert sum(command_evidence["stage_counts"].values()) == command_evidence[
            "documented_command_count"
        ]
        assert attempt["transcript_sha256"]["plan.json"] == command_evidence[
            "plan_sha256"
        ]
        assert attempt["transcript_sha256"]["events.jsonl"] == command_evidence[
            "events_sha256"
        ]
        assert attempt["completion_marker_present"] is True
        assert attempt["host_completion_guard_passed"] is True


def test_each_expected_result_is_bound_to_the_accepted_attempt() -> None:
    for record in _json(CLOSURE)["linux_targets"]:
        source_root = ET.fromstring(
            (ROOT / record["source_topic"]).read_text(encoding="utf-8")
        )
        manifest = _json(ROOT / record["accepted_manifest"])
        accepted = manifest["accepted_attempt"]
        result = record["result_evidence"]

        assert source_root.find("./taskbody/result") is not None
        assert source_root.find("./taskbody/postreq") is not None
        assert accepted["python_version"] == result["python_version"]
        assert accepted["editable_bpm_install"] == result["editable_bpm_install"]
        assert accepted["latest_migration"] == result["latest_migration"]
        assert {
            accepted["docs_validate_all_six_locales"],
            accepted["docs_build_all_six_locales"],
            accepted["docs_install_dev_all_six_locales"],
        } == {result["docs_all_six_locales"]} == {"pass"}
        assert accepted["runtime_start"] == "pass"
        assert accepted["runtime_log_sha256"] == result["runtime_log_sha256"]
        assert [probe["path"] for probe in accepted["probes"]] == result["probe_paths"]
        assert {probe["status"] for probe in accepted["probes"]} == {
            result["probe_status"]
        }
        assert accepted["runtime_shutdown"] == result["runtime_shutdown"]
        assert accepted["post_shutdown_health_probe"] == result["post_stop_probe"]
        assert accepted["completion_marker"] == result["completion"]


def test_reconciliation_preserves_dispositions_hashes_and_clean_correction() -> None:
    closure = {item["target_id"]: item for item in _json(CLOSURE)["linux_targets"]}
    reconciliation = {
        item["target_id"]: item for item in _json(RECONCILIATION)["targets"]
    }

    assert closure.keys() == reconciliation.keys()
    for target_id, record in closure.items():
        reconciled = reconciliation[target_id]
        assert record["accepted_manifest"] == reconciled["manifest"]
        assert record["accepted_attempt"] == reconciled["accepted_attempt"]
        assert record["reconciled_source_sha256"] == reconciled[
            "reconciled_source_sha256"
        ]
        assert record["disposition"] == reconciled["disposition"]
        assert record["command_evidence"]["events_sha256"] == reconciled[
            "accepted_events_sha256"
        ]

    manjaro = closure["manjaro-stable-2026-06-26"]["command_evidence"]
    correction = reconciliation["manjaro-stable-2026-06-26"]
    assert manjaro["diagnostic_events_sha256"] == correction[
        "diagnostic_events_sha256"
    ]
    assert correction["procedure_corrections"][0]["clean_rerun"] == (
        "attempt 2 passed all 37 documented commands"
    )


def test_wsl_outcomes_match_actual_host_evidence_without_validation_claims() -> None:
    closure = _json(CLOSURE)
    contract = _json(WSL_CONTRACT)
    records = closure["conditional_wsl_outcomes"]

    assert [record["target"] for record in records] == ["Windows10", "Windows11"]
    for record in records:
        outcome = contract["conditional_outcomes"][record["target"]]
        evidence = _json(ROOT / record["evidence"])
        disposition_key = record["target"].replace("Windows", "windows_").lower()

        assert record["owner_task"] == outcome["owner_task"]
        assert record["status"] == outcome["current_status"]
        assert record["validation_claimed"] is outcome["validation_claimed"] is False
        assert record["evidence"] == outcome["evidence"]
        assert record["result"] == evidence["result"] == "not-run"
        assert evidence["status"] == "accepted-unverified-boundary"
        assert evidence["target"]["actual_windows_host_supplied"] is False
        assert evidence["disposition"][disposition_key] == record["status"]
        assert evidence["disposition"]["actual_host_evidence_present"] is False
        assert set(evidence["claims"].values()) == {False}
        assert record["future_actual_host_rerun_allowed"] is True
        assert record["release_blocking"] is False


def test_environment_handoff_is_complete_and_retains_the_bounded_inventory() -> None:
    handoff = _json(CLOSURE)["environment_handoff"]
    manifest = _json(ROOT / handoff["manifest"])
    inventory = _json(ROOT / handoff["inventory"])

    assert handoff["status"] == manifest["status"] == inventory["status"] == "accepted"
    assert handoff["containers_stopped"] == manifest["observations"][
        "containers_stopped"
    ] == inventory["retention"]["container_count"] == 13
    assert handoff["images_retained"] == inventory["retention"]["image_count"] == 5
    assert handoff["network_retained"] == inventory["retention"]["network_count"] == 1
    assert handoff["docker_engine_retained"] is inventory["retention"][
        "docker_engine_retained"
    ] is True
    assert handoff["deletion_performed"] is manifest["retention_decision"][
        "deletion_performed"
    ] is inventory["handoff"]["deletion_performed"] is False
    assert handoff["storage_boundary_pass"] is inventory["storage"][
        "within_contract"
    ] is True
    assert handoff["host_integrity_pass"] is manifest["observations"][
        "host_integrity_pass"
    ] is True


def test_closure_lists_every_focused_contract_and_does_not_start_a_server() -> None:
    closure = _json(CLOSURE)
    contracts = closure["focused_contracts"]

    assert len(contracts) == len(set(contracts)) == 13
    assert CLOSURE.relative_to(ROOT).as_posix().startswith(
        "documentation/evidence/live-source-install/0.9.1/"
    )
    assert (
        "documentation/tests/contract/test_live_source_install_evidence_closure.py"
        in contracts
    )
    assert all((ROOT / path).is_file() for path in contracts)
    assert closure["verification"] == {
        "focused_contract": "pass-37",
        "full_documentation_contract": "pass-740-with-4-deselected",
        "docs_snapshot": "pass",
        "docs_validate": "pass-six-locales",
        "docs_install_dev": "pass",
        "dev_server_started": False,
    }
