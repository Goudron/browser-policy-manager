from __future__ import annotations

import inspect

import pytest

from app.compliance.firefox import profile_initialization_composition as composition
from app.compliance.firefox.profile_initialization_composition import (
    compose_profile_initialization,
)
from app.core.firefox_starter_catalog import CIS_LAYER_OPTIONS, STARTER_PRESETS
from app.core.policy_validation import validate_profile_policies_for_channel
from app.core.profile_baseline_provenance import is_valid_baseline_provenance
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS


@pytest.mark.parametrize("schema_id", SUPPORTED_SCHEMA_CHANNELS)
@pytest.mark.parametrize("preset_id", sorted(STARTER_PRESETS))
@pytest.mark.parametrize("cis_baseline_id", sorted(CIS_LAYER_OPTIONS))
def test_every_supported_schema_preset_cis_selection_is_valid_or_stably_terminal(
    schema_id: str,
    preset_id: str,
    cis_baseline_id: str,
) -> None:
    result = compose_profile_initialization(
        schema_id=schema_id,
        preset_id=preset_id,
        cis_baseline_id=cis_baseline_id,
    )

    if preset_id == "keep_current":
        assert result.status == "blocked"
        assert result.reason_code == "initialization_preset_requires_source"
        assert result.document is None
        assert result.baseline_provenance is None
        return

    assert result.status == "valid"
    assert result.reason_code is None
    assert result.schema is not None
    assert result.schema["artifact_id"] == schema_id
    assert result.document is not None
    assert validate_profile_policies_for_channel(result.document, schema_id) == []
    assert result.baseline_provenance is not None
    assert is_valid_baseline_provenance(result.baseline_provenance)
    assert result.baseline_provenance["starter"] == {
        "identity_state": "catalog",
        "catalog_id": composition.STARTER_CATALOG_ID,
        "catalog_version": composition.STARTER_CATALOG_VERSION,
        "preset_id": preset_id,
        "definition_sha256": result.baseline_provenance["starter"]["definition_sha256"],
        "resolved_schema_artifact_id": schema_id,
        "disposition": "created",
    }
    assert result.preset_decisions
    assert all(decision["source"] == "starter-catalog" for decision in result.preset_decisions)
    assert all(decision["preset_id"] == preset_id for decision in result.preset_decisions)

    if cis_baseline_id == "none":
        assert result.compliance is None
        assert result.cis_decisions == ()
        assert result.baseline_provenance["cis"]["identity_state"] == "none"
        assert result.baseline_provenance["cis"]["display_status"] == "none"
    else:
        assert result.compliance is not None
        assert result.compliance["baseline_id"] == cis_baseline_id
        assert result.cis_decisions
        assert all(decision["source"] == "cis-merge" for decision in result.cis_decisions)
        assert all(
            decision["catalog_id"] == composition.CIS_CATALOG_ID
            for decision in result.cis_decisions
        )
        assert result.baseline_provenance["cis"]["identity_state"] == "catalog"
        assert result.baseline_provenance["cis"]["resolved_schema_artifact_id"] == schema_id


def test_composition_is_deterministic_source_attributed_and_does_not_share_documents() -> None:
    first = compose_profile_initialization(
        schema_id="release-153",
        preset_id="basic_corporate",
        cis_baseline_id="cis_l2",
    )
    second = compose_profile_initialization(
        schema_id="release-153",
        preset_id="basic_corporate",
        cis_baseline_id="cis_l2",
    )

    assert first.status == second.status == "valid"
    assert first.result_digest == second.result_digest
    assert first.document == second.document
    assert first.baseline_provenance == second.baseline_provenance
    assert first.preset_decisions == second.preset_decisions
    assert first.cis_decisions == second.cis_decisions
    assert [decision["path"] for decision in first.preset_decisions] == sorted(
        decision["path"] for decision in first.preset_decisions
    )
    assert first.document is not None
    assert second.document is not None
    first.document["DisableTelemetry"] = False
    assert second.document["DisableTelemetry"] is True

    cis = second.baseline_provenance["cis"] if second.baseline_provenance else {}
    assert cis["catalog_id"] == composition.CIS_CATALOG_ID
    assert cis["layer_sha256"]
    assert cis["merge_rules_sha256"]
    assert cis["merge_result_sha256"]
    assert cis["proof_digest"]
    assert cis["display_status"] == "manual-review"
    assert cis["current_claim"] is False
    assert cis["reason_code"] == "cis_merge_manual_review_required"


def test_cis_is_verified_only_when_the_target_merge_has_no_review_decision() -> None:
    verified = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="cis_l1",
    )

    assert verified.status == "valid"
    assert verified.baseline_provenance is not None
    cis = verified.baseline_provenance["cis"]
    assert cis["identity_state"] == "catalog"
    assert cis["display_status"] == "verified"
    assert cis["current_claim"] is True
    assert cis["reason_code"] is None


def test_composition_accepts_catalog_identities_only_not_client_composed_flags() -> None:
    assert tuple(inspect.signature(compose_profile_initialization).parameters) == (
        "schema_id",
        "preset_id",
        "cis_baseline_id",
    )
    with pytest.raises(TypeError):
        compose_profile_initialization(  # type: ignore[call-arg]
            schema_id="release-153",
            preset_id="blank",
            cis_baseline_id="none",
            flags={"DisableTelemetry": False},
        )


@pytest.mark.parametrize(
    ("schema_id", "preset_id", "cis_baseline_id", "reason_code"),
    [
        ("unknown-schema", "blank", "none", "initialization_schema_unavailable"),
        ("release-153", "unknown-preset", "none", "initialization_preset_unavailable"),
        ("release-153", "blank", "unknown-cis", "initialization_cis_unavailable"),
    ],
)
def test_unknown_catalog_identities_are_stable_unavailable_results(
    schema_id: str,
    preset_id: str,
    cis_baseline_id: str,
    reason_code: str,
) -> None:
    result = compose_profile_initialization(
        schema_id=schema_id,
        preset_id=preset_id,
        cis_baseline_id=cis_baseline_id,
    )

    assert result.status == "unavailable"
    assert result.reason_code == reason_code
    assert result.document is None
    assert result.baseline_provenance is None


def test_unavailable_cis_layer_does_not_fall_back_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        composition,
        "cis_layer_availability",
        lambda schema_id: {
            "available": False,
            "reason_code": "cis_benchmark_not_validated_for_schema",
        },
    )

    result = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="cis_l1",
    )

    assert result.status == "unavailable"
    assert result.reason_code == "cis_benchmark_not_validated_for_schema"
    assert result.document is None
    assert result.baseline_provenance is None


def test_invalid_cis_catalog_is_a_stable_blocker(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(composition, "CIS_BASE_DIR", tmp_path)

    result = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="cis_l1",
    )

    assert result.status == "blocked"
    assert result.reason_code == "initialization_cis_catalog_invalid"
    assert result.document is None
    assert result.baseline_provenance is None


def test_final_target_validation_blocks_without_exposing_a_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(composition, "validate_profile_policies", lambda *_: [object()])

    result = compose_profile_initialization(
        schema_id="release-153",
        preset_id="blank",
        cis_baseline_id="none",
    )

    assert result.status == "blocked"
    assert result.reason_code == "initialization_candidate_invalid"
    assert result.document is None
    assert result.baseline_provenance is None
    assert result.validation == {
        "status": "invalid",
        "issue_count": 1,
        "resolved_schema_artifact_id": "release-153",
    }
