from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
HARNESS = DOCUMENTATION_ROOT / "config/live-source-install-harness-0.9.1.json"
COMMANDS = DOCUMENTATION_ROOT / "config/linux-source-install-command-contract-0.9.1.json"
PRIVILEGED = (
    DOCUMENTATION_ROOT / "config/live-source-install-privileged-validation-contract-0.9.1.json"
)
TOOL = DOCUMENTATION_ROOT / "tools/live_source_install_harness.py"

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_harness_contract_is_scoped_to_m11_03_and_the_accepted_boundaries() -> None:
    harness = _json(HARNESS)
    privileged = _json(PRIVILEGED)

    assert harness["schema_version"] == 1
    assert harness["harness_id"] == "bpm-0.9.1-live-source-install-harness"
    assert harness["backlog_item"] == "BPM091-M11-03"
    assert harness["target_bpm_version"] == "0.9.1"
    assert harness["status"] in {"implemented-awaiting-self-test", "accepted"}
    assert harness["command_contract"] == COMMANDS.relative_to(REPOSITORY_ROOT).as_posix()
    assert harness["privileged_contract"] == PRIVILEGED.relative_to(REPOSITORY_ROOT).as_posix()
    assert privileged["status"] == "accepted"
    assert harness["execution"]["resource_flags"] == privileged["container_isolation"][
        "resource_flags"
    ]
    assert harness["execution"]["network"] == privileged["container_isolation"]["network"][
        "name"
    ]
    assert harness["execution"]["runtime_readiness_attempts"] == 300
    assert harness["execution"]["runtime_readiness_interval_seconds"] == 2


def test_five_profiles_match_command_and_image_contracts_exactly() -> None:
    harness = _json(HARNESS)
    command_targets = _json(COMMANDS)["targets"]
    image_targets = _json(PRIVILEGED)["target_images"]
    profiles = harness["targets"]

    expected_ids = [target["id"] for target in command_targets]
    assert [profile["id"] for profile in profiles] == expected_ids
    assert [profile["image_target"] for profile in profiles] == expected_ids
    assert [target["target_id"] for target in image_targets] == expected_ids
    for profile, command_target in zip(profiles, command_targets, strict=True):
        assert profile["source_topic"].endswith(f"{command_target['topic_id']}.dita")
        source = REPOSITORY_ROOT / profile["source_topic"]
        root = ET.fromstring(source.read_text(encoding="utf-8"))
        assert [block.attrib["id"] for block in root.findall(".//codeblock")] == profile[
            "stage_order"
        ]


def test_container_adapter_is_visible_and_documented_commands_remain_source_owned() -> None:
    ownership = _json(HARNESS)["command_ownership"]

    assert ownership["source"].startswith("English DITA codeblocks")
    assert ownership["required_ref_argument"] == "--bpm-ref"
    assert ownership["placeholder_command"] == 'export BPM_REF="<approved-0.9.1-ref>"'
    assert "Replace only" in ownership["substitution_rule"]
    assert ownership["container_only_setup_class"] == "container_adapter"
    assert "OCI bases omit" in ownership["container_only_setup_rule"]
    assert "no-new-privileges" in ownership["container_only_setup_rule"]
    assert "without exiting the parent script" in ownership["runtime_rule"]
    assert "completion marker" in ownership["runtime_rule"]
    assert ownership["hidden_setup"] == "forbidden"


def test_retention_keeps_golden_images_and_retry_reuses_no_installed_state() -> None:
    retention = _json(HARNESS)["retention"]
    privileged_cleanup = _json(PRIVILEGED)["final_cleanup"]
    tool = TOOL.read_text(encoding="utf-8")

    assert retention["delete_subcommand"] == "absent"
    assert retention["remove_after_run"] is False
    assert retention["retain_golden_images"] is True
    assert "without registry access" in retention["golden_image_cache_rule"]
    assert "exact recorded identity" in retention["derived_install_state_rule"]
    assert retention["retain_network"] is True
    assert retention["retain_stopped_containers_until_evidence_handoff"] is True
    assert retention["stop_after_run"] is True
    assert "new container name" in retention["retry_rule"]
    assert retention["maximum_task_owned_docker_bytes"] == 200_000_000_000
    assert retention["minimum_host_free_bytes"] == 20 * 1024**3
    assert "docker rm" not in tool
    assert "docker system prune" not in tool
    assert '["stop", "--timeout", "30", name]' in tool
    assert '"--time"' not in tool
    assert "trap 'exit 0' TERM INT" in tool
    assert '"verify-completion-marker"' in tool
    forbidden = " ".join(privileged_cleanup["forbidden_cleanup"])
    assert "removing a clean target golden image" in forbidden
    assert "before evidence handoff" in forbidden


def test_evidence_contract_covers_commands_output_exit_inspect_and_inventory() -> None:
    evidence = _json(HARNESS)["evidence"]

    assert "attempt-<nn>" in evidence["plan"]
    assert evidence["plan"].endswith("plan.json")
    assert "attempt-<nn>" in evidence["events"]
    assert evidence["events"].endswith("events.jsonl")
    assert "command-output" in evidence["command_output"]
    assert evidence["container_evidence"].endswith("container-evidence")
    assert evidence["inspect"].endswith("container-inspect.json")
    assert evidence["inventory"].endswith("inventory.json")
    joined = " ".join(evidence["rules"])
    for required in ("documented and effective commands", "exit code", "SHA-256", "Stream output"):
        assert required in joined
    assert "credentials" in joined


def test_mint_preparation_is_authenticated_resource_limited_and_retained() -> None:
    harness = _json(HARNESS)
    mint = harness["mint_image_preparation"]
    image = next(
        target for target in _json(PRIVILEGED)["target_images"] if target["target_id"] == "linux-mint-22-3"
    )

    assert mint["owner_task"] == "BPM091-M11-03"
    assert mint["helper_target"] == "ubuntu-26-04"
    assert mint["iso_sha256"] == image["iso_sha256"]
    assert mint["signing_key_fingerprint"] == image["signing_key_fingerprint"]
    assert mint["image_tag"] == image["tag"]
    assert {"gnupg", "squashfs-tools", "xorriso"} <= set(mint["helper_packages"])
    rules = " ".join(mint["rules"])
    assert "detached signature" in rules
    assert "without host mounts or devices" in rules
    assert "stop and retain the helper" in rules
    assert "release only transient ISO" in rules
    assert "approximate_container_writable_bytes" in TOOL.read_text(encoding="utf-8")
