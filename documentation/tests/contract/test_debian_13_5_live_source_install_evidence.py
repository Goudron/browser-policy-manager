from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/m11-05-debian-source-install-20260714"
)
MANIFEST = EVIDENCE_ROOT / "run-manifest.json"
INVENTORY = EVIDENCE_ROOT / "retained-inventory.json"
HARNESS = REPOSITORY_ROOT / "documentation/config/live-source-install-harness-0.9.1.json"
RECONCILIATION = REPOSITORY_ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
EDITORIAL_RECONCILIATION = (
    REPOSITORY_ROOT / "documentation/config/linux-source-install-editorial-reconciliation-0.9.2.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_debian_live_install_is_accepted_against_an_immutable_091_ref() -> None:
    evidence = _json(MANIFEST)
    source = REPOSITORY_ROOT / evidence["target"]["source_topic"]
    reconciled = next(
        target
        for target in _json(RECONCILIATION)["targets"]
        if target["target_id"] == evidence["target"]["id"]
    )

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-05"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == "accepted"
    assert evidence["result"] == "pass"
    assert evidence["target"]["identity"] == {
        "ID": "debian",
        "VERSION_ID": "13",
        "debian_version": "13.5",
    }
    assert evidence["target"]["source_sha256"] == reconciled["validated_source_sha256"]
    current = next(
        target
        for target in _json(EDITORIAL_RECONCILIATION)["current_source_contract"]["targets"]
        if target["id"] == evidence["target"]["id"]
    )
    assert current["topic_id"] in source.name
    assert all(
        command not in source.read_text(encoding="utf-8")
        for command in _json(EDITORIAL_RECONCILIATION)["current_source_contract"]["removed_maintainer_commands"]
    )
    snapshot = evidence["source_snapshot"]
    assert snapshot["validation_branch"] == "validation/bpm-0.9.1-m11"
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["accepted_ref"])
    assert all(
        attempt["bpm_ref"] == snapshot["accepted_ref"]
        for attempt in evidence["attempts"]
    )
    assert snapshot["accepted_ref_version"] == "0.9.1"
    assert snapshot["remote_ref_fetched_and_verified"] is True
    assert snapshot["normal_development_branch_changed"] is False


def test_login_shell_path_diagnostic_cannot_be_accepted_or_reused() -> None:
    evidence = _json(MANIFEST)
    diagnostic, accepted = evidence["attempts"]

    assert diagnostic["raw_harness_result"] == "blocked"
    assert (
        diagnostic["accepted_disposition"]
        == "retained-diagnostic-login-shell-path-defect"
    )
    assert diagnostic["completion_marker_present"] is False
    assert diagnostic["last_event"] == "adapter-wait-ready:command_end:1"
    assert accepted["raw_harness_result"] == "pass"
    assert accepted["accepted_disposition"] == "accepted-clean-source-install-pass"
    assert accepted["completion_marker_present"] is True
    assert diagnostic["container_id"] != accepted["container_id"]
    assert all(attempt["installed_state_reused"] is False for attempt in evidence["attempts"])
    assert all(attempt["retained"] is True for attempt in evidence["attempts"])
    assert all(attempt["container_state"] == "exited" for attempt in evidence["attempts"])


def test_accepted_attempt_covers_every_debian_stage_and_runtime_boundary() -> None:
    evidence = _json(MANIFEST)
    attempt = evidence["attempts"][-1]
    accepted = evidence["accepted_attempt"]

    assert attempt["command_start_events"] == attempt["command_end_events"] == 52
    assert attempt["documented_commands_completed"] == 46
    assert attempt["documented_command_failures"] == 0
    assert attempt["documented_stage_counts"] == {
        "distro-prep": 4,
        "python": 13,
        "checkout": 9,
        "install": 8,
        "docs": 3,
        "start": 4,
        "verify": 5,
    }
    assert attempt["adapter_commands_completed"][-3:] == [
        "adapter-stop",
        "adapter-stop-probe",
        "adapter-complete",
    ]
    assert attempt["host_completion_guard_passed"] is True
    assert attempt["container_exit_code"] == 0
    assert attempt["oom_killed"] is False
    assert accepted["python_version"] == "3.14.6"
    assert accepted["editable_bpm_install"] == "0.9.1"
    assert accepted["alembic_upgrade_head"] == "pass"
    assert accepted["docs_validate_all_six_locales"] == "pass"
    assert accepted["docs_build_all_six_locales"] == "pass"
    assert accepted["docs_install_dev_all_six_locales"] == "pass"
    assert [probe["path"] for probe in accepted["probes"]] == [
        "/health",
        "/health/ready",
        "/profiles",
    ]
    assert all(probe["status"] == 200 for probe in accepted["probes"])
    assert accepted["runtime_shutdown"] == "pass"
    assert accepted["post_shutdown_health_probe"] == "connection-refused-as-required"
    assert accepted["completion_marker"] == "complete"


def test_cross_distribution_harness_guards_and_transcript_hashes_are_frozen() -> None:
    evidence = _json(MANIFEST)
    harness = _json(HARNESS)
    guards = evidence["inherited_harness_guards"]

    for attempt in evidence["attempts"]:
        assert len(attempt["transcript_sha256"]) >= 7
        assert all(
            re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in attempt["transcript_sha256"].values()
        )
    assert evidence["isolation"]["resource_flags"] == harness["execution"][
        "resource_flags"
    ]
    assert evidence["isolation"]["concurrency"] == 1
    assert evidence["isolation"]["published_ports"] == "none"
    assert evidence["isolation"]["host_bind_mounts"] == "none"
    assert evidence["isolation"]["docker_socket_mount"] == "none"
    assert evidence["isolation"]["privileged"] is False
    assert guards["fresh_container_per_attempt"] is True
    assert guards["parent_shell_exit_forbidden_in_adapters"] is True
    assert guards["runtime_exit_stops_readiness_wait"] is True
    assert guards["activated_environment_preserved_for_background_runtime"] is True
    assert guards["negative_stop_probe_required"] is True
    assert guards["completion_marker_required"] is True
    assert evidence["golden_image"]["initial_registry_pull_performed"] is True
    assert evidence["golden_image"]["accepted_attempt_local_exact_digest_reused"] is True
    assert evidence["golden_image"]["accepted_attempt_registry_pull_performed"] is False
    assert evidence["golden_image"]["retained"] is True


def test_inventory_retains_stopped_resources_within_the_current_storage_contract() -> None:
    inventory = _json(INVENTORY)
    retention = inventory["retention"]
    storage = inventory["storage"]

    assert inventory["status"] == "accepted"
    assert len(inventory["containers"]) == retention["container_count"] == 9
    assert len({container["id"] for container in inventory["containers"]}) == 9
    assert all(container["state"] == "exited" for container in inventory["containers"])
    assert len(inventory["images"]) == retention["image_count"] == 3
    assert retention["containers_removed"] == 0
    assert retention["images_removed"] == 0
    assert retention["networks_removed"] == 0
    assert retention["docker_engine_retained"] is True
    assert retention["golden_images_retained_for_reuse"] is True
    assert inventory["network"]["retained"] is True
    assert storage["maximum_task_owned_docker_bytes"] == 200_000_000_000
    assert storage["minimum_host_free_bytes"] == 20 * 1024**3
    assert storage["approximate_task_owned_docker_bytes"] < storage[
        "maximum_task_owned_docker_bytes"
    ]
    assert storage["host_free_bytes"] > storage["minimum_host_free_bytes"]
    assert storage["within_contract"] is True
