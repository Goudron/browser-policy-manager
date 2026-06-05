from __future__ import annotations

import pytest

from tests.marker_policy import LAYER_MARKERS, markers_for_path


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("tests/api/test_profiles_api.py", {"api"}),
        ("tests/core/test_policy_validation_with_schema.py", {"unit"}),
        ("tests/tools/test_locale_inventory.py", {"unit"}),
        ("tests/test_app_harness_unit.py", {"unit"}),
        ("tests/test_cache_harness_unit.py", {"unit"}),
        ("tests/test_ci_workflow_layers.py", {"unit"}),
        ("tests/test_db_harness_unit.py", {"unit"}),
        ("tests/test_frontend_vendor_rebuild_contract.py", {"unit"}),
        ("tests/test_makefile_test_targets.py", {"unit"}),
        ("tests/test_docs_index.py", {"contract", "docs_contract"}),
        ("tests/test_pytest_app_state_isolation_contract.py", {"contract"}),
        ("tests/test_pytest_db_isolation_contract.py", {"contract"}),
        (
            "tests/test_pytest_xdist_isolation_audit_contract.py",
            {"contract", "docs_contract"},
        ),
        ("tests/test_ui_runtime_i18n_contract.py", {"contract", "ui_contract"}),
        (
            "tests/web_profiles_page/test_assets_i18n_contracts.py",
            {"contract", "ui_contract"},
        ),
        (
            "tests/web_profiles_page/test_route_dom_contracts.py",
            {"contract", "ui_contract", "slow"},
        ),
        ("tests/compliance/test_cis_firefox_mapping_targets.py", {"contract", "slow"}),
        ("tests/test_ui_browser_tabs.py", {"browser_ui", "slow"}),
        ("tests/live_firefox/test_policy_activation.py", {"firefox_live", "slow"}),
        (
            "tests/live_firefox/test_extension_settings_amo.py",
            {"firefox_live", "firefox_live_amo", "slow"},
        ),
    ],
)
def test_marker_policy_assigns_expected_layers(path, expected):
    assert expected <= markers_for_path(path)


def test_marker_policy_only_emits_registered_layer_markers():
    sample_paths = (
        "tests/api/test_profiles_api.py",
        "tests/core/test_policy_validation_with_schema.py",
        "tests/test_docs_index.py",
        "tests/test_ui_runtime_i18n_contract.py",
        "tests/test_ui_browser_tabs.py",
        "tests/live_firefox/test_extension_settings_amo.py",
    )
    emitted = set().union(*(markers_for_path(path) for path in sample_paths))

    assert emitted <= LAYER_MARKERS
