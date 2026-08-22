from __future__ import annotations

import json
import re
from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "docs/architecture/profile-baseline-provenance-contract-0.9.6.md"
FIXTURE_MARKER = "<!-- bpm096-baseline-provenance-contract-v1 -->"


def _fixture() -> dict[str, object]:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "baseline provenance contract fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_baseline_provenance_contract_is_active_and_planning_only() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-baseline-provenance-contract-0.9.6.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "`bpm096-m2-04`" in source
    assert "no current runtime, api, database," in source
    assert "not inspect flags" in source


def test_durable_starter_and_cis_identity_states_are_explicit() -> None:
    contract = _fixture()
    assert contract["contract_id"] == "bpm096-profile-baseline-provenance"
    assert contract["contract_version"] == 1
    assert contract["status"] == "planning-only-no-runtime-change"
    assert contract["storage"] == {
        "profile_field": "baseline_provenance",
        "required_after_m3_01": True,
        "authoritative_for_header": True,
        "flags_or_compliance_inference": "forbidden",
    }
    assert contract["starter"] == {
        "identity_states": ["catalog", "custom-imported"],
        "catalog_identity_fields": [
            "catalog_id",
            "catalog_version",
            "preset_id",
            "definition_sha256",
            "resolved_schema_artifact_id",
        ],
        "custom_imported_catalog_fields": "all-null",
        "request_only_directive": "keep_current",
    }
    cis = contract["cis"]
    assert cis["identity_states"] == ["none", "catalog", "custom-imported"]
    assert cis["display_statuses"] == [
        "none",
        "verified",
        "manual-review",
        "invalidated",
        "unavailable",
    ]
    assert cis["catalog_identity_fields"] == [
        "catalog_id",
        "catalog_version",
        "baseline_id",
        "benchmark_id",
        "benchmark_version",
        "layer_sha256",
        "merge_rules_sha256",
        "merge_result_sha256",
        "resolved_schema_artifact_id",
    ]
    assert cis["current_claim_rule"] == "true-only-for-verified"
    assert cis["noncurrent_statuses"] == [
        "none",
        "manual-review",
        "invalidated",
        "unavailable",
    ]


def test_projection_and_compatibility_cannot_upgrade_unknown_history() -> None:
    contract = _fixture()
    assert contract["api"] == {
        "profile_read_fields": ["baseline_provenance", "baseline_display"],
        "request_provenance_authority": "server-only",
        "generic_create_default": "custom-imported-manual-review",
        "firefox_import_default": "custom-imported-manual-review",
        "legacy_migration_default": "custom-imported-manual-review",
    }
    assert contract["duplicate"] == {
        "same_schema_exact_copy": "preserve-baseline-identities-and-statuses",
        "different_composition": "rederive-under-m2-05",
        "source_mutation": "forbidden",
    }
    assert contract["conversion"] == {
        "verified_target_cis": "requires-target-recomputation-and-proof",
        "unproven_target_cis": "invalidated-or-manual-review",
        "source_preset_history": "never-inferred-from-flags",
    }

    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    for required_text in (
        "any row predating m3-01, including archived rows",
        "imported `compliance` is raw data",
        "copying never promotes custom/imported/manual-review/invalidated/unavailable",
        "never stores `keep_current` as that id",
        "starter_preset_identity_unavailable",
        "truth table rather than comparing flags",
        "neither may fall back to `verified`, `none`, or a current catalog label",
    ):
        assert required_text in source
