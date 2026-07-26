from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/m11-06-fedora-source-install-20260714"
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


def test_fedora_live_install_is_accepted_against_an_immutable_091_ref() -> None:
    evidence = _json(MANIFEST)
    source = REPOSITORY_ROOT / evidence["target"]["source_topic"]
    reconciled = next(
        target
        for target in _json(RECONCILIATION)["targets"]
        if target["target_id"] == evidence["target"]["id"]
    )

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-06"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == "accepted"
    assert evidence["result"] == "pass"
    assert evidence["target"]["identity"] == {"ID": "fedora", "VERSION_ID": "44"}
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
    attempt = evidence["attempts"][0]
    assert snapshot["validation_branch"] == "validation/bpm-0.9.1-m11"
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["accepted_ref"])
    assert attempt["bpm_ref"] == snapshot["accepted_ref"]
    assert snapshot["accepted_ref_version"] == "0.9.1"
    assert snapshot["remote_ref_fetched_and_verified"] is True
    assert snapshot["normal_development_branch_changed"] is False


def test_first_clean_fedora_attempt_covers_every_stage_and_runtime_boundary() -> None:
    evidence = _json(MANIFEST)
    attempt = evidence["attempts"][0]
    accepted = evidence["accepted_attempt"]

    assert attempt["attempt"] == 1
    assert attempt["raw_harness_result"] == "pass"
    assert attempt["accepted_disposition"] == "accepted-clean-source-install-pass"
    assert attempt["command_start_events"] == attempt["command_end_events"] == 40
    assert attempt["documented_commands_completed"] == 34
    assert attempt["documented_command_failures"] == 0
    assert attempt["documented_stage_counts"] == {
        "distro-prep": 5,
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
    assert attempt["completion_marker_present"] is True
    assert attempt["host_completion_guard_passed"] is True
    assert attempt["installed_state_reused"] is False
    assert attempt["container_state"] == "exited"
    assert attempt["container_exit_code"] == 0
    assert attempt["oom_killed"] is False
    assert attempt["retained"] is True
    assert accepted["python_version"] == "3.14.6"
    assert accepted["python_source"] == "fedora-44-updates-repository"
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


def test_ubuntu_and_debian_harness_guards_protect_fedora() -> None:
    evidence = _json(MANIFEST)
    harness = _json(HARNESS)
    guards = evidence["inherited_harness_guards"]
    attempt = evidence["attempts"][0]

    assert len(attempt["transcript_sha256"]) == 8
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
    assert guards["second_terminal_working_directory_restored"] is True
    assert guards["negative_stop_probe_required"] is True
    assert guards["completion_marker_required"] is True
    assert guards["host_completion_guard_required"] is True
    assert evidence["retry"]["required"] is False
    assert evidence["retry"]["inherited_ubuntu_and_debian_guards_effective"] is True


def test_fedora_golden_image_and_all_resources_remain_retained() -> None:
    evidence = _json(MANIFEST)
    inventory = _json(INVENTORY)
    retention = inventory["retention"]
    storage = inventory["storage"]

    assert evidence["golden_image"]["initial_registry_pull_performed"] is True
    assert evidence["golden_image"]["retained"] is True
    assert inventory["status"] == "accepted"
    assert len(inventory["containers"]) == retention["container_count"] == 10
    assert len({container["id"] for container in inventory["containers"]}) == 10
    assert all(container["state"] == "exited" for container in inventory["containers"])
    assert len(inventory["images"]) == retention["image_count"] == 4
    assert {image["target"] for image in inventory["images"]} == {
        "ubuntu-26-04",
        "debian-13-5",
        "fedora-44",
        "linux-mint-22-3",
    }
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
