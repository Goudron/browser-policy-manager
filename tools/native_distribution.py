#!/usr/bin/env python3
"""Build and smoke-test BPM 0.9.6 native Linux distribution packages.

The builder runs one frozen Linux target at a time. It assembles an isolated
CPython 3.14.6 runtime, BPM's base wheel, Alembic payload, and verified product
documentation into a native `.deb`, `.rpm`, or `pkg.tar.zst` artifact. No
registry publication happens here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "distributions" / "native" / "targets.json"
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "native-packages"
RELEASE_STORE_ROOT = REPO_ROOT / "distributions" / "releases"
TARGET_VERSION = "0.9.6"
ARCHITECTURE = "amd64"
REQUIRED_TARGET_IDS = frozenset(
    {
        "ubuntu-26-04",
        "debian-13-5",
        "fedora-44",
        "linux-mint-22-3",
        "manjaro-stable",
    }
)
REQUIRED_FORMATS = {"deb", "rpm", "arch"}


class NativeDistributionError(RuntimeError):
    """A package release input or target run does not meet its contract."""


@dataclass(frozen=True)
class Target:
    """One frozen native package target."""

    identifier: str
    release: str
    package_format: str
    builder_image: str
    builder_evidence: str
    package_release: str
    artifact: str
    runtime_dependencies: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(
    command: list[str], *, stage: str, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    print(f"[native-distribution] {stage}: {' '.join(command)}", flush=True)
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


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


def _parse_target(identifier: str, raw: Any) -> Target:
    if not isinstance(raw, dict):
        raise NativeDistributionError(f"target {identifier} must be an object")
    dependencies = raw.get("runtime_dependencies")
    if not isinstance(dependencies, list) or not all(
        isinstance(value, str) for value in dependencies
    ):
        raise NativeDistributionError(f"target {identifier} has invalid runtime_dependencies")
    values = {
        key: raw.get(key)
        for key in (
            "release",
            "format",
            "builder_image",
            "builder_evidence",
            "package_release",
            "artifact",
        )
    }
    if not all(isinstance(value, str) and value for value in values.values()):
        raise NativeDistributionError(f"target {identifier} has incomplete metadata")
    return Target(
        identifier=identifier,
        release=values["release"],
        package_format=values["format"],
        builder_image=values["builder_image"],
        builder_evidence=values["builder_evidence"],
        package_release=values["package_release"],
        artifact=values["artifact"],
        runtime_dependencies=tuple(dependencies),
    )


def load_targets() -> dict[str, Target]:
    """Load and validate the short, release-owned target manifest."""
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise NativeDistributionError("native target manifest schema_version must be 1")
    if payload.get("target_bpm_version") != TARGET_VERSION:
        raise NativeDistributionError("native target manifest must match BPM 0.9.6")
    if payload.get("architecture") != ARCHITECTURE:
        raise NativeDistributionError("native target manifest must be amd64-only")
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("python_version") != "3.14.6":
        raise NativeDistributionError("native target manifest must pin CPython 3.14.6")
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, dict) or set(raw_targets) != REQUIRED_TARGET_IDS:
        raise NativeDistributionError("native target manifest must declare exactly five targets")
    targets = {
        identifier: _parse_target(identifier, raw) for identifier, raw in raw_targets.items()
    }
    if {target.package_format for target in targets.values()} != REQUIRED_FORMATS:
        raise NativeDistributionError("native targets must cover deb, rpm, and Arch formats")
    if len({target.artifact for target in targets.values()}) != len(targets):
        raise NativeDistributionError("native artifact names must be unique")
    for target in targets.values():
        if not target.builder_evidence or not target.runtime_dependencies:
            raise NativeDistributionError(
                f"target {target.identifier} lacks reproducibility evidence"
            )
        if target.identifier == "linux-mint-22-3" and not target.builder_image.startswith(
            "bpm091/"
        ):
            raise NativeDistributionError("Mint must use the approved locally imported image")
    return targets


def _documentation_archive() -> tuple[Path, Path]:
    archive = REPO_ROOT / "documentation" / "dist" / f"bpm-documentation-{TARGET_VERSION}.tar.gz"
    return archive, archive.with_suffix(archive.suffix + ".sha256")


def validate_release_inputs() -> dict[str, Target]:
    """Fail before invoking a target package manager on incomplete release input."""
    targets = load_targets()
    if _project_version() != TARGET_VERSION:
        raise NativeDistributionError("pyproject version must match native target version")
    archive, checksum = _documentation_archive()
    if not archive.is_file() or not checksum.is_file():
        raise NativeDistributionError(
            "verified documentation archive is required before native packaging"
        )
    expected = f"{_sha256(archive)}  {archive.name}\n"
    if checksum.read_text(encoding="ascii") != expected:
        raise NativeDistributionError("documentation archive checksum does not match archive")
    required_paths = (
        REPO_ROOT / "app" / "static" / "profiles_bundles" / "profiles-bundles-manifest.json",
        REPO_ROOT / "alembic.ini",
        REPO_ROOT / "alembic",
        REPO_ROOT / "distributions" / "docker" / "requirements.lock",
        REPO_ROOT / "distributions" / "native" / "build-target.sh",
        REPO_ROOT / "distributions" / "native" / "smoke-target.sh",
    )
    missing = [
        path.relative_to(REPO_ROOT).as_posix() for path in required_paths if not path.exists()
    ]
    if missing:
        raise NativeDistributionError("native release payload is incomplete: " + ", ".join(missing))
    print(
        "native release inputs: OK "
        + json.dumps(
            {
                "documentation_sha256": _sha256(archive),
                "targets": sorted(targets),
                "version": TARGET_VERSION,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return targets


def _targets_for_selection(targets: dict[str, Target], selection: str) -> tuple[Target, ...]:
    if selection == "all":
        return tuple(targets[identifier] for identifier in sorted(targets))
    try:
        return (targets[selection],)
    except KeyError as exc:
        raise NativeDistributionError(f"unknown native target: {selection}") from exc


def _image_overrides(values: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for value in values:
        identifier, separator, image = value.partition("=")
        if not separator or not identifier or not image:
            raise NativeDistributionError("--image must have TARGET=IMAGE form")
        if identifier in overrides:
            raise NativeDistributionError(f"duplicate image override for {identifier}")
        overrides[identifier] = image
    unknown = set(overrides) - REQUIRED_TARGET_IDS
    if unknown:
        raise NativeDistributionError(
            "unknown image override target: " + ", ".join(sorted(unknown))
        )
    return overrides


def _artifact_directory(target: Target) -> Path:
    return ARTIFACT_ROOT / TARGET_VERSION / target.identifier


def _release_store_directory() -> Path:
    return RELEASE_STORE_ROOT / TARGET_VERSION


def _docker_command(
    target: Target,
    *,
    image: str,
    output: Path,
    script: str,
    source_revision: str,
    artifact_read_only: bool,
) -> list[str]:
    mount_mode = "readonly," if artifact_read_only else ""
    command = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
        "--cpus",
        "2",
        "--memory",
        "1536m",
        "--memory-swap",
        "2560m",
        "--pids-limit",
        "512",
        "--ulimit",
        "nofile=4096:4096",
        "--security-opt",
        "no-new-privileges:true",
        "--label",
        "bpm.native-distribution=0.9.6",
        "--label",
        f"bpm.native-target={target.identifier}",
        "--mount",
        f"type=bind,source={REPO_ROOT},target=/source,readonly",
        "--mount",
        f"type=bind,{mount_mode}source={output},target=/output" if not artifact_read_only else "",
    ]
    if artifact_read_only:
        command[-1] = f"type=bind,readonly,source={output},target=/packages"
    command.extend(
        [
            "--env",
            f"BPM_NATIVE_TARGET={target.identifier}",
            "--env",
            f"BPM_NATIVE_FORMAT={target.package_format}",
            "--env",
            f"BPM_NATIVE_ARTIFACT={target.artifact}",
            "--env",
            f"BPM_NATIVE_PACKAGE_RELEASE={target.package_release}",
            "--env",
            f"BPM_NATIVE_RUNTIME_DEPENDENCIES={','.join(target.runtime_dependencies)}",
            "--env",
            f"BPM_NATIVE_SOURCE_REVISION={source_revision}",
            image,
            "/bin/bash",
            f"/source/distributions/native/{script}",
        ]
    )
    return command


def _release_manifest(target: Target, *, image: str, artifact: Path) -> dict[str, object]:
    archive, _ = _documentation_archive()
    environment = artifact.parent / "build-environment.txt"
    if not environment.is_file():
        raise NativeDistributionError(
            "native builder did not retain its package-manager resolution"
        )
    return {
        "schema_version": 1,
        "bpm_version": TARGET_VERSION,
        "target": target.identifier,
        "target_release": target.release,
        "architecture": ARCHITECTURE,
        "format": target.package_format,
        "artifact": {"path": artifact.name, "sha256": _sha256(artifact)},
        "source_revision": _source_revision(),
        "documentation_archive": {"path": archive.name, "sha256": _sha256(archive)},
        "builder": {"image": image, "evidence": target.builder_evidence},
        "build_environment": {"path": environment.name, "sha256": _sha256(environment)},
        "migration_contract": "explicit-bpm-migrate-only",
    }


def build_target(target: Target, *, image: str) -> Path:
    """Build one exact target package and write its value-free release receipt."""
    output = _artifact_directory(target)
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / target.artifact
    for path in (
        artifact,
        artifact.with_suffix(artifact.suffix + ".sha256"),
        output / "manifest.json",
        output / "build-environment.txt",
    ):
        path.unlink(missing_ok=True)
    command = _docker_command(
        target,
        image=image,
        output=output,
        script="build-target.sh",
        source_revision=_source_revision(),
        artifact_read_only=False,
    )
    _run(command, stage=f"build {target.identifier}")
    if not artifact.is_file():
        raise NativeDistributionError(f"native builder did not produce {artifact.name}")
    expected_checksum = f"{_sha256(artifact)}  {artifact.name}\n"
    checksum = artifact.with_suffix(artifact.suffix + ".sha256")
    if not checksum.is_file() or checksum.read_text(encoding="ascii") != expected_checksum:
        raise NativeDistributionError(f"native builder checksum mismatch for {artifact.name}")
    manifest = _release_manifest(target, image=image, artifact=artifact)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"native package built: {artifact.relative_to(REPO_ROOT)} sha256={manifest['artifact']['sha256']}",
        flush=True,
    )
    return artifact


def smoke_target(target: Target, *, image: str) -> None:
    """Install the exact artifact into a fresh target userspace and prove it runs."""
    output = _artifact_directory(target)
    artifact = output / target.artifact
    checksum = artifact.with_suffix(artifact.suffix + ".sha256")
    if not artifact.is_file() or not checksum.is_file():
        raise NativeDistributionError(f"build {target.identifier} before smoke-testing it")
    if checksum.read_text(encoding="ascii") != f"{_sha256(artifact)}  {artifact.name}\n":
        raise NativeDistributionError(f"artifact checksum mismatch before smoke: {artifact.name}")
    command = _docker_command(
        target,
        image=image,
        output=output,
        script="smoke-target.sh",
        source_revision=_source_revision(),
        artifact_read_only=True,
    )
    _run(command, stage=f"smoke {target.identifier}")


def _verified_artifact(target: Target) -> tuple[Path, Path, dict[str, object]]:
    """Return one built artifact only after its receipt and checksum agree."""
    output = _artifact_directory(target)
    artifact = output / target.artifact
    checksum = artifact.with_suffix(artifact.suffix + ".sha256")
    manifest_path = output / "manifest.json"
    environment = output / "build-environment.txt"
    if not all(path.is_file() for path in (artifact, checksum, manifest_path, environment)):
        raise NativeDistributionError(f"build {target.identifier} before staging its release asset")
    expected_checksum = f"{_sha256(artifact)}  {artifact.name}\n"
    if checksum.read_text(encoding="ascii") != expected_checksum:
        raise NativeDistributionError(f"artifact checksum mismatch before staging: {artifact.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("target") != target.identifier:
        raise NativeDistributionError(f"release receipt is invalid for {target.identifier}")
    artifact_metadata = manifest.get("artifact")
    environment_metadata = manifest.get("build_environment")
    if not isinstance(artifact_metadata, dict) or not isinstance(environment_metadata, dict):
        raise NativeDistributionError(
            f"release receipt lacks asset metadata for {target.identifier}"
        )
    if artifact_metadata.get("path") != artifact.name or artifact_metadata.get("sha256") != _sha256(
        artifact
    ):
        raise NativeDistributionError(f"release receipt artifact mismatch for {target.identifier}")
    if environment_metadata.get("path") != environment.name or environment_metadata.get(
        "sha256"
    ) != _sha256(environment):
        raise NativeDistributionError(
            f"release receipt environment mismatch for {target.identifier}"
        )
    return artifact, environment, manifest


def _retained_non_native_release_assets(release_store: Path) -> list[dict[str, object]]:
    """Keep independently staged release assets such as the Windows MSI."""
    manifest_path = release_store / "release-manifest.json"
    if not manifest_path.is_file():
        return []
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(assets, list):
        raise NativeDistributionError("existing release manifest has invalid assets")
    return [
        asset
        for asset in assets
        if isinstance(asset, dict) and asset.get("target") not in REQUIRED_TARGET_IDS
    ]


def stage_release_assets(targets: tuple[Target, ...]) -> None:
    """Create a versioned, upload-ready release store from smoke-tested assets."""
    release_store = _release_store_directory()
    assets = release_store / "assets"
    if not release_store.is_dir():
        raise NativeDistributionError(
            f"versioned release store is missing: {release_store.relative_to(REPO_ROOT)}"
        )
    assets.mkdir(exist_ok=True)
    release_assets = _retained_non_native_release_assets(release_store)
    for target in targets:
        artifact, environment, manifest = _verified_artifact(target)
        target_assets = assets / target.identifier
        target_assets.mkdir(exist_ok=True)
        for source in (artifact, artifact.with_suffix(artifact.suffix + ".sha256"), environment):
            shutil.copy2(source, target_assets / source.name)
        receipt = target_assets / "build-receipt.json"
        receipt.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifact_metadata = manifest["artifact"]
        assert isinstance(artifact_metadata, dict)
        release_assets.append(
            {
                "target": target.identifier,
                "format": target.package_format,
                "path": f"assets/{target.identifier}/{artifact.name}",
                "sha256": artifact_metadata["sha256"],
                "size_bytes": artifact.stat().st_size,
            }
        )
    release_assets.sort(key=lambda asset: str(asset["target"]))
    aggregate_manifest = {
        "schema_version": 1,
        "bpm_version": TARGET_VERSION,
        "release_tag": f"v{TARGET_VERSION}",
        "source_revision": _source_revision(),
        "publication": {
            "provider": "github-release-assets",
            "repository": "Goudron/browser-policy-manager",
            "release_url": f"https://github.com/Goudron/browser-policy-manager/releases/tag/v{TARGET_VERSION}",
        },
        "assets": release_assets,
    }
    (release_store / "release-manifest.json").write_text(
        json.dumps(aggregate_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    checksums = [
        f"{asset['sha256']}  {Path(str(asset['path'])).name}"
        for asset in release_assets
        if isinstance(asset.get("sha256"), str) and isinstance(asset.get("path"), str)
    ]
    (release_store / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="ascii")
    print(
        f"native release assets staged: {assets.relative_to(REPO_ROOT)} ({len(release_assets)} assets)",
        flush=True,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "smoke", "stage-release", "list"))
    parser.add_argument("--target", default="all", help="target ID or all (default: all)")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        metavar="TARGET=IMAGE",
        help="replace one frozen builder image for a controlled local validation run",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    targets = validate_release_inputs()
    if args.command == "list":
        for target in _targets_for_selection(targets, args.target):
            print(
                f"{target.identifier}\t{target.release}\t{target.package_format}\t{target.artifact}"
            )
        return 0
    if args.command == "validate":
        return 0
    overrides = _image_overrides(args.image)
    for target in _targets_for_selection(targets, args.target):
        image = overrides.get(target.identifier, target.builder_image)
        if args.command == "build":
            build_target(target, image=image)
        elif args.command == "smoke":
            smoke_target(target, image=image)
    if args.command == "stage-release":
        stage_release_assets(_targets_for_selection(targets, args.target))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NativeDistributionError, subprocess.CalledProcessError) as exc:
        print(f"native distribution failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
