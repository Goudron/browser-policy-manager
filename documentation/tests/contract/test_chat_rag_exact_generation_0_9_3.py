from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/chat-rag-exact-generation-contract-0.9.3.json"
RUNNER_PATH = ROOT / "documentation/tools/generate_chat_rag_exact_generations_0_9_3.py"
PROGRESS_PATH = ROOT / "documentation/tools/report_chat_rag_exact_generation_progress_0_9_3.py"

SPEC = importlib.util.spec_from_file_location("chat_rag_exact_generation", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

PROGRESS_SPEC = importlib.util.spec_from_file_location("chat_rag_exact_generation_progress", PROGRESS_PATH)
assert PROGRESS_SPEC and PROGRESS_SPEC.loader
progress_reporter = importlib.util.module_from_spec(PROGRESS_SPEC)
sys.modules[PROGRESS_SPEC.name] = progress_reporter
PROGRESS_SPEC.loader.exec_module(progress_reporter)

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate() -> dict:
    return {
        "model_id": "intfloat/multilingual-e5-base",
        "artifact": "onnx/model_O4.onnx",
        "files": {"onnx/model_O4.onnx": "f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703"},
        "dimension": 768,
        "quantization": "ONNX O4 graph optimization; floating-point weights; no ISA-specific model requirement"
    }


def _manifest(config: dict) -> dict:
    chunks = []
    for ordinal, locale in enumerate(config["input"]["locales"]):
        chunks.append(
            {
                "chunk_id": f"ragc-v1:{locale}:topic-{ordinal}:root:0",
                "locale": locale,
                "topic_id": f"topic-{ordinal}",
                "anchor_id_or_root": "root",
                "ordinal": 0,
                "guide_id": "user-guide",
                "published_url": f"/help/{locale}/user/topic-{ordinal}.html",
                "source_sha256": f"{ordinal:064x}",
                "manifest_sha256": "a" * 64,
                "documentation_version": "0.9.3",
                "bpm_version": "0.9.3",
                "provenance_class": "published",
                "publication_state": "published",
                "heading_path": [f"Topic {ordinal}"],
                "identifiers": [f"ID-{ordinal}"],
                "text": f"Reviewed text for {locale}."
            }
        )
    return {
        "chunk_schema_version": "rag-chunk-v1",
        "text_normalization_revision": "dita-visible-text-v1",
        "source_manifest_sha256": "b" * 64,
        "chunks": chunks
    }


def test_generation_contract_pins_both_decisions_and_exact_matrix_boundary() -> None:
    config = _config()

    assert config["backlog_item"] == "BPM093-M5-05"
    assert config["storage_decision"]["sha256"] == _sha256(ROOT / config["storage_decision"]["path"])
    assert config["embedding_decision"]["sha256"] == _sha256(ROOT / config["embedding_decision"]["path"])
    assert config["matrix"]["dtype"] == "little-endian float32"
    assert config["matrix"]["dimension"] == 768
    assert config["matrix"]["metadata_fields"] == [
        "chunk_id",
        "topic_id",
        "anchor_id_or_root",
        "ordinal",
        "guide_id",
        "published_url",
        "source_sha256",
        "identifiers",
        "documentation_version",
        "bpm_version",
        "provenance_class",
        "heading_path",
        "text",
    ]
    assert config["boundaries"]["ordinary_search_calls"] == 0
    assert config["boundaries"]["cross_locale_vectors"] == "forbidden"
    assert config["index_build_runtime"]["intra_op_threads"] == "all_available_logical_threads"
    assert config["index_build_runtime"]["swap"] == "permitted"
    assert config["progress"] == {
        "stream": "stdout",
        "update_percent": 5,
        "flush": True,
        "content": "real runtime preparation, locale-local chunk completion, cache hits, and newly embedded vectors; no synthetic progress or ETA",
    }
    assert "does not fine-tune model weights" in config["boundaries"]["resource_policy"]


def test_generation_is_locale_private_atomic_and_reuses_verified_cache(tmp_path: Path) -> None:
    config = _config()
    manifest = _manifest(config)
    calls: list[list[str]] = []

    def encode(texts: list[str]) -> np.ndarray:
        calls.append(texts)
        vectors = np.zeros((len(texts), 768), dtype=np.float32)
        vectors[:, 0] = 1.0
        return vectors

    output_root = tmp_path / "output"
    cache_root = tmp_path / "cache"
    first = runner.build_generation(manifest, output_root, cache_root, config, _candidate(), encode)
    assert sum(first["cache_misses"].values()) == 6
    assert len(calls) == 6
    pointer = json.loads((output_root / config["matrix"]["active_pointer_file_name"]).read_text(encoding="utf-8"))
    assert pointer["generation_id"] == first["generation_id"]
    root = Path(first["generation_root"])
    generation = runner.validate_generation(root, config)
    assert [entry["locale"] for entry in generation["locales"]] == config["input"]["locales"]
    assert not root.is_symlink()

    calls.clear()
    second = runner.build_generation(manifest, output_root, cache_root, config, _candidate(), encode)
    assert second["generation_id"] == first["generation_id"]
    assert sum(second["cache_misses"].values()) == 0
    assert calls == []


def test_generation_integrity_rejects_tampered_vectors(tmp_path: Path) -> None:
    config = _config()

    def encode(texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), 768), dtype=np.float32)
        vectors[:, 0] = 1.0
        return vectors

    result = runner.build_generation(_manifest(config), tmp_path / "output", tmp_path / "cache", config, _candidate(), encode)
    vectors = Path(result["generation_root"]) / "en" / config["matrix"]["file_name"]
    vectors.write_bytes(b"tampered")
    with pytest.raises(runner.GenerationError, match="integrity mismatch"):
        runner.validate_generation(Path(result["generation_root"]), config)


def test_generation_integrity_rejects_tampered_chunk_metadata(tmp_path: Path) -> None:
    config = _config()

    def encode(texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), 768), dtype=np.float32)
        vectors[:, 0] = 1.0
        return vectors

    result = runner.build_generation(_manifest(config), tmp_path / "output", tmp_path / "cache", config, _candidate(), encode)
    metadata_path = Path(result["generation_root"]) / "en" / config["matrix"]["metadata_file_name"]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["chunks"][0]["bpm_version"] = "stale"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(runner.GenerationError, match="integrity mismatch"):
        runner.validate_generation(Path(result["generation_root"]), config)


def test_progress_reports_cache_staging_and_never_writes(tmp_path: Path) -> None:
    config = _config()
    manifest = _manifest(config)
    output_root = tmp_path / "output"
    cache_root = tmp_path / "cache"

    def encode(texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), 768), dtype=np.float32)
        vectors[:, 0] = 1.0
        return vectors

    runner.build_generation(manifest, output_root, cache_root, config, _candidate(), encode)
    chunks_path = tmp_path / "chunks.json"
    chunks_path.write_text(json.dumps(manifest), encoding="utf-8")
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    snapshot = progress_reporter.progress(chunks_path, output_root, cache_root, config_path=CONFIG_PATH)
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert snapshot["state"] == "activated"
    assert snapshot["locales_complete"] == 6
    assert snapshot["cached_vectors"] == snapshot["total_vectors"] == 6
    assert all(entry["state"] == "complete" for entry in snapshot["locales"])
    assert before == after


def test_generation_emits_real_flushed_chunk_progress(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = _config()

    def encode(texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), 768), dtype=np.float32)
        vectors[:, 0] = 1.0
        return vectors

    runner.build_generation(_manifest(config), tmp_path / "output", tmp_path / "cache", config, _candidate(), encode)
    output = capsys.readouterr().out
    assert "RAG exact generation: en: 0/1 chunks (0%; cache hits 0; embedded 0)" in output
    assert "RAG exact generation: en: 1/1 chunks (100%; cache hits 0; embedded 1)" in output
    assert "RAG exact generation: es-ES: staging complete" in output
