"""Verified local lifecycle for the fixed ``llama.cpp`` runtime archive.

The archive is retained instead of trusting an extracted directory.  A worker verifies that exact
archive and extracts a minimal private runtime bundle for its own lifetime, so no server binary or
unverified shared object becomes a persistent executable surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tarfile
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from app.core.config import get_settings

RUNTIME_ID = "llama.cpp-b9637-linux-x64-cpu"
RUNTIME_ARCHIVE_FILENAME = "llama-b9637-bin-ubuntu-x64.tar.gz"
RUNTIME_ARCHIVE_SOURCE = (
    "https://github.com/ggml-org/llama.cpp/releases/download/b9637/"
    "llama-b9637-bin-ubuntu-x64.tar.gz"
)
RUNTIME_ARCHIVE_SHA256 = "a50ee14f021a9d8e92e30f622f7e3be1318ee1125bb9a9ba8d2025388df48743"
RUNTIME_ARCHIVE_BYTES = 15_512_345
RUNTIME_REVISION = "aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3"
RUNTIME_LICENSE = "MIT"
RUNTIME_METADATA_FILENAME = "installation.json"


class RuntimeInstallationError(RuntimeError):
    """A stable failure while managing the pinned runtime archive."""


class RuntimeConfirmationRequired(RuntimeInstallationError):
    """A state-changing runtime operation needs explicit confirmation."""


class RuntimeVerificationError(RuntimeInstallationError):
    """The runtime archive or metadata is unsafe or does not match the pin."""


@dataclass(frozen=True)
class RuntimeVerification:
    state: str
    verified: bool
    reason_code: str
    runtime_id: str
    byte_count: int | None = None


@dataclass(frozen=True)
class RuntimeInstallationResult:
    state: str
    runtime_id: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class RuntimeCopyProgress:
    copied_bytes: int
    total_bytes: int


RuntimeProgressCallback = Callable[[RuntimeCopyProgress], None]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _regular_non_symlink(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    except FileNotFoundError:
        return False


def extract_verified_worker_bundle(archive_path: Path, destination: Path) -> Path:
    """Extract only ``llama-cli`` and its shared libraries from the verified archive.

    The worker calls this into a fresh private temporary directory on every start.  Server and RPC
    executables are intentionally not extracted, and all archive paths/links are validated before
    filesystem mutation.
    """

    archive_path = Path(archive_path)
    if (
        not _regular_non_symlink(archive_path)
        or archive_path.stat().st_size != RUNTIME_ARCHIVE_BYTES
        or _sha256(archive_path) != RUNTIME_ARCHIVE_SHA256
    ):
        raise RuntimeVerificationError("runtime_archive_checksum_mismatch")
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    destination.chmod(0o700)
    root = "llama-b9637"
    selected: dict[str, tarfile.TarInfo] = {}
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            for member in archive.getmembers():
                member_path = PurePosixPath(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise RuntimeVerificationError("unsafe_runtime_archive_path")
                if member_path.parts[:1] != (root,) or len(member_path.parts) != 2:
                    continue
                filename = member_path.name
                if filename == "llama-cli" or filename.startswith("lib"):
                    if not (member.isfile() or member.issym()):
                        raise RuntimeVerificationError("unsafe_runtime_archive_member")
                    selected[filename] = member
            if "llama-cli" not in selected:
                raise RuntimeVerificationError("runtime_cli_missing_from_archive")
            for filename, member in selected.items():
                destination_path = destination / filename
                if member.isfile():
                    source = archive.extractfile(member)
                    if source is None:
                        raise RuntimeVerificationError("runtime_archive_member_unreadable")
                    with source, destination_path.open("wb") as output:
                        while block := source.read(1024 * 1024):
                            output.write(block)
                    destination_path.chmod(0o700 if filename == "llama-cli" else 0o600)
                    continue
                target = PurePosixPath(member.linkname)
                if (
                    target.is_absolute()
                    or ".." in target.parts
                    or len(target.parts) != 1
                    or target.name not in selected
                ):
                    raise RuntimeVerificationError("unsafe_runtime_archive_link")
                destination_path.symlink_to(target.name)
    except OSError as error:
        raise RuntimeVerificationError("runtime_bundle_extraction_failed") from error
    except tarfile.TarError as error:
        raise RuntimeVerificationError("runtime_bundle_extraction_failed") from error
    executable = destination / "llama-cli"
    if not _regular_non_symlink(executable) or not os.access(executable, os.X_OK):
        raise RuntimeVerificationError("runtime_cli_extraction_failed")
    return executable


class RuntimeInstaller:
    """Manage one archive below the fixed BPM local-AI runtime root."""

    def __init__(self, runtime_root: Path) -> None:
        self._runtime_root = Path(runtime_root)

    @property
    def bundle_dir(self) -> Path:
        return self._runtime_root / RUNTIME_ID

    @property
    def archive_path(self) -> Path:
        return self.bundle_dir / RUNTIME_ARCHIVE_FILENAME

    @property
    def metadata_path(self) -> Path:
        return self.bundle_dir / RUNTIME_METADATA_FILENAME

    @property
    def _staging_dir(self) -> Path:
        return self._runtime_root / ".staging" / RUNTIME_ID

    def verify(self) -> RuntimeVerification:
        """Verify without extraction, execution, network access, or file creation."""

        if self.bundle_dir.is_symlink():
            return self._invalid("unsafe_runtime_directory")
        if not self.bundle_dir.exists():
            return RuntimeVerification("not-installed", False, "runtime_missing", RUNTIME_ID)
        if not self.bundle_dir.is_dir():
            return self._invalid("unsafe_runtime_directory")
        if not _regular_non_symlink(self.archive_path):
            return self._invalid("unsafe_or_missing_runtime_archive")
        if not _regular_non_symlink(self.metadata_path):
            return self._invalid("unsafe_or_missing_runtime_metadata")
        try:
            byte_count = self.archive_path.stat().st_size
        except OSError:
            return self._invalid("runtime_archive_stat_failed")
        if byte_count != RUNTIME_ARCHIVE_BYTES:
            return self._invalid("runtime_archive_size_mismatch", byte_count)
        if _sha256(self.archive_path) != RUNTIME_ARCHIVE_SHA256:
            return self._invalid("runtime_archive_checksum_mismatch", byte_count)
        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except OSError:
            return self._invalid("runtime_metadata_unreadable", byte_count)
        except UnicodeDecodeError:
            return self._invalid("runtime_metadata_unreadable", byte_count)
        except json.JSONDecodeError:
            return self._invalid("runtime_metadata_unreadable", byte_count)
        if not isinstance(metadata, dict) or any(
            metadata.get(key) != value
            for key, value in self._metadata().items()
            if key != "installed_at"
        ):
            return self._invalid("runtime_metadata_mismatch", byte_count)
        return RuntimeVerification("installed", True, "verified", RUNTIME_ID, byte_count)

    def install_local(
        self,
        source_archive: Path,
        *,
        confirmed: bool,
        progress: RuntimeProgressCallback | None = None,
    ) -> RuntimeInstallationResult:
        """Copy a user-selected archive only after exact source validation and consent."""

        if not confirmed:
            raise RuntimeConfirmationRequired("explicit_confirmation_required")
        self._ensure_root()
        current = self.verify()
        if current.verified:
            return RuntimeInstallationResult(
                "already-installed", RUNTIME_ID, RUNTIME_ARCHIVE_BYTES, RUNTIME_ARCHIVE_SHA256
            )
        source_archive = Path(source_archive)
        if not _regular_non_symlink(source_archive):
            raise RuntimeVerificationError("unsafe_local_runtime_archive")
        if source_archive.stat().st_size != RUNTIME_ARCHIVE_BYTES:
            raise RuntimeVerificationError("runtime_archive_size_mismatch")
        if _sha256(source_archive) != RUNTIME_ARCHIVE_SHA256:
            raise RuntimeVerificationError("runtime_archive_checksum_mismatch")
        self._prepare_staging()
        staging_archive = self._staging_dir / RUNTIME_ARCHIVE_FILENAME
        self._copy(source_archive, staging_archive, progress)
        if (
            staging_archive.stat().st_size != RUNTIME_ARCHIVE_BYTES
            or _sha256(staging_archive) != RUNTIME_ARCHIVE_SHA256
        ):
            raise RuntimeVerificationError("runtime_archive_copy_verification_failed")
        self._write_metadata(self._staging_dir / RUNTIME_METADATA_FILENAME)
        if self.bundle_dir.exists() or self.bundle_dir.is_symlink():
            raise RuntimeVerificationError("existing_runtime_bundle_requires_explicit_removal")
        os.replace(self._staging_dir, self.bundle_dir)
        self._staging_dir.mkdir(mode=0o700, exist_ok=True)
        verified = self.verify()
        if not verified.verified:
            raise RuntimeVerificationError(verified.reason_code)
        return RuntimeInstallationResult(
            "installed", RUNTIME_ID, RUNTIME_ARCHIVE_BYTES, RUNTIME_ARCHIVE_SHA256
        )

    def remove(self, *, confirmed: bool) -> RuntimeInstallationResult:
        """Remove only the fixed runtime bundle after separate explicit confirmation."""

        if not confirmed:
            raise RuntimeConfirmationRequired("explicit_confirmation_required")
        self._ensure_root()
        if self.bundle_dir.exists() or self.bundle_dir.is_symlink():
            self._remove_tree(self.bundle_dir)
            state = "removed"
        else:
            state = "not-installed"
        return RuntimeInstallationResult(state, RUNTIME_ID, 0, RUNTIME_ARCHIVE_SHA256)

    def _invalid(self, reason_code: str, byte_count: int | None = None) -> RuntimeVerification:
        return RuntimeVerification("incompatible", False, reason_code, RUNTIME_ID, byte_count)

    def _metadata(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "runtime_id": RUNTIME_ID,
            "revision": RUNTIME_REVISION,
            "license": RUNTIME_LICENSE,
            "archive_filename": RUNTIME_ARCHIVE_FILENAME,
            "archive_source": RUNTIME_ARCHIVE_SOURCE,
            "archive_sha256": RUNTIME_ARCHIVE_SHA256,
            "archive_byte_count": RUNTIME_ARCHIVE_BYTES,
        }

    def _ensure_root(self) -> None:
        if self._runtime_root.is_symlink() or (
            self._runtime_root.exists() and not self._runtime_root.is_dir()
        ):
            raise RuntimeInstallationError("unsafe_runtime_root")
        self._runtime_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._runtime_root.chmod(0o700)
        staging_root = self._runtime_root / ".staging"
        if staging_root.is_symlink() or (staging_root.exists() and not staging_root.is_dir()):
            raise RuntimeInstallationError("unsafe_runtime_staging_root")
        staging_root.mkdir(mode=0o700, exist_ok=True)
        staging_root.chmod(0o700)

    def _prepare_staging(self) -> None:
        if self._staging_dir.is_symlink() or (
            self._staging_dir.exists() and not self._staging_dir.is_dir()
        ):
            raise RuntimeInstallationError("unsafe_runtime_staging_directory")
        self._staging_dir.mkdir(mode=0o700, exist_ok=True)
        self._staging_dir.chmod(0o700)

    def _copy(
        self, source_archive: Path, destination: Path, progress: RuntimeProgressCallback | None
    ) -> None:
        copied = 0
        if progress is not None:
            progress(RuntimeCopyProgress(copied, RUNTIME_ARCHIVE_BYTES))
        with source_archive.open("rb") as source, destination.open("wb") as output:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                output.write(block)
                copied += len(block)
                if progress is not None:
                    progress(RuntimeCopyProgress(copied, RUNTIME_ARCHIVE_BYTES))
            output.flush()
            os.fsync(output.fileno())
        destination.chmod(0o600)

    def _write_metadata(self, destination: Path) -> None:
        payload = self._metadata() | {
            "installed_at": datetime.now(UTC).replace(microsecond=0).isoformat()
        }
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        os.replace(temporary, destination)

    def _remove_tree(self, target: Path) -> None:
        if target.is_symlink():
            raise RuntimeVerificationError("refusing_to_remove_runtime_symlink")
        if target.is_file():
            if not _regular_non_symlink(target):
                raise RuntimeVerificationError("unsafe_runtime_file_for_removal")
            target.unlink()
            return
        if not target.is_dir():
            raise RuntimeVerificationError("unsafe_runtime_path_for_removal")
        for child in target.iterdir():
            self._remove_tree(child)
        target.rmdir()


def _progress() -> RuntimeProgressCallback:
    last_percent = -1

    def write(item: RuntimeCopyProgress) -> None:
        nonlocal last_percent
        percent = int(item.copied_bytes * 100 / item.total_bytes)
        if (percent == 0 and last_percent < 0) or percent == 100 or percent >= last_percent + 5:
            print(
                f"M6-06: runtime install {percent}% ({item.copied_bytes}/{item.total_bytes} bytes)",
                flush=True,
            )
            last_percent = percent

    return write


def _result(result: RuntimeInstallationResult | RuntimeVerification) -> str:
    return json.dumps(asdict(result), sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage BPM's verified local llama.cpp runtime archive."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify", help="verify without extracting or executing the runtime")
    install = commands.add_parser("install-local", help="copy a pre-verified local runtime archive")
    install.add_argument("--archive", type=Path, required=True)
    install.add_argument("--confirm", action="store_true")
    remove = commands.add_parser("remove", help="remove the exact owned runtime archive")
    remove.add_argument("--confirm", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    installer = RuntimeInstaller(get_settings().DATA_DIR / "ai" / "runtime")
    try:
        if args.command == "verify":
            verification = installer.verify()
            print(_result(verification))
            return 0 if verification.verified else 1
        if args.command == "install-local":
            installation = installer.install_local(
                args.archive, confirmed=args.confirm, progress=_progress()
            )
            print(_result(installation))
            return 0
        if args.command == "remove":
            removal = installer.remove(confirmed=args.confirm)
            print(_result(removal))
            return 0
    except RuntimeInstallationError as error:
        print(json.dumps({"state": "failed", "reason_code": str(error)}), file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
