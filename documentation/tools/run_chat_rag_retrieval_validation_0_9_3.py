"""Validate the activated E5-base chat-RAG generation against the reviewed six-locale corpus.

The command loads a checksum-verified local model and drives the production exact retriever.  It
never invokes M4 ordinary search, an HTTP listener, a chat model, a browser, or a network provider.
Its JSON report is an ignored local artifact; progress is written to stdout for interactive runs.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/chat-rag-retrieval-validation-0.9.3.json"
TOOLS_ROOT = Path(__file__).resolve().parent

for import_root in (REPOSITORY_ROOT, TOOLS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import generate_chat_rag_exact_generations_0_9_3 as generation  # noqa: E402
import run_chat_rag_embedding_benchmark_0_9_3 as chat_benchmark  # noqa: E402
import run_embedding_model_benchmark_0_9_3 as embedding  # noqa: E402
import run_search_relevance_benchmark_0_9_3 as relevance  # noqa: E402

from app.documentation.retrieval import ExactLocaleRetriever, RetrievalUnavailable  # noqa: E402


class ValidationError(RuntimeError):
    """Raised when the active local retrieval evidence cannot safely be validated."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid JSON input: {path}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"JSON object required: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _contract(config: dict[str, Any], name: str) -> tuple[Path, dict[str, Any]]:
    entry = config["contracts"][name]
    path = REPOSITORY_ROOT / entry["path"]
    if _sha256(path) != entry["sha256"]:
        raise ValidationError(f"{name} contract drifted")
    return path, _read_json(path)


def _selected_candidate(config: dict[str, Any]) -> dict[str, Any]:
    _path, decision = _contract(config, "embedding_decision")
    expected = config["contracts"]["embedding_decision"]["candidate_id"]
    selected = decision.get("selected_candidate")
    if not isinstance(selected, dict) or selected.get("id") != expected:
        raise ValidationError("unexpected selected embedding candidate")
    source_path = REPOSITORY_ROOT / selected["source_contract"]
    if _sha256(source_path) != selected["source_contract_sha256"]:
        raise ValidationError("selected embedding source contract drifted")
    candidate = embedding._candidate(_read_json(source_path), selected["id"])
    if candidate["model_id"] != selected["model_id"] or candidate["dimension"] != selected["dimension"]:
        raise ValidationError("selected embedding candidate drifted")
    if candidate["files"][candidate["artifact"]] != selected["artifact_sha256"]:
        raise ValidationError("selected embedding artifact drifted")
    return candidate


def _active_generation(index_root: Path, config: dict[str, Any]) -> tuple[str, Path, dict[str, Any], dict[str, Any]]:
    _generation_path, generation_config = _contract(config, "exact_generation")
    if index_root.is_symlink():
        raise ValidationError("active generation root is unsafe")
    pointer_path = index_root / generation_config["matrix"]["active_pointer_file_name"]
    pointer = _read_json(pointer_path)
    generation_id = pointer.get("generation_id")
    expected_manifest_sha = pointer.get("manifest_sha256")
    if not isinstance(generation_id, str) or not isinstance(expected_manifest_sha, str):
        raise ValidationError("active generation pointer is malformed")
    root = index_root / "generations" / generation_id
    manifest_path = root / generation_config["matrix"]["root_manifest_file_name"]
    if root.is_symlink() or not root.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValidationError("active generation is unsafe or incomplete")
    if _sha256(manifest_path) != expected_manifest_sha:
        raise ValidationError("active generation pointer does not match its manifest")
    try:
        manifest = generation.validate_generation(root, generation_config)
    except generation.GenerationError as error:
        raise ValidationError(str(error)) from error
    return generation_id, root, manifest, generation_config


def _source_chunks(chunks_path: Path, config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    manifest = _read_json(chunks_path)
    if manifest.get("chunk_schema_version") != config["inputs"]["chunk_schema"]:
        raise ValidationError("input is not the approved RAG chunk schema")
    chunks = manifest.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValidationError("input chunk manifest is empty")
    locales = config["inputs"]["locales"]
    grouped: dict[str, list[dict[str, Any]]] = {locale: [] for locale in locales}
    for chunk in chunks:
        try:
            embedding._validate_retrieval_chunk(chunk)
        except embedding.BenchmarkError as error:
            raise ValidationError(str(error)) from error
        locale = chunk.get("locale")
        if locale not in grouped:
            raise ValidationError("input chunk has an unsupported locale")
        if chunk.get("documentation_version") != config["target_bpm_version"] or chunk.get("bpm_version") != config["target_bpm_version"]:
            raise ValidationError("input chunk is stale")
        grouped[locale].append(chunk)
    if any(not grouped[locale] for locale in locales):
        raise ValidationError("input chunk manifest does not cover the six supported locales")
    for locale in locales:
        grouped[locale].sort(key=lambda chunk: chunk["chunk_id"])
    return manifest, grouped


def _published_coverage(
    source_manifest: dict[str, Any],
    source_by_locale: dict[str, list[dict[str, Any]]],
    generation_manifest: dict[str, Any],
    generation_root: Path,
    generation_config: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, dict[str, float | int]]:
    if generation_manifest.get("source_manifest_sha256") != source_manifest.get("source_manifest_sha256"):
        raise ValidationError("active generation derives from a different source manifest")
    metadata_fields = generation_config["matrix"]["metadata_fields"]
    locale_entries = {entry["locale"]: entry for entry in generation_manifest["locales"]}
    coverage: dict[str, dict[str, float | int]] = {}
    for locale in config["inputs"]["locales"]:
        source_chunks = source_by_locale[locale]
        metadata = _read_json(generation_root / locale / generation_config["matrix"]["metadata_file_name"])
        generated_chunks = metadata.get("chunks")
        if metadata.get("locale") != locale or not isinstance(generated_chunks, list):
            raise ValidationError(f"{locale}: invalid active chunk metadata")
        expected = [{field: chunk[field] for field in metadata_fields} for chunk in source_chunks]
        if generated_chunks != expected:
            raise ValidationError(f"{locale}: active chunks do not exactly cover reviewed source chunks")
        entry = locale_entries.get(locale)
        if not isinstance(entry, dict) or entry.get("chunk_count") != len(expected):
            raise ValidationError(f"{locale}: active generation count mismatch")
        expected_topics = {chunk["topic_id"] for chunk in source_chunks}
        generated_topics = {chunk["topic_id"] for chunk in generated_chunks}
        if generated_topics != expected_topics:
            raise ValidationError(f"{locale}: active generation topic coverage mismatch")
        coverage[locale] = {
            "published_chunk_count": len(expected),
            "active_chunk_count": len(generated_chunks),
            "published_chunk_coverage_rate": 1.0,
            "published_topic_count": len(expected_topics),
            "active_topic_count": len(generated_topics),
            "published_topic_coverage_rate": 1.0,
        }
    return coverage


def _rank(candidates: tuple[Any, ...], expected_topic_id: str) -> int | None:
    for position, candidate in enumerate(candidates, start=1):
        if candidate.citation.topic_id == expected_topic_id:
            return position
    return None


def _citation_resolves(candidate: Any, locale: str) -> bool:
    citation = candidate.citation
    return (
        citation.source_kind == "local"
        and bool(citation.citation_id)
        and bool(citation.topic_id)
        and bool(citation.anchor_id_or_root)
        and citation.published_url.startswith(f"/help/{locale}/")
        and candidate.documentation_version == "0.9.3"
        and candidate.bpm_version == "0.9.3"
    )


def _p95_ms(samples_ns: list[int], expected_count: int) -> float:
    if len(samples_ns) != expected_count:
        raise ValidationError(f"expected {expected_count} latency samples, got {len(samples_ns)}")
    return sorted(samples_ns)[expected_count - 2] / 1_000_000


def _status(report: dict[str, Any], config: dict[str, Any]) -> tuple[str, list[str]]:
    acceptance = config["acceptance"]
    failures: list[str] = []
    for locale, metrics in report["per_locale"].items():
        for metric, minimum in (
            ("evidence_coverage_at_5", acceptance["same_locale_evidence_coverage_at_5_min"]),
            ("citation_resolution_rate", acceptance["citation_resolution_rate_min"]),
            ("no_evidence_disposition_rate", acceptance["no_evidence_disposition_rate_min"]),
        ):
            if metrics[metric] < minimum:
                failures.append(f"{locale}:{metric}")
        coverage = report["coverage"][locale]
        for metric, minimum in (
            ("published_chunk_coverage_rate", acceptance["published_chunk_coverage_rate_min"]),
            ("published_topic_coverage_rate", acceptance["published_topic_coverage_rate_min"]),
        ):
            if coverage[metric] < minimum:
                failures.append(f"{locale}:{metric}")
        if metrics["reproducible_ranking_rate"] < acceptance["reproducible_ranking_rate_min"]:
            failures.append(f"{locale}:reproducible_ranking")
    resources = report["resources"]
    if resources["model_and_direct_runtime_gib"] > acceptance["model_and_direct_runtime_disk_gib_max"]:
        failures.append("resource:model_and_direct_runtime")
    if resources["active_generation_gib"] > acceptance["active_generation_disk_gib_max"]:
        failures.append("resource:active_generation")
    if resources["peak_rss_gib"] > acceptance["peak_process_rss_gib_max"]:
        failures.append("resource:peak_rss")
    if report["latency"]["p95_ms_max"] > acceptance["chat_retrieval_p95_ms_max"]:
        failures.append("latency:p95")
    return ("pass" if not failures else "fail"), failures


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file() and not item.is_symlink())


def run(index_root: Path, model_dir: Path, chunks_path: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Run the active-generation validation and return a serializable report."""

    print("RAG retrieval validation: verifying pinned contracts and active generation", flush=True)
    config = _read_json(config_path)
    for name in config["contracts"]:
        _contract(config, name)
    corpus_path = REPOSITORY_ROOT / config["inputs"]["evaluation_corpus"]["path"]
    if _sha256(corpus_path) != config["inputs"]["evaluation_corpus"]["sha256"]:
        raise ValidationError("evaluation corpus drifted")
    if relevance.EVALUATION_CORPUS != corpus_path:
        raise ValidationError("evaluation corpus runner path drifted")
    candidate = _selected_candidate(config)
    embedding._validate_model_dir(candidate, model_dir)
    missing_features = sorted(set(candidate["required_cpu_features"]) - embedding._cpu_flags())
    if missing_features:
        raise ValidationError(f"required CPU features are unavailable: {', '.join(missing_features)}")
    generation_id, generation_root, generation_manifest, generation_config = _active_generation(index_root, config)
    source_manifest, source_by_locale = _source_chunks(chunks_path, config)
    coverage = _published_coverage(
        source_manifest, source_by_locale, generation_manifest, generation_root, generation_config, config
    )
    cases = chat_benchmark._answer_cases()
    no_evidence = chat_benchmark._no_evidence_cases()
    locales = config["inputs"]["locales"]
    if {case.locale for case in cases} != set(locales) or any(len(no_evidence[locale]) != 4 for locale in locales):
        raise ValidationError("reviewed evaluation corpus no longer has the required six-locale cases")
    if any(sum(case.locale == locale for case in cases) != config["inputs"]["answer_and_dialogue_cases_per_locale"] for locale in locales):
        raise ValidationError("reviewed answer case count drifted")

    print("RAG retrieval validation: active generation and published coverage verified; loading local E5-base", flush=True)
    runtime_config = {
        "runtime": {
            "threads": config["runtime"]["threads"],
            "maximum_sequence_tokens": config["runtime"]["maximum_sequence_tokens"],
        }
    }
    memory_before = embedding._memory_snapshot()
    with embedding.RssSampler(config["runtime"]["rss_sample_interval_ms"]) as sampler:
        encode, runtime_distributions = embedding._encoder(candidate, model_dir, runtime_config)
        retriever = ExactLocaleRetriever(index_root, bpm_version=config["target_bpm_version"])
        ranks: dict[str, list[int | None]] = defaultdict(list)
        citations: dict[str, list[bool]] = defaultdict(list)
        reproducible: dict[str, list[bool]] = defaultdict(list)
        for locale_index, locale in enumerate(locales, start=1):
            locale_cases = [case for case in cases if case.locale == locale]
            print(
                f"RAG retrieval validation: locale {locale_index}/{len(locales)} {locale}: "
                f"0/{len(locale_cases)} evaluated questions",
                flush=True,
            )
            for case_index, case in enumerate(locale_cases, start=1):
                vector = encode([candidate["prefixes"]["query"] + case.query])[0]
                first = retriever.retrieve(locale=locale, query_vector=vector, limit=config["inputs"]["top_k"])
                second = retriever.retrieve(locale=locale, query_vector=vector, limit=config["inputs"]["top_k"])
                ranks[locale].append(_rank(first.candidates, case.expected_topic_id))
                citations[locale].extend(_citation_resolves(item, locale) for item in first.candidates)
                reproducible[locale].append(
                    [item.chunk_id for item in first.candidates] == [item.chunk_id for item in second.candidates]
                    and [item.score for item in first.candidates] == [item.score for item in second.candidates]
                    and [item.citation for item in first.candidates] == [item.citation for item in second.candidates]
                )
                if case_index % config["progress"]["locale_case_update"] == 0 or case_index == len(locale_cases):
                    print(
                        f"RAG retrieval validation: locale {locale_index}/{len(locales)} {locale}: "
                        f"{case_index}/{len(locale_cases)} evaluated questions",
                        flush=True,
                    )
        no_evidence_results = {
            locale: [chat_benchmark._metadata_no_evidence(query, source_by_locale[locale]) for query in no_evidence[locale]]
            for locale in locales
        }
        latency: dict[str, float] = {}
        attempts = config["runtime"]["measured_attempts_per_locale"]
        for locale_index, locale in enumerate(locales, start=1):
            probe = next(case for case in cases if case.locale == locale)
            text = [candidate["prefixes"]["query"] + probe.query]
            for _ in range(config["runtime"]["warmup_attempts_per_locale"]):
                retriever.retrieve(locale=locale, query_vector=encode(text)[0], limit=config["inputs"]["top_k"])
            samples: list[int] = []
            print(
                f"RAG retrieval validation: latency locale {locale_index}/{len(locales)} {locale}: 0/{attempts} samples",
                flush=True,
            )
            for attempt in range(1, attempts + 1):
                started = time.monotonic_ns()
                retriever.retrieve(locale=locale, query_vector=encode(text)[0], limit=config["inputs"]["top_k"])
                samples.append(time.monotonic_ns() - started)
                if attempt % config["progress"]["latency_sample_update"] == 0 or attempt == attempts:
                    print(
                        f"RAG retrieval validation: latency locale {locale_index}/{len(locales)} {locale}: "
                        f"{attempt}/{attempts} samples",
                        flush=True,
                    )
            latency[locale] = _p95_ms(samples, attempts)
        runtime_bytes = embedding._direct_runtime_bytes(runtime_distributions)
    memory_after = embedding._memory_snapshot()
    gc.collect()

    per_locale = {
        locale: {
            "expected_case_count": len(ranks[locale]),
            "top_1": sum(rank == 1 for rank in ranks[locale]) / len(ranks[locale]),
            "evidence_coverage_at_5": sum(bool(rank and rank <= 5) for rank in ranks[locale]) / len(ranks[locale]),
            "citation_count": len(citations[locale]),
            "citation_resolution_rate": sum(citations[locale]) / len(citations[locale]),
            "no_evidence_case_count": len(no_evidence_results[locale]),
            "no_evidence_disposition_rate": sum(no_evidence_results[locale]) / len(no_evidence_results[locale]),
            "reproducibility_case_count": len(reproducible[locale]),
            "reproducible_ranking_rate": sum(reproducible[locale]) / len(reproducible[locale]),
        }
        for locale in locales
    }
    report = {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "validation_contract_sha256": _sha256(config_path),
        "generation_id": generation_id,
        "contracts": {name: config["contracts"][name] for name in config["contracts"]},
        "inputs": {
            "chunk_manifest_sha256": _sha256(chunks_path),
            "source_manifest_sha256": source_manifest["source_manifest_sha256"],
            "evaluation_corpus_sha256": _sha256(corpus_path),
            "chunk_count": len(source_manifest["chunks"]),
            "ordinary_search_calls": 0,
            "cross_locale_retrieval_calls": 0,
            "network_calls": 0,
            "network_disabled": True,
            "answer_generation_invocations": 0,
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_flags": sorted(embedding._cpu_flags()),
            "memory_before": memory_before,
            "memory_after": memory_after,
            "swap_used_delta_bytes": memory_after["swap_used_bytes"] - memory_before["swap_used_bytes"],
        },
        "coverage": coverage,
        "per_locale": per_locale,
        "latency": {"p95_ms_by_locale": latency, "p95_ms_max": max(latency.values())},
        "resources": {
            "model_bundle_bytes": embedding._directory_bytes(model_dir),
            "direct_runtime_bytes": runtime_bytes,
            "model_and_direct_runtime_gib": (embedding._directory_bytes(model_dir) + runtime_bytes) / 1024**3,
            "active_generation_bytes": _directory_bytes(generation_root),
            "active_generation_gib": _directory_bytes(generation_root) / 1024**3,
            "peak_rss_bytes": max(sampler.samples),
            "peak_rss_gib": max(sampler.samples) / 1024**3,
            "rss_sample_count": len(sampler.samples),
        },
        "integrity": {
            "active_generation_manifest_validated": True,
            "source_manifest_identity_validated": True,
            "published_provenance_validated": True,
            "negative_runtime_tests": config["integrity_and_recovery"]["negative_runtime_tests"],
            "failure_isolation": config["integrity_and_recovery"]["failure_isolation"],
        },
    }
    report["status"], report["failures"] = _status(report, config)
    return report


def _write_report(report: dict[str, Any], output: Path) -> None:
    cache_root = (DOCUMENTATION_ROOT / ".cache").resolve()
    resolved = output.resolve()
    if cache_root not in (resolved, *resolved.parents):
        raise ValidationError("validation output must remain under documentation/.cache")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-root", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    try:
        report = run(args.index_root, args.model_dir, args.chunks, args.config)
        _write_report(report, args.output)
    except (ValidationError, RetrievalUnavailable, embedding.BenchmarkError) as error:
        parser.error(str(error))
    print(
        f"RAG retrieval validation: complete; status={report['status']}; "
        f"report={args.output}",
        flush=True,
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
