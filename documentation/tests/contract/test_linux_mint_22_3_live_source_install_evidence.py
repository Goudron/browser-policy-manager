from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT / "documentation/evidence/live-source-install/0.9.1/"
    "m11-07-mint-source-install-20260715"
)
MANIFEST = EVIDENCE_ROOT / "run-manifest.json"
INVENTORY = EVIDENCE_ROOT / "retained-inventory.json"
HARNESS = REPOSITORY_ROOT / "documentation/config/live-source-install-harness-0.9.1.json"
RECONCILIATION = REPOSITORY_ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
EDITORIAL_RECONCILIATION = (
    REPOSITORY_ROOT / "documentation/config/linux-source-install-editorial-reconciliation-0.9.2.json"
)
HARNESS_EVIDENCE = (
    REPOSITORY_ROOT / "documentation/evidence/live-source-install/0.9.1/"
    "m11-03-harness-20260714/run-manifest.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_mint_live_install_is_accepted_against_an_immutable_091_ref() -> None:
    evidence = _json(MANIFEST)
    source = REPOSITORY_ROOT / evidence["target"]["source_topic"]
    reconciled = next(
        target
        for target in _json(RECONCILIATION)["targets"]
        if target["target_id"] == evidence["target"]["id"]
    )

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-07"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == "accepted"
    assert evidence["result"] == "pass"
    assert evidence["target"]["identity"] == {
        "ID": "linuxmint",
        "VERSION_ID": "22.3",
        "VERSION_CODENAME": "zena",
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
    attempt = evidence["attempts"][0]
    assert snapshot["validation_branch"] == "validation/bpm-0.9.1-m11"
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["accepted_ref"])
    assert attempt["bpm_ref"] == snapshot["accepted_ref"]
    assert snapshot["accepted_ref_version"] == "0.9.1"
    assert snapshot["remote_ref_fetched_and_verified"] is True
    assert snapshot["normal_development_branch_changed"] is False


def test_mint_image_provenance_and_repository_activity_are_not_ubuntu_substitution() -> None:
    evidence = _json(MANIFEST)
    harness_evidence = _json(HARNESS_EVIDENCE)
    golden = evidence["golden_image"]
    construction = harness_evidence["mint_image_construction"]
    repositories = evidence["distribution_repository_observation"]

    assert golden["construction"] == "signed-official-iso-derived-rootfs"
    assert golden["id"] == construction["image_id"]
    assert golden["official_iso"] == construction["official_iso"]
    assert golden["iso_sha256"] == construction["iso_sha256"]
    assert golden["signing_key_fingerprint"] == construction["signing_key_fingerprint"]
    assert golden["numeric_owner_tar_sha256"] == construction["numeric_owner_tar_sha256"]
    assert golden["image_layer_digest"] == construction["image_layer_digest"]
    assert golden["initial_registry_pull_performed"] is False
    assert golden["reused_local_clean_image"] is True
    assert golden["retained"] is True
    assert repositories["mint_repository"] == "http://packages.linuxmint.com"
    assert repositories["mint_suite"] == "zena"
    assert repositories["mint_release_and_signature_index_fetched"] is True
    assert repositories["ubuntu_base_repositories"] == [
        "noble",
        "noble-updates",
        "noble-security",
        "noble-backports",
    ]
    assert repositories["silent_ubuntu_substitution"] is False


def test_first_clean_mint_attempt_covers_every_stage_and_runtime_boundary() -> None:
    evidence = _json(MANIFEST)
    attempt = evidence["attempts"][0]
    accepted = evidence["accepted_attempt"]

    assert attempt["attempt"] == 1
    assert attempt["raw_harness_result"] == "pass"
    assert attempt["accepted_disposition"] == "accepted-clean-source-install-pass"
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
    assert attempt["adapter_commands_completed"] == [
        "adapter-setup",
        "adapter-wait-ready",
        "adapter-second-terminal",
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
    assert accepted["python_source"] == "checksum-verified-upstream-source-archive"
    assert accepted["python_source_sha256"] == (
        "143b1dddefaec3bd2e21e3b839b34a2b7fb9842272883c576420d605e9f30c63"
    )
    assert accepted["optional_python_module_disposition"] == (
        "reviewed-non-blocking-after-complete-bpm-workflow-pass"
    )
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


def test_inherited_harness_guards_and_resource_limits_protect_mint() -> None:
    evidence = _json(MANIFEST)
    harness = _json(HARNESS)
    guards = evidence["inherited_harness_guards"]
    attempt = evidence["attempts"][0]

    assert len(attempt["transcript_sha256"]) == 8
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", digest) for digest in attempt["transcript_sha256"].values()
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
    assert evidence["retry"]["required"] is False
    assert evidence["retry"]["inherited_ubuntu_and_debian_guards_effective"] is True


def test_mint_golden_image_and_all_resources_remain_retained() -> None:
    inventory = _json(INVENTORY)
    retention = inventory["retention"]
    storage = inventory["storage"]

    assert inventory["status"] == "accepted"
    assert len(inventory["containers"]) == retention["container_count"] == 11
    assert len({container["id"] for container in inventory["containers"]}) == 11
    assert all(container["state"] == "exited" for container in inventory["containers"])
    mint_attempt = next(
        container
        for container in inventory["containers"]
        if container["owner_task"] == "BPM091-M11-07"
    )
    assert mint_attempt["exit_code"] == 0
    assert mint_attempt["disposition"] == "accepted-clean-source-install-pass"
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
    assert (
        storage["approximate_task_owned_docker_bytes"] < storage["maximum_task_owned_docker_bytes"]
    )
    assert storage["host_free_bytes"] > storage["minimum_host_free_bytes"]
    assert storage["within_contract"] is True
