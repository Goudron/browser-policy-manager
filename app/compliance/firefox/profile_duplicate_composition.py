"""Read-only, server-owned planning for Firefox profile duplication.

This is the BPM096-M3-03 boundary.  It binds one stored source snapshot and
returns a value-safe description of a possible duplicate without creating or
modifying an ORM row.  M3-05 will rederive this result in its write
transaction; this module deliberately contains no request, session, or ORM
dependency.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from app.compliance.firefox import profile_initialization_composition as initialization
from app.core.firefox_starter_catalog import CIS_LAYER_NONE, CIS_LAYER_OPTIONS, STARTER_PRESETS
from app.core.policy_validation import PolicyValidationIssue, validate_profile_policies
from app.core.profile_baseline_provenance import (
    CONTRACT_ID as PROVENANCE_CONTRACT_ID,
)
from app.core.profile_baseline_provenance import (
    CONTRACT_VERSION as PROVENANCE_CONTRACT_VERSION,
)
from app.core.profile_baseline_provenance import is_valid_baseline_provenance
from app.core.profile_certificate_provenance import duplicate_certificate_provenance
from app.core.profile_conversion_json import (
    JsonValue,
    ProfileConversionJsonError,
    canonical_json,
    ordered_keys,
    pointer,
    strict_json_copy,
)
from app.core.profile_conversion_planner import (
    ConversionPlanningContext,
    ConversionPlanningError,
    plan_profile_conversion,
)
from app.core.profile_extension_provenance import duplicate_extension_provenance

_CONTRACT_VERSION = 1
_DOCUMENT_DOMAIN = "bpm-policy-document:v1\n"
_COMPLIANCE_DOMAIN = "bpm-profile-compliance:v1\n"
_METADATA_DOMAIN = "bpm-profile-metadata:v1\n"
_RESULT_DOMAIN = "bpm096-profile-duplicate-result:v1\n"
_PLAN_DOMAIN = "bpm096-profile-duplicate-composition:v1\n"
_LINEAGE_DOMAIN = "bpm096-profile-duplicate-lineage:v1\n"
_METADATA_FIELDS = (
    "name",
    "description",
    "created_at",
    "updated_at",
    "deleted_at",
)

DuplicatePlanningStatus = Literal["valid", "unavailable", "blocked"]


@dataclass(frozen=True, slots=True)
class DuplicatePlanningSource:
    """One copied persisted source revision supplied by the service boundary."""

    profile_id: int
    revision: int
    lifecycle_state: str
    schema_artifact_id: str
    flags: Mapping[str, Any]
    compliance: Any
    baseline_provenance: Any
    metadata: Mapping[str, Any]
    extension_provenance: Any = None
    certificate_provenance: Any = None


@dataclass(frozen=True, slots=True)
class DuplicatePlanningResult:
    """Public plan plus private, independently copied valid candidate data."""

    status: DuplicatePlanningStatus
    reason_code: str | None
    _plan: dict[str, JsonValue]
    _candidate_document: dict[str, JsonValue] | None
    _candidate_compliance: JsonValue
    _candidate_baseline_provenance: dict[str, JsonValue] | None
    _candidate_extension_provenance: dict[str, JsonValue] | None
    _candidate_certificate_provenance: dict[str, JsonValue] | None

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"

    @property
    def plan(self) -> dict[str, JsonValue]:
        return deepcopy(self._plan)

    @property
    def candidate_document(self) -> dict[str, JsonValue] | None:
        return deepcopy(self._candidate_document)

    @property
    def candidate_compliance(self) -> JsonValue:
        return deepcopy(self._candidate_compliance)

    @property
    def candidate_baseline_provenance(self) -> dict[str, JsonValue] | None:
        return deepcopy(self._candidate_baseline_provenance)

    @property
    def candidate_extension_provenance(self) -> dict[str, JsonValue] | None:
        return deepcopy(self._candidate_extension_provenance)

    @property
    def candidate_certificate_provenance(self) -> dict[str, JsonValue] | None:
        return deepcopy(self._candidate_certificate_provenance)


def plan_profile_duplicate(
    source: DuplicatePlanningSource,
    *,
    expected_source_revision: int,
    target_schema_id: str,
    preset_id: str,
    cis_baseline_id: str,
) -> DuplicatePlanningResult:
    """Derive one duplicate candidate from a fixed source snapshot.

    The public result exposes catalog identities, RFC 6901 pointers, stable
    codes, counts, and digests only.  The full policy/compliance/provenance
    candidate remains private to the server process and is returned only for a
    valid plan, ready for M3-05 to rederive rather than trust.
    """

    source_identity = _source_identity(source)
    target: dict[str, JsonValue] = {
        "requested_artifact_id": target_schema_id if isinstance(target_schema_id, str) else None,
        "artifact": None,
    }
    empty_conversion: dict[str, JsonValue] = {"kind": "not-run", "plan_digest": None}
    empty_preset: dict[str, JsonValue] = {
        "selection": preset_id if isinstance(preset_id, str) else None,
        "identity": None,
        "decisions": [],
    }
    empty_cis: dict[str, JsonValue] = {
        "selection": cis_baseline_id if isinstance(cis_baseline_id, str) else None,
        "identity": None,
        "decisions": [],
        "source_compliance": None,
    }

    try:
        metadata = _normalized_metadata(source.metadata)
        source_document = _as_document(source.flags)
        source_compliance = strict_json_copy(source.compliance)
        source_provenance = strict_json_copy(source.baseline_provenance)
        source_extension_provenance = strict_json_copy(source.extension_provenance)
        source_certificate_provenance = strict_json_copy(source.certificate_provenance)
    except ProfileConversionJsonError, TypeError, ValueError:
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_source_invalid",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )

    if not _source_shape_is_valid(source, expected_source_revision):
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_source_invalid",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )
    if source.lifecycle_state != "active":
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_source_not_active",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )
    if source.revision != expected_source_revision:
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_source_stale",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )
    if not is_valid_baseline_provenance(source_provenance):
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_source_provenance_invalid",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )

    source_channel, source_schema = initialization._resolve_schema(source.schema_artifact_id)
    if source_channel is None or source_schema is None:
        return _terminal_result(
            status="unavailable",
            reason_code="duplicate_source_schema_unavailable",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )
    source_artifact = _json_object(initialization._schema_identity(source_channel, source_schema))
    source_identity["artifact"] = source_artifact

    target_channel, target_schema = initialization._resolve_schema(target_schema_id)
    if target_channel is None or target_schema is None:
        return _terminal_result(
            status="unavailable",
            reason_code="duplicate_target_schema_unavailable",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )
    target_artifact = _json_object(initialization._schema_identity(target_channel, target_schema))
    target["artifact"] = target_artifact

    source_issues = validate_profile_policies(source_document, source_schema)
    source_validation = _validation_projection(
        source_issues,
        source_schema,
        source_document,
        source_channel.artifact_id,
    )
    source_identity["validation"] = source_validation
    if source_issues:
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_source_invalid",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
            blockers=_json_object_list(source_validation["issues"]),
            validation=source_validation,
        )

    if preset_id not in STARTER_PRESETS:
        return _terminal_result(
            status="unavailable",
            reason_code="duplicate_preset_unavailable",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )
    if cis_baseline_id not in CIS_LAYER_OPTIONS:
        return _terminal_result(
            status="unavailable",
            reason_code="duplicate_cis_unavailable",
            source=source_identity,
            target=target,
            conversion=empty_conversion,
            preset=empty_preset,
            cis=empty_cis,
        )

    conversion: dict[str, JsonValue]
    candidate_document: dict[str, JsonValue]
    candidate_compliance: JsonValue
    if source_channel.artifact_id == target_channel.artifact_id:
        candidate_document = deepcopy(source_document)
        candidate_compliance = deepcopy(source_compliance)
        conversion = {
            "kind": "same-schema-copy",
            "source_document_digest": _document_digest(source_document),
            "source_validation": source_validation,
            "plan_digest": None,
        }
    else:
        try:
            conversion_result = plan_profile_conversion(
                {"policies": source_document},
                source_artifact_id=source_channel.artifact_id,
                target_artifact_id=target_channel.artifact_id,
                context=ConversionPlanningContext(
                    profile_id=source.profile_id,
                    revision=source.revision,
                    lifecycle_state="active",
                    metadata=metadata,
                    compliance=source_compliance,
                ),
            )
        except ConversionPlanningError as exc:
            return _terminal_result(
                status="blocked",
                reason_code="duplicate_conversion_unavailable",
                source=source_identity,
                target=target,
                conversion={
                    "kind": "cross-schema",
                    "plan_digest": None,
                    "error_code": exc.code,
                },
                preset=empty_preset,
                cis=empty_cis,
                blockers=[{"code": exc.code, "path": ""}],
            )
        conversion_plan = conversion_result.plan
        conversion = _conversion_projection(conversion_plan)
        conversion_blockers = conversion_plan.get("blockers")
        compatibility = conversion_plan.get("compatibility")
        target_validation = conversion_plan.get("target_validation")
        if (
            not isinstance(compatibility, dict)
            or compatibility.get("applicable") is not True
            or not isinstance(target_validation, dict)
            or target_validation.get("status") != "valid"
        ):
            return _terminal_result(
                status="blocked",
                reason_code="duplicate_conversion_blocked",
                source=source_identity,
                target=target,
                conversion=conversion,
                preset=empty_preset,
                cis=empty_cis,
                blockers=_json_object_list(conversion_blockers),
                validation=_json_object(target_validation)
                if isinstance(target_validation, dict)
                else None,
            )
        converted = conversion_result.candidate_document.get("policies")
        if not isinstance(converted, dict):
            return _terminal_result(
                status="blocked",
                reason_code="duplicate_conversion_invalid",
                source=source_identity,
                target=target,
                conversion=conversion,
                preset=empty_preset,
                cis=empty_cis,
            )
        candidate_document = converted
        candidate_compliance = conversion_result.candidate_compliance

    carry_forward = (
        source_channel.artifact_id == target_channel.artifact_id
        and preset_id == "keep_current"
        and _cis_selection_matches(source_provenance, cis_baseline_id)
    )
    preset: dict[str, JsonValue]
    cis: dict[str, JsonValue]
    preset_decisions: tuple[dict[str, JsonValue], ...]
    cis_decisions: tuple[dict[str, JsonValue], ...]
    if carry_forward:
        preset_decisions = ()
        cis_decisions = ()
        preset = {
            "selection": "keep_current",
            "identity": _starter_identity_projection(source_provenance),
            "decisions": [],
            "disposition": "preserved",
        }
        cis = {
            "selection": cis_baseline_id,
            "identity": _cis_identity_projection(source_provenance),
            "decisions": [],
            "disposition": "preserved",
            "source_compliance": {
                "disposition": "preserved-inert",
                "source_digest": _compliance_digest(source_compliance),
                "target_digest": _compliance_digest(candidate_compliance),
            },
        }
    else:
        candidate_document, preset, preset_decisions, preset_blockers = _compose_preset(
            candidate_document,
            schema_id=target_channel.artifact_id,
            schema_document=target_schema,
            preset_id=preset_id,
        )
        if preset_blockers:
            return _terminal_result(
                status="blocked",
                reason_code="duplicate_preset_composition_blocked",
                source=source_identity,
                target=target,
                conversion=conversion,
                preset=preset,
                cis=empty_cis,
                blockers=preset_blockers,
            )
        cis_result = _compose_cis(
            base_document=candidate_document,
            schema_id=target_channel.artifact_id,
            cis_baseline_id=cis_baseline_id,
            source_compliance=source_compliance,
            inherited_compliance=candidate_compliance,
        )
        cis = cis_result["projection"]
        cis_decisions = cis_result["decisions"]
        if cis_result["status"] != "valid":
            return _terminal_result(
                status=cis_result["status"],
                reason_code=str(cis_result["reason_code"]),
                source=source_identity,
                target=target,
                conversion=conversion,
                preset=preset,
                cis=cis,
                blockers=[{"code": str(cis_result["reason_code"]), "path": ""}],
            )
        candidate_document = cis_result["document"]
        candidate_compliance = cis_result["compliance"]

    target_issues = validate_profile_policies(candidate_document, target_schema)
    validation = _validation_projection(
        target_issues,
        target_schema,
        candidate_document,
        target_channel.artifact_id,
    )
    if target_issues:
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_candidate_invalid",
            source=source_identity,
            target=target,
            conversion=conversion,
            preset=preset,
            cis=cis,
            blockers=_json_object_list(validation["issues"]),
            validation=validation,
        )

    derivation_digest = _lineage_digest(
        source=source_identity,
        target=target,
        conversion=conversion,
        preset_decisions=preset_decisions,
        cis_decisions=cis_decisions,
        document=candidate_document,
        compliance=candidate_compliance,
        validation=validation,
    )
    provenance = _duplicate_provenance(
        source_provenance,
        source_profile_id=source.profile_id,
        source_revision=source.revision,
        lineage_plan_digest=derivation_digest,
        target_schema_id=target_channel.artifact_id,
        carry_forward=carry_forward,
        preset=preset,
        cis=cis,
    )
    if not is_valid_baseline_provenance(provenance):
        return _terminal_result(
            status="blocked",
            reason_code="duplicate_provenance_invalid",
            source=source_identity,
            target=target,
            conversion=conversion,
            preset=preset,
            cis=cis,
            validation=validation,
        )

    extension_provenance = duplicate_extension_provenance(
        source_document,
        source_extension_provenance,
        candidate_document,
        cross_schema=source_channel.artifact_id != target_channel.artifact_id,
        preset_decisions=preset_decisions,
        cis_decisions=cis_decisions,
    )
    certificate_provenance = duplicate_certificate_provenance(
        source_document,
        source_certificate_provenance,
        candidate_document,
        cross_schema=source_channel.artifact_id != target_channel.artifact_id,
        preset_decisions=preset_decisions,
        cis_decisions=cis_decisions,
    )

    result_digest = _domain_digest(
        _RESULT_DOMAIN,
        {
            "document": candidate_document,
            "compliance": candidate_compliance,
            "baseline_provenance": provenance,
            "extension_provenance": extension_provenance,
            "certificate_provenance": certificate_provenance,
            "validation": validation,
        },
    )
    result: dict[str, JsonValue] = {
        "document_digest": _document_digest(candidate_document),
        "compliance_digest": _compliance_digest(candidate_compliance),
        "baseline_provenance_digest": _sha256_jcs(provenance),
        "extension_provenance_digest": _sha256_jcs(extension_provenance),
        "certificate_provenance_digest": _sha256_jcs(certificate_provenance),
        "result_digest": result_digest,
    }
    plan = _public_plan(
        status="valid",
        reason_code=None,
        source=source_identity,
        target=target,
        conversion=conversion,
        preset=preset,
        cis=cis,
        validation=validation,
        blockers=[],
        result=result,
    )
    return DuplicatePlanningResult(
        status="valid",
        reason_code=None,
        _plan=plan,
        _candidate_document=candidate_document,
        _candidate_compliance=candidate_compliance,
        _candidate_baseline_provenance=provenance,
        _candidate_extension_provenance=extension_provenance,
        _candidate_certificate_provenance=certificate_provenance,
    )


def _source_shape_is_valid(source: DuplicatePlanningSource, expected_revision: int) -> bool:
    return (
        isinstance(source.profile_id, int)
        and not isinstance(source.profile_id, bool)
        and source.profile_id >= 1
        and isinstance(source.revision, int)
        and not isinstance(source.revision, bool)
        and source.revision >= 1
        and isinstance(expected_revision, int)
        and not isinstance(expected_revision, bool)
        and expected_revision >= 1
        and isinstance(source.schema_artifact_id, str)
        and bool(source.schema_artifact_id)
    )


def _source_identity(source: DuplicatePlanningSource) -> dict[str, JsonValue]:
    profile_id = (
        source.profile_id if isinstance(source.profile_id, int) and source.profile_id > 0 else None
    )
    revision = source.revision if isinstance(source.revision, int) and source.revision > 0 else None
    return {
        "profile_id": profile_id,
        "revision": revision,
        "lifecycle_state": source.lifecycle_state
        if isinstance(source.lifecycle_state, str)
        else None,
        "artifact": None,
        "document_digest": _safe_digest(source.flags, _DOCUMENT_DOMAIN),
        "compliance_digest": _safe_digest(source.compliance, _COMPLIANCE_DOMAIN),
        "baseline_provenance_digest": _safe_digest(source.baseline_provenance, ""),
        "extension_provenance_digest": _safe_digest(source.extension_provenance, ""),
        "certificate_provenance_digest": _safe_digest(source.certificate_provenance, ""),
        "metadata_digest": _safe_digest(source.metadata, _METADATA_DOMAIN),
    }


def _normalized_metadata(metadata: Mapping[str, Any]) -> dict[str, JsonValue]:
    copied = strict_json_copy(metadata)
    if not isinstance(copied, dict) or set(copied) != set(_METADATA_FIELDS):
        raise ValueError("duplicate source metadata is incomplete")
    ordered = {field: copied[field] for field in _METADATA_FIELDS}
    if not isinstance(ordered["name"], str):
        raise ValueError("duplicate source metadata is invalid")
    for field in _METADATA_FIELDS[1:]:
        if ordered[field] is not None and not isinstance(ordered[field], str):
            raise ValueError("duplicate source metadata is invalid")
    return ordered


def _as_document(value: Mapping[str, Any]) -> dict[str, JsonValue]:
    copied = strict_json_copy(value)
    if not isinstance(copied, dict):
        raise ValueError("duplicate source document is invalid")
    return copied


def _conversion_projection(plan: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """Retain the complete value-safe pairwise proof without private candidates."""

    return {
        "kind": "cross-schema",
        "plan_digest": plan.get("plan_digest"),
        "recipe_registry": deepcopy(plan.get("recipe_registry")),
        "compatibility": deepcopy(plan.get("compatibility")),
        "entries": deepcopy(plan.get("entries")),
        "target_validation": deepcopy(plan.get("target_validation")),
        "compliance": deepcopy(plan.get("compliance")),
        "warnings": deepcopy(plan.get("warnings")),
        "blockers": deepcopy(plan.get("blockers")),
    }


def _compose_preset(
    base_document: dict[str, JsonValue],
    *,
    schema_id: str,
    schema_document: dict[str, JsonValue],
    preset_id: str,
) -> tuple[
    dict[str, JsonValue],
    dict[str, JsonValue],
    tuple[dict[str, JsonValue], ...],
    list[dict[str, JsonValue]],
]:
    if preset_id == "keep_current":
        return (
            deepcopy(base_document),
            {
                "selection": "keep_current",
                "identity": None,
                "decisions": [],
                "disposition": "custom-imported",
            },
            (),
            [],
        )
    try:
        preset_document = initialization._as_document(
            initialization._build_server_starter_document(preset_id, schema_id, schema_document)
        )
        identity = initialization._preset_identity(preset_id, schema_id, preset_document)
    except KeyError, ProfileConversionJsonError, TypeError, ValueError:
        return (
            deepcopy(base_document),
            {"selection": preset_id, "identity": None, "decisions": []},
            (),
            [{"code": "duplicate_preset_invalid", "path": ""}],
        )

    candidate = deepcopy(base_document)
    decisions: list[dict[str, JsonValue]] = []
    blockers: list[dict[str, JsonValue]] = []
    _fill_absent_preset_paths(
        candidate,
        preset_document,
        path=("policies",),
        identity=identity,
        decisions=decisions,
        blockers=blockers,
    )
    ordered_decisions = tuple(
        sorted(decisions, key=lambda decision: str(decision["path"]).encode("utf-16-be"))
    )
    return (
        candidate,
        {
            "selection": preset_id,
            "identity": _json_object(identity),
            "decisions": list(ordered_decisions),
            "disposition": "recomposed",
        },
        ordered_decisions,
        sorted(blockers, key=lambda blocker: (str(blocker["path"]), str(blocker["code"]))),
    )


def _fill_absent_preset_paths(
    base: dict[str, JsonValue],
    preset: dict[str, JsonValue],
    *,
    path: tuple[str | int, ...],
    identity: Mapping[str, str],
    decisions: list[dict[str, JsonValue]],
    blockers: list[dict[str, JsonValue]],
) -> None:
    for key in ordered_keys(preset):
        preset_value = preset[key]
        child_path = (*path, key)
        if key not in base:
            base[key] = deepcopy(preset_value)
            for leaf_path in _leaf_paths(preset_value, child_path):
                decisions.append(_preset_decision(leaf_path, "filled-absent", identity))
            continue
        base_value = base[key]
        if isinstance(base_value, dict) and isinstance(preset_value, dict):
            _fill_absent_preset_paths(
                base_value,
                preset_value,
                path=child_path,
                identity=identity,
                decisions=decisions,
                blockers=blockers,
            )
            continue
        if isinstance(base_value, dict) != isinstance(preset_value, dict):
            for leaf_path in _leaf_paths(preset_value, child_path):
                decisions.append(
                    _preset_decision(leaf_path, "blocked-structural-collision", identity)
                )
                blockers.append(
                    {"code": "duplicate_preset_structural_collision", "path": leaf_path}
                )
            continue
        decision = (
            "source-identical" if _canonical_equal(base_value, preset_value) else "source-preserved"
        )
        for leaf_path in _leaf_paths(preset_value, child_path):
            decisions.append(_preset_decision(leaf_path, decision, identity))


def _preset_decision(
    path: str,
    decision: str,
    identity: Mapping[str, str],
) -> dict[str, JsonValue]:
    return {
        "path": path,
        "decision": decision,
        "source": "starter-catalog",
        "catalog_id": identity["catalog_id"],
        "catalog_version": identity["catalog_version"],
        "preset_id": identity["preset_id"],
        "definition_sha256": identity["definition_sha256"],
    }


def _compose_cis(
    *,
    base_document: dict[str, JsonValue],
    schema_id: str,
    cis_baseline_id: str,
    source_compliance: JsonValue,
    inherited_compliance: JsonValue,
) -> dict[str, Any]:
    if cis_baseline_id == CIS_LAYER_NONE:
        return {
            "status": "valid",
            "reason_code": None,
            "document": deepcopy(base_document),
            "compliance": deepcopy(inherited_compliance),
            "decisions": (),
            "projection": {
                "selection": CIS_LAYER_NONE,
                "identity": None,
                "decisions": [],
                "disposition": "none",
                "source_compliance": {
                    "disposition": "preserved-inert",
                    "source_digest": _compliance_digest(source_compliance),
                    "target_digest": _compliance_digest(inherited_compliance),
                },
            },
        }
    resolved = initialization._compose_cis(
        base_document=base_document,
        schema_id=schema_id,
        cis_baseline_id=cis_baseline_id,
    )
    decisions = resolved["decisions"]
    identity = resolved["identity"]
    projection = {
        "selection": cis_baseline_id,
        "identity": deepcopy(identity),
        "decisions": list(decisions),
        "disposition": "recomposed",
        "source_compliance": {
            "disposition": "replaced-by-selected-cis",
            "source_digest": _compliance_digest(source_compliance),
            "target_digest": _compliance_digest(resolved["compliance"]),
        },
    }
    return {
        "status": resolved["status"],
        "reason_code": resolved["reason_code"],
        "document": resolved["document"],
        "compliance": resolved["compliance"],
        "decisions": decisions,
        "projection": projection,
    }


def _cis_selection_matches(provenance: JsonValue, selection: str) -> bool:
    if not isinstance(provenance, dict):
        return False
    cis = provenance.get("cis")
    if not isinstance(cis, dict):
        return False
    if selection == CIS_LAYER_NONE:
        return cis.get("identity_state") == "none"
    return cis.get("identity_state") == "catalog" and cis.get("baseline_id") == selection


def _starter_identity_projection(provenance: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(provenance, dict)
    starter = provenance["starter"]
    assert isinstance(starter, dict)
    return {
        "identity_state": starter["identity_state"],
        "catalog_id": starter["catalog_id"],
        "catalog_version": starter["catalog_version"],
        "preset_id": starter.get("preset_id"),
        "definition_sha256": starter["definition_sha256"],
        "resolved_schema_artifact_id": starter["resolved_schema_artifact_id"],
        "disposition": starter["disposition"],
    }


def _cis_identity_projection(provenance: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(provenance, dict)
    cis = provenance["cis"]
    assert isinstance(cis, dict)
    return {
        "identity_state": cis["identity_state"],
        "catalog_id": cis["catalog_id"],
        "catalog_version": cis["catalog_version"],
        "baseline_id": cis["baseline_id"],
        "benchmark_id": cis["benchmark_id"],
        "benchmark_version": cis["benchmark_version"],
        "layer_sha256": cis["layer_sha256"],
        "merge_rules_sha256": cis["merge_rules_sha256"],
        "merge_result_sha256": cis["merge_result_sha256"],
        "resolved_schema_artifact_id": cis["resolved_schema_artifact_id"],
        "proof_digest": cis["proof_digest"],
        "display_status": cis["display_status"],
        "current_claim": cis["current_claim"],
        "reason_code": cis["reason_code"],
    }


def _duplicate_provenance(
    source_provenance: JsonValue,
    *,
    source_profile_id: int,
    source_revision: int,
    lineage_plan_digest: str,
    target_schema_id: str,
    carry_forward: bool,
    preset: Mapping[str, JsonValue],
    cis: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    if carry_forward:
        assert isinstance(source_provenance, dict)
        provenance = deepcopy(source_provenance)
        assert isinstance(provenance, dict)
        starter = provenance.get("starter")
        assert isinstance(starter, dict)
        # ``keep_current`` remains a request-only directive.  The duplicate
        # retains the source's exact catalog preset identity, while this
        # stored disposition truthfully tells M5 that it preserved source
        # settings rather than reapplying a preset.
        starter["disposition"] = "preserved"
    else:
        starter = _duplicate_starter_provenance(preset, target_schema_id)
        cis_provenance = _duplicate_cis_provenance(cis)
        provenance = {
            "contract_id": PROVENANCE_CONTRACT_ID,
            "contract_version": PROVENANCE_CONTRACT_VERSION,
            "lineage": {},
            "starter": starter,
            "cis": cis_provenance,
        }
    provenance["lineage"] = {
        "kind": "duplicate",
        "source_profile_id": source_profile_id,
        "source_revision": source_revision,
        "plan_digest": lineage_plan_digest,
    }
    return provenance


def _duplicate_starter_provenance(
    preset: Mapping[str, JsonValue], target_schema_id: str
) -> dict[str, JsonValue]:
    identity = preset.get("identity")
    if not isinstance(identity, dict):
        return {
            "identity_state": "custom-imported",
            "catalog_id": None,
            "catalog_version": None,
            "preset_id": None,
            "definition_sha256": None,
            "resolved_schema_artifact_id": None,
            "disposition": "custom-imported",
        }
    return {
        "identity_state": "catalog",
        "catalog_id": identity["catalog_id"],
        "catalog_version": identity["catalog_version"],
        "preset_id": identity["preset_id"],
        "definition_sha256": identity["definition_sha256"],
        "resolved_schema_artifact_id": target_schema_id,
        "disposition": "recomposed",
    }


def _duplicate_cis_provenance(cis: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    identity = cis.get("identity")
    if not isinstance(identity, dict):
        return {
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
    return {"identity_state": "catalog", **deepcopy(identity)}


def _validation_projection(
    issues: list[PolicyValidationIssue],
    schema: Mapping[str, JsonValue],
    document: Mapping[str, JsonValue],
    artifact_id: str,
) -> dict[str, JsonValue]:
    properties = schema.get("properties")
    known = set(properties) if isinstance(properties, dict) else set()
    diagnostics: list[dict[str, JsonValue]] = []
    for issue in issues:
        code = (
            "target_policy_unsupported"
            if issue.policy is not None and issue.policy not in known
            else "target_value_invalid"
        )
        diagnostics.append(
            {
                "code": code,
                "policy_id": issue.policy,
                "path": pointer(("policies", *issue.path)),
            }
        )
    diagnostics.sort(key=lambda item: (str(item["code"]), str(item["path"])))
    return {
        "status": "valid" if not diagnostics else "invalid",
        "issue_count": len(diagnostics),
        "resolved_schema_artifact_id": artifact_id,
        "validated_document_digest": _document_digest(document),
        "validation_schema_sha256": _sha256_jcs(schema),
        "issues": _json_copy(diagnostics),
    }


def _lineage_digest(
    *,
    source: Mapping[str, JsonValue],
    target: Mapping[str, JsonValue],
    conversion: Mapping[str, JsonValue],
    preset_decisions: tuple[dict[str, JsonValue], ...],
    cis_decisions: tuple[dict[str, JsonValue], ...],
    document: Mapping[str, JsonValue],
    compliance: JsonValue,
    validation: Mapping[str, JsonValue],
) -> str:
    """Create the acyclic digest persisted in duplicate lineage.

    The final result digest binds the complete resulting provenance.  The
    provenance itself cannot contain that final digest without a hash cycle,
    so its ``lineage.plan_digest`` binds this complete pre-provenance
    derivation instead.
    """

    return _domain_digest(
        _LINEAGE_DOMAIN,
        {
            "source": source,
            "target": target,
            "conversion": conversion,
            "preset_decisions": list(preset_decisions),
            "cis_decisions": list(cis_decisions),
            "document": document,
            "compliance": compliance,
            "validation": validation,
        },
    )


def _terminal_result(
    *,
    status: DuplicatePlanningStatus,
    reason_code: str,
    source: dict[str, JsonValue],
    target: dict[str, JsonValue],
    conversion: dict[str, JsonValue],
    preset: dict[str, JsonValue],
    cis: dict[str, JsonValue],
    blockers: list[dict[str, JsonValue]] | None = None,
    validation: dict[str, JsonValue] | None = None,
) -> DuplicatePlanningResult:
    target_artifact = target.get("artifact")
    resolved_validation = validation or {
        "status": "not-run",
        "issue_count": 0,
        "resolved_schema_artifact_id": (
            target_artifact.get("artifact_id") if isinstance(target_artifact, dict) else None
        ),
        "validated_document_digest": None,
        "validation_schema_sha256": None,
        "issues": [],
    }
    result_digest = _domain_digest(
        _RESULT_DOMAIN,
        {
            "status": status,
            "reason_code": reason_code,
            "source": source,
            "target": target,
            "conversion": conversion,
            "preset": preset,
            "cis": cis,
            "validation": resolved_validation,
            "blockers": blockers or [],
        },
    )
    plan = _public_plan(
        status=status,
        reason_code=reason_code,
        source=source,
        target=target,
        conversion=conversion,
        preset=preset,
        cis=cis,
        validation=resolved_validation,
        blockers=blockers or [],
        result={
            "document_digest": None,
            "compliance_digest": None,
            "baseline_provenance_digest": None,
            "extension_provenance_digest": None,
            "certificate_provenance_digest": None,
            "result_digest": result_digest,
        },
    )
    return DuplicatePlanningResult(
        status=status,
        reason_code=reason_code,
        _plan=plan,
        _candidate_document=None,
        _candidate_compliance=None,
        _candidate_baseline_provenance=None,
        _candidate_extension_provenance=None,
        _candidate_certificate_provenance=None,
    )


def _public_plan(
    *,
    status: DuplicatePlanningStatus,
    reason_code: str | None,
    source: Mapping[str, JsonValue],
    target: Mapping[str, JsonValue],
    conversion: Mapping[str, JsonValue],
    preset: Mapping[str, JsonValue],
    cis: Mapping[str, JsonValue],
    validation: Mapping[str, JsonValue],
    blockers: list[dict[str, JsonValue]],
    result: Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    plan: dict[str, JsonValue] = {
        "kind": "profile-duplicate-plan",
        "contract_version": _CONTRACT_VERSION,
        "status": status,
        "reason_code": reason_code,
        "source": _json_copy(source),
        "target": _json_copy(target),
        "conversion": _json_copy(conversion),
        "preset": _json_copy(preset),
        "cis": _json_copy(cis),
        "validation": _json_copy(validation),
        "blockers": _json_copy(blockers),
        "result": _json_copy(result),
    }
    plan["plan_digest"] = _domain_digest(_PLAN_DOMAIN, plan)
    return plan


def _leaf_paths(value: JsonValue, path: tuple[str | int, ...]) -> list[str]:
    if isinstance(value, dict):
        if not value:
            return [pointer(path)]
        return [
            leaf for key in ordered_keys(value) for leaf in _leaf_paths(value[key], (*path, key))
        ]
    if isinstance(value, list):
        if not value:
            return [pointer(path)]
        return [
            leaf for index, item in enumerate(value) for leaf in _leaf_paths(item, (*path, index))
        ]
    return [pointer(path)]


def _canonical_equal(left: JsonValue, right: JsonValue) -> bool:
    return canonical_json(left) == canonical_json(right)


def _document_digest(document: Mapping[str, JsonValue]) -> str:
    return _domain_digest(_DOCUMENT_DOMAIN, {"policies": document})


def _compliance_digest(compliance: JsonValue) -> str:
    return _domain_digest(_COMPLIANCE_DOMAIN, compliance)


def _safe_digest(value: Any, domain: str) -> str | None:
    try:
        return _domain_digest(domain, value)
    except ProfileConversionJsonError, TypeError, ValueError:
        return None


def _json_copy(value: Any) -> JsonValue:
    """Return a strict JSON copy at public-plan container boundaries."""

    return strict_json_copy(value)


def _json_object(value: Any) -> dict[str, JsonValue]:
    copied = _json_copy(value)
    if not isinstance(copied, dict):
        raise ValueError("duplicate planner expected a JSON object")
    return copied


def _json_object_list(value: Any) -> list[dict[str, JsonValue]]:
    copied = _json_copy(value)
    if not isinstance(copied, list):
        raise ValueError("duplicate planner expected JSON object diagnostics")
    objects: list[dict[str, JsonValue]] = []
    for item in copied:
        if not isinstance(item, dict):
            raise ValueError("duplicate planner expected JSON object diagnostics")
        objects.append(item)
    return objects


def _sha256_jcs(value: Any) -> str:
    return hashlib.sha256(canonical_json(strict_json_copy(value))).hexdigest()


def _domain_digest(domain: str, value: Any) -> str:
    return hashlib.sha256(
        domain.encode("utf-8") + canonical_json(strict_json_copy(value))
    ).hexdigest()
