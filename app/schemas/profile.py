# app/schemas/profile.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.schema_channels import DEFAULT_SCHEMA_CHANNEL


class ProfileBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    # Keep free-form; business logic enforces supported values elsewhere
    schema_version: str = Field(default=DEFAULT_SCHEMA_CHANNEL, max_length=50)
    flags: dict[str, Any] = Field(default_factory=dict)
    compliance: dict[str, Any] | None = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    description: str | None = None
    schema_version: str | None = Field(
        default=None,
        max_length=50,
        description=(
            "Deprecated for existing policy/compliance data: use the conversion preview and "
            "apply flow instead."
        ),
        json_schema_extra={"deprecated": True},
    )
    flags: dict[str, Any] | None = None
    compliance: dict[str, Any] | None = None
    expected_revision: int | None = Field(default=None, ge=1)


class ProfileRead(ProfileBase):
    id: int
    revision: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    is_deleted: bool
    validation_state: str = "not_validated"
    recommendation: ProfileRecommendation | None = None

    # Pydantic v2 style config (replaces deprecated class Config)
    model_config = ConfigDict(from_attributes=True)


class ProfileRecommendationArtifact(BaseModel):
    line_id: str
    artifact_id: str

    model_config = ConfigDict(extra="forbid")


class ProfileRecommendationTarget(ProfileRecommendationArtifact):
    label: str
    i18n_key: str


class ProfileRecommendationAction(BaseModel):
    action_id: Literal["conversion-preview"]
    preview_target_artifact_id: str

    model_config = ConfigDict(extra="forbid")


class ProfileRecommendation(BaseModel):
    """Value-free planning hint; M5-02 renders it without applying a change."""

    recommendation_id: Literal["schema-conversion.older-esr-recommendation"]
    reason_code: Literal["supported_older_esr_to_latest_esr"]
    profile_revision: int = Field(ge=1)
    source: ProfileRecommendationArtifact
    target: ProfileRecommendationTarget
    action: ProfileRecommendationAction

    model_config = ConfigDict(extra="forbid")


class ConversionPreviewRequest(BaseModel):
    """The only caller-controlled input to a conversion preview."""

    target_artifact_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Exact selectable target Firefox schema artifact ID.",
    )

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={"example": {"target_artifact_id": "esr-153.0"}},
    )


class ConversionArtifactIdentity(BaseModel):
    line_id: str
    artifact_id: str
    channel_id: str
    artifact_version: str
    source_tag: str
    schema_bundle_sha256: str
    validation_schema_sha256: str

    model_config = ConfigDict(extra="forbid")


class ConversionSourceIdentity(BaseModel):
    artifact: ConversionArtifactIdentity
    document_digest: str
    compliance_digest: str

    model_config = ConfigDict(extra="forbid")


class ConversionTargetIdentity(BaseModel):
    artifact: ConversionArtifactIdentity
    candidate_document_digest: str

    model_config = ConfigDict(extra="forbid")


class ConversionProfileIdentity(BaseModel):
    id: int = Field(ge=1)
    revision: int = Field(ge=1)
    lifecycle_state: Literal["active", "deleted"]
    metadata_digest: str

    model_config = ConfigDict(extra="forbid")


class ConversionRecipeUse(BaseModel):
    recipe_id: str
    recipe_version: int = Field(ge=1)
    definition_digest: str
    evidence_digest: str
    evidence_kind: Literal["reversible", "semantic-equivalence"]

    model_config = ConfigDict(extra="forbid")


class ConversionRegistryIdentity(BaseModel):
    registry_id: Literal["firefox-profile-conversion"]
    registry_version: int = Field(ge=1)
    registry_digest: str
    recipes: list[ConversionRecipeUse]

    model_config = ConfigDict(extra="forbid")


class ConversionDiagnostic(BaseModel):
    code: str
    policy_id: str | None
    paths: list[str]

    model_config = ConfigDict(extra="forbid")


class ConversionPlanEntry(BaseModel):
    entry_id: str
    policy_id: str
    source_paths: list[str]
    target_paths: list[str]
    classification: Literal["unchanged", "transformed", "blocked"]
    unchanged_kind: Literal["byte-identical", "semantic-equivalent"] | None
    recipe: ConversionRecipeUse | None
    evidence_digest: str | None
    reason_code: str
    source_subtree_digest: str
    target_subtree_digest: str | None

    model_config = ConfigDict(extra="forbid")


class ConversionCompatibilityCounts(BaseModel):
    source_atoms: int = Field(ge=0)
    target_atoms: int = Field(ge=0)
    unchanged_byte: int = Field(ge=0)
    unchanged_semantic: int = Field(ge=0)
    transformed: int = Field(ge=0)
    blocked: int = Field(ge=0)
    warnings: int = Field(ge=0)
    blockers: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class ConversionCompatibility(BaseModel):
    status: Literal["compatible-unchanged", "compatible-transformed", "blocked"]
    applicable: bool
    counts: ConversionCompatibilityCounts

    model_config = ConfigDict(extra="forbid")


class ConversionTargetValidation(BaseModel):
    status: Literal["valid", "invalid", "not-run-precondition-failed"]
    validated_document_digest: str | None
    validation_schema_sha256: str
    issues: list[ConversionDiagnostic]

    model_config = ConfigDict(extra="forbid")


class ConversionComplianceDisposition(BaseModel):
    disposition: Literal["absent", "preserved-verified", "recomputed", "invalidated-preserved"]
    reason_code: str
    source_digest: str
    target_digest: str
    target_claims_current: bool
    target_cis_artifact_digest: str | None
    accounted_source_paths: list[str]

    model_config = ConfigDict(extra="forbid")


class ConversionPreviewResponse(BaseModel):
    """Public, value-free projection of a deterministic M2-04 plan."""

    available: Literal[True] = Field(
        description=(
            "Both exact source and target artifacts were available and a plan was computed. "
            "Availability does not mean the plan is applicable."
        )
    )
    kind: Literal["profile-conversion-plan"]
    contract_version: Literal[1]
    profile: ConversionProfileIdentity
    source: ConversionSourceIdentity
    target: ConversionTargetIdentity
    recipe_registry: ConversionRegistryIdentity
    compatibility: ConversionCompatibility
    entries: list[ConversionPlanEntry]
    target_validation: ConversionTargetValidation
    compliance: ConversionComplianceDisposition
    warnings: list[ConversionDiagnostic]
    blockers: list[ConversionDiagnostic]
    plan_digest: str

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "available": True,
                "kind": "profile-conversion-plan",
                "contract_version": 1,
                "profile": {
                    "id": 42,
                    "revision": 7,
                    "lifecycle_state": "active",
                    "metadata_digest": "5c9cb875043459c1a411dae253939e20e6625620890a5cb27ccb3a5954bef269",
                },
                "source": {
                    "artifact": {
                        "line_id": "esr-140",
                        "artifact_id": "esr-140.13",
                        "channel_id": "esr-140.13",
                        "artifact_version": "140.13",
                        "source_tag": "mozilla-policy-templates-v7.12",
                        "schema_bundle_sha256": "0" * 64,
                        "validation_schema_sha256": "1" * 64,
                    },
                    "document_digest": "2" * 64,
                    "compliance_digest": "3" * 64,
                },
                "target": {
                    "artifact": {
                        "line_id": "esr-153",
                        "artifact_id": "esr-153.0",
                        "channel_id": "esr-153.0",
                        "artifact_version": "153.0",
                        "source_tag": "mozilla-policy-templates-v8.0",
                        "schema_bundle_sha256": "4" * 64,
                        "validation_schema_sha256": "5" * 64,
                    },
                    "candidate_document_digest": "6" * 64,
                },
                "recipe_registry": {
                    "registry_id": "firefox-profile-conversion",
                    "registry_version": 1,
                    "registry_digest": "7" * 64,
                    "recipes": [],
                },
                "compatibility": {
                    "status": "compatible-unchanged",
                    "applicable": True,
                    "counts": {
                        "source_atoms": 0,
                        "target_atoms": 0,
                        "unchanged_byte": 0,
                        "unchanged_semantic": 0,
                        "transformed": 0,
                        "blocked": 0,
                        "warnings": 0,
                        "blockers": 0,
                    },
                },
                "entries": [],
                "target_validation": {
                    "status": "valid",
                    "validated_document_digest": "6" * 64,
                    "validation_schema_sha256": "5" * 64,
                    "issues": [],
                },
                "compliance": {
                    "disposition": "absent",
                    "reason_code": "compliance_absent",
                    "source_digest": "3" * 64,
                    "target_digest": "3" * 64,
                    "target_claims_current": False,
                    "target_cis_artifact_digest": None,
                    "accounted_source_paths": [],
                },
                "warnings": [],
                "blockers": [],
                "plan_digest": "8" * 64,
            }
        },
    )


class ConversionPreviewError(BaseModel):
    kind: Literal["profile-conversion-error"]
    contract_version: Literal[1]
    code: str
    http_status: Literal[404, 409, 422, 500, 503]
    profile_id: int | None
    expected_revision: int | None
    current_revision: int | None
    plan_digest: str | None
    retry_preview_required: bool
    mutation: Literal["none"]
    parameters: dict[str, str | int | bool | None]

    model_config = ConfigDict(extra="forbid")


class ConversionPreviewErrorEnvelope(BaseModel):
    detail: ConversionPreviewError

    model_config = ConfigDict(extra="forbid")


class ConversionLineArtifactReference(BaseModel):
    """Stable lifecycle line plus exact selectable schema artifact."""

    line_id: str = Field(..., min_length=1, max_length=50)
    artifact_id: str = Field(..., min_length=1, max_length=50)

    model_config = ConfigDict(extra="forbid", strict=True)


class ConversionApplyRequest(BaseModel):
    """Value-free confirmation bound to one exact conversion preview."""

    kind: Literal["profile-conversion-apply-request"]
    contract_version: Literal[1]
    profile_id: int = Field(..., ge=1)
    expected_revision: int = Field(..., ge=1)
    source: ConversionLineArtifactReference
    target: ConversionLineArtifactReference
    target_artifact_id: str = Field(..., min_length=1, max_length=50)
    plan_digest: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    source_document_digest: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    source_compliance_digest: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    source_metadata_digest: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    source_validation_schema_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    target_validation_schema_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    recipe_registry_version: int = Field(..., ge=1)
    recipe_registry_digest: str = Field(..., pattern=r"^[a-f0-9]{64}$")

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={
            "example": {
                "kind": "profile-conversion-apply-request",
                "contract_version": 1,
                "profile_id": 42,
                "expected_revision": 7,
                "source": {"line_id": "esr-140", "artifact_id": "esr-140.13"},
                "target": {"line_id": "esr-153", "artifact_id": "esr-153.0"},
                "target_artifact_id": "esr-153.0",
                "plan_digest": "0" * 64,
                "source_document_digest": "1" * 64,
                "source_compliance_digest": "2" * 64,
                "source_metadata_digest": "3" * 64,
                "source_validation_schema_sha256": "4" * 64,
                "target_validation_schema_sha256": "5" * 64,
                "recipe_registry_version": 1,
                "recipe_registry_digest": "6" * 64,
            }
        },
    )


class ConversionFieldAccounting(BaseModel):
    application_write_fields: list[str]
    database_managed_fields: list[str]
    preserved_fields: list[str]
    updated_at_changed: bool

    model_config = ConfigDict(extra="forbid")


class ConversionApplyResponse(BaseModel):
    """Value-free record of one committed profile conversion."""

    kind: Literal["profile-conversion-result"]
    contract_version: Literal[1]
    status: Literal["applied"]
    profile_id: int = Field(ge=1)
    source_revision: int = Field(ge=1)
    result_revision: int = Field(ge=2)
    source: ConversionLineArtifactReference
    target: ConversionLineArtifactReference
    plan_digest: str
    result_document_digest: str
    result_compliance_digest: str
    compliance: ConversionComplianceDisposition
    target_validation: ConversionTargetValidation
    field_accounting: ConversionFieldAccounting

    model_config = ConfigDict(extra="forbid")


class ConversionApplyErrorEnvelope(BaseModel):
    detail: ConversionPreviewError

    model_config = ConfigDict(extra="forbid")
