"""Server-owned composition for a new profile's selected baseline catalogs.

This module intentionally has no request, persistence, or presentation
dependency.  M3-04 will pass catalog identities here and persist only this
server-derived candidate; a browser-composed flags document is not an input.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.compliance.firefox.cis.generation import (
    CisLayerUnavailableError,
    GeneratedCisLayer,
    build_cis_layer,
    cis_layer_availability,
)
from app.compliance.firefox.cis.merge import CisMergeResult, merge_base_with_cis_layer
from app.compliance.firefox.cis.validation import BASE_DIR as CIS_BASE_DIR
from app.core.firefox_starter_catalog import (
    CIS_LAYER_NONE,
    CIS_LAYER_OPTIONS,
    ESR_115_PRESET_NESTED_EXCLUSIONS,
    ESR_115_PRESET_POLICY_EXCLUSIONS,
    SCHEMA_ENABLED,
    STARTER_PRESETS,
)
from app.core.policy_validation import (
    load_policy_schema_for_channel,
    validate_profile_policies,
)
from app.core.profile_baseline_provenance import (
    CONTRACT_ID as PROVENANCE_CONTRACT_ID,
)
from app.core.profile_baseline_provenance import (
    CONTRACT_VERSION as PROVENANCE_CONTRACT_VERSION,
)
from app.core.profile_baseline_provenance import (
    is_valid_baseline_provenance,
)
from app.core.profile_certificate_provenance import initialization_certificate_provenance
from app.core.profile_conversion_json import (
    JsonValue,
    ProfileConversionJsonError,
    canonical_json,
    pointer,
    strict_json_copy,
)
from app.core.profile_extension_provenance import initialization_extension_provenance
from app.core.schema_channels import (
    SchemaChannel,
    SchemaChannelError,
    require_supported_schema_channel,
)

STARTER_CATALOG_ID = "firefox-guided-starter-presets"
STARTER_CATALOG_VERSION = "1"
CIS_CATALOG_ID = "firefox-cis-generated-layers"
INITIALIZATION_COMPOSITION_VERSION = 1
_DIGEST_DOMAIN = "bpm096-profile-initialization-composition:v1\n"
_PROOF_DOMAIN = "bpm096-profile-initialization-cis-proof:v1\n"

InitializationStatus = Literal["valid", "unavailable", "blocked"]


@dataclass(frozen=True)
class InitializationCompositionResult:
    """The complete server-derived candidate or a stable terminal disposition."""

    status: InitializationStatus
    reason_code: str | None
    schema: dict[str, Any] | None
    document: dict[str, JsonValue] | None
    compliance: dict[str, JsonValue] | None
    baseline_provenance: dict[str, JsonValue] | None
    extension_provenance: dict[str, JsonValue] | None
    certificate_provenance: dict[str, JsonValue] | None
    preset_decisions: tuple[dict[str, Any], ...]
    cis_decisions: tuple[dict[str, Any], ...]
    validation: dict[str, Any]
    result_digest: str

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"


def compose_profile_initialization(
    *,
    schema_id: str,
    preset_id: str,
    cis_baseline_id: str,
) -> InitializationCompositionResult:
    """Resolve catalog identities into one target-valid profile candidate.

    Inputs are identifiers only.  In particular there is deliberately no
    ``flags``/``document`` parameter: preparation must rederive policy data
    from the exact server catalog selected by these identities.
    """

    channel, schema_document = _resolve_schema(schema_id)
    if channel is None or schema_document is None:
        return _terminal_result(
            status="unavailable",
            reason_code="initialization_schema_unavailable",
            schema=None,
        )

    if preset_id not in STARTER_PRESETS:
        return _terminal_result(
            status="unavailable",
            reason_code="initialization_preset_unavailable",
            schema=_schema_identity(channel, schema_document),
        )
    if preset_id == "keep_current":
        return _terminal_result(
            status="blocked",
            reason_code="initialization_preset_requires_source",
            schema=_schema_identity(channel, schema_document),
        )
    if cis_baseline_id not in CIS_LAYER_OPTIONS:
        return _terminal_result(
            status="unavailable",
            reason_code="initialization_cis_unavailable",
            schema=_schema_identity(channel, schema_document),
        )

    try:
        base_document = _build_server_starter_document(
            preset_id, channel.artifact_id, schema_document
        )
        base_document = _as_document(base_document)
    except KeyError, ProfileConversionJsonError, TypeError, ValueError:
        return _terminal_result(
            status="blocked",
            reason_code="initialization_preset_invalid",
            schema=_schema_identity(channel, schema_document),
        )

    schema = _schema_identity(channel, schema_document)
    preset_identity = _preset_identity(preset_id, channel.artifact_id, base_document)
    preset_decisions = _preset_decisions(base_document, preset_identity)

    cis = _compose_cis(
        base_document=base_document,
        schema_id=channel.artifact_id,
        cis_baseline_id=cis_baseline_id,
    )
    if cis["status"] != "valid":
        return _terminal_result(
            status=cis["status"],
            reason_code=cis["reason_code"],
            schema=schema,
            preset_decisions=preset_decisions,
            cis_decisions=cis["decisions"],
        )

    document = cis["document"]
    assert isinstance(document, dict)
    validation_issues = validate_profile_policies(document, schema_document)
    validation = {
        "status": "valid" if not validation_issues else "invalid",
        "issue_count": len(validation_issues),
        "resolved_schema_artifact_id": channel.artifact_id,
    }
    if validation_issues:
        return _terminal_result(
            status="blocked",
            reason_code="initialization_candidate_invalid",
            schema=schema,
            preset_decisions=preset_decisions,
            cis_decisions=cis["decisions"],
            validation=validation,
        )

    provenance = _baseline_provenance(
        schema_id=channel.artifact_id,
        preset_identity=preset_identity,
        cis_identity=cis["identity"],
    )
    if not is_valid_baseline_provenance(provenance):
        return _terminal_result(
            status="blocked",
            reason_code="initialization_provenance_invalid",
            schema=schema,
            preset_decisions=preset_decisions,
            cis_decisions=cis["decisions"],
            validation=validation,
        )

    compliance = cis["compliance"]
    extension_provenance = initialization_extension_provenance(
        document,
        preset_decisions=preset_decisions,
        cis_decisions=cis["decisions"],
    )
    certificate_provenance = initialization_certificate_provenance(
        document,
        preset_decisions=preset_decisions,
        cis_decisions=cis["decisions"],
    )
    result_digest = _domain_digest(
        _DIGEST_DOMAIN,
        {
            "schema": schema,
            "document": document,
            "compliance": compliance,
            "baseline_provenance": provenance,
            "extension_provenance": extension_provenance,
            "certificate_provenance": certificate_provenance,
            "preset_decisions": list(preset_decisions),
            "cis_decisions": list(cis["decisions"]),
            "validation": validation,
        },
    )
    return InitializationCompositionResult(
        status="valid",
        reason_code=None,
        schema=schema,
        document=document,
        compliance=compliance,
        baseline_provenance=provenance,
        extension_provenance=extension_provenance,
        certificate_provenance=certificate_provenance,
        preset_decisions=preset_decisions,
        cis_decisions=cis["decisions"],
        validation=validation,
        result_digest=result_digest,
    )


def _resolve_schema(schema_id: str) -> tuple[SchemaChannel | None, dict[str, JsonValue] | None]:
    try:
        channel = require_supported_schema_channel(schema_id)
        schema = strict_json_copy(load_policy_schema_for_channel(channel.artifact_id))
    except SchemaChannelError, ProfileConversionJsonError, ValueError, OSError:
        return None, None
    return (channel, schema) if isinstance(schema, dict) else (None, None)


def _schema_identity(
    channel: SchemaChannel, schema_document: dict[str, JsonValue]
) -> dict[str, str]:
    bundle_path = Path(__file__).resolve().parents[2] / channel.source.output_path
    try:
        bundle_digest = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    except OSError:
        bundle_digest = _sha256_jcs(schema_document)
    return {
        "line_id": channel.line_id,
        "artifact_id": channel.artifact_id,
        "channel_id": channel.channel_id,
        "artifact_version": channel.artifact_version,
        "source_tag": channel.source.source_tag,
        "schema_bundle_sha256": bundle_digest,
        "validation_schema_sha256": _sha256_jcs(schema_document),
    }


def _build_server_starter_document(
    preset_id: str,
    schema_id: str,
    schema_document: dict[str, JsonValue],
) -> dict[str, Any]:
    preset = STARTER_PRESETS[preset_id]
    policy_values = preset.get("policy_values", {})
    if not isinstance(policy_values, dict):
        raise ValueError("starter policy values must be an object")
    resolved = _resolve_policy_values(policy_values.get("default", {}), schema_id, schema_document)
    resolved.update(
        _resolve_policy_values(policy_values.get(schema_id, {}), schema_id, schema_document)
    )
    homepage = deepcopy(preset.get("homepage", {}))
    proxy = deepcopy(preset.get("proxy", {}))
    if homepage:
        resolved["Homepage"] = homepage
    if proxy:
        resolved["Proxy"] = proxy
    return resolved


def _resolve_policy_values(
    policy_values: object,
    schema_id: str,
    schema_document: dict[str, JsonValue],
) -> dict[str, Any]:
    if not isinstance(policy_values, dict):
        raise ValueError("starter policy values must be an object")
    resolved: dict[str, Any] = {}
    for policy_id, value in policy_values.items():
        if not isinstance(policy_id, str):
            raise ValueError("starter policy id must be a string")
        resolved[policy_id] = (
            _schema_enabled_value(policy_id, schema_document)
            if value == SCHEMA_ENABLED
            else deepcopy(value)
        )
    if schema_id == "esr-115.39":
        for policy_id in ESR_115_PRESET_POLICY_EXCLUSIONS:
            resolved.pop(policy_id, None)
        for policy_id, excluded_fields in ESR_115_PRESET_NESTED_EXCLUSIONS.items():
            value = resolved.get(policy_id)
            if isinstance(value, dict):
                for field in excluded_fields:
                    value.pop(field, None)
    return resolved


def _schema_enabled_value(policy_id: str, schema_document: dict[str, JsonValue]) -> Any:
    properties = schema_document.get("properties")
    definition = properties.get(policy_id) if isinstance(properties, dict) else None
    if not isinstance(definition, dict):
        return True
    definition_type = _schema_node_type(definition)
    if definition_type == "object":
        return {}
    if definition_type == "array":
        return []
    if definition_type == "string":
        return ""
    if definition_type in {"integer", "number"}:
        return 1
    return True


def _schema_node_type(definition: dict[str, JsonValue]) -> str:
    type_value = definition.get("type")
    if isinstance(type_value, str):
        return type_value
    branches = definition.get("oneOf")
    if isinstance(branches, list):
        for branch in branches:
            if isinstance(branch, dict):
                branch_type = _schema_node_type(branch)
                if branch_type:
                    return branch_type
    if isinstance(definition.get("properties"), dict) or "additionalProperties" in definition:
        return "object"
    if isinstance(definition.get("items"), dict):
        return "array"
    return "object"


def _compose_cis(
    *,
    base_document: dict[str, JsonValue],
    schema_id: str,
    cis_baseline_id: str,
) -> dict[str, Any]:
    if cis_baseline_id == CIS_LAYER_NONE:
        return {
            "status": "valid",
            "reason_code": None,
            "document": deepcopy(base_document),
            "identity": None,
            "decisions": (),
            "compliance": None,
        }

    availability = cis_layer_availability(schema_id)
    if not availability["available"]:
        return {
            "status": "unavailable",
            "reason_code": str(availability["reason_code"]),
            "document": None,
            "identity": None,
            "decisions": (),
            "compliance": None,
        }

    level = CIS_LAYER_OPTIONS[cis_baseline_id].get("level")
    if not isinstance(level, int):
        return {
            "status": "blocked",
            "reason_code": "initialization_cis_catalog_invalid",
            "document": None,
            "identity": None,
            "decisions": (),
            "compliance": None,
        }
    try:
        layer = build_cis_layer(level, schema_id)
        merge_result = merge_base_with_cis_layer(
            base_document,
            layer,
            base_label="starter-catalog",
            cis_label="cis-catalog",
        )
        document = _as_document(merge_result.effective_policies)
        decisions = _cis_decisions(merge_result, cis_baseline_id)
        identity = _cis_identity(
            layer=layer,
            cis_baseline_id=cis_baseline_id,
            merge_result=merge_result,
            document=document,
        )
        compliance = {
            "kind": "cis-initialization",
            "catalog_id": identity["catalog_id"],
            "catalog_version": identity["catalog_version"],
            "baseline_id": identity["baseline_id"],
            "benchmark_id": identity["benchmark_id"],
            "benchmark_version": identity["benchmark_version"],
            "summary": dict(merge_result.summary),
            "decisions": list(decisions),
        }
    except CisLayerUnavailableError as exc:
        return {
            "status": "unavailable",
            "reason_code": str(exc),
            "document": None,
            "identity": None,
            "decisions": (),
            "compliance": None,
        }
    except OSError, ProfileConversionJsonError, TypeError, ValueError, KeyError:
        return {
            "status": "blocked",
            "reason_code": "initialization_cis_catalog_invalid",
            "document": None,
            "identity": None,
            "decisions": (),
            "compliance": None,
        }

    return {
        "status": "valid",
        "reason_code": None,
        "document": document,
        "identity": identity,
        "decisions": decisions,
        "compliance": compliance,
    }


def _preset_identity(
    preset_id: str,
    schema_id: str,
    document: dict[str, JsonValue],
) -> dict[str, str]:
    definition = {
        "catalog_id": STARTER_CATALOG_ID,
        "catalog_version": STARTER_CATALOG_VERSION,
        "preset_id": preset_id,
        "resolved_schema_artifact_id": schema_id,
        "resolved_definition": document,
    }
    return {
        "catalog_id": STARTER_CATALOG_ID,
        "catalog_version": STARTER_CATALOG_VERSION,
        "preset_id": preset_id,
        "definition_sha256": _sha256_jcs(definition),
        "resolved_schema_artifact_id": schema_id,
    }


def _preset_decisions(
    document: dict[str, JsonValue],
    identity: dict[str, str],
) -> tuple[dict[str, Any], ...]:
    paths = tuple(_leaf_paths(document))
    if not paths:
        paths = ("",)
    return tuple(
        {
            "path": path,
            "decision": "applied_from_preset" if path else "empty_preset",
            "source": "starter-catalog",
            "catalog_id": identity["catalog_id"],
            "catalog_version": identity["catalog_version"],
            "preset_id": identity["preset_id"],
            "definition_sha256": identity["definition_sha256"],
        }
        for path in paths
    )


def _cis_decisions(
    merge_result: CisMergeResult,
    cis_baseline_id: str,
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "path": pointer(decision.path),
            "decision": decision.decision,
            "source": "cis-merge",
            "selected_source": decision.selected_source,
            "catalog_id": CIS_CATALOG_ID,
            "baseline_id": cis_baseline_id,
            "recommendation_ids": list(decision.recommendation_ids),
            "merge_rule": decision.merge_rule,
            "review_required": decision.review_required,
        }
        for decision in merge_result.decisions
    )


def _cis_identity(
    *,
    layer: GeneratedCisLayer,
    cis_baseline_id: str,
    merge_result: CisMergeResult,
    document: dict[str, JsonValue],
) -> dict[str, Any]:
    layer_identity = {
        "benchmark_id": layer.benchmark_id,
        "upstream_version": layer.upstream_version,
        "level": layer.level,
        "schema_channel": layer.schema_channel,
        "recommendation_ids": list(layer.recommendation_ids),
        "policies": layer.policies,
    }
    merge_rules_digest = _sha256_bytes((CIS_BASE_DIR / "merge_rules.yaml").read_bytes())
    layer_digest = _sha256_jcs(layer_identity)
    merge_result_digest = _sha256_jcs(
        {
            "effective_policies": document,
            "decisions": [decision.to_dict() for decision in merge_result.decisions],
            "summary": merge_result.summary,
        }
    )
    review_required = any(decision.review_required for decision in merge_result.decisions)
    display_status = "manual-review" if review_required else "verified"
    proof_digest = _domain_digest(
        _PROOF_DOMAIN,
        {
            "layer_sha256": layer_digest,
            "merge_rules_sha256": merge_rules_digest,
            "merge_result_sha256": merge_result_digest,
            "resolved_schema_artifact_id": layer.schema_channel,
            "document": document,
            "review_required": review_required,
        },
    )
    return {
        "catalog_id": CIS_CATALOG_ID,
        "catalog_version": layer.upstream_version,
        "baseline_id": cis_baseline_id,
        "benchmark_id": layer.benchmark_id,
        "benchmark_version": layer.upstream_version,
        "layer_sha256": layer_digest,
        "merge_rules_sha256": merge_rules_digest,
        "merge_result_sha256": merge_result_digest,
        "resolved_schema_artifact_id": layer.schema_channel,
        "proof_digest": proof_digest,
        "display_status": display_status,
        "current_claim": display_status == "verified",
        "reason_code": "cis_merge_manual_review_required" if review_required else None,
    }


def _baseline_provenance(
    *,
    schema_id: str,
    preset_identity: dict[str, str],
    cis_identity: dict[str, Any] | None,
) -> dict[str, JsonValue]:
    starter: dict[str, JsonValue] = {
        "identity_state": "catalog",
        "catalog_id": preset_identity["catalog_id"],
        "catalog_version": preset_identity["catalog_version"],
        "preset_id": preset_identity["preset_id"],
        "definition_sha256": preset_identity["definition_sha256"],
        "resolved_schema_artifact_id": schema_id,
        "disposition": "created",
    }
    if cis_identity is None:
        cis: dict[str, JsonValue] = {
            "identity_state": "none",
            "catalog_id": None,
            "catalog_version": None,
            "baseline_id": None,
            "benchmark_id": None,
            "benchmark_version": None,
            "layer_sha256": None,
            "merge_rules_sha256": None,
            "merge_result_sha256": None,
            "resolved_schema_artifact_id": None,
            "proof_digest": None,
            "display_status": "none",
            "current_claim": False,
            "reason_code": None,
        }
    else:
        cis = {"identity_state": "catalog", **cis_identity}
    return {
        "contract_id": PROVENANCE_CONTRACT_ID,
        "contract_version": PROVENANCE_CONTRACT_VERSION,
        "lineage": {
            "kind": "prepared",
            "source_profile_id": None,
            "source_revision": None,
            "plan_digest": None,
        },
        "starter": starter,
        "cis": cis,
    }


def _terminal_result(
    *,
    status: Literal["unavailable", "blocked"],
    reason_code: str,
    schema: dict[str, Any] | None,
    preset_decisions: tuple[dict[str, Any], ...] = (),
    cis_decisions: tuple[dict[str, Any], ...] = (),
    validation: dict[str, Any] | None = None,
) -> InitializationCompositionResult:
    resolved_validation = validation or {
        "status": "not-run",
        "issue_count": 0,
        "resolved_schema_artifact_id": schema["artifact_id"] if schema else None,
    }
    result_digest = _domain_digest(
        _DIGEST_DOMAIN,
        {
            "status": status,
            "reason_code": reason_code,
            "schema": schema,
            "preset_decisions": list(preset_decisions),
            "cis_decisions": list(cis_decisions),
            "validation": resolved_validation,
        },
    )
    return InitializationCompositionResult(
        status=status,
        reason_code=reason_code,
        schema=schema,
        document=None,
        compliance=None,
        baseline_provenance=None,
        extension_provenance=None,
        certificate_provenance=None,
        preset_decisions=preset_decisions,
        cis_decisions=cis_decisions,
        validation=resolved_validation,
        result_digest=result_digest,
    )


def _as_document(value: object) -> dict[str, JsonValue]:
    document = strict_json_copy(value)
    if not isinstance(document, dict):
        raise ValueError("policy document must be an object")
    return document


def _leaf_paths(value: JsonValue, path: tuple[str | int, ...] = ()) -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key in sorted(value):
            paths.extend(_leaf_paths(value[key], (*path, key)))
        return paths
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_leaf_paths(item, (*path, index)))
        return paths
    return [pointer(path)]


def _sha256_jcs(value: object) -> str:
    return hashlib.sha256(canonical_json(strict_json_copy(value))).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _domain_digest(domain: str, value: object) -> str:
    return hashlib.sha256(
        domain.encode("utf-8") + canonical_json(strict_json_copy(value))
    ).hexdigest()
