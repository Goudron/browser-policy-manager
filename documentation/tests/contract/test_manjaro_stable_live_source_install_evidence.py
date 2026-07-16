from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT / "documentation/evidence/live-source-install/0.9.1/"
    "m11-08-manjaro-source-install-20260715"
)
MANIFEST = EVIDENCE_ROOT / "run-manifest.json"
INVENTORY = EVIDENCE_ROOT / "retained-inventory.json"
HARNESS = REPOSITORY_ROOT / "documentation/config/live-source-install-harness-0.9.1.json"
RECONCILIATION = REPOSITORY_ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
PRIVILEGED_CONTRACT = (
    REPOSITORY_ROOT
    / "documentation/config/live-source-install-privileged-validation-contract-0.9.1.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manjaro_live_install_is_accepted_against_an_immutable_091_ref() -> None:
    evidence = _json(MANIFEST)
    source = REPOSITORY_ROOT / evidence["target"]["source_topic"]
    reconciled = next(
        target
        for target in _json(RECONCILIATION)["targets"]
        if target["target_id"] == evidence["target"]["id"]
    )

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-08"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == "accepted"
    assert evidence["result"] == "pass"
    assert evidence["target"]["identity"] == {
        "ID": "manjaro",
        "branch": "stable",
    }
    assert evidence["target"]["source_sha256"] == reconciled["validated_source_sha256"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == reconciled["reconciled_source_sha256"]
    snapshot = evidence["source_snapshot"]
    assert snapshot["validation_branch"] == "validation/bpm-0.9.1-m11"
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["accepted_ref"])
    assert all(attempt["bpm_ref"] == snapshot["accepted_ref"] for attempt in evidence["attempts"])
    assert snapshot["accepted_ref_version"] == "0.9.1"
    assert snapshot["remote_ref_fetched_and_verified"] is True
    assert snapshot["normal_development_branch_changed"] is False


def test_interactive_pacman_diagnostic_cannot_be_accepted_or_reused() -> None:
    evidence = _json(MANIFEST)
    diagnostic, accepted = evidence["attempts"]
    english = (
        REPOSITORY_ROOT
        / "documentation/src/dita/en/admin/admin-task-install-manjaro-stable-source.dita"
    ).read_text(encoding="utf-8")
    russian = (
        REPOSITORY_ROOT
        / "documentation/src/dita/ru/admin/admin-task-install-manjaro-stable-source.dita"
    ).read_text(encoding="utf-8")
    corrected_command = (
        "sudo pacman -Syu --needed --noconfirm base-devel ca-certificates curl git "
        "python python-pip"
    )

    assert diagnostic["raw_harness_result"] == "blocked"
    assert diagnostic["accepted_disposition"] == (
        "retained-diagnostic-interactive-pacman-confirmation-defect"
    )
    assert diagnostic["last_event"] == "distro-prep-04:command_end:1"
    assert diagnostic["documented_command_failures"] == 1
    assert diagnostic["completion_marker_present"] is False
    assert diagnostic["source_sha256"] != evidence["target"]["source_sha256"]
    assert corrected_command in english
    assert corrected_command in russian
    assert accepted["raw_harness_result"] == "pass"
    assert accepted["accepted_disposition"] == "accepted-clean-source-install-pass"
    assert accepted["source_sha256"] == evidence["target"]["source_sha256"]
    assert accepted["completion_marker_present"] is True
    assert diagnostic["container_id"] != accepted["container_id"]
    assert all(attempt["installed_state_reused"] is False for attempt in evidence["attempts"])
    assert all(attempt["retained"] is True for attempt in evidence["attempts"])
    assert all(attempt["container_state"] == "exited" for attempt in evidence["attempts"])


def test_stable_snapshot_and_package_state_are_newer_than_the_required_boundary() -> None:
    evidence = _json(MANIFEST)
    rolling = evidence["rolling_snapshot"]
    boundary = evidence["container_fidelity_boundary"]

    assert rolling["branch_before_update"] == "stable"
    assert rolling["branch_after_update"] == "stable"
    assert "-Syu" in rolling["full_system_update_command"]
    assert "--noconfirm" in rolling["full_system_update_command"]
    assert rolling["full_system_update_result"] == "pass"
    assert rolling["resolved_package_count"] == 160
    assert rolling["post_update_markers"] == {
        "manjaro-release": "26.1.0-1",
        "archlinux-keyring": "20260707.1-1",
        "python": "3.14.6-1",
        "python-pip": "26.1.2-1",
        "pacman": "7.1.0.r9.g54d9411-2",
        "tzdata": "2026b-1",
    }
    assert rolling["later_than_required_2026_06_26_snapshot"] is True
    assert re.fullmatch(r"[0-9a-f]{64}", rolling["complete_update_transaction_sha256"])
    assert rolling["mirror_timeout_disposition"] == (
        "one-download-timeout-recovered-by-pacman-mirror-fallback"
    )
    assert boundary["userspace_identity_and_package_state"] == "validated"
    assert boundary["kernel"] == "shared-host-kernel-not-native-manjaro-kernel"
    assert boundary["native_desktop_or_boot_validation_claimed"] is False


def test_accepted_attempt_covers_every_manjaro_stage_and_runtime_boundary() -> None:
    evidence = _json(MANIFEST)
    attempt = evidence["attempts"][-1]
    accepted = evidence["accepted_attempt"]

    assert attempt["command_start_events"] == attempt["command_end_events"] == 43
    assert attempt["documented_commands_completed"] == 37
    assert attempt["documented_command_failures"] == 0
    assert attempt["documented_stage_counts"] == {
        "distro-prep": 8,
        "checkout": 9,
        "install": 8,
        "docs": 3,
        "start": 4,
        "verify": 5,
    }
    assert attempt["adapter_commands_completed"] == [
        "adapter-setup",
        "adapter-wait-ready",
        "adapter-second-terminal",
        "adapter-stop",
        "adapter-stop-probe",
        "adapter-complete",
    ]
    assert attempt["host_completion_guard_passed"] is True
    assert attempt["container_exit_code"] == 0
    assert attempt["oom_killed"] is False
    assert accepted["python_version"] == "3.14.6"
    assert accepted["python_source"] == ("manjaro-stable-repositories-after-full-system-update")
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


def test_pinned_image_and_cross_distribution_harness_guards_are_frozen() -> None:
    evidence = _json(MANIFEST)
    harness = _json(HARNESS)
    privileged_contract = _json(PRIVILEGED_CONTRACT)
    target_image = next(
        image
        for image in privileged_contract["target_images"]
        if image["target_id"] == "manjaro-stable-2026-06-26"
    )
    golden = evidence["golden_image"]
    guards = evidence["inherited_harness_guards"]

    assert golden["ref"] == target_image["pull_ref"]
    assert golden["index_digest"] == target_image["index_digest"]
    assert golden["amd64_manifest_digest"] == target_image["linux_amd64_manifest_digest"]
    assert golden["initial_registry_pull_performed"] is True
    assert golden["accepted_attempt_local_exact_digest_reused"] is True
    assert golden["accepted_attempt_registry_pull_performed"] is False
    assert golden["retained"] is True
    for attempt in evidence["attempts"]:
        assert len(attempt["transcript_sha256"]) >= 6
        assert all(
            re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in attempt["transcript_sha256"].values()
        )
    assert evidence["isolation"]["resource_flags"] == harness["execution"]["resource_flags"]
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


def test_inventory_retains_all_stopped_resources_within_the_storage_contract() -> None:
    inventory = _json(INVENTORY)
    retention = inventory["retention"]
    storage = inventory["storage"]

    assert inventory["status"] == "accepted"
    assert len(inventory["containers"]) == retention["container_count"] == 13
    assert len({container["id"] for container in inventory["containers"]}) == 13
    assert all(container["state"] == "exited" for container in inventory["containers"])
    manjaro_attempts = [
        container
        for container in inventory["containers"]
        if container["owner_task"] == "BPM091-M11-08"
    ]
    assert [container["attempt"] for container in manjaro_attempts] == [1, 2]
    assert manjaro_attempts[-1]["disposition"] == "accepted-clean-source-install-pass"
    assert len(inventory["images"]) == retention["image_count"] == 5
    assert {image["target"] for image in inventory["images"]} == {
        "ubuntu-26-04",
        "debian-13-5",
        "fedora-44",
        "linux-mint-22-3",
        "manjaro-stable-2026-06-26",
    }
    assert retention["containers_removed"] == 0
    assert retention["images_removed"] == 0
    assert retention["networks_removed"] == 0
    assert retention["docker_engine_retained"] is True
    assert retention["golden_images_retained_for_reuse"] is True
    assert inventory["network"]["retained"] is True
    assert storage["maximum_task_owned_docker_bytes"] == 200_000_000_000
    assert storage["minimum_host_free_bytes"] == 20 * 1024**3
    assert (
        storage["approximate_task_owned_docker_bytes"] < storage["maximum_task_owned_docker_bytes"]
    )
    assert storage["host_free_bytes"] > storage["minimum_host_free_bytes"]
    assert storage["within_contract"] is True
