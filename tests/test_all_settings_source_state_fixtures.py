from __future__ import annotations

from typing import Any

import pytest

from app.core.schema_channels import CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from tests.support import (
    AllSettingsSourceStateFixture,
    build_all_settings_inventory_counts,
    build_all_settings_source_state_regression_fixtures,
)

EXPECTED_SOURCE_STATE_CASES = {
    "baseline-only",
    "cis-added",
    "cis-replaced",
    "manual-review",
    "imported-unknown-policy",
    "imported-unknown-preference",
    "raw-fallback-policy",
    "manually-edited-setting",
}


def _get_path_value(source: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = source
    for part in path:
        value = value[part]
    return value


def _decision_by_path(fixture: AllSettingsSourceStateFixture) -> dict[tuple[str, ...], dict[str, Any]]:
    return {
        tuple(decision["path"]): decision
        for decision in fixture.compliance.get("decisions", [])
        if isinstance(decision, dict) and isinstance(decision.get("path"), list)
    }


@pytest.mark.parametrize("schema_version", (CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL))
def test_all_settings_source_state_regression_fixtures_cover_required_cases(schema_version):
    fixtures = build_all_settings_source_state_regression_fixtures(schema_version=schema_version)

    assert {fixture.id for fixture in fixtures} == EXPECTED_SOURCE_STATE_CASES
    assert all(fixture.schema_version == schema_version for fixture in fixtures)
    assert all(fixture.payload["schema_version"] == schema_version for fixture in fixtures)
    assert all(fixture.payload["flags"] == fixture.flags for fixture in fixtures)
    assert all(fixture.payload.get("compliance", {}) == fixture.compliance for fixture in fixtures)


def test_all_settings_source_state_regression_fixtures_include_cis_decision_states():
    fixtures = {
        fixture.id: fixture
        for fixture in build_all_settings_source_state_regression_fixtures(
            schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL
        )
    }

    expected_decisions = {
        "baseline-only": "kept_base_only",
        "cis-added": "added_from_cis",
        "cis-replaced": "cis_replaced_base",
        "manual-review": "manual_review_kept_base",
    }
    for case_id, expected_decision in expected_decisions.items():
        fixture = fixtures[case_id]
        expectation = fixture.expectation
        decision = _decision_by_path(fixture)[expectation.path]
        assert expectation.decision == expected_decision
        assert decision["decision"] == expected_decision
        assert decision["path"] == list(expectation.path)

    assert fixtures["manual-review"].expectation.review_required is True
    assert _decision_by_path(fixtures["manual-review"])[("Proxy", "Mode")]["review_required"] is True
    assert fixtures["cis-replaced"].compliance["summary"]["cis_replaced_base"] == 1
    assert fixtures["cis-replaced"].flags["BlockAboutConfig"] is True


def test_all_settings_source_state_regression_fixtures_track_imported_unknown_entries():
    fixtures = {
        fixture.id: fixture
        for fixture in build_all_settings_source_state_regression_fixtures(
            schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL
        )
    }

    unknown_policy = fixtures["imported-unknown-policy"]
    unknown_policy_counts = build_all_settings_inventory_counts(
        schema_version=unknown_policy.schema_version,
        flags=unknown_policy.flags,
    )
    assert unknown_policy.expectation.imported_unknown is True
    assert unknown_policy.expectation.expected_sources == ("imported", "unknown")
    assert unknown_policy_counts.unknown_policy_entries == 1

    unknown_preference = fixtures["imported-unknown-preference"]
    unknown_preference_counts = build_all_settings_inventory_counts(
        schema_version=unknown_preference.schema_version,
        flags=unknown_preference.flags,
    )
    assert unknown_preference.expectation.imported_unknown is True
    assert unknown_preference.expectation.kind == "preference"
    assert unknown_preference_counts.imported_preference_entries == 1


def test_all_settings_source_state_regression_fixtures_track_raw_fallback_policy():
    fixture = {
        fixture.id: fixture
        for fixture in build_all_settings_source_state_regression_fixtures(
            schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL
        )
    }["raw-fallback-policy"]
    shell_catalog = get_wizard_schema_shell_catalog(get_wizard_preferences_catalog())
    raw_ids = {
        item["id"]
        for step in shell_catalog["steps"]
        for item in shell_catalog["channels"][CURRENT_RELEASE_SCHEMA_CHANNEL]["steps"][
            str(step["step"])
        ].get("raw_fallback", [])
    }

    assert fixture.expectation.raw_fallback is True
    assert fixture.expectation.entry_id in raw_ids
    assert fixture.expectation.entry_id in fixture.flags


def test_all_settings_source_state_regression_fixtures_track_manual_edit_state():
    fixture = {
        fixture.id: fixture
        for fixture in build_all_settings_source_state_regression_fixtures(
            schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL
        )
    }["manually-edited-setting"]
    edit = fixture.manual_edits[0]

    assert fixture.expectation.manually_edited is True
    assert fixture.expectation.expected_sources == ("manual", "baseline", "cis")
    assert edit.path == fixture.expectation.path
    assert edit.previous_value is True
    assert edit.current_value is False
    assert _get_path_value(fixture.flags, edit.path) == edit.current_value
