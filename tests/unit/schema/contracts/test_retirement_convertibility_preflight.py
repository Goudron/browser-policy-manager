from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.core.lifecycle_transition_plan import build_lifecycle_transition_plan
from app.core.profile_conversion_json import canonical_json
from app.core.profile_conversion_recipes import ConversionRecipe, ConversionRecipeRegistry
from app.core.retirement_convertibility_preflight import (
    RetirementConvertibilityPreflightError,
    ReviewedSchemaContainment,
    SchemaArtifactBinding,
    load_exact_schema_containment_evidence,
    prove_retirement_total_convertibility,
)
from app.core.schema_channels import SCHEMA_CHANNEL_CATALOG


def _schema_bundle(
    *, line_id: str, artifact_id: str, schema: dict[object, object]
) -> SchemaArtifactBinding:
    return SchemaArtifactBinding.from_schema(
        line_id=line_id,
        artifact_id=artifact_id,
        bundle_bytes=canonical_json(schema),  # type: ignore[arg-type]
        normalized_schema=schema,
    )


def _esr115_to_esr140_plan():
    candidate = tuple(
        replace(channel, support_state="retired", selectable=False)
        if channel.line_id == "esr-115"
        else channel
        for channel in SCHEMA_CHANNEL_CATALOG
    )
    return build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        tuple(reversed(candidate)),
        bundled_artifact_ids={channel.artifact_id for channel in candidate},
    )


def _esr140_to_esr153_plan():
    candidate = tuple(
        replace(channel, support_state="retired", selectable=False)
        if channel.line_id == "esr-140"
        else replace(channel, retirement_successor_line_id="esr-153")
        if channel.line_id == "esr-115"
        else channel
        for channel in SCHEMA_CHANNEL_CATALOG
    )
    return build_lifecycle_transition_plan(
        SCHEMA_CHANNEL_CATALOG,
        tuple(reversed(candidate)),
        bundled_artifact_ids={channel.artifact_id for channel in candidate},
    )


def _synthetic_artifacts() -> tuple[SchemaArtifactBinding, SchemaArtifactBinding]:
    source_schema = {
        "type": "object",
        "properties": {
            "Legacy": {"enum": ["legacy-a", "legacy-b"]},
            "Stable": {"type": "boolean"},
        },
        "additionalProperties": False,
    }
    target_schema = {
        "type": "object",
        "properties": {
            "Legacy": {"enum": ["modern-a", "modern-b"]},
            "Stable": {"type": "boolean"},
            "TargetOnly": {"type": "string"},
        },
        "additionalProperties": False,
    }
    return (
        _schema_bundle(line_id="esr-115", artifact_id="esr-115.38", schema=source_schema),
        _schema_bundle(line_id="esr-140", artifact_id="esr-140.13", schema=target_schema),
    )


def _evidence(
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    *,
    source_schema_pointer: str,
    target_schema_pointer: str | None = None,
) -> ReviewedSchemaContainment:
    return ReviewedSchemaContainment(
        evidence_id="reviewed-synthetic-containment",
        evidence_digest="a" * 64,
        source_artifact_id=source.artifact_id,
        target_artifact_id=target.artifact_id,
        source_validation_schema_sha256=source.validation_schema_sha256,
        target_validation_schema_sha256=target.validation_schema_sha256,
        source_schema_pointer=source_schema_pointer,
        target_schema_pointer=(
            source_schema_pointer if target_schema_pointer is None else target_schema_pointer
        ),
    )


def _legacy_recipe(
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
    *,
    predicate=lambda value: value in {"legacy-a", "legacy-b"},
) -> ConversionRecipe:
    forward = {"legacy-a": "modern-a", "legacy-b": "modern-b"}
    reverse = {value: key for key, value in forward.items()}
    return ConversionRecipe(
        recipe_id="synthetic.legacy-to-modern",
        recipe_version=1,
        source_artifact_id=source.artifact_id,
        target_artifact_id=target.artifact_id,
        source_validation_schema_sha256=source.validation_schema_sha256,
        target_validation_schema_sha256=target.validation_schema_sha256,
        source_path="/Legacy",
        target_path="/Legacy",
        input_predicate_id="synthetic.legacy.enum",
        target_constraint_id="synthetic.modern.enum",
        evidence_digest="b" * 64,
        predicate=predicate,
        transform=lambda value: forward[value],
        inverse=lambda value: reverse[value],
        target_constraint=lambda value: value in set(reverse),
    )


def _unrelated_recipe(
    source: SchemaArtifactBinding,
    target: SchemaArtifactBinding,
) -> ConversionRecipe:
    return ConversionRecipe(
        recipe_id="synthetic.unused",
        recipe_version=1,
        source_artifact_id=source.artifact_id,
        target_artifact_id=target.artifact_id,
        source_validation_schema_sha256=source.validation_schema_sha256,
        target_validation_schema_sha256=target.validation_schema_sha256,
        source_path="/Unrelated",
        target_path="/Unrelated",
        input_predicate_id="synthetic.unused.input",
        target_constraint_id="synthetic.unused.output",
        evidence_digest="c" * 64,
        predicate=lambda value: True,
        transform=lambda value: value,
        inverse=lambda value: value,
        target_constraint=lambda value: True,
    )


def test_synthetic_esr115_to_esr140_proves_complete_finite_recipe_partition_without_profiles():
    source, target = _synthetic_artifacts()
    report = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        recipe_registry=ConversionRecipeRegistry(recipes=(_legacy_recipe(source, target),)),
        containment_evidence=(
            _evidence(source, target, source_schema_pointer="/properties/Stable"),
        ),
    )

    assert report.promotable is True
    result = report.results[0]
    assert result.method == "complete-recipe-partition"
    assert result.uncovered_schema_locations == ()
    assert result.proof_artifact_digest is not None
    assert result.as_dict()["mutation"] == "none"


def test_uncovered_source_atom_reports_exact_rfc6901_schema_and_policy_paths():
    source, target = _synthetic_artifacts()
    report = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
    )

    uncovered = report.results[0].uncovered_schema_locations
    assert [(item.source_schema_pointer, item.source_atom_pointer) for item in uncovered] == [
        ("/properties/Legacy", "/Legacy"),
        ("/properties/Stable", "/Stable"),
    ]
    assert all(item.reason_code.startswith("retirement_") for item in uncovered)
    assert report.results[0].blockers == ("retirement_total_convertibility_unproven",)


def test_non_exhaustive_recipe_predicate_cannot_stand_in_for_total_domain_proof():
    source, target = _synthetic_artifacts()
    report = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        recipe_registry=ConversionRecipeRegistry(
            recipes=(_legacy_recipe(source, target, predicate=lambda value: value == "legacy-a"),)
        ),
        containment_evidence=(
            _evidence(source, target, source_schema_pointer="/properties/Stable"),
        ),
    )

    uncovered = report.results[0].uncovered_schema_locations
    assert [(item.source_schema_pointer, item.reason_code) for item in uncovered] == [
        ("/properties/Legacy", "retirement_recipe_partition_incomplete"),
    ]


def test_target_only_policy_does_not_create_a_source_domain_error_when_root_containment_is_reviewed():
    source_schema = {
        "type": "object",
        "properties": {"Stable": {"type": "boolean"}},
        "additionalProperties": False,
    }
    target_schema = {
        "type": "object",
        "properties": {
            "Stable": {"type": "boolean"},
            "TargetOnly": {"type": "string"},
        },
        "additionalProperties": False,
    }
    source = _schema_bundle(
        line_id="esr-115",
        artifact_id="esr-115.38",
        schema=source_schema,
    )
    target = _schema_bundle(
        line_id="esr-140",
        artifact_id="esr-140.13",
        schema=target_schema,
    )
    report = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        containment_evidence=(_evidence(source, target, source_schema_pointer=""),),
    )

    assert report.promotable is True
    assert report.results[0].method == "schema-containment"
    assert report.results[0].uncovered_schema_locations == ()


def test_semantic_evidence_cannot_override_a_target_rejected_source_value_shape():
    source, target = _synthetic_artifacts()
    report = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        containment_evidence=(_evidence(source, target, source_schema_pointer=""),),
    )

    assert report.promotable is False
    assert [
        item.source_schema_pointer for item in report.results[0].uncovered_schema_locations
    ] == ["/properties/Legacy"]
    assert report.results[0].uncovered_schema_locations[0].reason_code == (
        "retirement_unchanged_target_containment_unproven"
    )


def test_stale_recipe_schema_binding_is_uncovered_not_a_recipe_match():
    source, target = _synthetic_artifacts()
    stale = replace(_legacy_recipe(source, target), source_validation_schema_sha256="d" * 64)
    report = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        recipe_registry=ConversionRecipeRegistry(recipes=(stale,)),
        containment_evidence=(
            _evidence(source, target, source_schema_pointer="/properties/Stable"),
        ),
    )

    uncovered = report.results[0].uncovered_schema_locations
    assert [(item.source_schema_pointer, item.reason_code) for item in uncovered] == [
        ("/properties/Legacy", "retirement_recipe_binding_missing"),
    ]


def test_malformed_schema_and_artifact_line_substitution_fail_before_a_proof_result_exists():
    with pytest.raises(RetirementConvertibilityPreflightError, match="retirement_schema_malformed"):
        _schema_bundle(
            line_id="esr-115",
            artifact_id="esr-115.38",
            schema={"type": "not-a-json-schema-type"},
        )

    source, target = _synthetic_artifacts()
    substituted = replace(source, line_id="esr-140")
    with pytest.raises(
        RetirementConvertibilityPreflightError,
        match="retirement_schema_artifact_identity_mismatch",
    ):
        prove_retirement_total_convertibility(
            _esr115_to_esr140_plan(),
            artifacts={source.artifact_id: substituted, target.artifact_id: target},
        )


def test_checked_in_bundle_binding_rejects_duplicate_json_schema_keys(tmp_path):
    channel = next(channel for channel in SCHEMA_CHANNEL_CATALOG if channel.line_id == "esr-115")
    duplicate_key_channel = replace(
        channel, source=replace(channel.source, output_path="schema.json")
    )
    (tmp_path / "schema.json").write_text(
        '{"type":"object","type":"string"}',
        encoding="utf-8",
    )

    with pytest.raises(RetirementConvertibilityPreflightError, match="retirement_schema_malformed"):
        SchemaArtifactBinding.from_channel(duplicate_key_channel, repository_root=tmp_path)


def test_proof_is_independent_of_evidence_registry_and_lifecycle_declaration_order():
    source, target = _synthetic_artifacts()
    legacy = _legacy_recipe(source, target)
    unused = _unrelated_recipe(source, target)
    evidence = _evidence(source, target, source_schema_pointer="/properties/Stable")
    first = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        recipe_registry=ConversionRecipeRegistry(recipes=(legacy, unused)),
        containment_evidence=(evidence,),
    )
    second = prove_retirement_total_convertibility(
        _esr115_to_esr140_plan(),
        artifacts={target.artifact_id: target, source.artifact_id: source},
        recipe_registry=ConversionRecipeRegistry(recipes=(unused, legacy)),
        containment_evidence=tuple(reversed((evidence,))),
    )

    assert first.as_dict() == second.as_dict()


_ESR140_TO_ESR153_PROOF = (
    Path(__file__).resolve().parents[4]
    / "docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json"
)


def test_required_current_esr140_to_esr153_plan_is_bound_to_exact_complete_proof_artifact():
    channels = {channel.line_id: channel for channel in SCHEMA_CHANNEL_CATALOG}
    source = SchemaArtifactBinding.from_channel(channels["esr-140"])
    target = SchemaArtifactBinding.from_channel(channels["esr-153"])
    evidence = load_exact_schema_containment_evidence(
        _ESR140_TO_ESR153_PROOF,
        source=source,
        target=target,
    )
    report = prove_retirement_total_convertibility(
        _esr140_to_esr153_plan(),
        artifacts={source.artifact_id: source, target.artifact_id: target},
        containment_evidence=evidence,
    )

    result = report.results[0]
    assert result.source.artifact_id == "esr-140.13"
    assert result.target.artifact_id == "esr-153.0"
    assert result.promotable is True
    assert result.method == "schema-containment"
    assert (
        result.proof_artifact_digest
        == "3d04890c00a89534526fea7456e89250c36ba3617fa0d10949c8e51d98bcc2bb"
    )
    assert result.blockers == ()
    assert result.uncovered_schema_locations == ()


def test_exact_proof_artifact_rejects_stale_source_identity_before_proof():
    channels = {channel.line_id: channel for channel in SCHEMA_CHANNEL_CATALOG}
    source = SchemaArtifactBinding.from_channel(channels["esr-140"])
    target = SchemaArtifactBinding.from_channel(channels["esr-153"])

    with pytest.raises(
        RetirementConvertibilityPreflightError,
        match="retirement_proof_artifact_identity_mismatch",
    ):
        load_exact_schema_containment_evidence(
            _ESR140_TO_ESR153_PROOF,
            source=replace(source, artifact_id="esr-140.stale"),
            target=target,
        )


def test_schema_containment_evidence_cannot_override_a_real_target_counterexample():
    channels = {channel.line_id: channel for channel in SCHEMA_CHANNEL_CATALOG}
    source = SchemaArtifactBinding.from_channel(channels["esr-140"])
    target_schema = SchemaArtifactBinding.from_channel(channels["esr-153"]).normalized_schema
    cookies = target_schema["properties"]["Cookies"]
    assert isinstance(cookies, dict)
    cookie_properties = cookies["properties"]
    assert isinstance(cookie_properties, dict)
    behavior = cookie_properties["Behavior"]
    assert isinstance(behavior, dict)
    behavior["enum"] = ["accept"]
    counterexample_target = _schema_bundle(
        line_id="esr-153",
        artifact_id="esr-153.0",
        schema=target_schema,
    )
    claimed_evidence = ReviewedSchemaContainment(
        evidence_id="counterexample-does-not-override-structure",
        evidence_digest="e" * 64,
        source_artifact_id=source.artifact_id,
        target_artifact_id=counterexample_target.artifact_id,
        source_validation_schema_sha256=source.validation_schema_sha256,
        target_validation_schema_sha256=counterexample_target.validation_schema_sha256,
    )

    report = prove_retirement_total_convertibility(
        _esr140_to_esr153_plan(),
        artifacts={
            source.artifact_id: source,
            counterexample_target.artifact_id: counterexample_target,
        },
        containment_evidence=(claimed_evidence,),
    )

    assert report.promotable is False
    assert [
        (item.source_schema_pointer, item.reason_code)
        for item in report.results[0].uncovered_schema_locations
    ] == [("/properties/Cookies", "retirement_unchanged_target_containment_unproven")]
