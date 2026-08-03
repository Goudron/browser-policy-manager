from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.ai.runtime_installation as runtime


def _archive(path: Path, *, cli: bool = True, link: str | None = None) -> bytes:
    with tarfile.open(path, mode="w:gz") as archive:
        directory = tarfile.TarInfo("llama-b9637")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        if cli:
            command = tarfile.TarInfo("llama-b9637/llama-cli")
            command.mode = 0o755
            command.size = 4
            archive.addfile(command, io.BytesIO(b"cli\n"))
        library = tarfile.TarInfo("llama-b9637/libllama.so")
        library.mode = 0o600
        library.size = 3
        archive.addfile(library, io.BytesIO(b"lib"))
        readme = tarfile.TarInfo("llama-b9637/README.txt")
        readme.size = 1
        archive.addfile(readme, io.BytesIO(b"x"))
        if link is not None:
            alias = tarfile.TarInfo("llama-b9637/libalias.so")
            alias.type = tarfile.SYMTYPE
            alias.linkname = link
            archive.addfile(alias)
    return path.read_bytes()


@pytest.fixture
def pinned(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, bytes]:
    archive = tmp_path / "runtime.tar.gz"
    payload = _archive(archive, link="libllama.so")
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", len(payload))
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(payload).hexdigest())
    return archive, payload


def test_runtime_inspection_installation_and_filesystem_guards(
    tmp_path: Path, pinned: tuple[Path, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, payload = pinned
    installer = runtime.RuntimeInstaller(tmp_path / "runtime")
    installer._ensure_root()
    installer.bundle_dir.write_text("file", encoding="utf-8")
    assert installer.verify().reason_code == "unsafe_runtime_directory"
    installer.bundle_dir.unlink()
    assert installer.install_local(source, confirmed=True).state == "installed"
    assert installer.install_local(source, confirmed=True).state == "already-installed"
    installer.archive_path.write_bytes(b"x" * len(payload))
    assert installer.verify().reason_code == "runtime_archive_checksum_mismatch"
    installer.archive_path.write_bytes(payload)
    installer.metadata_path.write_bytes(b"\xff")
    assert installer.verify().reason_code == "runtime_metadata_unreadable"
    assert installer.remove(confirmed=True).state == "removed"
    assert installer.remove(confirmed=True).state == "not-installed"
    with pytest.raises(runtime.RuntimeConfirmationRequired):
        installer.remove(confirmed=False)

    bad_root = tmp_path / "bad-root"
    bad_root.write_text("file", encoding="utf-8")
    with pytest.raises(runtime.RuntimeInstallationError, match="unsafe_runtime_root"):
        runtime.RuntimeInstaller(bad_root)._ensure_root()
    staging_root = tmp_path / "staging-root"
    staging_root.mkdir()
    (staging_root / ".staging").write_text("file", encoding="utf-8")
    with pytest.raises(runtime.RuntimeInstallationError, match="unsafe_runtime_staging_root"):
        runtime.RuntimeInstaller(staging_root)._ensure_root()
    installer._ensure_root()
    installer._staging_dir.rmdir()
    installer._staging_dir.write_text("file", encoding="utf-8")
    with pytest.raises(runtime.RuntimeInstallationError, match="unsafe_runtime_staging_directory"):
        installer._prepare_staging()
    installer._staging_dir.unlink()
    installer._prepare_staging()
    monkeypatch.setattr(
        runtime,
        "_regular_non_symlink",
        lambda path: False if path == source else True,
    )
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_local_runtime_archive"):
        installer.install_local(source, confirmed=True)


def test_runtime_extraction_rejects_bad_archives_and_preserves_minimal_bundle(
    tmp_path: Path, pinned: tuple[Path, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = pinned
    with pytest.raises(runtime.RuntimeVerificationError, match="checksum"):
        runtime.extract_verified_worker_bundle(tmp_path / "missing", tmp_path / "out")

    missing_cli = tmp_path / "missing-cli.tar.gz"
    payload = _archive(missing_cli, cli=False)
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", len(payload))
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(payload).hexdigest())
    with pytest.raises(runtime.RuntimeVerificationError, match="runtime_cli_missing"):
        runtime.extract_verified_worker_bundle(missing_cli, tmp_path / "missing-cli")

    unsafe_link = tmp_path / "unsafe-link.tar.gz"
    payload = _archive(unsafe_link, link="../outside")
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", len(payload))
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(payload).hexdigest())
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_runtime_archive_link"):
        runtime.extract_verified_worker_bundle(unsafe_link, tmp_path / "unsafe-link")

    # A destination that already exists is a filesystem failure, never an overwrite.
    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(FileExistsError):
        runtime.extract_verified_worker_bundle(unsafe_link, destination)
    assert source.exists()


def test_runtime_copy_metadata_removal_progress_and_cli_paths(
    tmp_path: Path,
    pinned: tuple[Path, bytes],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source, payload = pinned
    installer = runtime.RuntimeInstaller(tmp_path / "runtime")
    installer._ensure_root()
    installer._prepare_staging()
    copied: list[int] = []
    copy = installer._staging_dir / "copy.tar.gz"
    installer._copy(source, copy, lambda item: copied.append(item.copied_bytes))
    assert copied == [0, len(payload)]
    installer._write_metadata(installer._staging_dir / "metadata.json")
    assert (installer._staging_dir / "metadata.json").is_file()
    missing = tmp_path / "missing"
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_runtime_path_for_removal"):
        installer._remove_tree(missing)
    unsafe = tmp_path / "unsafe"
    unsafe.write_text("unsafe", encoding="utf-8")
    original_regular = runtime._regular_non_symlink
    monkeypatch.setattr(runtime, "_regular_non_symlink", lambda path: False if path == unsafe else original_regular(path))
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_runtime_file_for_removal"):
        installer._remove_tree(unsafe)
    monkeypatch.setattr(runtime, "_regular_non_symlink", original_regular)

    report = runtime._progress()
    report(runtime.RuntimeCopyProgress(0, 100))
    report(runtime.RuntimeCopyProgress(3, 100))
    report(runtime.RuntimeCopyProgress(5, 100))
    report(runtime.RuntimeCopyProgress(100, 100))
    assert capsys.readouterr().out.count("runtime install") == 3
    assert runtime.build_parser().parse_args(["remove", "--confirm"]).command == "remove"
    assert '"verified": true' in runtime._result(runtime.RuntimeVerification("installed", True, "verified", "id"))

    class CliInstaller:
        def __init__(self, *_: object) -> None:
            pass

        def verify(self) -> runtime.RuntimeVerification:
            return runtime.RuntimeVerification("installed", True, "verified", "id")

        def install_local(self, *_: object, **__: object) -> runtime.RuntimeInstallationResult:
            return runtime.RuntimeInstallationResult("installed", "id", 1, "hash")

        def remove(self, **_: object) -> runtime.RuntimeInstallationResult:
            return runtime.RuntimeInstallationResult("removed", "id", 0, "hash")

    monkeypatch.setattr(runtime, "get_settings", lambda: SimpleNamespace(DATA_DIR=tmp_path))
    monkeypatch.setattr(runtime, "RuntimeInstaller", CliInstaller)
    assert runtime.main(["verify"]) == 0
    assert runtime.main(["install-local", "--confirm", "--archive", str(source)]) == 0
    assert runtime.main(["remove", "--confirm"]) == 0


def test_runtime_extraction_and_verification_all_failure_forms(
    tmp_path: Path, pinned: tuple[Path, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _ = pinned
    original_tar_open = tarfile.open

    def pin(path: Path) -> None:
        payload = path.read_bytes()
        monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", len(payload))
        monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(payload).hexdigest())

    unsafe_path = tmp_path / "unsafe-path.tar.gz"
    with tarfile.open(unsafe_path, mode="w:gz") as archive:
        member = tarfile.TarInfo("../escape")
        member.size = 1
        archive.addfile(member, io.BytesIO(b"x"))
    pin(unsafe_path)
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_runtime_archive_path"):
        runtime.extract_verified_worker_bundle(unsafe_path, tmp_path / "unsafe-path")

    unsafe_member = tmp_path / "unsafe-member.tar.gz"
    with tarfile.open(unsafe_member, mode="w:gz") as archive:
        directory = tarfile.TarInfo("llama-b9637")
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        command = tarfile.TarInfo("llama-b9637/llama-cli")
        command.type = tarfile.DIRTYPE
        archive.addfile(command)
    pin(unsafe_member)
    with pytest.raises(runtime.RuntimeVerificationError, match="unsafe_runtime_archive_member"):
        runtime.extract_verified_worker_bundle(unsafe_member, tmp_path / "unsafe-member")

    cli = tarfile.TarInfo("llama-b9637/llama-cli")
    cli.size = 1

    class Archive:
        def __enter__(self) -> Archive:
            return self

        def __exit__(self, *_: object) -> bool:
            return False

        def getmembers(self) -> list[tarfile.TarInfo]:
            return [cli]

        def extractfile(self, _: tarfile.TarInfo) -> None:
            return None

    fake_archive = tmp_path / "fake.tar.gz"
    fake_archive.write_bytes(b"x")
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_BYTES", 1)
    monkeypatch.setattr(runtime, "RUNTIME_ARCHIVE_SHA256", hashlib.sha256(b"x").hexdigest())
    monkeypatch.setattr(runtime.tarfile, "open", lambda *_args, **_kwargs: Archive())
    with pytest.raises(runtime.RuntimeVerificationError, match="member_unreadable"):
        runtime.extract_verified_worker_bundle(fake_archive, tmp_path / "unreadable")
    monkeypatch.setattr(runtime.tarfile, "open", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("bad")))
    with pytest.raises(runtime.RuntimeVerificationError, match="bundle_extraction_failed"):
        runtime.extract_verified_worker_bundle(fake_archive, tmp_path / "os-error")
    monkeypatch.setattr(runtime.tarfile, "open", lambda *_args, **_kwargs: (_ for _ in ()).throw(tarfile.TarError("bad")))
    with pytest.raises(runtime.RuntimeVerificationError, match="bundle_extraction_failed"):
        runtime.extract_verified_worker_bundle(fake_archive, tmp_path / "tar-error")

    monkeypatch.setattr(runtime.tarfile, "open", original_tar_open)
    valid = tmp_path / "valid.tar.gz"
    _archive(valid)
    pin(valid)
    monkeypatch.setattr(runtime.tarfile, "open", original_tar_open)
    monkeypatch.setattr(runtime.os, "access", lambda *_: False)
    with pytest.raises(runtime.RuntimeVerificationError, match="runtime_cli_extraction_failed"):
        runtime.extract_verified_worker_bundle(valid, tmp_path / "not-executable")


def test_runtime_install_verify_remove_and_cli_remaining_failures(
    tmp_path: Path, pinned: tuple[Path, bytes], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source, payload = pinned
    installer = runtime.RuntimeInstaller(tmp_path / "runtime")
    installer._ensure_root()
    installer.bundle_dir.symlink_to(tmp_path / "outside")
    assert installer.verify().reason_code == "unsafe_runtime_directory"
    installer.bundle_dir.unlink()
    installer.bundle_dir.mkdir()
    assert installer.verify().reason_code == "unsafe_or_missing_runtime_archive"
    installer.archive_path.write_bytes(b"x")
    assert installer.verify().reason_code == "unsafe_or_missing_runtime_metadata"
    installer.metadata_path.write_text("{}", encoding="utf-8")
    assert installer.verify().reason_code == "runtime_archive_size_mismatch"
    installer.archive_path.write_bytes(payload)
    assert installer.verify().reason_code == "runtime_metadata_mismatch"

    wrong = tmp_path / "wrong.tar.gz"
    wrong.write_bytes(b"wrong")
    installer.remove(confirmed=True)
    with pytest.raises(runtime.RuntimeVerificationError, match="runtime_archive_size_mismatch"):
        installer.install_local(wrong, confirmed=True)
    wrong.write_bytes(b"x" * len(payload))
    with pytest.raises(runtime.RuntimeVerificationError, match="runtime_archive_checksum_mismatch"):
        installer.install_local(wrong, confirmed=True)

    def bad_copy(_: Path, destination: Path, __: object) -> None:
        destination.write_bytes(b"wrong")

    original_copy = installer._copy
    monkeypatch.setattr(installer, "_copy", bad_copy)
    with pytest.raises(runtime.RuntimeVerificationError, match="copy_verification"):
        installer.install_local(source, confirmed=True)
    monkeypatch.setattr(installer, "_copy", original_copy)

    installer = runtime.RuntimeInstaller(tmp_path / "second")
    installer._ensure_root()
    installer._prepare_staging()
    installer.bundle_dir.mkdir()
    with pytest.raises(runtime.RuntimeVerificationError, match="existing_runtime_bundle"):
        installer.install_local(source, confirmed=True)

    symlink = tmp_path / "symlink"
    symlink.symlink_to(source)
    with pytest.raises(runtime.RuntimeVerificationError, match="refusing_to_remove_runtime_symlink"):
        installer._remove_tree(symlink)

    class ErrorInstaller:
        def __init__(self, *_: object) -> None:
            pass

        def verify(self) -> runtime.RuntimeVerification:
            return runtime.RuntimeVerification("missing", False, "missing", "id")

        def install_local(self, *_: object, **__: object) -> object:
            raise runtime.RuntimeInstallationError("failed")

        def remove(self, **_: object) -> object:
            raise runtime.RuntimeInstallationError("failed")

    monkeypatch.setattr(runtime, "get_settings", lambda: SimpleNamespace(DATA_DIR=tmp_path))
    monkeypatch.setattr(runtime, "RuntimeInstaller", ErrorInstaller)
    assert runtime.main(["install-local", "--confirm", "--archive", str(source)]) == 2
    assert runtime.main(["remove", "--confirm"]) == 2
    assert '"state": "failed"' in capsys.readouterr().err

    class Parser:
        def parse_args(self, _: object) -> object:
            return SimpleNamespace(command="unknown")

    monkeypatch.setattr(runtime, "build_parser", lambda: Parser())
    monkeypatch.setattr(runtime, "RuntimeInstaller", lambda *_: object())
    with pytest.raises(AssertionError, match="Unhandled"):
        runtime.main([])


def test_runtime_last_verification_and_promotion_guards(
    tmp_path: Path, pinned: tuple[Path, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = pinned
    installer = runtime.RuntimeInstaller(tmp_path / "runtime")
    assert installer.install_local(source, confirmed=True).state == "installed"
    original_stat = Path.stat
    monkeypatch.setattr(
        Path,
        "stat",
        lambda path, *args, **kwargs: (_ for _ in ()).throw(OSError("stat"))
        if path == installer.archive_path
        else original_stat(path, *args, **kwargs),
    )
    assert installer.verify().reason_code == "runtime_archive_stat_failed"
    monkeypatch.setattr(Path, "stat", original_stat)
    original_read_text = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *args, **kwargs: (_ for _ in ()).throw(OSError("read"))
        if path == installer.metadata_path
        else original_read_text(path, *args, **kwargs),
    )
    assert installer.verify().reason_code == "runtime_metadata_unreadable"
    monkeypatch.setattr(Path, "read_text", original_read_text)
    installer.metadata_path.write_text("{", encoding="utf-8")
    assert installer.verify().reason_code == "runtime_metadata_unreadable"

    expected = iter(
        (
            runtime.RuntimeVerification("missing", False, "runtime_missing", runtime.RUNTIME_ID),
            runtime.RuntimeVerification("bad", False, "post_promotion_failed", runtime.RUNTIME_ID),
        )
    )
    failing = runtime.RuntimeInstaller(tmp_path / "failing")
    monkeypatch.setattr(failing, "verify", lambda: next(expected))
    with pytest.raises(runtime.RuntimeVerificationError, match="post_promotion_failed"):
        failing.install_local(source, confirmed=True)
