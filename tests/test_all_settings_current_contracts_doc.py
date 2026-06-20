from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = REPO_ROOT / "docs" / "architecture" / "all-settings-current-contracts.md"


def test_all_settings_current_contracts_doc_records_route_dom_and_modules():
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    for snippet in (
        "Backlog item: `BPM088-M2-02`",
        "`GET /profiles/{profile_id}/settings`",
        "`app/templates/profiles/_page_settings_workspace.html`",
        "`#wizard-settings-search-input`",
        "`#all-settings-review-panel`",
        "`#all-settings-list`",
        "`#all-settings-detail-panel`",
        "`#settings-schema-shell-step-{step}`",
        "`#settings-preferences-{id}`",
        "`profiles_all_settings_state.js`",
        "`profiles_all_settings_list.js`",
        "`profiles_all_settings_detail.js`",
        "`profiles_settings_search.js`",
        "`profiles_bootstrap_core.js`",
    ):
        assert snippet in text


def test_all_settings_current_contracts_doc_records_render_data_flow():
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    for snippet in (
        "Create `schemaShell`.",
        "Create `allSettingsRouteState`.",
        "`getAllSettingsSearchEntries: () => allSettingsList.getSearchEntries()`",
        "`findAllSettingsEntryTarget: (target) => allSettingsList.findTarget(target)`",
        "`readWizardSchemaSource()`",
        "`getActiveWizardSchemaVersion()`",
        "`getValidationIssues()`",
        "`wizardSchemaShellCatalog`",
        "`wizardPreferencesCatalog`",
        "`allSettingsCategoryCatalog`",
        "schemaShell.renderWizardSchemaShell()",
        "allSettingsList.render()",
        "settingsSearch.buildIndex()",
        "settingsSearch.renderResults()",
        "workspace.updateActionState()",
    ):
        assert snippet in text
