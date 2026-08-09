"""Verify the BPM 0.9.4 release/incubation/development supply boundary."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path(__file__).with_name("release_boundary_manifest_0_9_4.json")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
REQUIRED_CATEGORIES = {
    "default_release",
    "optional_incubation",
    "development_tooling",
    "release_optional_integration",
}
REQUIRED_SECTIONS = {"modules", "dependencies", "commands", "fixtures", "tests"}
NATIVE_AI_DISTRIBUTIONS = {"numpy", "onnxruntime", "tokenizers"}
FORBIDDEN_BASE_MODULES = {
    *NATIVE_AI_DISTRIBUTIONS,
    "app.ai.e5_runtime",
    "app.ai.local_inference_worker",
    "app.ai.rag_bootstrap",
    "app.documentation.local_assistant_runtime",
    "app.documentation.retrieval",
}


def _canonicalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_names(values: list[str]) -> set[str]:
    names: set[str] = set()
    for value in values:
        match = re.match(r"\s*([A-Za-z0-9_.-]+)", value)
        if match is None:
            raise AssertionError(f"Unsupported requirement declaration: {value!r}")
        names.add(_canonicalize(match.group(1)))
    return names


def _load_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["target_version"] == "0.9.4"
    assert set(manifest["categories"]) == REQUIRED_CATEGORIES
    for category in manifest["categories"].values():
        assert set(category) == REQUIRED_SECTIONS
        assert all(isinstance(value, list) for value in category.values())
    return manifest


def _module_or_path_exists(value: str) -> bool:
    if "/" in value:
        return (REPO_ROOT / value).exists()
    relative = Path(*value.split("."))
    return (REPO_ROOT / relative).with_suffix(".py").is_file() or (REPO_ROOT / relative).is_dir()


def _make_targets() -> set[str]:
    source = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Za-z0-9_-]+):", source, re.MULTILINE))


def _verify_classification(manifest: dict[str, Any]) -> None:
    categories = manifest["categories"]
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    optional = project["optional-dependencies"]

    assert _requirement_names(project["dependencies"]) == set(
        categories["default_release"]["dependencies"]
    )
    assert _requirement_names(optional["ai"]) == set(
        categories["optional_incubation"]["dependencies"]
    )
    assert _requirement_names(optional["dev"]) == set(
        categories["development_tooling"]["dependencies"]
    )
    assert _requirement_names(optional["postgres"]) == set(
        categories["release_optional_integration"]["dependencies"]
    )
    assert _requirement_names(optional["ai"]) == NATIVE_AI_DISTRIBUTIONS
    assert set(optional) == {"ai", "dev", "postgres"}

    targets = _make_targets()
    for category in categories.values():
        for module in category["modules"]:
            assert _module_or_path_exists(module), module
        for fixture in category["fixtures"]:
            assert (REPO_ROOT / fixture).exists(), fixture
        for test in category["tests"]:
            assert (REPO_ROOT / test).is_file(), test
        assert set(category["commands"]) <= targets

    from tests.marker_policy import AI_INCUBATION_TEST_FILES

    assert set(categories["optional_incubation"]["tests"]) == AI_INCUBATION_TEST_FILES


def _copy_source_for_build(destination: Path) -> None:
    for filename in ("pyproject.toml", "README.md", "LICENSE"):
        shutil.copy2(REPO_ROOT / filename, destination / filename)
    shutil.copytree(
        REPO_ROOT / "app",
        destination / "app",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def _run(command: list[str], *, cwd: Path, stage: str) -> subprocess.CompletedProcess[str]:
    print(f"[release-boundary] {stage}", flush=True)
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(
            f"{stage} failed with exit {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed


def _clean_wheel_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="bpm-release-boundary-") as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        _copy_source_for_build(source)
        wheels = root / "wheels"
        wheels.mkdir()
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--disable-pip-version-check",
                "--no-deps",
                "--wheel-dir",
                str(wheels),
                str(source),
            ],
            cwd=root,
            stage="build clean wheel",
        )
        (wheel,) = wheels.glob("browser_policy_manager-*.whl")

        environment = root / "base-venv"
        _run([sys.executable, "-m", "venv", str(environment)], cwd=root, stage="create base venv")
        python = environment / "bin" / "python"
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheel),
            ],
            cwd=root,
            stage="install base wheel without extras",
        )
        _run([str(python), "-m", "pip", "check"], cwd=root, stage="check base dependencies")
        probe = """
import asyncio
import importlib.util
import json
import sys

import httpx
import app.main

native = ("numpy", "onnxruntime", "tokenizers")
assert all(importlib.util.find_spec(name) is None for name in native)
assert not (set(sys.modules) & set(__FORBIDDEN_MODULES__))

async def verify():
    transport = httpx.ASGITransport(app=app.main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assistant = await client.get("/api/documentation-assistant/status?locale=en")
        local_model = await client.get("/api/local-model")
    assert assistant.status_code == 200
    assert local_model.status_code == 200
    assistant_payload = assistant.json()
    model_payload = local_model.json()
    assert {key: assistant_payload[key] for key in ("api_version", "state", "reason_code", "message_key", "locale")} == {
        "api_version": 1,
        "state": "ready",
        "reason_code": "assistant_training_notice",
        "message_key": "assistant_training_notice",
        "locale": "en",
    }
    assert model_payload["api_version"] == 1
    assert model_payload["operation"] == {"state": "idle"}
    assert model_payload["verification"]["reason_code"] == "artifact_missing"
    print(json.dumps({
        "forbidden_loaded": sorted(set(sys.modules) & set(__FORBIDDEN_MODULES__)),
        "assistant": {key: assistant_payload[key] for key in ("state", "reason_code", "message_key", "locale")},
        "local_model": {
            "operation": model_payload["operation"]["state"],
            "verification": model_payload["verification"]["reason_code"],
        },
    }, sort_keys=True))

asyncio.run(verify())
""".replace("__FORBIDDEN_MODULES__", repr(sorted(FORBIDDEN_BASE_MODULES)))
        completed = _run(
            [str(python), "-I", "-c", probe],
            cwd=root,
            stage="probe base wheel startup and disabled surfaces",
        )
        return json.loads(completed.stdout)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-clean-wheel-smoke",
        action="store_true",
        help="Validate the manifest only; intended for focused unit tests.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = _load_manifest()
    print("[release-boundary] validate delivery classification", flush=True)
    _verify_classification(manifest)
    if args.skip_clean_wheel_smoke:
        print("release/incubation/development classification: OK", flush=True)
        return 0
    result = _clean_wheel_smoke()
    print(f"base wheel without AI extras: OK {json.dumps(result, sort_keys=True)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
