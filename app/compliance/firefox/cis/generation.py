from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.compliance.firefox.cis.validation import BASE_DIR, find_benchmark, load_yaml_file
from app.core.policy_validation import (
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS

GENERATED_DIR = BASE_DIR / "generated"


@dataclass(frozen=True)
class GeneratedCisLayer:
    benchmark_id: str
    upstream_version: str
    level: int
    schema_channel: str
    recommendation_ids: tuple[str, ...]
    policies: dict[str, Any]

    def to_document(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "upstream_version": self.upstream_version,
            "level": self.level,
            "schema_channel": self.schema_channel,
            "recommendation_ids": list(self.recommendation_ids),
            "policies": self.policies,
        }


def build_cis_layer(
    level: int,
    schema_channel: str,
    *,
    base_dir: Path = BASE_DIR,
    benchmark_id: str | None = None,
    upstream_version: str | None = None,
) -> GeneratedCisLayer:
    if level not in {1, 2}:
        raise ValueError("CIS level must be 1 or 2")

    resolved_benchmark_id = benchmark_id or "cis-firefox-esr-gpo"
    benchmark_entry = find_benchmark(
        resolved_benchmark_id,
        upstream_version=upstream_version,
        base_dir=base_dir,
    )
    if benchmark_entry is None:
        raise ValueError(f"Unknown CIS benchmark {resolved_benchmark_id!r}")

    source_file = benchmark_entry.get("source_file") or "firefox_esr_gpo_1_0_0.yaml"
    mapping_file = benchmark_entry.get("mapping_file") or "mappings.yaml"

    source = load_yaml_file(base_dir / source_file)
    mappings_doc = load_yaml_file(base_dir / mapping_file)
    benchmark = source.get("benchmark", {})
    recommendations = source.get("recommendations", [])
    mappings = mappings_doc.get("mappings", [])

    included_ids = {
        recommendation_id
        for recommendation in recommendations
        if isinstance(recommendation, dict)
        and recommendation.get("level") in set(range(1, level + 1))
        and isinstance((recommendation_id := recommendation.get("id")), str)
    }
    mappings_by_id = {
        mapping.get("recommendation_id"): mapping
        for mapping in mappings
        if isinstance(mapping, dict)
    }

    policies: dict[str, Any] = {}
    applied_ids: list[str] = []
    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            continue
        recommendation_id = recommendation.get("id")
        if not isinstance(recommendation_id, str):
            continue
        if recommendation_id not in included_ids:
            continue
        mapping = mappings_by_id.get(recommendation_id)
        if not mapping:
            continue

        applied = False
        for target in mapping.get("targets") or []:
            if not _target_supports_channel(target, schema_channel):
                continue
            _apply_target(policies, target)
            applied = True
        if applied:
            applied_ids.append(recommendation_id)

    layer = GeneratedCisLayer(
        benchmark_id=str(benchmark.get("id", mappings_doc.get("benchmark_id", ""))),
        upstream_version=str(benchmark.get("upstream_version", mappings_doc.get("upstream_version", ""))),
        level=level,
        schema_channel=schema_channel,
        recommendation_ids=tuple(applied_ids),
        policies=policies,
    )
    validate_cis_layer(layer)
    return layer


def build_all_cis_layers(
    *,
    base_dir: Path = BASE_DIR,
    schema_channels: tuple[str, ...] = SUPPORTED_SCHEMA_CHANNELS,
    benchmark_id: str | None = None,
    upstream_version: str | None = None,
) -> list[GeneratedCisLayer]:
    return [
        build_cis_layer(
            level,
            schema_channel,
            base_dir=base_dir,
            benchmark_id=benchmark_id,
            upstream_version=upstream_version,
        )
        for schema_channel in schema_channels
        for level in (1, 2)
    ]


def validate_cis_layer(layer: GeneratedCisLayer) -> None:
    schema = load_policy_schema_for_channel(layer.schema_channel)
    validate_profile_policies_or_raise(layer.policies, schema)


def write_generated_layers(
    *,
    base_dir: Path = BASE_DIR,
    output_dir: Path = GENERATED_DIR,
    benchmark_id: str | None = None,
    upstream_version: str | None = None,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for layer in build_all_cis_layers(
        base_dir=base_dir,
        benchmark_id=benchmark_id,
        upstream_version=upstream_version,
    ):
        path = output_dir / f"cis_l{layer.level}.{layer.schema_channel}.json"
        path.write_text(
            json.dumps(layer.to_document(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def _target_supports_channel(target: dict[str, Any], schema_channel: str) -> bool:
    schema_channels = target.get("schema_channels") or {}
    return schema_channels.get(schema_channel) == "valid"


def _apply_target(policies: dict[str, Any], target: dict[str, Any]) -> None:
    kind = target.get("kind")
    path = target.get("path") or []
    value = deepcopy(target.get("value"))
    if kind == "policy":
        _set_nested(policies, path, value)
        return
    if kind == "preference":
        preference_key = path[0]
        policies.setdefault("Preferences", {})[preference_key] = value
        return
    raise ValueError(f"Cannot generate target kind {kind!r}")


def _set_nested(document: dict[str, Any], path: list[str], value: Any) -> None:
    if not path:
        raise ValueError("Cannot apply empty target path")
    current = document
    for part in path[:-1]:
        existing = current.setdefault(part, {})
        if not isinstance(existing, dict):
            raise ValueError(f"Cannot merge nested policy path through scalar at {part!r}")
        current = existing
    current[path[-1]] = value
