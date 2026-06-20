from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

from app.core.schema_channels import CURRENT_RELEASE_SCHEMA_CHANNEL
from app.web.firefox_all_settings_categories import get_all_settings_category_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from tests.support import build_corporate_cis_l2_profile_fixture

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def test_all_settings_heavy_fixture_keeps_rendered_rows_bounded():
    fixture = build_corporate_cis_l2_profile_fixture(
        schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL,
    )
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_inventory.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

        const fixture = {json.dumps({
            "schema_version": fixture.schema_version,
            "flags": fixture.flags,
            "compliance": fixture.compliance,
            "configured_count": fixture.configured_policy_count + fixture.configured_preference_count,
        })};
        const allSettingsCategoryCatalog = {json.dumps(get_all_settings_category_catalog())};
        const wizardPreferencesCatalog = {json.dumps(wizard_preferences_catalog)};
        const wizardSchemaShellCatalog = {json.dumps(get_wizard_schema_shell_catalog(wizard_preferences_catalog))};
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_list_value_object": "{{count}} keys",
            "profiles.settings_list_value_array": "{{count}} items",
            "profiles.settings_list_summary": "{{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_summary_filtered": "{{visible}} shown of {{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_empty": "Empty",
            "profiles.settings_list_filtered_empty": "Filtered empty",
            "profiles.settings_list_budget": "Showing {{visible}} of {{total}}.",
            "profiles.settings_list_window": "Showing {{from}}-{{to}} of {{total}}.",
            "profiles.settings_list_show_more": "Show {{count}} more",
            "profiles.settings_list_show_less": "Show fewer",
            "profiles.settings_list_previous_page": "Previous",
            "profiles.settings_list_next_page": "Next",
        }}[key] || key);

        function fakeElement() {{
            return {{
                hidden: false,
                textContent: "",
                innerHTML: "",
                addEventListener: () => {{}},
                querySelectorAll: () => [],
                querySelector: () => null,
            }};
        }}

        function fakeListElement() {{
            let html = "";
            let rows = [];
            return {{
                hidden: false,
                addEventListener: () => {{}},
                get innerHTML() {{
                    return html;
                }},
                set innerHTML(value) {{
                    html = String(value || "");
                    rows = Array.from(html.matchAll(/data-settings-entry-id="([^"]+)"[\\s\\S]*?data-settings-entry-kind="([^"]+)"/g))
                        .map((match) => ({{
                            hidden: false,
                            dataset: {{
                                settingsEntryId: match[1],
                                settingsEntryKind: match[2],
                            }},
                        }}));
                }},
                querySelectorAll: (selector) => selector === "[data-settings-entry-id]" ? rows : [],
                querySelector: () => null,
                renderedRows: () => rows.length,
                visibleRows: () => rows.filter((row) => !row.hidden).length,
            }};
        }}

        function fakeBudgetElement() {{
            let clickHandler = null;
            return {{
                hidden: true,
                innerHTML: "",
                addEventListener: (eventName, handler) => {{
                    if (eventName === "click") clickHandler = handler;
                }},
                currentGroup: function() {{
                    return (this.innerHTML.match(/data-settings-list-budget-toggle="([^"]+)"/) || [])[1] || "";
                }},
                clickAction: function(actionName) {{
                    const groupId = this.currentGroup();
                    clickHandler?.({{
                        target: {{
                            closest: (selector) => selector === "[data-settings-list-budget-toggle]"
                                ? {{
                                    disabled: false,
                                    dataset: {{
                                        settingsListBudgetToggle: groupId,
                                        settingsListBudgetAction: actionName,
                                    }},
                                }}
                                : null,
                        }},
                    }});
                }},
            }};
        }}

        const inventory = window.BPMProfilesSettingsInventory.create({{
            dependencies: {{
                t,
                getActiveWizardSchemaVersion: () => fixture.schema_version,
                getValidationIssues: () => [],
                getComplianceInfo: () => fixture.compliance,
                getManualEdits: () => [],
            }},
            allSettingsCategoryCatalog,
            wizardPreferencesCatalog,
            wizardSchemaShellCatalog,
        }});
        const routeState = window.BPMProfilesAllSettingsState.create({{ activeMode: "catalog" }});
        const listEl = fakeListElement();
        const budgetEl = fakeBudgetElement();
        const list = window.BPMProfilesAllSettingsList.create({{
            documentRef: {{ documentElement: {{ lang: "en" }} }},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsListEl: listEl,
                allSettingsListEmptyEl: fakeElement(),
                allSettingsListBudgetEl: budgetEl,
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                getActiveWizardSchemaVersion: () => fixture.schema_version,
                readWizardSchemaSource: () => ({{ ok: true, data: fixture.flags }}),
                getValidationIssues: () => [],
                getComplianceInfo: () => fixture.compliance,
                getManualEdits: () => [],
                getCurrentLang: () => "en",
                onSelectionChange: () => {{}},
                allSettingsRouteState: routeState,
                settingsInventory: inventory,
            }},
        }});

        list.render();
        const catalogTotal = routeState.getVisibleEntries().length;
        if (catalogTotal < 145) throw new Error(`heavy catalog too small: ${{catalogTotal}}`);
        if (listEl.renderedRows() > 7) throw new Error(`collapsed catalog rendered ${{listEl.renderedRows()}} rows`);
        if (!budgetEl.innerHTML.includes("Show ")) throw new Error("catalog show-more control missing");

        budgetEl.clickAction("expand");
        if (listEl.renderedRows() > 50) throw new Error(`expanded catalog rendered ${{listEl.renderedRows()}} rows`);
        if (!budgetEl.innerHTML.includes("Showing 1-50")) throw new Error("catalog first page range missing");

        budgetEl.clickAction("next");
        if (listEl.renderedRows() > 50) throw new Error(`paged catalog rendered ${{listEl.renderedRows()}} rows`);
        if (!budgetEl.innerHTML.includes("Showing 51-100")) throw new Error("catalog second page range missing");

        routeState.setActiveMode("configured");
        routeState.setActiveFilter("all");
        list.render();
        const configuredTotal = routeState.getVisibleEntries().length;
        const configuredCount = routeState.getSnapshot().counts.configured;
        if (configuredCount !== fixture.configured_count) {{
            throw new Error(`configured count expected ${{fixture.configured_count}} got ${{configuredCount}}`);
        }}
        if (configuredTotal <= 7) throw new Error(`configured domain view is not a long-list probe: ${{configuredTotal}}`);
        if (listEl.renderedRows() > 7) throw new Error(`collapsed configured rendered ${{listEl.renderedRows()}} rows`);
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)
