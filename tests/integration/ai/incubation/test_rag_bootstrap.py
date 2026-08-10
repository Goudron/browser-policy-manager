from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai import rag_bootstrap


class _Generation:
    CONFIG_PATH = Path("unused")
    GenerationError = ValueError

    @staticmethod
    def _read_json(path: Path) -> dict:
        return {
            "matrix": {
                "active_pointer_file_name": "active-generation.json",
                "root_manifest_file_name": "generation-manifest.json",
            },
            "input": {"locales": ["en", "ru", "de", "zh-CN", "fr", "es-ES"]},
        }

    @staticmethod
    def _validate_storage_decision(config: dict) -> None:
        del config

    @staticmethod
    def _decision_candidate(config: dict) -> dict:
        del config
        return {}

    @staticmethod
    def validate_generation(root: Path, config: dict) -> dict:
        return json.loads(
            (root / config["matrix"]["root_manifest_file_name"]).read_text(encoding="utf-8")
        )


def _write_ready_state(root: Path, fingerprint: str = "fingerprint") -> None:
    chunks = {
        "bpm_version": "0.9.3",
        "source_manifest_sha256": "source-manifest",
    }
    chunks_path = root / "chunks.json"
    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    chunks_path.write_text(json.dumps(chunks), encoding="utf-8")
    generation_id = "raggen-v1-test"
    generation_root = root / "index/generations" / generation_id
    generation_root.mkdir(parents=True, exist_ok=True)
    generation_manifest = {
        "generation_id": generation_id,
        "source_manifest_sha256": chunks["source_manifest_sha256"],
    }
    manifest_path = generation_root / "generation-manifest.json"
    manifest_path.write_text(json.dumps(generation_manifest), encoding="utf-8")
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    pointer_path = root / "index/active-generation.json"
    pointer_path.parent.mkdir(exist_ok=True)
    pointer_path.write_text(
        json.dumps({"generation_id": generation_id, "manifest_sha256": manifest_sha256}),
        encoding="utf-8",
    )
    (root / rag_bootstrap.BOOTSTRAP_STATE_FILE_NAME).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_fingerprint": fingerprint,
                "chunk_manifest_sha256": hashlib.sha256(chunks_path.read_bytes()).hexdigest(),
                "generation_id": generation_id,
                "generation_manifest_sha256": manifest_sha256,
            }
        ),
        encoding="utf-8",
    )


def test_provision_retains_verified_generation_without_dita_extraction(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rag_root = tmp_path / "ai/rag"
    _write_ready_state(rag_root)

    class Installer:
        def __init__(self, root: Path) -> None:
            self.root = root

        def provision(self) -> Path:
            return self.root / "e5-base"

    def unexpected_extraction(destination: Path) -> None:
        raise AssertionError(f"unexpected chunk extraction: {destination}")

    monkeypatch.setattr(rag_bootstrap, "E5ModelInstaller", Installer)
    monkeypatch.setattr(
        rag_bootstrap,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, APP_VERSION="0.9.3"),
    )
    monkeypatch.setattr(rag_bootstrap, "_generation_module", lambda: _Generation)
    monkeypatch.setattr(rag_bootstrap, "_published_source_fingerprint", lambda: "fingerprint")
    monkeypatch.setattr(rag_bootstrap, "_extract_chunks", unexpected_extraction)

    result = rag_bootstrap.provision()

    assert result["generation_id"] == "raggen-v1-test"
    assert result["cache_misses"] == {
        locale: 0 for locale in _Generation._read_json(Path())["input"]["locales"]
    }
    output = capsys.readouterr().out
    assert "retained verified active generation raggen-v1-test" in output
    assert "extracting current six-locale" not in output


def test_verified_generation_is_not_reused_after_source_fingerprint_changes(tmp_path: Path) -> None:
    rag_root = tmp_path / "rag"
    _write_ready_state(rag_root)

    result = rag_bootstrap._active_generation_result(
        rag_root,
        rag_root / "chunks.json",
        "changed-fingerprint",
        "0.9.3",
        _Generation,
    )

    assert result is None


def test_provision_adopts_a_verified_legacy_generation_without_extraction(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    rag_root = tmp_path / "ai/rag"
    _write_ready_state(rag_root)
    (rag_root / rag_bootstrap.BOOTSTRAP_STATE_FILE_NAME).unlink()

    class Installer:
        def __init__(self, root: Path) -> None:
            self.root = root

        def provision(self) -> Path:
            return self.root / "e5-base"

    monkeypatch.setattr(rag_bootstrap, "E5ModelInstaller", Installer)
    monkeypatch.setattr(
        rag_bootstrap,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, APP_VERSION="0.9.3"),
    )
    monkeypatch.setattr(rag_bootstrap, "_generation_module", lambda: _Generation)
    monkeypatch.setattr(rag_bootstrap, "_published_source_fingerprint", lambda: "fingerprint")
    monkeypatch.setattr(rag_bootstrap, "_chunks_match_current_sources", lambda chunks: True)
    monkeypatch.setattr(
        rag_bootstrap,
        "_extract_chunks",
        lambda destination: (_ for _ in ()).throw(
            AssertionError(f"unexpected extraction: {destination}")
        ),
    )

    result = rag_bootstrap.provision()

    assert result["generation_id"] == "raggen-v1-test"
    assert (rag_root / rag_bootstrap.BOOTSTRAP_STATE_FILE_NAME).is_file()
    assert "adopted verified existing active generation raggen-v1-test" in capsys.readouterr().out


def test_json_source_guards_and_chunks_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    regular = tmp_path / "value.json"
    regular.write_text("[]", encoding="utf-8")
    assert rag_bootstrap._read_regular_json(regular) is None
    regular.write_text("{", encoding="utf-8")
    assert rag_bootstrap._read_regular_json(regular) is None
    regular.write_text('{"value": 1}', encoding="utf-8")
    assert rag_bootstrap._read_regular_json(regular) == {"value": 1}
    assert not rag_bootstrap._chunks_match_current_sources({"chunks": "bad"})
    assert not rag_bootstrap._chunks_match_current_sources({"chunks": [{}]})
    source = tmp_path / "documentation/source.dita"
    source.parent.mkdir()
    source.write_text("source", encoding="utf-8")
    monkeypatch.setattr(rag_bootstrap, "REPOSITORY_ROOT", tmp_path)
    assert rag_bootstrap._chunks_match_current_sources(
        {
            "chunks": [
                {
                    "source_dita_path": "documentation/source.dita",
                    "source_sha256": rag_bootstrap._sha256(source),
                }
            ]
        }
    )
    assert not rag_bootstrap._chunks_match_current_sources(
        {"chunks": [{"source_dita_path": "outside", "source_sha256": "x"}]}
    )


def test_installer_copies_pinned_source_and_preserves_invalid_existing_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "embeddings"
    source = tmp_path / "source"
    source.mkdir()
    payload = b"model"
    (source / "model.bin").write_bytes(payload)
    monkeypatch.setattr(
        rag_bootstrap, "MODEL_FILES", {"model.bin": hashlib.sha256(payload).hexdigest()}
    )
    monkeypatch.setattr(rag_bootstrap, "MODEL_DIRECTORY_NAME", "model")
    verified: list[Path] = []
    monkeypatch.setattr(rag_bootstrap, "verify_model_directory", lambda path: verified.append(path))
    installer = rag_bootstrap.E5ModelInstaller(root, source_model_dir=source)
    assert installer.provision() == root / "model"
    assert (root / "model/model.bin").read_bytes() == payload
    assert installer.provision() == root / "model"
    monkeypatch.setattr(
        rag_bootstrap, "verify_model_directory", lambda path: (_ for _ in ()).throw(ValueError())
    )
    with pytest.raises(rag_bootstrap.RagBootstrapError, match="not removed"):
        installer.provision()


def test_installer_rejects_unsafe_root_and_extract_reports_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "not-directory"
    root.write_text("x", encoding="utf-8")
    with pytest.raises(rag_bootstrap.RagBootstrapError, match="unsafe"):
        rag_bootstrap.E5ModelInstaller(root).provision()
    monkeypatch.setattr(rag_bootstrap.os, "spawnv", lambda *args: 1)
    with pytest.raises(rag_bootstrap.RagBootstrapError, match="extraction failed"):
        rag_bootstrap._extract_chunks(tmp_path / "chunks.json")


def test_provision_rebuilds_generation_and_rejects_wrong_chunk_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Installer:
        def __init__(self, root: Path) -> None:
            self.root = root

        def provision(self) -> Path:
            return self.root / "e5"

    class Generation(_Generation):
        @staticmethod
        def run(chunks: Path, model: Path, index: Path, cache: Path) -> dict[str, object]:
            root = index / "generations/raggen-v1-new"
            root.mkdir(parents=True)
            manifest = root / "generation-manifest.json"
            manifest.write_text('{"generation_id":"raggen-v1-new"}', encoding="utf-8")
            return {"generation_id": "raggen-v1-new", "generation_root": str(root)}

    monkeypatch.setattr(rag_bootstrap, "E5ModelInstaller", Installer)
    monkeypatch.setattr(
        rag_bootstrap,
        "get_settings",
        lambda: SimpleNamespace(DATA_DIR=tmp_path, APP_VERSION="0.9.3"),
    )
    monkeypatch.setattr(rag_bootstrap, "_generation_module", lambda: Generation)
    monkeypatch.setattr(rag_bootstrap, "_published_source_fingerprint", lambda: "fingerprint")
    monkeypatch.setattr(
        rag_bootstrap,
        "_extract_chunks",
        lambda path: path.write_text('{"bpm_version":"0.9.3"}', encoding="utf-8"),
    )
    assert rag_bootstrap.provision()["generation_id"] == "raggen-v1-new"
    monkeypatch.setattr(
        rag_bootstrap,
        "_extract_chunks",
        lambda path: path.write_text('{"bpm_version":"wrong"}', encoding="utf-8"),
    )
    with pytest.raises(rag_bootstrap.RagBootstrapError, match="active BPM version"):
        rag_bootstrap.provision()


def test_download_checksum_and_cli_failure_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    class Response:
        headers = {"content-length": "2"}

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self, size: int):
            assert size == 1024 * 1024
            yield b"ok"

    class Stream:
        def __enter__(self) -> Response:
            return Response()

        def __exit__(self, *args: object) -> None:
            return None

    class Client:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["follow_redirects"]

        def __enter__(self) -> Client:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def stream(self, method: str, url: str) -> Stream:
            assert method == "GET" and "huggingface.co" in url
            return Stream()

    monkeypatch.setattr(rag_bootstrap.httpx, "Client", Client)
    destination = tmp_path / "download.bin"
    rag_bootstrap.E5ModelInstaller._download(
        destination, "download.bin", hashlib.sha256(b"ok").hexdigest()
    )
    assert destination.read_bytes() == b"ok"
    with pytest.raises(rag_bootstrap.RagBootstrapError, match="checksum"):
        rag_bootstrap.E5ModelInstaller._download(destination, "download.bin", "wrong")
    monkeypatch.setattr(
        rag_bootstrap,
        "provision",
        lambda: (_ for _ in ()).throw(rag_bootstrap.RagBootstrapError("bad")),
    )
    monkeypatch.setattr("sys.argv", ["rag_bootstrap.py", "provision"])
    assert rag_bootstrap.main() == 2
    assert '"state": "failed"' in capsys.readouterr().err


def test_bootstrap_copy_download_import_and_chunk_edge_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"payload")
    copied = tmp_path / "copied.bin"
    rag_bootstrap.E5ModelInstaller._copy(source, copied, "model.bin")
    assert copied.read_bytes() == b"payload"

    class Response:
        headers = {"content-length": "0"}

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self, _: int):
            yield b"payload"

    class Stream:
        def __enter__(self) -> Response:
            return Response()

        def __exit__(self, *_: object) -> bool:
            return False

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        def __enter__(self) -> Client:
            return self

        def __exit__(self, *_: object) -> bool:
            return False

        def stream(self, *_: object, **__: object) -> Stream:
            return Stream()

    monkeypatch.setattr(rag_bootstrap.httpx, "Client", Client)
    downloaded = tmp_path / "downloaded.bin"
    rag_bootstrap.E5ModelInstaller._download(
        downloaded, "model.bin", hashlib.sha256(b"payload").hexdigest()
    )
    assert downloaded.read_bytes() == b"payload"

    installer = rag_bootstrap.E5ModelInstaller(
        tmp_path / "root", source_model_dir=tmp_path / "missing"
    )
    monkeypatch.setattr(
        rag_bootstrap, "MODEL_FILES", {"model.bin": hashlib.sha256(b"payload").hexdigest()}
    )
    monkeypatch.setattr(rag_bootstrap, "MODEL_DIRECTORY_NAME", "model")
    monkeypatch.setattr(rag_bootstrap, "verify_model_directory", lambda _: None)
    monkeypatch.setattr(
        installer,
        "_download",
        lambda destination, *_: destination.write_bytes(b"payload"),
    )
    assert installer.provision().name == "model"

    failing = rag_bootstrap.E5ModelInstaller(
        tmp_path / "failure", source_model_dir=tmp_path / "missing"
    )
    monkeypatch.setattr(
        failing,
        "_download",
        lambda destination, *_: destination.write_bytes(b"wrong"),
    )
    with pytest.raises(rag_bootstrap.RagBootstrapError, match="verification failed"):
        failing.provision()
    assert not failing.model_dir.exists()
    monkeypatch.setattr(rag_bootstrap.os, "spawnv", lambda *_: 0)
    rag_bootstrap._extract_chunks(tmp_path / "chunks.json")
    assert "extracting current six-locale" in capsys.readouterr().out


def test_bootstrap_fingerprints_active_generation_and_cli_ready_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tools = tmp_path / "documentation/tools"
    tools.mkdir(parents=True)
    monkeypatch.setattr(rag_bootstrap, "REPOSITORY_ROOT", tmp_path)
    for relative in (
        "documentation/tools/extract_rag_chunks_0_9_3.py",
        "documentation/config/rag-chunk-extraction-0.9.3.json",
        "documentation/config/rag-corpus-exclusions-0.9.3.json",
        "documentation/tools/generate_chat_rag_exact_generations_0_9_3.py",
        "documentation/config/chat-rag-exact-generation-contract-0.9.3.json",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    build_docs = SimpleNamespace(_source_fingerprint=lambda: "docs")
    generation_module = SimpleNamespace(marker=True)
    monkeypatch.setitem(__import__("sys").modules, "build_docs", build_docs)
    monkeypatch.setitem(
        __import__("sys").modules,
        "generate_chat_rag_exact_generations_0_9_3",
        generation_module,
    )
    assert rag_bootstrap._generation_module() is generation_module
    assert rag_bootstrap._generation_module() is generation_module
    assert len(rag_bootstrap._published_source_fingerprint()) == 64
    assert len(rag_bootstrap._published_source_fingerprint()) == 64

    root = tmp_path / "rag"
    _write_ready_state(root)
    result = rag_bootstrap._active_generation_result(
        root, root / "chunks.json", "fingerprint", "wrong", _Generation
    )
    assert result is None
    _write_ready_state(root)
    pointer = root / "index/active-generation.json"
    pointer.write_text('{"generation_id":"../bad"}', encoding="utf-8")
    assert (
        rag_bootstrap._active_generation_result(
            root, root / "chunks.json", "fingerprint", "0.9.3", _Generation
        )
        is None
    )
    _write_ready_state(root)
    manifest = root / "index/generations/raggen-v1-test/generation-manifest.json"
    manifest.write_text(
        '{"generation_id":"wrong","source_manifest_sha256":"source-manifest"}', encoding="utf-8"
    )
    # The pointer now has a stale checksum, which must stop reuse before inference.
    assert (
        rag_bootstrap._active_generation_result(
            root, root / "chunks.json", "fingerprint", "0.9.3", _Generation
        )
        is None
    )

    monkeypatch.setattr(rag_bootstrap, "provision", lambda: {"generation_id": "ready"})
    monkeypatch.setattr("sys.argv", ["rag_bootstrap.py", "provision"])
    assert rag_bootstrap.main() == 0
    assert '"state": "ready"' in capsys.readouterr().out


def test_bootstrap_remaining_copy_chunk_and_active_generation_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    large = tmp_path / "large.bin"
    large.write_bytes(b"x" * (1024 * 1024 + 1))
    copied = tmp_path / "large-copy.bin"
    rag_bootstrap.E5ModelInstaller._copy(large, copied, "large.bin")
    assert copied.read_bytes() == large.read_bytes()

    class EmptyResponse:
        headers = {"content-length": "0"}

        def raise_for_status(self) -> None:
            return None

        def iter_bytes(self, _: int):
            return iter(())

    class EmptyStream:
        def __enter__(self) -> EmptyResponse:
            return EmptyResponse()

        def __exit__(self, *_: object) -> bool:
            return False

    class EmptyClient:
        def __init__(self, **_: object) -> None:
            pass

        def __enter__(self) -> EmptyClient:
            return self

        def __exit__(self, *_: object) -> bool:
            return False

        def stream(self, *_: object, **__: object) -> EmptyStream:
            return EmptyStream()

    monkeypatch.setattr(rag_bootstrap.httpx, "Client", EmptyClient)
    empty = tmp_path / "empty.bin"
    rag_bootstrap.E5ModelInstaller._download(empty, "empty.bin", hashlib.sha256(b"").hexdigest())
    assert empty.read_bytes() == b""

    class Output:
        def write(self, _: bytes) -> int:
            raise OSError("simulated write failure")

        def close(self) -> None:
            return None

    class Destination:
        def open(self, _: str) -> Output:
            return Output()

        def chmod(self, _: int) -> None:
            return None

    class OneBlockResponse(EmptyResponse):
        def iter_bytes(self, _: int):
            return iter((b"x",))

    class OneBlockStream:
        def __enter__(self) -> OneBlockResponse:
            return OneBlockResponse()

        def __exit__(self, *_: object) -> bool:
            return False

    class OneBlockClient(EmptyClient):
        def stream(self, *_: object, **__: object) -> OneBlockStream:
            return OneBlockStream()

    monkeypatch.setattr(rag_bootstrap.httpx, "Client", OneBlockClient)
    monkeypatch.setattr(rag_bootstrap, "sha256", lambda _: hashlib.sha256(b"").hexdigest())
    with pytest.raises(OSError, match="simulated write failure"):
        rag_bootstrap.E5ModelInstaller._download(
            Destination(), "suppressed.bin", hashlib.sha256(b"").hexdigest()
        )  # type: ignore[arg-type]

    class WorkingOutput:
        def write(self, _: bytes) -> int:
            return 1

        def close(self) -> None:
            return None

    class WorkingDestination(Destination):
        def open(self, _: str) -> WorkingOutput:
            return WorkingOutput()

    rag_bootstrap.E5ModelInstaller._download(
        WorkingDestination(), "working.bin", hashlib.sha256(b"").hexdigest()
    )  # type: ignore[arg-type]

    root = tmp_path / "root"
    source = root / "documentation/source.dita"
    source.parent.mkdir(parents=True)
    source.write_text("source", encoding="utf-8")
    monkeypatch.setattr(rag_bootstrap, "REPOSITORY_ROOT", root)
    for relative in (
        "documentation/tools/extract_rag_chunks_0_9_3.py",
        "documentation/config/rag-chunk-extraction-0.9.3.json",
        "documentation/config/rag-corpus-exclusions-0.9.3.json",
        "documentation/tools/generate_chat_rag_exact_generations_0_9_3.py",
        "documentation/config/chat-rag-exact-generation-contract-0.9.3.json",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    monkeypatch.setitem(
        sys.modules, "build_docs", SimpleNamespace(_source_fingerprint=lambda: "docs")
    )
    tools_root = str(root / "documentation/tools")
    sys.path.insert(0, tools_root)
    try:
        assert len(rag_bootstrap._published_source_fingerprint()) == 64
    finally:
        sys.path.remove(tools_root)
    assert len(rag_bootstrap._published_source_fingerprint()) == 64
    digest = rag_bootstrap._sha256(source)
    assert not rag_bootstrap._chunks_match_current_sources({"chunks": []})
    assert not rag_bootstrap._chunks_match_current_sources({"chunks": ["invalid"]})
    assert not rag_bootstrap._chunks_match_current_sources(
        {
            "chunks": [
                {"source_dita_path": "documentation/source.dita", "source_sha256": digest},
                {"source_dita_path": "documentation/source.dita", "source_sha256": "different"},
            ]
        }
    )
    assert not rag_bootstrap._chunks_match_current_sources(
        {"chunks": [{"source_dita_path": "documentation/missing.dita", "source_sha256": digest}]}
    )

    rag_root = root / "rag"
    _write_ready_state(rag_root)
    chunks_path = rag_root / "chunks.json"
    state_path = rag_root / rag_bootstrap.BOOTSTRAP_STATE_FILE_NAME
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["chunk_manifest_sha256"] = "wrong"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    assert (
        rag_bootstrap._active_generation_result(
            rag_root, chunks_path, "fingerprint", "0.9.3", _Generation
        )
        is None
    )
    _write_ready_state(rag_root)

    class BadConfig(_Generation):
        @staticmethod
        def _read_json(_: Path) -> dict:
            raise ValueError("bad")

    assert (
        rag_bootstrap._active_generation_result(
            rag_root, chunks_path, "fingerprint", "0.9.3", BadConfig
        )
        is None
    )

    class BadValidation(_Generation):
        @staticmethod
        def validate_generation(_: Path, __: dict) -> dict:
            raise ValueError("bad")

    assert (
        rag_bootstrap._active_generation_result(
            rag_root, chunks_path, "fingerprint", "0.9.3", BadValidation
        )
        is None
    )

    class MismatchedManifest(_Generation):
        @staticmethod
        def validate_generation(_: Path, __: dict) -> dict:
            return {"generation_id": "wrong", "source_manifest_sha256": "wrong"}

    assert (
        rag_bootstrap._active_generation_result(
            rag_root, chunks_path, "fingerprint", "0.9.3", MismatchedManifest
        )
        is None
    )
    (rag_root / rag_bootstrap.BOOTSTRAP_STATE_FILE_NAME).unlink()
    assert (
        rag_bootstrap._active_generation_result(
            rag_root, chunks_path, "fingerprint", "0.9.3", _Generation
        )
        is None
    )
