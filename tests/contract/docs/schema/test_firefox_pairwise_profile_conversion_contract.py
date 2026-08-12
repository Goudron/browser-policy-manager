from __future__ import annotations

import copy
import hashlib
import itertools
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from app.core.schemas_loader import load_schema
from app.models.profile import Profile
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = (
    REPO_ROOT / "docs/architecture/firefox-pairwise-profile-conversion-contract-0.9.5.md"
)
FIXTURE_PATH = (
    REPO_ROOT / "docs/architecture/firefox-pairwise-profile-conversion-contract-0.9.5.json"
)
SCHEMA_PATH = (
    REPO_ROOT / "docs/architecture/schemas/firefox-profile-conversion-contract-v1.schema.json"
)
LIFECYCLE_PATH = (
    REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
)
GOLDEN_PROFILES_PATH = REPO_ROOT / "tests/fixtures/database_upgrade/golden_profiles_0_9_4.json"

ARTIFACT_IDS = ("release-153", "esr-153.0", "esr-140.13", "esr-115.38")
CURRENT_ARTIFACT_IDS = ARTIFACT_IDS[:3]
PLAN_INCLUDE_KEYS = (
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
SOURCE_DOCUMENT = {"policies": {"DisableTelemetry": True}}
TARGET_DOCUMENT = copy.deepcopy(SOURCE_DOCUMENT)
PROFILE_METADATA = {
    "name": "Reference unchanged plan",
    "description": "Contract-only example",
    "created_at": "2026-08-10T00:00:00Z",
    "updated_at": "2026-08-10T00:00:00Z",
    "deleted_at": None,
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    assert isinstance(value, dict)
    return value


def _fixture() -> dict[str, Any]:
    return _load_json(FIXTURE_PATH)


def _schema_validator() -> Draft202012Validator:
    schema = _load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _definition_validator(definition: str) -> Draft202012Validator:
    schema = _load_json(SCHEMA_PATH)
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$ref": f"#/$defs/{definition}",
            "$defs": schema["$defs"],
        }
    )


def _canonical_json(value: Any) -> bytes:
    # Contract vectors avoid the numeric edge cases where a dedicated RFC 8785
    # implementation is required. M4 owns that runtime dependency/implementation.
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _domain_digest(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("utf-8") + _canonical_json(value)).hexdigest()


def _plan_digest(contract: dict[str, Any], plan: dict[str, Any]) -> str:
    projection = {key: plan[key] for key in PLAN_INCLUDE_KEYS}
    return _domain_digest(contract["canonical_identity"]["plan_domain"], projection)


def _escape_pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _atom_paths(value: Any, pointer: str = "") -> tuple[str, ...]:
    if isinstance(value, dict):
        if not value:
            return (pointer,)
        return tuple(
            path
            for key in sorted(value)
            for path in _atom_paths(value[key], f"{pointer}/{_escape_pointer_part(key)}")
        )
    if isinstance(value, list):
        if not value:
            return (pointer,)
        return tuple(
            path
            for index, item in enumerate(value)
            for path in _atom_paths(item, f"{pointer}/{index}")
        )
    return (pointer,)


def _assert_sorted_unique(values: list[str], *, label: str) -> None:
    if values != sorted(set(values), key=lambda value: value.encode("utf-8")):
        raise ValueError(f"{label} must be unique and stable-sorted")


def _assert_plan_semantics(
    contract: dict[str, Any],
    plan: dict[str, Any],
    *,
    source_document: dict[str, Any],
    target_document: dict[str, Any],
) -> None:
    source_atoms = _atom_paths(source_document)
    target_atoms = _atom_paths(target_document)
    entries = plan["entries"]

    flattened_source = [path for entry in entries for path in entry["source_paths"]]
    flattened_target = [path for entry in entries for path in entry["target_paths"]]
    if sorted(flattened_source) != sorted(source_atoms) or len(flattened_source) != len(
        set(flattened_source)
    ):
        raise ValueError("every source atom must be covered exactly once")
    if sorted(flattened_target) != sorted(target_atoms) or len(flattened_target) != len(
        set(flattened_target)
    ):
        raise ValueError("every target atom must be produced and covered exactly once")

    entry_order = sorted(
        entries,
        key=lambda entry: (
            tuple(path.encode("utf-8") for path in entry["source_paths"]),
            tuple(path.encode("utf-8") for path in entry["target_paths"]),
            entry["classification"],
            (entry["recipe"] or {}).get("recipe_id", ""),
            (entry["recipe"] or {}).get("recipe_version", 0),
        ),
    )
    if entries != entry_order:
        raise ValueError("plan entries are not in stable order")

    registry_recipes = {
        (recipe["recipe_id"], recipe["recipe_version"], recipe["definition_digest"]): recipe
        for recipe in plan["recipe_registry"]["recipes"]
    }
    classified_atom_counts = {
        "unchanged_byte": 0,
        "unchanged_semantic": 0,
        "transformed": 0,
        "blocked": 0,
    }
    for entry in entries:
        classification = entry["classification"]
        atom_count = len(entry["source_paths"])
        if classification == "unchanged":
            if entry["recipe"] is not None or entry["unchanged_kind"] is None:
                raise ValueError(
                    "unchanged entries cannot use a recipe and must name unchanged kind"
                )
            if entry["source_paths"] != entry["target_paths"]:
                raise ValueError("unchanged entries preserve exact paths")
            if entry["source_subtree_digest"] != entry["target_subtree_digest"]:
                raise ValueError("unchanged entries preserve canonical subtree bytes")
            if entry["unchanged_kind"] == "semantic-equivalent":
                if entry["evidence_digest"] is None:
                    raise ValueError("semantic unchanged entries require evidence")
                classified_atom_counts["unchanged_semantic"] += atom_count
            else:
                if entry["evidence_digest"] is not None:
                    raise ValueError("byte-identical entry must not invent semantic evidence")
                classified_atom_counts["unchanged_byte"] += atom_count
        elif classification == "transformed":
            recipe = entry["recipe"]
            if (
                entry["unchanged_kind"] is not None
                or recipe is None
                or entry["evidence_digest"] is None
            ):
                raise ValueError(
                    "transformed entries require one recipe/evidence and are not unchanged"
                )
            key = (recipe["recipe_id"], recipe["recipe_version"], recipe["definition_digest"])
            if registry_recipes.get(key) != recipe:
                raise ValueError("transformed entry recipe is not bound to exact registry identity")
            if recipe["evidence_digest"] != entry["evidence_digest"]:
                raise ValueError("entry and recipe evidence identities differ")
            if not entry["target_paths"] or entry["target_subtree_digest"] is None:
                raise ValueError("transformation must explicitly produce target atoms")
            classified_atom_counts["transformed"] += atom_count
        elif classification == "blocked":
            if entry["unchanged_kind"] is not None:
                raise ValueError("blocked entry cannot claim unchanged evidence")
            classified_atom_counts["blocked"] += atom_count
        else:  # JSON Schema also rejects this; keep semantic validation fail-closed.
            raise ValueError(f"unapproved classification {classification!r}")

    counts = plan["compatibility"]["counts"]
    if counts["source_atoms"] != len(source_atoms) or counts["target_atoms"] != len(target_atoms):
        raise ValueError("atom summary does not match document coverage")
    for key, expected in classified_atom_counts.items():
        if counts[key] != expected:
            raise ValueError(f"classification count mismatch for {key}")
    if counts["warnings"] != len(plan["warnings"]) or counts["blockers"] != len(plan["blockers"]):
        raise ValueError("diagnostic counts do not match payload")

    is_blocked = bool(classified_atom_counts["blocked"] or plan["blockers"])
    target_valid = plan["target_validation"]["status"] == "valid"
    expected_applicable = not is_blocked and target_valid
    if plan["compatibility"]["applicable"] is not expected_applicable:
        raise ValueError("applicability does not match blockers/target validation")
    expected_status = (
        "blocked"
        if not expected_applicable
        else "compatible-transformed"
        if classified_atom_counts["transformed"]
        else "compatible-unchanged"
    )
    if plan["compatibility"]["status"] != expected_status:
        raise ValueError("compatibility status does not match classified atoms")

    target_validation = plan["target_validation"]
    if (
        target_validation["validated_document_digest"]
        != plan["target"]["candidate_document_digest"]
    ):
        raise ValueError("target validator did not bind the exact candidate")
    if (
        target_validation["validation_schema_sha256"]
        != plan["target"]["artifact"]["validation_schema_sha256"]
    ):
        raise ValueError("target validator schema identity drift")
    if target_validation["status"] == "valid" and target_validation["issues"]:
        raise ValueError("valid target cannot contain validation issues")

    for collection_name in ("warnings", "blockers"):
        collection = plan[collection_name]
        ordered = sorted(
            collection,
            key=lambda item: (
                item["code"],
                item["policy_id"] or "",
                tuple(path.encode("utf-8") for path in item["paths"]),
            ),
        )
        if collection != ordered:
            raise ValueError(f"{collection_name} are not stable-sorted")

    if plan["plan_digest"] != _plan_digest(contract, plan):
        raise ValueError("plan digest does not match canonical projection")


def _assert_pair_matrix(contract: dict[str, Any]) -> None:
    lifecycle = _load_json(LIFECYCLE_PATH)
    rows = {row["artifact_id"]: row for row in lifecycle["channels"]}
    expected_pairs = set(itertools.permutations(ARTIFACT_IDS, 2))
    observed_pairs = {
        (pair["source_artifact_id"], pair["target_artifact_id"]) for pair in contract["pair_matrix"]
    }
    if observed_pairs != expected_pairs or len(contract["pair_matrix"]) != len(observed_pairs):
        raise ValueError("pair matrix must contain every directed non-self pair exactly once")

    for pair in contract["pair_matrix"]:
        source_id = pair["source_artifact_id"]
        target_id = pair["target_artifact_id"]
        if pair["pair_id"] != f"{source_id}--to--{target_id}":
            raise ValueError("pair id is not derived from exact artifacts")
        if pair["source_line_id"] != rows[source_id]["line_id"]:
            raise ValueError("source stable line mismatch")
        if pair["target_line_id"] != rows[target_id]["line_id"]:
            raise ValueError("target stable line mismatch")
        if pair["artifact_availability"] != "current":
            raise ValueError("all four M3 artifacts must be current planner inputs")
        if pair["runtime_status"] != "planner-runtime-active-empty-production-registry":
            raise ValueError("pair runtime status must retain the empty-registry boundary")


def _assert_contract_semantics(contract: dict[str, Any]) -> None:
    if contract["status"] != "active-m4-06-directed-matrix-gate":
        raise ValueError("M4-06 directed matrix handoff status drift")
    matrix_gate = contract["implementation"]["matrix_gate"]
    if matrix_gate != {
        "status": "implemented",
        "command": "make verify-firefox-conversion-matrix",
        "tool": "tools/verify_firefox_conversion_matrix.py",
        "report": "deterministic-value-free-json",
    }:
        raise ValueError("M4-06 matrix gate handoff drift")
    _assert_pair_matrix(contract)
    disposition = contract["transform_registry_contract"]["production_disposition"]
    if disposition["production_recipe_count"] != 0:
        raise ValueError("M4-02 production registry must not invent a recipe")
    if disposition["code"] != "no-production-recipe-after-four-channel-diff-audit":
        raise ValueError("M4-02 no-recipe disposition drift")
    if set(disposition["all_pair_source_only_policy_counts"]) != {
        pair["pair_id"] for pair in contract["pair_matrix"]
    }:
        raise ValueError("all directed pair audit coverage drift")
    expected_stored_fields = {column.name for column in Profile.__table__.columns}
    if set(contract["profile_field_accounting"]["stored_fields"]) != expected_stored_fields:
        raise ValueError("stored profile field coverage drift")
    if set(contract["profile_field_accounting"]["application_write_fields"]) != {
        "schema_version",
        "flags",
        "compliance",
        "revision",
    }:
        raise ValueError("conversion application write set drift")
    if set(contract["profile_field_accounting"]["preserved_fields"]) != {
        "id",
        "name",
        "name_casefold",
        "description",
        "created_at",
        "deleted_at",
    }:
        raise ValueError("preserved metadata field coverage drift")
    if contract["profile_field_accounting"]["revision_increment"] != 1:
        raise ValueError("successful apply must increment revision exactly once")

    expected_failures = {
        "conversion_profile_not_found",
        "conversion_source_not_active",
        "schema_channel_unknown",
        "schema_channel_retired",
        "schema_channel_retired_requires_migration",
        "conversion_target_unsupported",
        "conversion_target_identical",
        "conversion_source_invalid",
        "conversion_source_schema_missing",
        "conversion_target_schema_missing",
        "conversion_revision_stale",
        "conversion_source_identity_stale",
        "conversion_plan_stale",
        "conversion_schema_identity_stale",
        "conversion_recipe_registry_stale",
        "conversion_plan_blocked",
        "conversion_apply_failed",
    }
    failures = contract["failure_semantics"]
    if {failure["code"] for failure in failures} != expected_failures:
        raise ValueError("failure code matrix is incomplete")
    if any(failure["mutation"] != "none" for failure in failures):
        raise ValueError("conversion failure may not mutate a profile")

    plan = contract["examples"]["plan"]
    _assert_plan_semantics(
        contract,
        plan,
        source_document=SOURCE_DOCUMENT,
        target_document=TARGET_DOCUMENT,
    )
    pair = (plan["source"]["artifact"]["artifact_id"], plan["target"]["artifact"]["artifact_id"])
    if pair not in {
        (item["source_artifact_id"], item["target_artifact_id"]) for item in contract["pair_matrix"]
    }:
        raise ValueError("example plan pair is outside the required matrix")

    for side in ("source", "target"):
        artifact = plan[side]["artifact"]
        if artifact["artifact_id"] != artifact["channel_id"]:
            raise ValueError("channel and exact artifact identities diverge")

    apply_request = contract["examples"]["apply_request"]
    result = contract["examples"]["result"]
    for payload in (apply_request, result):
        if payload["plan_digest"] != plan["plan_digest"]:
            raise ValueError("apply/result is not bound to preview identity")
        if payload["source"] != {
            "line_id": plan["source"]["artifact"]["line_id"],
            "artifact_id": plan["source"]["artifact"]["artifact_id"],
        }:
            raise ValueError("apply/result source identity drift")
        if payload["target"] != {
            "line_id": plan["target"]["artifact"]["line_id"],
            "artifact_id": plan["target"]["artifact"]["artifact_id"],
        }:
            raise ValueError("apply/result target identity drift")

    if apply_request["profile_id"] != plan["profile"]["id"]:
        raise ValueError("apply profile identity drift")
    if apply_request["expected_revision"] != plan["profile"]["revision"]:
        raise ValueError("apply revision is not preview revision")
    if apply_request["source_document_digest"] != plan["source"]["document_digest"]:
        raise ValueError("apply source document identity drift")
    if apply_request["source_compliance_digest"] != plan["source"]["compliance_digest"]:
        raise ValueError("apply compliance identity drift")
    if apply_request["source_metadata_digest"] != plan["profile"]["metadata_digest"]:
        raise ValueError("apply metadata identity drift")
    if apply_request["recipe_registry_version"] != plan["recipe_registry"]["registry_version"]:
        raise ValueError("apply recipe registry version drift")
    if apply_request["recipe_registry_digest"] != plan["recipe_registry"]["registry_digest"]:
        raise ValueError("apply recipe registry identity drift")
    if result["source_revision"] != plan["profile"]["revision"]:
        raise ValueError("result source revision drift")
    if result["result_revision"] != result["source_revision"] + 1:
        raise ValueError("result revision must increment once")
    if result["result_document_digest"] != plan["target"]["candidate_document_digest"]:
        raise ValueError("result document is not exact preview candidate")
    if result["result_compliance_digest"] != plan["compliance"]["target_digest"]:
        raise ValueError("result compliance is not exact preview disposition")
    if (
        result["field_accounting"]["application_write_fields"]
        != contract["profile_field_accounting"]["application_write_fields"]
    ):
        raise ValueError("result application write set drift")
    if (
        result["field_accounting"]["database_managed_fields"]
        != contract["profile_field_accounting"]["database_managed_fields"]
    ):
        raise ValueError("result timestamp ownership drift")
    if (
        result["field_accounting"]["preserved_fields"]
        != contract["profile_field_accounting"]["preserved_fields"]
    ):
        raise ValueError("result preserved metadata drift")


def _rehash_plan(contract: dict[str, Any], plan: dict[str, Any]) -> None:
    plan["plan_digest"] = _plan_digest(contract, plan)


def _make_transformed_plan(contract: dict[str, Any]) -> dict[str, Any]:
    plan = copy.deepcopy(contract["examples"]["plan"])
    recipe = {
        "recipe_id": "contract-test.identity-copy",
        "recipe_version": 1,
        "definition_digest": "1" * 64,
        "evidence_digest": "2" * 64,
        "evidence_kind": "reversible",
    }
    entry = plan["entries"][0]
    entry.update(
        {
            "classification": "transformed",
            "unchanged_kind": None,
            "recipe": recipe,
            "evidence_digest": recipe["evidence_digest"],
            "reason_code": "lossless_transformation_applied",
        }
    )
    plan["recipe_registry"]["recipes"] = [recipe]
    plan["compatibility"]["status"] = "compatible-transformed"
    plan["compatibility"]["counts"].update({"unchanged_semantic": 0, "transformed": 1})
    plan["warnings"] = [
        {
            "code": "lossless_transformation_used",
            "policy_id": "DisableTelemetry",
            "paths": ["/policies/DisableTelemetry"],
        }
    ]
    _rehash_plan(contract, plan)
    return plan


def _make_blocked_plan(contract: dict[str, Any]) -> dict[str, Any]:
    plan = copy.deepcopy(contract["examples"]["plan"])
    entry = plan["entries"][0]
    entry.update(
        {
            "classification": "blocked",
            "unchanged_kind": None,
            "recipe": None,
            "evidence_digest": None,
            "reason_code": "semantic_equivalence_unproven",
        }
    )
    plan["compatibility"].update({"status": "blocked", "applicable": False})
    plan["compatibility"]["counts"].update(
        {"unchanged_semantic": 0, "blocked": 1, "warnings": 0, "blockers": 1}
    )
    plan["warnings"] = []
    plan["blockers"] = [
        {
            "code": "semantic_equivalence_unproven",
            "policy_id": "DisableTelemetry",
            "paths": ["/policies/DisableTelemetry"],
        }
    ]
    _rehash_plan(contract, plan)
    return plan


def test_contract_fixture_schema_examples_index_and_current_artifact_identities() -> None:
    contract = _fixture()
    _schema_validator().validate(contract)
    _assert_contract_semantics(contract)

    assert (
        doc_path_from_index(
            "architecture/firefox-pairwise-profile-conversion-contract-0.9.5.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    assert (
        doc_path_from_index(
            "architecture/firefox-pairwise-profile-conversion-contract-0.9.5.json",
            status="active",
        )
        == FIXTURE_PATH
    )
    assert (
        doc_path_from_index(
            "architecture/schemas/firefox-profile-conversion-contract-v1.schema.json",
            status="active",
        )
        == SCHEMA_PATH
    )

    plan = contract["examples"]["plan"]
    lifecycle_rows = {row["artifact_id"]: row for row in _load_json(LIFECYCLE_PATH)["channels"]}
    for side in ("source", "target"):
        identity = plan[side]["artifact"]
        artifact_id = identity["artifact_id"]
        row = lifecycle_rows[artifact_id]
        assert identity["line_id"] == row["line_id"]
        assert identity["artifact_version"] == row["artifact_version"]
        assert identity["source_tag"] == row["source"]["source_tag"]
        bundle_path = REPO_ROOT / row["source"]["output_path"]
        assert (
            hashlib.sha256(bundle_path.read_bytes()).hexdigest() == identity["schema_bundle_sha256"]
        )
        normalized_schema = load_schema(artifact_id)
        assert (
            hashlib.sha256(_canonical_json(normalized_schema)).hexdigest()
            == identity["validation_schema_sha256"]
        )

    assert plan["source"]["document_digest"] == _domain_digest(
        contract["canonical_identity"]["document_domain"], SOURCE_DOCUMENT
    )
    assert plan["source"]["compliance_digest"] == _domain_digest(
        contract["canonical_identity"]["compliance_domain"], None
    )
    assert plan["profile"]["metadata_digest"] == _domain_digest(
        contract["canonical_identity"]["metadata_domain"], PROFILE_METADATA
    )


def test_all_directed_pairs_are_current_planner_inputs_after_m3() -> None:
    contract = _fixture()
    _assert_pair_matrix(contract)
    assert len(contract["pair_matrix"]) == 4 * (4 - 1)
    assert {pair["artifact_availability"] for pair in contract["pair_matrix"]} == {"current"}
    assert {pair["runtime_status"] for pair in contract["pair_matrix"]} == {
        "planner-runtime-active-empty-production-registry"
    }
    assert (REPO_ROOT / "app/schemas/policies/firefox-esr-115.38.json").exists()


def test_preview_identity_and_atomization_ignore_object_and_pair_declaration_order() -> None:
    first_document = {
        "policies": {
            "Dynamic": {
                "empty/key~one": {},
                "list": [True, {"z": 1, "a": 2}],
            },
            "EmptyArray": [],
        }
    }
    second_document = {
        "policies": {
            "EmptyArray": [],
            "Dynamic": {
                "list": [True, {"a": 2, "z": 1}],
                "empty/key~one": {},
            },
        }
    }
    expected_atoms = (
        "/policies/Dynamic/empty~1key~0one",
        "/policies/Dynamic/list/0",
        "/policies/Dynamic/list/1/a",
        "/policies/Dynamic/list/1/z",
        "/policies/EmptyArray",
    )
    assert _atom_paths(first_document) == expected_atoms
    assert _atom_paths(second_document) == expected_atoms
    contract = _fixture()
    assert _domain_digest(contract["canonical_identity"]["document_domain"], first_document) == (
        _domain_digest(contract["canonical_identity"]["document_domain"], second_document)
    )

    reordered = copy.deepcopy(contract)
    reordered["pair_matrix"].reverse()
    _assert_contract_semantics(reordered)
    plan = contract["examples"]["plan"]
    reversed_mapping_plan = dict(reversed(list(plan.items())))
    assert _plan_digest(contract, reversed_mapping_plan) == plan["plan_digest"]


def test_positive_transformed_and_blocked_vectors_preserve_no_silent_loss_rules() -> None:
    contract = _fixture()
    transformed = _make_transformed_plan(contract)
    _definition_validator("conversionPlan").validate(transformed)
    _assert_plan_semantics(
        contract,
        transformed,
        source_document=SOURCE_DOCUMENT,
        target_document=TARGET_DOCUMENT,
    )

    blocked = _make_blocked_plan(contract)
    _assert_plan_semantics(
        contract,
        blocked,
        source_document=SOURCE_DOCUMENT,
        target_document=TARGET_DOCUMENT,
    )
    assert blocked["target_validation"]["status"] == "valid"
    assert blocked["compatibility"] == {
        "status": "blocked",
        "applicable": False,
        "counts": {
            "source_atoms": 1,
            "target_atoms": 1,
            "unchanged_byte": 0,
            "unchanged_semantic": 0,
            "transformed": 0,
            "blocked": 1,
            "warnings": 0,
            "blockers": 1,
        },
    }
    assert contract["examples"]["error"]["code"] == "conversion_plan_blocked"
    assert contract["examples"]["error"]["mutation"] == "none"


def test_compliance_contract_matches_current_opaque_json_and_preserves_every_leaf_on_invalidation() -> (
    None
):
    contract = _fixture()
    golden = _load_json(GOLDEN_PROFILES_PATH)
    compliance_values = [
        case["source"]["compliance"]
        for scenario in golden["scenarios"]
        for case in scenario["cases"]
        if case["source"].get("compliance") is not None
    ]
    assert compliance_values
    assert any("schema_version" not in value for value in compliance_values)
    assert contract["compliance_contract"]["non_null_fallback"] == "invalidated-preserved"

    source = {
        "benchmark": "CIS Firefox Benchmark",
        "level": 2,
        "decisions": {"Proxy/Mode": {"decision": "exception", "note": "internal ticket 42"}},
    }
    source_digest = _domain_digest(contract["canonical_identity"]["compliance_domain"], source)
    invalidated = {
        "schema_version": 1,
        "status": "invalidated",
        "reason_code": "compliance_target_proof_unavailable",
        "source_artifact_id": "release-153",
        "target_artifact_id": "esr-153.0",
        "source_compliance_digest": source_digest,
        "current_claims": False,
        "preserved_source": copy.deepcopy(source),
    }
    assert set(contract["compliance_contract"]["invalidated_envelope_required_fields"]) == set(
        invalidated
    )
    assert invalidated["preserved_source"] == source
    assert _atom_paths(invalidated["preserved_source"]) == _atom_paths(source)
    assert invalidated["current_claims"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["classifications"].append("drop"),
        lambda value: value["pair_matrix"].pop(),
        lambda value: value["examples"]["plan"]["entries"][0].__setitem__("source_paths", []),
        lambda value: value["failure_semantics"][0].__setitem__("mutation", "partial"),
        lambda value: value["compliance_contract"].__setitem__("non_null_fallback", "preserve"),
        lambda value: value["examples"]["apply_request"].pop("recipe_registry_digest"),
    ],
)
def test_json_schema_rejects_drop_missing_identity_and_mutation_escape_hatches(
    mutation: Callable[[dict[str, Any]], Any],
) -> None:
    contract = copy.deepcopy(_fixture())
    mutation(contract)
    with pytest.raises(ValidationError):
        _schema_validator().validate(contract)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value["pair_matrix"].__setitem__(
                -1, copy.deepcopy(value["pair_matrix"][0])
            ),
            "pair matrix",
        ),
        (
            lambda value: value["examples"]["plan"]["entries"][0].__setitem__(
                "source_paths", ["/policies/Missing"]
            ),
            "source atom",
        ),
        (
            lambda value: value["examples"]["plan"]["entries"][0].__setitem__(
                "evidence_digest", None
            ),
            "require evidence",
        ),
        (
            lambda value: value["examples"]["plan"]["target_validation"].__setitem__(
                "status", "invalid"
            ),
            "applicability",
        ),
        (
            lambda value: value["examples"]["plan"].__setitem__("plan_digest", "f" * 64),
            "plan digest",
        ),
        (
            lambda value: value["profile_field_accounting"]["preserved_fields"].remove(
                "description"
            ),
            "preserved metadata",
        ),
        (
            lambda value: value["examples"]["result"].__setitem__("result_revision", 9),
            "increment once",
        ),
    ],
)
def test_semantic_mutations_reject_unaccounted_paths_stale_identity_and_metadata_loss(
    mutation: Callable[[dict[str, Any]], Any],
    message: str,
) -> None:
    contract = copy.deepcopy(_fixture())
    mutation(contract)
    with pytest.raises(ValueError, match=message):
        _assert_contract_semantics(contract)


def test_transformation_without_exact_registry_recipe_is_rejected() -> None:
    contract = _fixture()
    transformed = _make_transformed_plan(contract)
    transformed["recipe_registry"]["recipes"] = []
    _rehash_plan(contract, transformed)
    with pytest.raises(ValueError, match="not bound to exact registry identity"):
        _assert_plan_semantics(
            contract,
            transformed,
            source_document=SOURCE_DOCUMENT,
            target_document=TARGET_DOCUMENT,
        )


def test_markdown_records_cross_system_boundaries_and_no_runtime_claim() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    normalized_contract = " ".join(contract.split()).casefold()
    for required in (
        "no `drop`, `best-effort`, `implicit-default`",
        "every source atom is covered exactly once",
        "every candidate-target atom is produced and covered exactly once",
        "opaque compliance is invalidated while preserved",
        "permanent requirement is all",
        "`4 × (4 - 1) = 12` ordered pairs",
        "empty immutable recipe registry",
        "M4-03 owns the read-only API",
        "M2-05 separately owns the retirement gate",
        "assigns only `schema_version`",
        "revision = source_revision + 1",
        "leave every profile field and timestamp unchanged",
        "direct `PATCH` changes of `schema_version`",
        "M2-04 approves no production transformation recipe",
        "Sol-level cross-system decisions",
        "no raw values",
    ):
        assert required.casefold() in normalized_contract
