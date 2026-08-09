from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path

import pytest

import app.ai.runtime_installation as runtime


def _write_archive(path: Path, cli_source: bytes) -> bytes:
    with tarfile.open(path, mode="w:gz") as archive:
        directory = tarfile.TarInfo("llama-b9637")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        executable = tarfile.TarInfo("llama-b9637/llama-cli")
        executable.mode = 0o755
        executable.size = len(cli_source)
        archive.addfile(executable, io.BytesIO(cli_source))
        library = tarfile.TarInfo("llama-b9637/libllama.so.0.0")
        library.mode = 0o755
        library.size = 3
        archive.addfile(library, io.BytesIO(b"lib"))
        link = tarfile.TarInfo("llama-b9637/libllama.so")
        link.type = tarfile.SYMTYPE
        link.linkname = "libllama.so.0.0"
        archive.addfile(link)
    return path.read_bytes()


@pytest.fixture
def pinned_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, bytes]:
    archive = tmp_path / "llama.tar.gz"
    cli_source = b"#!/usr/bin/python3\nprint('ready')\n"
    payload = _write_archive(archive, cli_source)
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", len(payload))
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SOURCE", "https://example.invalid/llama.tar.gz")
    return archive, cli_source


def test_local_runtime_archive_is_verified_promoted_and_extracted_minimally(
    tmp_path: Path, pinned_runtime: tuple[Path, bytes]
) -> None:
    archive, cli_source = pinned_runtime
    installer = runtime.RuntimeInstaller(tmp_path / "runtime")

    assert installer.install_local(archive, confirmed=True).state == "installed"
    assert installer.verify().verified is True
    assert (installer.bundle_dir / runtime.RUNTIME_ARCHIVE_FILENAME).is_file()

    destination = tmp_path / "extracted"
    executable = runtime.extract_verified_worker_bundle(installer.archive_path, destination)
    assert executable.read_bytes() == cli_source
    assert (destination / "libllama.so").is_symlink()
    assert not (destination / "llama-server").exists()


def test_runtime_archive_requires_confirmation_and_rejects_symlink_source(
    tmp_path: Path, pinned_runtime: tuple[Path, bytes]
) -> None:
    archive, _ = pinned_runtime
    installer = runtime.RuntimeInstaller(tmp_path / "runtime")

    with pytest.raises(runtime.RuntimeConfirmationRequired):
        installer.install_local(archive, confirmed=False)

    alias = tmp_path / "alias.tar.gz"
    alias.symlink_to(archive)
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_local_runtime_archive"):
        installer.install_local(alias, confirmed=True)
