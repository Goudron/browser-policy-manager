"""Compare exact locale-private float32 scan with a supplied sqlite-vec extension.

The tool uses deterministic synthetic normalized E5-base-shaped vectors, never reads product
content, invokes no model or ordinary search, opens no listener, and writes only an ignored report.
It is selection evidence for storage behaviour, not a product index builder.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = DOCUMENTATION_ROOT / "config/chat-rag-vector-storage-decision-0.9.3.json"


class BenchmarkError(RuntimeError):
    """Raised for an unavailable or unverifiable benchmark dependency or result."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _p95_ms(samples_ns: list[int]) -> float:
    if len(samples_ns) != 30:
        raise BenchmarkError(f"expected 30 latency samples, received {len(samples_ns)}")
    return sorted(samples_ns)[28] / 1_000_000


def _normalized_vectors(count: int, dimension: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vectors = rng.standard_normal((count, dimension), dtype=np.float32)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors.astype("<f4", copy=False)


def _dataset(config: dict[str, Any], multiplier: int) -> dict[str, np.ndarray]:
    counts = {"en": 397, "ru": 424, "de": 434, "zh-CN": 302, "fr": 427, "es-ES": 417}
    if sum(counts.values()) != config["corpus_scope"]["current_chunk_count"]:
        raise BenchmarkError("current corpus count drifted")
    dimension = config["embedding_decision"]["dimension"]
    return {
        locale: _normalized_vectors(count * multiplier, dimension, 9304 + ordinal)
        for ordinal, (locale, count) in enumerate(counts.items())
    }


def _queries(vectors: dict[str, np.ndarray]) -> dict[str, list[np.ndarray]]:
    return {
        locale: [matrix[(index * 17 + 3) % len(matrix)] for index in range(30)]
        for locale, matrix in vectors.items()
    }


def _exact_top_k(matrix: np.ndarray, query: np.ndarray, top_k: int) -> list[int]:
    scores = matrix @ query
    candidate_ids = np.argpartition(-scores, top_k - 1)[:top_k]
    return [int(index) for index in candidate_ids[np.argsort(-scores[candidate_ids], kind="stable")]]


def _exact_measure(vectors: dict[str, np.ndarray], queries: dict[str, list[np.ndarray]], top_k: int) -> dict[str, Any]:
    result: dict[str, Any] = {"top_k": {}, "p95_ms_by_locale": {}}
    for locale, matrix in vectors.items():
        samples: list[int] = []
        answers: list[list[int]] = []
        for query in queries[locale]:
            started = time.monotonic_ns()
            answers.append(_exact_top_k(matrix, query, top_k))
            samples.append(time.monotonic_ns() - started)
        result["top_k"][locale] = answers
        result["p95_ms_by_locale"][locale] = _p95_ms(samples)
    return result


def _load_sqlite_vec(config: dict[str, Any]) -> Any:
    try:
        sqlite_vec = importlib.import_module("sqlite_vec")
    except ModuleNotFoundError as error:
        raise BenchmarkError("sqlite-vec must be supplied through an isolated PYTHONPATH") from error
    candidate = config["rejected_candidates"][0]["observed_package"]
    if getattr(sqlite_vec, "__version__", None) != candidate["distribution"].split("==", 1)[1]:
        raise BenchmarkError("sqlite-vec distribution version drifted")
    extension = Path(sqlite_vec.loadable_path())
    if not extension.is_file() and extension.with_suffix(".so").is_file():
        extension = extension.with_suffix(".so")
    if _sha256(extension) != candidate["linux_x86_64_extension_sha256"]:
        raise BenchmarkError("sqlite-vec extension checksum drifted")
    return sqlite_vec


def _sqlite_measure(
    vectors: dict[str, np.ndarray], queries: dict[str, list[np.ndarray]], top_k: int, sqlite_vec: Any, root: Path
) -> tuple[dict[str, Any], int]:
    database_path = root / "sqlite-vec.db"
    connection = sqlite3.connect(database_path)
    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    tables: dict[str, str] = {}
    for ordinal, (locale, matrix) in enumerate(vectors.items()):
        table = f"vectors_{ordinal}"
        tables[locale] = table
        connection.execute(f"CREATE VIRTUAL TABLE {table} USING vec0(vector float[{matrix.shape[1]}])")
        connection.executemany(
            f"INSERT INTO {table}(rowid, vector) VALUES (?, ?)",
            ((index + 1, sqlite_vec.serialize_float32(vector)) for index, vector in enumerate(matrix)),
        )
    connection.commit()
    result: dict[str, Any] = {"top_k": {}, "p95_ms_by_locale": {}}
    for locale, locale_queries in queries.items():
        samples: list[int] = []
        answers: list[list[int]] = []
        for query in locale_queries:
            started = time.monotonic_ns()
            rows = connection.execute(
                f"SELECT rowid FROM {tables[locale]} WHERE vector MATCH ? ORDER BY distance LIMIT ?",
                (sqlite_vec.serialize_float32(query), top_k),
            ).fetchall()
            answers.append([int(row[0]) - 1 for row in rows])
            samples.append(time.monotonic_ns() - started)
        result["top_k"][locale] = answers
        result["p95_ms_by_locale"][locale] = _p95_ms(samples)
    connection.close()
    return result, database_path.stat().st_size


def _matrix_bytes(vectors: dict[str, np.ndarray]) -> int:
    return sum(matrix.nbytes for matrix in vectors.values())


def run(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = _read_json(config_path)
    sqlite_vec = _load_sqlite_vec(config)
    output: dict[str, Any] = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "contract_sha256": _sha256(config_path),
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "scales": {}
    }
    for scale_name, multiplier in (("current", 1), ("growth_10x", config["corpus_scope"]["growth_multiplier"])):
        vectors = _dataset(config, multiplier)
        queries = _queries(vectors)
        exact = _exact_measure(vectors, queries, config["corpus_scope"]["top_k"])
        with tempfile.TemporaryDirectory(prefix="bpm093-m5-04-") as temporary:
            sqlite_result, sqlite_bytes = _sqlite_measure(
                vectors, queries, config["corpus_scope"]["top_k"], sqlite_vec, Path(temporary)
            )
        same_results = exact["top_k"] == sqlite_result["top_k"]
        if not same_results:
            raise BenchmarkError(f"exact and sqlite-vec top-k diverged at {scale_name}")
        output["scales"][scale_name] = {
            "chunk_count": sum(len(matrix) for matrix in vectors.values()),
            "locale_private": True,
            "same_ordered_top_k": same_results,
            "exact_matrix": {
                "vector_bytes": _matrix_bytes(vectors),
                "p95_ms_by_locale": exact["p95_ms_by_locale"],
                "p95_ms_max": max(exact["p95_ms_by_locale"].values())
            },
            "sqlite_vec": {
                "database_bytes": sqlite_bytes,
                "p95_ms_by_locale": sqlite_result["p95_ms_by_locale"],
                "p95_ms_max": max(sqlite_result["p95_ms_by_locale"].values())
            }
        }
    growth = output["scales"]["growth_10x"]
    output["acceptance"] = {
        "correct": all(scale["same_ordered_top_k"] for scale in output["scales"].values()),
        "exact_latency": growth["exact_matrix"]["p95_ms_max"] <= config["acceptance"]["latency_p95_ms_max"],
        "exact_disk": growth["exact_matrix"]["vector_bytes"] / 1024**3 <= config["acceptance"]["disk_gib_max_at_growth"]
    }
    output["status"] = "pass" if all(output["acceptance"].values()) else "fail"
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config", default=CONFIG_PATH, type=Path)
    args = parser.parse_args()
    try:
        report = run(args.config)
    except BenchmarkError as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
