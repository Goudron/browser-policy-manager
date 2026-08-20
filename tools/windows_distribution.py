#!/usr/bin/env python3
"""Build, smoke-test, and stage the BPM 0.9.5.1 native Windows x64 MSI.

This tool owns Windows packaging only. It never substitutes WSL for native
Windows, runs only on a Windows x64 host for build or smoke, and keeps MSI
publication separate from evidence generation. The release staging command
accepts an Authenticode-valid MSI only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "distributions" / "windows" / "targets.json"
WINDOWS_ROOT = REPO_ROOT / "distributions" / "windows"
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "windows-packages"
RELEASE_STORE_ROOT = REPO_ROOT / "distributions" / "releases"
TARGET_VERSION = "0.9.5.1"
TARGET_ID = "windows-10-11-x64"
ARCHITECTURE = "x64"


class WindowsDistributionError(RuntimeError):
    """A Windows package release input or target run violates its contract."""


@dataclass(frozen=True)
class WindowsTarget:
    """The one release-owned native Windows MSI target."""

    artifact: str
    product_upgrade_code: str
    python_version: str
    python_installer_url: str
    python_installer_sha256: str
    winsw_version: str
    winsw_url: str
    winsw_sha256: str
    wix_version: str


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


def _require_string(raw: dict[str, Any], key: str, *, location: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise WindowsDistributionError(f"{location}.{key} must be a non-empty string")
    return value


def _require_sha256(value: str, *, location: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise WindowsDistributionError(f"{location} must be a lowercase SHA-256 digest")


def load_target() -> WindowsTarget:
    """Load and validate the frozen Windows MSI manifest."""
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise WindowsDistributionError("Windows target manifest schema_version must be 1")
    if payload.get("target_bpm_version") != TARGET_VERSION:
        raise WindowsDistributionError("Windows target manifest must match BPM 0.9.5.1")
    if payload.get("architecture") != ARCHITECTURE or payload.get("installer_format") != "msi":
        raise WindowsDistributionError("Windows target must be an x64 MSI")
    if payload.get("supported_platforms") != ["Windows 10 x64", "Windows 11 x64"]:
        raise WindowsDistributionError("Windows target must name Windows 10 and 11 x64 explicitly")
    runtime = payload.get("runtime")
    wrapper = payload.get("service_wrapper")
    installer = payload.get("installer")
    wix = payload.get("wix")
    if not all(isinstance(value, dict) for value in (runtime, wrapper, installer, wix)):
        raise WindowsDistributionError("Windows target manifest has incomplete nested metadata")
    assert isinstance(runtime, dict)
    assert isinstance(wrapper, dict)
    assert isinstance(installer, dict)
    assert isinstance(wix, dict)
    target = WindowsTarget(
        artifact=_require_string(installer, "artifact", location="installer"),
        product_upgrade_code=_require_string(
            installer, "product_upgrade_code", location="installer"
        ),
        python_version=_require_string(runtime, "python_version", location="runtime"),
        python_installer_url=_require_string(runtime, "installer_url", location="runtime"),
        python_installer_sha256=_require_string(runtime, "installer_sha256", location="runtime"),
        winsw_version=_require_string(wrapper, "version", location="service_wrapper"),
        winsw_url=_require_string(wrapper, "url", location="service_wrapper"),
        winsw_sha256=_require_string(wrapper, "sha256", location="service_wrapper"),
        wix_version=_require_string(wix, "tool_version", location="wix"),
    )
    if target.python_version != "3.14.6":
        raise WindowsDistributionError("Windows target must pin CPython 3.14.6")
    if target.artifact != "browser-policy-manager-0.9.5.1-windows-x64.msi":
        raise WindowsDistributionError(
            "Windows MSI artifact name is not the BPM 0.9.5.1 release name"
        )
    if not target.python_installer_url.startswith("https://www.python.org/"):
        raise WindowsDistributionError("Windows runtime must come from python.org over HTTPS")
    if not target.winsw_url.startswith("https://github.com/winsw/winsw/"):
        raise WindowsDistributionError(
            "Windows service wrapper must come from the pinned WinSW release"
        )
    _require_sha256(target.python_installer_sha256, location="runtime.installer_sha256")
    _require_sha256(target.winsw_sha256, location="service_wrapper.sha256")
    if installer.get("service_account") != "NT AUTHORITY\\LocalService":
        raise WindowsDistributionError("Windows service must run as LocalService")
    return target


def _documentation_archive() -> tuple[Path, Path]:
    archive = REPO_ROOT / "documentation" / "dist" / f"bpm-documentation-{TARGET_VERSION}.tar.gz"
    return archive, archive.with_suffix(archive.suffix + ".sha256")


def validate_release_inputs() -> WindowsTarget:
    """Fail before any Windows packaging action on incomplete immutable input."""
    target = load_target()
    if _project_version() != TARGET_VERSION:
        raise WindowsDistributionError("pyproject version must match Windows target version")
    archive, checksum = _documentation_archive()
    if not archive.is_file() or not checksum.is_file():
        raise WindowsDistributionError(
            "verified documentation archive is required before Windows packaging"
        )
    expected = f"{_sha256(archive)}  {archive.name}\n"
    if checksum.read_text(encoding="ascii") != expected:
        raise WindowsDistributionError("documentation archive checksum does not match archive")
    required_paths = (
        WINDOWS_ROOT / "Product.wxs",
        WINDOWS_ROOT / "build-msi.ps1",
        WINDOWS_ROOT / "smoke-msi.ps1",
        WINDOWS_ROOT / "requirements.windows.lock",
        WINDOWS_ROOT / "templates" / "bpm.env",
        WINDOWS_ROOT / "templates" / "bpm-migrate.cmd",
        REPO_ROOT / "distributions" / "docker" / "requirements.lock",
        REPO_ROOT / "app" / "static" / "profiles_bundles" / "profiles-bundles-manifest.json",
        REPO_ROOT / "alembic.ini",
        REPO_ROOT / "alembic",
    )
    missing = [
        path.relative_to(REPO_ROOT).as_posix() for path in required_paths if not path.exists()
    ]
    if missing:
        raise WindowsDistributionError(
            "Windows release payload is incomplete: " + ", ".join(missing)
        )
    lock = (WINDOWS_ROOT / "requirements.windows.lock").read_text(encoding="utf-8")
    if "uvloop==" in lock:
        raise WindowsDistributionError("Windows runtime lock must not include unsupported uvloop")
    print(
        "windows release inputs: OK "
        + json.dumps(
            {
                "documentation_sha256": _sha256(archive),
                "target": TARGET_ID,
                "version": TARGET_VERSION,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return target


def _artifact_directory() -> Path:
    return ARTIFACT_ROOT / TARGET_VERSION / TARGET_ID


def _release_store_directory() -> Path:
    return RELEASE_STORE_ROOT / TARGET_VERSION


def _require_windows_host() -> None:
    if os.name != "nt" or not sys.maxsize > 2**32:
        raise WindowsDistributionError(
            "native Windows x64 build and smoke require a Windows x64 host"
        )


def _run_powershell(script: Path, *arguments: str, stage: str) -> None:
    command = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *arguments]
    print(f"[windows-distribution] {stage}: {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def build_target(target: WindowsTarget) -> Path:
    """Build one native Windows MSI and record its signature state as evidence."""
    _require_windows_host()
    output = _artifact_directory()
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / target.artifact
    for path in (
        artifact,
        artifact.with_suffix(artifact.suffix + ".sha256"),
        output / "manifest.json",
        output / "build-environment.json",
        output / "smoke.json",
    ):
        path.unlink(missing_ok=True)
    _run_powershell(
        WINDOWS_ROOT / "build-msi.ps1",
        "-SourceRoot",
        str(REPO_ROOT),
        "-OutputDirectory",
        str(output),
        "-SourceRevision",
        _source_revision(),
        stage="build windows-10-11-x64",
    )
    checksum = artifact.with_suffix(artifact.suffix + ".sha256")
    environment = output / "build-environment.json"
    if not artifact.is_file() or not checksum.is_file() or not environment.is_file():
        raise WindowsDistributionError("Windows builder did not produce complete MSI evidence")
    expected_checksum = f"{_sha256(artifact)}  {artifact.name}\n"
    if checksum.read_text(encoding="ascii") != expected_checksum:
        raise WindowsDistributionError("Windows MSI checksum does not match generated artifact")
    build_environment = json.loads(environment.read_text(encoding="utf-8"))
    signature = build_environment.get("authenticode_status")
    if not isinstance(signature, str):
        raise WindowsDistributionError("Windows builder did not record Authenticode status")
    archive, _ = _documentation_archive()
    manifest = {
        "schema_version": 1,
        "bpm_version": TARGET_VERSION,
        "target": TARGET_ID,
        "target_release": "Windows 10 x64 and Windows 11 x64",
        "architecture": ARCHITECTURE,
        "format": "msi",
        "artifact": {"path": artifact.name, "sha256": _sha256(artifact)},
        "source_revision": _source_revision(),
        "documentation_archive": {"path": archive.name, "sha256": _sha256(archive)},
        "builder": {
            "python_installer_url": target.python_installer_url,
            "python_installer_sha256": target.python_installer_sha256,
            "winsw_version": target.winsw_version,
            "winsw_sha256": target.winsw_sha256,
            "wix_version": target.wix_version,
        },
        "build_environment": {"path": environment.name, "sha256": _sha256(environment)},
        "authenticode": {"status": signature},
        "migration_contract": "explicit-bpm-migrate-only",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Windows MSI built: {artifact.relative_to(REPO_ROOT)} "
        f"sha256={manifest['artifact']['sha256']} authenticode={signature}",
        flush=True,
    )
    return artifact


def smoke_target(target: WindowsTarget) -> None:
    """Clean-install the exact MSI on native Windows and prove lifecycle boundaries."""
    _require_windows_host()
    artifact = _artifact_directory() / target.artifact
    checksum = artifact.with_suffix(artifact.suffix + ".sha256")
    if not artifact.is_file() or not checksum.is_file():
        raise WindowsDistributionError("build the Windows MSI before smoke-testing it")
    if checksum.read_text(encoding="ascii") != f"{_sha256(artifact)}  {artifact.name}\n":
        raise WindowsDistributionError("Windows MSI checksum mismatch before smoke")
    _run_powershell(
        WINDOWS_ROOT / "smoke-msi.ps1",
        "-MsiPath",
        str(artifact),
        stage="smoke windows-10-11-x64",
    )
    artifact = _artifact_directory() / target.artifact
    smoke = {
        "schema_version": 1,
        "target": TARGET_ID,
        "artifact": artifact.name,
        "artifact_sha256": _sha256(artifact),
        "result": "passed",
    }
    (_artifact_directory() / "smoke.json").write_text(
        json.dumps(smoke, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _verified_artifact(target: WindowsTarget) -> tuple[Path, Path, dict[str, object]]:
    output = _artifact_directory()
    artifact = output / target.artifact
    checksum = artifact.with_suffix(artifact.suffix + ".sha256")
    environment = output / "build-environment.json"
    manifest_path = output / "manifest.json"
    smoke_path = output / "smoke.json"
    if not all(
        path.is_file() for path in (artifact, checksum, environment, manifest_path, smoke_path)
    ):
        raise WindowsDistributionError("build and smoke-test the Windows MSI before staging it")
    if checksum.read_text(encoding="ascii") != f"{_sha256(artifact)}  {artifact.name}\n":
        raise WindowsDistributionError("Windows MSI checksum mismatch before staging")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("target") != TARGET_ID:
        raise WindowsDistributionError("Windows release receipt is invalid")
    artifact_metadata = manifest.get("artifact")
    environment_metadata = manifest.get("build_environment")
    signature = manifest.get("authenticode")
    if not all(
        isinstance(value, dict) for value in (artifact_metadata, environment_metadata, signature)
    ):
        raise WindowsDistributionError("Windows release receipt lacks required asset metadata")
    assert isinstance(artifact_metadata, dict)
    assert isinstance(environment_metadata, dict)
    assert isinstance(signature, dict)
    if artifact_metadata.get("path") != artifact.name or artifact_metadata.get("sha256") != _sha256(
        artifact
    ):
        raise WindowsDistributionError("Windows release receipt artifact mismatch")
    if environment_metadata.get("path") != environment.name or environment_metadata.get(
        "sha256"
    ) != _sha256(environment):
        raise WindowsDistributionError("Windows release receipt environment mismatch")
    if signature.get("status") != "Valid":
        raise WindowsDistributionError(
            "only an Authenticode-valid Windows MSI may be staged for release"
        )
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    if not isinstance(smoke, dict) or smoke != {
        "schema_version": 1,
        "target": TARGET_ID,
        "artifact": artifact.name,
        "artifact_sha256": _sha256(artifact),
        "result": "passed",
    }:
        raise WindowsDistributionError("Windows MSI smoke receipt is invalid")
    return artifact, environment, manifest


def _existing_release_assets(release_store: Path) -> list[dict[str, object]]:
    manifest_path = release_store / "release-manifest.json"
    if not manifest_path.is_file():
        return []
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(assets, list):
        raise WindowsDistributionError("existing release manifest has invalid assets")
    return [
        asset for asset in assets if isinstance(asset, dict) and asset.get("target") != TARGET_ID
    ]


def stage_release_assets(target: WindowsTarget) -> None:
    """Add the verified signed MSI to the shared BPM 0.9.5.1 release store."""
    artifact, environment, manifest = _verified_artifact(target)
    release_store = _release_store_directory()
    if not release_store.is_dir():
        raise WindowsDistributionError(
            f"versioned release store is missing: {release_store.relative_to(REPO_ROOT)}"
        )
    asset_directory = release_store / "assets" / TARGET_ID
    asset_directory.mkdir(parents=True, exist_ok=True)
    for source in (
        artifact,
        artifact.with_suffix(artifact.suffix + ".sha256"),
        environment,
        _artifact_directory() / "smoke.json",
    ):
        shutil.copy2(source, asset_directory / source.name)
    (asset_directory / "build-receipt.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    artifact_metadata = manifest["artifact"]
    assert isinstance(artifact_metadata, dict)
    release_assets = _existing_release_assets(release_store)
    release_assets.append(
        {
            "target": TARGET_ID,
            "format": "msi",
            "path": f"assets/{TARGET_ID}/{artifact.name}",
            "sha256": artifact_metadata["sha256"],
            "size_bytes": artifact.stat().st_size,
            "authenticode": "Valid",
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
        f"Windows MSI staged: {asset_directory.relative_to(REPO_ROOT)} "
        f"({len(release_assets)} release assets)",
        flush=True,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "smoke", "stage-release", "list"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = validate_release_inputs()
    if args.command == "list":
        print(f"{TARGET_ID}\tWindows 10 x64 / Windows 11 x64\tmsi\t{target.artifact}")
        return 0
    if args.command == "validate":
        return 0
    if args.command == "build":
        build_target(target)
    elif args.command == "smoke":
        smoke_target(target)
    elif args.command == "stage-release":
        stage_release_assets(target)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (WindowsDistributionError, subprocess.CalledProcessError) as exc:
        print(f"Windows distribution failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
