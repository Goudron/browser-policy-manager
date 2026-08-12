"""Schema-wide, read-only retirement convertibility proof.

This module is deliberately narrower than the profile conversion planner.  A
planner can truthfully describe one stored document; retirement needs a proof
about *every* document valid under the source schema before an Alembic
revision, database preflight, or profile write is even allowed to exist.

The proof is consequently conservative.  It accepts only either an exact,
reviewed schema-containment attestation whose structural implication can be
checked locally, or an exhaustive finite-domain execution of M4's immutable
and reversible recipe registry.  Everything else is an uncovered RFC 6901
location, never a best-effort conversion or a sampled-profile shortcut.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for

from app.core.lifecycle_transition_plan import (
    LifecycleTransitionPlan,
    RetirementSuccessorMapping,
)
from app.core.profile_conversion_json import canonical_json, pointer, strict_json_copy
from app.core.profile_conversion_recipes import (
    EMPTY_CONVERSION_RECIPE_REGISTRY,
    ConversionRecipeRegistry,
)
from app.core.schema_channels import SchemaChannel
from app.core.schemas_loader import _normalize_schema

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]

_PROOF_DOMAIN = "bpm-retired-esr-total-proof:v1\n"
_RESULT_DOMAIN = "bpm-retired-esr-total-preflight:v1\n"
_EXACT_PROOF_ARTIFACT_DOMAIN = "bpm-retired-esr-exact-proof-artifact:v1\n"
_SHA256_LENGTH = 64
_ANNOTATION_KEYWORDS = frozenset(
    {
        "$schema",
        "$comment",
        "default",
        "deprecated",
        "description",
        "examples",
        "markdownDescription",
        "readOnly",
        "title",
        "writeOnly",
    }
)


class RetirementConvertibilityPreflightError(ValueError):
    """A source/target proof input is malformed or cannot be exactly bound."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sha256_jcs(value: JsonValue) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _is_sha256(value: str) -> bool:
    return len(value) == _SHA256_LENGTH and all(
        character in "0123456789abcdef" for character in value
    )


def _json_pointer_parts(value: str) -> tuple[str, ...] | None:
    if value == "":
        return ()
    if not value.startswith("/"):
        return None
    parts: list[str] = []
    for part in value[1:].split("/"):
        index = 0
        unescaped = ""
        while index < len(part):
            character = part[index]
            if character != "~":
                unescaped += character
                index += 1
                continue
            if index + 1 >= len(part) or part[index + 1] not in "01":
                return None
            unescaped += "~" if part[index + 1] == "0" else "/"
            index += 2
        parts.append(unescaped)
    return tuple(parts)


def _schema_pointer_for_policy(policy_id: str) -> str:
    return pointer(("properties", policy_id))


def _policy_pointer(policy_id: str) -> str:
    return pointer((policy_id,))


def _property_name_from_pointer(value: str) -> str | None:
    parts = _json_pointer_parts(value)
    if parts is None or len(parts) != 1:
        return None
    return parts[0]


def _sorted_uncovered(
    items: Iterable[UncoveredSchemaLocation],
) -> tuple[UncoveredSchemaLocation, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                item.source_schema_pointer.encode("utf-8"),
                item.source_atom_pointer.encode("utf-8"),
                item.reason_code,
            ),
        )
    )


@dataclass(frozen=True, slots=True)
class SchemaArtifactBinding:
    """Exact source or target bundle plus its normalized validator identity."""

    line_id: str
    artifact_id: str
    schema_bundle_sha256: str
    validation_schema_sha256: str
    _normalized_schema: JsonValue

    def __post_init__(self) -> None:
        if not self.line_id or not self.artifact_id:
            raise RetirementConvertibilityPreflightError("retirement_schema_identity_invalid")
        if not _is_sha256(self.schema_bundle_sha256) or not _is_sha256(
            self.validation_schema_sha256
        ):
            raise RetirementConvertibilityPreflightError("retirement_schema_digest_invalid")
        try:
            schema = strict_json_copy(self._normalized_schema)
        except ValueError as exc:
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed") from exc
        if not isinstance(schema, dict):
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed")
        if _sha256_jcs(schema) != self.validation_schema_sha256:
            raise RetirementConvertibilityPreflightError("retirement_schema_digest_stale")
        try:
            validator_for(schema).check_schema(schema)
        except SchemaError as exc:
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed") from exc
        object.__setattr__(self, "_normalized_schema", schema)

    @classmethod
    def from_schema(
        cls,
        *,
        line_id: str,
        artifact_id: str,
        bundle_bytes: bytes,
        normalized_schema: Mapping[str, Any],
    ) -> SchemaArtifactBinding:
        """Bind an already-normalized schema used by a synthetic proof fixture."""
        try:
            schema = strict_json_copy(normalized_schema)
        except ValueError as exc:
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed") from exc
        if not isinstance(schema, dict):
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed")
        return cls(
            line_id=line_id,
            artifact_id=artifact_id,
            schema_bundle_sha256=_sha256_bytes(bundle_bytes),
            validation_schema_sha256=_sha256_jcs(schema),
            _normalized_schema=schema,
        )

    @classmethod
    def from_channel(
        cls,
        channel: SchemaChannel,
        *,
        repository_root: Path | None = None,
    ) -> SchemaArtifactBinding:
        """Read one checked-in bundle without consulting runtime support state.

        The lifecycle candidate may mark its source row retired.  Loading by
        the runtime catalog would then be circular, so this bounded builder
        reads the candidate's reviewed output path directly and applies the
        same schema normalization as the validator loader.
        """
        if not isinstance(channel, SchemaChannel):
            raise RetirementConvertibilityPreflightError("retirement_schema_identity_invalid")
        root = Path(__file__).resolve().parents[2] if repository_root is None else repository_root
        path = root / channel.source.output_path
        try:
            bundle_bytes = path.read_bytes()
        except OSError as exc:
            raise RetirementConvertibilityPreflightError("retirement_schema_missing") from exc
        try:
            loaded = json.loads(bundle_bytes, object_pairs_hook=_reject_duplicate_json_keys)
            normalized = _normalize_schema(loaded)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed") from exc
        if not isinstance(normalized, dict):
            raise RetirementConvertibilityPreflightError("retirement_schema_malformed")
        return cls.from_schema(
            line_id=channel.line_id,
            artifact_id=channel.artifact_id,
            bundle_bytes=bundle_bytes,
            normalized_schema=normalized,
        )

    @property
    def normalized_schema(self) -> dict[str, JsonValue]:
        schema = strict_json_copy(self._normalized_schema)
        assert isinstance(schema, dict)
        return schema

    def as_identity(self) -> dict[str, str]:
        return {
            "line_id": self.line_id,
            "artifact_id": self.artifact_id,
            "schema_bundle_sha256": self.schema_bundle_sha256,
            "validation_schema_sha256": self.validation_schema_sha256,
        }

    def as_recipe_artifact(self) -> dict[str, JsonValue]:
        return {
            "artifact_id": self.artifact_id,
            "validation_schema_sha256": self.validation_schema_sha256,
        }


@dataclass(frozen=True, slots=True)
class ReviewedSchemaContainment:
    """Immutable review record for semantic identity of an unchanged domain.

    JSON Schema proves acceptance, not a browser's semantic interpretation of
    a policy.  The record is therefore required in addition to local
    structural implication.  Its digest is part of the total-proof identity.
    """

    evidence_id: str
    evidence_digest: str
    source_artifact_id: str
    target_artifact_id: str
    source_validation_schema_sha256: str
    target_validation_schema_sha256: str
    source_schema_pointer: str = ""
    target_schema_pointer: str = ""
    proof_artifact_digest: str | None = None
    recipe_registry_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id or not _is_sha256(self.evidence_digest):
            raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")
        if not all(
            _is_sha256(value)
            for value in (
                self.source_validation_schema_sha256,
                self.target_validation_schema_sha256,
            )
        ):
            raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")
        if (
            _json_pointer_parts(self.source_schema_pointer) is None
            or _json_pointer_parts(self.target_schema_pointer) is None
        ):
            raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")
        if self.proof_artifact_digest is not None and not _is_sha256(self.proof_artifact_digest):
            raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")
        if self.recipe_registry_digest is not None and not _is_sha256(self.recipe_registry_digest):
            raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")
        if (self.proof_artifact_digest is None) != (self.recipe_registry_digest is None):
            raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")

    def matches(
        self,
        source: SchemaArtifactBinding,
        target: SchemaArtifactBinding,
        *,
        source_schema_pointer: str,
        target_schema_pointer: str,
    ) -> bool:
        return (
            self.source_artifact_id == source.artifact_id
            and self.target_artifact_id == target.artifact_id
            and self.source_validation_schema_sha256 == source.validation_schema_sha256
            and self.target_validation_schema_sha256 == target.validation_schema_sha256
            and self.source_schema_pointer == source_schema_pointer
            and self.target_schema_pointer == target_schema_pointer
        )

    def as_identity(self) -> dict[str, str]:
        result = {
            "evidence_id": self.evidence_id,
            "evidence_digest": self.evidence_digest,
            "source_schema_pointer": self.source_schema_pointer,
            "target_schema_pointer": self.target_schema_pointer,
        }
        if self.proof_artifact_digest is not None:
            assert self.recipe_registry_digest is not None
            result["proof_artifact_digest"] = self.proof_artifact_digest
            result["recipe_registry_digest"] = self.recipe_registry_digest
        return result


def load_exact_schema_containment_evidence(
    path: Path,
    *,
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    recipe_registry: ConversionRecipeRegistry = EMPTY_CONVERSION_RECIPE_REGISTRY,
) -> tuple[ReviewedSchemaContainment, ...]:
    """Load one reviewed immutable, exact-artifact containment proof.

    The proof document is deliberately not an executable recipe.  Its sole
    claim is that preserving every source-valid document unchanged is both
    target-valid and semantically reviewed for the exact two artifacts.  All
    structural implications are still rechecked by
    :func:`prove_retirement_total_convertibility`; this loader only prevents a
    stale or substituted review record from reaching that gate.
    """
    if not isinstance(path, Path):
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")
    if not isinstance(source, SchemaArtifactBinding) or not isinstance(
        target, SchemaArtifactBinding
    ):
        raise RetirementConvertibilityPreflightError("retirement_schema_artifact_identity_mismatch")
    if not isinstance(recipe_registry, ConversionRecipeRegistry):
        raise RetirementConvertibilityPreflightError("retirement_recipe_registry_invalid")
    try:
        loaded = json.loads(path.read_bytes(), object_pairs_hook=_reject_duplicate_json_keys)
        artifact = strict_json_copy(loaded)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid") from exc
    if not isinstance(artifact, dict):
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")

    artifact_digest = artifact.get("proof_artifact_digest")
    projection = {key: value for key, value in artifact.items() if key != "proof_artifact_digest"}
    if (
        artifact.get("kind") != "firefox-retirement-exact-schema-containment-proof"
        or artifact.get("contract_version") != 1
        or not isinstance(artifact_digest, str)
        or not _is_sha256(artifact_digest)
        or hashlib.sha256(
            _EXACT_PROOF_ARTIFACT_DOMAIN.encode("utf-8") + canonical_json(projection)
        ).hexdigest()
        != artifact_digest
    ):
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")

    if (
        artifact.get("method") != "schema-containment"
        or artifact.get("evidence_scope") != "production-exact-artifacts"
        or artifact.get("successor_line_id") != target.line_id
        or artifact.get("source") != source.as_identity()
        or artifact.get("target") != target.as_identity()
        or artifact.get("recipe_registry") != recipe_registry.as_identity()
    ):
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_identity_mismatch")

    semantic_attestation = artifact.get("semantic_attestation")
    evidence_rows = artifact.get("containment_evidence")
    if not isinstance(semantic_attestation, dict) or not isinstance(evidence_rows, list):
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")
    semantic_digest = _sha256_jcs(semantic_attestation)
    evidence: list[ReviewedSchemaContainment] = []
    for row in evidence_rows:
        if not isinstance(row, dict) or set(row) != {
            "evidence_id",
            "evidence_digest",
            "source_schema_pointer",
            "target_schema_pointer",
        }:
            raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")
        if row["evidence_digest"] != semantic_digest:
            raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")
        try:
            evidence.append(
                ReviewedSchemaContainment(
                    evidence_id=str(row["evidence_id"]),
                    evidence_digest=str(row["evidence_digest"]),
                    source_artifact_id=source.artifact_id,
                    target_artifact_id=target.artifact_id,
                    source_validation_schema_sha256=source.validation_schema_sha256,
                    target_validation_schema_sha256=target.validation_schema_sha256,
                    source_schema_pointer=str(row["source_schema_pointer"]),
                    target_schema_pointer=str(row["target_schema_pointer"]),
                    proof_artifact_digest=artifact_digest,
                    recipe_registry_digest=str(recipe_registry.as_identity()["registry_digest"]),
                )
            )
        except (TypeError, ValueError) as exc:
            raise RetirementConvertibilityPreflightError(
                "retirement_proof_artifact_invalid"
            ) from exc
    if not evidence:
        raise RetirementConvertibilityPreflightError("retirement_proof_artifact_invalid")
    return tuple(evidence)


@dataclass(frozen=True, slots=True)
class UncoveredSchemaLocation:
    """A source-schema domain that cannot yet be used for retirement."""

    source_schema_pointer: str
    source_atom_pointer: str
    reason_code: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source_schema_pointer": self.source_schema_pointer,
            "source_atom_pointer": self.source_atom_pointer,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True, slots=True)
class RetirementConvertibilityResult:
    """One deterministic, value-free proof outcome for one retirement edge."""

    source: SchemaArtifactBinding
    target: SchemaArtifactBinding
    successor_line_id: str
    recipe_registry_identity: dict[str, JsonValue]
    status: str
    method: str
    uncovered_schema_locations: tuple[UncoveredSchemaLocation, ...]
    proof_artifact_digest: str | None
    result_digest: str

    @property
    def promotable(self) -> bool:
        return self.status == "complete"

    @property
    def blockers(self) -> tuple[str, ...]:
        return () if self.promotable else ("retirement_total_convertibility_unproven",)

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "source": strict_json_copy(self.source.as_identity()),
            "target": strict_json_copy(self.target.as_identity()),
            "successor_line_id": self.successor_line_id,
            "recipe_registry": copy.deepcopy(self.recipe_registry_identity),
            "status": self.status,
            "method": self.method,
            "uncovered_schema_locations": strict_json_copy(
                [item.as_dict() for item in self.uncovered_schema_locations]
            ),
            "proof_artifact_digest": self.proof_artifact_digest,
            "blockers": list(self.blockers),
            "mutation": "none",
            "result_digest": self.result_digest,
        }


@dataclass(frozen=True, slots=True)
class RetirementConvertibilityReport:
    """All retirement edges from one already-valid lifecycle transition plan."""

    results: tuple[RetirementConvertibilityResult, ...]
    report_digest: str

    @property
    def promotable(self) -> bool:
        return bool(self.results) and all(result.promotable for result in self.results)

    def as_dict(self) -> dict[str, JsonValue]:
        return {
            "kind": "retirement-total-convertibility-report",
            "contract_version": 1,
            "status": "complete" if self.promotable else "rejected",
            "results": [result.as_dict() for result in self.results],
            "report_digest": self.report_digest,
        }


def prove_retirement_total_convertibility(
    transition_plan: LifecycleTransitionPlan,
    *,
    artifacts: Mapping[str, SchemaArtifactBinding],
    recipe_registry: ConversionRecipeRegistry = EMPTY_CONVERSION_RECIPE_REGISTRY,
    containment_evidence: Iterable[ReviewedSchemaContainment] = (),
) -> RetirementConvertibilityReport:
    """Prove all retired ESR mappings before any database or Alembic activity.

    ``artifacts`` is an explicit exact-artifact map, rather than a runtime
    lookup.  This lets a reviewed candidate catalog mark a source retired while
    its checked-in bundle remains available to the static gate.  No profile,
    ORM object, database connection, migration, API, or UI is accepted here.
    """
    if not isinstance(transition_plan, LifecycleTransitionPlan):
        raise RetirementConvertibilityPreflightError("retirement_transition_plan_invalid")
    if not isinstance(recipe_registry, ConversionRecipeRegistry):
        raise RetirementConvertibilityPreflightError("retirement_recipe_registry_invalid")
    evidence = tuple(containment_evidence)
    if not all(isinstance(item, ReviewedSchemaContainment) for item in evidence):
        raise RetirementConvertibilityPreflightError("retirement_containment_evidence_invalid")
    if not transition_plan.retirement_successor_mappings:
        raise RetirementConvertibilityPreflightError("retirement_transition_plan_empty")

    results: list[RetirementConvertibilityResult] = []
    for mapping in transition_plan.retirement_successor_mappings:
        source = _require_exact_artifact(
            artifacts, mapping.source.line_id, mapping.source.artifact_id
        )
        target = _require_exact_artifact(
            artifacts, mapping.target.line_id, mapping.target.artifact_id
        )
        results.append(
            _prove_mapping(
                mapping,
                source=source,
                target=target,
                recipe_registry=recipe_registry,
                containment_evidence=evidence,
            )
        )

    ordered_results = tuple(
        sorted(
            results,
            key=lambda result: (
                result.source.line_id.encode("utf-8"),
                result.source.artifact_id.encode("utf-8"),
                result.target.line_id.encode("utf-8"),
            ),
        )
    )
    projection: dict[str, JsonValue] = {
        "kind": "retirement-total-convertibility-report",
        "contract_version": 1,
        "results": [result.as_dict() for result in ordered_results],
    }
    return RetirementConvertibilityReport(
        results=ordered_results,
        report_digest=hashlib.sha256(
            _RESULT_DOMAIN.encode("utf-8") + canonical_json(projection)
        ).hexdigest(),
    )


def _require_exact_artifact(
    artifacts: Mapping[str, SchemaArtifactBinding], line_id: str, artifact_id: str
) -> SchemaArtifactBinding:
    item = artifacts.get(artifact_id)
    if not isinstance(item, SchemaArtifactBinding):
        raise RetirementConvertibilityPreflightError("retirement_schema_artifact_missing")
    if item.line_id != line_id or item.artifact_id != artifact_id:
        raise RetirementConvertibilityPreflightError("retirement_schema_artifact_identity_mismatch")
    return item


def _prove_mapping(
    mapping: RetirementSuccessorMapping,
    *,
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    recipe_registry: ConversionRecipeRegistry,
    containment_evidence: tuple[ReviewedSchemaContainment, ...],
) -> RetirementConvertibilityResult:
    if source.line_id != mapping.source.line_id or target.line_id != mapping.target.line_id:
        raise RetirementConvertibilityPreflightError("retirement_schema_artifact_identity_mismatch")
    registry_identity = recipe_registry.as_identity()
    source_schema = _effective_profile_root(source.normalized_schema)
    target_schema = _effective_profile_root(target.normalized_schema)

    shape_uncovered = _root_shape_uncovered(source_schema, target_schema)
    full_containment_uncovered = (
        _full_root_containment_uncovered(source_schema, target_schema)
        if not shape_uncovered
        else shape_uncovered
    )
    root_evidence = _matching_evidence(
        containment_evidence,
        source,
        target,
        source_schema_pointer="",
        target_schema_pointer="",
    )
    methods: set[str] = set()
    uncovered: list[UncoveredSchemaLocation] = []

    if not full_containment_uncovered and root_evidence is not None:
        methods.add("schema-containment")
    else:
        if full_containment_uncovered:
            uncovered.extend(full_containment_uncovered)
        else:
            uncovered.append(
                UncoveredSchemaLocation(
                    source_schema_pointer="",
                    source_atom_pointer="",
                    reason_code="retirement_semantic_containment_evidence_missing",
                )
            )

    # A root containment proof covers every source shape.  Otherwise we can
    # still prove a complete partition property-by-property, but only after
    # the root object shape itself is structurally safe.
    if root_evidence is None and not shape_uncovered:
        uncovered = _prove_top_level_partition(
            source_schema,
            target_schema,
            source=source,
            target=target,
            recipe_registry=recipe_registry,
            containment_evidence=containment_evidence,
        )
        if not uncovered:
            methods.add("complete-recipe-partition")

    ordered_uncovered = _sorted_uncovered(uncovered)
    exact_proof_artifact_digest: str | None = None
    if not ordered_uncovered and root_evidence is not None:
        exact_proof_artifact_digest = _bound_exact_proof_artifact_digest(
            root_evidence,
            recipe_registry_identity=registry_identity,
        )
        if root_evidence.proof_artifact_digest is not None and exact_proof_artifact_digest is None:
            ordered_uncovered = (
                UncoveredSchemaLocation(
                    source_schema_pointer="",
                    source_atom_pointer="",
                    reason_code="retirement_proof_artifact_registry_stale",
                ),
            )
    if ordered_uncovered:
        status = "rejected"
        method = "none"
        proof_digest = None
    else:
        status = "complete"
        method = (
            "schema-containment"
            if methods == {"schema-containment"}
            else "complete-recipe-partition"
        )
        proof_projection: dict[str, JsonValue] = {
            "source": strict_json_copy(source.as_identity()),
            "target": strict_json_copy(target.as_identity()),
            "successor_line_id": mapping.declared_successor_line_id,
            "method": method,
            "recipe_registry": registry_identity,
            "containment_evidence": strict_json_copy(
                [
                    item.as_identity()
                    for item in sorted(
                        containment_evidence,
                        key=lambda item: (
                            item.source_schema_pointer.encode("utf-8"),
                            item.target_schema_pointer.encode("utf-8"),
                            item.evidence_id,
                        ),
                    )
                    if item.matches(
                        source,
                        target,
                        source_schema_pointer=item.source_schema_pointer,
                        target_schema_pointer=item.target_schema_pointer,
                    )
                ]
            ),
        }
        proof_digest = (
            exact_proof_artifact_digest
            or hashlib.sha256(
                _PROOF_DOMAIN.encode("utf-8") + canonical_json(proof_projection)
            ).hexdigest()
        )

    result_projection: dict[str, JsonValue] = {
        "source": strict_json_copy(source.as_identity()),
        "target": strict_json_copy(target.as_identity()),
        "successor_line_id": mapping.declared_successor_line_id,
        "recipe_registry": registry_identity,
        "status": status,
        "method": method,
        "uncovered_schema_locations": strict_json_copy(
            [item.as_dict() for item in ordered_uncovered]
        ),
        "proof_artifact_digest": proof_digest,
        "blockers": [] if status == "complete" else ["retirement_total_convertibility_unproven"],
        "mutation": "none",
    }
    result_digest = hashlib.sha256(
        _RESULT_DOMAIN.encode("utf-8") + canonical_json(result_projection)
    ).hexdigest()
    return RetirementConvertibilityResult(
        source=source,
        target=target,
        successor_line_id=mapping.declared_successor_line_id,
        recipe_registry_identity=registry_identity,
        status=status,
        method=method,
        uncovered_schema_locations=ordered_uncovered,
        proof_artifact_digest=proof_digest,
        result_digest=result_digest,
    )


def _effective_profile_root(schema: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Mirror profile validation's root unknown-policy rejection without I/O."""
    root = strict_json_copy(schema)
    assert isinstance(root, dict)
    properties = root.get("properties")
    if isinstance(properties, dict) and properties:
        root["additionalProperties"] = False
    return root


def _root_shape_uncovered(
    source: dict[str, JsonValue], target: dict[str, JsonValue]
) -> list[UncoveredSchemaLocation]:
    """Check only object-shape implications that are sound without a solver."""
    source_properties = source.get("properties")
    target_properties = target.get("properties")
    if (
        source.get("type") != "object"
        or target.get("type") != "object"
        or not isinstance(source_properties, dict)
        or not isinstance(target_properties, dict)
    ):
        return [
            UncoveredSchemaLocation(
                source_schema_pointer="",
                source_atom_pointer="",
                reason_code="retirement_root_object_schema_unproven",
            )
        ]
    forbidden_shape_keywords = {
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "if",
        "then",
        "else",
        "patternProperties",
        "propertyNames",
        "dependentRequired",
        "dependentSchemas",
        "unevaluatedProperties",
        "minProperties",
        "maxProperties",
    }
    if any(keyword in source or keyword in target for keyword in forbidden_shape_keywords):
        return [
            UncoveredSchemaLocation(
                source_schema_pointer="",
                source_atom_pointer="",
                reason_code="retirement_root_shape_keyword_unproven",
            )
        ]
    if source.get("additionalProperties") is not False:
        return [
            UncoveredSchemaLocation(
                source_schema_pointer="",
                source_atom_pointer="",
                reason_code="retirement_dynamic_policy_key_unproven",
            )
        ]
    if _required_names(source) is None or _required_names(target) is None:
        return [
            UncoveredSchemaLocation(
                source_schema_pointer="/required",
                source_atom_pointer="",
                reason_code="retirement_root_required_shape_malformed",
            )
        ]
    return []


def _full_root_containment_uncovered(
    source: dict[str, JsonValue], target: dict[str, JsonValue]
) -> list[UncoveredSchemaLocation]:
    """Prove unchanged source documents are target-valid before root evidence.

    A semantic attestation may never turn a target-rejected source value into
    containment.  This pass is deliberately separate from the recipe-partition
    shape check because recipes may legitimately map one policy pointer to a
    different target pointer.
    """
    uncovered = _root_shape_uncovered(source, target)
    if uncovered:
        return uncovered
    source_properties = source["properties"]
    target_properties = target["properties"]
    assert isinstance(source_properties, dict)
    assert isinstance(target_properties, dict)
    for source_name in sorted(source_properties, key=lambda item: item.encode("utf-8")):
        target_node = target_properties.get(source_name)
        if target_node is None or not _schema_node_contained(
            source_properties[source_name], target_node
        ):
            uncovered.append(
                UncoveredSchemaLocation(
                    source_schema_pointer=_schema_pointer_for_policy(source_name),
                    source_atom_pointer=_policy_pointer(source_name),
                    reason_code="retirement_unchanged_target_containment_unproven",
                )
            )
    source_required = _required_names(source)
    target_required = _required_names(target)
    assert source_required is not None and target_required is not None
    if not target_required.issubset(source_required):
        uncovered.append(
            UncoveredSchemaLocation(
                source_schema_pointer="/required",
                source_atom_pointer="",
                reason_code="retirement_target_required_property_unproven",
            )
        )
    return uncovered


def _required_names(schema: Mapping[str, JsonValue]) -> set[str] | None:
    value = schema.get("required", [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return {item for item in value if isinstance(item, str)}


def _matching_evidence(
    evidence: Iterable[ReviewedSchemaContainment],
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    *,
    source_schema_pointer: str,
    target_schema_pointer: str,
) -> ReviewedSchemaContainment | None:
    matches = [
        item
        for item in evidence
        if item.matches(
            source,
            target,
            source_schema_pointer=source_schema_pointer,
            target_schema_pointer=target_schema_pointer,
        )
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _bound_exact_proof_artifact_digest(
    evidence: ReviewedSchemaContainment,
    *,
    recipe_registry_identity: Mapping[str, JsonValue],
) -> str | None:
    """Return an immutable artifact identity only when its registry still binds."""
    if evidence.proof_artifact_digest is None:
        return None
    registry_digest = recipe_registry_identity.get("registry_digest")
    if (
        evidence.recipe_registry_digest is None
        or not isinstance(registry_digest, str)
        or registry_digest != evidence.recipe_registry_digest
    ):
        return None
    return evidence.proof_artifact_digest


def _prove_top_level_partition(
    source_root: dict[str, JsonValue],
    target_root: dict[str, JsonValue],
    *,
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    recipe_registry: ConversionRecipeRegistry,
    containment_evidence: tuple[ReviewedSchemaContainment, ...],
) -> list[UncoveredSchemaLocation]:
    source_properties = source_root["properties"]
    target_properties = target_root["properties"]
    assert isinstance(source_properties, dict)
    assert isinstance(target_properties, dict)
    target_required = _required_names(target_root)
    source_required = _required_names(source_root)
    assert target_required is not None and source_required is not None

    uncovered: list[UncoveredSchemaLocation] = []
    target_names: dict[str, str] = {}
    source_names = sorted(source_properties, key=lambda item: item.encode("utf-8"))
    for source_name in source_names:
        source_node = source_properties[source_name]
        source_schema_pointer = _schema_pointer_for_policy(source_name)
        source_atom_pointer = _policy_pointer(source_name)
        target_name = source_name
        target_node = target_properties.get(target_name)
        semantic = (
            target_node is not None
            and _schema_node_contained(source_node, target_node)
            and _matching_evidence(
                containment_evidence,
                source,
                target,
                source_schema_pointer=source_schema_pointer,
                target_schema_pointer=source_schema_pointer,
            )
            is not None
        )
        if semantic:
            target_names[target_name] = source_name
            continue

        recipe_outcome = _prove_finite_recipe_domain(
            source_node,
            source_name=source_name,
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            target_properties=target_properties,
            source=source,
            target=target,
            recipe_registry=recipe_registry,
        )
        if isinstance(recipe_outcome, UncoveredSchemaLocation):
            uncovered.append(recipe_outcome)
            continue
        target_name = recipe_outcome
        if target_name in target_names:
            uncovered.append(
                UncoveredSchemaLocation(
                    source_schema_pointer=source_schema_pointer,
                    source_atom_pointer=source_atom_pointer,
                    reason_code="retirement_target_atom_ambiguous",
                )
            )
            continue
        target_names[target_name] = source_name

    # An optional source policy cannot satisfy a target-required policy.  The
    # check is after recipe routing so a reviewed source->target rename is not
    # accidentally rejected as a target-only property.
    for target_name in sorted(target_required, key=lambda item: item.encode("utf-8")):
        mapped_source_name = target_names.get(target_name)
        if mapped_source_name is None or mapped_source_name not in source_required:
            uncovered.append(
                UncoveredSchemaLocation(
                    source_schema_pointer="/required",
                    source_atom_pointer="",
                    reason_code="retirement_target_required_property_unproven",
                )
            )
            break
    return uncovered


def _schema_node_contained(source_node: JsonValue, target_node: JsonValue) -> bool:
    """Prove a bounded, additive JSON-Schema subset without sampling.

    This recognises only semantic identity after removing standard annotation
    keywords, finite enum/const widening, and optional-property additions to
    otherwise identical object schemas.  Anything outside those rules remains
    unproved.  In particular, it does not interpret a matching policy name as
    a semantic claim; that still requires :class:`ReviewedSchemaContainment`.
    """
    try:
        source_copy = strict_json_copy(source_node)
        target_copy = strict_json_copy(target_node)
    except ValueError:
        return False
    source_validation = _validation_projection(source_copy)
    target_validation = _validation_projection(target_copy)
    if canonical_json(source_validation) == canonical_json(target_validation):
        return True
    if target_validation is True or target_validation == {}:
        return True
    if source_validation is False:
        return True
    if not isinstance(source_validation, dict) or not isinstance(target_validation, dict):
        return False
    # A finite enum/const is the one non-identical branch whose implication can
    # be exhaustively evaluated without making a sample stand in for a domain.
    values = _finite_schema_values(source_validation)
    if values is not None:
        return all(_validates(target_validation, value) for value in values)
    return _additive_object_schema_contained(source_validation, target_validation)


def _validation_projection(value: JsonValue) -> JsonValue:
    """Remove JSON-Schema annotations that cannot affect validation."""
    if isinstance(value, list):
        return [_validation_projection(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: _validation_projection(item)
        for key, item in value.items()
        if key not in _ANNOTATION_KEYWORDS
    }


def _additive_object_schema_contained(
    source: dict[str, JsonValue], target: dict[str, JsonValue]
) -> bool:
    """Check the one structural widening we can prove recursively and exactly."""
    source_properties = source.get("properties")
    target_properties = target.get("properties")
    if not isinstance(source_properties, dict) or not isinstance(target_properties, dict):
        return False
    source_required = _required_names(source)
    target_required = _required_names(target)
    if (
        source_required is None
        or target_required is None
        or not target_required.issubset(source_required)
    ):
        return False

    for key in source.keys() | target.keys():
        if key in {"properties", "required", "additionalProperties"}:
            continue
        if source.get(key) != target.get(key):
            return False
    if not _additional_properties_contained(
        source.get("additionalProperties", True), target.get("additionalProperties", True)
    ):
        return False
    if not set(source_properties).issubset(target_properties):
        return False
    return all(
        _schema_node_contained(source_node, target_properties[name])
        for name, source_node in source_properties.items()
    )


def _additional_properties_contained(source: JsonValue, target: JsonValue) -> bool:
    """Prove target acceptance for every source dynamic object property."""
    if source is False:
        return True
    if target is True or target == {}:
        return True
    if source is True:
        return target is True or target == {}
    if isinstance(source, dict) and isinstance(target, dict):
        return _schema_node_contained(source, target)
    return source == target


def _finite_schema_values(schema: JsonValue) -> tuple[JsonValue, ...] | None:
    if not isinstance(schema, dict):
        return None
    if "const" in schema:
        try:
            value = strict_json_copy(schema["const"])
        except ValueError:
            return None
        return (value,)
    values = schema.get("enum")
    if not isinstance(values, list) or not values:
        return None
    try:
        copied = tuple(strict_json_copy(value) for value in values)
    except ValueError:
        return None
    unique: dict[bytes, JsonValue] = {canonical_json(value): value for value in copied}
    return tuple(value for _, value in sorted(unique.items(), key=lambda item: item[0]))


def _validates(schema: JsonValue, value: JsonValue) -> bool:
    if schema is True:
        return True
    if schema is False or not isinstance(schema, dict):
        return False
    try:
        validator = validator_for(schema)(schema)
    except SchemaError:
        return False
    return not list(validator.iter_errors(value))


def _prove_finite_recipe_domain(
    source_node: JsonValue,
    *,
    source_name: str,
    source_schema_pointer: str,
    source_atom_pointer: str,
    target_properties: Mapping[str, JsonValue],
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    recipe_registry: ConversionRecipeRegistry,
) -> str | UncoveredSchemaLocation:
    values = _finite_schema_values(source_node)
    if values is None:
        return UncoveredSchemaLocation(
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            reason_code="retirement_recipe_domain_not_finite",
        )
    source_path = _policy_pointer(source_name)
    applications = [
        recipe_registry.apply(
            source_artifact=source.as_recipe_artifact(),
            target_artifact=target.as_recipe_artifact(),
            source_path=source_path,
            source_value=value,
        )
        for value in values
    ]
    if any(application is None for application in applications):
        return UncoveredSchemaLocation(
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            reason_code="retirement_recipe_binding_missing",
        )
    typed_applications = [application for application in applications if application is not None]
    if any(application.failure_code is not None for application in typed_applications):
        return UncoveredSchemaLocation(
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            reason_code="retirement_recipe_partition_incomplete",
        )
    recipe_identities = {
        (
            application.recipe.recipe_id,
            application.recipe.recipe_version,
            application.recipe.definition_digest,
            application.recipe.evidence_digest,
            application.recipe.target_path,
        )
        for application in typed_applications
    }
    if len(recipe_identities) != 1:
        return UncoveredSchemaLocation(
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            reason_code="retirement_recipe_partition_ambiguous",
        )
    recipe = typed_applications[0].recipe
    target_name = _property_name_from_pointer(recipe.target_path)
    if target_name is None or target_name not in target_properties:
        return UncoveredSchemaLocation(
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            reason_code="retirement_recipe_target_atom_unproven",
        )
    target_node = target_properties[target_name]
    if any(
        application.output is None or not _validates(target_node, application.output)
        for application in typed_applications
    ):
        return UncoveredSchemaLocation(
            source_schema_pointer=source_schema_pointer,
            source_atom_pointer=source_atom_pointer,
            reason_code="retirement_recipe_output_invalid",
        )
    return target_name
