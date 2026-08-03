"""Run one checksum-verified compact embedding candidate without network access.

The command deliberately measures one candidate per process.  It can then select a single artifact
from independent reports, so an ONNX allocator from one model cannot inflate another model's RSS.
Downloaded models, output reports, and runtime wheels remain ignored local benchmark artifacts.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

try:
    from . import run_search_relevance_benchmark_0_9_3 as relevance_benchmark
except ImportError:  # Direct script execution keeps documentation/tools on sys.path.
    import run_search_relevance_benchmark_0_9_3 as relevance_benchmark


DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = DOCUMENTATION_ROOT / "config/embedding-model-benchmark-0.9.3.json"
EXCLUSIONS_PATH = DOCUMENTATION_ROOT / "config/rag-corpus-exclusions-0.9.3.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")


class BenchmarkError(RuntimeError):
    """Raised for an unsafe, incomplete, or non-reproducible benchmark input."""


@dataclass(frozen=True)
class RetrievalCase:
    query_id: str
    locale: str
    query: str
    expected_topic_id: str
    query_class: str = "answer_question"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _candidate(config: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    matches = [item for item in config["candidates"] if item["id"] == candidate_id]
    if len(matches) != 1:
        raise BenchmarkError(f"unknown or ambiguous candidate: {candidate_id}")
    return matches[0]


def _retrieval_cases() -> list[RetrievalCase]:
    corpus = _read_json(relevance_benchmark.EVALUATION_CORPUS)
    cases: list[RetrievalCase] = []
    for locale in corpus["locales"]:
        for domain in corpus["domains"]:
            term = domain["terms"][locale][0]
            for ordinal, template in enumerate(corpus["answer_templates"][locale]):
                cases.append(
                    RetrievalCase(
                        query_id=f"{locale}:{domain['id']}:answer:{ordinal}",
                        locale=locale,
                        query=template.format(term=term),
                        expected_topic_id=domain["topic_id"],
                    )
                )
    return cases


def _validate_retrieval_chunk(chunk: dict[str, Any]) -> None:
    policy = _read_json(EXCLUSIONS_PATH)
    allowed = policy["allow"]
    path = str(chunk.get("source_dita_path", ""))
    normalized_path = f"/{path.strip('/')}/"
    if any(fragment in normalized_path for fragment in policy["deny"]["path_fragments"]):
        raise BenchmarkError("chunk manifest contains an excluded retrieval path")
    if not any(path.startswith(prefix) for prefix in allowed["source_path_prefixes"]):
        raise BenchmarkError("chunk manifest contains an unapproved retrieval source")
    if chunk.get("publication_state") != allowed["publication_state"]:
        raise BenchmarkError("chunk manifest contains an unpublished retrieval chunk")
    if chunk.get("provenance_class") not in allowed["provenance_classes"]:
        raise BenchmarkError("chunk manifest contains blocked provenance")
    if not str(chunk.get("published_url", "")).startswith(allowed["published_url_prefix"]):
        raise BenchmarkError("chunk manifest contains an unpublished retrieval URL")


def _cpu_flags() -> set[str]:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        return set()
    match = re.search(r"^flags\s*: (.+)$", cpuinfo.read_text(encoding="utf-8"), re.MULTILINE)
    return set(match.group(1).split()) if match else set()


def _memory_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, value, *_ = line.split()
        values[key.rstrip(":")] = int(value) * 1024
    return {
        "memory_total_bytes": values["MemTotal"],
        "memory_available_bytes": values["MemAvailable"],
        "swap_total_bytes": values["SwapTotal"],
        "swap_used_bytes": values["SwapTotal"] - values["SwapFree"],
    }


def _current_rss_bytes() -> int:
    for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) * 1024
    raise BenchmarkError("VmRSS is unavailable")


class RssSampler:
    def __init__(self, interval_ms: int) -> None:
        self._interval = interval_ms / 1000
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self.samples: list[int] = []

    def __enter__(self) -> RssSampler:
        self._running.set()
        self.samples.append(_current_rss_bytes())
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()
        return self

    def _sample(self) -> None:
        while self._running.is_set():
            time.sleep(self._interval)
            if not self._running.is_set():
                break
            self.samples.append(_current_rss_bytes())

    def __exit__(self, *_: object) -> None:
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=max(1.0, self._interval * 4))
        self.samples.append(_current_rss_bytes())


def _validate_model_dir(candidate: dict[str, Any], model_dir: Path) -> None:
    if not model_dir.is_dir():
        raise BenchmarkError(f"model directory does not exist: {model_dir}")
    for relative, expected_sha256 in candidate["files"].items():
        file_path = model_dir / relative
        if not file_path.is_file():
            raise BenchmarkError(f"candidate artifact is missing: {file_path}")
        actual = _sha256(file_path)
        if actual != expected_sha256:
            raise BenchmarkError(f"candidate artifact SHA-256 mismatch: {relative}: {actual}")


def _directory_bytes(path: Path) -> int:
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def _direct_runtime_bytes(distributions: list[str]) -> int:
    # Distribution metadata gives the direct package contents without charging unrelated benchmark
    # dependencies that happen to share the virtual environment.
    files = {
        Path(importlib.metadata.distribution(distribution).locate_file(file)).resolve()
        for distribution in distributions
        for file in (importlib.metadata.files(distribution) or [])
        if Path(importlib.metadata.distribution(distribution).locate_file(file)).is_file()
    }
    return sum(file.stat().st_size for file in files)


def _import_runtime() -> tuple[Any, Any]:
    os.environ.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "NO_PROXY": "*",
            "http_proxy": "",
            "https_proxy": "",
        }
    )
    try:
        import onnxruntime
        from tokenizers import Tokenizer
    except ImportError as error:
        raise BenchmarkError("install the pinned offline benchmark runtime before measuring") from error
    return onnxruntime, Tokenizer


def _onnx_feeds(encoded: list[Any], input_names: set[str]) -> dict[str, np.ndarray]:
    values = {
        "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
        "attention_mask": np.asarray([item.attention_mask for item in encoded], dtype=np.int64),
        "token_type_ids": np.asarray([item.type_ids for item in encoded], dtype=np.int64),
    }
    required = {"input_ids", "attention_mask"}
    if not required <= input_names:
        raise BenchmarkError(f"unsupported ONNX inputs: {sorted(input_names)}")
    return {name: values[name] for name in input_names if name in values}


def _post_pooling(candidate: dict[str, Any], model_dir: Path) -> tuple[Any, list[str]]:
    post_pooling = candidate.get("post_pooling")
    if post_pooling is None:
        return lambda values: values, []
    if post_pooling.get("kind") != "dense_tanh_safetensors":
        raise BenchmarkError(f"unsupported post-pooling step: {post_pooling}")
    try:
        from safetensors.numpy import load_file
    except ImportError as error:
        raise BenchmarkError("install the pinned safetensors benchmark dependency") from error
    tensors = load_file(str(model_dir / post_pooling["artifact"]))
    weight = tensors[post_pooling["weight_key"]]
    bias = tensors[post_pooling["bias_key"]]
    if weight.shape != (post_pooling["out_features"], post_pooling["in_features"]) or bias.shape != (
        post_pooling["out_features"],
    ):
        raise BenchmarkError("post-pooling tensor shape does not match the benchmark contract")
    return lambda values: np.tanh(values @ weight.T + bias), ["safetensors"]


def _encoder(candidate: dict[str, Any], model_dir: Path, config: dict[str, Any]) -> Any:
    onnxruntime, tokenizer_type = _import_runtime()
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = config["runtime"]["threads"]["intra_op"]
    options.inter_op_num_threads = config["runtime"]["threads"]["inter_op"]
    session = onnxruntime.InferenceSession(
        str(model_dir / candidate["artifact"]),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise BenchmarkError(f"unexpected execution providers: {session.get_providers()}")
    input_names = {input_.name for input_ in session.get_inputs()}
    tokenizer = tokenizer_type.from_file(str(model_dir / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=config["runtime"]["maximum_sequence_tokens"])
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
    post_pooling, extra_distributions = _post_pooling(candidate, model_dir)

    def encode(texts: list[str], batch_size: int = 8) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            encoded = tokenizer.encode_batch(texts[start : start + batch_size])
            feeds = _onnx_feeds(encoded, input_names)
            hidden = session.run(None, feeds)[0]
            mask = feeds["attention_mask"][..., None]
            pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
            transformed = post_pooling(pooled)
            normalized = transformed / np.maximum(np.linalg.norm(transformed, axis=1, keepdims=True), 1e-12)
            vectors.append(normalized.astype(np.float32))
        return np.vstack(vectors)

    return encode, ["onnxruntime", "tokenizers", *extra_distributions]


def _ranked_topic_ids(scores: np.ndarray, chunks: list[dict[str, Any]], top_k: int) -> list[str]:
    result: list[str] = []
    for index in np.argsort(-scores):
        topic_id = chunks[int(index)]["topic_id"]
        if topic_id not in result:
            result.append(topic_id)
        if len(result) == top_k:
            break
    return result


def _rank(position_ids: list[str], expected_topic_id: str) -> int | None:
    return position_ids.index(expected_topic_id) + 1 if expected_topic_id in position_ids else None


def _metrics(ranks: list[int | None]) -> dict[str, float]:
    return {
        "top_1": sum(rank == 1 for rank in ranks) / len(ranks),
        "recall_at_5": sum(bool(rank) for rank in ranks) / len(ranks),
    }


def _nearest_rank_p95_ms(samples_ns: list[int]) -> float:
    if len(samples_ns) != 30:
        raise BenchmarkError(f"expected 30 measured latency samples, got {len(samples_ns)}")
    return sorted(samples_ns)[28] / 1_000_000


def _candidate_status(result: dict[str, Any], config: dict[str, Any]) -> tuple[str, list[str]]:
    failures: list[str] = []
    acceptance = config["acceptance"]
    if not result["validity"]["valid"]:
        failures.extend(result["validity"]["reasons"])
    for locale, metrics in result["per_locale"].items():
        for metric, minimum in acceptance["per_locale"].items():
            metric_name = metric.removesuffix("_min")
            if metrics[metric_name] < minimum:
                failures.append(f"{locale}:{metric_name}")
    if result["cross_language"]["recall_at_5"] < acceptance["cross_language_recall_at_5_min"]:
        failures.append("cross-language:recall_at_5")
    resource = result["resources"]
    if resource["direct_disk_gib"] > acceptance["model_and_direct_runtime_disk_gib_max"]:
        failures.append("resource:direct_disk")
    if resource["peak_rss_gib"] > acceptance["peak_process_rss_gib_max"]:
        failures.append("resource:peak_rss")
    if result["latency"]["p95_ms_max"] > acceptance["embedding_p95_ms_max"]:
        failures.append("latency:p95")
    return ("pass" if not failures else "fail"), failures


def run_candidate(
    candidate_id: str, model_dir: Path, chunks_path: Path, config_path: Path = CONFIG_PATH
) -> dict[str, Any]:
    config = _read_json(config_path)
    candidate = _candidate(config, candidate_id)
    _validate_model_dir(candidate, model_dir)
    missing_features = sorted(set(candidate["required_cpu_features"]) - _cpu_flags())
    if missing_features:
        raise BenchmarkError(f"required CPU features are unavailable: {', '.join(missing_features)}")
    manifest = _read_json(chunks_path)
    chunks = manifest.get("chunks", [])
    if manifest.get("chunk_schema_version") != "rag-chunk-v1" or not chunks:
        raise BenchmarkError("the input must be a non-empty rag-chunk-v1 manifest")
    for chunk in chunks:
        _validate_retrieval_chunk(chunk)
    grouped_chunks = {locale: [chunk for chunk in chunks if chunk["locale"] == locale] for locale in LOCALES}
    if any(not grouped_chunks[locale] for locale in LOCALES):
        raise BenchmarkError("chunk manifest does not cover the exact six locales")
    cases = _retrieval_cases()
    if {case.locale for case in cases} != set(LOCALES):
        raise BenchmarkError("evaluation corpus does not cover the exact six locales")

    memory_before = _memory_snapshot()
    with RssSampler(config["protocol"]["validity"]["rss_sample_interval_ms"]) as sampler:
        encode, runtime_distributions = _encoder(candidate, model_dir, config)
        vectors: dict[str, np.ndarray] = {}
        for locale in LOCALES:
            passages = [
                candidate["prefixes"]["passage"]
                + " ".join(chunk["heading_path"])
                + "\n"
                + chunk["text"]
                for chunk in grouped_chunks[locale]
            ]
            vectors[locale] = encode(passages)
        ranks: dict[str, list[int | None]] = defaultdict(list)
        for locale in LOCALES:
            locale_cases = [case for case in cases if case.locale == locale]
            query_vectors = encode([candidate["prefixes"]["query"] + case.query for case in locale_cases])
            for case, vector in zip(locale_cases, query_vectors, strict=True):
                topic_ids = _ranked_topic_ids(
                    vector @ vectors[locale].T, grouped_chunks[locale], config["inputs"]["top_k"]
                )
                rank = _rank(topic_ids, case.expected_topic_id)
                ranks[locale].append(rank)
        probe = config["inputs"]["cross_language_probe"]
        source_cases = [
            case
            for case in cases
            if case.locale == probe["query_locale"] and case.query_class == probe["query_class"]
        ]
        cross_language_ranks: list[int | None] = []
        cross_queries = encode([candidate["prefixes"]["query"] + case.query for case in source_cases])
        for locale in probe["target_locales"]:
            for case, vector in zip(source_cases, cross_queries, strict=True):
                topic_ids = _ranked_topic_ids(
                    vector @ vectors[locale].T, grouped_chunks[locale], config["inputs"]["top_k"]
                )
                cross_language_ranks.append(_rank(topic_ids, case.expected_topic_id))
        latency: dict[str, float] = {}
        for locale in LOCALES:
            probe_case = next(
                case
                for case in cases
                if case.locale == locale and case.query_class == probe["query_class"]
            )
            query = [candidate["prefixes"]["query"] + probe_case.query]
            for _ in range(config["protocol"]["validity"]["warmup_attempts_per_locale"]):
                encode(query)
            samples = []
            for _ in range(config["protocol"]["validity"]["measured_attempts_per_locale"]):
                started = time.monotonic_ns()
                encode(query)
                samples.append(time.monotonic_ns() - started)
            latency[locale] = _nearest_rank_p95_ms(samples)
        runtime_bytes = _direct_runtime_bytes(runtime_distributions)
    memory_after = _memory_snapshot()
    gc.collect()

    result = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "benchmark_contract_sha256": _sha256(config_path),
        "candidate": {
            key: candidate[key]
            for key in (
                "id",
                "model_id",
                "revision",
                "source",
                "license",
                "dimension",
                "artifact",
                "quantization",
                "required_cpu_features",
                "prefixes",
                "normalization",
                "files",
            )
        },
        "inputs": {
            "chunk_manifest_sha256": _sha256(chunks_path),
            "chunk_count": len(chunks),
            "source_manifest_sha256": manifest["source_manifest_sha256"],
            "evaluation_corpus_sha256": _sha256(relevance_benchmark.EVALUATION_CORPUS),
            "network_calls": 0,
            "network_disabled": True,
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_flags": sorted(_cpu_flags()),
            "memory_before": memory_before,
            "memory_after": memory_after,
        },
        "validity": {"valid": True, "reasons": []},
        "per_locale": {
            locale: _metrics(ranks[locale]) for locale in LOCALES
        },
        "cross_language": {
            "query_locale": probe["query_locale"],
            "target_locales": probe["target_locales"],
            "case_count": len(cross_language_ranks),
            "recall_at_5": sum(bool(rank) for rank in cross_language_ranks) / len(cross_language_ranks),
        },
        "latency": {"p95_ms_by_locale": latency, "p95_ms_max": max(latency.values())},
        "resources": {
            "model_bundle_bytes": _directory_bytes(model_dir),
            "direct_runtime_bytes": runtime_bytes,
            "direct_disk_gib": (_directory_bytes(model_dir) + runtime_bytes) / 1024**3,
            "peak_rss_bytes": max(sampler.samples),
            "peak_rss_gib": max(sampler.samples) / 1024**3,
            "rss_sample_count": len(sampler.samples),
        },
    }
    if memory_before["swap_used_bytes"] != memory_after["swap_used_bytes"]:
        result["validity"] = {"valid": False, "reasons": ["swap-changed-during-measurement"]}
    result["status"], result["failures"] = _candidate_status(result, config)
    return result


def select_reports(paths: list[Path], config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = _read_json(config_path)
    reports = [_read_json(path) for path in paths]
    if {report["candidate"]["id"] for report in reports} != {
        candidate["id"] for candidate in config["candidates"]
    }:
        raise BenchmarkError("selection requires one report for every configured candidate")
    passing = [report for report in reports if report["status"] == "pass"]
    if not passing:
        return {"schema_version": 1, "backlog_item": config["backlog_item"], "status": "fail", "selected": None, "reports": reports}
    def selection_key(report: dict[str, Any]) -> tuple[float, float, float, float, float, float]:
        per_locale = list(report["per_locale"].values())
        return (
            -sum(item["recall_at_5"] for item in per_locale) / len(per_locale),
            -sum(item["top_1"] for item in per_locale) / len(per_locale),
            -report["cross_language"]["recall_at_5"],
            report["resources"]["direct_disk_gib"],
            report["resources"]["peak_rss_gib"],
            report["latency"]["p95_ms_max"],
        )
    ordered = sorted(passing, key=selection_key)
    if len(ordered) > 1 and selection_key(ordered[0]) == selection_key(ordered[1]):
        raise BenchmarkError("selection tie requires a new reviewed criterion")
    return {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "status": "pass",
        "selected": ordered[0]["candidate"],
        "reports": reports,
    }


def _write_json(value: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate")
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--chunks", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--select-report", type=Path, action="append", default=[])
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    try:
        if args.select_report:
            if args.candidate or args.model_dir or args.chunks:
                raise BenchmarkError("selection accepts reports only")
            result = select_reports(args.select_report, args.config)
        else:
            if not args.candidate or not args.model_dir or not args.chunks:
                raise BenchmarkError("candidate, model directory, and chunks are required")
            result = run_candidate(args.candidate, args.model_dir, args.chunks, args.config)
        _write_json(result, args.output)
    except BenchmarkError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
