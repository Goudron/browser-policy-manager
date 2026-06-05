from __future__ import annotations

from pathlib import Path

LAYER_MARKERS = {
    "api",
    "browser_ui",
    "contract",
    "docs_contract",
    "firefox_live",
    "firefox_live_amo",
    "slow",
    "ui_contract",
    "unit",
}

SLOW_TEST_FILES = {
    "tests/compliance/test_cis_firefox_mapping_targets.py",
    "tests/test_e2e_profile_lifecycle.py",
    "tests/test_ui_browser_tabs.py",
    "tests/test_ui_smoke_profile_workflow.py",
    "tests/web_profiles_page/test_route_dom_contracts.py",
}

DOCS_CONTRACT_FILES = {
    "tests/test_docs_index.py",
    "tests/test_pytest_xdist_isolation_audit_contract.py",
    "tests/test_readme_firefox_policies_contract.py",
}

UI_CONTRACT_FILES = {
    "tests/test_all_settings_search_filter_i18n.py",
    "tests/test_browser_datetime_i18n.py",
    "tests/test_chromium_locale_smoke_matrix_contract.py",
    "tests/test_cjk_font_fallback_contract.py",
    "tests/test_de_overflow_layout_contract.py",
    "tests/test_es_es_overflow_layout_contract.py",
    "tests/test_fr_overflow_layout_contract.py",
    "tests/test_locale_picker_layout_contract.py",
    "tests/test_locale_screenshot_pack_contract.py",
    "tests/test_locale_switching_regression_contract.py",
    "tests/test_locale_viewport_overflow_contract.py",
    "tests/test_localized_import_edit_export_workflow_contract.py",
    "tests/test_responsive_long_label_css_contract.py",
    "tests/test_runtime_count_i18n.py",
    "tests/test_ui_locale_glossary.py",
    "tests/test_ui_runtime_i18n_contract.py",
    "tests/test_ui_smoke_profile_workflow.py",
    "tests/test_validation_error_i18n.py",
    "tests/test_web_profiles_page.py",
    "tests/test_zh_cn_script_layout_contract.py",
}


def normalize_test_path(path: str | Path) -> str:
    return Path(path).as_posix()


def markers_for_path(path: str | Path) -> set[str]:
    normalized = normalize_test_path(path)
    filename = Path(normalized).name
    parts = set(Path(normalized).parts)
    markers: set[str] = set()

    if "live_firefox" in parts:
        markers.add("firefox_live")
        if filename == "test_extension_settings_amo.py":
            markers.add("firefox_live_amo")

    if normalized == "tests/test_ui_browser_tabs.py":
        markers.add("browser_ui")

    if normalized in SLOW_TEST_FILES or markers & {"browser_ui", "firefox_live"}:
        markers.add("slow")

    if normalized.startswith("tests/api/") or filename in {
        "test_api.py",
        "test_api_validation_unit.py",
        "test_health_endpoints.py",
        "test_openapi_surface.py",
        "test_profiles_conflict_name_api.py",
        "test_validation_api.py",
    }:
        markers.add("api")

    if normalized in DOCS_CONTRACT_FILES:
        markers.update({"contract", "docs_contract"})

    if normalized in UI_CONTRACT_FILES or normalized.startswith("tests/web_profiles_page/"):
        markers.update({"contract", "ui_contract"})

    if filename.endswith("_contract.py") or normalized.startswith("tests/compliance/"):
        markers.add("contract")

    if (
        filename.endswith("_unit.py")
        or normalized.startswith("tests/core/")
        or normalized.startswith("tests/tools/")
        or filename
        in {
            "test_bootstrap_config.py",
            "test_ci_workflow_layers.py",
            "test_db_helpers.py",
            "test_firefox_settings_catalog_builders.py",
            "test_firefox_starter_presets.py",
            "test_frontend_vendor_rebuild_contract.py",
            "test_live_firefox_harness_unit.py",
            "test_makefile_test_targets.py",
            "test_policy_schema_models.py",
            "test_policy_schema_service.py",
            "test_profile_navigation.py",
            "test_profile_schema_normalization.py",
            "test_pytest_marker_policy.py",
            "test_schema_channels.py",
            "test_workspace_export_links_unit.py",
            "test_yaml_io.py",
        }
    ):
        markers.add("unit")

    return markers
