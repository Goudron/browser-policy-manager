#!/usr/bin/env python3
"""Build evidence for the BPM 0.9.5 Docker distribution without publishing it."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.9.5.1"
FORBIDDEN_BASE_MODULES = ("numpy", "onnxruntime", "tokenizers")


def _run(*command: str, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    print(f"[docker-smoke] {' '.join(command)}", flush=True)
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def _request(port: int, path: str) -> tuple[int, object]:
    with urlopen(f"http://127.0.0.1:{port}{path}", timeout=3) as response:  # noqa: S310
        content = response.read()
        payload = (
            json.loads(content)
            if response.headers.get_content_type() == "application/json"
            else content
        )
        return response.status, payload


def _wait_ready(port: int) -> None:
    deadline = time.monotonic() + 45
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, payload = _request(port, "/health/ready")
            if status == 200 and payload == {"status": "ready", "ready": True}:
                return
        except (OSError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(0.5)
    raise RuntimeError(f"BPM did not become ready within 45 seconds: {last_error}")


def _published_port(container: str) -> int:
    output = _run("docker", "port", container, "8000/tcp", capture_output=True).stdout.strip()
    host, separator, port = output.rpartition(":")
    if not separator or not host or not port.isdecimal():
        raise RuntimeError(f"Unable to parse BPM port mapping: {output!r}")
    return int(port)


def _start(image: str, volume: str, container: str) -> int:
    _run(
        "docker",
        "run",
        "--detach",
        "--name",
        container,
        "--volume",
        f"{volume}:/var/lib/bpm",
        "--publish",
        "127.0.0.1::8000",
        image,
        "serve",
    )
    return _published_port(container)


def _remove_container(container: str) -> None:
    _run("docker", "rm", "--force", container)


def _assert_base_runtime(image: str) -> None:
    probe = """
import importlib.metadata
import importlib.util

assert importlib.metadata.version('browser-policy-manager') == '0.9.5.1'
assert all(importlib.util.find_spec(module) is None for module in ('numpy', 'onnxruntime', 'tokenizers'))
print('base runtime: OK')
"""
    _run("docker", "run", "--rm", "--entrypoint", "python", image, "-I", "-c", probe)


def smoke(image: str) -> None:
    suffix = uuid.uuid4().hex[:12]
    volume = f"bpm-smoke-{suffix}"
    first = f"bpm-smoke-first-{suffix}"
    second = f"bpm-smoke-second-{suffix}"
    active: str | None = None

    try:
        _assert_base_runtime(image)
        _run("docker", "volume", "create", volume)
        _run("docker", "run", "--rm", "--volume", f"{volume}:/var/lib/bpm", image, "migrate")

        active = first
        port = _start(image, volume, active)
        _wait_ready(port)
        status, root = _request(port, "/")
        assert status == 200 and isinstance(root, dict) and root.get("version") == EXPECTED_VERSION
        status, _ = _request(port, "/health")
        assert status == 200
        status, _ = _request(port, "/help/")
        assert status == 200
        _remove_container(active)
        active = None

        active = second
        port = _start(image, volume, active)
        _wait_ready(port)
        status, profiles = _request(port, "/api/profiles")
        assert status == 200 and isinstance(profiles, list)
        print(
            json.dumps(
                {
                    "image": image,
                    "status": "OK",
                    "version": EXPECTED_VERSION,
                    "volume": "restart-verified",
                },
                sort_keys=True,
            ),
            flush=True,
        )
    finally:
        if active is not None:
            subprocess.run(["docker", "rm", "--force", active], check=False, text=True)
        subprocess.run(["docker", "rm", "--force", first], check=False, text=True)
        subprocess.run(["docker", "rm", "--force", second], check=False, text=True)
        subprocess.run(["docker", "volume", "rm", volume], check=False, text=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Local BPM image tag to verify")
    args = parser.parse_args(argv)
    smoke(args.image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
