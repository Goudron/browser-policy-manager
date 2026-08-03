"""Explicit installation lifecycle for the single approved local chat model.

This module deliberately has no HTTP route and never starts an inference process.
M6-05 owns only the opt-in, checksum-verified local artifact lifecycle.  The
bounded worker and browser-facing chat surface remain work for later backlog
items.
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
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from app.core.config import get_settings
from app.core.locales import ACTIVE_CATALOG_LOCALES

MODEL_ID = "qwen3-0.6b-q8_0-official-gguf"
ARTIFACT_FILENAME = "Qwen3-0.6B-Q8_0.gguf"
ARTIFACT_SOURCE = (
    "https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/"
    "23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf"
)
ARTIFACT_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
ARTIFACT_BYTES = 639_446_688
ARTIFACT_LICENSE = "Apache-2.0"
ARTIFACT_UPSTREAM = "Qwen / Qwen3-0.6B-GGUF"
METADATA_FILENAME = "installation.json"
SUPPORTED_ARCHITECTURES = frozenset({"x86_64", "amd64"})


class ModelInstallationError(RuntimeError):
    """A safe, stable failure while handling the selected model artifact."""


class ExplicitConfirmationRequired(ModelInstallationError):
    """Raised when a state-changing action lacks an explicit confirmation."""


class ArtifactVerificationError(ModelInstallationError):
    """Raised when an artifact does not match the selected immutable manifest."""


class ArtifactCompatibilityError(ModelInstallationError):
    """Raised when the selected artifact cannot run on the host profile."""


class InstallationBusyError(ModelInstallationError):
    """Raised when another explicit install or removal is already active."""


class InstallationCancelled(ModelInstallationError):
    """Raised when the owner explicitly stops an in-progress artifact operation."""


@dataclass(frozen=True)
class ModelArtifact:
    """Immutable provenance and integrity data for the only installable model."""

    model_id: str
    filename: str
    source: str
    sha256: str
    byte_count: int
    license_spdx: str
    upstream: str
    source_revision: str
    target_architectures: tuple[str, ...]


SELECTED_ARTIFACT = ModelArtifact(
    model_id=MODEL_ID,
    filename=ARTIFACT_FILENAME,
    source=ARTIFACT_SOURCE,
    sha256=ARTIFACT_SHA256,
    byte_count=ARTIFACT_BYTES,
    license_spdx=ARTIFACT_LICENSE,
    upstream=ARTIFACT_UPSTREAM,
    source_revision="23749fefcc72300e3a2ad315e1317431b06b590a",
    target_architectures=("x86_64",),
)


@dataclass(frozen=True)
class VerificationResult:
    """Non-sensitive inspection result for the selected local artifact."""

    state: str
    verified: bool
    reason_code: str
    model_id: str
    byte_count: int | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class InstallationResult:
    """Result of an explicit install or removal action."""

    state: str
    model_id: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class DownloadProgress:
    """Bounded progress data suitable for a local CLI or future UI."""

    downloaded_bytes: int
    total_bytes: int


ProgressCallback = Callable[[DownloadProgress], None]
CancellationCallback = Callable[[], bool]
ClientFactory = Callable[[], httpx.Client]


DISCLOSURES: dict[str, dict[str, str]] = {
    "en": {
        "summary": "Local chat is optional and runs on this computer's CPU. No fixed response-time SLA is promised.",
        "action": "Installation downloads only the selected, checksum-verified local model after explicit confirmation.",
    },
    "ru": {
        "summary": "Локальный чат необязателен и работает на процессоре этого компьютера. Фиксированное время ответа не гарантируется.",
        "action": "Установка загружает только выбранную локальную модель с проверкой контрольной суммы после явного подтверждения.",
    },
    "de": {
        "summary": "Der lokale Chat ist optional und läuft auf der CPU dieses Computers. Eine feste Antwortzeit wird nicht zugesagt.",
        "action": "Die Installation lädt nur das ausgewählte lokale Modell nach ausdrücklicher Bestätigung und Prüfsummenprüfung herunter.",
    },
    "zh-CN": {
        "summary": "本地聊天为可选功能，使用此计算机的 CPU 运行；不保证固定响应时间。",
        "action": "安装仅会在明确确认后下载已选定且经过校验和验证的本地模型。",
    },
    "fr": {
        "summary": "Le chat local est facultatif et utilise le processeur de cet ordinateur. Aucun délai de réponse fixe n'est garanti.",
        "action": "L'installation ne télécharge le modèle local sélectionné et vérifié par somme de contrôle qu'après confirmation explicite.",
    },
    "es-ES": {
        "summary": "El chat local es opcional y se ejecuta en la CPU de este equipo. No se garantiza un tiempo de respuesta fijo.",
        "action": "La instalación descarga únicamente el modelo local seleccionado y verificado mediante suma de comprobación tras una confirmación explícita.",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact_file:
        for block in iter(lambda: artifact_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_regular_non_symlink(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return False
    return stat.S_ISREG(mode) and not stat.S_ISLNK(mode)


def _machine_architecture() -> str:
    return platform.machine().strip().lower()


def _raise_if_cancelled(cancelled: CancellationCallback | None) -> None:
    if cancelled is not None and cancelled():
        raise InstallationCancelled("installation_cancelled")


class ModelInstaller:
    """Manage only the manifest-owned selected artifact under a fixed store root."""

    def __init__(
        self,
        store_dir: Path,
        *,
        client_factory: ClientFactory | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._store_dir = Path(store_dir)
        self._client_factory = client_factory
        self._timeout_seconds = timeout_seconds

    @property
    def model_dir(self) -> Path:
        return self._store_dir / SELECTED_ARTIFACT.model_id

    @property
    def artifact_path(self) -> Path:
        return self.model_dir / SELECTED_ARTIFACT.filename

    @property
    def metadata_path(self) -> Path:
        return self.model_dir / METADATA_FILENAME

    @property
    def _staging_dir(self) -> Path:
        return self._store_dir / ".staging" / SELECTED_ARTIFACT.model_id

    @property
    def _quarantine_dir(self) -> Path:
        return self._store_dir / ".quarantine" / SELECTED_ARTIFACT.model_id

    @property
    def _lock_path(self) -> Path:
        return self._store_dir / ".model-install.lock"

    def disclosure(self, locale: str) -> dict[str, Any]:
        """Return the localized, inspectable consent information without I/O."""

        if locale not in ACTIVE_CATALOG_LOCALES:
            raise ModelInstallationError("unsupported_locale")
        return {
            "locale": locale,
            "model_id": SELECTED_ARTIFACT.model_id,
            "upstream": SELECTED_ARTIFACT.upstream,
            "source": SELECTED_ARTIFACT.source,
            "source_revision": SELECTED_ARTIFACT.source_revision,
            "license": SELECTED_ARTIFACT.license_spdx,
            "filename": SELECTED_ARTIFACT.filename,
            "byte_count": SELECTED_ARTIFACT.byte_count,
            "sha256": SELECTED_ARTIFACT.sha256,
            "summary": DISCLOSURES[locale]["summary"],
            "action": DISCLOSURES[locale]["action"],
        }

    def verify(self) -> VerificationResult:
        """Verify an installed artifact without downloading, executing, or creating files."""

        if _machine_architecture() not in SUPPORTED_ARCHITECTURES:
            return VerificationResult(
                state="incompatible",
                verified=False,
                reason_code="unsupported_architecture",
                model_id=SELECTED_ARTIFACT.model_id,
            )
        if self.model_dir.is_symlink():
            return self._invalid("unsafe_model_directory")
        if not self.model_dir.exists():
            return VerificationResult(
                state="not-installed",
                verified=False,
                reason_code="artifact_missing",
                model_id=SELECTED_ARTIFACT.model_id,
            )
        if not self.model_dir.is_dir():
            return self._invalid("unsafe_model_directory")
        if not _is_regular_non_symlink(self.artifact_path):
            return self._invalid("unsafe_or_missing_artifact")
        if not _is_regular_non_symlink(self.metadata_path):
            return self._invalid("unsafe_or_missing_metadata")
        try:
            actual_size = self.artifact_path.stat().st_size
        except OSError:
            return self._invalid("artifact_stat_failed")
        if actual_size != SELECTED_ARTIFACT.byte_count:
            return self._invalid("artifact_size_mismatch", actual_size)
        if _sha256(self.artifact_path) != SELECTED_ARTIFACT.sha256:
            return self._invalid("artifact_checksum_mismatch", actual_size)
        try:
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except OSError:
            return self._invalid("metadata_unreadable", actual_size)
        except UnicodeDecodeError:
            return self._invalid("metadata_unreadable", actual_size)
        except json.JSONDecodeError:
            return self._invalid("metadata_unreadable", actual_size)
        if not self._metadata_matches(metadata):
            return self._invalid("metadata_mismatch", actual_size)
        return VerificationResult(
            state="installed",
            verified=True,
            reason_code="verified",
            model_id=SELECTED_ARTIFACT.model_id,
            byte_count=actual_size,
            sha256=SELECTED_ARTIFACT.sha256,
        )

    def install(
        self,
        *,
        confirmed: bool,
        progress: ProgressCallback | None = None,
        cancelled: CancellationCallback | None = None,
    ) -> InstallationResult:
        """Download, verify and atomically promote the selected artifact after consent."""

        if not confirmed:
            raise ExplicitConfirmationRequired("explicit_confirmation_required")
        _raise_if_cancelled(cancelled)
        self._assert_compatible_host()
        self._ensure_store()
        with self._exclusive_operation():
            current = self.verify()
            if current.verified:
                return InstallationResult(
                    state="already-installed",
                    model_id=SELECTED_ARTIFACT.model_id,
                    byte_count=SELECTED_ARTIFACT.byte_count,
                    sha256=SELECTED_ARTIFACT.sha256,
                )
            self._ensure_disk_capacity()
            self._prepare_staging()
            part_path = self._staging_dir / f"{SELECTED_ARTIFACT.filename}.part"
            self._download(part_path, progress, cancelled)
            _raise_if_cancelled(cancelled)
            self._verify_download(part_path)
            self._write_metadata(self._staging_dir / METADATA_FILENAME)
            self._promote_staging()
            return self._verified_installation_result()

    def install_local(
        self,
        source_path: Path,
        *,
        confirmed: bool,
        progress: ProgressCallback | None = None,
        cancelled: CancellationCallback | None = None,
    ) -> InstallationResult:
        """Explicitly copy one local candidate into the verified artifact store.

        This is the offline path for a pre-obtained artifact. The user-supplied
        source is treated as untrusted input: it must be a direct regular file,
        has no authority to choose the destination, and is verified before it
        can be promoted.
        """

        if not confirmed:
            raise ExplicitConfirmationRequired("explicit_confirmation_required")
        _raise_if_cancelled(cancelled)
        source_path = Path(source_path)
        if not _is_regular_non_symlink(source_path):
            raise ArtifactVerificationError("unsafe_local_artifact_source")
        self._assert_compatible_host()
        self._ensure_store()
        with self._exclusive_operation():
            current = self.verify()
            if current.verified:
                return InstallationResult(
                    state="already-installed",
                    model_id=SELECTED_ARTIFACT.model_id,
                    byte_count=SELECTED_ARTIFACT.byte_count,
                    sha256=SELECTED_ARTIFACT.sha256,
                )
            if source_path.stat().st_size != SELECTED_ARTIFACT.byte_count:
                raise ArtifactVerificationError("local_artifact_size_mismatch")
            self._ensure_disk_capacity()
            self._prepare_staging()
            part_path = self._staging_dir / f"{SELECTED_ARTIFACT.filename}.part"
            self._copy_local_artifact(source_path, part_path, progress, cancelled)
            _raise_if_cancelled(cancelled)
            self._verify_download(part_path)
            self._write_metadata(self._staging_dir / METADATA_FILENAME)
            self._promote_staging()
            return self._verified_installation_result()

    def remove(self, *, confirmed: bool) -> InstallationResult:
        """Remove only this manifest-owned model, staging state and quarantine state."""

        if not confirmed:
            raise ExplicitConfirmationRequired("explicit_confirmation_required")
        self._ensure_store()
        with self._exclusive_operation():
            removed_any = False
            for target in (self.model_dir, self._staging_dir, self._quarantine_dir):
                if target.exists() or target.is_symlink():
                    self._safe_remove_tree(target)
                    removed_any = True
            return InstallationResult(
                state="removed" if removed_any else "not-installed",
                model_id=SELECTED_ARTIFACT.model_id,
                byte_count=0,
                sha256=SELECTED_ARTIFACT.sha256,
            )

    def _invalid(self, reason_code: str, byte_count: int | None = None) -> VerificationResult:
        return VerificationResult(
            state="incompatible",
            verified=False,
            reason_code=reason_code,
            model_id=SELECTED_ARTIFACT.model_id,
            byte_count=byte_count,
        )

    def _metadata_matches(self, metadata: object) -> bool:
        if not isinstance(metadata, dict):
            return False
        expected = self._metadata_payload()
        return all(
            metadata.get(key) == value for key, value in expected.items() if key != "installed_at"
        )

    def _metadata_payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "model_id": SELECTED_ARTIFACT.model_id,
            "filename": SELECTED_ARTIFACT.filename,
            "source": SELECTED_ARTIFACT.source,
            "source_revision": SELECTED_ARTIFACT.source_revision,
            "sha256": SELECTED_ARTIFACT.sha256,
            "byte_count": SELECTED_ARTIFACT.byte_count,
            "license": SELECTED_ARTIFACT.license_spdx,
            "target_architectures": list(SELECTED_ARTIFACT.target_architectures),
        }

    def _assert_compatible_host(self) -> None:
        if _machine_architecture() not in SUPPORTED_ARCHITECTURES:
            raise ArtifactCompatibilityError("unsupported_architecture")

    def _ensure_store(self) -> None:
        if self._store_dir.is_symlink() or (
            self._store_dir.exists() and not self._store_dir.is_dir()
        ):
            raise ModelInstallationError("unsafe_store_directory")
        self._store_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._store_dir.chmod(0o700)
        for child in (self._store_dir / ".staging", self._store_dir / ".quarantine"):
            if child.is_symlink() or (child.exists() and not child.is_dir()):
                raise ModelInstallationError("unsafe_store_subdirectory")
            child.mkdir(mode=0o700, exist_ok=True)
            child.chmod(0o700)

    def _ensure_disk_capacity(self) -> None:
        free_bytes = shutil.disk_usage(self._store_dir).free
        if free_bytes < SELECTED_ARTIFACT.byte_count:
            raise ModelInstallationError("insufficient_disk_space")

    def _prepare_staging(self) -> None:
        if self._staging_dir.is_symlink() or (
            self._staging_dir.exists() and not self._staging_dir.is_dir()
        ):
            raise ModelInstallationError("unsafe_staging_directory")
        self._staging_dir.mkdir(mode=0o700, exist_ok=True)
        self._staging_dir.chmod(0o700)

    def _download(
        self,
        part_path: Path,
        progress: ProgressCallback | None,
        cancelled: CancellationCallback | None,
    ) -> None:
        if part_path.exists() and not _is_regular_non_symlink(part_path):
            raise ArtifactVerificationError("unsafe_partial_artifact")
        offset = part_path.stat().st_size if part_path.exists() else 0
        if offset > SELECTED_ARTIFACT.byte_count:
            part_path.unlink()
            offset = 0
        if offset == SELECTED_ARTIFACT.byte_count:
            _raise_if_cancelled(cancelled)
            self._verify_download(part_path)
            if progress is not None:
                progress(DownloadProgress(offset, SELECTED_ARTIFACT.byte_count))
            return
        if progress is not None:
            progress(DownloadProgress(offset, SELECTED_ARTIFACT.byte_count))
        headers = {"Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        client = self._new_client()
        try:
            _raise_if_cancelled(cancelled)
            with client.stream("GET", SELECTED_ARTIFACT.source, headers=headers) as response:
                redirect = self._verified_redirect(response)
                if redirect is None:
                    offset = self._write_download(response, part_path, offset, progress, cancelled)
            if redirect is not None:
                with client.stream("GET", redirect, headers=headers) as response:
                    offset = self._write_download(response, part_path, offset, progress, cancelled)
            part_path.chmod(0o600)
        except httpx.HTTPError as error:
            raise ModelInstallationError("download_failed") from error
        finally:
            client.close()

    @staticmethod
    def _verified_redirect(response: httpx.Response) -> str | None:
        if response.status_code not in {301, 302, 303, 307, 308}:
            return None
        location = response.headers.get("location")
        if not location:
            raise ModelInstallationError("download_redirect_missing")
        target = urlsplit(urljoin(str(response.url), location))
        host = target.hostname or ""
        if target.scheme != "https" or not host.endswith(".hf.co"):
            raise ModelInstallationError("download_redirect_rejected")
        return target.geturl()

    @staticmethod
    def _write_download(
        response: httpx.Response,
        part_path: Path,
        offset: int,
        progress: ProgressCallback | None,
        cancelled: CancellationCallback | None,
    ) -> int:
        if response.status_code not in ({200} if offset == 0 else {200, 206}):
            raise ModelInstallationError(f"download_http_{response.status_code}")
        mode = "ab" if offset and response.status_code == 206 else "wb"
        if mode == "wb":
            offset = 0
        with part_path.open(mode) as output:
            for block in response.iter_bytes(chunk_size=1024 * 1024):
                _raise_if_cancelled(cancelled)
                if not block:
                    continue
                output.write(block)
                offset += len(block)
                if offset > SELECTED_ARTIFACT.byte_count:
                    raise ArtifactVerificationError("download_exceeds_expected_size")
                if progress is not None:
                    progress(DownloadProgress(offset, SELECTED_ARTIFACT.byte_count))
            output.flush()
            os.fsync(output.fileno())
        return offset

    def _copy_local_artifact(
        self,
        source_path: Path,
        part_path: Path,
        progress: ProgressCallback | None,
        cancelled: CancellationCallback | None,
    ) -> None:
        if part_path.exists() or part_path.is_symlink():
            if not _is_regular_non_symlink(part_path):
                raise ArtifactVerificationError("unsafe_partial_artifact")
            part_path.unlink()
        copied = 0
        if progress is not None:
            progress(DownloadProgress(copied, SELECTED_ARTIFACT.byte_count))
        with source_path.open("rb") as source_file, part_path.open("wb") as output:
            for block in iter(lambda: source_file.read(1024 * 1024), b""):
                _raise_if_cancelled(cancelled)
                output.write(block)
                copied += len(block)
                if progress is not None:
                    progress(DownloadProgress(copied, SELECTED_ARTIFACT.byte_count))
            output.flush()
            os.fsync(output.fileno())
        part_path.chmod(0o600)

    def _new_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(
            timeout=httpx.Timeout(self._timeout_seconds),
            follow_redirects=False,
            trust_env=False,
        )

    def _verify_download(self, part_path: Path) -> None:
        if not _is_regular_non_symlink(part_path):
            raise ArtifactVerificationError("unsafe_partial_artifact")
        if part_path.stat().st_size != SELECTED_ARTIFACT.byte_count:
            raise ArtifactVerificationError("download_size_mismatch")
        if _sha256(part_path) != SELECTED_ARTIFACT.sha256:
            raise ArtifactVerificationError("download_checksum_mismatch")

    def _write_metadata(self, metadata_path: Path) -> None:
        payload = self._metadata_payload() | {
            "installed_at": datetime.now(UTC).replace(microsecond=0).isoformat()
        }
        temporary_path = metadata_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.chmod(0o600)
        with temporary_path.open("rb") as metadata_file:
            os.fsync(metadata_file.fileno())
        os.replace(temporary_path, metadata_path)

    def _promote_staging(self) -> None:
        part_path = self._staging_dir / f"{SELECTED_ARTIFACT.filename}.part"
        final_staging_path = self._staging_dir / SELECTED_ARTIFACT.filename
        os.replace(part_path, final_staging_path)
        if self.model_dir.exists() or self.model_dir.is_symlink():
            if self.model_dir.is_symlink() or not self.model_dir.is_dir():
                raise ArtifactVerificationError("unsafe_existing_model_directory")
            if self._quarantine_dir.exists() or self._quarantine_dir.is_symlink():
                self._safe_remove_tree(self._quarantine_dir)
            os.replace(self.model_dir, self._quarantine_dir)
        os.replace(self._staging_dir, self.model_dir)
        self._staging_dir.mkdir(mode=0o700, exist_ok=True)

    def _verified_installation_result(self) -> InstallationResult:
        verified = self.verify()
        if not verified.verified:
            raise ArtifactVerificationError(verified.reason_code)
        return InstallationResult(
            state="installed",
            model_id=SELECTED_ARTIFACT.model_id,
            byte_count=SELECTED_ARTIFACT.byte_count,
            sha256=SELECTED_ARTIFACT.sha256,
        )

    def _safe_remove_tree(self, target: Path) -> None:
        """Delete only a fixed manifest-owned path, refusing all symlinks."""

        if target.is_symlink():
            raise ArtifactVerificationError("refusing_to_remove_symlink")
        if not target.exists():
            return
        if target.is_file():
            if not _is_regular_non_symlink(target):
                raise ArtifactVerificationError("unsafe_file_for_removal")
            target.unlink()
            return
        if not target.is_dir():
            raise ArtifactVerificationError("unsafe_path_for_removal")
        for child in target.iterdir():
            self._safe_remove_tree(child)
        target.rmdir()

    def _exclusive_operation(self) -> _OperationLock:
        return _OperationLock(self._lock_path)


class _OperationLock:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._fd: int | None = None

    def __enter__(self) -> _OperationLock:
        try:
            self._fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            if not self._remove_stale_lock():
                raise InstallationBusyError("installation_in_progress") from error
            try:
                self._fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as retry_error:
                raise InstallationBusyError("installation_in_progress") from retry_error
        os.write(self._fd, str(os.getpid()).encode("ascii"))
        os.fsync(self._fd)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._fd is not None:
            os.close(self._fd)
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass

    def _remove_stale_lock(self) -> bool:
        """Recover only a fixed regular lock whose recorded process is no longer alive."""

        if not _is_regular_non_symlink(self._path):
            raise ArtifactVerificationError("unsafe_install_lock")
        try:
            process_id = int(self._path.read_text(encoding="ascii").strip())
        except OSError:
            process_id = -1
        except UnicodeDecodeError:
            process_id = -1
        except ValueError:
            process_id = -1
        if process_id > 0 and self._process_is_alive(process_id):
            return False
        try:
            self._path.unlink()
        except FileNotFoundError:
            return False
        return True

    @staticmethod
    def _process_is_alive(process_id: int) -> bool:
        try:
            os.kill(process_id, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True


def _cli_progress_writer() -> ProgressCallback:
    last_percent = -1

    def report(progress: DownloadProgress) -> None:
        nonlocal last_percent
        percent = int(progress.downloaded_bytes * 100 / progress.total_bytes)
        if (percent == 0 and last_percent < 0) or percent == 100 or percent >= last_percent + 5:
            print(
                f"M6-05: model download {percent}% "
                f"({progress.downloaded_bytes}/{progress.total_bytes} bytes)",
                flush=True,
            )
            last_percent = percent

    return report


def _result_as_json(result: InstallationResult | VerificationResult) -> str:
    return json.dumps(asdict(result), ensure_ascii=False, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage BPM's explicitly installed local chat model."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    describe = commands.add_parser("describe", help="show the localized install disclosure")
    describe.add_argument("--locale", choices=ACTIVE_CATALOG_LOCALES, default="en")
    commands.add_parser("verify", help="verify a local artifact without network or execution")
    install = commands.add_parser("install", help="download and verify the selected artifact")
    install.add_argument(
        "--confirm", action="store_true", help="confirm the visible installation disclosure"
    )
    install.add_argument("--locale", choices=ACTIVE_CATALOG_LOCALES, default="en")
    install_local = commands.add_parser(
        "install-local", help="verify and copy a pre-obtained local artifact without network"
    )
    install_local.add_argument("--artifact", type=Path, required=True, help="local GGUF candidate")
    install_local.add_argument(
        "--confirm", action="store_true", help="confirm the visible installation disclosure"
    )
    install_local.add_argument("--locale", choices=ACTIVE_CATALOG_LOCALES, default="en")
    remove = commands.add_parser("remove", help="remove only the selected model's owned state")
    remove.add_argument("--confirm", action="store_true", help="confirm model removal")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    installer = ModelInstaller(
        settings.DATA_DIR / "ai" / "models",
        timeout_seconds=settings.AI_MODEL_DOWNLOAD_TIMEOUT_SECONDS,
    )
    try:
        if args.command == "describe":
            print(json.dumps(installer.disclosure(args.locale), ensure_ascii=False, indent=2))
            return 0
        if args.command == "verify":
            verification = installer.verify()
            print(_result_as_json(verification))
            return 0 if verification.verified else 1
        if args.command == "install":
            if not args.confirm:
                raise ExplicitConfirmationRequired("explicit_confirmation_required")
            print(json.dumps(installer.disclosure(args.locale), ensure_ascii=False, indent=2))
            installation = installer.install(confirmed=True, progress=_cli_progress_writer())
            print(_result_as_json(installation))
            return 0
        if args.command == "install-local":
            if not args.confirm:
                raise ExplicitConfirmationRequired("explicit_confirmation_required")
            print(json.dumps(installer.disclosure(args.locale), ensure_ascii=False, indent=2))
            local_installation = installer.install_local(
                args.artifact, confirmed=True, progress=_cli_progress_writer()
            )
            print(_result_as_json(local_installation))
            return 0
        if args.command == "remove":
            removal = installer.remove(confirmed=args.confirm)
            print(_result_as_json(removal))
            return 0
    except ModelInstallationError as error:
        print(json.dumps({"state": "failed", "reason_code": str(error)}), file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":  # pragma: no cover - command entry point
    raise SystemExit(main())
