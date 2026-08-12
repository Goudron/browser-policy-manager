from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from app.core.locales import ACTIVE_CATALOG_LOCALES, SOURCE_LOCALE
from app.documentation.manifest import DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS
from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = (
    REPO_ROOT / "docs/architecture/firefox-schema-conversion-ui-copy-interaction-contract-0.9.5.md"
)
FIXTURE_PATH = (
    REPO_ROOT
    / "docs/architecture/firefox-schema-conversion-ui-copy-interaction-contract-0.9.5.json"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "docs/architecture/schemas/firefox-schema-conversion-ui-interaction-contract-v1.schema.json"
)
ACTIVE_UI_COPY_PATH = REPO_ROOT / "docs/architecture/ui-copy-classification-contract-0.9.2.md"
LIFECYCLE_PATH = (
    REPO_ROOT / "docs/architecture/firefox-schema-lifecycle-catalog-contract-0.9.5.json"
)
CONVERSION_PATH = (
    REPO_ROOT / "docs/architecture/firefox-pairwise-profile-conversion-contract-0.9.5.json"
)
RETIREMENT_PATH = (
    REPO_ROOT / "docs/architecture/firefox-retired-esr-migration-safety-contract-0.9.5.json"
)

EXPECTED_SURFACES = {"library", "compare", "guided", "settings", "json", "shared-review"}
EXPECTED_STATE_IDS = {
    "schema-conversion.older-esr-recommendation",
    "schema-conversion.recommendation-not-eligible",
    "schema-conversion.manual-target-selection",
    "schema-conversion.preview-pending",
    "schema-conversion.preview-available",
    "schema-conversion.preview-blocked",
    "schema-conversion.preview-unavailable",
    "schema-conversion.unsaved-work-decision",
    "schema-conversion.confirmation-ready",
    "schema-conversion.apply-in-progress",
    "schema-conversion.apply-success",
    "schema-conversion.stale-revision",
    "schema-conversion.plan-or-validation-changed",
    "schema-conversion.source-not-active",
    "schema-conversion.target-unavailable",
    "schema-conversion.source-invalid",
    "schema-conversion.apply-failed-retry",
    "schema-conversion.retirement-operator-boundary",
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


def _validator() -> Draft202012Validator:
    schema = _load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _state_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {state["state_id"]: state for state in contract["interaction_states"]}


def _assert_semantics(contract: dict[str, Any]) -> None:
    owners = contract["surface_owners"]
    owner_ids = [owner["owner_id"] for owner in owners]
    assert len(owner_ids) == len(set(owner_ids))
    assert {owner["surface"] for owner in owners} == EXPECTED_SURFACES
    assert [owner["owner_id"] for owner in owners if owner["may_apply"]] == ["shared-review-owner"]
    for owner in owners:
        for source_owner in owner["source_owners"]:
            if not source_owner.startswith("planned:"):
                assert (REPO_ROOT / source_owner).is_file(), source_owner

    states = contract["interaction_states"]
    state_ids = [state["state_id"] for state in states]
    assert len(state_ids) == len(set(state_ids))
    assert set(state_ids) == EXPECTED_STATE_IDS
    owner_id_set = set(owner_ids)
    assert all(set(state["surface_owner_ids"]) <= owner_id_set for state in states)

    primary_keys = [state["copy"]["primary_key"] for state in states]
    consequence_keys = [state["copy"]["consequence_key"] for state in states]
    assert len(primary_keys) == len(set(primary_keys))
    assert len(consequence_keys) == len(set(consequence_keys))
    for state in states:
        assert state["copy"]["local_consequence"].strip()
        assert state["accessibility"]["accessible_name_key"].strip()
        assert state["accessibility"]["description_key"] == state["copy"]["consequence_key"]
        assert state["accessibility"]["focus_behavior"].strip()
        assert state["accessibility"]["keyboard_behavior"].strip()
        assert state["recovery_action"].strip()
        assert state["telemetry"]["privacy_profile"] == ("conversion-ui-no-enterprise-data-v1")

    state_by_id = _state_map(contract)
    recommendation = state_by_id["schema-conversion.older-esr-recommendation"]
    assert "esr-115" in recommendation["trigger"]
    assert "esr-140" in recommendation["trigger"]
    assert "esr-153.0" in recommendation["trigger"]
    assert recommendation["confirmation"] == {
        "required": False,
        "danger_class": "none",
        "apply_enabled": False,
    }
    assert "will not change" in recommendation["copy"]["local_consequence"]

    preview = state_by_id["schema-conversion.preview-available"]
    blocked = state_by_id["schema-conversion.preview-blocked"]
    confirmation = state_by_id["schema-conversion.confirmation-ready"]
    pending_apply = state_by_id["schema-conversion.apply-in-progress"]
    assert preview["confirmation"]["apply_enabled"] is True
    assert blocked["confirmation"]["apply_enabled"] is False
    assert confirmation["confirmation"] == {
        "required": True,
        "danger_class": "explicit-state-change",
        "apply_enabled": True,
    }
    assert pending_apply["confirmation"]["apply_enabled"] is False
    assert "duplicate" in pending_apply["accessibility"]["keyboard_behavior"]

    inactive = state_by_id["schema-conversion.source-not-active"]
    retirement = state_by_id["schema-conversion.retirement-operator-boundary"]
    assert set(inactive["error_codes"]) == {
        "conversion_profile_not_found",
        "conversion_source_not_active",
    }
    assert retirement["confirmation"]["danger_class"] == "operator-only"
    assert retirement["confirmation"]["apply_enabled"] is False
    assert "Do not convert profiles manually" in retirement["copy"]["local_consequence"]

    locales = contract["locale_owners"]
    locale_codes = [locale["locale"] for locale in locales]
    assert tuple(locale_codes) == ACTIVE_CATALOG_LOCALES
    assert locale_codes[0] == SOURCE_LOCALE
    assert locales[0]["status"] == "english-source-planned"
    assert all(locale["status"] == "human-reviewed-translation-planned" for locale in locales[1:])
    assert all(locale["owner"] == "project-maintainer" for locale in locales)

    help_policy = contract["help_link_policy"]
    assert help_policy["existing_surface_targets"] == DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS
    assert help_policy["inline_copy_may_be_replaced"] is False
    assert help_policy["new_target_authorized"] is False
    assert "local-action-copy-retained" in help_policy["new_link_requirements"]

    lifecycle = _load_json(LIFECYCLE_PATH)
    rows = {row["artifact_id"]: row for row in lifecycle["channels"]}
    assert rows["esr-115.38"]["recommendation_target_line_id"] == "esr-153"
    assert rows["esr-140.13"]["recommendation_target_line_id"] == "esr-153"
    assert rows["esr-115.38"]["retirement_successor_line_id"] == "esr-140"
    assert rows["esr-140.13"]["retirement_successor_line_id"] == "esr-153"

    conversion = _load_json(CONVERSION_PATH)
    manual_codes = {failure["code"] for failure in conversion["failure_semantics"]}
    assert set(contract["error_code_coverage"]["manual_conversion"]) == manual_codes
    state_manual_codes = {
        code
        for state in states
        if state["group"] != "retirement-boundary"
        for code in state["error_codes"]
    }
    assert state_manual_codes == manual_codes

    retirement_contract = _load_json(RETIREMENT_PATH)
    retirement_codes = {failure["code"] for failure in retirement_contract["failure_semantics"]}
    retirement_codes.add(retirement_contract["ownership"]["unupgraded_runtime_behavior"]["code"])
    assert set(contract["error_code_coverage"]["retirement_operator_boundary"]) == (
        retirement_codes
    )
    assert set(retirement["error_codes"]) == retirement_codes

    privacy = contract["privacy_contract"]
    assert privacy["localized_text_sent_to_server"] is False
    assert privacy["raw_values_rendered_from_plan"] is False
    assert {
        "policy_values",
        "policy_presence",
        "policy_ids",
        "json_pointers",
        "dynamic_keys",
        "profile_id",
        "profile_name_or_description",
        "compliance_values_or_notes",
        "plan_or_document_digests",
        "localized_copy",
    } == set(privacy["forbidden_in_urls_or_telemetry"])
    forbidden_telemetry = set(privacy["forbidden_in_urls_or_telemetry"])
    for state in states:
        assert not (set(state["telemetry"]["allowed_fields"]) & forbidden_telemetry)


def test_contract_schema_semantics_dependencies_and_docs_index() -> None:
    contract = _fixture()
    _validator().validate(contract)
    _assert_semantics(contract)

    assert "Status: active contract" in ACTIVE_UI_COPY_PATH.read_text(encoding="utf-8")
    assert contract["classification_inheritance"]["supersedes"] == []
    for path in (
        CONTRACT_PATH,
        FIXTURE_PATH,
        SCHEMA_PATH,
        ACTIVE_UI_COPY_PATH,
        LIFECYCLE_PATH,
        CONVERSION_PATH,
        RETIREMENT_PATH,
    ):
        assert path.is_file()
        assert doc_path_from_index(path.name) == path


@pytest.mark.parametrize(
    "mutation",
    [
        lambda contract: contract["interaction_states"].pop(),
        lambda contract: contract["interaction_states"][0]["copy"].__setitem__(
            "local_consequence", ""
        ),
        lambda contract: contract["interaction_states"][0].pop("accessibility"),
        lambda contract: contract["interaction_states"][0].__setitem__("recovery_action", ""),
        lambda contract: contract["locale_owners"].pop(),
        lambda contract: contract["help_link_policy"]["existing_surface_targets"].pop("library"),
    ],
    ids=(
        "missing-state",
        "missing-local-consequence",
        "missing-accessibility",
        "missing-recovery",
        "missing-locale-owner",
        "missing-help-owner",
    ),
)
def test_schema_rejects_missing_state_safety_locale_and_help_ownership(
    mutation: Callable[[dict[str, Any]], Any],
) -> None:
    contract = copy.deepcopy(_fixture())
    mutation(contract)

    with pytest.raises(ValidationError):
        _validator().validate(contract)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda contract: contract["interaction_states"][0]["surface_owner_ids"].append(
            "unowned-surface"
        ),
        lambda contract: contract["interaction_states"][0]["telemetry"]["allowed_fields"].append(
            "profile_id"
        ),
        lambda contract: contract["interaction_states"][-1]["confirmation"].__setitem__(
            "apply_enabled", True
        ),
    ],
    ids=("unowned-surface", "sensitive-telemetry", "retirement-manual-apply"),
)
def test_semantics_reject_owner_privacy_and_retirement_boundary_drift(
    mutation: Callable[[dict[str, Any]], Any],
) -> None:
    contract = copy.deepcopy(_fixture())
    mutation(contract)

    with pytest.raises(AssertionError):
        _assert_semantics(contract)
