from __future__ import annotations

from pathlib import Path

from tests.web_profiles_page_helpers import static_source

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_all_settings_search_grouping_contract_is_wired():
    search_source = static_source("profiles_settings_search.js")
    css_source = static_source("profiles_css/21-settings.css")
    template_source = (
        REPO_ROOT / "app/templates/profiles/_page_settings_workspace.html"
    ).read_text(encoding="utf-8")
    dom_source = static_source("profiles_dom.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")

    for snippet in (
        'searchGroup = "actions"',
        "searchScopes = []",
        "function matchesSearchScope(entry, scope)",
        "function syncScopeButtons()",
        'activeSearchScope = button.dataset.settingsSearchScope || "all"',
        "function resolveAllSettingsEntryTarget(targetKey)",
        "const entryTarget = resolveAllSettingsEntryTarget(normalizedTarget);",
        "findAllSettingsEntryTarget?.(entryTarget)",
        "[data-settings-detail-primary-focus], .all-settings-detail-editor [data-schema-policy-field]",
        'searchGroup: entry.kind === "preference"',
        "function dedupeTargets(matches)",
        "function allSettingsSearchGroups()",
        "function renderGroupedResults(matches)",
        "function firstResultButton()",
        "function activateSearchResult(button)",
        "profiles.settings_search_group_configured",
        "profiles.settings_search_group_available_policies",
        "profiles.settings_search_group_preferences",
        "profiles.settings_search_group_actions",
        "dataset.settingsSearchGroup = group.id",
        "scope: activeSearchScope",
        "dedupeTargets: isAllSettingsRoute",
        "export { create };",
    ):
        assert snippet in search_source

    for snippet in (
        ".wizard-settings-search-group",
        ".wizard-settings-search-group-title",
        ".wizard-settings-search-scope",
        ".wizard-settings-search-scope-button",
    ):
        assert snippet in css_source

    assert 'wizardSettingsSearchScopeEl: byId("wizard-settings-search-scope")' in dom_source
    assert 'wizardSettingsSearchScopeButtons: all("[data-settings-search-scope]")' in dom_source
    assert "wizardSettingsSearchScopeEl," in bootstrap_source
    assert "wizardSettingsSearchScopeButtons," in bootstrap_source
    assert "profiles.settings_search_scope_review" in template_source
