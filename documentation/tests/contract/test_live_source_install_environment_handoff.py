from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/"
    "m11-13-validation-environment-handoff-20260715"
)
MANIFEST = EVIDENCE_ROOT / "run-manifest.json"
INVENTORY = EVIDENCE_ROOT / "retained-inventory.json"
PREVIOUS_INVENTORY = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/"
    "m11-08-manjaro-source-install-20260715/retained-inventory.json"
)
INSTALL_EVIDENCE = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/"
    "m11-02-docker-engine-20260714/run-manifest.json"
)
CONTRACT = (
    REPOSITORY_ROOT
    / "documentation/config/live-source-install-privileged-validation-contract-0.9.1.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_m11_environment_handoff_is_accepted_without_cleanup_deletion() -> None:
    manifest = _json(MANIFEST)
    inventory = _json(INVENTORY)

    assert manifest["schema_version"] == inventory["schema_version"] == 1
    assert manifest["backlog_item"] == inventory["backlog_item"] == "BPM091-M11-13"
    assert manifest["target_bpm_version"] == inventory["target_bpm_version"] == "0.9.1"
    assert manifest["status"] == inventory["status"] == "accepted"
    assert manifest["result"] == "pass"
    assert manifest["retained_inventory"] == INVENTORY.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    assert manifest["retention_decision"]["deletion_performed"] is False
    assert inventory["handoff"]["deletion_performed"] is False
    assert inventory["handoff"]["result"] == "complete"


def test_all_thirteen_containers_are_stopped_identified_and_retained() -> None:
    inventory = _json(INVENTORY)
    previous = _json(PREVIOUS_INVENTORY)
    containers = inventory["containers"]

    assert len(containers) == inventory["retention"]["container_count"] == 13
    assert {container["id"] for container in containers} == {
        container["id"] for container in previous["containers"]
    }
    assert len({container["id"] for container in containers}) == 13
    assert len({container["name"] for container in containers}) == 13
    assert all(container["state"] == "exited" for container in containers)
    assert all(container["retention_decision"] == "retain" for container in containers)
    for container in containers:
        assert container["owner_task"].startswith("BPM091-M11-")
        assert container["target"]
        assert container["attempt"] >= 1
        assert container["disposition"]
        assert (REPOSITORY_ROOT / container["evidence"]).is_file()
    assert inventory["retention"]["all_containers_stopped"] is True
    assert inventory["retention"]["containers_removed"] == 0


def test_five_golden_images_and_dedicated_network_are_unchanged() -> None:
    inventory = _json(INVENTORY)
    previous = _json(PREVIOUS_INVENTORY)
    images = inventory["images"]
    network = inventory["network"]

    assert len(images) == inventory["retention"]["image_count"] == 5
    assert {image["id"] for image in images} == {
        image["id"] for image in previous["images"]
    }
    assert {image["target"] for image in images} == {
        "ubuntu-26-04",
        "debian-13-5",
        "fedora-44",
        "linux-mint-22-3",
        "manjaro-stable-2026-06-26",
    }
    assert all(image["role"] == "clean-golden-image" for image in images)
    assert all(image["disposition"] == "retained-for-reuse" for image in images)
    assert all((REPOSITORY_ROOT / image["evidence"]).is_file() for image in images)
    assert network["id"] == previous["network"]["id"]
    assert network["name"] == "bpm091-m11-net"
    assert network["attached_containers"] == 0
    assert network["retained"] is True
    assert inventory["retention"]["images_removed"] == 0
    assert inventory["retention"]["networks_removed"] == 0


def test_docker_tooling_repository_key_services_socket_and_group_are_retained() -> None:
    inventory = _json(INVENTORY)
    installation = _json(INSTALL_EVIDENCE)
    tooling = inventory["host_tooling"]

    assert tooling["packages"] == installation["packages"][
        "candidate_and_installed_versions"
    ]
    assert tooling["repository"]["path"] == installation["repository"]["source_path"]
    assert tooling["repository"]["sha256"] == installation["repository"]["source_sha256"]
    assert tooling["repository"]["unchanged_from_m11_02"] is True
    assert tooling["key"]["path"] == installation["repository"]["key_path"]
    assert tooling["key"]["sha256"] == installation["repository"]["key_sha256"]
    assert tooling["key"]["unchanged_from_m11_02"] is True
    assert tooling["docker_server_version"] == installation["daemon"][
        "docker_server_version"
    ]
    assert tooling["services"] == {
        "docker.service": "active/enabled",
        "containerd.service": "active/enabled",
        "drop_in_overrides": [],
    }
    assert tooling["socket"] == "root:docker 0660"
    assert tooling["docker_group_members"] == []
    assert tooling["maintainer_in_docker_group"] is False
    assert tooling["daemon_json_present"] is False
    assert tooling["retained"] is tooling["healthy"] is True


def test_storage_volumes_and_cache_stay_within_the_approved_boundary() -> None:
    inventory = _json(INVENTORY)
    boundary = _json(CONTRACT)["storage_boundary"]
    storage = inventory["storage"]
    retention = inventory["retention"]

    assert storage["inspect_image_bytes"] == sum(
        image["inspect_size_bytes"] for image in inventory["images"]
    )
    assert storage["container_writable_bytes"] == sum(
        container["size_rw_bytes"] for container in inventory["containers"]
    )
    assert storage["identity_accounting_bytes"] == (
        storage["inspect_image_bytes"] + storage["container_writable_bytes"]
    )
    assert storage["maximum_task_owned_docker_bytes"] == boundary[
        "maximum_task_owned_docker_bytes"
    ]
    assert storage["minimum_host_free_bytes"] == boundary["minimum_host_free_bytes"]
    assert storage["physical_docker_and_containerd_root_bytes"] < storage[
        "maximum_task_owned_docker_bytes"
    ]
    assert storage["host_free_bytes"] > storage["minimum_host_free_bytes"]
    assert storage["within_contract"] is True
    assert retention["volume_count"] == retention["volumes_removed"] == 0
    assert retention["build_cache_bytes"] == 0


def test_firewall_membership_and_unrelated_host_state_match_the_baseline() -> None:
    integrity = _json(INVENTORY)["host_integrity"]

    assert integrity["maintainer_groups_match_m11_01"] is True
    assert integrity["firewall_configuration_hashes_match_m11_02"] is True
    assert integrity["firewall_hashes"] == {
        "/etc/nftables.conf": (
            "60dac93ffe0ea440fc4a8941a080b6fb8d2c8655d47baf856e97182a0d1ca29a"
        ),
        "/etc/default/ufw": (
            "07db07bb07e5ac1388707b7c59dabfbce8ad06d5001236248fbf3f93b79c2ed7"
        ),
        "/etc/ufw/user.rules": (
            "320f53e1ee90a7fd92f17b67f50b06b51cb20998cd52f01dbcb52e24160618bf"
        ),
        "/etc/ufw/user6.rules": (
            "f6696cd7741aada36ab2055dd1a9d098e23e0290ca3a67dafbbad2920e5fdf60"
        ),
        "/etc/sysctl.conf": "absent",
    }
    assert integrity["unrelated_persistent_changes"] == []
    assert integrity["result"] == "pass"


def test_handoff_used_only_read_only_inventory_and_preserved_raw_hashes() -> None:
    manifest = _json(MANIFEST)
    capture = manifest["capture"]

    assert capture["mode"] == "read-only"
    assert capture["privileged_read_only_attempts"] == 3
    assert capture["successful_privileged_read_only_attempts"] == 2
    assert capture["failed_formatting_attempts"] == 1
    assert capture["raw_transcripts_committed"] is False
    assert re.fullmatch(r"[0-9a-f]{64}", capture["local_transcript_sha256"])
    assert re.fullmatch(r"[0-9a-f]{64}", capture["local_firewall_hash_record_sha256"])
    assert set(manifest["mutations"].values()) == {0}
    assert manifest["observations"]["container_stop_required"] is False
    assert manifest["handoff"]["next_backlog_item"] == "BPM091-M11-14"


def test_final_cleanup_contract_points_to_the_accepted_handoff() -> None:
    manifest = _json(MANIFEST)
    cleanup = _json(CONTRACT)["final_cleanup"]

    assert cleanup["owner_task"] == "BPM091-M11-13"
    assert cleanup["status"] == "accepted"
    assert cleanup["completion_evidence"] == MANIFEST.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    assert cleanup["retained_inventory"] == INVENTORY.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    assert cleanup["retained_host_tooling"]["decision"] == (
        "retain-after-successful-installation"
    )
    assert manifest["verification"] == {
        "focused_contract": "pass-15",
        "full_documentation_contract": "pass-733-with-4-deselected",
        "docs_snapshot": "pass",
        "docs_validate": "pass-six-locales",
        "docs_install_dev": "pass",
        "dev_server_started": False,
    }
