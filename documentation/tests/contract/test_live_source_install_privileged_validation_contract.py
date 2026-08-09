from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "documentation/config/live-source-install-privileged-validation-contract-0.9.1.json"
)
M6_CONTRACT_PATH = (
    REPOSITORY_ROOT / "documentation/config/linux-source-install-command-contract-0.9.1.json"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_contract_records_maintainer_approval_of_the_exact_boundary() -> None:
    contract = _json(CONTRACT_PATH)

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-0.9.1-live-source-install-privileged-validation"
    assert contract["backlog_item"] == "BPM091-M11-01"
    assert contract["target_bpm_version"] == "0.9.1"
    assert contract["status"] == "accepted"

    approval = contract["approval"]
    assert approval["required_before"] == "BPM091-M11-02"
    assert approval["status"] == contract["status"]
    assert approval["approved_by"] == "project maintainer"
    assert approval["approved_at"] == "2026-07-14T01:00:29+03:00"
    assert "retained" in approval["approved_scope_note"]
    assert "invalidates approval" in approval["scope_change_rule"]


def _preflight_baseline_errors(contract: dict[str, object]) -> list[str]:
    baseline = contract["host_baseline"]
    errors: list[str] = []

    if baseline["capture_mode"] != "read-only commands without sudo":
        errors.append("baseline capture must remain read-only")
    if not {"pretty_name", "id", "version_id", "architecture"} <= set(baseline["host"]):
        errors.append("baseline must identify the observed host")
    if not baseline["docker_state"]:
        errors.append("baseline must distinguish Docker state before task ownership")
    if baseline["capacity"]["root_available_bytes"] <= 0:
        errors.append("baseline capacity must be a positive observation")
    if not contract["mandatory_preflight_recheck"]["stop_conditions"]:
        errors.append("preflight must name stop conditions")
    return errors


def test_read_only_baseline_distinguishes_preexisting_and_task_owned_docker_state() -> None:
    contract = _json(CONTRACT_PATH)
    baseline = contract["host_baseline"]

    assert _preflight_baseline_errors(contract) == []
    assert "maintainer-approved retained project tooling" in baseline["ownership_conclusion"]

    preflight = contract["mandatory_preflight_recheck"]
    assert preflight["timing"].startswith("Immediately before")
    assert any("Docker" in condition for condition in preflight["stop_conditions"])
    assert "never silently" in preflight["decision_rule"]

    stale_contract = copy.deepcopy(contract)
    stale_contract["mandatory_preflight_recheck"]["stop_conditions"] = []
    assert _preflight_baseline_errors(stale_contract) == ["preflight must name stop conditions"]


def test_exact_target_identities_match_the_frozen_m6_selection() -> None:
    contract = _json(CONTRACT_PATH)
    m6 = _json(M6_CONTRACT_PATH)
    targets = contract["target_images"]

    assert [target["target_id"] for target in targets] == [target["id"] for target in m6["targets"]]
    assert [target["m6_release"] for target in targets] == [
        target["release"] for target in m6["targets"]
    ]
    assert contract["image_resolution"]["architecture"] == "linux/amd64"

    registry_targets = [target for target in targets if target["pull_ref"]]
    assert len(registry_targets) == 4
    for target in registry_targets:
        assert target["pull_ref"].endswith(target["index_digest"])
        assert target["index_digest"].startswith("sha256:")
        assert len(target["index_digest"]) == 71
        assert target["linux_amd64_manifest_digest"].startswith("sha256:")
        assert len(target["linux_amd64_manifest_digest"]) == 71

    mint = next(target for target in targets if target["target_id"] == "linux-mint-22-3")
    assert mint["pull_ref"] is None
    assert mint["iso_sha256"] == "a081ab202cfda17f6924128dbd2de8b63518ac0531bcfe3f1a1b88097c459bd4"
    assert mint["signing_key_fingerprint"] == "27DEB15644C6B3CF3BD7D291300F846BA25BAE09"
    assert "no Ubuntu image substitution" in mint["source"]
    assert "fail" in mint["construction_rule"]

    manjaro = next(
        target for target in targets if target["target_id"] == "manjaro-stable-2026-06-26"
    )
    assert "reproducible seed" in manjaro["update_rule"]
    assert "2026-06-26" in manjaro["update_rule"]


def test_installation_privileges_are_minimal_and_do_not_grant_docker_group_access() -> None:
    install = _json(CONTRACT_PATH)["docker_installation"]

    assert install["minimum_packages"] == [
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-compose-plugin",
    ]
    assert "official Ubuntu apt repository" in install["method"]
    transport = install["privilege_transport"]
    assert transport["maintainer_terminal"] == "sudo docker"
    assert "pkexec" in transport["automation"]
    assert "graphical" in transport["automation"]
    assert "Never request" in transport["credential_rule"]
    assert "sudo -n" in transport["approval_evidence"]
    forbidden = " ".join(install["forbidden_host_changes"])
    assert "adding any user to the docker group" in forbidden
    assert "firewall" in forbidden
    assert "daemon TCP exposure" in forbidden
    assert "apt autoremove" in forbidden


def test_runtime_cannot_reach_user_data_production_or_unbounded_host_resources() -> None:
    contract = _json(CONTRACT_PATH)
    isolation = contract["container_isolation"]

    assert isolation["concurrency"] == 1
    assert set(isolation["resource_flags"]) >= {
        "--cpus=2",
        "--memory=1536m",
        "--memory-swap=2560m",
        "--pids-limit=512",
        "--security-opt=no-new-privileges",
    }
    assert isolation["network"]["published_ports"] == "none"
    assert isolation["network"]["host_network"] == "forbidden"
    assert isolation["filesystem"]["host_bind_mounts"] == "forbidden"
    assert isolation["filesystem"]["docker_socket_mount"] == "forbidden"
    assert isolation["runtime"]["secrets_credentials_tokens"] == "forbidden"
    assert isolation["runtime"]["production_endpoints_and_databases"] == "forbidden"
    assert isolation["runtime"]["privileged"] is False
    assert isolation["runtime"]["cap_add"] == "forbidden"

    storage = contract["storage_boundary"]
    assert storage["maximum_task_owned_docker_bytes"] == 200_000_000_000
    assert storage["minimum_host_free_bytes"] == 20 * 1024**3
    assert any("local golden image" in rule for rule in storage["rules"])
    assert any("Never run docker system prune" in rule for rule in storage["rules"])


def test_evidence_rollback_and_cleanup_are_scoped_and_explicit() -> None:
    contract = _json(CONTRACT_PATH)
    evidence = contract["evidence"]

    assert evidence["committed_root"] == "documentation/evidence/live-source-install/0.9.1"
    assert evidence["local_staging_root"].startswith("documentation/build/")
    assert evidence["target_transcript"].endswith("transcript.jsonl")
    assert {"exact command in documented order", "exit code", "result disposition"} <= set(
        evidence["required_fields"]
    )
    assert any("credentials" in rule for rule in evidence["commit_rules"])

    rollback = " ".join(contract["rollback"]["install_failure"])
    assert "only task-installed Docker package names" in rollback
    assert "only when the repeated preflight proved both absent" in rollback
    assert "Stop and report" in rollback

    cleanup = contract["final_cleanup"]
    assert cleanup["owner_task"] == "BPM091-M11-13"
    retained = cleanup["retained_host_tooling"]
    assert retained["decision"] == "retain-after-successful-installation"
    assert retained["approved_by"] == "project maintainer"
    assert set(retained["components"]) >= {
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "/etc/apt/sources.list.d/docker.sources",
        "/etc/apt/keyrings/docker.asc",
        "M11 clean target golden images and imported Mint golden image",
        "failed or evidence-needed stopped M11 validation containers",
        "bpm091-m11-net dedicated bridge network",
    }
    assert "Do not add" in retained["user_access_rule"]
    forbidden = " ".join(cleanup["forbidden_cleanup"])
    assert "docker system prune" in forbidden
    assert "apt autoremove" in forbidden
    assert "purging the retained Docker packages" in forbidden
    assert "removing a clean target golden image" in forbidden
    assert "before evidence handoff" in forbidden
    assert "deletion of committed evidence" in forbidden
    assert "Docker Engine remain healthy" in cleanup["success_condition"]
    assert "stopped and inventoried" in cleanup["success_condition"]
    assert "below 200,000,000,000 bytes" in cleanup["success_condition"]


def test_linux_container_work_cannot_be_reported_as_wsl_validation() -> None:
    boundary = _json(CONTRACT_PATH)["wsl_boundary"]

    assert boundary["docker_linux_containers_are_wsl_evidence"] is False
    assert boundary["actual_windows_host_required"] is True
    assert boundary["owner_tasks"] == ["BPM091-M11-10", "BPM091-M11-11", "BPM091-M11-12"]
