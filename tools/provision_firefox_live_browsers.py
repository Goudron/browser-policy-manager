#!/usr/bin/env python3
"""Provision immutable, checksum-verified Firefox live-test installations.

The cache stores only archives whose digest is rechecked before every reuse.
Each channel is extracted to a separate immutable installation.  Test code must
clone that installation before it writes ``distribution/policies.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "tools" / "firefox_live_browsers_manifest_0_9_4.json"
DEFAULT_ROOT = REPO_ROOT / ".bpm-test-browsers"
CHUNK_SIZE = 1024 * 1024
PROGRESS_INTERVAL = 8 * CHUNK_SIZE


class ProvisioningError(RuntimeError):
    """A manifest, download, or installation failed verification."""


@dataclass(frozen=True)
class ArchiveSpec:
    label: str
    version: str
    url: str
    sha256: str
    archive: str


@dataclass(frozen=True)
class ProvisionSpec:
    channel: str
    platform: str
    firefox: ArchiveSpec
    geckodriver: ArchiveSpec

    @property
    def installation_id(self) -> str:
        return f"{self.channel}-{self.firefox.version}"


def _progress(message: str) -> None:
    print(message, flush=True)


def host_platform() -> str:
    if sys.platform.startswith("linux") and platform.machine().lower() in {"x86_64", "amd64"}:
        return "linux-x86_64"
    raise ProvisioningError(
        f"Unsupported host platform {sys.platform!r}/{platform.machine()!r}; "
        "the pinned live-browser manifest currently supports linux-x86_64."
    )


def _required_string(payload: dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ProvisioningError(f"{context} requires non-empty string {key!r}")
    return value


def _archive_spec(label: str, payload: dict[str, Any], context: str) -> ArchiveSpec:
    digest = _required_string(payload, "sha256", context)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ProvisioningError(f"{context} has invalid sha256 digest")
    return ArchiveSpec(
        label=label,
        version=_required_string(payload, "version", context),
        url=_required_string(payload, "url", context),
        sha256=digest,
        archive=_required_string(payload, "archive", context),
    )


def load_spec(manifest_path: Path, *, channel: str, platform_name: str) -> ProvisionSpec:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProvisioningError(
            f"Cannot read provisioning manifest {manifest_path}: {error}"
        ) from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ProvisioningError("Firefox provisioning manifest requires schema_version 1")
    platforms = payload.get("platforms")
    if not isinstance(platforms, dict) or not isinstance(platforms.get(platform_name), dict):
        raise ProvisioningError(f"Manifest has no platform entry for {platform_name!r}")
    platform_payload = platforms[platform_name]
    firefox_entries = platform_payload.get("firefox")
    if not isinstance(firefox_entries, dict) or not isinstance(firefox_entries.get(channel), dict):
        supported = sorted(firefox_entries) if isinstance(firefox_entries, dict) else []
        raise ProvisioningError(
            f"Unsupported Firefox channel {channel!r}; supported: {', '.join(supported)}"
        )
    geckodriver_payload = platform_payload.get("geckodriver")
    if not isinstance(geckodriver_payload, dict):
        raise ProvisioningError(f"Manifest platform {platform_name!r} has no geckodriver entry")
    return ProvisionSpec(
        channel=channel,
        platform=platform_name,
        firefox=_archive_spec("Firefox", firefox_entries[channel], f"firefox.{channel}"),
        geckodriver=_archive_spec("geckodriver", geckodriver_payload, "geckodriver"),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_archive_path(root: Path, spec: ArchiveSpec) -> Path:
    return root / "cache" / "sha256" / spec.sha256 / spec.archive


def _verify_archive(path: Path, spec: ArchiveSpec) -> None:
    actual = sha256_file(path)
    if actual != spec.sha256:
        raise ProvisioningError(
            f"Checksum mismatch for {spec.label} archive {path}: expected {spec.sha256}, got {actual}"
        )


def _download_verified_archive(root: Path, spec: ArchiveSpec) -> Path:
    cache_path = _verified_archive_path(root, spec)
    if cache_path.is_file():
        try:
            _verify_archive(cache_path, spec)
        except ProvisioningError:
            _progress(f"Discarding corrupt cached {spec.label} archive: {cache_path}")
            cache_path.unlink()
        else:
            _progress(f"Reusing checksum-verified {spec.label} archive: {cache_path}")
            return cache_path

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache_path.with_name(f".{cache_path.name}.{os.getpid()}.part")
    with tempfile.NamedTemporaryFile(
        dir=cache_path.parent, prefix=temporary.name, delete=False
    ) as stream:
        temporary = Path(stream.name)
        downloaded = 0
        reported_at = 0
        started_at = time.monotonic()
        _progress(f"Downloading {spec.label} {spec.version} from {spec.url}")
        try:
            with urlopen(spec.url, timeout=120) as response:  # nosec B310: URL is manifest-pinned
                content_length = response.headers.get("Content-Length")
                total = int(content_length) if content_length and content_length.isdigit() else None
                while chunk := response.read(CHUNK_SIZE):
                    stream.write(chunk)
                    downloaded += len(chunk)
                    if downloaded - reported_at >= PROGRESS_INTERVAL:
                        suffix = f" of {total}" if total is not None else ""
                        _progress(f"  downloaded {downloaded}{suffix} bytes")
                        reported_at = downloaded
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    elapsed = time.monotonic() - started_at
    _progress(f"  downloaded {downloaded} bytes in {elapsed:.1f}s; verifying SHA-256")
    try:
        _verify_archive(temporary, spec)
        os.replace(temporary, cache_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    _progress(f"Verified {spec.label} SHA-256: {spec.sha256}")
    return cache_path


def _extract_archive(archive_path: Path, *, target: Path, mode: str) -> None:
    with tarfile.open(archive_path, mode) as archive:
        archive.extractall(target, filter="data")


def _binary_version(binary: Path, expected: str, label: str) -> str:
    import subprocess

    completed = subprocess.run(
        [str(binary), "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    actual = (
        (completed.stdout or completed.stderr).strip().splitlines()[0]
        if (completed.stdout or completed.stderr).strip()
        else "<no version output>"
    )
    if completed.returncode != 0 or expected not in actual:
        raise ProvisioningError(f"{label} version mismatch: expected {expected!r}, got {actual!r}")
    return actual


def installation_root(root: Path, spec: ProvisionSpec) -> Path:
    return root / "installs" / spec.platform / spec.installation_id


def _provenance_payload(
    spec: ProvisionSpec, *, firefox_actual: str, geckodriver_actual: str
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "channel": spec.channel,
        "platform": spec.platform,
        "policy_root_mode": "clone-per-test-run",
        "firefox": {
            "version": spec.firefox.version,
            "url": spec.firefox.url,
            "sha256": spec.firefox.sha256,
            "actual_version": firefox_actual,
        },
        "geckodriver": {
            "version": spec.geckodriver.version,
            "url": spec.geckodriver.url,
            "sha256": spec.geckodriver.sha256,
            "actual_version": geckodriver_actual,
        },
    }


def _make_read_only(root: Path) -> None:
    paths = sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True)
    for path in paths:
        current = path.stat().st_mode
        if path.is_dir():
            path.chmod(0o555)
        else:
            path.chmod(0o555 if current & stat.S_IXUSR else 0o444)
    root.chmod(0o555)


def _remove_immutable_tree(root: Path) -> None:
    """Remove a previously verified read-only installation during --force."""

    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        path.chmod(path.stat().st_mode | stat.S_IWUSR)
    root.chmod(root.stat().st_mode | stat.S_IWUSR)
    shutil.rmtree(root)


def verify_installation(root: Path, spec: ProvisionSpec) -> dict[str, Any]:
    install_root = installation_root(root, spec)
    provenance_path = install_root / "installation.json"
    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProvisioningError(
            f"No verified installation for {spec.installation_id}: {error}"
        ) from error
    expected = _provenance_payload(
        spec,
        firefox_actual=provenance.get("firefox", {}).get("actual_version", ""),
        geckodriver_actual=provenance.get("geckodriver", {}).get("actual_version", ""),
    )
    if provenance != expected:
        raise ProvisioningError(
            f"Installation provenance is not the pinned manifest for {spec.installation_id}"
        )
    firefox_actual = _binary_version(
        install_root / "firefox" / "firefox", spec.firefox.version, "Firefox"
    )
    geckodriver_actual = _binary_version(
        install_root / "geckodriver" / "geckodriver", spec.geckodriver.version, "geckodriver"
    )
    if firefox_actual != provenance["firefox"]["actual_version"]:
        raise ProvisioningError("Installed Firefox version changed after verification")
    if geckodriver_actual != provenance["geckodriver"]["actual_version"]:
        raise ProvisioningError("Installed geckodriver version changed after verification")
    return provenance


def provision(
    root: Path, spec: ProvisionSpec, *, force: bool = False
) -> tuple[Path, dict[str, Any]]:
    target = installation_root(root, spec)
    if target.exists() and not force:
        provenance = verify_installation(root, spec)
        _progress(f"Reusing verified isolated installation: {target}")
        return target, provenance

    firefox_archive = _download_verified_archive(root, spec.firefox)
    geckodriver_archive = _download_verified_archive(root, spec.geckodriver)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{spec.installation_id}.staging-", dir=target.parent))
    try:
        _progress(f"Extracting verified Firefox into isolated staging: {staging}")
        _extract_archive(firefox_archive, target=staging, mode="r:xz")
        _progress("Extracting verified geckodriver into isolated staging")
        (staging / "geckodriver").mkdir()
        _extract_archive(geckodriver_archive, target=staging / "geckodriver", mode="r:gz")
        firefox_actual = _binary_version(
            staging / "firefox" / "firefox", spec.firefox.version, "Firefox"
        )
        geckodriver_actual = _binary_version(
            staging / "geckodriver" / "geckodriver", spec.geckodriver.version, "geckodriver"
        )
        provenance = _provenance_payload(
            spec, firefox_actual=firefox_actual, geckodriver_actual=geckodriver_actual
        )
        (staging / "installation.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _make_read_only(staging)
        backup = target.with_name(f".{target.name}.previous-{os.getpid()}")
        if backup.exists():
            _remove_immutable_tree(backup)
        if target.exists():
            os.replace(target, backup)
        try:
            os.replace(staging, target)
        except Exception:
            if backup.exists():
                os.replace(backup, target)
            raise
        if backup.exists():
            _remove_immutable_tree(backup)
    except Exception:
        if staging.exists():
            _remove_immutable_tree(staging)
        raise
    _progress(f"Installed verified Firefox pair atomically: {target}")
    return target, provenance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("channel", nargs="?", default="release", help="release, esr153, or esr140")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--platform", dest="platform_name", default=None)
    parser.add_argument(
        "--verify", action="store_true", help="verify an existing isolated installation only"
    )
    parser.add_argument(
        "--force", action="store_true", help="replace an existing verified installation"
    )
    parser.add_argument(
        "--json", action="store_true", help="print the verified installation provenance as JSON"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        spec = load_spec(
            args.manifest.resolve(),
            channel=args.channel,
            platform_name=args.platform_name or host_platform(),
        )
        root = args.root.resolve()
        if args.verify:
            provenance = verify_installation(root, spec)
            target = installation_root(root, spec)
            _progress(f"Verified isolated installation: {target}")
        else:
            target, provenance = provision(root, spec, force=args.force)
        _progress(f"Firefox: {provenance['firefox']['actual_version']}")
        _progress(f"geckodriver: {provenance['geckodriver']['actual_version']}")
        _progress("Policy roots: cloned per test run; cached installations remain immutable.")
        if args.json:
            print(
                json.dumps({"installation": str(target), **provenance}, sort_keys=True), flush=True
            )
    except ProvisioningError as error:
        print(f"Firefox provisioning failed: {error}", file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
