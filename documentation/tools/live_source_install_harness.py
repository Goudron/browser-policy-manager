#!/usr/bin/env python3
"""Run retained, evidence-producing Docker validation for Linux source-install topics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DEFAULT_CONFIG = DOCUMENTATION_ROOT / "config/live-source-install-harness-0.9.1.json"
RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,48}$")
BACKLOG_ITEM_PATTERN = re.compile(r"BPM091-M11-[0-9]{2}\Z")
PLACEHOLDER_REF = 'export BPM_REF="<approved-0.9.1-ref>"'
LABEL_VALIDATION = "com.browser-policy-manager.validation"
LABEL_OWNER = "com.browser-policy-manager.owner"
LABEL_RUN = "com.browser-policy-manager.run-id"
LABEL_TARGET = "com.browser-policy-manager.target"
LABEL_ATTEMPT = "com.browser-policy-manager.attempt"
VALIDATION_VALUE = "BPM091-M11"
OWNER_VALUE = "live-source-install"


class HarnessError(RuntimeError):
    """Raised when the harness must fail closed."""


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    output: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")[:60] or "command"


def _repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPOSITORY_ROOT).as_posix()


def _target_profile(config: dict[str, Any], target_id: str) -> dict[str, Any]:
    profiles = {profile["id"]: profile for profile in config["targets"]}
    try:
        return profiles[target_id]
    except KeyError as exc:
        raise HarnessError(f"Unknown target: {target_id}") from exc


def _privileged_target(config: dict[str, Any], target_id: str) -> dict[str, Any]:
    contract_path = REPOSITORY_ROOT / config["privileged_contract"]
    targets = {target["target_id"]: target for target in _load_json(contract_path)["target_images"]}
    try:
        return targets[target_id]
    except KeyError as exc:
        raise HarnessError(f"No privileged image contract for target: {target_id}") from exc


def validate_run_identity(run_id: str, attempt: int) -> None:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise HarnessError("run-id must match [a-z0-9][a-z0-9-]{2,48}")
    if not 1 <= attempt <= 99:
        raise HarnessError("attempt must be between 1 and 99")


def parse_backlog_item(value: str) -> str:
    if not BACKLOG_ITEM_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("backlog item must match BPM091-M11-<two digits>")
    return value


def container_name(config: dict[str, Any], target_id: str, run_id: str, attempt: int) -> str:
    validate_run_identity(run_id, attempt)
    template = config["retention"]["container_name_template"]
    name = template.format(target_id=target_id, run_id=run_id, attempt=f"{attempt:02d}")
    if len(name) > 128:
        raise HarnessError("Generated container name exceeds Docker's 128-character limit")
    return name


def build_plan(
    config: dict[str, Any],
    target_id: str,
    *,
    bpm_ref: str | None,
) -> dict[str, Any]:
    profile = _target_profile(config, target_id)
    source_path = REPOSITORY_ROOT / profile["source_topic"]
    source_bytes = source_path.read_bytes()
    root = ET.fromstring(source_bytes)
    blocks = {block.attrib["id"]: block for block in root.findall(".//codeblock")}
    expected = profile["stage_order"]
    if list(blocks) != expected:
        raise HarnessError(
            f"DITA stage drift for {target_id}: expected {expected}, observed {list(blocks)}"
        )

    commands: list[dict[str, Any]] = []
    placeholder_count = 0
    sequence = 0
    for stage in expected:
        text = (blocks[stage].text or "").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for stage_sequence, documented in enumerate(lines, start=1):
            if documented.endswith("\\"):
                raise HarnessError(
                    f"Multiline shell continuation is not supported: {target_id}/{stage}"
                )
            effective = documented
            if documented == PLACEHOLDER_REF:
                placeholder_count += 1
                if bpm_ref:
                    if bpm_ref == "<approved-0.9.1-ref>" or any(char.isspace() for char in bpm_ref):
                        raise HarnessError("bpm-ref must be a concrete whitespace-free Git ref")
                    effective = f"export BPM_REF={shlex.quote(bpm_ref)}"
            sequence += 1
            commands.append(
                {
                    "command_id": f"{stage}-{stage_sequence:02d}",
                    "sequence": sequence,
                    "stage": stage,
                    "classification": "documented",
                    "documented": documented,
                    "effective": effective,
                    "mode": "background" if documented == "make dev" else "foreground",
                }
            )
    if placeholder_count != 1:
        raise HarnessError(
            f"Expected one BPM_REF placeholder for {target_id}, found {placeholder_count}"
        )

    readiness_attempts = int(config["execution"]["runtime_readiness_attempts"])
    readiness_interval = int(config["execution"]["runtime_readiness_interval_seconds"])
    if readiness_attempts <= 0 or readiness_interval <= 0:
        raise HarnessError("Runtime readiness attempts and interval must be positive")

    return {
        "schema_version": 1,
        "harness_id": config["harness_id"],
        "target_id": target_id,
        "source_topic": profile["source_topic"],
        "source_sha256": _sha256_bytes(source_bytes),
        "stage_order": expected,
        "bpm_ref": bpm_ref,
        "executable": bool(bpm_ref),
        "container_adapter": {
            "classification": config["command_ownership"]["container_only_setup_class"],
            "reason": config["command_ownership"]["container_only_setup_rule"],
            "command": profile["container_adapter_command"],
        },
        "runtime_adapter": {
            "readiness_attempts": readiness_attempts,
            "readiness_interval_seconds": readiness_interval,
        },
        "identity_probe": profile["identity_probe"],
        "commands": commands,
    }


def container_create_args(
    config: dict[str, Any],
    *,
    name: str,
    image: str,
    target_id: str,
    run_id: str,
    attempt: int,
) -> list[str]:
    execution = config["execution"]
    labels = {
        LABEL_VALIDATION: VALIDATION_VALUE,
        LABEL_OWNER: OWNER_VALUE,
        LABEL_RUN: run_id,
        LABEL_TARGET: target_id,
        LABEL_ATTEMPT: str(attempt),
    }
    args = ["create", "--name", name]
    for key, value in labels.items():
        args.extend(["--label", f"{key}={value}"])
    args.extend(execution["resource_flags"])
    args.extend(
        [
            "--network",
            execution["network"],
            "--restart=no",
            "--platform",
            execution["platform"],
            image,
            "/bin/sh",
            "-c",
            "trap 'exit 0' TERM INT; while :; do sleep 3600 & wait $!; done",
        ]
    )
    return args


def render_execution_script(plan: dict[str, Any], run_id: str) -> str:
    if not plan["executable"]:
        raise HarnessError("A concrete --bpm-ref is required before rendering an executable plan")
    evidence_dir = f"/var/tmp/bpm091-live-source/{run_id}/{plan['target_id']}"
    lines = [
        "#!/usr/bin/env bash",
        "set -u -o pipefail",
        f"evidence_dir={shlex.quote(evidence_dir)}",
        'mkdir -p "$evidence_dir/command-output"',
        'events="$evidence_dir/events.jsonl"',
        'runtime_log="$evidence_dir/runtime.log"',
        'runtime_pid=""',
        "emit_start() {",
        '  printf \'{"event":"command_start","command_id":"%s",'
        '"stage":"%s","classification":"%s","started_at":"%s"}\\n\' '
        '"$1" "$2" "$3" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$events"',
        "}",
        "emit_end() {",
        '  output="$evidence_dir/command-output/$1.txt"',
        '  bytes="$(stat -c %s "$output" 2>/dev/null || printf 0)"',
        '  sha="$(sha256sum "$output" 2>/dev/null | awk \'{print $1}\' || true)"',
        '  printf \'{"event":"command_end","command_id":"%s",'
        '"stage":"%s","classification":"%s","finished_at":"%s",'
        '"exit_code":%s,"output_bytes":%s,"output_sha256":"%s"}\\n\' '
        '"$1" "$2" "$3" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$4" "$bytes" "$sha" '
        '>> "$events"',
        "}",
        "run_foreground() {",
        '  command_id="$1"; stage="$2"; classification="$3"; command="$4"',
        '  output="$evidence_dir/command-output/$command_id.txt"',
        '  emit_start "$command_id" "$stage" "$classification"',
        "  set +e",
        '  eval "$command" > >(tee "$output") 2> >(tee -a "$output" >&2)',
        "  rc=$?",
        "  set -e",
        '  emit_end "$command_id" "$stage" "$classification" "$rc"',
        '  return "$rc"',
        "}",
        "run_background() {",
        '  command_id="$1"; stage="$2"; classification="$3"; command="$4"',
        '  emit_start "$command_id" "$stage" "$classification"',
        '  setsid bash -c "$command" >> "$runtime_log" 2>&1 &',
        "  runtime_pid=$!",
        '  : > "$evidence_dir/command-output/$command_id.txt"',
        '  emit_end "$command_id" "$stage" "$classification" 0',
        "}",
        "stop_runtime() {",
        '  if test -n "$runtime_pid" && kill -0 "$runtime_pid" 2>/dev/null; then',
        '    kill -INT -- "-$runtime_pid" 2>/dev/null || kill -INT "$runtime_pid"',
        '    wait "$runtime_pid" || true',
        "  fi",
        "}",
        "trap stop_runtime EXIT",
    ]

    adapter = plan["container_adapter"]
    lines.append(
        "run_foreground adapter-setup container-adapter container_adapter "
        f"{shlex.quote(adapter['command'])} || exit $?"
    )
    second_terminal_started = False
    for command in plan["commands"]:
        if command["stage"] == "verify" and not second_terminal_started:
            lines.append(
                "run_foreground adapter-second-terminal runtime container_adapter "
                + shlex.quote('cd "$HOME"')
                + " || exit $?"
            )
            second_terminal_started = True
        args = " ".join(
            shlex.quote(str(value))
            for value in (
                command["command_id"],
                command["stage"],
                command["classification"],
                command["effective"],
            )
        )
        if command["mode"] == "background":
            lines.append(f"run_background {args}")
            runtime_adapter = plan["runtime_adapter"]
            wait_command = (
                "ready=0; "
                f"for attempt in $(seq 1 {runtime_adapter['readiness_attempts']}); do "
                "if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; "
                "then ready=1; break; fi; "
                'if ! kill -0 "$runtime_pid" 2>/dev/null; then break; fi; '
                f"sleep {runtime_adapter['readiness_interval_seconds']}; done; "
                'test "$ready" -eq 1'
            )
            lines.append(
                "run_foreground adapter-wait-ready runtime container_adapter "
                f"{shlex.quote(wait_command)} || exit $?"
            )
        else:
            lines.append(f"run_foreground {args} || exit $?")
    lines.extend(
        [
            "run_foreground adapter-stop runtime container_adapter "
            + shlex.quote(
                'test -n "$runtime_pid" && kill -INT -- "-$runtime_pid" '
                '2>/dev/null || true; wait "$runtime_pid" || true; runtime_pid=""'
            )
            + " || exit $?",
            "run_foreground adapter-stop-probe runtime container_adapter "
            + shlex.quote("! curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1")
            + " || exit $?",
            'cat "$runtime_log"',
            "run_foreground adapter-complete runtime container_adapter "
            + shlex.quote('printf "complete\\n" > "$evidence_dir/completed"')
            + " || exit $?",
        ]
    )
    return "\n".join(lines) + "\n"


class EventRecorder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.output_root = root / "command-output"
        self.events_path = root / "events.jsonl"
        self.output_root.mkdir(parents=True, exist_ok=True)
        self._counter = 0

    def append(self, event: dict[str, Any]) -> None:
        with self.events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")

    def next_event_id(self, label: str) -> str:
        self._counter += 1
        return f"{self._counter:04d}-{_slug(label)}"


class DockerClient:
    def __init__(self, recorder: EventRecorder) -> None:
        self.recorder = recorder

    def run(
        self,
        label: str,
        args: list[str],
        *,
        check: bool = True,
        input_text: str | None = None,
        quiet: bool = False,
    ) -> CommandResult:
        event_id = self.recorder.next_event_id(label)
        output_path = self.recorder.output_root / f"{event_id}.txt"
        command = ["docker", *args]
        self.recorder.append(
            {
                "event": "host_command_start",
                "event_id": event_id,
                "classification": "harness",
                "started_at": _utc_now(),
                "command": command,
                "stdin_sha256": _sha256_bytes(input_text.encode()) if input_text else None,
            }
        )
        if input_text is not None:
            completed = subprocess.run(
                command,
                input=input_text,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            output = completed.stdout
            if output and not quiet:
                print(output, end="", flush=True)
            returncode = completed.returncode
        else:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            chunks: list[str] = []
            assert process.stdout is not None
            with output_path.open("w", encoding="utf-8") as stream:
                for line in process.stdout:
                    stream.write(line)
                    chunks.append(line)
                    if not quiet:
                        print(line, end="", flush=True)
            returncode = process.wait()
            output = "".join(chunks)
        if input_text is not None:
            output_path.write_text(output, encoding="utf-8")
        output_bytes = output_path.read_bytes()
        self.recorder.append(
            {
                "event": "host_command_end",
                "event_id": event_id,
                "classification": "harness",
                "finished_at": _utc_now(),
                "exit_code": returncode,
                "output_path": output_path.relative_to(self.recorder.root).as_posix(),
                "output_bytes": len(output_bytes),
                "output_sha256": _sha256_bytes(output_bytes),
            }
        )
        if check and returncode != 0:
            raise HarnessError(f"Docker command failed ({returncode}): {shlex.join(command)}")
        return CommandResult(returncode=returncode, output=output)


def _require_root() -> None:
    if os.geteuid() != 0:
        raise HarnessError(
            "Docker mutation requires root: use sudo in a terminal or approve one pkexec dialog"
        )


def _check_host_storage(config: dict[str, Any]) -> int:
    free = shutil.disk_usage(REPOSITORY_ROOT).free
    minimum = int(config["retention"]["minimum_host_free_bytes"])
    if free < minimum:
        raise HarnessError(f"Host free space {free} is below the required floor {minimum}")
    return free


def _ensure_no_running_validation_container(client: DockerClient) -> None:
    result = client.run(
        "running-validation-containers",
        ["ps", "-q", "--filter", f"label={LABEL_VALIDATION}={VALIDATION_VALUE}"],
        quiet=True,
    )
    if result.output.strip():
        raise HarnessError("Another M11 validation container is running; concurrency is one")


def _ensure_network(config: dict[str, Any], client: DockerClient) -> None:
    name = config["execution"]["network"]
    current = client.run("inspect-network", ["network", "inspect", name], check=False, quiet=True)
    if current.returncode == 0:
        network = json.loads(current.output)[0]
        labels = network.get("Labels") or {}
        if network["Driver"] != "bridge" or labels.get(LABEL_VALIDATION) != VALIDATION_VALUE:
            raise HarnessError(f"Existing network {name} does not match the M11 contract")
        return
    client.run(
        "create-network",
        [
            "network",
            "create",
            "--driver",
            "bridge",
            "--label",
            f"{LABEL_VALIDATION}={VALIDATION_VALUE}",
            "--label",
            f"{LABEL_OWNER}={OWNER_VALUE}",
            "--label",
            f"{LABEL_RUN}=shared-retained",
            "--label",
            f"{LABEL_TARGET}=shared-network",
            name,
        ],
    )


def _resolve_image(
    config: dict[str, Any], target_id: str, client: DockerClient
) -> tuple[str, dict[str, Any]]:
    target = _privileged_target(config, target_id)
    pull_ref = target.get("pull_ref")
    if pull_ref:
        cached = client.run(
            f"inspect-cached-golden-image-{target_id}",
            ["image", "inspect", pull_ref],
            check=False,
            quiet=True,
        )
        if cached.returncode == 0:
            image = json.loads(cached.output)[0]
            expected_digest = target["index_digest"]
            observed_digests = {
                image.get("Id"),
                image.get("Descriptor", {}).get("digest"),
                *(digest.rsplit("@", 1)[-1] for digest in image.get("RepoDigests") or []),
            }
            if image.get("Os") != "linux" or image.get("Architecture") != "amd64":
                raise HarnessError(f"Cached golden image platform drift for {target_id}")
            if expected_digest not in observed_digests:
                raise HarnessError(f"Cached golden image digest drift for {target_id}")
            return pull_ref, image

        raw = client.run(
            f"inspect-registry-{target_id}",
            ["buildx", "imagetools", "inspect", "--raw", pull_ref],
            quiet=True,
        )
        manifest = json.loads(raw.output)
        amd64 = [
            item
            for item in manifest.get("manifests", [])
            if item.get("platform", {}).get("os") == "linux"
            and item.get("platform", {}).get("architecture") == "amd64"
        ]
        if len(amd64) != 1:
            raise HarnessError(f"Expected one linux/amd64 manifest for {target_id}")
        if amd64[0]["digest"] != target["linux_amd64_manifest_digest"]:
            raise HarnessError(f"linux/amd64 manifest drift for {target_id}")
        client.run(
            f"pull-{target_id}",
            ["pull", "--platform", config["execution"]["platform"], pull_ref],
        )
        image_ref = pull_ref
    else:
        image_ref = target["tag"]
        available = client.run(
            f"inspect-local-image-{target_id}",
            ["image", "inspect", image_ref],
            check=False,
            quiet=True,
        )
        if available.returncode != 0:
            raise HarnessError(
                f"Local image {image_ref} is unavailable; run prepare-mint before this target"
            )
    inspected = client.run(
        f"inspect-image-{target_id}", ["image", "inspect", image_ref], quiet=True
    )
    image = json.loads(inspected.output)[0]
    if image.get("Os") != "linux" or image.get("Architecture") != "amd64":
        raise HarnessError(f"Image platform drift for {target_id}")
    return image_ref, image


def _create_retained_container(
    config: dict[str, Any],
    client: DockerClient,
    *,
    target_id: str,
    run_id: str,
    attempt: int,
    image_ref: str,
    name_override: str | None = None,
) -> str:
    name = name_override or container_name(config, target_id, run_id, attempt)
    existing = client.run("check-container-name", ["inspect", name], check=False, quiet=True)
    if existing.returncode == 0:
        raise HarnessError(f"Container already exists and will not be reused: {name}")
    client.run(
        "create-retained-container",
        container_create_args(
            config,
            name=name,
            image=image_ref,
            target_id=target_id,
            run_id=run_id,
            attempt=attempt,
        ),
    )
    client.run("start-retained-container", ["start", name])
    return name


def _stop_and_inspect(client: DockerClient, name: str, output_root: Path) -> dict[str, Any]:
    running = client.run(
        "container-running-state",
        ["inspect", "--format", "{{.State.Running}}", name],
        check=False,
        quiet=True,
    )
    if running.returncode == 0 and running.output.strip() == "true":
        client.run("stop-retained-container", ["stop", "--timeout", "30", name])
    inspected = client.run("inspect-retained-container", ["inspect", "--size", name], quiet=True)
    payload = json.loads(inspected.output)[0]
    _write_json(output_root / "container-inspect.json", payload)
    return payload


def _inventory(config: dict[str, Any], client: DockerClient) -> dict[str, Any]:
    containers_result = client.run(
        "inventory-containers",
        [
            "ps",
            "-a",
            "--filter",
            f"label={LABEL_VALIDATION}={VALIDATION_VALUE}",
            "--format",
            "{{json .}}",
        ],
        quiet=True,
    )
    containers = [json.loads(line) for line in containers_result.output.splitlines() if line]
    container_storage = []
    writable_bytes = 0
    for container in containers:
        name = container["Names"]
        inspected = client.run(
            f"inventory-container-size-{name}",
            ["inspect", "--size", name],
            quiet=True,
        )
        payload = json.loads(inspected.output)[0]
        size_rw = int(payload.get("SizeRw") or 0)
        writable_bytes += size_rw
        container_storage.append(
            {
                "name": name,
                "id": payload["Id"],
                "state": payload["State"]["Status"],
                "exit_code": payload["State"].get("ExitCode"),
                "image": payload["Image"],
                "size_rw_bytes": size_rw,
            }
        )
    network_result = client.run(
        "inventory-network",
        ["network", "inspect", config["execution"]["network"]],
        check=False,
        quiet=True,
    )
    network = json.loads(network_result.output)[0] if network_result.returncode == 0 else None

    image_refs = []
    image_ids: dict[str, dict[str, Any]] = {}
    privileged = _load_json(REPOSITORY_ROOT / config["privileged_contract"])
    for target in privileged["target_images"]:
        image_ref = target.get("pull_ref") or target["tag"]
        result = client.run(
            f"inventory-image-{target['target_id']}",
            ["image", "inspect", image_ref],
            check=False,
            quiet=True,
        )
        if result.returncode != 0:
            continue
        image = json.loads(result.output)[0]
        image_refs.append({"target_id": target["target_id"], "ref": image_ref, "id": image["Id"]})
        image_ids[image["Id"]] = image

    approximate_image_bytes = sum(int(image.get("Size", 0)) for image in image_ids.values())
    approximate_bytes = approximate_image_bytes + writable_bytes
    maximum = int(config["retention"]["maximum_task_owned_docker_bytes"])
    if approximate_bytes > maximum:
        raise HarnessError(
            f"Retained Docker bytes {approximate_bytes} exceed the M11 ceiling {maximum}"
        )
    return {
        "captured_at": _utc_now(),
        "containers": containers,
        "container_storage": container_storage,
        "images": image_refs,
        "network": network,
        "approximate_unique_image_bytes": approximate_image_bytes,
        "approximate_container_writable_bytes": writable_bytes,
        "approximate_task_owned_docker_bytes": approximate_bytes,
        "maximum_task_owned_docker_bytes": maximum,
        "host_free_bytes": _check_host_storage(config),
        "minimum_host_free_bytes": config["retention"]["minimum_host_free_bytes"],
    }


def _record_inventory(
    config: dict[str, Any],
    client: DockerClient,
    output_root: Path,
    filename: str,
) -> dict[str, Any]:
    inventory = _inventory(config, client)
    _write_json(output_root / filename, inventory)
    return inventory


def _run_self_test(
    config: dict[str, Any], args: argparse.Namespace, output_root: Path
) -> dict[str, Any]:
    _require_root()
    _check_host_storage(config)
    recorder = EventRecorder(output_root)
    client = DockerClient(recorder)
    _ensure_no_running_validation_container(client)
    _ensure_network(config, client)
    _record_inventory(config, client, output_root, "inventory-before.json")
    image_ref, image = _resolve_image(config, args.target, client)
    name = _create_retained_container(
        config,
        client,
        target_id=args.target,
        run_id=args.run_id,
        attempt=args.attempt,
        image_ref=image_ref,
    )
    result = "blocked"
    error = None
    try:
        profile = _target_profile(config, args.target)
        probe = client.run(
            "identity-probe",
            ["exec", name, "/bin/sh", "-lc", profile["identity_probe"]],
        )
        if probe.returncode != 0:
            raise HarnessError(f"Identity probe failed for {args.target}")
        result = "pass"
    except HarnessError as exc:
        error = str(exc)
    finally:
        inspect = _stop_and_inspect(client, name, output_root)
    exit_code = int(inspect["State"]["ExitCode"])
    if exit_code != 0:
        result = "blocked"
        error = error or f"Retained container exited with code {exit_code}"
    inventory = _record_inventory(config, client, output_root, "inventory.json")
    summary = {
        "schema_version": 1,
        "backlog_item": "BPM091-M11-03",
        "run_id": args.run_id,
        "attempt": args.attempt,
        "target_id": args.target,
        "mode": "self-test",
        "result": result,
        "error": error,
        "container_name": name,
        "container_id": inspect["Id"],
        "container_state": inspect["State"]["Status"],
        "container_exit_code": exit_code,
        "container_retained": True,
        "image_ref": image_ref,
        "image_id": image["Id"],
        "network_retained": True,
        "inventory": inventory,
    }
    _write_json(output_root / "summary.json", summary)
    if error:
        raise HarnessError(error)
    return summary


def _run_documented_install(
    config: dict[str, Any], args: argparse.Namespace, output_root: Path
) -> dict[str, Any]:
    _require_root()
    plan = build_plan(config, args.target, bpm_ref=args.bpm_ref)
    _write_json(output_root / "plan.json", plan)
    script = render_execution_script(plan, args.run_id)
    (output_root / "run.sh").write_text(script, encoding="utf-8")

    recorder = EventRecorder(output_root)
    client = DockerClient(recorder)
    _ensure_no_running_validation_container(client)
    _ensure_network(config, client)
    _record_inventory(config, client, output_root, "inventory-before.json")
    image_ref, image = _resolve_image(config, args.target, client)
    name = _create_retained_container(
        config,
        client,
        target_id=args.target,
        run_id=args.run_id,
        attempt=args.attempt,
        image_ref=image_ref,
    )
    result = "blocked"
    error = None
    try:
        remote_root = f"/var/tmp/bpm091-live-source/{args.run_id}/{args.target}"
        client.run(
            "inject-execution-script",
            [
                "exec",
                "-i",
                name,
                "/bin/sh",
                "-c",
                f"mkdir -p {shlex.quote(remote_root)} && cat > {shlex.quote(remote_root + '/run.sh')}",
            ],
            input_text=script,
        )
        client.run(
            "execute-documented-install",
            ["exec", name, "/bin/bash", f"{remote_root}/run.sh"],
        )
        client.run(
            "verify-completion-marker",
            [
                "exec",
                name,
                "/bin/sh",
                "-lc",
                f'test "$(cat {shlex.quote(remote_root + "/completed")})" = complete',
            ],
        )
        result = "pass"
    except HarnessError as exc:
        error = str(exc)
        raise
    finally:
        remote_root = f"/var/tmp/bpm091-live-source/{args.run_id}/{args.target}"
        client.run(
            "copy-container-evidence",
            ["cp", f"{name}:{remote_root}/.", str(output_root / "container-evidence")],
            check=False,
        )
        inspect = _stop_and_inspect(client, name, output_root)
        inventory = _record_inventory(config, client, output_root, "inventory.json")
        _write_json(
            output_root / "summary.json",
            {
                "schema_version": 1,
                "backlog_item": args.backlog_item,
                "run_id": args.run_id,
                "attempt": args.attempt,
                "target_id": args.target,
                "mode": "documented-install",
                "bpm_ref": args.bpm_ref,
                "result": result,
                "error": error,
                "container_name": name,
                "container_id": inspect["Id"],
                "container_state": inspect["State"]["Status"],
                "container_retained": True,
                "image_ref": image_ref,
                "image_id": image["Id"],
                "inventory": inventory,
            },
        )
    return _load_json(output_root / "summary.json")


def _run_mint_stage(
    config: dict[str, Any],
    client: DockerClient,
    output_root: Path,
    container: str,
    label: str,
    command: str,
) -> None:
    client.run(label, ["exec", container, "/bin/bash", "-lc", command])
    _record_inventory(config, client, output_root, f"inventory-after-{label}.json")


def _import_mint_rootfs(
    recorder: EventRecorder,
    *,
    container: str,
    workdir: str,
    import_command: list[str],
) -> str:
    event_id = recorder.next_event_id("import-mint-rootfs")
    output_path = recorder.output_root / f"{event_id}.txt"
    source_script = (
        "set -o pipefail; "
        f"tar --numeric-owner --xattrs --acls -C {shlex.quote(workdir + '/rootfs')} "
        f"-cf - . | tee >(sha256sum > {shlex.quote(workdir + '/mint-rootfs.tar.sha256')})"
    )
    source_command = ["docker", "exec", container, "/bin/bash", "-lc", source_script]
    recorder.append(
        {
            "event": "host_command_start",
            "event_id": event_id,
            "classification": "harness",
            "started_at": _utc_now(),
            "pipeline": [source_command, import_command],
            "stdin_sha256": None,
        }
    )
    source = subprocess.Popen(source_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert source.stdout is not None
    imported = subprocess.run(
        import_command,
        stdin=source.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    source.stdout.close()
    source_status = source.wait()
    source_error = source.stderr.read().decode(errors="replace") if source.stderr else ""
    output = source_error + imported.stdout
    output_path.write_text(output, encoding="utf-8")
    print(output, end="", flush=True)
    output_bytes = output_path.read_bytes()
    recorder.append(
        {
            "event": "host_command_end",
            "event_id": event_id,
            "classification": "harness",
            "finished_at": _utc_now(),
            "exit_code": imported.returncode if source_status == 0 else source_status,
            "source_exit_code": source_status,
            "import_exit_code": imported.returncode,
            "output_path": output_path.relative_to(recorder.root).as_posix(),
            "output_bytes": len(output_bytes),
            "output_sha256": _sha256_bytes(output_bytes),
        }
    )
    if source_status != 0 or imported.returncode != 0:
        raise HarnessError("Docker import of the verified Mint rootfs failed")
    return imported.stdout.strip()


def _prepare_mint(
    config: dict[str, Any], args: argparse.Namespace, output_root: Path
) -> dict[str, Any]:
    _require_root()
    _check_host_storage(config)
    recorder = EventRecorder(output_root)
    client = DockerClient(recorder)
    _ensure_no_running_validation_container(client)
    _ensure_network(config, client)
    _record_inventory(config, client, output_root, "inventory-before.json")
    preparation = config["mint_image_preparation"]
    mint_target = _privileged_target(config, "linux-mint-22-3")
    existing = client.run(
        "check-mint-image", ["image", "inspect", preparation["image_tag"]], check=False, quiet=True
    )
    if existing.returncode == 0:
        raise HarnessError("Mint image already exists and will not be overwritten")

    helper_ref, helper_image = _resolve_image(config, preparation["helper_target"], client)
    helper_name = preparation["helper_name_template"].format(
        run_id=args.run_id, attempt=f"{args.attempt:02d}"
    )
    name = _create_retained_container(
        config,
        client,
        target_id="linux-mint-rootfs-helper",
        run_id=args.run_id,
        attempt=args.attempt,
        image_ref=helper_ref,
        name_override=helper_name,
    )
    workdir = preparation["workdir"]
    packages = " ".join(preparation["helper_packages"])
    iso_url = mint_target["official_iso"]
    sums_url = mint_target["official_checksum_file"]
    signature_url = mint_target["official_signature_file"]
    fingerprint = preparation["signing_key_fingerprint"]
    filename = preparation["iso_filename"]
    expected_iso_sha = preparation["iso_sha256"]
    cd = f"cd {shlex.quote(workdir)}"
    stages = [
        (
            "mint-helper-packages",
            " && ".join(
                [
                    "apt-get update",
                    f"apt-get install -y --no-install-recommends {packages}",
                    f"mkdir -p {shlex.quote(workdir)}",
                ]
            ),
        ),
        (
            "mint-authenticate-checksum",
            " && ".join(
                [
                    cd,
                    f"curl -fL --progress-bar {shlex.quote(sums_url)} -o sha256sum.txt",
                    f"curl -fL --progress-bar {shlex.quote(signature_url)} -o sha256sum.txt.gpg",
                    f"gpg --batch --keyserver hkp://keys.openpgp.org:80 --recv-key {fingerprint}",
                    f"gpg --batch --with-colons --fingerprint {fingerprint} | grep -F 'fpr:::::::::{fingerprint}:'",
                    "gpg --batch --verify sha256sum.txt.gpg sha256sum.txt",
                    f"awk '$2 == \"*{filename}\" {{print $1}}' sha256sum.txt | grep -Fx {expected_iso_sha}",
                ]
            ),
        ),
        (
            "mint-download-iso",
            " && ".join(
                [
                    cd,
                    f"curl -fL --progress-bar {shlex.quote(iso_url)} -o {shlex.quote(filename)}",
                    f"printf '%s  %s\\n' {expected_iso_sha} {shlex.quote(filename)} | sha256sum -c -",
                ]
            ),
        ),
        (
            "mint-extract-squashfs",
            " && ".join(
                [
                    cd,
                    "xorriso -osirrox on "
                    f"-indev {shlex.quote(filename)} "
                    "-extract /casper/filesystem.squashfs filesystem.squashfs",
                ]
            ),
        ),
        (
            "mint-unpack-rootfs",
            " && ".join(
                [
                    cd,
                    "unsquashfs -processors 2 -d rootfs filesystem.squashfs",
                    '. rootfs/etc/os-release && test "$ID" = linuxmint '
                    '&& test "$VERSION_ID" = 22.3 && test "$VERSION_CODENAME" = zena',
                ]
            ),
        ),
        ("mint-measure-rootfs", f"{cd} && du -sb rootfs"),
    ]
    imported_id = ""
    try:
        for label, command in stages:
            _run_mint_stage(config, client, output_root, name, label, command)
        import_command = [
            "docker",
            "import",
            "--change",
            f"LABEL {LABEL_VALIDATION}={VALIDATION_VALUE}",
            "--change",
            f"LABEL {LABEL_OWNER}={OWNER_VALUE}",
            "--change",
            f"LABEL {LABEL_RUN}={args.run_id}",
            "--change",
            f"LABEL {LABEL_TARGET}=linux-mint-22-3",
            "-",
            preparation["image_tag"],
        ]
        imported_id = _import_mint_rootfs(
            recorder,
            container=name,
            workdir=workdir,
            import_command=import_command,
        )
        _record_inventory(config, client, output_root, "inventory-after-mint-import.json")
        _run_mint_stage(
            config,
            client,
            output_root,
            name,
            "mint-record-and-release-transients",
            " && ".join(
                [
                    cd,
                    "cat mint-rootfs.tar.sha256",
                    f"rm -rf rootfs filesystem.squashfs {shlex.quote(filename)}",
                    "test ! -e rootfs && test ! -e filesystem.squashfs",
                ]
            ),
        )
    finally:
        helper_inspect = _stop_and_inspect(client, name, output_root)
    image = client.run(
        "inspect-imported-mint-image",
        ["image", "inspect", preparation["image_tag"]],
        quiet=True,
    )
    inventory = _record_inventory(config, client, output_root, "inventory.json")
    summary = {
        "schema_version": 1,
        "backlog_item": "BPM091-M11-03",
        "run_id": args.run_id,
        "attempt": args.attempt,
        "target_id": "linux-mint-22-3",
        "mode": "prepare-mint",
        "result": "pass",
        "official_iso": iso_url,
        "iso_sha256": preparation["iso_sha256"],
        "signing_key_fingerprint": fingerprint,
        "helper_container": name,
        "helper_container_id": helper_inspect["Id"],
        "helper_container_state": helper_inspect["State"]["Status"],
        "helper_container_retained": True,
        "helper_image_id": helper_image["Id"],
        "mint_image_tag": preparation["image_tag"],
        "mint_image_import_result": imported_id,
        "mint_image": json.loads(image.output)[0],
        "inventory": inventory,
    }
    _write_json(output_root / "summary.json", summary)
    return summary


def _output_root(config: dict[str, Any], args: argparse.Namespace) -> Path:
    base = (
        Path(args.output_root)
        if args.output_root
        else REPOSITORY_ROOT / config["evidence"]["local_root"]
    )
    return base / args.run_id / args.target / f"attempt-{args.attempt:02d}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Extract a non-mutating command plan from DITA")
    plan.add_argument("--target", required=True)
    plan.add_argument("--bpm-ref")
    plan.add_argument("--output", type=Path)

    for name in ("self-test", "run", "prepare-mint"):
        command = subparsers.add_parser(name)
        command.add_argument("--run-id", required=True)
        command.add_argument("--attempt", type=int, default=1)
        command.add_argument("--output-root", type=Path)
        if name == "prepare-mint":
            command.set_defaults(target="linux-mint-22-3")
        else:
            command.add_argument("--target", required=True)
        if name == "run":
            command.add_argument("--bpm-ref", required=True)
            command.add_argument("--backlog-item", required=True, type=parse_backlog_item)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--run-id", required=True)
    inventory.add_argument("--output-root", type=Path)
    inventory.set_defaults(target="inventory", attempt=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = _load_json(args.config)
    try:
        if args.command == "plan":
            plan = build_plan(config, args.target, bpm_ref=args.bpm_ref)
            if args.output:
                _write_json(args.output, plan)
            else:
                print(json.dumps(plan, ensure_ascii=True, indent=2))
            return 0

        validate_run_identity(args.run_id, args.attempt)
        output_root = _output_root(config, args)
        if output_root.exists():
            raise HarnessError(
                f"Evidence directory already exists and will not be reused: {output_root}"
            )
        output_root.mkdir(parents=True, exist_ok=True)
        if args.command == "self-test":
            result = _run_self_test(config, args, output_root)
        elif args.command == "run":
            result = _run_documented_install(config, args, output_root)
        elif args.command == "prepare-mint":
            result = _prepare_mint(config, args, output_root)
        else:
            _require_root()
            recorder = EventRecorder(output_root)
            result = _inventory(config, DockerClient(recorder))
            _write_json(output_root / "inventory.json", result)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except HarnessError as exc:
        print(f"live-source-install harness: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
