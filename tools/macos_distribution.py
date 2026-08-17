#!/usr/bin/env python3
"""Build and smoke-test the BPM 0.9.5 native macOS DMG test artifacts.

The tool never uses Linux, Docker, or a cross-compiled substitute for a macOS
bundle. Build and smoke run only on the target-native macOS architecture.
Unsigned test evidence is deliberately not eligible for release staging.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MACOS_ROOT = REPO_ROOT / "distributions" / "macos"
CONFIG_PATH = MACOS_ROOT / "targets.json"
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "macos-packages"
RELEASE_STORE_ROOT = REPO_ROOT / "distributions" / "releases"
TARGET_VERSION = "0.9.5"


class MacOSDistributionError(RuntimeError):
    """A macOS DMG input, target, or receipt violates its release contract."""


@dataclass(frozen=True)
class MacOSTarget:
    identifier: str
    architecture: str
    runner: str
    artifact: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_version() -> str:
    payload = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def _source_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _documentation_archive() -> tuple[Path, Path]:
    archive = REPO_ROOT / "documentation" / "dist" / f"bpm-documentation-{TARGET_VERSION}.tar.gz"
    return archive, archive.with_suffix(archive.suffix + ".sha256")


def _require_string(raw: dict[str, Any], key: str, *, location: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise MacOSDistributionError(f"{location}.{key} must be a non-empty string")
    return value


def load_targets() -> list[MacOSTarget]:
    """Load the frozen Intel and Apple Silicon target manifest."""
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise MacOSDistributionError("macOS target manifest schema_version must be 1")
    if payload.get("target_bpm_version") != TARGET_VERSION:
        raise MacOSDistributionError("macOS target manifest must match BPM 0.9.5")
    if payload.get("installer_format") != "dmg" or payload.get("minimum_macos_version") != "14":
        raise MacOSDistributionError("macOS targets must be macOS 14+ DMGs")
    runtime = payload.get("runtime")
    application = payload.get("application")
    records = payload.get("targets")
    if (
        not isinstance(runtime, dict)
        or not isinstance(application, dict)
        or not isinstance(records, list)
    ):
        raise MacOSDistributionError("macOS target manifest has incomplete metadata")
    if runtime.get("python_version") != "3.14.6" or runtime.get("pyinstaller_version") != "6.21.0":
        raise MacOSDistributionError("macOS targets must pin CPython 3.14.6 and PyInstaller 6.21.0")
    if application.get("bundle_name") != "Browser Policy Manager.app":
        raise MacOSDistributionError("macOS application bundle name is not frozen")
    targets: list[MacOSTarget] = []
    for record in records:
        if not isinstance(record, dict):
            raise MacOSDistributionError("macOS target must be an object")
        target = MacOSTarget(
            identifier=_require_string(record, "id", location="target"),
            architecture=_require_string(record, "architecture", location="target"),
            runner=_require_string(record, "runner", location="target"),
            artifact=_require_string(record, "artifact", location="target"),
        )
        expected_artifact = (
            f"browser-policy-manager-{TARGET_VERSION}-macos-{target.architecture}.dmg"
        )
        if target.artifact != expected_artifact:
            raise MacOSDistributionError(f"{target.identifier} artifact name is not frozen")
        targets.append(target)
    if {(target.identifier, target.architecture, target.runner) for target in targets} != {
        ("macos-14-x64", "x64", "macos-15-intel"),
        ("macos-14-arm64", "arm64", "macos-14"),
    }:
        raise MacOSDistributionError("macOS target manifest must contain the two native CI targets")
    return sorted(targets, key=lambda target: target.identifier)


def validate_release_inputs() -> list[MacOSTarget]:
    """Fail before an assembly action when immutable inputs are incomplete."""
    targets = load_targets()
    if _project_version() != TARGET_VERSION:
        raise MacOSDistributionError("pyproject version must match macOS target version")
    archive, checksum = _documentation_archive()
    if not archive.is_file() or not checksum.is_file():
        raise MacOSDistributionError(
            "verified documentation archive is required before macOS packaging"
        )
    if checksum.read_text(encoding="ascii") != f"{_sha256(archive)}  {archive.name}\n":
        raise MacOSDistributionError("documentation archive checksum does not match archive")
    required_paths = (
        MACOS_ROOT / "build-dmg.sh",
        MACOS_ROOT / "smoke-dmg.sh",
        MACOS_ROOT / "launcher.py",
        MACOS_ROOT / "Info.plist.in",
        MACOS_ROOT / "BPM Migrate.command.in",
        MACOS_ROOT / "requirements.macos.lock",
        REPO_ROOT / "app" / "static" / "profiles_bundles" / "profiles-bundles-manifest.json",
        REPO_ROOT / "alembic.ini",
        REPO_ROOT / "alembic",
        REPO_ROOT / "migration_support",
    )
    missing = [
        path.relative_to(REPO_ROOT).as_posix() for path in required_paths if not path.exists()
    ]
    if missing:
        raise MacOSDistributionError("macOS release payload is incomplete: " + ", ".join(missing))
    lock = (MACOS_ROOT / "requirements.macos.lock").read_text(encoding="utf-8")
    for prohibited in ("numpy==", "onnxruntime==", "tokenizers=="):
        if prohibited in lock:
            raise MacOSDistributionError(
                "macOS runtime lock must not include optional AI dependencies"
            )
    print(
        "macOS release inputs: OK "
        + json.dumps(
            {
                "documentation_sha256": _sha256(archive),
                "targets": [target.identifier for target in targets],
                "version": TARGET_VERSION,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return targets


def _select_targets(selector: str, targets: list[MacOSTarget]) -> list[MacOSTarget]:
    if selector == "all":
        return targets
    chosen = [target for target in targets if target.identifier == selector]
    if not chosen:
        available = ", ".join(target.identifier for target in targets)
        raise MacOSDistributionError(
            f"unknown macOS target {selector!r}; choose one of: {available}, all"
        )
    return chosen


def _artifact_directory(target: MacOSTarget) -> Path:
    return ARTIFACT_ROOT / TARGET_VERSION / target.identifier


def _require_native_host(target: MacOSTarget) -> None:
    expected = {"x64": "x86_64", "arm64": "arm64"}[target.architecture]
    if sys.platform != "darwin" or platform.machine() != expected:
        raise MacOSDistributionError(
            f"{target.identifier} build and smoke require native macOS {expected}; "
            f"found {sys.platform}/{platform.machine()}"
        )


def _run(script: Path, *arguments: str, stage: str) -> None:
    command = [str(script), *arguments]
    print(f"[macos-distribution] {stage}: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def build_target(target: MacOSTarget) -> Path:
    _require_native_host(target)
    output = _artifact_directory(target)
    output.mkdir(parents=True, exist_ok=True)
    for path in (
        output / target.artifact,
        output / f"{target.artifact}.sha256",
        output / "build-environment.json",
        output / "manifest.json",
        output / "smoke.json",
    ):
        path.unlink(missing_ok=True)
    _run(
        MACOS_ROOT / "build-dmg.sh",
        "--source-root",
        str(REPO_ROOT),
        "--output-directory",
        str(output),
        "--source-revision",
        _source_revision(),
        "--target",
        target.identifier,
        "--architecture",
        target.architecture,
        "--artifact",
        target.artifact,
        stage=f"build {target.identifier}",
    )
    artifact = output / target.artifact
    checksum = output / f"{target.artifact}.sha256"
    environment = output / "build-environment.json"
    if not all(path.is_file() for path in (artifact, checksum, environment)):
        raise MacOSDistributionError("macOS builder did not produce complete DMG evidence")
    if checksum.read_text(encoding="ascii") != f"{_sha256(artifact)}  {artifact.name}\n":
        raise MacOSDistributionError("macOS DMG checksum does not match generated artifact")
    build_environment = json.loads(environment.read_text(encoding="utf-8"))
    if build_environment.get("signing") != "ad-hoc-test-only":
        raise MacOSDistributionError("test DMG builder did not record its ad-hoc signature state")
    archive, _ = _documentation_archive()
    manifest = {
        "schema_version": 1,
        "bpm_version": TARGET_VERSION,
        "target": target.identifier,
        "architecture": target.architecture,
        "format": "dmg",
        "minimum_macos_version": "14",
        "artifact": {"path": artifact.name, "sha256": _sha256(artifact)},
        "source_revision": _source_revision(),
        "documentation_archive": {"path": archive.name, "sha256": _sha256(archive)},
        "build_environment": {"path": environment.name, "sha256": _sha256(environment)},
        "signing": "ad-hoc-test-only",
        "notarization": "not-submitted",
        "migration_contract": "explicit-bpm-migrate-only",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"macOS DMG built: {artifact.relative_to(REPO_ROOT)} sha256={manifest['artifact']['sha256']}",
        flush=True,
    )
    return artifact


def smoke_target(target: MacOSTarget) -> None:
    _require_native_host(target)
    output = _artifact_directory(target)
    artifact = output / target.artifact
    checksum = output / f"{target.artifact}.sha256"
    if not artifact.is_file() or not checksum.is_file():
        raise MacOSDistributionError("build the native macOS DMG before smoke-testing it")
    if checksum.read_text(encoding="ascii") != f"{_sha256(artifact)}  {artifact.name}\n":
        raise MacOSDistributionError("macOS DMG checksum mismatch before smoke")
    _run(
        MACOS_ROOT / "smoke-dmg.sh",
        "--dmg",
        str(artifact),
        "--architecture",
        target.architecture,
        stage=f"smoke {target.identifier}",
    )
    smoke = {
        "schema_version": 1,
        "target": target.identifier,
        "artifact": artifact.name,
        "artifact_sha256": _sha256(artifact),
        "result": "passed",
    }
    (output / "smoke.json").write_text(
        json.dumps(smoke, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "smoke", "list"))
    parser.add_argument("--target", default="all")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    targets = validate_release_inputs()
    selected = _select_targets(args.target, targets)
    if args.command == "list":
        for target in selected:
            print(f"{target.identifier}\tmacOS 14+ {target.architecture}\tdmg\t{target.artifact}")
        return 0
    if args.command == "validate":
        return 0
    for target in selected:
        if args.command == "build":
            build_target(target)
        elif args.command == "smoke":
            smoke_target(target)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MacOSDistributionError, subprocess.CalledProcessError) as exc:
        print(f"macOS distribution failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
