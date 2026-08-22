#!/usr/bin/env python3
"""Run the offline four-channel Firefox schema release gate.

The gate is deliberately an owner command rather than a collection of ad-hoc
test invocations.  It consumes only the checksum-verified local policy-template
cache, regenerates every bundled schema in two isolated roots, and emits a
deterministic terminal report that can be retained with release evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, NoReturn
from unittest.mock import patch

import jsonschema

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.core.schema_channels as schema_channels
from app.compliance.firefox.cis.generation import (
    build_cis_layer,
    cis_layer_availability,
)
from app.core.locales import ACTIVE_CATALOG_LOCALES
from app.core.policy_validation import (
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise_for_channel,
)
from app.core.schema_channels import (
    DEFAULT_SCHEMA_CHANNEL,
    HEADER_SCHEMA_CHANNEL_VALUES,
    LATEST_ESR_SCHEMA_CHANNEL,
    SCHEMA_FILENAMES,
    SUPPORTED_SCHEMA_CHANNELS,
    RetiredSchemaChannelError,
    UnbundledSchemaChannelError,
    UnknownSchemaChannelError,
    build_schema_channels_catalog,
    get_schema_channel,
    require_supported_schema_channel,
)
from app.services.firefox_policy_export import render_firefox_policies_document
from app.services.firefox_policy_import import validate_firefox_policies_document
from app.services.policy_schema_service import load_policy_schema
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from app.web.firefox_wizard_shell.catalog import CERTIFICATE_TRUST_GUIDED_POLICY_IDS
from tools import build_locale_catalogs
from tools import provision_firefox_schema_inputs as provisioner
from tools.convert_policies_from_upstream_lib.cli import generate_schema_targets
from tools.convert_policies_from_upstream_lib.common import (
    DEFAULT_SCHEMA_TARGETS_PATH,
    SchemaBuildTarget,
    load_schema_build_targets,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "app" / "schemas" / "policies"
AUDIT_PATH = (
    REPO_ROOT / "docs" / "architecture" / "firefox-esr-115-policy-disposition-audit-0.9.5.json"
)
AUDIT_SCHEMA_PATH = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "schemas"
    / "firefox-esr-115-policy-disposition-audit-v1.schema.json"
)

GATE_ID = "bpm095-firefox-four-channel-schema-release-gate"
REPORT_VERSION = 1
EXPECTED_CHANNELS = (
    "release-153",
    "esr-153.0",
    "esr-140.13",
    "esr-115.39",
)
SOURCE_CHANNEL = "esr-115.39"
AUDIT_TARGETS = ("esr-140.13", "esr-153.0", "release-153")
SEMANTIC_SHAPE_KEYS = (
    "type",
    "enum",
    "minimum",
    "maximum",
    "pattern",
    "additionalProperties",
    "required",
    "oneOf",
)

REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": (
        "report_version",
        "gate_id",
        "offline",
        "status",
        "target_count",
        "completed_targets",
        "channels",
        "matrix_checks",
    ),
    "properties": {
        "report_version": {"const": REPORT_VERSION},
        "gate_id": {"const": GATE_ID},
        "offline": {"const": True},
        "status": {"const": "passed"},
        "target_count": {"const": len(EXPECTED_CHANNELS)},
        "completed_targets": {"const": len(EXPECTED_CHANNELS)},
        "channels": {
            "type": "array",
            "minItems": len(EXPECTED_CHANNELS),
            "maxItems": len(EXPECTED_CHANNELS),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": (
                    "channel",
                    "artifact_sha256",
                    "policy_count",
                    "input_digests",
                    "cis_available",
                    "checks",
                ),
                "properties": {
                    "channel": {"type": "string"},
                    "artifact_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "policy_count": {"type": "integer", "minimum": 1},
                    "input_digests": {
                        "type": "object",
                        "additionalProperties": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                    "cis_available": {"type": "boolean"},
                    "checks": {
                        "type": "array",
                        "minItems": 8,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "matrix_checks": {
            "type": "array",
            "minItems": 4,
            "items": {"type": "string"},
        },
    },
}


class FirefoxSchemaMatrixGateError(RuntimeError):
    """Raised when a release-gate invariant cannot be proven."""


def _default_emit(message: str) -> None:
    print(message, flush=True)


def _progress(
    emit: Callable[[str], None],
    *,
    phase: str,
    channel: str,
    completed: int,
    total: int,
    detail: str = "",
) -> None:
    suffix = f" {detail}" if detail else ""
    emit(f"phase={phase} channel={channel} [{completed}/{total}]{suffix}")


def _fail(message: str) -> NoReturn:
    raise FirefoxSchemaMatrixGateError(message)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"Cannot read JSON evidence {path}: {error}")
    if not isinstance(payload, dict):
        _fail(f"JSON evidence must be an object: {path}")
    return payload


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _require_equal(actual: Any, expected: Any, context: str) -> None:
    if actual != expected:
        _fail(f"{context}: expected {expected!r}, got {actual!r}")


def _unique_input_specs(
    targets: tuple[SchemaBuildTarget, ...],
) -> tuple[tuple[str, provisioner.InputFile, Path], ...]:
    input_sets = provisioner.load_manifest()
    by_tag = {input_set.source_tag: input_set for input_set in input_sets}
    result: list[tuple[str, provisioner.InputFile, Path]] = []
    seen: set[tuple[str, str]] = set()
    for target in targets:
        input_set = by_tag.get(target.source_tag)
        if input_set is None:
            _fail(f"Target {target.channel} has no pinned input manifest entry")
        for spec in input_set.files:
            identity = (input_set.upstream_tag, spec.name)
            if identity in seen:
                continue
            seen.add(identity)
            result.append(
                (
                    input_set.upstream_tag,
                    spec,
                    REPO_ROOT
                    / "data"
                    / "upstream"
                    / "policy-templates"
                    / input_set.upstream_tag
                    / spec.name,
                )
            )
    return tuple(result)


def _verify_cache_file(path: Path, *, expected_bytes: int, expected_sha256: str) -> None:
    if not path.is_file():
        _fail(f"Offline gate requires a cached pinned input: {_relative(path)}")
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        _fail(
            f"Pinned input size drift for {_relative(path)}: "
            f"expected {expected_bytes}, got {actual_bytes}"
        )
    actual_sha256 = _sha256_bytes(path.read_bytes())
    if actual_sha256 != expected_sha256:
        _fail(
            f"Pinned input hash drift for {_relative(path)}: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )


def _assert_target_runtime_identity(target: SchemaBuildTarget) -> None:
    runtime = get_schema_channel(target.channel)
    if runtime is None:
        _fail(f"Target {target.channel} is absent from the runtime catalog")
    metadata = target.schema_metadata
    if metadata is None:
        _fail(f"Target {target.channel} has no schema metadata")
    _require_equal(runtime.artifact_id, target.channel, f"Runtime artifact ID for {target.channel}")
    _require_equal(runtime.line_id, metadata["line_id"], f"Runtime line ID for {target.channel}")
    _require_equal(
        runtime.line_number,
        metadata["firefox_line"],
        f"Runtime Firefox line for {target.channel}",
    )
    _require_equal(
        runtime.artifact_version,
        target.version,
        f"Runtime artifact version for {target.channel}",
    )
    _require_equal(runtime.label, metadata["ui_label"], f"Runtime label for {target.channel}")
    _require_equal(
        runtime.source_tag, target.source_tag, f"Runtime source tag for {target.channel}"
    )
    _require_equal(
        runtime.filename,
        target.output.name,
        f"Runtime filename for {target.channel}",
    )
    _require_equal(
        runtime.source.output_path,
        _relative(target.output),
        f"Runtime output path for {target.channel}",
    )
    source_provenance = metadata["source_provenance"]
    _require_equal(
        runtime.source.upstream_tag,
        source_provenance["upstream_tag"],
        f"Runtime upstream tag for {target.channel}",
    )
    _require_equal(
        runtime.source.documentation_input_path,
        _relative(target.documentation_input),
        f"Runtime documentation cache path for {target.channel}",
    )
    _require_equal(
        runtime.source.linux_policies_input_path,
        _relative(target.linux_policies_input),
        f"Runtime Linux cache path for {target.channel}",
    )
    _require_equal(
        runtime.source.documentation_input_url,
        source_provenance["inputs"]["policy-templates.md"]["url"],
        f"Runtime documentation URL for {target.channel}",
    )
    _require_equal(
        runtime.source.documentation_input_sha256,
        source_provenance["inputs"]["policy-templates.md"]["sha256"],
        f"Runtime documentation digest for {target.channel}",
    )
    _require_equal(
        runtime.source.linux_policies_input_url,
        source_provenance["inputs"]["linux-policies.json"]["url"],
        f"Runtime Linux URL for {target.channel}",
    )
    _require_equal(
        runtime.source.linux_policies_input_sha256,
        source_provenance["inputs"]["linux-policies.json"]["sha256"],
        f"Runtime Linux digest for {target.channel}",
    )


def _verify_preflight(
    targets: tuple[SchemaBuildTarget, ...], emit: Callable[[str], None]
) -> dict[str, dict[str, str]]:
    _require_equal(
        tuple(target.channel for target in targets),
        EXPECTED_CHANNELS,
        "Schema target declaration order",
    )
    _require_equal(SUPPORTED_SCHEMA_CHANNELS, EXPECTED_CHANNELS, "Runtime schema channel order")
    input_specs = _unique_input_specs(targets)
    input_digests: dict[str, dict[str, str]] = {}
    for position, (upstream_tag, spec, path) in enumerate(input_specs, start=1):
        _progress(
            emit,
            phase="preflight-input",
            channel=upstream_tag,
            completed=position,
            total=len(input_specs),
            detail=f"input={spec.name}",
        )
        _verify_cache_file(path, expected_bytes=spec.bytes, expected_sha256=spec.sha256)
        input_digests.setdefault(upstream_tag, {})[spec.name] = spec.sha256

    for position, target in enumerate(targets, start=1):
        _progress(
            emit,
            phase="preflight-target",
            channel=target.channel,
            completed=position,
            total=len(targets),
        )
        _assert_target_runtime_identity(target)
    return input_digests


@contextmanager
def _offline_network_guard() -> Any:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Network access is forbidden during offline schema reproducibility")

    with (
        patch.object(socket, "create_connection", blocked),
        patch.object(socket.socket, "connect", blocked),
    ):
        yield


def _reproduce_bundles(
    targets: tuple[SchemaBuildTarget, ...], emit: Callable[[str], None]
) -> dict[str, bytes]:
    with tempfile.TemporaryDirectory(prefix="bpm095-schema-repro-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        first_targets = tuple(
            replace(target, output=temporary_root / "first" / target.output.name)
            for target in targets
        )
        second_targets = tuple(
            replace(target, output=temporary_root / "second" / target.output.name)
            for target in targets
        )
        _progress(emit, phase="reproducibility", channel="matrix", completed=0, total=len(targets))
        with _offline_network_guard():
            generate_schema_targets(first_targets)
            generate_schema_targets(second_targets)

        generated: dict[str, bytes] = {}
        for position, (first, second) in enumerate(
            zip(first_targets, second_targets, strict=True), start=1
        ):
            _progress(
                emit,
                phase="reproducibility-compare",
                channel=first.channel,
                completed=position,
                total=len(targets),
            )
            first_bytes = first.output.read_bytes()
            second_bytes = second.output.read_bytes()
            committed_path = SCHEMAS_DIR / first.output.name
            if first_bytes != second_bytes:
                _fail(f"Isolated conversion is not byte reproducible for {first.channel}")
            if first_bytes != committed_path.read_bytes():
                _fail(
                    f"Committed bundled schema differs from offline conversion for {first.channel}: "
                    f"{_relative(committed_path)}"
                )
            generated[first.channel] = first_bytes
    return generated


def _assert_bundle_metadata(target: SchemaBuildTarget, bundle: dict[str, Any]) -> None:
    metadata = target.schema_metadata
    if metadata is None:
        _fail(f"Target {target.channel} has no metadata")
    expected = {
        "x-bpm-channel": target.channel,
        "x-bpm-version": target.version,
        "x-bpm-source": target.source_tag,
        "x-bpm-artifact-id": metadata["artifact_id"],
        "x-bpm-line-id": metadata["line_id"],
        "x-bpm-firefox-line": metadata["firefox_line"],
        "x-bpm-firefox-version": metadata["firefox_version"],
        "x-bpm-ui-label": metadata["ui_label"],
        "x-bpm-source-provenance": metadata["source_provenance"],
        "x-bpm-generator": metadata["generator"],
    }
    for key, expected_value in expected.items():
        _require_equal(
            bundle.get(key), expected_value, f"Bundle metadata {key} for {target.channel}"
        )


def _assert_catalog_contract(targets: tuple[SchemaBuildTarget, ...]) -> dict[str, Any]:
    catalog = build_schema_channels_catalog()
    expected = list(EXPECTED_CHANNELS)
    for field in ("supported_channels", "selector_channels", "header_channels"):
        _require_equal(catalog.get(field), expected, f"Catalog {field}")
    _require_equal(tuple(HEADER_SCHEMA_CHANNEL_VALUES), EXPECTED_CHANNELS, "Header channel order")
    _require_equal(
        catalog.get("default_channel"), DEFAULT_SCHEMA_CHANNEL, "Catalog default channel"
    )
    _require_equal(
        catalog.get("latest_esr_channel"), LATEST_ESR_SCHEMA_CHANNEL, "Latest ESR channel"
    )
    _require_equal(DEFAULT_SCHEMA_CHANNEL, "esr-153.0", "Product default channel")
    _require_equal(LATEST_ESR_SCHEMA_CHANNEL, "esr-153.0", "Latest ESR channel")
    options = catalog.get("options")
    if not isinstance(options, list):
        _fail("Catalog options must be a list")
    filenames = catalog.get("filenames")
    if not isinstance(filenames, dict):
        _fail("Catalog filenames must be an object")
    _require_equal([option.get("value") for option in options], expected, "Catalog option order")
    for target in targets:
        runtime = get_schema_channel(target.channel)
        if runtime is None:
            _fail(f"Missing runtime channel {target.channel}")
        option = next((item for item in options if item.get("value") == target.channel), None)
        if option is None:
            _fail(f"Missing catalog option for {target.channel}")
        _require_equal(option.get("label"), runtime.label, f"Catalog label for {target.channel}")
        _require_equal(
            filenames.get(target.channel),
            target.output.name,
            f"Catalog filename for {target.channel}",
        )
    return catalog


def _assert_policy_placement(channel: str, shell_catalog: dict[str, Any]) -> int:
    policy_schema = load_policy_schema(channel)
    channel_shell = shell_catalog.get("channels", {}).get(channel)
    if not isinstance(channel_shell, dict):
        _fail(f"Wizard shell does not contain {channel}")
    placed: set[str] = set()
    guided: set[str] = set()
    raw_fallback: set[str] = set()
    steps = channel_shell.get("steps")
    if not isinstance(steps, dict):
        _fail(f"Wizard shell steps are invalid for {channel}")
    for step in steps.values():
        if not isinstance(step, dict):
            _fail(f"Wizard shell step is invalid for {channel}")
        recommended = {item["id"] for item in step.get("recommended", [])}
        additional = {item["id"] for item in step.get("additional", [])}
        raw = {item["id"] for item in step.get("raw_fallback", [])}
        if (recommended | additional) & raw:
            _fail(f"Guided/raw policy placement overlaps for {channel}")
        guided.update(recommended | additional)
        raw_fallback.update(raw)
        placed.update(recommended | additional | raw)
    certificate_posture = channel_shell.get("certificate_trust_posture", {})
    if not isinstance(certificate_posture, dict):
        _fail(f"Certificate and trust placement is invalid for {channel}")
    certificate_policy_ids = set(certificate_posture.get("policy_ids", []))
    certificate_component_ids = {
        policy_id
        for policy_id in CERTIFICATE_TRUST_GUIDED_POLICY_IDS
        if policy_id in policy_schema.policies
    }
    if not certificate_policy_ids <= certificate_component_ids:
        _fail(f"Certificate and trust placement exposes an unavailable policy for {channel}")
    if placed & certificate_component_ids:
        _fail(f"Certificate and trust policy placement overlaps a wizard shell step for {channel}")
    # The posture summary deliberately exposes only the four controls rendered in
    # its card.  Authentication and SecurityDevices are still owned by the same
    # dedicated certificate component, so include the full component here when
    # proving that every schema policy has exactly one editor owner.
    placed.update(certificate_component_ids)
    expected = set(policy_schema.policies)
    _require_equal(placed, expected, f"Policy placement for {channel}")
    manual = get_manual_policy_controls_catalog(channel)
    if manual.get("schema_version") != channel:
        _fail(f"Manual policy catalog resolves a different channel for {channel}")
    if not set(manual.get("quick_policy_keys", [])) <= expected:
        _fail(f"Manual policy catalog exposes an unavailable policy for {channel}")
    return len(expected)


def _assert_locales(
    targets: tuple[SchemaBuildTarget, ...],
) -> dict[str, dict[str, str]]:
    generated_catalogs = build_locale_catalogs.build_catalogs()
    _require_equal(tuple(generated_catalogs), ACTIVE_CATALOG_LOCALES, "Active locale source order")
    runtime_catalogs: dict[str, dict[str, str]] = {}
    for locale in ACTIVE_CATALOG_LOCALES:
        runtime_catalog = _load_json(REPO_ROOT / "app" / "i18n" / f"{locale}.json")
        _require_equal(
            runtime_catalog, generated_catalogs[locale], f"Runtime locale catalog {locale}"
        )
        runtime_catalogs[locale] = runtime_catalog
        for target in targets:
            runtime = get_schema_channel(target.channel)
            if runtime is None:
                _fail(f"Missing runtime channel {target.channel}")
            value = runtime_catalog.get(runtime.i18n_key)
            if not isinstance(value, str) or not value.strip():
                _fail(
                    f"Locale {locale} lacks a non-empty channel label key "
                    f"{runtime.i18n_key} for {target.channel}"
                )
    return runtime_catalogs


def _assert_presets(channel: str, starter_catalog: dict[str, Any]) -> None:
    presets = starter_catalog.get("presets")
    if not isinstance(presets, dict) or not presets:
        _fail("Starter preset catalog is empty")
    for preset_name, preset in presets.items():
        if not isinstance(preset, dict):
            _fail(f"Starter preset {preset_name} is invalid")
        policy_values = preset.get("policy_values")
        if not isinstance(policy_values, dict) or not isinstance(policy_values.get(channel), dict):
            _fail(f"Starter preset {preset_name} lacks {channel} values")
        try:
            validate_profile_policies_or_raise_for_channel(policy_values[channel], channel)
        except ValueError as error:
            _fail(f"Starter preset {preset_name} is invalid for {channel}: {error}")


def _assert_cis(channel: str, audit: dict[str, Any]) -> bool:
    cis_evidence = audit.get("cis_evidence")
    if not isinstance(cis_evidence, dict):
        _fail("M3-05 audit lacks CIS evidence")
    available_channels = set(cis_evidence.get("available_channels", []))
    unavailable_channels = cis_evidence.get("unavailable_channels")
    if not isinstance(unavailable_channels, dict):
        _fail("M3-05 audit lacks unavailable CIS channel evidence")
    _require_equal(
        available_channels,
        set(EXPECTED_CHANNELS),
        "CIS availability matrix in M3-05 audit",
    )
    _require_equal(unavailable_channels, {}, "CIS unavailable channel matrix")
    availability = cis_layer_availability(channel)
    _require_equal(
        availability,
        {"available": True},
        f"CIS availability for {channel}",
    )
    for level, expected_recommendations in ((1, 49), (2, 53)):
        layer = build_cis_layer(level, channel)
        _require_equal(layer.schema_channel, channel, f"CIS layer channel for {channel}")
        _require_equal(
            len(layer.recommendation_ids),
            expected_recommendations,
            f"CIS L{level} recommendation coverage for {channel}",
        )
    return True


def _assert_import_edit_export_roundtrip(channel: str) -> None:
    imported_document = {
        "policies": {
            "DisableTelemetry": True,
            "BlockAboutConfig": True,
        }
    }
    flags = validate_firefox_policies_document(imported_document, channel)
    edited_flags = {**flags, "DisablePrivateBrowsing": True}
    validate_profile_policies_or_raise_for_channel(edited_flags, channel)
    exported = render_firefox_policies_document(edited_flags)
    _require_equal(
        exported,
        {"policies": edited_flags},
        f"Import/edit/export round trip for {channel}",
    )


def _shape(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    result: dict[str, Any] = {key: value[key] for key in SEMANTIC_SHAPE_KEYS if key in value}
    if isinstance(value.get("properties"), dict):
        result["properties"] = {key: _shape(child) for key, child in value["properties"].items()}
    if isinstance(value.get("items"), dict):
        result["items"] = _shape(value["items"])
    if isinstance(value.get("additionalProperties"), dict):
        result["additionalProperties"] = _shape(value["additionalProperties"])
    if isinstance(value.get("oneOf"), list):
        result["oneOf"] = [_shape(child) for child in value["oneOf"]]
    return result


def _changed_paths(source: Any, target: Any, path: str = "") -> set[str]:
    if source == target:
        return set()
    if isinstance(source, dict) and isinstance(target, dict):
        return {
            changed
            for key in source.keys() | target.keys()
            for changed in _changed_paths(
                source.get(key, "__missing__"), target.get(key, "__missing__"), f"{path}/{key}"
            )
        }
    return {path}


def _assert_m3_05_audit(
    bundles: dict[str, dict[str, Any]], emit: Callable[[str], None]
) -> dict[str, Any]:
    audit = _load_json(AUDIT_PATH)
    schema = _load_json(AUDIT_SCHEMA_PATH)
    try:
        jsonschema.Draft202012Validator(schema).validate(audit)
    except jsonschema.ValidationError as error:
        _fail(f"M3-05 disposition audit violates its schema: {error.message}")
    _require_equal(audit.get("source_channel"), SOURCE_CHANNEL, "M3-05 audit source channel")
    artifact_digests = audit.get("artifacts")
    if not isinstance(artifact_digests, dict):
        _fail("M3-05 audit lacks artifact digests")
    _require_equal(set(artifact_digests), set(EXPECTED_CHANNELS), "M3-05 audit artifact matrix")
    for channel in EXPECTED_CHANNELS:
        _require_equal(
            artifact_digests[channel],
            _sha256_bytes((SCHEMAS_DIR / f"firefox-{channel}.json").read_bytes()),
            f"M3-05 audit bundle digest for {channel}",
        )

    comparisons = audit.get("comparisons")
    if not isinstance(comparisons, list):
        _fail("M3-05 audit comparisons must be a list")
    by_target = {comparison.get("target_channel"): comparison for comparison in comparisons}
    _require_equal(set(by_target), set(AUDIT_TARGETS), "M3-05 audit comparison matrix")
    source_properties = bundles[SOURCE_CHANNEL].get("properties")
    if not isinstance(source_properties, dict):
        _fail("ESR 115 bundle has invalid policy properties")
    for position, target in enumerate(AUDIT_TARGETS, start=1):
        _progress(
            emit,
            phase="m3-05-audit",
            channel=SOURCE_CHANNEL,
            completed=position,
            total=len(AUDIT_TARGETS),
            detail=f"pair={SOURCE_CHANNEL}->{target}",
        )
        comparison = by_target[target]
        if not isinstance(comparison, dict):
            _fail(f"M3-05 audit comparison is invalid for {target}")
        target_properties = bundles[target].get("properties")
        if not isinstance(target_properties, dict):
            _fail(f"Bundle has invalid policy properties for {target}")
        expected_added = {
            f"/{policy}" for policy in target_properties.keys() - source_properties.keys()
        }
        expected_changed = {
            path
            for policy in source_properties.keys() & target_properties.keys()
            for path in _changed_paths(
                _shape(source_properties[policy]), _shape(target_properties[policy]), f"/{policy}"
            )
        }
        recorded_added: set[str] = set()
        recorded_changed: set[str] = set()
        recorded_members: set[str] = set()
        groups = comparison.get("groups")
        if not isinstance(groups, list):
            _fail(f"M3-05 audit groups are invalid for {target}")
        for group in groups:
            if not isinstance(group, dict):
                _fail(f"M3-05 audit group is invalid for {target}")
            owner = group.get("owner")
            if owner not in {"guided", "raw_fallback"}:
                _fail(f"M3-05 audit owner is not a product placement for {target}: {owner!r}")
            kind = group.get("kind")
            members = group.get("members")
            if kind not in {"target_only_policy", "changed_path"} or not isinstance(members, list):
                _fail(f"M3-05 audit group is incomplete for {target}")
            for member in members:
                if not isinstance(member, str) or member in recorded_members:
                    _fail(f"M3-05 audit has a duplicate or invalid difference for {target}")
                recorded_members.add(member)
                (recorded_added if kind == "target_only_policy" else recorded_changed).add(member)
        _require_equal(recorded_added, expected_added, f"M3-05 audited added policies for {target}")
        _require_equal(
            recorded_changed, expected_changed, f"M3-05 audited changed paths for {target}"
        )
    return audit


def _must_fail(label: str, callback: Callable[[], Any]) -> None:
    try:
        callback()
    except (
        FirefoxSchemaMatrixGateError,
        ValueError,
        UnknownSchemaChannelError,
        RetiredSchemaChannelError,
        UnbundledSchemaChannelError,
    ):
        return
    _fail(f"Fail-closed mutation unexpectedly succeeded: {label}")


def run_fail_closed_mutation_checks(targets: tuple[SchemaBuildTarget, ...]) -> tuple[str, ...]:
    """Prove representative declared and runtime drift is rejected without writes."""

    target = next(item for item in targets if item.channel == "esr-140.13")
    raw_target_manifest = _load_json(DEFAULT_SCHEMA_TARGETS_PATH)
    targets_payload = raw_target_manifest.get("targets")
    if not isinstance(targets_payload, list):
        _fail("Schema target manifest has invalid targets")

    with tempfile.TemporaryDirectory(prefix="bpm095-schema-mutations-") as temporary_directory:
        temporary_root = Path(temporary_directory)

        unknown_source = deepcopy(raw_target_manifest)
        unknown_source["targets"][0]["source_tag"] = "mozilla-policy-templates-unpinned"
        unknown_source_path = temporary_root / "unknown-source.json"
        unknown_source_path.write_text(json.dumps(unknown_source), encoding="utf-8")
        _must_fail(
            "manifest source-tag drift", lambda: load_schema_build_targets(unknown_source_path)
        )

        metadata_drift = deepcopy(raw_target_manifest)
        metadata_drift["targets"][0]["artifact_id"] = "release-incorrect"
        metadata_drift_path = temporary_root / "metadata-drift.json"
        metadata_drift_path.write_text(json.dumps(metadata_drift), encoding="utf-8")
        _must_fail(
            "manifest artifact metadata drift",
            lambda: load_schema_build_targets(metadata_drift_path),
        )

    _must_fail(
        "pinned input hash drift",
        lambda: _verify_cache_file(
            target.documentation_input,
            expected_bytes=target.documentation_input.stat().st_size,
            expected_sha256="0" * 64,
        ),
    )

    metadata = target.schema_metadata
    if metadata is None:
        _fail("Target metadata unexpectedly absent")
    bundle = _load_json(SCHEMAS_DIR / target.output.name)
    metadata_bundle = deepcopy(bundle)
    metadata_bundle["x-bpm-line-id"] = "drifted-line"
    _must_fail("bundle metadata drift", lambda: _assert_bundle_metadata(target, metadata_bundle))

    _must_fail("unknown channel", lambda: require_supported_schema_channel("unknown-channel"))
    _must_fail("unknown loader channel", lambda: load_policy_schema_for_channel("unknown-channel"))
    _must_fail("unknown policy-service channel", lambda: load_policy_schema("unknown-channel"))

    original_catalog = schema_channels.SCHEMA_CHANNEL_CATALOG
    original_filenames = schema_channels.SCHEMA_FILENAMES
    resolved = get_schema_channel(target.channel)
    if resolved is None:
        _fail(f"Missing mutable channel {target.channel}")
    try:
        schema_channels.SCHEMA_CHANNEL_CATALOG = tuple(
            replace(channel, support_state="retired", selectable=False)
            if channel.artifact_id == target.channel
            else channel
            for channel in original_catalog
        )
        _must_fail("retired channel", lambda: require_supported_schema_channel(target.channel))
    finally:
        schema_channels.SCHEMA_CHANNEL_CATALOG = original_catalog

    try:
        schema_channels.SCHEMA_FILENAMES = {
            channel: filename
            for channel, filename in original_filenames.items()
            if channel != target.channel
        }
        _must_fail("unbundled channel", lambda: require_supported_schema_channel(target.channel))
    finally:
        schema_channels.SCHEMA_FILENAMES = original_filenames

    return (
        "manifest_source_tag_drift_rejected",
        "manifest_metadata_drift_rejected",
        "pinned_input_hash_drift_rejected",
        "bundle_metadata_drift_rejected",
        "unknown_channel_rejected",
        "retired_channel_rejected",
        "unbundled_channel_rejected",
    )


def _write_report(path: Path, report: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(REPORT_SCHEMA).validate(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_gate(
    *,
    report_path: Path | None = None,
    emit: Callable[[str], None] = _default_emit,
) -> dict[str, Any]:
    """Execute the deterministic, offline four-channel schema evidence matrix."""

    _progress(emit, phase="start", channel="matrix", completed=0, total=len(EXPECTED_CHANNELS))
    targets = load_schema_build_targets()
    input_digests = _verify_preflight(targets, emit)
    generated_bytes = _reproduce_bundles(targets, emit)
    bundles = {
        channel: json.loads(payload.decode("utf-8")) for channel, payload in generated_bytes.items()
    }
    audit = _assert_m3_05_audit(bundles, emit)
    catalog = _assert_catalog_contract(targets)
    shell_catalog = get_wizard_schema_shell_catalog()
    starter_catalog = get_wizard_starter_catalog(include_compliance=False)
    _assert_locales(targets)

    profiles = dict(SCHEMA_FILENAMES)
    channel_reports: list[dict[str, Any]] = []
    for position, target in enumerate(targets, start=1):
        channel = target.channel
        _progress(
            emit,
            phase="channel-proof",
            channel=channel,
            completed=position - 1,
            total=len(targets),
        )
        _assert_bundle_metadata(target, bundles[channel])
        _require_equal(
            profiles.get(channel), target.output.name, f"Schema loader filename for {channel}"
        )
        loaded_schema = load_policy_schema_for_channel(channel)
        _require_equal(
            loaded_schema.get("x-bpm-channel"), channel, f"Schema loader identity for {channel}"
        )
        _require_equal(
            load_policy_schema(channel).channel, channel, f"Policy service identity for {channel}"
        )
        validate_profile_policies_or_raise_for_channel({"DisableTelemetry": True}, channel)
        policy_count = _assert_policy_placement(channel, shell_catalog)
        _assert_presets(channel, starter_catalog)
        cis_available = _assert_cis(channel, audit)
        _assert_import_edit_export_roundtrip(channel)
        source_provenance = (
            target.schema_metadata["source_provenance"] if target.schema_metadata else {}
        )
        provenance_inputs = source_provenance.get("inputs", {})
        channel_reports.append(
            {
                "channel": channel,
                "artifact_sha256": _sha256_bytes(generated_bytes[channel]),
                "policy_count": policy_count,
                "input_digests": {
                    name: spec["sha256"]
                    for name, spec in provenance_inputs.items()
                    if isinstance(spec, dict) and isinstance(spec.get("sha256"), str)
                },
                "cis_available": cis_available,
                "checks": [
                    "pinned_input_provenance",
                    "isolated_byte_reproducibility",
                    "bundle_metadata_identity",
                    "loader_and_validator_isolation",
                    "catalog_header_and_default",
                    "all_settings_and_manual_placement",
                    "six_locale_catalog_consistency",
                    "starter_preset_validity",
                    "cis_four_channel_compatibility_and_evidence",
                    "import_edit_export_roundtrip",
                ],
            }
        )
        _progress(
            emit,
            phase="channel-proof",
            channel=channel,
            completed=position,
            total=len(targets),
            detail=f"policy_count={policy_count}",
        )

    _progress(emit, phase="legacy-guard", channel="matrix", completed=0, total=1)
    mutation_checks = run_fail_closed_mutation_checks(targets)
    _progress(emit, phase="legacy-guard", channel="matrix", completed=1, total=1)
    _require_equal(catalog["default_channel"], DEFAULT_SCHEMA_CHANNEL, "Final catalog default")
    _require_equal(
        input_digests.keys(),
        {"a892b621f7f98ee91c8ed84290641f2703e88490", "v7.12", "v5.12"},
        "Pinned source matrix",
    )

    report: dict[str, Any] = {
        "report_version": REPORT_VERSION,
        "gate_id": GATE_ID,
        "offline": True,
        "status": "passed",
        "target_count": len(targets),
        "completed_targets": len(channel_reports),
        "channels": channel_reports,
        "matrix_checks": [
            "offline_pinned_input_size_hash_and_provenance",
            "two_isolated_roots_byte_identity_to_committed_bundles",
            "m3_05_audit_covers_every_schema_difference_without_refresh_bypass",
            "unknown_retired_unbundled_manifest_metadata_and_hash_drift_fail_closed",
            *mutation_checks,
        ],
    }
    jsonschema.Draft202012Validator(REPORT_SCHEMA).validate(report)
    if report_path is not None:
        _write_report(report_path, report)
    _progress(
        emit,
        phase="complete",
        channel="matrix",
        completed=len(targets),
        total=len(targets),
        detail="status=passed",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional deterministic JSON report path; no report file is written by default.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_gate(report_path=args.report)
    except (FirefoxSchemaMatrixGateError, OSError, ValueError, json.JSONDecodeError) as error:
        print(
            f"phase=complete channel=matrix [0/{len(EXPECTED_CHANNELS)}] status=failed: {error}",
            flush=True,
        )
        return 1
    print(
        "terminal-report="
        + json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
