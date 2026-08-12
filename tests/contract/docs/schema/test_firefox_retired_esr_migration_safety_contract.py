from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from app.core.schemas_loader import load_schema
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = (
    REPO_ROOT / "docs/architecture/firefox-retired-esr-migration-safety-contract-0.9.5.md"
)
FIXTURE_PATH = (
    REPO_ROOT / "docs/architecture/firefox-retired-esr-migration-safety-contract-0.9.5.json"
)
SCHEMA_PATH = (
    REPO_ROOT / "docs/architecture/schemas/firefox-retired-esr-migration-contract-v1.schema.json"
)
LIFECYCLE_PATH = (
    REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
)
CONVERSION_PATH = (
    REPO_ROOT / "docs/architecture/firefox-pairwise-profile-conversion-contract-0.9.5.json"
)
DATABASE_CONTRACT_PATH = REPO_ROOT / "docs/architecture/database-upgrade-matrix-0.9.4.json"


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


def _validator() -> Draft202012Validator:
    schema = _load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _canonical_json(value: Any) -> bytes:
    # Contract vectors avoid RFC 8785 numeric edge cases. M6 owns the runtime
    # canonicalizer used for production evidence.
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _domain_digest(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("utf-8") + _canonical_json(value)).hexdigest()


def _manifest_digest(contract: dict[str, Any], manifest: dict[str, Any]) -> str:
    projection = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    return _domain_digest(contract["canonical_identity"]["transition_manifest_domain"], projection)


def _preflight_digest(contract: dict[str, Any], preflight: dict[str, Any]) -> str:
    projection = {key: value for key, value in preflight.items() if key != "preflight_digest"}
    return _domain_digest(contract["canonical_identity"]["preflight_evidence_domain"], projection)


def _rehash_fixture(contract: dict[str, Any], fixture: dict[str, Any]) -> None:
    fixture["manifest"]["manifest_digest"] = _manifest_digest(contract, fixture["manifest"])
    fixture["preflight"]["manifest_digest"] = fixture["manifest"]["manifest_digest"]
    fixture["preflight"]["preflight_digest"] = _preflight_digest(contract, fixture["preflight"])


def _assert_transition_fixture(contract: dict[str, Any], fixture: dict[str, Any]) -> None:
    manifest = fixture["manifest"]
    proof = fixture["total_proof"]
    preflight = fixture["preflight"]
    expected = fixture["expected"]

    if manifest["manifest_digest"] != _manifest_digest(contract, manifest):
        raise ValueError("transition manifest digest is stale")
    if preflight["manifest_digest"] != manifest["manifest_digest"]:
        raise ValueError("preflight does not bind the transition manifest")
    if preflight["preflight_digest"] != _preflight_digest(contract, preflight):
        raise ValueError("preflight evidence digest is stale")

    source = manifest["source"]
    target = manifest["target"]
    if source["family"] != "esr" or target["family"] != "esr":
        raise ValueError("retirement successor must remain in the ESR family")
    if target["line_number"] <= source["line_number"]:
        raise ValueError("retirement successor must be newer")

    supported_rows = manifest["candidate_supported_esr_lines"]
    line_ids = [row["line_id"] for row in supported_rows]
    if len(line_ids) != len(set(line_ids)):
        raise ValueError("candidate supported ESR lines must be unique")
    if supported_rows != sorted(supported_rows, key=lambda row: row["line_number"]):
        raise ValueError("candidate supported ESR lines must use numeric order")
    newer_rows = [row for row in supported_rows if row["line_number"] > source["line_number"]]
    if not newer_rows:
        raise ValueError("retirement successor is missing")
    immediate = min(newer_rows, key=lambda row: row["line_number"])
    if target["line_id"] != immediate["line_id"]:
        raise ValueError("retirement successor skips a supported intermediate ESR")
    if target["artifact_id"] != immediate["artifact_id"]:
        raise ValueError("retirement target exact artifact does not resolve from successor")
    if manifest["declared_successor_line_id"] != immediate["line_id"]:
        raise ValueError("declared successor does not equal immediate supported ESR")

    if proof["proof_artifact_digest"] != manifest["total_proof_artifact_digest"]:
        raise ValueError("manifest total-proof identity mismatch")
    if proof["status"] == "complete":
        if proof["method"] not in contract["total_convertibility"]["approved_methods"]:
            raise ValueError("complete proof uses an unapproved method")
        if not proof["exact_artifacts_bound"]:
            raise ValueError("complete proof must bind exact artifacts")
        if proof["uncovered_schema_locations"] or proof["blockers"]:
            raise ValueError("complete proof cannot leave uncovered schema locations")
        if preflight["status"] == "not-run-m6-03-migration-pending":
            if manifest["alembic_target_revision"] is not None:
                raise ValueError("M6-03-pending proof cannot name a migration revision")
            if manifest["evidence_scope"] != "current-exact-artifacts":
                raise ValueError("M6-03-pending fixture must retain its reviewed candidate scope")
            if proof["evidence_scope"] != "production-exact-artifacts":
                raise ValueError("M6-03-pending fixture requires production exact proof evidence")
            if any(
                preflight[key] != 0
                for key in (
                    "profile_count",
                    "affected_source_count",
                    "planned_count",
                    "blocked_count",
                    "already_target_count",
                )
            ):
                raise ValueError("M6-03-pending fixture cannot invent database preflight counts")
            if preflight["no_active_writers"] is not None or preflight["backup"]["status"] != (
                "not-required-m6-03-migration-pending"
            ):
                raise ValueError("M6-03-pending proof cannot claim backup or writer evidence")
            if expected != {
                "decision": "m6-02-proof-complete-m6-03-pending",
                "production_promotable": False,
                "mutation": "none",
                "code": None,
            }:
                raise ValueError("M6-03-pending fixture must not imply a production migration")
        else:
            if preflight["status"] == "not-run-static-gate-blocked":
                raise ValueError("complete proof fixture must exercise preflight")
            if preflight["planned_count"] != preflight["affected_source_count"]:
                raise ValueError("preflight must plan every affected source profile")
            if preflight["blocked_count"] != 0:
                raise ValueError("passing preflight cannot contain blocked profiles")
            backup = preflight["backup"]
            if backup["status"] != "verified-native-restore":
                raise ValueError("passing preflight requires verified native restore")
            if backup["source_stamp"] != backup["restored_stamp"]:
                raise ValueError("restored backup stamp differs from source")
            if backup["source_profile_count"] != backup["restored_profile_count"]:
                raise ValueError("restored backup profile count differs from source")
            if preflight["no_active_writers"] is not True:
                raise ValueError("passing preflight requires all writers stopped")
            if manifest["evidence_scope"] == "synthetic-contract-only":
                if expected["decision"] != "pass-contract-fixture-only":
                    raise ValueError("synthetic proof may pass only as a contract fixture")
                if expected["production_promotable"]:
                    raise ValueError("synthetic evidence cannot promote production retirement")
    else:
        if not proof["uncovered_schema_locations"] or not proof["blockers"]:
            raise ValueError("incomplete proof must expose exact uncovered schema locations")
        if expected != {
            "decision": "block-before-mutation",
            "production_promotable": False,
            "mutation": "none",
            "code": "retirement_total_convertibility_unproven",
        }:
            raise ValueError("incomplete proof must fail closed before mutation")
        if manifest["alembic_target_revision"] is not None:
            raise ValueError("incomplete proof cannot name a migration revision")
        if preflight["status"] != "not-run-static-gate-blocked":
            raise ValueError("database preflight cannot run before the static proof gate")


def _assert_contract_semantics(contract: dict[str, Any]) -> None:
    required_gate_order = contract["retirement_promotion_gate"]["required_order"]
    if required_gate_order.index("successor-valid") >= required_gate_order.index(
        "total-convertibility-complete"
    ):
        raise ValueError("successor validation must precede total proof")
    if required_gate_order.index("total-convertibility-complete") >= required_gate_order.index(
        "native-backup-restored-and-verified"
    ):
        raise ValueError("schema-wide proof must precede database backup/preflight")
    if required_gate_order.index("database-preflight-complete") >= required_gate_order.index(
        "single-transaction-apply"
    ):
        raise ValueError("database preflight must precede apply")

    ownership = contract["ownership"]
    if ownership["sole_writer"] != "versioned-alembic-retirement-revision":
        raise ValueError("Alembic revision must remain the sole writer")
    required_forbidden_writers = {
        "application-startup",
        "request-handler",
        "profile-list-or-get",
        "conversion-preview",
        "ui-rendering",
    }
    if set(ownership["forbidden_write_paths"]) != required_forbidden_writers:
        raise ValueError("runtime read-only writer boundary drift")

    atomic = contract["atomic_apply"]
    if atomic["transaction_scope"] != "all-affected-profiles-plus-alembic-version-stamp":
        raise ValueError("profile rows and Alembic stamp must share one transaction")
    if atomic["commit_count"] != 1 or atomic["partial_success_reportable"]:
        raise ValueError("retirement apply must expose one atomic outcome")
    if atomic["revision_increment"] != 1:
        raise ValueError("affected profile revision must increment exactly once")

    failures = contract["failure_semantics"]
    failure_codes = [failure["code"] for failure in failures]
    if len(failure_codes) != len(set(failure_codes)):
        raise ValueError("retirement failure codes must be unique")
    if any(failure["mutation"] != "none" for failure in failures):
        raise ValueError("every retirement failure must be nonmutating")

    transition_fixtures = [
        contract["fixtures"]["synthetic_esr115_to_esr140"],
        contract["fixtures"]["required_esr140_to_esr153"],
    ]
    fixture_ids = [fixture["fixture_id"] for fixture in transition_fixtures]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise ValueError("transition fixture IDs must be unique")
    for fixture in transition_fixtures:
        _assert_transition_fixture(contract, fixture)

    negative_vectors = contract["fixtures"]["negative_vectors"]
    vector_ids = [vector["vector_id"] for vector in negative_vectors]
    if len(vector_ids) != len(set(vector_ids)):
        raise ValueError("negative vector IDs must be unique")
    if {vector["base_fixture_id"] for vector in negative_vectors} - set(fixture_ids):
        raise ValueError("negative vector references an unknown fixture")
    failure_code_set = set(failure_codes)
    for vector in negative_vectors:
        if vector["expected_mutation"] == "none":
            if vector["expected_code"] not in failure_code_set:
                raise ValueError("negative vector code lacks failure semantics")
        elif vector != next(
            item for item in negative_vectors if item["vector_id"] == "already-migrated"
        ):
            raise ValueError("only already-applied idempotency may be a no-op")

    engines = contract["engine_evidence"]
    if set(engines) != {"sqlite", "postgresql"}:
        raise ValueError("both database engines require evidence")
    if any(not evidence["required"] for evidence in engines.values()):
        raise ValueError("database engine evidence cannot be optional")


def test_contract_schema_examples_digests_and_docs_index() -> None:
    contract = _fixture()
    _validator().validate(contract)
    _assert_contract_semantics(contract)

    assert (
        doc_path_from_index(
            "architecture/firefox-retired-esr-migration-safety-contract-0.9.5.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    assert (
        doc_path_from_index(
            "architecture/firefox-retired-esr-migration-safety-contract-0.9.5.json",
            status="active",
        )
        == FIXTURE_PATH
    )
    assert (
        doc_path_from_index(
            "architecture/schemas/firefox-retired-esr-migration-contract-v1.schema.json",
            status="active",
        )
        == SCHEMA_PATH
    )


def test_contract_reuses_lifecycle_conversion_and_database_boundaries() -> None:
    contract = _fixture()
    lifecycle = _load_json(LIFECYCLE_PATH)
    conversion = _load_json(CONVERSION_PATH)
    database_contract = _load_json(DATABASE_CONTRACT_PATH)

    assert contract["dependencies"]["lifecycle_catalog"] == {
        "contract_id": lifecycle["contract_id"],
        "schema_version": lifecycle["schema_version"],
        "path": LIFECYCLE_PATH.relative_to(REPO_ROOT).as_posix(),
    }
    assert contract["dependencies"]["conversion_contract"] == {
        "contract_id": conversion["contract_id"],
        "schema_version": conversion["schema_version"],
        "path": CONVERSION_PATH.relative_to(REPO_ROOT).as_posix(),
    }
    assert contract["dependencies"]["database_upgrade_contract"] == {
        "contract_version": database_contract["contract_version"],
        "path": DATABASE_CONTRACT_PATH.relative_to(REPO_ROOT).as_posix(),
    }

    atomic = contract["atomic_apply"]
    profile_fields = conversion["profile_field_accounting"]
    assert atomic["application_write_fields"] == profile_fields["application_write_fields"]
    assert atomic["database_managed_fields"] == profile_fields["database_managed_fields"]
    assert atomic["preserved_fields"] == profile_fields["preserved_fields"]
    assert atomic["revision_increment"] == profile_fields["revision_increment"]
    assert atomic["compliance_dispositions"] == conversion["compliance_contract"]["dispositions"]
    assert contract["ownership"]["unupgraded_runtime_behavior"]["code"] in {
        failure["code"] for failure in conversion["failure_semantics"]
    }
    conversion_failure_codes = {failure["code"] for failure in conversion["failure_semantics"]}
    retirement_shared_conversion_codes = {
        failure["code"]
        for failure in contract["failure_semantics"]
        if failure["code"].startswith("conversion_")
    }
    assert retirement_shared_conversion_codes == {
        "conversion_source_schema_missing",
        "conversion_target_schema_missing",
        "conversion_source_invalid",
        "conversion_recipe_registry_stale",
        "conversion_plan_blocked",
    }
    assert retirement_shared_conversion_codes <= conversion_failure_codes
    assert contract["idempotency_and_interruption"]["already_applied_outcome_code"] == (
        "retirement_already_applied"
    )
    assert database_contract["recovery_evidence"]["engines"] == ["sqlite", "postgresql"]
    assert "unsupported" in database_contract["recovery_evidence"]["downgrade_policy"]


def test_required_transition_identities_match_catalog_pair_and_current_bundles() -> None:
    contract = _fixture()
    fixture = contract["fixtures"]["required_esr140_to_esr153"]
    manifest = fixture["manifest"]
    lifecycle = _load_json(LIFECYCLE_PATH)
    lifecycle_rows = {row["artifact_id"]: row for row in lifecycle["channels"]}
    conversion = _load_json(CONVERSION_PATH)

    assert (
        manifest["previous_catalog_digest"]
        == hashlib.sha256(_canonical_json(lifecycle)).hexdigest()
    )
    assert manifest["conversion_contract_version"] == conversion["schema_version"]
    registry = conversion["examples"]["plan"]["recipe_registry"]
    assert manifest["recipe_registry_version"] == registry["registry_version"]
    assert manifest["recipe_registry_digest"] == registry["registry_digest"]

    for side in ("source", "target"):
        identity = manifest[side]
        row = lifecycle_rows[identity["artifact_id"]]
        assert identity["family"] == row["family"]
        assert identity["line_id"] == row["line_id"]
        assert identity["line_number"] == row["line_number"]
        bundle = REPO_ROOT / row["source"]["output_path"]
        assert hashlib.sha256(bundle.read_bytes()).hexdigest() == identity["schema_bundle_sha256"]
        normalized = load_schema(identity["artifact_id"])
        assert (
            hashlib.sha256(_canonical_json(normalized)).hexdigest()
            == identity["validation_schema_sha256"]
        )

    assert (
        lifecycle_rows[manifest["source"]["artifact_id"]]["retirement_successor_line_id"]
        == manifest["declared_successor_line_id"]
    )
    assert (
        manifest["source"]["artifact_id"],
        manifest["target"]["artifact_id"],
    ) in {
        (pair["source_artifact_id"], pair["target_artifact_id"])
        for pair in conversion["pair_matrix"]
    }
    assert fixture["total_proof"] == {
        "status": "complete",
        "method": "schema-containment",
        "evidence_scope": "production-exact-artifacts",
        "exact_artifacts_bound": True,
        "source_schema_domain": "all-valid-instances",
        "proof_artifact_digest": "3d04890c00a89534526fea7456e89250c36ba3617fa0d10949c8e51d98bcc2bb",
        "uncovered_schema_locations": [],
        "blockers": [],
    }
    assert fixture["preflight"]["status"] == "not-run-m6-03-migration-pending"
    assert fixture["expected"]["decision"] == "m6-02-proof-complete-m6-03-pending"


def test_synthetic_transition_proves_gate_shape_without_production_claim() -> None:
    contract = _fixture()
    fixture = contract["fixtures"]["synthetic_esr115_to_esr140"]
    manifest = fixture["manifest"]

    assert manifest["source"]["line_id"] == "esr-115"
    assert manifest["target"]["line_id"] == "esr-140"
    assert fixture["total_proof"]["status"] == "complete"
    assert fixture["total_proof"]["evidence_scope"] == "synthetic-contract-only"
    assert fixture["expected"] == {
        "decision": "pass-contract-fixture-only",
        "production_promotable": False,
        "mutation": "none",
        "code": None,
    }
    assert fixture["preflight"]["affected_source_count"] == fixture["preflight"]["planned_count"]
    assert fixture["preflight"]["already_target_count"] == 1


def test_negative_vectors_cover_required_failure_and_idempotency_boundaries() -> None:
    vectors = _fixture()["fixtures"]["negative_vectors"]
    by_id = {vector["vector_id"]: vector for vector in vectors}

    assert set(by_id) == {
        "missing-successor",
        "skip-supported-intermediate",
        "incomplete-total-proof",
        "stale-transition-manifest",
        "mismatched-transition-manifest",
        "partial-failure",
        "interrupted-before-commit",
        "already-migrated",
        "partial-state-before-retry",
        "rollback-or-downgrade",
    }
    assert by_id["partial-failure"]["expected_mutation"] == "none"
    assert by_id["already-migrated"]["expected_mutation"] == "no-op"
    assert by_id["rollback-or-downgrade"]["expected_code"] == ("retirement_downgrade_unsupported")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["ownership"].__setitem__("sole_writer", "application-startup"),
        lambda value: value["retirement_promotion_gate"].__setitem__(
            "sample_profiles_are_total_proof", True
        ),
        lambda value: value["atomic_apply"].__setitem__("commit_count", 2),
        lambda value: value["engine_evidence"]["postgresql"].__setitem__("required", False),
        lambda value: value["downgrade"].__setitem__("downgrade_writes_allowed", True),
        lambda value: value["fixtures"]["negative_vectors"][5].__setitem__(
            "expected_mutation", "partial"
        ),
    ],
)
def test_json_schema_rejects_writer_sample_partial_and_engine_escape_hatches(
    mutation: Callable[[dict[str, Any]], Any],
) -> None:
    contract = copy.deepcopy(_fixture())
    mutation(contract)
    with pytest.raises(ValidationError):
        _validator().validate(contract)


def test_semantics_reject_skip_stale_manifest_incomplete_claim_and_unverified_backup() -> None:
    contract = _fixture()

    skipped = copy.deepcopy(contract)
    skipped_fixture = skipped["fixtures"]["synthetic_esr115_to_esr140"]
    skipped_fixture["manifest"]["target"].update(
        {
            "line_id": "esr-153",
            "line_number": 153,
            "artifact_id": "esr-153.0",
        }
    )
    skipped_fixture["manifest"]["declared_successor_line_id"] = "esr-153"
    _rehash_fixture(skipped, skipped_fixture)
    with pytest.raises(ValueError, match="skips a supported intermediate ESR"):
        _assert_contract_semantics(skipped)

    stale = copy.deepcopy(contract)
    stale["fixtures"]["synthetic_esr115_to_esr140"]["manifest"]["candidate_catalog_digest"] = (
        "f" * 64
    )
    with pytest.raises(ValueError, match="manifest digest is stale"):
        _assert_contract_semantics(stale)

    stale_proof = copy.deepcopy(contract)
    stale_proof["fixtures"]["required_esr140_to_esr153"]["total_proof"]["proof_artifact_digest"] = (
        "e" * 64
    )
    with pytest.raises(ValueError, match="manifest total-proof identity mismatch"):
        _assert_contract_semantics(stale_proof)

    unverified_backup = copy.deepcopy(contract)
    unverified_fixture = unverified_backup["fixtures"]["synthetic_esr115_to_esr140"]
    unverified_fixture["preflight"]["backup"]["status"] = "not-required-static-gate-blocked"
    _rehash_fixture(unverified_backup, unverified_fixture)
    with pytest.raises(ValueError, match="verified native restore"):
        _assert_contract_semantics(unverified_backup)


def test_markdown_records_fail_closed_safety_and_nonimplementation_boundary() -> None:
    markdown = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    for required in (
        "only in this order",
        "every json instance valid under the exact normalized source validation schema",
        "schema containment",
        "complete recipe partition",
        "policy-name subset comparison is not semantic or value-shape containment",
        "sampled/current profiles are explicitly forbidden substitutes",
        "one explicit offline alembic revision is the sole writer",
        "application startup, request handlers, profile list/get",
        "all stored profiles on the exact retired artifact",
        "revision` from its exact preflight value to that value plus one",
        "one commit",
        "already on the successor",
        "downgrade is not recovery",
        "sqlite and postgresql candidates",
        "retirement_total_convertibility_unproven",
        "creates no runtime converter",
    ):
        assert required in markdown
