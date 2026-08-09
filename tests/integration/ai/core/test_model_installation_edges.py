from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

import app.ai.model_installation as installation


@pytest.fixture
def artifact(monkeypatch: pytest.MonkeyPatch) -> tuple[installation.ModelArtifact, bytes]:
    payload = b"compact pinned test model"
    selected = installation.ModelArtifact(
        model_id=installation.MODEL_ID,
        filename=installation.ARTIFACT_FILENAME,
        source="https://huggingface.co/owner/model/resolve/pin.gguf",
        sha256=hashlib.sha256(payload).hexdigest(),
        byte_count=len(payload),
        license_spdx="Apache-2.0",
        upstream="fixture",
        source_revision="a" * 40,
        target_architectures=("x86_64",),
    )
    monkeypatch.setattr(installation, "SELECTED_ARTIFACT", selected)
    return selected, payload


def _installer(tmp_path: Path) -> installation.ModelInstaller:
    return installation.ModelInstaller(tmp_path / "models")


def _write_verified(installer: installation.ModelInstaller, payload: bytes) -> None:
    installer._ensure_store()
    installer.model_dir.mkdir(exist_ok=True)
    installer.artifact_path.write_bytes(payload)
    installer._write_metadata(installer.metadata_path)


def test_installation_inspection_and_store_guards(
    tmp_path: Path,
    artifact: tuple[installation.ModelArtifact, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, payload = artifact
    installer = _installer(tmp_path)
    with pytest.raises(installation.ModelInstallationError, match="unsupported_locale"):
        installer.disclosure("xx")
    installer._ensure_store()
    installer.model_dir.rmdir() if installer.model_dir.exists() else None
    installer.model_dir.write_text("file", encoding="utf-8")
    assert installer.verify().reason_code == "unsafe_model_directory"
    installer.model_dir.unlink()
    _write_verified(installer, payload)
    installer.artifact_path.write_bytes(b"x" * len(payload))
    assert installer.verify().reason_code == "artifact_checksum_mismatch"
    installer.artifact_path.write_bytes(payload)
    installer.metadata_path.write_bytes(b"\xff")
    assert installer.verify().reason_code == "metadata_unreadable"
    assert installer._metadata_matches([]) is False

    bad_store = tmp_path / "bad-store"
    bad_store.write_text("file", encoding="utf-8")
    with pytest.raises(installation.ModelInstallationError, match="unsafe_store_directory"):
        installation.ModelInstaller(bad_store)._ensure_store()
    bad_subdir = tmp_path / "bad-subdir"
    bad_subdir.mkdir()
    (bad_subdir / ".staging").write_text("file", encoding="utf-8")
    with pytest.raises(installation.ModelInstallationError, match="unsafe_store_subdirectory"):
        installation.ModelInstaller(bad_subdir)._ensure_store()
    monkeypatch.setattr(installation, "_machine_architecture", lambda: "arm64")
    with pytest.raises(installation.ArtifactCompatibilityError):
        installer._assert_compatible_host()
    monkeypatch.setattr(installation.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    with pytest.raises(installation.ModelInstallationError, match="insufficient_disk_space"):
        installer._ensure_disk_capacity()


def test_install_local_remove_and_staging_edge_cases(
    tmp_path: Path, artifact: tuple[installation.ModelArtifact, bytes]
) -> None:
    selected, payload = artifact
    installer = _installer(tmp_path)
    with pytest.raises(
        installation.ArtifactVerificationError, match="unsafe_local_artifact_source"
    ):
        installer.install_local(tmp_path / "missing", confirmed=True)
    wrong = tmp_path / "wrong.gguf"
    wrong.write_bytes(b"wrong")
    with pytest.raises(
        installation.ArtifactVerificationError, match="local_artifact_size_mismatch"
    ):
        installer.install_local(wrong, confirmed=True)
    source = tmp_path / "source.gguf"
    source.write_bytes(payload)
    assert installer.install_local(source, confirmed=True).state == "installed"
    assert installer.install_local(source, confirmed=True).state == "already-installed"
    with pytest.raises(installation.ExplicitConfirmationRequired):
        installer.remove(confirmed=False)
    assert installer.remove(confirmed=True).state == "removed"
    assert installer.remove(confirmed=True).state == "not-installed"

    installer._ensure_store()
    installer._staging_dir.write_text("unsafe", encoding="utf-8")
    with pytest.raises(installation.ModelInstallationError, match="unsafe_staging_directory"):
        installer._prepare_staging()
    installer._staging_dir.unlink()
    installer._prepare_staging()
    unsafe_part = installer._staging_dir / f"{selected.filename}.part"
    unsafe_part.symlink_to(source)
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_partial_artifact"):
        installer._copy_local_artifact(source, unsafe_part, None, None)


def test_download_copy_promotion_and_removal_primitives(
    tmp_path: Path,
    artifact: tuple[installation.ModelArtifact, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected, payload = artifact
    installer = _installer(tmp_path)
    installer._ensure_store()
    installer._prepare_staging()
    part = installer._staging_dir / f"{selected.filename}.part"
    part.write_bytes(payload + b"over")
    installer._client_factory = lambda: httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=payload))
    )
    installer._download(part, None, None)
    assert part.read_bytes() == payload

    class Response:
        status_code = 200

        def iter_bytes(self, **_: object):
            return iter((b"", payload))

    progress: list[int] = []
    assert installer._write_download(
        Response(), part, 0, lambda item: progress.append(item.downloaded_bytes), None
    ) == len(payload)  # type: ignore[arg-type]
    assert progress == [len(payload)]
    wrong_size = part.with_name("wrong-size.part")
    wrong_size.write_bytes(b"x")
    with pytest.raises(installation.ArtifactVerificationError, match="download_size_mismatch"):
        installer._verify_download(wrong_size)
    installer._copy_local_artifact(part, part.with_name("copy.part"), None, None)

    installer._write_metadata(installer._staging_dir / installation.METADATA_FILENAME)
    installer._promote_staging()
    assert installer.model_dir.is_dir()
    installer._ensure_store()
    installer._prepare_staging()
    part = installer._staging_dir / f"{selected.filename}.part"
    part.write_bytes(payload)
    installer._write_metadata(installer._staging_dir / installation.METADATA_FILENAME)
    installer._quarantine_dir.mkdir(parents=True)
    (installer._quarantine_dir / "old").write_text("old", encoding="utf-8")
    installer._promote_staging()
    assert installer.model_dir.is_dir() and installer._quarantine_dir.is_dir()

    plain_file = tmp_path / "plain"
    plain_file.write_text("x", encoding="utf-8")
    installer._safe_remove_tree(plain_file)
    assert not plain_file.exists()

    class Unsupported:
        def is_symlink(self) -> bool:
            return False

        def exists(self) -> bool:
            return True

        def is_file(self) -> bool:
            return False

        def is_dir(self) -> bool:
            return False

    unsupported = Unsupported()
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_path_for_removal"):
        installer._safe_remove_tree(unsupported)


def test_locks_progress_parser_and_cli_dispatch(
    tmp_path: Path,
    artifact: tuple[installation.ModelArtifact, bytes],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, payload = artifact
    lock_path = tmp_path / "lock"
    lock = installation._OperationLock(lock_path)
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_install_lock"):
        lock._remove_stale_lock()
    lock_path.write_text("invalid", encoding="ascii")
    assert lock._remove_stale_lock() is True
    lock_path.write_text("1", encoding="ascii")
    monkeypatch.setattr(lock, "_process_is_alive", lambda _: False)
    original_unlink = Path.unlink
    monkeypatch.setattr(
        Path,
        "unlink",
        lambda path, *args, **kwargs: (
            (_ for _ in ()).throw(FileNotFoundError())
            if path == lock_path
            else original_unlink(path, *args, **kwargs)
        ),
    )
    assert lock._remove_stale_lock() is False
    lock_path.write_text("1", encoding="ascii")
    original_regular = installation._is_regular_non_symlink
    monkeypatch.setattr(installation, "_is_regular_non_symlink", lambda _: False)
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_install_lock"):
        lock._remove_stale_lock()
    monkeypatch.setattr(Path, "unlink", original_unlink)
    monkeypatch.setattr(installation, "_is_regular_non_symlink", original_regular)

    reporter = installation._cli_progress_writer()
    reporter(installation.DownloadProgress(0, 100))
    reporter(installation.DownloadProgress(3, 100))
    reporter(installation.DownloadProgress(5, 100))
    reporter(installation.DownloadProgress(100, 100))
    assert capsys.readouterr().out.count("model download") == 3
    assert installation.build_parser().parse_args(["remove", "--confirm"]).command == "remove"
    assert '"verified": true' in installation._result_as_json(
        installation.VerificationResult("installed", True, "verified", "model")
    )

    class CliInstaller:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        def disclosure(self, locale: str) -> dict[str, str]:
            return {"locale": locale}

        def verify(self) -> installation.VerificationResult:
            return installation.VerificationResult("installed", True, "verified", "model")

        def install(self, **_: object) -> installation.InstallationResult:
            return installation.InstallationResult("installed", "model", len(payload), "hash")

        def install_local(self, *_: object, **__: object) -> installation.InstallationResult:
            return installation.InstallationResult("installed", "model", len(payload), "hash")

        def remove(self, **_: object) -> installation.InstallationResult:
            return installation.InstallationResult("removed", "model", 0, "hash")

    monkeypatch.setattr(
        installation,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, AI_MODEL_DOWNLOAD_TIMEOUT_SECONDS=1),
    )
    monkeypatch.setattr(installation, "ModelInstaller", CliInstaller)
    assert installation.main(["describe"]) == 0
    assert installation.main(["verify"]) == 0
    assert installation.main(["install", "--confirm"]) == 0
    local = tmp_path / "local.gguf"
    local.write_bytes(payload)
    assert installation.main(["install-local", "--confirm", "--artifact", str(local)]) == 0
    assert installation.main(["remove", "--confirm"]) == 0


def test_remaining_model_lifecycle_fail_closed_branches(
    tmp_path: Path,
    artifact: tuple[installation.ModelArtifact, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected, payload = artifact
    installer = _installer(tmp_path)
    installer._ensure_store()
    installer.model_dir.symlink_to(tmp_path / "outside")
    assert installer.verify().reason_code == "unsafe_model_directory"
    installer.model_dir.unlink()
    _write_verified(installer, payload)
    original_stat = Path.stat
    monkeypatch.setattr(
        Path,
        "stat",
        lambda path, *args, **kwargs: (
            (_ for _ in ()).throw(OSError("stat"))
            if path == installer.artifact_path
            else original_stat(path, *args, **kwargs)
        ),
    )
    assert installer.verify().reason_code == "artifact_stat_failed"
    monkeypatch.setattr(Path, "stat", original_stat)

    original_read_text = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *args, **kwargs: (
            (_ for _ in ()).throw(OSError("read"))
            if path == installer.metadata_path
            else original_read_text(path, *args, **kwargs)
        ),
    )
    assert installer.verify().reason_code == "metadata_unreadable"
    monkeypatch.setattr(Path, "read_text", original_read_text)
    assert installer.install(confirmed=True).state == "already-installed"

    installer.remove(confirmed=True)
    installer._ensure_store()
    installer._prepare_staging()
    unsafe = installer._staging_dir / f"{selected.filename}.part"
    outside = tmp_path / "outside"
    outside.write_bytes(payload)
    unsafe.symlink_to(outside)
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_partial_artifact"):
        installer._download(unsafe, None, None)
    unsafe.unlink()
    unsafe.write_bytes(payload)
    seen: list[int] = []
    installer._download(unsafe, lambda item: seen.append(item.downloaded_bytes), None)
    assert seen == [len(payload)]

    redirect_calls: list[str] = []

    def redirected(request: httpx.Request) -> httpx.Response:
        redirect_calls.append(str(request.url))
        if len(redirect_calls) == 1:
            return httpx.Response(302, headers={"location": "https://cdn.hf.co/model"})
        return httpx.Response(200, content=payload)

    redirect_part = unsafe.with_name("redirect.part")
    installer._client_factory = lambda: httpx.Client(transport=httpx.MockTransport(redirected))
    installer._download(redirect_part, None, None)
    assert len(redirect_calls) == 2
    installer._client_factory = lambda: httpx.Client(
        transport=httpx.MockTransport(lambda _: (_ for _ in ()).throw(httpx.ConnectError("no")))
    )
    with pytest.raises(installation.ModelInstallationError, match="download_failed"):
        installer._download(redirect_part.with_name("http.part"), None, None)

    copy_part = unsafe.with_name("copy-existing.part")
    copy_part.write_bytes(b"old")
    copied: list[int] = []
    installer._copy_local_artifact(
        unsafe, copy_part, lambda item: copied.append(item.downloaded_bytes), None
    )
    assert copied == [0, len(payload)]
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_partial_artifact"):
        installer._verify_download(copy_part.with_name("missing"))
    installer.model_dir.write_text("unsafe", encoding="utf-8")
    installer._prepare_staging()
    (installer._staging_dir / f"{selected.filename}.part").write_bytes(payload)
    with pytest.raises(
        installation.ArtifactVerificationError, match="unsafe_existing_model_directory"
    ):
        installer._promote_staging()
    installer.model_dir.unlink()
    monkeypatch.setattr(
        installer,
        "verify",
        lambda: installation.VerificationResult("bad", False, "broken", selected.model_id),
    )
    with pytest.raises(installation.ArtifactVerificationError, match="broken"):
        installer._verified_installation_result()


def test_remaining_lock_and_cli_error_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    lock_path = tmp_path / "lock"
    lock_path.write_text("1", encoding="ascii")
    lock = installation._OperationLock(lock_path)
    monkeypatch.setattr(lock, "_remove_stale_lock", lambda: True)
    original_open = installation.os.open
    calls = 0

    def already_exists(*args: object, **kwargs: object) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise FileExistsError()
        raise FileExistsError()

    monkeypatch.setattr(installation.os, "open", already_exists)
    with pytest.raises(installation.InstallationBusyError):
        lock.__enter__()
    monkeypatch.setattr(installation.os, "open", original_open)
    lock._fd = None
    lock.__exit__(None, None, None)
    assert not lock_path.exists()

    for error, expected in ((ProcessLookupError(), False), (PermissionError(), True)):
        monkeypatch.setattr(
            installation.os,
            "kill",
            lambda *_args, actual=error: (_ for _ in ()).throw(actual),
        )
        assert installation._OperationLock._process_is_alive(1) is expected

    class FailedInstaller:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        def disclosure(self, _: str) -> dict[str, str]:
            return {}

        def install(self, **_: object) -> object:
            raise installation.ModelInstallationError("failed")

        def install_local(self, *_: object, **__: object) -> object:
            raise installation.ModelInstallationError("failed")

        def verify(self) -> installation.VerificationResult:
            return installation.VerificationResult("missing", False, "missing", "model")

        def remove(self, **_: object) -> object:
            return installation.InstallationResult("removed", "model", 0, "hash")

    monkeypatch.setattr(
        installation,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, AI_MODEL_DOWNLOAD_TIMEOUT_SECONDS=1),
    )
    monkeypatch.setattr(installation, "ModelInstaller", FailedInstaller)
    assert installation.main(["install"]) == 2
    assert installation.main(["install-local", "--artifact", str(tmp_path / "model")]) == 2
    assert installation.main(["install", "--confirm"]) == 2
    assert '"state": "failed"' in capsys.readouterr().err


def test_model_installation_last_recovery_branches(
    tmp_path: Path,
    artifact: tuple[installation.ModelArtifact, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected, payload = artifact
    installer = _installer(tmp_path)
    installer._ensure_store()
    installer._prepare_staging()
    part = installer._staging_dir / f"{selected.filename}.part"
    part.write_bytes(payload)
    installer._write_metadata(installer._staging_dir / installation.METADATA_FILENAME)
    installer.model_dir.mkdir()
    (installer.model_dir / "old").write_bytes(payload)
    installer._promote_staging()
    assert installer.model_dir.is_dir()
    assert installer._quarantine_dir.is_dir()

    installer._safe_remove_tree(tmp_path / "missing")
    unsafe_file = tmp_path / "unsafe-file"
    unsafe_file.write_bytes(b"x")
    original_regular = installation._is_regular_non_symlink
    monkeypatch.setattr(
        installation,
        "_is_regular_non_symlink",
        lambda path: False if path == unsafe_file else original_regular(path),
    )
    with pytest.raises(installation.ArtifactVerificationError, match="unsafe_file_for_removal"):
        installer._safe_remove_tree(unsafe_file)
    monkeypatch.setattr(installation, "_is_regular_non_symlink", original_regular)

    missing_lock = installation._OperationLock(tmp_path / "missing-lock")
    missing_lock.__exit__(None, None, None)
    lock_path = tmp_path / "lock"
    lock_path.write_text("1", encoding="ascii")
    lock = installation._OperationLock(lock_path)
    original_read_text = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *args, **kwargs: (
            (_ for _ in ()).throw(OSError("read"))
            if path == lock_path
            else original_read_text(path, *args, **kwargs)
        ),
    )
    assert lock._remove_stale_lock() is True
    monkeypatch.setattr(Path, "read_text", original_read_text)
    lock_path.write_bytes(b"\xff")
    assert lock._remove_stale_lock() is True
    monkeypatch.setattr(installation.os, "kill", lambda *_: None)
    assert installation._OperationLock._process_is_alive(1) is True

    class Parser:
        def parse_args(self, _: object) -> object:
            return SimpleNamespace(command="unknown")

    monkeypatch.setattr(installation, "build_parser", lambda: Parser())
    monkeypatch.setattr(
        installation,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, AI_MODEL_DOWNLOAD_TIMEOUT_SECONDS=1),
    )
    monkeypatch.setattr(installation, "ModelInstaller", lambda *_args, **_kwargs: object())
    with pytest.raises(AssertionError, match="Unhandled"):
        installation.main([])
