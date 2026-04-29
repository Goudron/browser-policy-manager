from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNEL_SET

BASE_DIR = Path(__file__).resolve().parent
SOURCES_FILE = BASE_DIR / "sources.yaml"

ALLOWED_MAPPING_STATUSES = frozenset(
    {
        "mapped",
        "preference_mapped",
        "manual",
        "not_applicable",
        "needs_research",
        "deprecated_or_removed",
    }
)
ALLOWED_ASSESSMENTS = frozenset({"automated", "manual", "unknown"})
ALLOWED_TARGET_KINDS = frozenset({"policy", "preference", "manual", "unsupported"})
ALLOWED_CONFIDENCE = frozenset({"high", "medium", "low"})
TARGET_REQUIRED_STATUSES = frozenset({"mapped", "preference_mapped"})


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    summary: dict[str, Any]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_yaml_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    return loaded if loaded is not None else {}


def load_benchmarks(base_dir: Path = BASE_DIR) -> list[dict[str, Any]]:
    sources = load_yaml_file(base_dir / "sources.yaml")
    benchmarks = sources.get("benchmarks", [])
    return benchmarks if isinstance(benchmarks, list) else []


def find_benchmark(
    benchmark_id: str,
    *,
    upstream_version: str | None = None,
    base_dir: Path = BASE_DIR,
) -> dict[str, Any] | None:
    benchmarks = load_benchmarks(base_dir)
    matches = [
        benchmark
        for benchmark in benchmarks
        if isinstance(benchmark, dict) and benchmark.get("id") == benchmark_id
    ]
    if upstream_version is None:
        if len(matches) == 1:
            return matches[0]
        return next(
            (benchmark for benchmark in matches if benchmark.get("is_default")),
            matches[0] if matches else None,
        )
    return next(
        (
            benchmark
            for benchmark in matches
            if str(benchmark.get("upstream_version")) == str(upstream_version)
        ),
        None,
    )


def validate_sources(base_dir: Path = BASE_DIR) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    sources_path = base_dir / "sources.yaml"
    sources = _load_mapping(sources_path, errors, "sources")
    benchmarks = sources.get("benchmarks", [])
    if not isinstance(benchmarks, list):
        errors.append("sources.yaml: benchmarks must be a list")
        benchmarks = []

    benchmark_ids: set[str] = set()
    benchmark_summaries: list[dict[str, Any]] = []

    for index, benchmark in enumerate(benchmarks):
        location = f"sources.yaml: benchmarks[{index}]"
        if not isinstance(benchmark, dict):
            errors.append(f"{location}: benchmark entry must be an object")
            continue

        benchmark_id = _require_string(benchmark, "id", errors, location)
        if benchmark_id:
            if benchmark_id in benchmark_ids:
                errors.append(f"{location}: duplicate benchmark id {benchmark_id!r}")
            benchmark_ids.add(benchmark_id)

        _require_string(benchmark, "upstream_name", errors, location)
        upstream_version = _require_string(benchmark, "upstream_version", errors, location)
        _require_string(benchmark, "release_window", errors, location)
        source_file = _require_string(benchmark, "source_file", errors, location)
        mapping_file = _require_string(benchmark, "mapping_file", errors, location)
        _validate_urlish(benchmark, "benchmark_page_url", errors, location)
        _validate_urlish(benchmark, "public_versions_page_url", errors, location)
        _validate_urlish(benchmark, "official_update_article_url", errors, location, required=False)

        source_data = _load_mapping(base_dir / source_file, errors, source_file) if source_file else {}
        mapping_data = _load_mapping(base_dir / mapping_file, errors, mapping_file) if mapping_file else {}

        source_summary = _validate_recommendations(
            source_file,
            source_data,
            benchmark_id,
            upstream_version,
            errors,
            warnings,
        )
        mapping_summary = _validate_mappings(
            mapping_file,
            mapping_data,
            source_summary["recommendation_ids"],
            source_summary["statuses_by_id"],
            benchmark_id,
            upstream_version,
            errors,
        )

        if source_summary["total"] == 0 and benchmark.get("official_source_status") == "pending":
            warnings.append(
                f"{source_file}: recommendation list is empty while official CIS PDF curation is pending"
            )
        elif source_summary["total"] == 0:
            warnings.append(f"{source_file}: recommendation list is empty")

        benchmark_summaries.append(
            {
                "id": benchmark_id,
                "upstream_version": upstream_version,
                "recommendations": source_summary["total"],
                "mappings": mapping_summary["total"],
                "source_file": source_file,
                "mapping_file": mapping_file,
                "official_source_status": benchmark.get("official_source_status"),
            }
        )

    return ValidationResult(
        errors=tuple(errors),
        warnings=tuple(warnings),
        summary={
            "benchmarks": benchmark_summaries,
            "benchmark_count": len(benchmark_summaries),
        },
    )


def build_coverage_report(base_dir: Path = BASE_DIR) -> dict[str, Any]:
    validation = validate_sources(base_dir)
    sources = load_yaml_file(base_dir / "sources.yaml")
    reports: list[dict[str, Any]] = []

    for benchmark in sources.get("benchmarks", []):
        source_file = benchmark.get("source_file", "")
        mapping_file = benchmark.get("mapping_file", "")
        source_data = load_yaml_file(base_dir / source_file) if source_file else {}
        mapping_data = load_yaml_file(base_dir / mapping_file) if mapping_file else {}

        recommendations = source_data.get("recommendations", [])
        mappings = mapping_data.get("mappings", [])
        status_counts = Counter(
            rec.get("mapping_status", "unknown") for rec in recommendations if isinstance(rec, dict)
        )
        level_counts = Counter(
            f"L{rec.get('level')}" for rec in recommendations if isinstance(rec, dict)
        )
        mapping_status_counts = Counter(
            mapping.get("status", "unknown") for mapping in mappings if isinstance(mapping, dict)
        )
        schema_counts: Counter[str] = Counter()
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            for target in mapping.get("targets") or []:
                if not isinstance(target, dict):
                    continue
                for channel, status in (target.get("schema_channels") or {}).items():
                    schema_counts[f"{channel}:{status}"] += 1

        reports.append(
            {
                "benchmark_id": benchmark.get("id"),
                "upstream_name": benchmark.get("upstream_name"),
                "upstream_version": benchmark.get("upstream_version"),
                "official_source_status": benchmark.get("official_source_status"),
                "total_recommendations": len(recommendations),
                "total_mappings": len(mappings),
                "by_recommendation_status": dict(sorted(status_counts.items())),
                "by_mapping_status": dict(sorted(mapping_status_counts.items())),
                "by_level": dict(sorted(level_counts.items())),
                "schema_compatibility": dict(sorted(schema_counts.items())),
            }
        )

    return {
        "ok": validation.ok,
        "errors": list(validation.errors),
        "warnings": list(validation.warnings),
        "benchmarks": reports,
    }


def format_validation_summary(result: ValidationResult) -> str:
    lines = [
        f"CIS Firefox source validation: {'ok' if result.ok else 'failed'}",
        f"Benchmarks: {result.summary.get('benchmark_count', 0)}",
    ]
    for benchmark in result.summary.get("benchmarks", []):
        lines.append(
            "- {id} v{version}: {recommendations} recommendations, {mappings} mappings "
            "({source_status})".format(
                id=benchmark.get("id"),
                version=benchmark.get("upstream_version"),
                recommendations=benchmark.get("recommendations"),
                mappings=benchmark.get("mappings"),
                source_status=benchmark.get("official_source_status") or "source status unknown",
            )
        )
    if result.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def format_coverage_markdown(report: dict[str, Any]) -> str:
    lines = ["# CIS Firefox Coverage Report", ""]
    for benchmark in report.get("benchmarks", []):
        lines.extend(
            [
                f"## {benchmark.get('upstream_name')} v{benchmark.get('upstream_version')}",
                "",
                f"- Benchmark id: `{benchmark.get('benchmark_id')}`",
                f"- Official source status: `{benchmark.get('official_source_status')}`",
                f"- Total recommendations: {benchmark.get('total_recommendations')}",
                f"- Total mappings: {benchmark.get('total_mappings')}",
                "",
                "### Recommendation Status",
            ]
        )
        lines.extend(_format_counter_lines(benchmark.get("by_recommendation_status", {})))
        lines.extend(["", "### Mapping Status"])
        lines.extend(_format_counter_lines(benchmark.get("by_mapping_status", {})))
        lines.extend(["", "### By Level"])
        lines.extend(_format_counter_lines(benchmark.get("by_level", {})))
        lines.extend(["", "### Schema Compatibility"])
        lines.extend(_format_counter_lines(benchmark.get("schema_compatibility", {})))
        lines.append("")

    if report.get("warnings"):
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.append("")
    if report.get("errors"):
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_counter_lines(counter: dict[str, int]) -> list[str]:
    if not counter:
        return ["- none: 0"]
    return [f"- {key}: {value}" for key, value in sorted(counter.items())]


def _load_mapping(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label}: file does not exist at {path}")
        return {}
    loaded = load_yaml_file(path)
    if not isinstance(loaded, dict):
        errors.append(f"{label}: top-level YAML document must be an object")
        return {}
    return loaded


def _validate_recommendations(
    label: str,
    data: dict[str, Any],
    benchmark_id: str,
    upstream_version: str,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    benchmark = data.get("benchmark", {})
    if not isinstance(benchmark, dict):
        errors.append(f"{label}: benchmark must be an object")
        benchmark = {}
    if benchmark_id and benchmark.get("id") != benchmark_id:
        errors.append(f"{label}: benchmark.id must be {benchmark_id!r}")
    if upstream_version and str(benchmark.get("upstream_version")) != str(upstream_version):
        errors.append(f"{label}: benchmark.upstream_version must be {upstream_version!r}")

    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list):
        errors.append(f"{label}: recommendations must be a list")
        recommendations = []

    recommendation_ids: set[str] = set()
    statuses_by_id: dict[str, str] = {}
    for index, recommendation in enumerate(recommendations):
        location = f"{label}: recommendations[{index}]"
        if not isinstance(recommendation, dict):
            errors.append(f"{location}: recommendation must be an object")
            continue
        rec_id = _require_string(recommendation, "id", errors, location)
        if rec_id:
            if rec_id in recommendation_ids:
                errors.append(f"{location}: duplicate recommendation id {rec_id!r}")
            recommendation_ids.add(rec_id)
        _require_string(recommendation, "title", errors, location)
        _require_string(recommendation, "category", errors, location)
        level = recommendation.get("level")
        if level not in {1, 2}:
            errors.append(f"{location}: level must be 1 or 2")
        assessment = _require_string(recommendation, "assessment", errors, location)
        if assessment and assessment not in ALLOWED_ASSESSMENTS:
            errors.append(f"{location}: unknown assessment {assessment!r}")
        status = _require_string(recommendation, "mapping_status", errors, location)
        if status:
            if status not in ALLOWED_MAPPING_STATUSES:
                errors.append(f"{location}: unknown mapping_status {status!r}")
            if rec_id:
                statuses_by_id[rec_id] = status
        if _has_long_prose(recommendation):
            warnings.append(f"{location}: contains long prose; confirm CIS licensing boundary")

    return {
        "total": len(recommendations),
        "recommendation_ids": recommendation_ids,
        "statuses_by_id": statuses_by_id,
    }


def _validate_mappings(
    label: str,
    data: dict[str, Any],
    recommendation_ids: set[str],
    statuses_by_id: dict[str, str],
    benchmark_id: str,
    upstream_version: str,
    errors: list[str],
) -> dict[str, Any]:
    if benchmark_id and data.get("benchmark_id") != benchmark_id:
        errors.append(f"{label}: benchmark_id must be {benchmark_id!r}")
    if upstream_version and str(data.get("upstream_version")) != str(upstream_version):
        errors.append(f"{label}: upstream_version must be {upstream_version!r}")

    mappings = data.get("mappings", [])
    if not isinstance(mappings, list):
        errors.append(f"{label}: mappings must be a list")
        mappings = []

    mapping_ids: set[str] = set()
    for index, mapping in enumerate(mappings):
        location = f"{label}: mappings[{index}]"
        if not isinstance(mapping, dict):
            errors.append(f"{location}: mapping must be an object")
            continue
        rec_id = _require_string(mapping, "recommendation_id", errors, location)
        if rec_id:
            if rec_id not in recommendation_ids:
                errors.append(f"{location}: unknown recommendation_id {rec_id!r}")
            if rec_id in mapping_ids:
                errors.append(f"{location}: duplicate mapping for recommendation {rec_id!r}")
            mapping_ids.add(rec_id)
        status = _require_string(mapping, "status", errors, location)
        if status:
            if status not in ALLOWED_MAPPING_STATUSES:
                errors.append(f"{location}: unknown status {status!r}")
            if rec_id and rec_id in statuses_by_id and statuses_by_id[rec_id] != status:
                errors.append(
                    f"{location}: status {status!r} does not match recommendation "
                    f"mapping_status {statuses_by_id[rec_id]!r}"
                )
        confidence = _require_string(mapping, "confidence", errors, location)
        if confidence and confidence not in ALLOWED_CONFIDENCE:
            errors.append(f"{location}: unknown confidence {confidence!r}")

        targets = mapping.get("targets") or []
        if status in TARGET_REQUIRED_STATUSES and not targets:
            errors.append(f"{location}: mapped statuses require at least one target")
        if not isinstance(targets, list):
            errors.append(f"{location}: targets must be a list")
            targets = []
        seen_targets: set[tuple[Any, ...]] = set()
        for target_index, target in enumerate(targets):
            target_location = f"{location}: targets[{target_index}]"
            if not isinstance(target, dict):
                errors.append(f"{target_location}: target must be an object")
                continue
            _validate_target(target, target_location, seen_targets, errors)

    missing_mapping_ids = recommendation_ids - mapping_ids
    for rec_id in sorted(missing_mapping_ids):
        errors.append(f"{label}: missing mapping for recommendation {rec_id!r}")

    return {"total": len(mappings)}


def _validate_target(
    target: dict[str, Any],
    location: str,
    seen_targets: set[tuple[Any, ...]],
    errors: list[str],
) -> None:
    kind = _require_string(target, "kind", errors, location)
    if kind and kind not in ALLOWED_TARGET_KINDS:
        errors.append(f"{location}: unknown target kind {kind!r}")

    if kind in {"policy", "preference"}:
        if "value" not in target:
            errors.append(f"{location}: {kind} target requires value")
        path = target.get("path")
        if not isinstance(path, list) or not path or not all(isinstance(part, str) for part in path):
            errors.append(f"{location}: {kind} target path must be a non-empty string list")
        if kind == "preference" and path and len(path) != 1:
            errors.append(f"{location}: preference target path must contain exactly one preference key")

        schema_channels = target.get("schema_channels") or {}
        if not isinstance(schema_channels, dict):
            errors.append(f"{location}: schema_channels must be an object when provided")
        else:
            for channel in schema_channels:
                if channel not in SUPPORTED_SCHEMA_CHANNEL_SET:
                    errors.append(f"{location}: unsupported schema channel {channel!r}")

        signature = (kind, tuple(path or []))
        if signature in seen_targets and not target.get("allow_duplicate"):
            errors.append(f"{location}: duplicate target {signature!r}")
        seen_targets.add(signature)


def _require_string(
    value: dict[str, Any],
    field: str,
    errors: list[str],
    location: str,
) -> str:
    raw = value.get(field)
    if raw is None or raw == "":
        errors.append(f"{location}: missing required field {field!r}")
        return ""
    if not isinstance(raw, str):
        errors.append(f"{location}: field {field!r} must be a string")
        return ""
    return raw


def _validate_urlish(
    value: dict[str, Any],
    field: str,
    errors: list[str],
    location: str,
    *,
    required: bool = True,
) -> None:
    raw = value.get(field)
    if raw in {None, ""}:
        if required:
            errors.append(f"{location}: missing required field {field!r}")
        return
    if not isinstance(raw, str) or not raw.startswith(("https://", "http://")):
        errors.append(f"{location}: field {field!r} must be an HTTP(S) URL")


def _has_long_prose(recommendation: dict[str, Any]) -> bool:
    for field in ("rationale_summary", "remediation_summary"):
        value = recommendation.get(field)
        if isinstance(value, str) and len(value.split()) > 80:
            return True
    return False
