"""Benchmark checksum-pinned embeddings for same-locale, chat-only RAG evidence retrieval.

This runner never invokes the M4 documentation search, a browser, a listener, a chat model, or a
network provider. It retrieves only published chunks in the active locale and writes ignored local
benchmark reports.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

try:
    from . import run_embedding_model_benchmark_0_9_3 as embedding
    from . import run_search_relevance_benchmark_0_9_3 as relevance
except ImportError:  # Direct execution keeps documentation/tools on sys.path.
    import run_embedding_model_benchmark_0_9_3 as embedding
    import run_search_relevance_benchmark_0_9_3 as relevance


DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = DOCUMENTATION_ROOT / "config/chat-rag-embedding-benchmark-0.9.3.json"
LOCALES = embedding.LOCALES
IDENTIFIER = re.compile(r"\b[A-Za-z][A-Za-z0-9_]*(?:[-:][A-Za-z0-9_.-]+)+\b")


class BenchmarkError(RuntimeError):
    """Raised for incomplete, unsafe, or non-reproducible chat benchmark input."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _candidate(config: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    entries = [entry for entry in config["candidates"] if entry["id"] == candidate_id]
    if len(entries) != 1:
        raise BenchmarkError(f"unknown or ambiguous candidate: {candidate_id}")
    entry = entries[0]
    source_path = DOCUMENTATION_ROOT.parent / entry["source_contract"]
    if _sha256(source_path) != entry["source_contract_sha256"]:
        raise BenchmarkError(f"candidate source contract drifted: {entry['source_contract']}")
    source = _read_json(source_path)
    candidate = embedding._candidate(source, entry["source_candidate_id"])
    if candidate["id"] != entry["id"]:
        raise BenchmarkError("candidate source contract does not resolve the declared candidate")
    return candidate


def _answer_cases() -> list[embedding.RetrievalCase]:
    corpus = _read_json(relevance.EVALUATION_CORPUS)
    citation_topics = {domain["citation_id"]: domain["topic_id"] for domain in corpus["domains"]}
    cases = embedding._retrieval_cases()
    for locale in LOCALES:
        for case_id, query, disposition, citation_id in corpus["boundary_cases"][locale]["dialogue"]:
            if disposition == "answer":
                cases.append(
                    embedding.RetrievalCase(
                        query_id=f"{locale}:dialogue:{case_id}",
                        locale=locale,
                        query=query,
                        expected_topic_id=citation_topics[citation_id],
                        query_class="dialogue_answer",
                    )
                )
    return cases


def _no_evidence_cases() -> dict[str, list[str]]:
    corpus = _read_json(relevance.EVALUATION_CORPUS)
    cases: dict[str, list[str]] = defaultdict(list)
    for locale in LOCALES:
        for _case_id, query, disposition in corpus["boundary_cases"][locale]["search"]:
            if disposition == "abstain":
                cases[locale].append(query)
        for _case_id, query, disposition, _citation in corpus["boundary_cases"][locale]["dialogue"]:
            if disposition == "abstain":
                cases[locale].append(query)
    return dict(cases)


def _metadata_no_evidence(query: str, chunks: list[dict[str, Any]]) -> bool:
    query_identifiers = {match.group(0).casefold() for match in IDENTIFIER.finditer(query)}
    known_identifiers = {
        str(identifier).casefold()
        for chunk in chunks
        for identifier in chunk.get("identifiers", [])
    }
    return bool(query_identifiers) and query_identifiers.isdisjoint(known_identifiers)


def _citation_resolves(chunk: dict[str, Any], locale: str) -> bool:
    return (
        chunk["locale"] == locale
        and bool(chunk.get("topic_id"))
        and str(chunk.get("published_url", "")).startswith(f"/help/{locale}/")
    )


def _metrics(ranks: list[int | None]) -> dict[str, float]:
    return {
        "top_1": sum(rank == 1 for rank in ranks) / len(ranks),
        "evidence_coverage_at_5": sum(bool(rank and rank <= 5) for rank in ranks) / len(ranks),
    }


def _nearest_rank_p95_ms(samples_ns: list[int]) -> float:
    if len(samples_ns) != 30:
        raise BenchmarkError(f"expected 30 measured latency samples, got {len(samples_ns)}")
    return sorted(samples_ns)[28] / 1_000_000


def _candidate_status(report: dict[str, Any], config: dict[str, Any]) -> tuple[str, list[str]]:
    failures: list[str] = []
    acceptance = config["acceptance"]
    if not report["validity"]["valid"]:
        failures.extend(report["validity"]["reasons"])
    for locale, metrics in report["per_locale"].items():
        if metrics["evidence_coverage_at_5"] < acceptance["same_locale_evidence_coverage_at_5_min"]:
            failures.append(f"{locale}:evidence_coverage_at_5")
        if metrics["citation_resolution_rate"] < acceptance["citation_resolution_rate_min"]:
            failures.append(f"{locale}:citation_resolution")
        if metrics["no_evidence_disposition_rate"] < acceptance["no_evidence_disposition_rate_min"]:
            failures.append(f"{locale}:no_evidence_disposition")
    if report["resources"]["direct_disk_gib"] > acceptance["model_and_direct_runtime_disk_gib_max"]:
        failures.append("resource:direct_disk")
    if report["resources"]["peak_rss_gib"] > acceptance["peak_process_rss_gib_max"]:
        failures.append("resource:peak_rss")
    if report["latency"]["p95_ms_max"] > acceptance["chat_retrieval_p95_ms_max"]:
        failures.append("latency:p95")
    return ("pass" if not failures else "fail"), failures


def run_candidate(candidate_id: str, model_dir: Path, chunks_path: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = _read_json(config_path)
    candidate = _candidate(config, candidate_id)
    embedding._validate_model_dir(candidate, model_dir)
    missing_features = sorted(set(candidate["required_cpu_features"]) - embedding._cpu_flags())
    if missing_features:
        raise BenchmarkError(f"required CPU features are unavailable: {', '.join(missing_features)}")
    manifest = _read_json(chunks_path)
    chunks = manifest.get("chunks", [])
    if manifest.get("chunk_schema_version") != "rag-chunk-v1" or not chunks:
        raise BenchmarkError("the input must be a non-empty rag-chunk-v1 manifest")
    for chunk in chunks:
        embedding._validate_retrieval_chunk(chunk)
    grouped = {locale: [chunk for chunk in chunks if chunk["locale"] == locale] for locale in LOCALES}
    if any(not grouped[locale] for locale in LOCALES):
        raise BenchmarkError("chunk manifest does not cover the exact six locales")
    cases = _answer_cases()
    no_evidence = _no_evidence_cases()
    if {case.locale for case in cases} != set(LOCALES) or any(not no_evidence[locale] for locale in LOCALES):
        raise BenchmarkError("chat evaluation corpus does not cover the exact six locales")

    memory_before = embedding._memory_snapshot()
    with embedding.RssSampler(config["protocol"]["validity"]["rss_sample_interval_ms"]) as sampler:
        encode, runtime_distributions = embedding._encoder(candidate, model_dir, config)
        vectors: dict[str, np.ndarray] = {}
        for locale in LOCALES:
            passages = [
                candidate["prefixes"]["passage"] + " ".join(chunk["heading_path"]) + "\n" + chunk["text"]
                for chunk in grouped[locale]
            ]
            vectors[locale] = encode(passages)

        ranks: dict[str, list[int | None]] = defaultdict(list)
        citation_results: dict[str, list[bool]] = defaultdict(list)
        for locale in LOCALES:
            locale_cases = [case for case in cases if case.locale == locale]
            query_vectors = encode([candidate["prefixes"]["query"] + case.query for case in locale_cases])
            for case, vector in zip(locale_cases, query_vectors, strict=True):
                scores = vector @ vectors[locale].T
                topic_ids = embedding._ranked_topic_ids(scores, grouped[locale], config["inputs"]["top_k"])
                rank = embedding._rank(topic_ids, case.expected_topic_id)
                ranks[locale].append(rank)
                citation_results[locale].extend(
                    _citation_resolves(chunk, locale)
                    for chunk in grouped[locale]
                    if chunk["topic_id"] in topic_ids
                )

        no_evidence_results = {
            locale: [_metadata_no_evidence(query, grouped[locale]) for query in no_evidence[locale]]
            for locale in LOCALES
        }
        latency: dict[str, float] = {}
        for locale in LOCALES:
            probe = next(case for case in cases if case.locale == locale)
            query = [candidate["prefixes"]["query"] + probe.query]
            for _ in range(config["protocol"]["validity"]["warmup_attempts_per_locale"]):
                encode(query)
            samples: list[int] = []
            for _ in range(config["protocol"]["validity"]["measured_attempts_per_locale"]):
                started = time.monotonic_ns()
                vector = encode(query)[0]
                _ = embedding._ranked_topic_ids(vector @ vectors[locale].T, grouped[locale], config["inputs"]["top_k"])
                samples.append(time.monotonic_ns() - started)
            latency[locale] = _nearest_rank_p95_ms(samples)
        runtime_bytes = embedding._direct_runtime_bytes(runtime_distributions)
    memory_after = embedding._memory_snapshot()
    gc.collect()

    per_locale = {}
    for locale in LOCALES:
        per_locale[locale] = {
            **_metrics(ranks[locale]),
            "expected_case_count": len(ranks[locale]),
            "citation_resolution_rate": sum(citation_results[locale]) / len(citation_results[locale]),
            "no_evidence_case_count": len(no_evidence_results[locale]),
            "no_evidence_disposition_rate": sum(no_evidence_results[locale]) / len(no_evidence_results[locale]),
        }
    result = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "benchmark_contract_sha256": _sha256(config_path),
        "candidate": candidate,
        "inputs": {
            "chunk_manifest_sha256": _sha256(chunks_path),
            "chunk_count": len(chunks),
            "source_manifest_sha256": manifest["source_manifest_sha256"],
            "evaluation_corpus_sha256": _sha256(relevance.EVALUATION_CORPUS),
            "ordinary_search_calls": 0,
            "cross_locale_retrieval_calls": 0,
            "network_calls": 0,
            "network_disabled": True,
            "answer_generation_invocations": 0
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_flags": sorted(embedding._cpu_flags()),
            "memory_before": memory_before,
            "memory_after": memory_after
        },
        "validity": {"valid": True, "reasons": []},
        "per_locale": per_locale,
        "latency": {"p95_ms_by_locale": latency, "p95_ms_max": max(latency.values())},
        "resources": {
            "model_bundle_bytes": embedding._directory_bytes(model_dir),
            "direct_runtime_bytes": runtime_bytes,
            "direct_disk_gib": (embedding._directory_bytes(model_dir) + runtime_bytes) / 1024**3,
            "peak_rss_bytes": max(sampler.samples),
            "peak_rss_gib": max(sampler.samples) / 1024**3,
            "rss_sample_count": len(sampler.samples)
        }
    }
    if memory_before["swap_used_bytes"] != memory_after["swap_used_bytes"]:
        result["validity"] = {"valid": False, "reasons": ["swap-changed-during-measurement"]}
    result["status"], result["failures"] = _candidate_status(result, config)
    return result


def select_reports(paths: list[Path], config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = _read_json(config_path)
    reports = [_read_json(path) for path in paths]
    expected = {candidate["id"] for candidate in config["candidates"]}
    if {report["candidate"]["id"] for report in reports} != expected:
        raise BenchmarkError("selection requires one report for every configured candidate")
    passing = [report for report in reports if report["status"] == "pass"]
    if not passing:
        return {"schema_version": 1, "backlog_item": config["backlog_item"], "status": "fail", "selected": None, "reports": reports}

    def selection_key(report: dict[str, Any]) -> tuple[float, float, float, float, float]:
        metrics = list(report["per_locale"].values())
        return (
            -sum(item["evidence_coverage_at_5"] for item in metrics) / len(metrics),
            -sum(item["top_1"] for item in metrics) / len(metrics),
            report["resources"]["direct_disk_gib"],
            report["resources"]["peak_rss_gib"],
            report["latency"]["p95_ms_max"]
        )

    ordered = sorted(passing, key=selection_key)
    if len(ordered) > 1 and selection_key(ordered[0]) == selection_key(ordered[1]):
        raise BenchmarkError("selection tie requires a new reviewed criterion")
    return {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "status": "pass",
        "selected": ordered[0]["candidate"],
        "reports": reports
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
