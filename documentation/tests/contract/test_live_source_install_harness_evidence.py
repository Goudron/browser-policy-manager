from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT / "documentation/evidence/live-source-install/0.9.1/m11-03-harness-20260714"
)
MANIFEST = EVIDENCE_ROOT / "run-manifest.json"
INVENTORY = EVIDENCE_ROOT / "retained-inventory.json"
HARNESS_CONFIG = REPOSITORY_ROOT / "documentation/config/live-source-install-harness-0.9.1.json"
MANJARO_LIVE_MANIFEST = (
    REPOSITORY_ROOT / "documentation/evidence/live-source-install/0.9.1/"
    "m11-08-manjaro-source-install-20260715/run-manifest.json"
)
RECONCILIATION = REPOSITORY_ROOT / "docs/architecture/linux-source-install-validation-0.9.1.json"
EDITORIAL_RECONCILIATION = (
    REPOSITORY_ROOT / "documentation/config/linux-source-install-editorial-reconciliation-0.9.2.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_harness_evidence_is_accepted_and_contract_backed() -> None:
    evidence = _json(MANIFEST)
    config = _json(HARNESS_CONFIG)

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-03"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == config["status"] == "accepted"
    assert (
        evidence["contracts"]["harness"] == HARNESS_CONFIG.relative_to(REPOSITORY_ROOT).as_posix()
    )
    assert evidence["implementation"]["deletion_commands_exposed"] is False
    assert evidence["implementation"]["password_requested_or_recorded"] is False


def test_plan_coverage_matches_all_five_dita_sources() -> None:
    evidence = _json(MANIFEST)
    config = _json(HARNESS_CONFIG)
    manjaro_live = _json(MANJARO_LIVE_MANIFEST)
    reconciled = {
        target["target_id"]: target for target in _json(RECONCILIATION)["targets"]
    }
    current_targets = {
        target["id"]: target
        for target in _json(EDITORIAL_RECONCILIATION)["current_source_contract"]["targets"]
    }
    removed_commands = _json(EDITORIAL_RECONCILIATION)["current_source_contract"][
        "removed_maintainer_commands"
    ]
    profiles = {profile["id"]: profile for profile in config["targets"]}

    assert [item["target_id"] for item in evidence["plan_coverage"]] == list(profiles)
    for item in evidence["plan_coverage"]:
        source = REPOSITORY_ROOT / profiles[item["target_id"]]["source_topic"]
        current_digest = hashlib.sha256(source.read_bytes()).hexdigest()
        target = reconciled[item["target_id"]]
        if item["target_id"] == "manjaro-stable-2026-06-26":
            diagnostic, accepted = manjaro_live["attempts"]
            assert item["source_sha256"] == diagnostic["source_sha256"]
            assert accepted["source_sha256"] == target["validated_source_sha256"]
        else:
            assert item["source_sha256"] == target["validated_source_sha256"]
        assert current_digest != target["reconciled_source_sha256"]
        assert current_targets[item["target_id"]]["topic_id"] in source.name
        assert all(command not in source.read_text(encoding="utf-8") for command in removed_commands)
        assert item["documented_command_count"] > 0


def test_retry_retains_the_failed_attempt_without_reusing_its_state() -> None:
    evidence = _json(MANIFEST)
    attempts = evidence["ubuntu_self_test"]["attempts"]

    assert [attempt["attempt"] for attempt in attempts] == [1, 2]
    assert [attempt["container_id"] for attempt in attempts] == [
        "199a2081f6a90e7cf6f118a05d83a9e9590f766b689d5ff3ccf07dd1eb45fbcf",
        "d4385396d9ef6c0f4fe10a3d1b9d3863599fb7777e5c72bfc2f0b821162bcccc",
    ]
    assert attempts[0]["exit_code"] == 137
    assert attempts[0]["result"] == "retained-harness-lifecycle-defect"
    assert attempts[1]["exit_code"] == 0
    assert attempts[1]["result"] == "pass"
    assert evidence["ubuntu_self_test"]["retry_reused_installed_state"] is False


def test_mint_image_is_signed_iso_derived_and_identity_verified() -> None:
    evidence = _json(MANIFEST)
    mint = evidence["mint_image_construction"]
    self_test = evidence["mint_identity_self_test"]

    assert mint["result"] == self_test["result"] == "pass"
    assert mint["signed_checksum_result"] == "good-signature-and-pinned-checksum-match"
    assert mint["signing_key_fingerprint"] == "27DEB15644C6B3CF3BD7D291300F846BA25BAE09"
    assert mint["iso_sha256"] == "a081ab202cfda17f6924128dbd2de8b63518ac0531bcfe3f1a1b88097c459bd4"
    assert (
        mint["rootfs_identity"]
        == self_test["identity"]
        == {
            "ID": "linuxmint",
            "VERSION_ID": "22.3",
            "VERSION_CODENAME": "zena",
        }
    )
    assert mint["numeric_owner_tar_sha256"] == mint["image_layer_digest"].removeprefix("sha256:")
    assert mint["image_id"] == self_test["image_id"]
    assert mint["helper_exit_code"] == self_test["container_exit_code"] == 0
    assert mint["helper_retained"] is True


def test_inventory_retains_every_resource_stopped_and_within_storage_limits() -> None:
    inventory = _json(INVENTORY)
    retention = inventory["retention"]
    storage = inventory["storage"]

    assert inventory["status"] == "accepted"
    assert len({container["id"] for container in inventory["containers"]}) == 4
    assert all(container["state"] == "exited" for container in inventory["containers"])
    assert retention == {
        "all_containers_stopped": True,
        "container_count": 4,
        "image_count": 2,
        "network_count": 1,
        "containers_removed": 0,
        "images_removed": 0,
        "networks_removed": 0,
        "docker_engine_retained": True,
    }
    assert storage["within_contract"] is True
    assert (
        storage["approximate_task_owned_docker_bytes"] < storage["maximum_task_owned_docker_bytes"]
    )
    assert storage["host_free_bytes"] > storage["minimum_host_free_bytes"]
    assert inventory["network"]["retained"] is True
