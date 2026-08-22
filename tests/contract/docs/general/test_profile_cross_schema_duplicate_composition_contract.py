from __future__ import annotations

import json
import re
from itertools import permutations
from pathlib import Path

from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNELS
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = (
    REPO_ROOT / "docs/architecture/profile-cross-schema-duplicate-composition-contract-0.9.6.md"
)
FIXTURE_MARKER = "<!-- bpm096-profile-duplicate-composition-contract-v1 -->"


def _fixture() -> dict[str, object]:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "profile duplicate composition contract fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_duplicate_composition_contract_is_active_planning_only_and_backlog_linked() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-cross-schema-duplicate-composition-contract-0.9.6.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "`bpm096-m2-05`" in source
    assert "adds no runtime composer" in source
    assert "not an m3 api or m4 ui implementation" in source

    backlog = (
        REPO_ROOT / "docs/bpm_0_9_6_profile_creation_guided_editor_backlog_2026-08-20.md"
    ).read_text(encoding="utf-8")
    assert "### BPM096-M2-05 — Cross-schema duplicate composition contract" in backlog
    assert "profile-cross-schema-duplicate-composition-contract-0.9.6.md" in backlog


def test_schema_matrix_covers_same_schema_and_every_directed_cross_schema_target() -> None:
    matrix = _fixture()["schema_matrix"]
    assert isinstance(matrix, dict)
    artifacts = matrix["artifacts"]
    assert artifacts == list(SUPPORTED_SCHEMA_CHANNELS)
    assert matrix["same_schema_target_count"] == len(artifacts) == 4
    same_schema_targets = tuple(tuple(pair) for pair in matrix["same_schema_targets"])
    assert same_schema_targets == tuple((artifact, artifact) for artifact in artifacts)

    pairs = tuple(permutations(artifacts, 2))
    assert len(pairs) == matrix["directed_cross_schema_pair_count"] == 12
    assert len(set(pairs)) == 12
    assert all(source != target for source, target in pairs)
    assert matrix["pair_rule"] == "all-ordered-non-self-pairs"
    declared_pairs = tuple(tuple(pair) for pair in matrix["directed_cross_schema_pairs"])
    assert declared_pairs == pairs
    assert len(set(declared_pairs)) == len(declared_pairs)


def test_source_precedence_preset_fill_and_cis_decisions_are_closed_sets() -> None:
    contract = _fixture()
    assert contract["precedence"] == [
        "converted-source",
        "absent-path-preset-fill",
        "reviewed-cis-merge",
    ]
    assert contract["base_derivation"] == {
        "same_schema": "validated-private-deep-copy",
        "cross_schema": "current-applicable-pairwise-plan-private-candidate",
        "relabel_without_conversion": "forbidden",
        "blocked_or_diagnostic_candidate_persistable": False,
        "production_recipe_count_at_contract_time": 0,
    }

    preset = contract["preset"]
    assert preset["keep_current"] == "no-fill-and-never-stored-as-preset-id"
    assert preset["existing_value_authority"] == "converted-source"
    assert preset["overwrite_or_remove_source_value"] == "forbidden"
    assert preset["every_resolved_atom_accounted"] is True
    assert set(preset["allowed_decisions"]) == {
        "filled-absent",
        "source-identical",
        "source-preserved",
        "blocked-structural-collision",
        "blocked-invalid-preset-path",
    }

    cis = contract["cis"]
    assert cis["none"] == "no-layer"
    assert cis["merge_owner"] == ("app.compliance.firefox.cis.merge.merge_base_with_cis_layer")
    assert set(cis["allowed_decisions"]) == {
        "added_from_cis",
        "kept_base_only",
        "already_satisfied",
        "cis_replaced_base",
        "kept_base_stricter",
        "manual_review_kept_base",
    }
    assert cis["cis_replacement_requires_reviewed_rule"] is True
    assert cis["manual_review_current_claim"] is False
    assert cis["verified_requires_target_proof_and_zero_review"] is True
    assert cis["every_layer_and_base_outcome_accounted"] is True

    assert contract["baseline_provenance"] == {
        "same_schema_exact_carry": "preserve-identities-and-statuses-without-promotion",
        "explicit_preset_starter": "exact-target-catalog-identity-recomposed",
        "keep_current_recomposed_starter": "custom-imported-with-source-lineage-digest",
        "cis_none": "none-with-current-claim-false",
        "cis_catalog_verified": "target-proof-and-zero-review-only",
        "cis_catalog_review": "manual-review-with-current-claim-false",
        "source_compliance_evidence": "preserved-and-never-live-without-target-proof",
    }
    assert contract["extension_provenance"] == {
        "storage": "separate-value-level-review-metadata",
        "same_schema_unchanged": "preserve-source-attribution",
        "cross_schema_supported": "converted-only-after-applicable-pairwise-plan",
        "cross_schema_unsupported": "block-with-zero-target-writes",
        "preset_fill": "preset",
        "cis_selected_layer": "cis",
        "legacy_migration": "imported-without-historical-inference",
    }
    assert contract["certificate_provenance"] == {
        "storage": "separate-value-level-review-metadata",
        "baseline_provenance": "never-modified-by-attribution",
        "same_schema_unchanged": "preserve-source-attribution",
        "cross_schema_supported": "converted-only-after-applicable-pairwise-plan",
        "cross_schema_unsupported": "block-with-zero-target-writes",
        "preset_fill": "baseline",
        "cis_selected_layer": "cis-with-review-visible-without-benchmark-promotion",
        "legacy_migration": "imported-without-historical-inference",
    }


def test_digest_revision_validation_and_source_nonmutation_fail_closed() -> None:
    contract = _fixture()
    identity = contract["identity"]
    assert identity["canonicalization"] == "RFC-8785-JCS"
    assert identity["digest"] == "sha256-lowercase-hex"
    assert identity["composition_domain"] == "bpm096-profile-duplicate-composition:v1\n"
    assert set(identity["binds"]) == {
        "source-snapshot",
        "source-target-artifacts-and-validators",
        "conversion-plan-and-recipe-registry-or-same-schema-marker",
        "preset-definition",
        "cis-layer-and-merge-rules",
        "ordered-decision-ledgers-and-blockers",
        "target-document-compliance-and-provenance",
        "final-target-validation",
    }

    acceptance = contract["acceptance"]
    assert acceptance == {
        "source_must_validate": True,
        "cross_schema_plan_applicable": True,
        "cross_schema_plan_blockers": 0,
        "final_target_validation": "valid",
        "final_blockers": 0,
        "ledger_coverage": "complete",
        "stale_plan_creation": "forbidden",
        "invalid_plan_creation": "forbidden",
    }
    assert contract["revision"] == {
        "target_initial_revision": 1,
        "source_revision_increment": 0,
    }

    nonmutation = contract["source_nonmutation"]
    assert set(nonmutation["applies_to"]) == {"planning", "rejection", "success"}
    assert set(nonmutation["unchanged_fields"]) == {
        "name",
        "description",
        "schema_version",
        "flags",
        "compliance",
        "baseline_provenance",
        "extension_provenance",
        "certificate_provenance",
        "lifecycle",
        "revision",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert nonmutation["source_writes"] == 0

    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    for required_text in (
        "rerun target validation",
        "cannot be accepted because its final document happens to validate",
        "inserts zero rows",
        "source revision does not advance",
    ):
        assert required_text in source
