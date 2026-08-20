"""Semantic drift guards for the catalog-owned Firefox schema lifecycle.

The guard deliberately reads structured owners instead of recursively grepping
the repository.  Historical/migration literals are recorded in the adjacent
owner map and never become alternate active catalog sources.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from app.compliance.firefox.cis.generation import build_all_cis_layers
from app.compliance.firefox.cis.validation import load_yaml_file
from app.core.locales import ACTIVE_CATALOG_LOCALES
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG

REPO_ROOT = Path(__file__).resolve().parents[3]
OWNER_MAP_PATH = REPO_ROOT / "tests/fixtures/schema_lifecycle_drift_guard_owner_map_0_9_5.json"
_CHANNEL_LITERAL = re.compile(r"\b(?:esr-\d+(?:\.\d+)?|release-\d+)\b")


class SchemaLifecycleDriftError(AssertionError):
    """One derived owner no longer agrees with the lifecycle catalog."""


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SchemaLifecycleDriftError(f"JSON owner must be an object: {path}")
    return payload


def _owner_map() -> dict[str, Any]:
    return _read_json(OWNER_MAP_PATH)


def _active_paths(owner_map: Mapping[str, Any]) -> dict[str, Path]:
    surfaces = owner_map.get("active_surfaces")
    if not isinstance(surfaces, dict):
        raise SchemaLifecycleDriftError("owner map active surfaces are malformed")
    result: dict[str, Path] = {}
    for name, relative_path in surfaces.items():
        if not isinstance(name, str) or not isinstance(relative_path, str):
            raise SchemaLifecycleDriftError("owner map active surface is malformed")
        path = REPO_ROOT / relative_path
        if not path.is_file():
            raise SchemaLifecycleDriftError(f"active owner is missing: {relative_path}")
        result[name] = path
    return result


def _rows_by_artifact(rows: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        artifact_id = row.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise SchemaLifecycleDriftError("catalog row has no exact artifact ID")
        if artifact_id in result:
            raise SchemaLifecycleDriftError(f"duplicate catalog artifact ID: {artifact_id}")
        result[artifact_id] = row
    return result


def _validate_catalog_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    by_artifact = _rows_by_artifact(rows)
    by_line: dict[str, Mapping[str, Any]] = {}
    latest_esr: list[Mapping[str, Any]] = []
    product_defaults: list[Mapping[str, Any]] = []
    default_releases: list[Mapping[str, Any]] = []
    esr_rows: list[Mapping[str, Any]] = []

    for row in by_artifact.values():
        line_id = row.get("line_id")
        roles = row.get("roles")
        support = row.get("support")
        if not isinstance(line_id, str) or line_id in by_line:
            raise SchemaLifecycleDriftError("catalog line IDs must be unique")
        if not isinstance(roles, Mapping) or not isinstance(support, Mapping):
            raise SchemaLifecycleDriftError(f"catalog roles/support are malformed: {line_id}")
        by_line[line_id] = row
        if roles.get("latest_esr") is True:
            latest_esr.append(row)
        if roles.get("product_default") is True:
            product_defaults.append(row)
        if roles.get("default_release") is True:
            default_releases.append(row)
        if row.get("family") == "esr":
            esr_rows.append(row)

    if len(latest_esr) != 1 or len(product_defaults) != 1:
        raise SchemaLifecycleDriftError(
            "catalog must have exactly one latest ESR and product default"
        )
    if latest_esr != product_defaults:
        raise SchemaLifecycleDriftError("product default must be the latest ESR")
    if len(default_releases) != 1 or default_releases[0].get("family") != "release":
        raise SchemaLifecycleDriftError("catalog must have exactly one default Release")

    for row in esr_rows:
        line_number = row.get("line_number")
        successor_line_id = row.get("retirement_successor_line_id")
        if not isinstance(line_number, int):
            raise SchemaLifecycleDriftError("ESR line number is malformed")
        newer = sorted(
            (
                candidate
                for candidate in esr_rows
                if isinstance(candidate.get("line_number"), int)
                and candidate["line_number"] > line_number
            ),
            key=lambda candidate: candidate["line_number"],
        )
        expected = newer[0].get("line_id") if newer else None
        if successor_line_id != expected:
            raise SchemaLifecycleDriftError(
                f"retirement successor drift for {row['line_id']}: "
                f"expected {expected!r}, got {successor_line_id!r}"
            )
        if successor_line_id is not None:
            successor = by_line.get(successor_line_id)
            if (
                successor is None
                or successor.get("family") != "esr"
                or successor.get("selectable") is not True
                or successor.get("support", {}).get("state") != "supported"
            ):
                raise SchemaLifecycleDriftError(
                    f"retirement successor is not a supported selectable ESR: {successor_line_id}"
                )
    return by_artifact


def _validate_targets(
    rows: Iterable[Mapping[str, Any]],
    targets_document: Mapping[str, Any],
    inputs_document: Mapping[str, Any],
) -> None:
    by_artifact = _validate_catalog_rows(rows)
    targets = targets_document.get("targets")
    inputs = inputs_document.get("inputs")
    if not isinstance(targets, list) or not isinstance(inputs, list):
        raise SchemaLifecycleDriftError("target or input manifest is malformed")
    targets_by_channel = {
        target.get("channel"): target for target in targets if isinstance(target, dict)
    }
    if set(targets_by_channel) != set(by_artifact):
        raise SchemaLifecycleDriftError("schema target artifacts do not exactly match the catalog")
    inputs_by_tag = {item.get("source_tag"): item for item in inputs if isinstance(item, dict)}
    for artifact_id, row in by_artifact.items():
        source = row.get("source")
        target = targets_by_channel[artifact_id]
        if not isinstance(source, Mapping):
            raise SchemaLifecycleDriftError(f"catalog source is malformed: {artifact_id}")
        expected = {
            "artifact_id": artifact_id,
            "line_id": row.get("line_id"),
            "version": row.get("artifact_version"),
            "source_tag": source.get("source_tag"),
            "documentation_input": source["documentation_input"]["local_path"],
            "linux_policies_input": source["linux_policies_input"]["local_path"],
            "output": source.get("output_path"),
            "ui_label": row.get("label"),
        }
        if {key: target.get(key) for key in expected} != expected:
            raise SchemaLifecycleDriftError(f"stale target identity for {artifact_id}")
        input_spec = inputs_by_tag.get(source.get("source_tag"))
        if not isinstance(input_spec, Mapping) or input_spec.get("upstream_tag") != source.get(
            "upstream_tag"
        ):
            raise SchemaLifecycleDriftError(f"source tag is missing or stale for {artifact_id}")


def _validate_runtime_and_bundles(rows: Iterable[Mapping[str, Any]]) -> None:
    by_artifact = _validate_catalog_rows(rows)
    runtime = {channel.artifact_id: channel for channel in SCHEMA_CHANNEL_CATALOG}
    if set(runtime) != set(by_artifact):
        raise SchemaLifecycleDriftError("runtime catalog does not exactly match lifecycle contract")
    for artifact_id, row in by_artifact.items():
        source = row["source"]
        channel = runtime[artifact_id]
        if (
            channel.line_id != row["line_id"]
            or channel.label != row["label"]
            or channel.i18n_key != row["i18n_key"]
            or channel.source_tag != source["source_tag"]
            or channel.source.output_path != source["output_path"]
        ):
            raise SchemaLifecycleDriftError(f"runtime channel metadata is stale: {artifact_id}")
        bundle_path = REPO_ROOT / source["output_path"]
        bundle = _read_json(bundle_path)
        if (
            bundle.get("x-bpm-channel") != artifact_id
            or bundle.get("x-bpm-source") != source["source_tag"]
            or bundle.get("x-bpm-ui-label") != row["label"]
        ):
            raise SchemaLifecycleDriftError(f"bundle label or source tag is stale: {artifact_id}")


def _validate_conversion_pairs(
    rows: Iterable[Mapping[str, Any]], contract: Mapping[str, Any]
) -> None:
    by_artifact = _validate_catalog_rows(rows)
    artifact_ids = tuple(
        row["artifact_id"]
        for row in sorted(
            by_artifact.values(),
            key=lambda row: (
                {"release": 0, "esr": 1}.get(row.get("family"), 2),
                -int(row.get("line_number", -1)),
                tuple(-int(part) for part in str(row.get("artifact_version", "")).split(".")),
                str(row["artifact_id"]),
            ),
        )
    )
    expected = {
        f"{source}--to--{target}"
        for source in artifact_ids
        for target in artifact_ids
        if source != target
    }
    pairs = contract.get("pair_matrix")
    if not isinstance(pairs, list):
        raise SchemaLifecycleDriftError("conversion pair matrix is malformed")
    actual = {pair.get("pair_id") for pair in pairs if isinstance(pair, Mapping)}
    if actual != expected or len(pairs) != len(expected):
        raise SchemaLifecycleDriftError("conversion pair matrix is incomplete")
    for pair in pairs:
        if not isinstance(pair, Mapping):
            raise SchemaLifecycleDriftError("conversion pair is malformed")
        source = pair.get("source_artifact_id")
        target = pair.get("target_artifact_id")
        if source not in by_artifact or target not in by_artifact:
            raise SchemaLifecycleDriftError("conversion pair names an undeclared artifact")
        if pair.get("source_line_id") != by_artifact[source].get("line_id") or pair.get(
            "target_line_id"
        ) != by_artifact[target].get("line_id"):
            raise SchemaLifecycleDriftError(
                f"conversion pair line identity is stale: {pair.get('pair_id')}"
            )


def _validate_locales_and_cis(
    rows: Iterable[Mapping[str, Any]], mappings: Mapping[str, Any]
) -> None:
    by_artifact = _validate_catalog_rows(rows)
    labels = {row["i18n_key"] for row in by_artifact.values()}
    for locale in ACTIVE_CATALOG_LOCALES:
        source_catalog = _read_json(REPO_ROOT / "app/i18n_src" / locale / "common.json")
        runtime_catalog = _read_json(REPO_ROOT / "app/i18n" / f"{locale}.json")
        missing = {
            key
            for key in labels
            if not isinstance(source_catalog.get(key), str) or not source_catalog[key].strip()
        }
        if missing:
            raise SchemaLifecycleDriftError(
                f"locale source misses catalog labels: {locale}:{sorted(missing)}"
            )
        missing_runtime = {
            key
            for key in labels
            if not isinstance(runtime_catalog.get(key), str) or not runtime_catalog[key].strip()
        }
        if missing_runtime:
            raise SchemaLifecycleDriftError(
                f"runtime locale misses catalog labels: {locale}:{sorted(missing_runtime)}"
            )

    target_channels = set(by_artifact)
    mapping_rows = mappings.get("mappings")
    if not isinstance(mapping_rows, list):
        raise SchemaLifecycleDriftError("CIS mappings are malformed")
    for mapping in mapping_rows:
        if not isinstance(mapping, Mapping):
            continue
        for target in mapping.get("targets") or []:
            if not isinstance(target, Mapping):
                continue
            statuses = target.get("schema_channels")
            if isinstance(statuses, Mapping) and set(statuses) != target_channels:
                raise SchemaLifecycleDriftError("CIS target omits an active schema channel")
    expected_layers = {(level, artifact) for level in (1, 2) for artifact in target_channels}
    actual_layers = {(layer.level, layer.schema_channel) for layer in build_all_cis_layers()}
    if actual_layers != expected_layers:
        raise SchemaLifecycleDriftError("generated CIS layers omit an active schema channel")


def _validate_documentation_inventory(
    rows: Iterable[Mapping[str, Any]], inventory: Mapping[str, Any]
) -> None:
    by_artifact = _validate_catalog_rows(rows)
    channels = inventory.get("channels")
    policies = inventory.get("policies")
    if not isinstance(channels, Mapping) or not isinstance(policies, list):
        raise SchemaLifecycleDriftError("policy documentation/help inventory is malformed")
    if set(channels) != set(by_artifact):
        raise SchemaLifecycleDriftError(
            "policy documentation/help inventory omits an active channel"
        )
    for artifact_id, row in by_artifact.items():
        entry = channels[artifact_id]
        source = row["source"]
        if not isinstance(entry, Mapping) or (
            entry.get("filename") != source["filename"]
            or entry.get("schema_source") != source["source_tag"]
            or entry.get("schema_version") != row["artifact_version"]
        ):
            raise SchemaLifecycleDriftError(f"documentation channel source is stale: {artifact_id}")
    for policy in policies:
        if not isinstance(policy, Mapping):
            raise SchemaLifecycleDriftError("policy documentation/help entry is malformed")
        if not isinstance(policy.get("ui_target"), str) or not policy["ui_target"].startswith(
            "policy:"
        ):
            raise SchemaLifecycleDriftError("policy documentation/help target is missing")
        declared = policy.get("channels")
        if not isinstance(declared, Mapping) or not set(declared).issubset(by_artifact):
            raise SchemaLifecycleDriftError(
                "policy documentation/help target has an undeclared channel"
            )


def _validate_cis_documentation_inventory(
    rows: Iterable[Mapping[str, Any]], inventory: Mapping[str, Any]
) -> None:
    expected = {(level, artifact) for level in (1, 2) for artifact in _validate_catalog_rows(rows)}
    layers = inventory.get("generated_layers")
    if not isinstance(layers, list):
        raise SchemaLifecycleDriftError("CIS documentation inventory is malformed")
    actual = {
        (layer.get("level"), layer.get("schema_channel"))
        for layer in layers
        if isinstance(layer, Mapping)
    }
    if actual != expected or len(layers) != len(expected):
        raise SchemaLifecycleDriftError("CIS documentation inventory omits an active channel")


def _validate_active_literals(owner_map: Mapping[str, Any], artifact_ids: set[str]) -> None:
    paths = owner_map.get("literal_scan_files")
    if not isinstance(paths, list):
        raise SchemaLifecycleDriftError("literal scan owner list is malformed")
    for relative_path in paths:
        if not isinstance(relative_path, str):
            raise SchemaLifecycleDriftError("literal scan path is malformed")
        values = set(
            _CHANNEL_LITERAL.findall((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
        )
        unknown = values - artifact_ids
        if unknown:
            raise SchemaLifecycleDriftError(
                f"undeclared active channel literal in {relative_path}: {sorted(unknown)}"
            )


def test_active_schema_surfaces_are_catalog_derived_and_complete() -> None:
    owner_map = _owner_map()
    paths = _active_paths(owner_map)
    lifecycle = _read_json(paths["lifecycle_contract"])
    rows = lifecycle["channels"]
    assert isinstance(rows, list)
    _validate_catalog_rows(rows)
    _validate_targets(
        rows, _read_json(paths["schema_targets"]), _read_json(paths["input_manifest"])
    )
    _validate_runtime_and_bundles(rows)
    _validate_conversion_pairs(rows, _read_json(paths["conversion_contract"]))
    _validate_locales_and_cis(rows, load_yaml_file(paths["cis_mappings"]))
    _validate_documentation_inventory(rows, _read_json(paths["policy_documentation_inventory"]))
    _validate_cis_documentation_inventory(rows, _read_json(paths["cis_documentation_inventory"]))
    _validate_active_literals(owner_map, set(_rows_by_artifact(rows)))


def test_historical_and_migration_literal_exceptions_are_explicit_and_bounded() -> None:
    owner_map = _owner_map()
    exceptions = owner_map["historical_or_migration_literal_exceptions"]
    assert isinstance(exceptions, list)
    active_paths = {str(path.relative_to(REPO_ROOT)) for path in _active_paths(owner_map).values()}
    for relative_path in exceptions:
        assert isinstance(relative_path, str)
        assert relative_path not in active_paths
        assert relative_path.startswith("alembic/") or relative_path.startswith(
            "docs/architecture/"
        )
        assert (REPO_ROOT / relative_path).is_file()


def test_partial_future_bump_and_derived_surface_mutations_fail_at_the_owner_layer() -> None:
    paths = _active_paths(_owner_map())
    lifecycle = _read_json(paths["lifecycle_contract"])
    rows = lifecycle["channels"]
    assert isinstance(rows, list)

    partial_bump = copy.deepcopy(rows)
    promoted = next(row for row in partial_bump if row["line_id"] == "esr-153")
    promoted["roles"]["latest_esr"] = False
    promoted["roles"]["product_default"] = False
    future = copy.deepcopy(promoted)
    future.update(
        {
            "line_id": "esr-166",
            "artifact_id": "esr-166.0",
            "channel_id": "esr-166.0",
            "line_number": 166,
            "artifact_version": "166.0",
            "label": "ESR 166.0",
            "i18n_key": "profiles.firefox_schema_esr_166_0",
            "retirement_successor_line_id": None,
        }
    )
    future["roles"] = {"latest_esr": True, "product_default": True, "default_release": False}
    partial_bump.append(future)
    with pytest.raises(SchemaLifecycleDriftError, match="retirement successor drift"):
        _validate_catalog_rows(partial_bump)

    stale_target_document = copy.deepcopy(_read_json(paths["schema_targets"]))
    stale_target_document["targets"][0]["ui_label"] = "stale label"
    with pytest.raises(SchemaLifecycleDriftError, match="stale target identity"):
        _validate_targets(rows, stale_target_document, _read_json(paths["input_manifest"]))

    missing_source_document = copy.deepcopy(_read_json(paths["input_manifest"]))
    missing_source_document["inputs"] = [
        entry
        for entry in missing_source_document["inputs"]
        if entry["source_tag"] != "mozilla-policy-templates-v5.12"
    ]
    with pytest.raises(SchemaLifecycleDriftError, match="source tag is missing or stale"):
        _validate_targets(rows, _read_json(paths["schema_targets"]), missing_source_document)

    missing_pair_contract = copy.deepcopy(_read_json(paths["conversion_contract"]))
    missing_pair_contract["pair_matrix"].pop()
    with pytest.raises(SchemaLifecycleDriftError, match="pair matrix is incomplete"):
        _validate_conversion_pairs(rows, missing_pair_contract)

    locale_rows = copy.deepcopy(rows)
    locale_rows[0]["i18n_key"] = "profiles.firefox_schema_missing"
    with pytest.raises(SchemaLifecycleDriftError, match="locale source misses catalog labels"):
        _validate_locales_and_cis(locale_rows, load_yaml_file(paths["cis_mappings"]))

    cis_mappings = copy.deepcopy(load_yaml_file(paths["cis_mappings"]))
    first_target = next(
        target
        for mapping in cis_mappings["mappings"]
        for target in mapping.get("targets") or []
        if isinstance(target, dict) and isinstance(target.get("schema_channels"), dict)
    )
    first_target["schema_channels"].pop("esr-115.39")
    with pytest.raises(SchemaLifecycleDriftError, match="CIS target omits"):
        _validate_locales_and_cis(rows, cis_mappings)

    inventory = copy.deepcopy(_read_json(paths["policy_documentation_inventory"]))
    inventory["channels"].pop("esr-115.39")
    with pytest.raises(SchemaLifecycleDriftError, match="documentation/help inventory omits"):
        _validate_documentation_inventory(rows, inventory)

    missing_help_target = copy.deepcopy(_read_json(paths["policy_documentation_inventory"]))
    missing_help_target["policies"][0]["ui_target"] = ""
    with pytest.raises(SchemaLifecycleDriftError, match="documentation/help target is missing"):
        _validate_documentation_inventory(rows, missing_help_target)

    cis_inventory = copy.deepcopy(_read_json(paths["cis_documentation_inventory"]))
    cis_inventory["generated_layers"].pop()
    with pytest.raises(SchemaLifecycleDriftError, match="CIS documentation inventory omits"):
        _validate_cis_documentation_inventory(rows, cis_inventory)

    literal_owner_map = copy.deepcopy(_owner_map())
    literal_owner_map["literal_scan_files"] = []
    literal_owner_map["literal_scan_files"].append(
        "tests/contract/schema/test_schema_lifecycle_drift_guards.py"
    )
    with pytest.raises(SchemaLifecycleDriftError, match="undeclared active channel literal"):
        _validate_active_literals(literal_owner_map, {"release-153"})
