"""Build and atomically activate locale-private E5-base exact-vector generations.

The command consumes a reviewed RAG chunk manifest and an already verified local model directory.
It has no network client, never invokes ordinary search, and writes only ignored generated artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

TOOLS_ROOT = Path(__file__).resolve().parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

try:
    from . import run_embedding_model_benchmark_0_9_3 as embedding
except ImportError:
    import run_embedding_model_benchmark_0_9_3 as embedding


DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/chat-rag-exact-generation-contract-0.9.3.json"
Encode = Callable[[list[str]], np.ndarray]


class GenerationError(RuntimeError):
    """Raised when a generation cannot be safely built or activated."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    candidate.write_bytes(_canonical_json(value))
    os.replace(candidate, path)


def _decision_candidate(config: dict[str, Any]) -> dict[str, Any]:
    decision_entry = config["embedding_decision"]
    decision_path = REPOSITORY_ROOT / decision_entry["path"]
    if _sha256(decision_path) != decision_entry["sha256"]:
        raise GenerationError("embedding decision contract drifted")
    decision = _read_json(decision_path)
    selected = decision["selected_candidate"]
    if selected["id"] != decision_entry["candidate_id"]:
        raise GenerationError("embedding decision selected an unexpected candidate")
    source_path = REPOSITORY_ROOT / selected["source_contract"]
    if _sha256(source_path) != selected["source_contract_sha256"]:
        raise GenerationError("embedding source contract drifted")
    source = _read_json(source_path)
    candidate = embedding._candidate(source, selected["id"])
    if candidate["files"][candidate["artifact"]] != selected["artifact_sha256"]:
        raise GenerationError("selected embedding artifact checksum drifted")
    return candidate


def _validate_storage_decision(config: dict[str, Any]) -> None:
    entry = config["storage_decision"]
    path = REPOSITORY_ROOT / entry["path"]
    if _sha256(path) != entry["sha256"]:
        raise GenerationError("vector-storage decision contract drifted")
    storage = _read_json(path)
    if storage["selected_backend"]["id"] != entry["backend_id"]:
        raise GenerationError("vector-storage backend drifted")


def _compatibility_key(config: dict[str, Any], manifest: dict[str, Any], candidate: dict[str, Any], locale: str) -> dict[str, Any]:
    values = {
        "chunk_schema_version": manifest["chunk_schema_version"],
        "text_normalization_revision": manifest["text_normalization_revision"],
        "embedding_model_id": candidate["model_id"],
        "embedding_model_revision_or_checksum": candidate["files"][candidate["artifact"]],
        "embedding_dimension": candidate["dimension"],
        "embedding_dtype_or_quantization": candidate["quantization"],
        "vector_normalization": config["matrix"]["normalization"],
        "distance_metric": config["matrix"]["distance_metric"],
        "locale": locale,
        "source_manifest_sha256": manifest["source_manifest_sha256"],
        "storage_backend_id": config["storage_decision"]["backend_id"]
    }
    return {name: values[name] for name in config["compatibility_key"]}


def _passage(chunk: dict[str, Any]) -> str:
    return "passage: " + " ".join(chunk["heading_path"]) + "\n" + chunk["text"]


def _validate_chunks(config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    source = config["input"]
    if manifest.get("chunk_schema_version") != source["chunk_schema_version"]:
        raise GenerationError("input is not the required chunk schema")
    if not isinstance(manifest.get("source_manifest_sha256"), str) or len(manifest["source_manifest_sha256"]) != 64:
        raise GenerationError("input manifest lacks its source hash")
    grouped = {locale: [] for locale in source["locales"]}
    for chunk in manifest.get("chunks", []):
        if not set(source["required_chunk_fields"]) <= set(chunk):
            raise GenerationError("input chunk misses required metadata")
        locale = chunk["locale"]
        if locale not in grouped or chunk["publication_state"] != "published":
            raise GenerationError("input chunk has forbidden locale or publication state")
        if not str(chunk["published_url"]).startswith(f"/help/{locale}/"):
            raise GenerationError("input chunk has an unresolved locale citation target")
        grouped[locale].append(chunk)
    if any(not chunks for chunks in grouped.values()):
        raise GenerationError("input does not cover every required locale")
    for locale in grouped:
        grouped[locale].sort(key=lambda chunk: chunk["chunk_id"])
        ids = [chunk["chunk_id"] for chunk in grouped[locale]]
        if len(ids) != len(set(ids)):
            raise GenerationError(f"duplicate chunk ID in {locale}")
    return grouped


def _cache_entry(cache_root: Path, compatibility: dict[str, Any], passage: str) -> tuple[Path, Path]:
    key = hashlib.sha256(_canonical_json(compatibility)).hexdigest()
    input_hash = hashlib.sha256(passage.encode("utf-8")).hexdigest()
    directory = cache_root / key
    return directory / f"{input_hash}.f32", directory / f"{input_hash}.json"


def _read_cached_vector(cache_root: Path, compatibility: dict[str, Any], passage: str, dimension: int) -> np.ndarray | None:
    vector_path, metadata_path = _cache_entry(cache_root, compatibility, passage)
    if not vector_path.is_file() or not metadata_path.is_file() or vector_path.is_symlink() or metadata_path.is_symlink():
        return None
    try:
        metadata = _read_json(metadata_path)
        raw = vector_path.read_bytes()
    except (OSError, json.JSONDecodeError):
        return None
    if (
        metadata.get("compatibility_sha256") != hashlib.sha256(_canonical_json(compatibility)).hexdigest()
        or metadata.get("vector_sha256") != hashlib.sha256(raw).hexdigest()
        or metadata.get("byte_count") != len(raw)
    ):
        return None
    vector = np.frombuffer(raw, dtype="<f4")
    if vector.shape != (dimension,) or not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector), 1.0, atol=1e-4):
        return None
    return vector.copy()


def _write_cached_vector(cache_root: Path, compatibility: dict[str, Any], passage: str, vector: np.ndarray) -> None:
    vector_path, metadata_path = _cache_entry(cache_root, compatibility, passage)
    vector_path.parent.mkdir(parents=True, exist_ok=True)
    raw = np.asarray(vector, dtype="<f4").tobytes(order="C")
    candidate = vector_path.with_name(f".{vector_path.name}.{uuid.uuid4().hex}.tmp")
    candidate.write_bytes(raw)
    os.replace(candidate, vector_path)
    _write_json_atomic(
        metadata_path,
        {
            "byte_count": len(raw),
            "compatibility_sha256": hashlib.sha256(_canonical_json(compatibility)).hexdigest(),
            "vector_sha256": hashlib.sha256(raw).hexdigest()
        },
    )


def _vectors_for_locale(
    chunks: list[dict[str, Any]],
    compatibility: dict[str, Any],
    cache_root: Path,
    dimension: int,
    encode: Encode,
    progress: Callable[[int, int, int], None] | None = None,
) -> tuple[np.ndarray, int]:
    vectors: list[np.ndarray | None] = []
    missing_texts: list[str] = []
    missing_positions: list[int] = []
    for chunk in chunks:
        text = _passage(chunk)
        cached = _read_cached_vector(cache_root, compatibility, text, dimension)
        vectors.append(cached)
        if cached is None:
            missing_texts.append(text)
            missing_positions.append(len(vectors) - 1)
    cache_hits = len(chunks) - len(missing_texts)
    if progress is not None:
        progress(cache_hits, len(chunks), cache_hits)
    if missing_texts:
        for start in range(0, len(missing_texts), 8):
            texts = missing_texts[start : start + 8]
            positions = missing_positions[start : start + 8]
            encoded = np.asarray(encode(texts), dtype="<f4")
            if encoded.shape != (len(texts), dimension):
                raise GenerationError("encoder returned an unexpected vector shape")
            for position, vector, text in zip(positions, encoded, texts, strict=True):
                if not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector), 1.0, atol=1e-4):
                    raise GenerationError("encoder returned a non-normalized vector")
                vectors[position] = vector
                _write_cached_vector(cache_root, compatibility, text, vector)
            if progress is not None:
                progress(cache_hits + start + len(texts), len(chunks), cache_hits)
    return np.vstack([vector for vector in vectors if vector is not None]).astype("<f4", copy=False), len(missing_texts)


def _chunk_metadata(chunks: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    return [{field: chunk[field] for field in fields} for chunk in chunks]


def _write_locale(stage: Path, locale: str, chunks: list[dict[str, Any]], vectors: np.ndarray, compatibility: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    matrix = config["matrix"]
    directory = stage / locale
    directory.mkdir()
    vector_path = directory / matrix["file_name"]
    vector_path.write_bytes(vectors.tobytes(order="C"))
    metadata_path = directory / matrix["metadata_file_name"]
    metadata = {"locale": locale, "chunks": _chunk_metadata(chunks, matrix["metadata_fields"])}
    metadata_path.write_bytes(_canonical_json(metadata))
    manifest_path = directory / matrix["locale_manifest_file_name"]
    locale_manifest = {
        "schema_version": 1,
        "locale": locale,
        "compatibility_key": compatibility,
        "vector_shape": [len(chunks), vectors.shape[1]],
        "vector_dtype": matrix["dtype"],
        "files": {
            matrix["file_name"]: {"byte_count": vector_path.stat().st_size, "sha256": _sha256(vector_path)},
            matrix["metadata_file_name"]: {"byte_count": metadata_path.stat().st_size, "sha256": _sha256(metadata_path)}
        }
    }
    manifest_path.write_bytes(_canonical_json(locale_manifest))
    return {"locale": locale, "manifest_sha256": _sha256(manifest_path), "chunk_count": len(chunks)}


def _generation_id(config: dict[str, Any], manifest: dict[str, Any], locale_entries: list[dict[str, Any]]) -> str:
    identity = {
        "contract_id": config["contract_id"],
        "source_manifest_sha256": manifest["source_manifest_sha256"],
        "locales": locale_entries,
        "backend": config["storage_decision"]["backend_id"]
    }
    return "raggen-v1-" + hashlib.sha256(_canonical_json(identity)).hexdigest()[:20]


def validate_generation(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    matrix = config["matrix"]
    manifest_path = root / matrix["root_manifest_file_name"]
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise GenerationError("generation root manifest is missing or unsafe")
    manifest = _read_json(manifest_path)
    if manifest.get("storage_backend_id") != config["storage_decision"]["backend_id"]:
        raise GenerationError("generation has an unexpected backend")
    expected_locales = config["input"]["locales"]
    if [entry["locale"] for entry in manifest.get("locales", [])] != expected_locales:
        raise GenerationError("generation locale set is incomplete or reordered")
    for entry in manifest["locales"]:
        directory = root / entry["locale"]
        locale_manifest_path = directory / matrix["locale_manifest_file_name"]
        if not directory.is_dir() or directory.is_symlink() or _sha256(locale_manifest_path) != entry["manifest_sha256"]:
            raise GenerationError("generation locale manifest mismatch")
        locale_manifest = _read_json(locale_manifest_path)
        rows, dimension = locale_manifest["vector_shape"]
        if dimension != config["matrix"]["dimension"] or rows != entry["chunk_count"]:
            raise GenerationError("generation matrix shape mismatch")
        compatibility = locale_manifest.get("compatibility_key", {})
        if set(compatibility) != set(config["compatibility_key"]) or compatibility.get("locale") != entry["locale"]:
            raise GenerationError("generation compatibility key mismatch")
        if (
            compatibility.get("embedding_dimension") != config["matrix"]["dimension"]
            or compatibility.get("vector_normalization") != config["matrix"]["normalization"]
            or compatibility.get("distance_metric") != config["matrix"]["distance_metric"]
            or compatibility.get("storage_backend_id") != config["storage_decision"]["backend_id"]
        ):
            raise GenerationError("generation compatibility values drifted")
        for name, expected in locale_manifest["files"].items():
            path = directory / name
            if not path.is_file() or path.is_symlink() or path.stat().st_size != expected["byte_count"] or _sha256(path) != expected["sha256"]:
                raise GenerationError("generation file integrity mismatch")
        if locale_manifest["files"][matrix["file_name"]]["byte_count"] != rows * dimension * 4:
            raise GenerationError("generation vector byte size mismatch")
        metadata = _read_json(directory / matrix["metadata_file_name"])
        chunks = metadata.get("chunks")
        if metadata.get("locale") != entry["locale"] or not isinstance(chunks, list) or len(chunks) != rows:
            raise GenerationError("generation chunk metadata shape mismatch")
        if any(set(chunk) != set(matrix["metadata_fields"]) for chunk in chunks if isinstance(chunk, dict)):
            raise GenerationError("generation chunk metadata fields mismatch")
        if any(not isinstance(chunk, dict) for chunk in chunks):
            raise GenerationError("generation chunk metadata is malformed")
        identifiers = [chunk["chunk_id"] for chunk in chunks]
        if identifiers != sorted(identifiers) or len(identifiers) != len(set(identifiers)):
            raise GenerationError("generation chunk metadata order mismatch")
    return manifest


def build_generation(
    manifest: dict[str, Any], output_root: Path, cache_root: Path, config: dict[str, Any], candidate: dict[str, Any], encode: Encode
) -> dict[str, Any]:
    if output_root.is_symlink() or cache_root.is_symlink():
        raise GenerationError("generation output and cache roots must not be symlinks")
    grouped = _validate_chunks(config, manifest)
    stage = output_root / f".staging-{uuid.uuid4().hex}"
    stage.mkdir(parents=True)
    try:
        locale_entries: list[dict[str, Any]] = []
        cache_misses: dict[str, int] = {}
        for locale in config["input"]["locales"]:
            compatibility = _compatibility_key(config, manifest, candidate, locale)
            last_percent = -1

            def report(completed: int, total: int, cache_hits: int, current_locale: str = locale) -> None:
                nonlocal last_percent
                percent = 100 * completed // total
                if last_percent >= 0 and (
                    percent == last_percent or (percent != 100 and percent < last_percent + config["progress"]["update_percent"])
                ):
                    return
                last_percent = percent
                print(
                    f"RAG exact generation: {current_locale}: {completed}/{total} chunks ({percent}%; "
                    f"cache hits {cache_hits}; embedded {completed - cache_hits})",
                    flush=True,
                )

            vectors, misses = _vectors_for_locale(
                grouped[locale], compatibility, cache_root, config["matrix"]["dimension"], encode, report
            )
            cache_misses[locale] = misses
            locale_entries.append(_write_locale(stage, locale, grouped[locale], vectors, compatibility, config))
            print(
                f"RAG exact generation: {locale}: staging complete ({len(grouped[locale])} chunks; "
                f"cache hits {len(grouped[locale]) - misses}; embedded {misses})",
                flush=True,
            )
        generation_id = _generation_id(config, manifest, locale_entries)
        root_manifest = {
            "schema_version": 1,
            "generation_id": generation_id,
            "storage_backend_id": config["storage_decision"]["backend_id"],
            "source_manifest_sha256": manifest["source_manifest_sha256"],
            "locales": locale_entries,
            "network_calls": 0,
            "ordinary_search_calls": 0
        }
        (stage / config["matrix"]["root_manifest_file_name"]).write_bytes(_canonical_json(root_manifest))
        validate_generation(stage, config)
        generations = output_root / "generations"
        generations.mkdir(parents=True, exist_ok=True)
        final = generations / generation_id
        if final.exists():
            existing = validate_generation(final, config)
            if existing != root_manifest:
                raise GenerationError("immutable generation ID already refers to different content")
            shutil.rmtree(stage)
        else:
            os.replace(stage, final)
        _write_json_atomic(output_root / config["matrix"]["active_pointer_file_name"], {"generation_id": generation_id, "manifest_sha256": _sha256(final / config["matrix"]["root_manifest_file_name"])})
        return {"generation_id": generation_id, "generation_root": str(final), "cache_misses": cache_misses}
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def run(chunks_path: Path, model_dir: Path, output_root: Path, cache_root: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    print("RAG exact generation: verifying local E5-base runtime and model", flush=True)
    config = _read_json(config_path)
    _validate_storage_decision(config)
    candidate = _decision_candidate(config)
    embedding._validate_model_dir(candidate, model_dir)
    manifest = _read_json(chunks_path)
    runtime = config["index_build_runtime"]
    intra_op = os.cpu_count() or 1 if runtime["intra_op_threads"] == "all_available_logical_threads" else runtime["intra_op_threads"]
    benchmark_config = {
        "runtime": {
            "threads": {"intra_op": intra_op, "inter_op": runtime["inter_op_threads"]},
            "maximum_sequence_tokens": runtime["maximum_sequence_tokens"]
        }
    }
    try:
        encode, _ = embedding._encoder(candidate, model_dir, benchmark_config)
    except embedding.BenchmarkError as error:
        raise GenerationError(str(error)) from error
    print("RAG exact generation: verified runtime ready; scanning locale caches", flush=True)
    result = build_generation(manifest, output_root, cache_root, config, candidate, encode)
    result.update({"chunk_manifest_sha256": _sha256(chunks_path), "network_calls": 0, "ordinary_search_calls": 0})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--config", default=CONFIG_PATH, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.chunks, args.model_dir, args.output_root, args.cache_root, args.config)
    except GenerationError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
