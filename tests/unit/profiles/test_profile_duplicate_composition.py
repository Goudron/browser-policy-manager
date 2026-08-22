from __future__ import annotations

import copy
import json

import pytest

from app.compliance.firefox.profile_duplicate_composition import (
    DuplicatePlanningSource,
    plan_profile_duplicate,
)
from app.compliance.firefox.profile_initialization_composition import (
    compose_profile_initialization,
)
from app.core.profile_baseline_provenance import generic_create_baseline_provenance
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS


def _source(
    *,
    schema_id: str = "release-153",
    flags: dict | None = None,
    compliance: object = None,
    provenance: dict | None = None,
    revision: int = 7,
) -> DuplicatePlanningSource:
    return DuplicatePlanningSource(
        profile_id=41,
        revision=revision,
        lifecycle_state="active",
        schema_artifact_id=schema_id,
        flags=flags or {},
        compliance=compliance,
        baseline_provenance=provenance or generic_create_baseline_provenance(),
        metadata={
            "name": "private source name",
            "description": "private source description",
            "created_at": "2026-08-20T10:00:00+00:00",
            "updated_at": "2026-08-20T10:00:00+00:00",
            "deleted_at": None,
        },
    )


def _plan(source: DuplicatePlanningSource, **overrides):
    return plan_profile_duplicate(
        source,
        expected_source_revision=overrides.pop("expected_source_revision", source.revision),
        target_schema_id=overrides.pop("target_schema_id", source.schema_artifact_id),
        preset_id=overrides.pop("preset_id", "keep_current"),
        cis_baseline_id=overrides.pop("cis_baseline_id", "none"),
        **overrides,
    )


def test_same_schema_exact_carry_forward_binds_source_artifact_revision_and_result() -> None:
    initialized = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="none",
    )
    assert initialized.is_valid
    assert initialized.baseline_provenance is not None
    result = _plan(
        _source(
            flags=initialized.document,
            provenance=initialized.baseline_provenance,
        )
    )

    assert result.is_valid
    assert result.candidate_document == {}
    assert result.candidate_compliance is None
    assert result.candidate_baseline_provenance is not None
    assert result.candidate_baseline_provenance["lineage"] == {
        "kind": "duplicate",
        "source_profile_id": 41,
        "source_revision": 7,
        "plan_digest": result.candidate_baseline_provenance["lineage"]["plan_digest"],
    }
    assert result.candidate_baseline_provenance["starter"] == {
        **initialized.baseline_provenance["starter"],
        "disposition": "preserved",
    }
    assert result.candidate_baseline_provenance["cis"] == initialized.baseline_provenance["cis"]

    plan = result.plan
    assert plan["source"]["profile_id"] == 41
    assert plan["source"]["revision"] == 7
    assert plan["source"]["artifact"]["artifact_id"] == "release-153"
    assert plan["target"]["artifact"]["artifact_id"] == "release-153"
    assert plan["conversion"]["kind"] == "same-schema-copy"
    assert plan["preset"]["identity"] == initialized.baseline_provenance["starter"]
    assert plan["cis"]["identity"] == initialized.baseline_provenance["cis"]
    assert plan["validation"]["status"] == "valid"
    assert plan["blockers"] == []
    assert len(plan["result"]["result_digest"]) == 64
    assert len(plan["plan_digest"]) == 64


def test_explicit_preset_fills_only_absent_paths_and_preserves_source_values() -> None:
    source = _source(flags={"DisableTelemetry": False})
    before = copy.deepcopy(source.flags)

    result = _plan(source, preset_id="basic_corporate")

    assert result.is_valid
    assert result.candidate_document is not None
    assert result.candidate_document["DisableTelemetry"] is False
    assert result.candidate_document["BlockAboutConfig"] is True
    assert source.flags == before
    decisions = result.plan["preset"]["decisions"]
    telemetry = next(item for item in decisions if item["path"] == "/policies/DisableTelemetry")
    assert telemetry["decision"] == "source-preserved"
    assert any(item["decision"] == "filled-absent" for item in decisions)
    assert result.candidate_baseline_provenance is not None
    assert result.candidate_baseline_provenance["starter"]["disposition"] == "recomposed"
    assert result.candidate_baseline_provenance["starter"]["preset_id"] == "basic_corporate"
    assert result.candidate_baseline_provenance["cis"]["identity_state"] == "none"


def test_cross_schema_reuses_conversion_proof_and_returns_private_independent_candidate() -> None:
    source = _source(schema_id="release-153", flags={"DisableTelemetry": True})
    before = copy.deepcopy(source.flags)

    result = _plan(source, target_schema_id="esr-153.0")

    assert result.is_valid
    plan = result.plan
    assert plan["conversion"]["kind"] == "cross-schema"
    assert plan["conversion"]["compatibility"]["applicable"] is True
    assert plan["conversion"]["entries"]
    assert plan["source"]["artifact"]["artifact_id"] == "release-153"
    assert plan["target"]["artifact"]["artifact_id"] == "esr-153.0"
    assert source.flags == before
    first = result.candidate_document
    second = result.candidate_document
    assert first is not None and second is not None
    first["DisableTelemetry"] = False
    assert second["DisableTelemetry"] is True


@pytest.mark.parametrize("source_schema", SUPPORTED_SCHEMA_CHANNELS)
@pytest.mark.parametrize("target_schema", SUPPORTED_SCHEMA_CHANNELS)
def test_every_schema_pair_binds_the_exact_source_and_target_artifacts(
    source_schema: str,
    target_schema: str,
) -> None:
    result = _plan(_source(schema_id=source_schema), target_schema_id=target_schema)

    assert result.is_valid
    plan = result.plan
    assert plan["source"]["artifact"]["artifact_id"] == source_schema
    assert plan["target"]["artifact"]["artifact_id"] == target_schema
    assert plan["validation"]["status"] == "valid"
    if source_schema == target_schema:
        assert plan["conversion"]["kind"] == "same-schema-copy"
    else:
        assert plan["conversion"]["kind"] == "cross-schema"
        assert plan["conversion"]["compatibility"]["applicable"] is True


def test_blocked_cross_schema_exposes_blockers_but_never_a_candidate() -> None:
    source = _source(
        schema_id="esr-153.0",
        flags={"AIControls": {"Default": {"Value": "blocked", "Locked": True}}},
    )
    before = copy.deepcopy(source.flags)

    result = _plan(source, target_schema_id="esr-115.39")

    assert result.status == "blocked"
    assert result.reason_code == "duplicate_conversion_blocked"
    assert result.candidate_document is None
    assert result.candidate_compliance is None
    assert result.plan["conversion"]["compatibility"]["applicable"] is False
    assert result.plan["conversion"]["blockers"]
    assert result.plan["blockers"]
    assert source.flags == before


def test_plan_is_value_safe_deterministic_and_never_exposes_source_values() -> None:
    secret_url = "https://private.example.invalid/only-source"
    source = _source(
        flags={"HttpAllowlist": [secret_url]},
        compliance={"operator_note": "private compliance note"},
    )

    first = _plan(source, preset_id="blank")
    second = _plan(copy.deepcopy(source), preset_id="blank")

    assert first.is_valid and second.is_valid
    assert first.plan == second.plan
    public = json.dumps(first.plan, ensure_ascii=False, sort_keys=True)
    for private_value in (
        secret_url,
        "private compliance note",
        "private source name",
        "private source description",
        "2026-08-20T10:00:00+00:00",
    ):
        assert private_value not in public


@pytest.mark.parametrize(
    ("expected_revision", "reason_code"),
    [(6, "duplicate_source_stale"), (0, "duplicate_source_invalid")],
)
def test_fixed_source_revision_rejects_stale_or_invalid_requests(
    expected_revision: int,
    reason_code: str,
) -> None:
    result = _plan(_source(), expected_source_revision=expected_revision)

    assert result.status == "blocked"
    assert result.reason_code == reason_code
    assert result.candidate_document is None
    assert result.plan["result"]["result_digest"]
