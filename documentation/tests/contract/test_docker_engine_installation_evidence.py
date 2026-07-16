from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_ROOT = (
    REPOSITORY_ROOT
    / "documentation/evidence/live-source-install/0.9.1/m11-02-docker-engine-20260714"
)
MANIFEST = EVIDENCE_ROOT / "run-manifest.json"
HOST_STATE = EVIDENCE_ROOT / "host-state.json"
CONTRACT = (
    REPOSITORY_ROOT
    / "documentation/config/live-source-install-privileged-validation-contract-0.9.1.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_installation_evidence_is_accepted_and_contract_backed() -> None:
    evidence = _json(MANIFEST)
    contract = _json(CONTRACT)

    assert evidence["schema_version"] == 1
    assert evidence["backlog_item"] == "BPM091-M11-02"
    assert evidence["target_bpm_version"] == "0.9.1"
    assert evidence["status"] == "accepted"
    assert evidence["contract"]["path"] == CONTRACT.relative_to(REPOSITORY_ROOT).as_posix()
    assert evidence["contract"]["contract_id"] == contract["contract_id"]
    assert evidence["contract"]["status"] == contract["status"] == "accepted"
    assert evidence["preflight"]["result"] == "pass"
    assert evidence["preflight"]["stop_condition_triggered"] is False


def test_only_the_five_approved_packages_were_installed() -> None:
    evidence = _json(MANIFEST)
    packages = evidence["packages"]
    contract_packages = _json(CONTRACT)["docker_installation"]["minimum_packages"]

    assert set(packages["candidate_and_installed_versions"]) == set(contract_packages)
    assert packages["new_package_count"] == 5
    assert packages["removed_packages"] == []
    assert packages["recommended_packages_installed"] == []
    assert packages["unrelated_packages_changed"] == []
    assert packages["install_flags"] == ["--no-install-recommends"]


def test_repository_key_and_privilege_transport_match_the_approved_boundary() -> None:
    evidence = _json(MANIFEST)
    repository = evidence["repository"]
    privilege = evidence["privilege"]

    assert repository["suite"] == "resolute"
    assert repository["architecture"] == "amd64"
    assert repository["component"] == "stable"
    assert repository["key_fingerprints"][0] == "9DC858229FC7DD38854AE2D88D81803C0EBFCD88"
    assert repository["convenience_script_used"] is False
    assert repository["docker_desktop_used"] is False
    assert "pkexec" in privilege["transport"]
    assert "graphical" in privilege["transport"]
    assert privilege["password_requested_or_recorded"] is False
    assert privilege["docker_group_membership_granted"] is False


def test_daemon_socket_group_and_versions_are_recorded_without_user_group_access() -> None:
    daemon = _json(MANIFEST)["daemon"]

    assert daemon["docker_client_version"] == daemon["docker_server_version"] == "29.6.1"
    assert daemon["docker_service"] == {
        "load": "loaded",
        "active": "active",
        "sub": "running",
        "enabled": True,
    }
    assert daemon["containerd_service"]["active"] == "active"
    assert daemon["containerd_service"]["enabled"] is True
    assert daemon["socket"] == {
        "path": "/run/docker.sock",
        "owner": "root",
        "group": "docker",
        "mode": "0660",
    }
    assert daemon["docker_group"]["members"] == []
    assert "docker" not in daemon["maintainer_groups"]
    assert daemon["unprivileged_docker_access"] == "denied"


def test_smoke_used_the_approved_limits_and_isolation() -> None:
    evidence = _json(MANIFEST)
    smoke = evidence["smoke"]

    assert smoke["result"] == "pass"
    assert smoke["platform"] == "linux/amd64"
    assert smoke["exit_code"] == 0
    assert smoke["expected_output_observed"] == "Hello from Docker!"
    assert smoke["limits"] == {
        "nano_cpus": 2_000_000_000,
        "memory_bytes": 1536 * 1024**2,
        "memory_swap_bytes": 2560 * 1024**2,
        "pids_limit": 512,
        "nofile": "4096:4096",
        "security_options": ["no-new-privileges"],
    }
    assert smoke["isolation"] == {
        "privileged": False,
        "cap_add": None,
        "binds": None,
        "published_ports": {},
        "host_network": False,
        "restart_policy": "no",
    }
    assert smoke["required_labels"]["com.browser-policy-manager.validation"] == "BPM091-M11"


def test_smoke_resources_were_removed_while_docker_was_retained() -> None:
    evidence = _json(MANIFEST)
    cleanup = evidence["smoke_cleanup"]
    retention = evidence["retention"]
    host = _json(HOST_STATE)

    assert cleanup["container_removed"] is True
    assert cleanup["image_removed"] is True
    assert cleanup["network_removed"] is True
    assert cleanup["remaining_m11_containers"] == 0
    assert cleanup["remaining_m11_networks"] == 0
    assert cleanup["remaining_m11_volumes"] == 0
    assert cleanup["daemon_container_count"] == 0
    assert cleanup["daemon_image_count"] == 0
    assert all(retention[key] is True for key in retention if key != "reason")
    assert host["after"]["m11_labeled_resources"] == 0
    assert host["after"]["maintainer_in_docker_group"] is False
    assert host["unexpected_persistent_differences"] == []
    assert host["result"] == "pass"


def test_unrelated_persistent_host_and_firewall_settings_did_not_change() -> None:
    evidence = _json(MANIFEST)
    review = evidence["host_change_review"]

    assert review["firewall_configuration_hashes_unchanged"] is True
    assert review["manual_firewall_or_network_configuration_changes"] is False
    assert review["new_running_services"] == ["docker.service", "containerd.service"]
    assert review["unrelated_persistent_service_changes"] == []
    assert review["unrelated_host_settings_changed"] == []
    transient = review["transient_observation"]
    assert transient["service"] == "packagekit.service"
    assert transient["unit_file_state"] == "static"
    assert transient["final_active_state"] == "inactive"
    assert transient["final_sub_state"] == "dead"
    assert transient["dpkg_verify_findings"] == []
    assert "no stop/start/configuration command" in transient["disposition"]
    assert evidence["capacity_after"]["storage_floor_pass"] is True
    assert evidence["capacity_after"]["root_available_bytes"] > 200 * 1024**3
