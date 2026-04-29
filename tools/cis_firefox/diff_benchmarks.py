from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.compliance.firefox.cis.validation import BASE_DIR, find_benchmark, load_yaml_file
from app.core.policy_validation import load_policy_schema_for_channel, validate_profile_policies


@dataclass(frozen=True)
class BenchmarkBundle:
    benchmark: dict[str, Any]
    source: dict[str, Any]
    mappings: dict[str, Any]


def _parse_selector(raw: str) -> tuple[str, str | None]:
    if "@" in raw:
        benchmark_id, version = raw.split("@", 1)
        return benchmark_id.strip(), version.strip() or None
    return raw.strip(), None


def _load_bundle(selector: str, base_dir: Path = BASE_DIR) -> BenchmarkBundle:
    benchmark_id, version = _parse_selector(selector)
    benchmark = find_benchmark(benchmark_id, upstream_version=version, base_dir=base_dir)
    if not benchmark:
        raise ValueError(f"Benchmark {selector!r} not found in sources.yaml")
    source_file = benchmark.get("source_file")
    mapping_file = benchmark.get("mapping_file")
    if not source_file or not mapping_file:
        raise ValueError(f"Benchmark {selector!r} missing source_file or mapping_file")
    source = load_yaml_file(base_dir / source_file)
    mappings = load_yaml_file(base_dir / mapping_file)
    return BenchmarkBundle(benchmark=benchmark, source=source, mappings=mappings)


def _index_recommendations(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    recs = source.get("recommendations", [])
    indexed: dict[str, dict[str, Any]] = {}
    for rec in recs:
        if not isinstance(rec, dict):
            continue
        rec_id = str(rec.get("id", "")).strip()
        if rec_id:
            indexed[rec_id] = rec
    return indexed


def _index_mappings(mapping_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mappings = mapping_doc.get("mappings", [])
    indexed: dict[str, dict[str, Any]] = {}
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        rec_id = str(mapping.get("recommendation_id", "")).strip()
        if rec_id:
            indexed[rec_id] = mapping
    return indexed


def _target_signature(target: dict[str, Any]) -> tuple[Any, ...]:
    return (
        target.get("kind"),
        tuple(target.get("path") or []),
        json.dumps(target.get("value"), sort_keys=True, default=str),
        target.get("merge_rule"),
        json.dumps(target.get("schema_channels") or {}, sort_keys=True),
    )


def _diff_recommendation(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    fields = ["title", "level", "assessment", "scored", "category", "mapping_status"]
    changes: dict[str, Any] = {}
    for field in fields:
        if a.get(field) != b.get(field):
            changes[field] = {"from": a.get(field), "to": b.get(field)}
    return changes


def _diff_mapping(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for field in ("status", "confidence"):
        if a.get(field) != b.get(field):
            changes[field] = {"from": a.get(field), "to": b.get(field)}
    a_targets = sorted((_target_signature(t) for t in a.get("targets") or []))
    b_targets = sorted((_target_signature(t) for t in b.get("targets") or []))
    if a_targets != b_targets:
        changes["targets"] = {
            "from": len(a_targets),
            "to": len(b_targets),
        }
    return changes


def _build_policy_from_target(target: dict[str, Any]) -> dict[str, Any] | None:
    kind = target.get("kind")
    path = target.get("path") or []
    value = target.get("value")
    if kind == "policy":
        if not path:
            return None
        root: dict[str, Any] = {}
        current = root
        for part in path[:-1]:
            current = current.setdefault(part, {})
        current[path[-1]] = value
        return root
    if kind == "preference":
        if not path:
            return None
        return {"Preferences": {path[0]: value}}
    return None


def _find_invalid_targets(mapping_doc: dict[str, Any]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    mappings = mapping_doc.get("mappings", [])
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        rec_id = mapping.get("recommendation_id")
        for target in mapping.get("targets") or []:
            if not isinstance(target, dict):
                continue
            schema_channels = target.get("schema_channels") or {}
            for channel, status in schema_channels.items():
                if status != "valid":
                    continue
                policy_doc = _build_policy_from_target(target)
                if not policy_doc:
                    continue
                schema = load_policy_schema_for_channel(channel)
                issues = validate_profile_policies(policy_doc, schema)
                if issues:
                    invalid.append(
                        {
                            "recommendation_id": rec_id,
                            "channel": channel,
                            "path": target.get("path") or [],
                            "issues": [issue.message for issue in issues],
                        }
                    )
    return invalid


def diff_benchmarks(from_bundle: BenchmarkBundle, to_bundle: BenchmarkBundle) -> dict[str, Any]:
    from_recs = _index_recommendations(from_bundle.source)
    to_recs = _index_recommendations(to_bundle.source)
    from_map = _index_mappings(from_bundle.mappings)
    to_map = _index_mappings(to_bundle.mappings)

    from_ids = set(from_recs)
    to_ids = set(to_recs)

    added = sorted(to_ids - from_ids)
    removed = sorted(from_ids - to_ids)
    shared = sorted(from_ids & to_ids)

    rec_changes: dict[str, Any] = {}
    map_changes: dict[str, Any] = {}
    for rec_id in shared:
        rec_diff = _diff_recommendation(from_recs[rec_id], to_recs[rec_id])
        if rec_diff:
            rec_changes[rec_id] = rec_diff
        if rec_id in from_map and rec_id in to_map:
            map_diff = _diff_mapping(from_map[rec_id], to_map[rec_id])
            if map_diff:
                map_changes[rec_id] = map_diff

    return {
        "from": {
            "benchmark_id": from_bundle.benchmark.get("id"),
            "upstream_version": from_bundle.benchmark.get("upstream_version"),
        },
        "to": {
            "benchmark_id": to_bundle.benchmark.get("id"),
            "upstream_version": to_bundle.benchmark.get("upstream_version"),
        },
        "recommendations": {
            "added": added,
            "removed": removed,
            "changed": rec_changes,
        },
        "mappings": {
            "changed": map_changes,
        },
    }


def format_diff_markdown(diff: dict[str, Any], *, max_items: int = 20) -> str:
    lines = [
        "# CIS Firefox Benchmark Diff",
        "",
        "## Summary",
        f"- From: `{diff['from']['benchmark_id']}` v{diff['from']['upstream_version']}",
        f"- To: `{diff['to']['benchmark_id']}` v{diff['to']['upstream_version']}",
        "",
        "### Recommendations",
        f"- Added: {len(diff['recommendations']['added'])}",
        f"- Removed: {len(diff['recommendations']['removed'])}",
        f"- Changed: {len(diff['recommendations']['changed'])}",
        "",
        "### Mappings",
        f"- Changed: {len(diff['mappings']['changed'])}",
        "",
    ]

    def _append_list(label: str, items: list[str]) -> None:
        if not items:
            return
        lines.append(f"#### {label}")
        for rec_id in items[:max_items]:
            lines.append(f"- `{rec_id}`")
        if len(items) > max_items:
            lines.append(f"- ...and {len(items) - max_items} more")
        lines.append("")

    _append_list("Added recommendations", diff["recommendations"]["added"])
    _append_list("Removed recommendations", diff["recommendations"]["removed"])

    if diff["recommendations"]["changed"]:
        lines.append("#### Changed recommendations")
        for rec_id in list(diff["recommendations"]["changed"].keys())[:max_items]:
            lines.append(f"- `{rec_id}`")
        if len(diff["recommendations"]["changed"]) > max_items:
            lines.append(f"- ...and {len(diff['recommendations']['changed']) - max_items} more")
        lines.append("")

    if diff["mappings"]["changed"]:
        lines.append("#### Changed mappings")
        for rec_id in list(diff["mappings"]["changed"].keys())[:max_items]:
            lines.append(f"- `{rec_id}`")
        if len(diff["mappings"]["changed"]) > max_items:
            lines.append(f"- ...and {len(diff['mappings']['changed']) - max_items} more")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff CIS Firefox benchmark versions.")
    parser.add_argument("--from", dest="from_selector", required=True, help="From benchmark id or id@version.")
    parser.add_argument("--to", dest="to_selector", required=True, help="To benchmark id or id@version.")
    parser.add_argument("--json", action="store_true", help="Emit JSON diff.")
    parser.add_argument(
        "--validate-targets",
        action="store_true",
        help="Validate mapping targets against schemas and include invalid targets.",
    )
    args = parser.parse_args()

    try:
        from_bundle = _load_bundle(args.from_selector)
        to_bundle = _load_bundle(args.to_selector)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    diff = diff_benchmarks(from_bundle, to_bundle)
    if args.validate_targets:
        diff["invalid_targets"] = {
            "from": _find_invalid_targets(from_bundle.mappings),
            "to": _find_invalid_targets(to_bundle.mappings),
        }

    if args.json:
        print(json.dumps(diff, indent=2, sort_keys=True))
    else:
        print(format_diff_markdown(diff))
    return 0


if __name__ == "__main__":
    sys.exit(main())
