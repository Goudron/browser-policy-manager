from __future__ import annotations

from tests.web_profiles_page_helpers import static_source


def test_all_settings_detail_primary_editor_contract_is_wired():
    detail_source = static_source("profiles_all_settings_detail.js")
    list_source = static_source("profiles_all_settings_list.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")
    runtime_source = static_source("profiles_runtime.js")

    for snippet in (
        "function renderEntryMetadata(entry, extraRows = [])",
        "function sourceSummary(entry)",
        "function locationSummary(entry)",
        "onDocumentChange(normalized);",
        "data-settings-detail-primary-focus",
        "data-settings-detail-${escapeHtml(key)}",
        "profiles.settings_detail_meta_source",
        "profiles.settings_detail_meta_location",
        "renderEntryMetadata(entry)",
        "data-settings-detail-reset",
        "data-settings-detail-remove",
        "data-settings-detail-apply-raw",
        "data-settings-detail-apply-preference",
        'getAllSettingsMode = () => "review"',
        'getAllSettingsMode() === "catalog"',
        "export { create };",
    ):
        assert snippet in detail_source

    assert "routeState.setSelectedEntryKey(entryKey(" in list_source
    assert "function revealTargetForSelectedRow(row)" in list_source
    assert 'documentRef.getElementById("all-settings-detail-panel") || row' in list_source
    assert "onSelectionChange: (entry) => allSettingsDetail.render(entry)" in bootstrap_source
    assert (
        "findAllSettingsEntryTarget: (target) => allSettingsList.findTarget(target)"
        in bootstrap_source
    )
    assert (
        "onDocumentChange: (...args) => handleAllSettingsDocumentChange(...args)"
        in bootstrap_source
    )
    assert (
        "getAllSettingsMode: () => allSettingsRouteState.getSnapshot().activeMode"
        in bootstrap_source
    )
    assert (
        "[data-settings-detail-primary-focus], .all-settings-detail-editor "
        "[data-schema-policy-field]" in runtime_source
    )
