from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
MODULE_PATH = DOCUMENTATION_ROOT / "tools/live_source_install_harness.py"
CONFIG_PATH = DOCUMENTATION_ROOT / "config/live-source-install-harness-0.9.1.json"
SPEC = importlib.util.spec_from_file_location("live_source_install_harness", MODULE_PATH)
assert SPEC and SPEC.loader
harness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = harness
SPEC.loader.exec_module(harness)


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_run_identity_and_container_names_are_bounded_and_attempt_specific() -> None:
    config = _config()

    assert harness.container_name(config, "ubuntu-26-04", "m11-03-self-test", 1) == (
        "bpm091-ubuntu-26-04-m11-03-self-test-a01"
    )
    assert harness.container_name(config, "ubuntu-26-04", "m11-03-self-test", 2).endswith(
        "-a02"
    )
    with pytest.raises(harness.HarnessError, match="run-id"):
        harness.validate_run_identity("INVALID", 1)
    with pytest.raises(harness.HarnessError, match="attempt"):
        harness.validate_run_identity("valid-run", 0)


@pytest.mark.parametrize("profile", _config()["targets"], ids=lambda item: item["id"])
def test_plan_extracts_each_dita_stage_and_command_in_source_order(profile: dict) -> None:
    plan = harness.build_plan(_config(), profile["id"], bpm_ref="7ee1d3e")

    assert plan["target_id"] == profile["id"]
    assert plan["stage_order"] == profile["stage_order"]
    assert plan["executable"] is True
    assert plan["runtime_adapter"] == {
        "readiness_attempts": 300,
        "readiness_interval_seconds": 2,
    }
    assert len(plan["source_sha256"]) == 64
    assert [command["sequence"] for command in plan["commands"]] == list(
        range(1, len(plan["commands"]) + 1)
    )
    observed_stages = list(dict.fromkeys(command["stage"] for command in plan["commands"]))
    assert observed_stages == profile["stage_order"]
    assert all(command["classification"] == "documented" for command in plan["commands"])


def test_plan_substitutes_only_the_approved_ref_assignment() -> None:
    plan = harness.build_plan(_config(), "ubuntu-26-04", bpm_ref="feature/bpm-0.9.1")
    changed = [
        command
        for command in plan["commands"]
        if command["documented"] != command["effective"]
    ]

    assert changed == [
        {
            "command_id": "checkout-02",
            "sequence": 8,
            "stage": "checkout",
            "classification": "documented",
            "documented": 'export BPM_REF="<approved-0.9.1-ref>"',
            "effective": "export BPM_REF=feature/bpm-0.9.1",
            "mode": "foreground",
        }
    ]
    with pytest.raises(harness.HarnessError, match="concrete whitespace-free"):
        harness.build_plan(_config(), "ubuntu-26-04", bpm_ref="bad ref")


def test_non_mutating_plan_without_ref_cannot_render_an_execution_script() -> None:
    plan = harness.build_plan(_config(), "ubuntu-26-04", bpm_ref=None)

    assert plan["executable"] is False
    with pytest.raises(harness.HarnessError, match="concrete --bpm-ref"):
        harness.render_execution_script(plan, "m11-03-test")


def test_rendered_script_records_adapter_documented_runtime_and_shutdown_events() -> None:
    plan = harness.build_plan(_config(), "ubuntu-26-04", bpm_ref="7ee1d3e")
    script = harness.render_execution_script(plan, "m11-03-test")

    assert "run_foreground adapter-setup container-adapter container_adapter" in script
    assert "run_background checkout" not in script
    assert "run_background start-04 start documented 'make dev'" in script
    assert "adapter-wait-ready" in script
    assert "seq 1 300" in script
    assert 'test \"$ready\" -eq 1' in script
    assert "&& exit 0" not in script
    assert script.count("adapter-second-terminal") == 1
    assert script.index("adapter-second-terminal") < script.index(
        "run_foreground verify-01 verify documented"
    )
    assert "container_adapter 'cd \"$HOME\"'" in script
    assert "adapter-stop-probe" in script
    assert "! curl -fsS http://127.0.0.1:8000/health" in script
    assert "then exit 1" not in script
    assert "else exit 0" not in script
    assert "adapter-complete" in script
    assert 'completed\"' in script
    assert '"exit_code"' in script
    assert "command-output" in script
    assert "docker rm" not in script
    assert "docker system prune" not in script


def test_container_create_arguments_match_resource_network_and_retention_boundary() -> None:
    config = _config()
    args = harness.container_create_args(
        config,
        name="bpm091-ubuntu-test-a01",
        image="ubuntu@example",
        target_id="ubuntu-26-04",
        run_id="m11-03-test",
        attempt=1,
    )
    joined = " ".join(args)

    assert args[0] == "create"
    assert "--cpus=2" in args
    assert "--memory=1536m" in args
    assert "--memory-swap=2560m" in args
    assert "--pids-limit=512" in args
    assert "--ulimit=nofile=4096:4096" in args
    assert "--security-opt=no-new-privileges" in args
    assert "--network bpm091-m11-net" in joined
    assert "--restart=no" in args
    assert "--rm" not in args
    assert "--privileged" not in args
    assert "--cap-add" not in args
    assert "--volume" not in args
    assert "--mount" not in args
    assert "--publish" not in args
    assert args[-4:-2] == ["ubuntu@example", "/bin/sh"]
    assert args[-2] == "-c"
    assert "trap 'exit 0' TERM INT" in args[-1]
    assert "sleep infinity" not in args


def test_cached_golden_image_is_reused_without_registry_or_pull() -> None:
    config = _config()
    target = next(
        item
        for item in json.loads(
            (REPOSITORY_ROOT / config["privileged_contract"]).read_text(encoding="utf-8")
        )["target_images"]
        if item["target_id"] == "ubuntu-26-04"
    )

    class CachedClient:
        def __init__(self) -> None:
            self.labels: list[str] = []

        def run(self, label: str, args: list[str], **_: object) -> harness.CommandResult:
            self.labels.append(label)
            assert args == ["image", "inspect", target["pull_ref"]]
            return harness.CommandResult(
                returncode=0,
                output=json.dumps(
                    [
                        {
                            "Id": target["index_digest"],
                            "RepoDigests": [f"ubuntu@{target['index_digest']}"],
                            "Descriptor": {"digest": target["index_digest"]},
                            "Os": "linux",
                            "Architecture": "amd64",
                        }
                    ]
                ),
            )

    client = CachedClient()
    image_ref, image = harness._resolve_image(config, "ubuntu-26-04", client)

    assert image_ref == target["pull_ref"]
    assert image["Id"] == target["index_digest"]
    assert client.labels == ["inspect-cached-golden-image-ubuntu-26-04"]


def test_cli_plan_writes_reviewable_json_without_docker(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"

    result = harness.main(
        [
            "--config",
            str(CONFIG_PATH),
            "plan",
            "--target",
            "fedora-44",
            "--bpm-ref",
            "7ee1d3e",
            "--output",
            str(output),
        ]
    )

    assert result == 0
    plan = json.loads(output.read_text(encoding="utf-8"))
    assert plan["target_id"] == "fedora-44"
    assert plan["commands"][0]["documented"] == ". /etc/os-release"


def test_mutating_modes_fail_before_docker_when_not_elevated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(harness.os, "geteuid", lambda: 1000)

    result = harness.main(
        [
            "--config",
            str(CONFIG_PATH),
            "self-test",
            "--target",
            "ubuntu-26-04",
            "--run-id",
            "m11-03-test",
            "--output-root",
            str(tmp_path),
        ]
    )

    assert result == 2
    assert not list(tmp_path.rglob("events.jsonl"))


def test_mutating_mode_never_reuses_an_attempt_evidence_directory(tmp_path: Path) -> None:
    existing = tmp_path / "m11-03-test/ubuntu-26-04/attempt-02"
    existing.mkdir(parents=True)
    marker = existing / "retained.txt"
    marker.write_text("attempt one evidence\n", encoding="utf-8")

    result = harness.main(
        [
            "--config",
            str(CONFIG_PATH),
            "self-test",
            "--target",
            "ubuntu-26-04",
            "--run-id",
            "m11-03-test",
            "--attempt",
            "2",
            "--output-root",
            str(tmp_path),
        ]
    )

    assert result == 2
    assert marker.read_text(encoding="utf-8") == "attempt one evidence\n"
    assert not list(existing.rglob("events.jsonl"))
