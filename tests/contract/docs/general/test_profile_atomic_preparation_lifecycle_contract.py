from __future__ import annotations

import json
import re
from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = (
    REPO_ROOT / "docs/architecture/profile-atomic-preparation-lifecycle-contract-0.9.6.md"
)
FIXTURE_MARKER = "<!-- bpm096-atomic-preparation-contract-v1 -->"

EXPECTED_FAILURES = {
    "preparation_request_invalid",
    "preparation_schema_unavailable",
    "preparation_starter_unavailable",
    "preparation_cis_unavailable",
    "preparation_candidate_invalid",
    "preparation_name_conflict",
    "preparation_duplicate_source_not_found",
    "preparation_duplicate_source_not_eligible",
    "preparation_source_stale",
    "preparation_conversion_blocked",
    "preparation_composition_blocked",
    "preparation_idempotency_key_reused",
    "preparation_transaction_failed",
}


def _fixture() -> dict[str, object]:
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(FIXTURE_MARKER)}\s*```json\s*(\{{.*?\}})\s*```",
        source,
        flags=re.DOTALL,
    )
    assert match, "atomic preparation contract fixture is missing"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def test_atomic_preparation_contract_is_active_and_is_explicitly_planning_only() -> None:
    assert (
        doc_path_from_index(
            "architecture/profile-atomic-preparation-lifecycle-contract-0.9.6.md",
            status="active",
        )
        == CONTRACT_PATH
    )
    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "`bpm096-m2-03`" in source
    assert "no current runtime, api, database, or" in source
    assert "generic `post /api/profiles`" in source
    assert "generic `patch`" in source


def test_form_modes_and_get_are_unsaved_and_non_authoritative() -> None:
    contract = _fixture()
    assert contract["contract_id"] == "bpm096-atomic-profile-preparation"
    assert contract["contract_version"] == 1
    assert contract["status"] == "planning-only-no-runtime-change"
    assert contract["preparation_route"] == "/profiles/new"
    assert contract["modes"] == {
        "create": {"source_required": False, "terminal_action": "create"},
        "duplicate": {"source_required": True, "terminal_action": "duplicate"},
    }

    form = contract["form"]
    assert form["unsaved_only"] is True
    assert form["get_profile_rows_written"] == 0
    assert form["get_reserves_name"] is False
    assert form["get_persists_idempotency"] is False
    assert set(form["client_submit_fields"]) == {
        "mode",
        "name",
        "target_schema_id",
        "starter_id",
        "cis_baseline_id",
        "source_id",
        "expected_source_revision",
        "preparation_idempotency_key",
    }
    assert set(form["client_forbidden_authority"]) == {
        "flags",
        "composed_document",
        "compliance",
        "provenance",
        "conversion_candidate",
        "destination",
    }


def test_terminal_outcomes_prove_zero_failure_rows_source_nonmutation_and_one_destination() -> None:
    contract = _fixture()
    boundary = contract["write_boundary"]
    assert boundary == {
        "generic_create_or_patch_authorized": False,
        "server_rederives_candidate": True,
        "single_transaction": True,
        "success_new_profile_rows": 1,
        "terminal_failure_new_profile_rows": 0,
        "source_mutation": "forbidden",
    }
    assert set(contract["terminal_failures"]) == EXPECTED_FAILURES

    success = contract["success"]
    assert success == {
        "saved_profile": True,
        "destination_template": "/profiles/{profile_id}/edit",
        "navigation_after_success_only": True,
        "navigation_count": 1,
    }


def test_retry_and_interruption_boundary_cannot_create_a_second_profile() -> None:
    contract = _fixture()
    assert contract["idempotency"] == {
        "key_scope": "profile-library",
        "same_key_same_fingerprint": "return-original-success-without-insert",
        "same_key_different_fingerprint": "preparation_idempotency_key_reused",
        "terminal_failure_persistence": "none",
        "post_commit_response_loss": "indeterminate-reconcile-same-key",
    }
    assert contract["interruption"] == [
        {"point": "before-transaction", "profile_rows": 0, "source_changed": False},
        {"point": "before-commit", "profile_rows": 0, "source_changed": False},
        {
            "point": "after-commit-before-response",
            "profile_rows": 1,
            "source_changed": False,
        },
    ]

    source = " ".join(CONTRACT_PATH.read_text(encoding="utf-8").split()).casefold()
    assert "must never report a terminal failure after committing the target" in source
    assert (
        "no idempotency, planning, audit, or navigation state may be written to the source"
        in source
    )
