"""Deterministic, read-only Firefox profile schema-conversion planning.

This module is deliberately a domain boundary.  It knows how to bind a
profile's exact schema artifacts, construct a diagnostic target candidate and
prove complete JSON atom coverage.  It does not expose an HTTP route, write an
ORM object, or contain a conversion recipe.  M4-02 extends the bounded empty
registry below with reviewed recipes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.policy_validation import (
    PolicyValidationIssue,
    validate_profile_policies,
)
from app.core.profile_conversion_recipes import (
    EMPTY_CONVERSION_RECIPE_REGISTRY,
    ConversionRecipeRegistry,
    RecipeApplication,
)
from app.core.schema_channels import (
    SCHEMA_FILENAMES,
    SchemaChannel,
    get_schema_channel,
)
from app.core.schemas_loader import SchemaNotFoundError, UnsupportedProfileError, load_schema

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

_CONTRACT_VERSION = 1
_DOCUMENT_DOMAIN = "bpm-policy-document:v1\n"
_COMPLIANCE_DOMAIN = "bpm-profile-compliance:v1\n"
_METADATA_DOMAIN = "bpm-profile-metadata:v1\n"
_PLAN_DOMAIN = "bpm-profile-conversion-plan:v1\n"
_ENTRY_DOMAIN = "bpm-profile-conversion-entry:v1\n"
_MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
_PROFILE_METADATA_FIELDS = (
    "name",
    "description",
    "created_at",
    "updated_at",
    "deleted_at",
)
_PLAN_IDENTITY_FIELDS = (
    "kind",
    "contract_version",
    "profile",
    "source",
    "target",
    "recipe_registry",
    "compatibility",
    "entries",
    "target_validation",
    "compliance",
    "warnings",
    "blockers",
)


class ConversionPlanningError(ValueError):
    """A fail-closed precondition with a stable, locale-neutral code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ConversionPlannerInvariantError(RuntimeError):
    """Raised only if the planner itself cannot prove its coverage invariant."""


@dataclass(frozen=True, slots=True)
class ConversionComplianceReplan:
    """A target-bound compliance candidate supplied by a higher domain layer."""

    candidate_compliance: dict[str, JsonValue]
    target_cis_artifact_digest: str


type ComplianceReplanner = Callable[
    [JsonValue, SchemaChannel, SchemaChannel, dict[str, JsonValue], dict[str, JsonValue]],
    ConversionComplianceReplan | None,
]


@dataclass(frozen=True, slots=True)
class ConversionPlanningContext:
    """Non-policy profile state that M2-04 binds into a conversion plan.

    ``metadata`` must contain the five exact persisted metadata fields.  Their
    raw values are used solely to calculate the required digest and never
    appear in a plan.  The API/service layer will create this context in M4-03
    and M4-04; the planner remains independent of ORM models.
    """

    profile_id: int
    revision: int
    lifecycle_state: str
    metadata: Mapping[str, Any]
    compliance: Any = None
    recipe_registry: ConversionRecipeRegistry = EMPTY_CONVERSION_RECIPE_REGISTRY
    compliance_replanner: ComplianceReplanner | None = None


@dataclass(frozen=True, slots=True)
class ConversionPlanningResult:
    """A public plan plus private-copy diagnostic candidates for later apply.

    ``plan`` is the serializable M2-04 shape and contains no raw policy,
    compliance, metadata, clock or localized text.  Candidate accessors return
    fresh deep copies so callers cannot obtain shared references to the source
    document or to an earlier accessor result.
    """

    _plan: dict[str, JsonValue]
    _candidate_document: dict[str, JsonValue]
    _candidate_compliance: JsonValue

    @property
    def plan(self) -> dict[str, JsonValue]:
        return copy.deepcopy(self._plan)

    @property
    def candidate_document(self) -> dict[str, JsonValue]:
        return copy.deepcopy(self._candidate_document)

    @property
    def candidate_compliance(self) -> JsonValue:
        return copy.deepcopy(self._candidate_compliance)


@dataclass(slots=True)
class _EntryDraft:
    policy_id: str
    source_path: str
    target_path: str
    source_value: JsonValue
    target_value: JsonValue
    classification: str = "unchanged"
    reason_code: str = "policy_byte_identical"
    unchanged_kind: str | None = "byte-identical"
    recipe: dict[str, JsonValue] | None = None
    evidence_digest: str | None = None


def plan_profile_conversion(
    source_document: Mapping[str, Any],
    *,
    source_artifact_id: str,
    target_artifact_id: str,
    context: ConversionPlanningContext,
) -> ConversionPlanningResult:
    """Return a deterministic no-silent-loss plan for one directed artifact pair.

    Unknown, retired, unbundled, identical and source-invalid states are
    precondition failures represented by :class:`ConversionPlanningError`.
    A valid source with a target incompatibility returns a blocked plan after
    target validation; this distinction is required for a read-only preview.
    """

    source_channel = _resolve_source_channel(source_artifact_id)
    target_channel = _resolve_target_channel(target_artifact_id)
    if source_channel.artifact_id == target_channel.artifact_id:
        raise ConversionPlanningError("conversion_target_identical")

    source_artifact, source_schema = _load_artifact(source_channel, source=True)
    target_artifact, target_schema = _load_artifact(target_channel, source=False)
    profile, metadata, source_compliance = _normalize_context(context)
    normalized_document = _normalize_source_document(source_document)
    policies = normalized_document["policies"]
    assert isinstance(policies, dict)

    if validate_profile_policies(policies, source_schema):
        raise ConversionPlanningError("conversion_source_invalid")

    # Recipes are applied only inside their exact reviewed domain.  A failed
    # recipe leaves its source atom untouched in the diagnostic candidate so
    # target validation still runs and the source document remains immutable.
    candidate_document = copy.deepcopy(normalized_document)
    candidate_policies = candidate_document["policies"]
    assert isinstance(candidate_policies, dict)
    applications = _apply_recipes(
        policies,
        candidate_policies,
        context.recipe_registry,
        source_artifact,
        target_artifact,
    )
    entries = _initial_entries(policies, candidate_policies, applications)
    try:
        _assert_atom_coverage(entries, policies, candidate_policies)
    except ConversionPlannerInvariantError:
        # A recipe may never make a candidate's atom accounting implicit.  The
        # failed attempted transforms are discarded and reported as blockers.
        candidate_document = copy.deepcopy(normalized_document)
        candidate_policies = candidate_document["policies"]
        assert isinstance(candidate_policies, dict)
        applications = {
            path: RecipeApplication(application.recipe, None, "transform_target_coverage_mismatch")
            for path, application in applications.items()
            if application.failure_code is None
        }
        entries = _initial_entries(policies, candidate_policies, applications)
        _assert_atom_coverage(entries, policies, candidate_policies)

    target_issues = validate_profile_policies(candidate_policies, target_schema)
    target_diagnostics = _target_diagnostics(target_issues, target_schema)
    _block_entries_for_target_issues(entries, target_diagnostics)
    _assert_atom_coverage(entries, policies, candidate_policies)

    target_validation = {
        "status": "valid" if not target_diagnostics else "invalid",
        "validated_document_digest": _domain_digest(_DOCUMENT_DOMAIN, candidate_document),
        "validation_schema_sha256": target_artifact["validation_schema_sha256"],
        "issues": target_diagnostics,
    }
    compliance, candidate_compliance, compliance_warnings = _plan_compliance(
        source_compliance,
        source_channel,
        target_channel,
        source_policies=policies,
        target_policies=candidate_policies,
        compliance_replanner=context.compliance_replanner,
    )
    entry_values = [_finalize_entry(entry) for entry in _ordered_entries(entries)]
    blockers = _diagnostics_for_blocked_entries(entries, target_diagnostics)
    warnings = _sort_diagnostics(compliance_warnings)
    compatibility = _compatibility(entry_values, target_diagnostics, warnings, blockers)
    plan: dict[str, JsonValue] = {
        "kind": "profile-conversion-plan",
        "contract_version": _CONTRACT_VERSION,
        "profile": profile,
        "source": _strict_json_copy(
            {
                "artifact": source_artifact,
                "document_digest": _domain_digest(_DOCUMENT_DOMAIN, normalized_document),
                "compliance_digest": _domain_digest(_COMPLIANCE_DOMAIN, source_compliance),
            }
        ),
        "target": _strict_json_copy(
            {
                "artifact": target_artifact,
                "candidate_document_digest": _domain_digest(_DOCUMENT_DOMAIN, candidate_document),
            }
        ),
        "recipe_registry": _strict_json_copy(context.recipe_registry.as_identity()),
        "compatibility": compatibility,
        "entries": _strict_json_copy(entry_values),
        "target_validation": _strict_json_copy(target_validation),
        "compliance": compliance,
        "warnings": _strict_json_copy(warnings),
        "blockers": _strict_json_copy(blockers),
    }
    plan["plan_digest"] = _domain_digest(
        _PLAN_DOMAIN,
        {field: plan[field] for field in _PLAN_IDENTITY_FIELDS},
    )
    _assert_strict_json(plan)
    return ConversionPlanningResult(plan, candidate_document, candidate_compliance)


def _normalize_context(
    context: ConversionPlanningContext,
) -> tuple[dict[str, JsonValue], dict[str, JsonValue], JsonValue]:
    if isinstance(context.profile_id, bool) or context.profile_id < 1:
        raise ConversionPlanningError("conversion_source_invalid")
    if isinstance(context.revision, bool) or context.revision < 1:
        raise ConversionPlanningError("conversion_source_invalid")
    if context.lifecycle_state != "active":
        raise ConversionPlanningError("conversion_source_not_active")
    if not isinstance(context.recipe_registry, ConversionRecipeRegistry):
        raise ConversionPlanningError("conversion_source_invalid")

    metadata = _strict_json_copy(context.metadata)
    # The mapping is rebuilt in contract order below, so an input declaration
    # order cannot affect identity.  Missing or surplus fields, however, would
    # make a metadata digest insufficient for a later apply recheck.
    if not isinstance(metadata, dict) or set(metadata) != set(_PROFILE_METADATA_FIELDS):
        raise ConversionPlanningError("conversion_source_invalid")
    ordered_metadata = {field: metadata[field] for field in _PROFILE_METADATA_FIELDS}
    if not isinstance(ordered_metadata["name"], str):
        raise ConversionPlanningError("conversion_source_invalid")
    for optional_field in ("description", "created_at", "updated_at", "deleted_at"):
        if ordered_metadata[optional_field] is not None and not isinstance(
            ordered_metadata[optional_field], str
        ):
            raise ConversionPlanningError("conversion_source_invalid")
    compliance = _strict_json_copy(context.compliance)
    return (
        {
            "id": context.profile_id,
            "revision": context.revision,
            "lifecycle_state": context.lifecycle_state,
            "metadata_digest": _domain_digest(_METADATA_DOMAIN, ordered_metadata),
        },
        ordered_metadata,
        compliance,
    )


def _normalize_source_document(source_document: Mapping[str, Any]) -> dict[str, JsonValue]:
    document = _strict_json_copy(source_document)
    if not isinstance(document, dict) or set(document) != {"policies"}:
        raise ConversionPlanningError("conversion_source_invalid")
    policies = document["policies"]
    if not isinstance(policies, dict):
        raise ConversionPlanningError("conversion_source_invalid")
    return {"policies": policies}


def _resolve_source_channel(artifact_id: str) -> SchemaChannel:
    channel = get_schema_channel(artifact_id)
    if channel is None:
        raise ConversionPlanningError("schema_channel_unknown")
    if channel.support_state == "retired" or not channel.selectable:
        raise ConversionPlanningError("schema_channel_retired_requires_migration")
    if artifact_id not in SCHEMA_FILENAMES:
        raise ConversionPlanningError("conversion_source_schema_missing")
    return channel


def _resolve_target_channel(artifact_id: str) -> SchemaChannel:
    channel = get_schema_channel(artifact_id)
    if channel is None:
        raise ConversionPlanningError("schema_channel_unknown")
    if channel.support_state == "retired" or not channel.selectable:
        raise ConversionPlanningError("schema_channel_retired")
    if artifact_id not in SCHEMA_FILENAMES:
        raise ConversionPlanningError("conversion_target_unsupported")
    return channel


def _load_artifact(
    channel: SchemaChannel,
    *,
    source: bool,
) -> tuple[dict[str, JsonValue], dict[str, JsonValue]]:
    missing_code = (
        "conversion_source_schema_missing" if source else "conversion_target_schema_missing"
    )
    bundle_path = Path(__file__).resolve().parents[2] / channel.source.output_path
    try:
        bundle_bytes = bundle_path.read_bytes()
        # The loader's normalized schema is the validator identity, while raw
        # checked-in bundle bytes remain the provenance identity.
        normalized_schema = _strict_json_copy(load_schema(channel.artifact_id))
    except (OSError, SchemaNotFoundError, UnsupportedProfileError, ValueError, KeyError) as exc:
        raise ConversionPlanningError(missing_code) from exc
    if not isinstance(normalized_schema, dict):
        raise ConversionPlanningError(missing_code)
    return (
        {
            "line_id": channel.line_id,
            "artifact_id": channel.artifact_id,
            "channel_id": channel.channel_id,
            "artifact_version": channel.artifact_version,
            "source_tag": channel.source_tag,
            "schema_bundle_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
            "validation_schema_sha256": _sha256_jcs(normalized_schema),
        },
        normalized_schema,
    )


def _initial_entries(
    source_policies: dict[str, JsonValue],
    target_policies: dict[str, JsonValue],
    applications: Mapping[str, RecipeApplication],
) -> list[_EntryDraft]:
    target_atoms = dict(_policy_atoms(target_policies))
    entries: list[_EntryDraft] = []
    for source_path, source_value in _policy_atoms(source_policies):
        policy_id = _policy_id_for_path(source_path)
        application = applications.get(source_path)
        if application is not None:
            if application.failure_code is not None:
                entries.append(
                    _EntryDraft(
                        policy_id=policy_id,
                        source_path=source_path,
                        target_path=source_path,
                        source_value=source_value,
                        target_value=source_value,
                        classification="blocked",
                        reason_code=application.failure_code,
                        unchanged_kind=None,
                    )
                )
                continue
            target_path = application.recipe.target_path
            target_value = target_atoms.get(target_path)
            if target_value is None and target_path not in target_atoms:
                entries.append(
                    _EntryDraft(
                        policy_id=policy_id,
                        source_path=source_path,
                        target_path="",
                        source_value=source_value,
                        target_value=source_value,
                        classification="blocked",
                        reason_code="transform_target_coverage_mismatch",
                        unchanged_kind=None,
                    )
                )
                continue
            entries.append(
                _EntryDraft(
                    policy_id=policy_id,
                    source_path=source_path,
                    target_path=target_path,
                    source_value=source_value,
                    target_value=target_value,
                    classification="transformed",
                    reason_code="lossless_transformation_applied",
                    unchanged_kind=None,
                    recipe=application.recipe.as_identity(),
                    evidence_digest=application.recipe.evidence_digest,
                )
            )
            continue
        if source_path not in target_atoms:
            # This is unreachable until M4-02 recipes can change shape, but it
            # remains fail-closed rather than introducing an implicit drop.
            entries.append(
                _EntryDraft(
                    policy_id=policy_id,
                    source_path=source_path,
                    target_path="",
                    source_value=source_value,
                    target_value=source_value,
                    classification="blocked",
                    reason_code="transform_recipe_missing",
                    unchanged_kind=None,
                )
            )
            continue
        target_value = target_atoms[source_path]
        if _canonical_json(source_value) != _canonical_json(target_value):
            entries.append(
                _EntryDraft(
                    policy_id=policy_id,
                    source_path=source_path,
                    target_path=source_path,
                    source_value=source_value,
                    target_value=target_value,
                    classification="blocked",
                    reason_code="transform_recipe_missing",
                    unchanged_kind=None,
                )
            )
            continue
        entries.append(
            _EntryDraft(
                policy_id=policy_id,
                source_path=source_path,
                target_path=source_path,
                source_value=source_value,
                target_value=target_value,
            )
        )
    return entries


def _apply_recipes(
    source_policies: Mapping[str, JsonValue],
    candidate_policies: dict[str, JsonValue],
    registry: ConversionRecipeRegistry,
    source_artifact: Mapping[str, JsonValue],
    target_artifact: Mapping[str, JsonValue],
) -> dict[str, RecipeApplication]:
    """Apply exact recipes to a private candidate, never to the source tree."""

    applications: dict[str, RecipeApplication] = {}
    for source_path, source_value in _policy_atoms(source_policies):
        application = registry.apply(
            source_artifact=source_artifact,
            target_artifact=target_artifact,
            source_path=source_path,
            source_value=source_value,
        )
        if application is None:
            continue
        applications[source_path] = application
        if application.failure_code is not None:
            continue
        assert application.output is not None
        try:
            if application.recipe.source_path != application.recipe.target_path:
                _remove_policy_pointer(candidate_policies, application.recipe.source_path)
            _set_policy_pointer(
                candidate_policies,
                application.recipe.target_path,
                copy.deepcopy(application.output),
            )
        except ConversionPlannerInvariantError:
            applications[source_path] = RecipeApplication(
                application.recipe,
                None,
                "transform_target_coverage_mismatch",
            )
    return applications


def _target_diagnostics(
    issues: Sequence[PolicyValidationIssue],
    target_schema: dict[str, JsonValue],
) -> list[dict[str, JsonValue]]:
    properties = target_schema.get("properties")
    known_policies = set(properties) if isinstance(properties, dict) else set()
    diagnostics: list[dict[str, JsonValue]] = []
    for issue in issues:
        policy_id = issue.policy
        code = (
            "target_policy_unsupported"
            if policy_id is not None and policy_id not in known_policies
            else "target_value_invalid"
        )
        paths = [_pointer(("policies", *issue.path))]
        diagnostics.append(
            {"code": code, "policy_id": policy_id, "paths": _strict_json_copy(paths)}
        )
    return _sort_diagnostics(diagnostics)


def _block_entries_for_target_issues(
    entries: list[_EntryDraft],
    diagnostics: Sequence[dict[str, JsonValue]],
) -> None:
    for diagnostic in diagnostics:
        code = diagnostic["code"]
        paths = diagnostic["paths"]
        assert isinstance(code, str)
        assert isinstance(paths, list)
        affected = [
            entry
            for entry in entries
            if any(
                isinstance(path, str)
                and (
                    _pointer_prefix(path, entry.source_path)
                    or _pointer_prefix(entry.source_path, path)
                )
                for path in paths
            )
        ]
        if not affected:
            policy_id = diagnostic["policy_id"]
            if isinstance(policy_id, str):
                policy_root = _pointer(("policies", policy_id))
                affected = [
                    entry for entry in entries if _pointer_prefix(policy_root, entry.source_path)
                ]
        for entry in affected:
            # A recipe failure is the primary stable explanation.  Keep it
            # even though the mandatory target validator adds its independent
            # diagnostic to the plan's blocker collection.
            if entry.classification == "blocked":
                continue
            entry.classification = "blocked"
            entry.reason_code = code
            entry.unchanged_kind = None


def _diagnostics_for_blocked_entries(
    entries: Sequence[_EntryDraft],
    target_diagnostics: Sequence[dict[str, JsonValue]],
) -> list[dict[str, JsonValue]]:
    # Validation diagnostics explain target rejection.  Shape changes that are
    # impossible in M4-01 still receive a per-entry locale-neutral blocker.
    diagnostics = list(target_diagnostics)
    represented_paths: set[str] = set()
    for diagnostic in target_diagnostics:
        paths = diagnostic["paths"]
        if isinstance(paths, list):
            represented_paths.update(path for path in paths if isinstance(path, str))
    for entry in entries:
        if entry.classification != "blocked" or any(
            _pointer_prefix(path, entry.source_path) or _pointer_prefix(entry.source_path, path)
            for path in represented_paths
        ):
            continue
        diagnostics.append(
            {
                "code": entry.reason_code,
                "policy_id": entry.policy_id,
                "paths": [entry.source_path],
            }
        )
    return _sort_diagnostics(diagnostics)


def _finalize_entry(entry: _EntryDraft) -> dict[str, JsonValue]:
    recipe: JsonValue = entry.recipe
    projection: dict[str, JsonValue] = {
        "source_paths": [entry.source_path],
        "target_paths": [entry.target_path] if entry.target_path else [],
        "classification": entry.classification,
        "recipe": recipe,
    }
    return {
        "entry_id": _domain_digest(_ENTRY_DOMAIN, projection),
        "policy_id": entry.policy_id,
        **projection,
        "unchanged_kind": entry.unchanged_kind,
        "evidence_digest": entry.evidence_digest,
        "reason_code": entry.reason_code,
        "source_subtree_digest": _sha256_jcs(entry.source_value),
        "target_subtree_digest": (_sha256_jcs(entry.target_value) if entry.target_path else None),
    }


def _ordered_entries(entries: Sequence[_EntryDraft]) -> list[_EntryDraft]:
    return sorted(
        entries,
        key=lambda entry: (
            entry.source_path.encode("utf-8"),
            entry.source_path.encode("utf-8"),
            entry.target_path.encode("utf-8"),
            entry.classification,
        ),
    )


def _compatibility(
    entries: Sequence[dict[str, JsonValue]],
    target_diagnostics: Sequence[dict[str, JsonValue]],
    warnings: Sequence[dict[str, JsonValue]],
    blockers: Sequence[dict[str, JsonValue]],
) -> dict[str, JsonValue]:
    classifications = [
        entry["classification"] for entry in entries if isinstance(entry["classification"], str)
    ]
    target_atoms = sum(
        len(target_paths)
        for entry in entries
        if isinstance((target_paths := entry["target_paths"]), list)
    )
    blocked = classifications.count("blocked")
    transformed = classifications.count("transformed")
    target_valid = not target_diagnostics
    applicable = blocked == 0 and target_valid and not blockers
    status = (
        "blocked"
        if not applicable
        else "compatible-transformed"
        if transformed
        else "compatible-unchanged"
    )
    return {
        "status": status,
        "applicable": applicable,
        "counts": {
            "source_atoms": len(entries),
            "target_atoms": target_atoms,
            "unchanged_byte": sum(entry["unchanged_kind"] == "byte-identical" for entry in entries),
            "unchanged_semantic": sum(
                entry["unchanged_kind"] == "semantic-equivalent" for entry in entries
            ),
            "transformed": transformed,
            "blocked": blocked,
            "warnings": len(warnings),
            "blockers": len(blockers),
        },
    }


def _plan_compliance(
    source_compliance: JsonValue,
    source_channel: SchemaChannel,
    target_channel: SchemaChannel,
    *,
    source_policies: dict[str, JsonValue],
    target_policies: dict[str, JsonValue],
    compliance_replanner: ComplianceReplanner | None,
) -> tuple[dict[str, JsonValue], JsonValue, list[dict[str, JsonValue]]]:
    source_digest = _domain_digest(_COMPLIANCE_DOMAIN, source_compliance)
    if source_compliance is None:
        return (
            {
                "disposition": "absent",
                "reason_code": "compliance_absent",
                "source_digest": source_digest,
                "target_digest": source_digest,
                "target_claims_current": False,
                "target_cis_artifact_digest": None,
                "accounted_source_paths": [],
            },
            None,
            [],
        )
    recomputed = (
        compliance_replanner(
            source_compliance,
            source_channel,
            target_channel,
            source_policies,
            target_policies,
        )
        if compliance_replanner is not None
        else None
    )
    candidate_compliance: JsonValue
    if recomputed is not None:
        candidate_compliance = recomputed.candidate_compliance
        target_cis_artifact_digest = recomputed.target_cis_artifact_digest
        accounted_paths = [path for path, _value in _atoms(source_compliance, "")]
        return (
            {
                "disposition": "recomputed",
                "reason_code": "cis_target_compliance_recomputed",
                "source_digest": source_digest,
                "target_digest": _domain_digest(_COMPLIANCE_DOMAIN, candidate_compliance),
                "target_claims_current": True,
                "target_cis_artifact_digest": target_cis_artifact_digest,
                "accounted_source_paths": _strict_json_copy(accounted_paths),
            },
            candidate_compliance,
            [
                {
                    "code": "compliance_recomputed",
                    "policy_id": None,
                    "paths": _strict_json_copy(accounted_paths),
                }
            ],
        )
    candidate_compliance = {
        "schema_version": 1,
        "status": "invalidated",
        "reason_code": "compliance_target_proof_unavailable",
        "source_artifact_id": source_channel.artifact_id,
        "target_artifact_id": target_channel.artifact_id,
        "source_compliance_digest": source_digest,
        "current_claims": False,
        "preserved_source": copy.deepcopy(source_compliance),
    }
    accounted_paths = [path for path, _value in _atoms(source_compliance, "")]
    return (
        {
            "disposition": "invalidated-preserved",
            "reason_code": "compliance_target_proof_unavailable",
            "source_digest": source_digest,
            "target_digest": _domain_digest(_COMPLIANCE_DOMAIN, candidate_compliance),
            "target_claims_current": False,
            "target_cis_artifact_digest": None,
            "accounted_source_paths": _strict_json_copy(accounted_paths),
        },
        candidate_compliance,
        [
            {
                "code": "compliance_invalidated",
                "policy_id": None,
                "paths": _strict_json_copy(accounted_paths),
            }
        ],
    )


def _policy_atoms(policies: Mapping[str, JsonValue]) -> list[tuple[str, JsonValue]]:
    atoms: list[tuple[str, JsonValue]] = []
    for policy_id in _ordered_keys(policies):
        atoms.extend(_atoms(policies[policy_id], _pointer(("policies", policy_id))))
    return atoms


def _atoms(value: JsonValue, pointer: str) -> list[tuple[str, JsonValue]]:
    if isinstance(value, dict):
        if not value:
            return [(pointer, value)]
        atoms: list[tuple[str, JsonValue]] = []
        for key in _ordered_keys(value):
            atoms.extend(_atoms(value[key], _pointer((*_pointer_parts(pointer), key))))
        return atoms
    if isinstance(value, list):
        if not value:
            return [(pointer, value)]
        atoms = []
        for index, item in enumerate(value):
            atoms.extend(_atoms(item, _pointer((*_pointer_parts(pointer), str(index)))))
        return atoms
    return [(pointer, value)]


def _assert_atom_coverage(
    entries: Sequence[_EntryDraft],
    source_policies: Mapping[str, JsonValue],
    target_policies: Mapping[str, JsonValue],
) -> None:
    expected_source = [path for path, _value in _policy_atoms(source_policies)]
    expected_target = [path for path, _value in _policy_atoms(target_policies)]
    actual_source = [entry.source_path for entry in entries]
    actual_target = [entry.target_path for entry in entries if entry.target_path]
    if (
        sorted(actual_source, key=lambda path: path.encode("utf-8"))
        != sorted(expected_source, key=lambda path: path.encode("utf-8"))
        or len(actual_source) != len(set(actual_source))
        or sorted(actual_target, key=lambda path: path.encode("utf-8"))
        != sorted(expected_target, key=lambda path: path.encode("utf-8"))
        or len(actual_target) != len(set(actual_target))
    ):
        raise ConversionPlannerInvariantError("conversion atom coverage is incomplete")


def _sort_diagnostics(
    diagnostics: Sequence[dict[str, JsonValue]],
) -> list[dict[str, JsonValue]]:
    return sorted(
        (copy.deepcopy(diagnostic) for diagnostic in diagnostics),
        key=lambda diagnostic: (
            str(diagnostic["code"]),
            "" if diagnostic["policy_id"] is None else str(diagnostic["policy_id"]),
            tuple(path.encode("utf-8") for path in _diagnostic_paths(diagnostic)),
        ),
    )


def _diagnostic_paths(diagnostic: Mapping[str, JsonValue]) -> tuple[str, ...]:
    """Return only the validated string paths from one public diagnostic."""
    value = diagnostic["paths"]
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _policy_id_for_path(path: str) -> str:
    parts = _pointer_parts(path)
    if len(parts) < 2 or parts[0] != "policies":
        raise ConversionPlannerInvariantError("policy atom has no policy identifier")
    return parts[1]


def _pointer(parts: Sequence[str | int]) -> str:
    return "/" + "/".join(_escape_pointer_part(str(part)) for part in parts)


def _pointer_parts(pointer: str) -> tuple[str, ...]:
    if not pointer:
        return ()
    if not pointer.startswith("/"):
        raise ConversionPlannerInvariantError("invalid internal JSON pointer")
    return tuple(part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/"))


def _pointer_prefix(prefix: str, value: str) -> bool:
    return value == prefix or value.startswith(prefix + "/")


def _set_policy_pointer(
    policies: dict[str, JsonValue],
    pointer: str,
    value: JsonValue,
) -> None:
    parts = _pointer_parts(pointer)
    if len(parts) < 2 or parts[0] != "policies":
        raise ConversionPlannerInvariantError("recipe target lies outside policy contract")
    current: dict[str, JsonValue] = policies
    for part in parts[1:-1]:
        next_value = current.get(part)
        if next_value is None:
            next_value = {}
            current[part] = next_value
        if not isinstance(next_value, dict):
            raise ConversionPlannerInvariantError("recipe target parent is not an object")
        current = next_value
    current[parts[-1]] = value


def _remove_policy_pointer(policies: dict[str, JsonValue], pointer: str) -> None:
    parts = _pointer_parts(pointer)
    if len(parts) < 2 or parts[0] != "policies":
        raise ConversionPlannerInvariantError("recipe source lies outside policy contract")
    chain: list[tuple[dict[str, JsonValue], str]] = []
    current: dict[str, JsonValue] = policies
    for part in parts[1:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            raise ConversionPlannerInvariantError("recipe source parent is not an object")
        chain.append((current, part))
        current = next_value
    if parts[-1] not in current:
        raise ConversionPlannerInvariantError("recipe source pointer is missing")
    del current[parts[-1]]
    # Empty containers created only by a renamed source atom must not become
    # unaccounted target atoms.  Never prune the outer ``policies`` object.
    for parent, key in reversed(chain):
        child = parent[key]
        if isinstance(child, dict) and not child:
            del parent[key]
        else:
            break


def _escape_pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _ordered_keys(value: Mapping[str, JsonValue]) -> list[str]:
    return sorted(value, key=lambda key: key.encode("utf-16-be"))


def _strict_json_copy(value: Any, ancestors: set[int] | None = None) -> JsonValue:
    """Deep-copy strict JSON/I-JSON without coercion or shared references."""

    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ConversionPlanningError("conversion_source_invalid") from exc
        return value
    if isinstance(value, int):
        if not -_MAX_SAFE_JSON_INTEGER <= value <= _MAX_SAFE_JSON_INTEGER:
            raise ConversionPlanningError("conversion_source_invalid")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ConversionPlanningError("conversion_source_invalid")
        return value
    ancestors = set() if ancestors is None else ancestors
    if isinstance(value, Mapping):
        object_id = id(value)
        if object_id in ancestors:
            raise ConversionPlanningError("conversion_source_invalid")
        descendants = {*ancestors, object_id}
        copied: dict[str, JsonValue] = {}
        for key in value:
            if not isinstance(key, str) or key in copied:
                raise ConversionPlanningError("conversion_source_invalid")
            copied[_strict_json_copy(key, descendants)] = _strict_json_copy(value[key], descendants)  # type: ignore[index]
        return copied
    if isinstance(value, list):
        object_id = id(value)
        if object_id in ancestors:
            raise ConversionPlanningError("conversion_source_invalid")
        descendants = {*ancestors, object_id}
        return [_strict_json_copy(item, descendants) for item in value]
    raise ConversionPlanningError("conversion_source_invalid")


def _assert_strict_json(value: JsonValue) -> None:
    _strict_json_copy(value)


def _canonical_json(value: JsonValue) -> bytes:
    """Serialize strict JSON as RFC 8785 JCS bytes.

    Python's native JSON encoder is used only for strings, whose escaping rules
    match JCS after the strict Unicode gate.  Objects use RFC 8785 UTF-16 key
    order and numbers use the ECMAScript spelling thresholds (not Python's
    scientific-notation spelling).
    """

    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if isinstance(value, int):
        return str(value).encode("ascii")
    if isinstance(value, float):
        return _jcs_number(value).encode("ascii")
    if isinstance(value, list):
        return b"[" + b",".join(_canonical_json(item) for item in value) + b"]"
    if isinstance(value, dict):
        serialized = []
        for key in _ordered_keys(value):
            serialized.append(_canonical_json(key) + b":" + _canonical_json(value[key]))
        return b"{" + b",".join(serialized) + b"}"
    raise ConversionPlannerInvariantError("non-JSON value reached canonical serializer")


def _jcs_number(value: float) -> str:
    if not math.isfinite(value):
        raise ConversionPlannerInvariantError("non-finite value reached canonical serializer")
    if value == 0:
        return "0"
    lexical = repr(value).lower()
    mantissa, separator, exponent_text = lexical.partition("e")
    exponent = int(exponent_text) if separator else 0
    absolute = abs(value)
    if 1e-6 <= absolute < 1e21:
        if separator:
            return _expand_scientific(mantissa, exponent)
        return mantissa[:-2] if mantissa.endswith(".0") else mantissa
    if not separator:
        # ``repr`` uses fixed notation for a few values at the JCS boundary.
        mantissa, exponent = _scientific_from_fixed(mantissa)
    mantissa = mantissa[:-2] if mantissa.endswith(".0") else mantissa
    sign = "+" if exponent >= 0 else "-"
    return f"{mantissa}e{sign}{abs(exponent)}"


def _expand_scientific(mantissa: str, exponent: int) -> str:
    sign = ""
    if mantissa.startswith("-"):
        sign, mantissa = "-", mantissa[1:]
    whole, dot, fraction = mantissa.partition(".")
    digits = whole + fraction
    decimal_index = len(whole) + exponent
    if decimal_index <= 0:
        return sign + "0." + ("0" * -decimal_index) + digits
    if decimal_index >= len(digits):
        return sign + digits + ("0" * (decimal_index - len(digits)))
    return sign + digits[:decimal_index] + "." + digits[decimal_index:]


def _scientific_from_fixed(value: str) -> tuple[str, int]:
    sign = ""
    if value.startswith("-"):
        sign, value = "-", value[1:]
    whole, dot, fraction = value.partition(".")
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return "0", 0
    if whole.lstrip("0"):
        exponent = len(whole.lstrip("0")) - 1
    else:
        exponent = -(len(fraction) - len(fraction.lstrip("0")) + 1)
    remainder = digits[1:].rstrip("0")
    return sign + digits[0] + ("." + remainder if remainder else ""), exponent


def _sha256_jcs(value: JsonValue) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _domain_digest(domain: str, value: JsonValue) -> str:
    return hashlib.sha256(domain.encode("utf-8") + _canonical_json(value)).hexdigest()
