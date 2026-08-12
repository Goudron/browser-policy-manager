from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.core import profile_conversion_planner as planner
from app.core import profile_conversion_recipes as recipes
from app.core import schema_channels
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS

REPO_ROOT = Path(__file__).resolve().parents[4]
PLAN_SCHEMA_PATH = (
    REPO_ROOT / "docs/architecture/schemas/firefox-profile-conversion-contract-v1.schema.json"
)


def _context(*, compliance: object = None) -> planner.ConversionPlanningContext:
    return planner.ConversionPlanningContext(
        profile_id=17,
        revision=3,
        lifecycle_state="active",
        metadata={
            "name": "Private profile name",
            "description": "Private profile description",
            "created_at": "2026-08-11T10:00:00+00:00",
            "updated_at": "2026-08-11T10:00:00+00:00",
            "deleted_at": None,
        },
        compliance=compliance,
    )


def _plan(
    document: dict[str, object],
    *,
    source: str = "release-153",
    target: str = "esr-153.0",
    context: planner.ConversionPlanningContext | None = None,
) -> planner.ConversionPlanningResult:
    return planner.plan_profile_conversion(
        document,
        source_artifact_id=source,
        target_artifact_id=target,
        context=context or _context(),
    )


def _plan_validator() -> Draft202012Validator:
    schema = json.loads(PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$ref": "#/$defs/conversionPlan",
            "$defs": schema["$defs"],
        }
    )


def _atom_paths(value: object, pointer: str = "") -> list[str]:
    if isinstance(value, dict):
        if not value:
            return [pointer]
        return [
            path
            for key in sorted(value)
            for path in _atom_paths(
                value[key],
                f"{pointer}/{key.replace('~', '~0').replace('/', '~1')}",
            )
        ]
    if isinstance(value, list):
        if not value:
            return [pointer]
        return [
            path
            for index, item in enumerate(value)
            for path in _atom_paths(item, f"{pointer}/{index}")
        ]
    return [pointer]


def test_plan_is_m2_contract_serializable_and_excludes_raw_enterprise_values():
    document = {
        "policies": {
            "Preferences": {
                "a/slash~key": {
                    "Status": "locked",
                    "Type": "string",
                    "Value": "https://private.example.invalid/path",
                }
            },
            "Bookmarks": [],
            "SearchEngines": {"Add": []},
        }
    }
    compliance = {"operator_note": "private compliance note", "opaque": {"token": "secret"}}
    result = _plan(document, context=_context(compliance=compliance))
    plan = result.plan

    assert list(_plan_validator().iter_errors(plan)) == []
    assert plan["compatibility"]["applicable"] is True
    assert plan["compatibility"]["counts"] == {
        "source_atoms": 5,
        "target_atoms": 5,
        "unchanged_byte": 5,
        "unchanged_semantic": 0,
        "transformed": 0,
        "blocked": 0,
        "warnings": 1,
        "blockers": 0,
    }
    source_paths = [path for entry in plan["entries"] for path in entry["source_paths"]]
    target_paths = [path for entry in plan["entries"] for path in entry["target_paths"]]
    expected_paths = _atom_paths(document["policies"], "/policies")
    assert sorted(source_paths) == sorted(expected_paths)
    assert sorted(target_paths) == sorted(expected_paths)
    assert "/policies/Preferences/a~1slash~0key/Value" in source_paths
    assert "/policies/Bookmarks" in source_paths
    assert "/policies/SearchEngines/Add" in source_paths
    assert plan["compliance"]["disposition"] == "invalidated-preserved"
    assert plan["compliance"]["accounted_source_paths"] == [
        "/opaque/token",
        "/operator_note",
    ]

    public_bytes = json.dumps(plan, ensure_ascii=False, sort_keys=True)
    for raw_value in (
        "private.example.invalid",
        "private compliance note",
        "secret",
        "Private profile name",
        "Private profile description",
        "2026-08-11T10:00:00+00:00",
    ):
        assert raw_value not in public_bytes


def test_nested_dynamic_arrays_and_empty_containers_are_classified_once_without_mutation():
    document = {
        "policies": {
            "ExtensionSettings": {
                "*": {
                    "installation_mode": "blocked",
                    "allowed_types": ["extension", "theme"],
                }
            },
            "Preferences": {
                "browser.tabs.warnOnClose": {
                    "Value": True,
                    "Status": "locked",
                    "Type": "boolean",
                }
            },
            "Bookmarks": [],
        }
    }
    original = copy.deepcopy(document)

    result = _plan(document, source="esr-115.38", target="esr-140.13")
    plan = result.plan
    source_paths = [path for entry in plan["entries"] for path in entry["source_paths"]]
    target_paths = [path for entry in plan["entries"] for path in entry["target_paths"]]

    assert document == original
    assert len(source_paths) == len(set(source_paths))
    assert len(target_paths) == len(set(target_paths))
    assert "/policies/ExtensionSettings/*/allowed_types/0" in source_paths
    assert "/policies/ExtensionSettings/*/allowed_types/1" in source_paths
    assert "/policies/Bookmarks" in source_paths
    assert plan["compatibility"]["status"] == "compatible-unchanged"
    assert all(entry["classification"] == "unchanged" for entry in plan["entries"])

    candidate = result.candidate_document
    candidate["policies"]["Bookmarks"].append({"Title": "mutated"})
    assert document == original
    assert result.candidate_document["policies"]["Bookmarks"] == []


def test_empty_document_is_positive_and_target_validation_always_binds_candidate():
    result = _plan({"policies": {}}, source="esr-115.38", target="release-153")
    plan = result.plan

    assert plan["entries"] == []
    assert plan["compatibility"] == {
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
    }
    assert plan["target_validation"]["status"] == "valid"
    assert (
        plan["target_validation"]["validated_document_digest"]
        == plan["target"]["candidate_document_digest"]
    )


def test_target_invalid_preview_remains_complete_but_is_blocked_after_exact_validation():
    result = _plan(
        {"policies": {"BrowserDataBackup": {"AllowBackup": True}}},
        source="release-153",
        target="esr-140.13",
    )
    plan = result.plan

    assert plan["target_validation"]["status"] == "invalid"
    assert plan["target_validation"]["issues"] == [
        {
            "code": "target_policy_unsupported",
            "policy_id": "BrowserDataBackup",
            "paths": ["/policies/BrowserDataBackup"],
        }
    ]
    assert plan["compatibility"]["status"] == "blocked"
    assert plan["compatibility"]["applicable"] is False
    assert plan["compatibility"]["counts"]["source_atoms"] == 1
    assert plan["compatibility"]["counts"]["target_atoms"] == 1
    assert plan["compatibility"]["counts"]["blocked"] == 1
    assert plan["blockers"] == plan["target_validation"]["issues"]
    assert plan["entries"][0]["classification"] == "blocked"
    assert plan["entries"][0]["reason_code"] == "target_policy_unsupported"
    assert result.candidate_document == {"policies": {"BrowserDataBackup": {"AllowBackup": True}}}


def test_source_invalid_is_precondition_failure_without_a_target_preview():
    with pytest.raises(planner.ConversionPlanningError) as excinfo:
        _plan(
            {"policies": {"UnknownPolicy": True}},
            source="release-153",
            target="esr-153.0",
        )

    assert excinfo.value.code == "conversion_source_invalid"


def test_plan_is_deterministic_for_object_declaration_order_and_accessors_do_not_share_references():
    first_document = {
        "policies": {
            "HttpAllowlist": ["https://one.example.invalid", "https://two.example.invalid"],
            "DisableTelemetry": True,
        }
    }
    second_document = {
        "policies": {
            "DisableTelemetry": True,
            "HttpAllowlist": ["https://one.example.invalid", "https://two.example.invalid"],
        }
    }
    first = _plan(first_document)
    second = _plan(second_document)

    assert first.plan == second.plan
    first_plan = first.plan
    first_plan["entries"].clear()
    assert first.plan == second.plan
    first_candidate = first.candidate_document
    first_candidate["policies"]["HttpAllowlist"].clear()
    assert first.candidate_document == second.candidate_document
    assert first_document["policies"]["HttpAllowlist"] == [
        "https://one.example.invalid",
        "https://two.example.invalid",
    ]


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            [1.0, -0.0, 0.000001, 0.0000001, 1e20, 1e21],
            b"[1,0,0.000001,1e-7,100000000000000000000,1e+21]",
        ),
        ({"\uffff": 1, "😀": 2}, '{"😀":2,"\uffff":1}'.encode("utf-8")),
    ],
)
def test_jcs_identity_serialization_handles_number_and_utf16_order_boundaries(value, expected):
    assert planner._canonical_json(value) == expected


def test_unknown_retired_unbundled_and_identical_artifacts_fail_closed(monkeypatch):
    document = {"policies": {"DisableTelemetry": True}}
    with pytest.raises(planner.ConversionPlanningError, match="schema_channel_unknown"):
        _plan(document, source="unknown", target="release-153")
    with pytest.raises(planner.ConversionPlanningError, match="conversion_target_identical"):
        _plan(document, source="release-153", target="release-153")

    esr_140 = next(
        channel
        for channel in schema_channels.SCHEMA_CHANNEL_CATALOG
        if channel.artifact_id == "esr-140.13"
    )
    retired = replace(esr_140, support_state="retired", selectable=False)
    monkeypatch.setattr(
        schema_channels,
        "SCHEMA_CHANNEL_CATALOG",
        tuple(
            retired if channel.artifact_id == retired.artifact_id else channel
            for channel in schema_channels.SCHEMA_CHANNEL_CATALOG
        ),
    )
    with pytest.raises(planner.ConversionPlanningError, match="schema_channel_retired") as excinfo:
        _plan(document, source="release-153", target="esr-140.13")
    assert excinfo.value.code == "schema_channel_retired"

    monkeypatch.undo()
    monkeypatch.setattr(planner, "SCHEMA_FILENAMES", {"release-153": "firefox-release-153.json"})
    with pytest.raises(planner.ConversionPlanningError) as excinfo:
        _plan(document, source="release-153", target="esr-153.0")
    assert excinfo.value.code == "conversion_target_unsupported"


def test_four_channel_directed_matrix_has_a_valid_deterministic_empty_recipe_plan():
    pairs = [
        (source, target)
        for source in SUPPORTED_SCHEMA_CHANNELS
        for target in SUPPORTED_SCHEMA_CHANNELS
        if source != target
    ]
    total = len(pairs)
    assert total == 12

    for completed, (source, target) in enumerate(pairs, start=1):
        result = _plan(
            {"policies": {"DisableTelemetry": True}},
            source=source,
            target=target,
        )
        plan = result.plan
        assert plan["compatibility"]["applicable"] is True
        assert plan["target_validation"]["status"] == "valid"
        print(f"conversion pair completed {completed}/{total}: {source} -> {target}")


def _synthetic_recipe(
    *,
    recipe_id: str = "synthetic-mode-vocabulary",
    source_digest: str = "a" * 64,
    target_digest: str = "b" * 64,
    predicate=lambda value: value == "legacy",
    transform=lambda value: "modern",
    inverse=lambda value: "legacy",
    target_constraint=lambda value: value == "modern",
    source_path: str = "/policies/Synthetic/mode",
    target_path: str = "/policies/Synthetic/mode",
) -> recipes.ConversionRecipe:
    return recipes.ConversionRecipe(
        recipe_id=recipe_id,
        recipe_version=1,
        source_artifact_id="release-153",
        target_artifact_id="esr-153.0",
        source_validation_schema_sha256=source_digest,
        target_validation_schema_sha256=target_digest,
        source_path=source_path,
        target_path=target_path,
        input_predicate_id="legacy-only",
        target_constraint_id="modern-only",
        evidence_digest="c" * 64,
        predicate=predicate,
        transform=transform,
        inverse=inverse,
        target_constraint=target_constraint,
    )


def _synthetic_planner_artifacts(monkeypatch):
    def load_artifact(channel, *, source):
        expected = "legacy" if source else "modern"
        digest = "a" * 64 if source else "b" * 64
        return (
            {
                "line_id": channel.line_id,
                "artifact_id": channel.artifact_id,
                "channel_id": channel.channel_id,
                "artifact_version": channel.artifact_version,
                "source_tag": channel.source_tag,
                "schema_bundle_sha256": "d" * 64,
                "validation_schema_sha256": digest,
            },
            {"properties": {"Synthetic": {}}, "expected": expected},
        )

    validations: list[dict[str, object]] = []

    def validate(policies, schema):
        validations.append(copy.deepcopy(policies))
        mode = policies.get("Synthetic", {}).get("mode")
        if mode == schema["expected"]:
            return []
        return [
            planner.PolicyValidationIssue(
                policy="Synthetic",
                path=("Synthetic", "mode"),
                message="synthetic invalid",
            )
        ]

    monkeypatch.setattr(planner, "_load_artifact", load_artifact)
    monkeypatch.setattr(planner, "validate_profile_policies", validate)
    return validations


def test_synthetic_exact_recipe_is_reversible_target_valid_and_identity_is_order_independent(
    monkeypatch,
):
    validations = _synthetic_planner_artifacts(monkeypatch)
    recipe = _synthetic_recipe()
    registry = recipes.ConversionRecipeRegistry(recipes=(recipe,))
    document = {"policies": {"Synthetic": {"mode": "legacy"}}}
    original = copy.deepcopy(document)

    result = _plan(document, context=replace(_context(), recipe_registry=registry))
    plan = result.plan

    assert document == original
    assert result.candidate_document == {"policies": {"Synthetic": {"mode": "modern"}}}
    assert plan["compatibility"]["status"] == "compatible-transformed"
    assert plan["target_validation"]["status"] == "valid"
    assert len(validations) == 2  # source and target validation always run
    entry = plan["entries"][0]
    assert entry["classification"] == "transformed"
    assert entry["recipe"] == recipe.as_identity()
    assert entry["evidence_digest"] == recipe.evidence_digest
    assert recipe.inverse("modern") == "legacy"
    assert (
        registry.as_identity() == recipes.ConversionRecipeRegistry(recipes=(recipe,)).as_identity()
    )


@pytest.mark.parametrize(
    ("recipe_kwargs", "expected_code"),
    [
        ({"predicate": lambda value: False}, "transform_predicate_mismatch"),
        ({"source_digest": "e" * 64}, "target_value_invalid"),
        ({"transform": lambda value: (_ for _ in ()).throw(RuntimeError())}, "transform_exception"),
        ({"transform": lambda value: "wrong"}, "transform_output_invalid"),
        ({"inverse": lambda value: "wrong"}, "transform_lossless_evidence_missing"),
    ],
)
def test_synthetic_recipe_failures_are_blocked_and_never_mutate_source(
    monkeypatch, recipe_kwargs, expected_code
):
    validations = _synthetic_planner_artifacts(monkeypatch)
    document = {"policies": {"Synthetic": {"mode": "legacy"}}}
    original = copy.deepcopy(document)
    registry = recipes.ConversionRecipeRegistry(recipes=(_synthetic_recipe(**recipe_kwargs),))

    result = _plan(document, context=replace(_context(), recipe_registry=registry))

    assert document == original
    assert result.plan["compatibility"]["status"] == "blocked"
    assert expected_code in {entry["reason_code"] for entry in result.plan["entries"]}
    assert len(validations) == 2


def test_synthetic_recipe_target_coverage_collision_fails_closed_without_source_mutation(
    monkeypatch,
):
    _synthetic_planner_artifacts(monkeypatch)
    document = {"policies": {"Synthetic": {"mode": "legacy", "second": "legacy"}}}
    original = copy.deepcopy(document)
    registry = recipes.ConversionRecipeRegistry(
        recipes=(
            _synthetic_recipe(target_path="/policies/Synthetic/renamed"),
            _synthetic_recipe(
                recipe_id="synthetic-second-vocabulary",
                source_path="/policies/Synthetic/second",
                target_path="/policies/Synthetic/renamed",
            ),
        )
    )

    result = _plan(document, context=replace(_context(), recipe_registry=registry))

    assert document == original
    assert result.candidate_document == original
    assert {entry["reason_code"] for entry in result.plan["entries"]} == {
        "transform_target_coverage_mismatch"
    }


def test_recipe_registry_rejects_duplicate_or_overlapping_exact_domains():
    recipe = _synthetic_recipe()
    same_domain_next_version = replace(recipe, recipe_version=2)
    with pytest.raises(recipes.ConversionRecipeError, match="transform_recipe_domain_overlap"):
        recipes.ConversionRecipeRegistry(recipes=(recipe, same_domain_next_version))
    with pytest.raises(recipes.ConversionRecipeError, match="transform_recipe_duplicate"):
        recipes.ConversionRecipeRegistry(recipes=(recipe, recipe))
