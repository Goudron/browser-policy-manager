"""Persistent, progress-reporting development bootstrap for the local chat RAG artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import httpx

from app.ai.e5_runtime import (
    MODEL_DIRECTORY_NAME,
    MODEL_FILES,
    MODEL_REPOSITORY,
    MODEL_REVISION,
    sha256,
    verify_model_directory,
)
from app.core.config import get_settings

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_MODEL_DIR = REPOSITORY_ROOT / "documentation/.cache/bpm093-m5-03/models/e5-base"
BOOTSTRAP_STATE_FILE_NAME = "bootstrap-state.json"


class RagBootstrapError(RuntimeError):
    """A persistent local RAG dependency cannot safely be prepared."""


def _regular(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


class E5ModelInstaller:
    """Install the exact selected E5 files once and never remove a verified installation."""

    def __init__(self, root: Path, *, source_model_dir: Path = DEFAULT_SOURCE_MODEL_DIR) -> None:
        self._root = Path(root)
        self._source_model_dir = Path(source_model_dir)

    @property
    def model_dir(self) -> Path:
        return self._root / MODEL_DIRECTORY_NAME

    def provision(self) -> Path:
        if self.model_dir.exists() or self.model_dir.is_symlink():
            try:
                verify_model_directory(self.model_dir)
            except Exception as error:
                raise RagBootstrapError(
                    "existing E5 installation is invalid; it was not removed"
                ) from error
            print("M12A-02: E5-base: verified persistent installation", flush=True)
            return self.model_dir
        if self._root.is_symlink() or (self._root.exists() and not self._root.is_dir()):
            raise RagBootstrapError("unsafe E5 installation root")
        self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._root.chmod(0o700)
        stage = Path(tempfile.mkdtemp(prefix=".e5-stage-", dir=self._root))
        try:
            for relative, expected in MODEL_FILES.items():
                destination = stage / relative
                destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                source = self._source_model_dir / relative
                if _regular(source) and sha256(source) == expected:
                    self._copy(source, destination, relative)
                else:
                    self._download(destination, relative, expected)
                if sha256(destination) != expected:
                    raise RagBootstrapError(f"E5 verification failed: {relative}")
            os.replace(stage, self.model_dir)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        verify_model_directory(self.model_dir)
        print("M12A-02: E5-base: installed and verified persistently", flush=True)
        return self.model_dir

    @staticmethod
    def _copy(source: Path, destination: Path, relative: str) -> None:
        total = source.stat().st_size
        copied = 0
        print(f"M12A-02: E5-base: {relative}: local verified source ({total} bytes)", flush=True)
        with source.open("rb") as input_file, destination.open("wb") as output_file:
            for block in iter(lambda: input_file.read(1024 * 1024), b""):
                output_file.write(block)
                copied += len(block)
                if copied == total or copied % (64 * 1024 * 1024) < len(block):
                    print(
                        f"M12A-02: E5-base: {relative}: copied {copied}/{total} bytes", flush=True
                    )
        destination.chmod(0o600)

    @staticmethod
    def _download(destination: Path, relative: str, expected: str) -> None:
        url = f"https://huggingface.co/{MODEL_REPOSITORY}/resolve/{MODEL_REVISION}/{relative}"
        print(f"M12A-02: E5-base: {relative}: downloading checksum-pinned artifact", flush=True)
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", "0"))
                copied = 0
                output_file = destination.open("wb")
                try:
                    for block in response.iter_bytes(1024 * 1024):
                        output_file.write(block)
                        copied += len(block)
                        if copied == total or copied % (64 * 1024 * 1024) < len(block):
                            print(
                                f"M12A-02: E5-base: {relative}: downloaded {copied}/{total or '?'} bytes",
                                flush=True,
                            )
                finally:
                    output_file.close()
        destination.chmod(0o600)
        if sha256(destination) != expected:
            raise RagBootstrapError(f"E5 downloaded checksum mismatch: {relative}")


def _extract_chunks(destination: Path) -> None:
    command = [
        sys.executable,
        "documentation/tools/extract_rag_chunks_0_9_3.py",
        "--output",
        str(destination),
    ]
    print("M12A-02: RAG chunks: extracting current six-locale published documentation", flush=True)
    result = os.spawnv(os.P_WAIT, sys.executable, command)
    if result != 0:
        raise RagBootstrapError("RAG chunk extraction failed")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _write_json_atomic(path: Path, value: dict[str, object]) -> None:
    candidate = path.with_name(f".{path.name}.tmp")
    candidate.write_bytes(_canonical_json(value))
    os.replace(candidate, path)


def _generation_module() -> Any:
    tools_root = REPOSITORY_ROOT / "documentation/tools"
    if str(tools_root) not in sys.path:
        sys.path.insert(0, str(tools_root))
    import generate_chat_rag_exact_generations_0_9_3 as generation

    return generation


def _published_source_fingerprint() -> str:
    """Hash the exact source/tool inputs without starting a DITA publication."""

    tools_root = REPOSITORY_ROOT / "documentation/tools"
    if str(tools_root) not in sys.path:
        sys.path.insert(0, str(tools_root))
    import build_docs

    inputs = {
        "published_documentation": build_docs._source_fingerprint(),
        "chunk_extractor": _sha256(
            REPOSITORY_ROOT / "documentation/tools/extract_rag_chunks_0_9_3.py"
        ),
        "chunk_contract": _sha256(
            REPOSITORY_ROOT / "documentation/config/rag-chunk-extraction-0.9.3.json"
        ),
        "corpus_exclusions": _sha256(
            REPOSITORY_ROOT / "documentation/config/rag-corpus-exclusions-0.9.3.json"
        ),
        "generation_tool": _sha256(
            REPOSITORY_ROOT / "documentation/tools/generate_chat_rag_exact_generations_0_9_3.py"
        ),
        "generation_contract": _sha256(
            REPOSITORY_ROOT / "documentation/config/chat-rag-exact-generation-contract-0.9.3.json"
        ),
    }
    return hashlib.sha256(_canonical_json(inputs)).hexdigest()


def _read_regular_json(path: Path) -> dict[str, object] | None:
    if not _regular(path):
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _chunks_match_current_sources(chunks: dict[str, object]) -> bool:
    recorded: dict[str, str] = {}
    raw_chunks = chunks.get("chunks", [])
    if not isinstance(raw_chunks, list):
        return False
    for chunk in raw_chunks:
        if not isinstance(chunk, dict):
            return False
        source_path = chunk.get("source_dita_path")
        source_sha256 = chunk.get("source_sha256")
        if not isinstance(source_path, str) or not isinstance(source_sha256, str):
            return False
        previous = recorded.setdefault(source_path, source_sha256)
        if previous != source_sha256:
            return False
    if not recorded:
        return False
    for source_path, source_sha256 in recorded.items():
        source = (REPOSITORY_ROOT / source_path).resolve()
        try:
            source.relative_to((REPOSITORY_ROOT / "documentation").resolve())
        except ValueError:
            return False
        if not _regular(source) or _sha256(source) != source_sha256:
            return False
    return True


def _active_generation_result(
    rag_root: Path,
    chunks_path: Path,
    fingerprint: str,
    bpm_version: str,
    generation: Any,
) -> dict[str, object] | None:
    """Return a verified active generation only when its exact source state is unchanged."""

    state = _read_regular_json(rag_root / BOOTSTRAP_STATE_FILE_NAME)
    chunks = _read_regular_json(chunks_path)
    if chunks is None:
        return None
    state_data = state if state is not None else {}
    legacy_adoption = state is None
    if state is None and not _chunks_match_current_sources(chunks):
        return None
    if state_data.get("source_fingerprint") != fingerprint and not legacy_adoption:
        return None
    if chunks.get("bpm_version") != bpm_version:
        return None
    if not legacy_adoption and state_data.get("chunk_manifest_sha256") != _sha256(chunks_path):
        return None

    try:
        config = generation._read_json(generation.CONFIG_PATH)
        generation._validate_storage_decision(config)
        generation._decision_candidate(config)
    except OSError, ValueError, generation.GenerationError:
        return None

    pointer = _read_regular_json(rag_root / "index" / config["matrix"]["active_pointer_file_name"])
    pointer_data = pointer if pointer is not None else {}
    generation_id = pointer_data.get("generation_id")
    if not isinstance(generation_id, str) or "/" in generation_id or "\\" in generation_id:
        return None
    generation_root = rag_root / "index" / "generations" / generation_id
    root_manifest_path = generation_root / config["matrix"]["root_manifest_file_name"]
    if (
        not _regular(root_manifest_path)
        or pointer_data.get("manifest_sha256") != _sha256(root_manifest_path)
        or (not legacy_adoption and state_data.get("generation_id") != generation_id)
        or (
            not legacy_adoption
            and state_data.get("generation_manifest_sha256") != _sha256(root_manifest_path)
        )
    ):
        return None
    try:
        manifest = generation.validate_generation(generation_root, config)
    except OSError, ValueError, generation.GenerationError:
        return None
    if manifest.get("generation_id") != generation_id or manifest.get(
        "source_manifest_sha256"
    ) != chunks.get("source_manifest_sha256"):
        return None
    return {
        "generation_id": generation_id,
        "generation_root": str(generation_root),
        "chunk_manifest_sha256": _sha256(chunks_path),
        "cache_misses": {locale: 0 for locale in config["input"]["locales"]},
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "legacy_adoption": legacy_adoption,
    }


def _write_bootstrap_state(
    rag_root: Path,
    chunks_path: Path,
    fingerprint: str,
    result: dict[str, object],
    generation: Any,
) -> None:
    generation_root = Path(str(result["generation_root"]))
    root_manifest = (
        generation_root
        / generation._read_json(generation.CONFIG_PATH)["matrix"]["root_manifest_file_name"]
    )
    _write_json_atomic(
        rag_root / BOOTSTRAP_STATE_FILE_NAME,
        {
            "schema_version": 1,
            "source_fingerprint": fingerprint,
            "chunk_manifest_sha256": _sha256(chunks_path),
            "generation_id": result["generation_id"],
            "generation_manifest_sha256": _sha256(root_manifest),
        },
    )


def provision() -> dict[str, object]:
    settings = get_settings()
    ai_root = settings.DATA_DIR / "ai"
    model_dir = E5ModelInstaller(ai_root / "embeddings").provision()
    rag_root = ai_root / "rag"
    rag_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    generation = _generation_module()
    fingerprint = _published_source_fingerprint()
    chunks_path = rag_root / "chunks.json"
    active = _active_generation_result(
        rag_root, chunks_path, fingerprint, settings.APP_VERSION, generation
    )
    if active is not None:
        if active.pop("legacy_adoption"):
            _write_bootstrap_state(rag_root, chunks_path, fingerprint, active, generation)
            action = "adopted verified existing active generation "
        else:
            action = "retained verified active generation "
        print(
            "M12A-02: RAG index: " + action + str(active["generation_id"]),
            flush=True,
        )
        return active
    chunks_stage = rag_root / ".chunks-next.json"
    _extract_chunks(chunks_stage)
    chunks = json.loads(chunks_stage.read_text(encoding="utf-8"))
    if chunks.get("bpm_version") != settings.APP_VERSION:
        raise RagBootstrapError("RAG chunks do not match the active BPM version")
    os.replace(chunks_stage, chunks_path)
    print("M12A-02: RAG index: building or verifying six locale generations", flush=True)
    result = generation.run(
        chunks_path,
        model_dir,
        rag_root / "index",
        rag_root / "embedding-cache",
    )
    _write_bootstrap_state(rag_root, chunks_path, fingerprint, result, generation)
    print(
        "M12A-02: RAG index: active generation " + str(result["generation_id"]),
        flush=True,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("provision",))
    parser.parse_args()
    try:
        result = provision()
    except (OSError, ValueError, RagBootstrapError) as error:
        print(json.dumps({"state": "failed", "reason_code": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps({"state": "ready", **result}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
