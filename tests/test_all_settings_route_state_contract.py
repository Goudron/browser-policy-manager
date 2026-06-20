from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def _static_source(filename: str) -> str:
    return (STATIC_ROOT / filename).read_text(encoding="utf-8")


def test_all_settings_route_state_initializes_navigation_state_contract():
    source = _static_source("profiles_all_settings_state.js")

    for snippet in (
        "const DEFAULT_FILTER = \"all\";",
        "const DEFAULT_CATEGORY = \"all\";",
        "const DEFAULT_MODE = \"review\";",
        "const VALID_MODES = new Set([\"review\", \"configured\", \"catalog\"]);",
        "function normalizeMode(mode)",
        "activeCategory: normalizeText(initialState.activeCategory, DEFAULT_CATEGORY)",
        "activeMode: normalizeMode(initialState.activeMode)",
        "activeFilter: normalizeText(initialState.activeFilter, DEFAULT_FILTER)",
        "searchQuery: normalizeText(initialState.searchQuery)",
        "selectedEntryKey: normalizeText(initialState.selectedEntryKey)",
        "focusedTarget: normalizeText(initialState.focusedTarget)",
        "expandedGroups: new Set(uniqueList(initialState.expandedGroups))",
        "function getSnapshot()",
        "function setActiveMode(mode)",
        "window.BPMProfilesAllSettingsState = { create };",
    ):
        assert snippet in source


def test_all_settings_route_state_update_contract_tracks_counts_visibility_and_selection():
    source = _static_source("profiles_all_settings_state.js")

    for snippet in (
        "function updateEntries(entries = [], options = {})",
        "const matchesMode = typeof options.matchesMode === \"function\"",
        "const nextModeEntries = nextEntries.filter((entry) => matchesMode(entry, state.activeMode));",
        "const nextVisibleEntries = nextCategoryEntries.filter((entry) => matchesFilter(entry, state.activeFilter));",
        "state.modeEntries = nextModeEntries;",
        "state.categoryEntries = nextCategoryEntries;",
        "state.visibleEntries = nextVisibleEntries;",
        "state.counts = buildCounts(",
        "filters[filterValue] = visibleEntries.categoryEntries.filter((entry) => matchesFilter(entry, filterValue)).length;",
        "metadata.updateCategory && metadata.categoryId",
        "fallbackVisible && state.activeCategory !== DEFAULT_CATEGORY",
        "function getCategoryEntries()",
        "function getModeEntries()",
        "function getVisibleEntries()",
        "function getSelectedEntry(entries = state.entries, entryKey = defaultEntryKey)",
    ):
        assert snippet in source


def test_all_settings_list_uses_route_state_instead_of_local_navigation_state():
    source = _static_source("profiles_all_settings_list.js")

    for stale_local_state in ("let activeFilter", "let selectedEntryKey", "let lastEntries"):
        assert stale_local_state not in source

    for snippet in (
        "allSettingsRouteState",
        "const routeState = allSettingsRouteState || window.BPMProfilesAllSettingsState.create();",
        "onModeChange,",
        "function setActiveMode(mode, options = {})",
        "onModeChange?.(routeState.getSnapshot().activeMode, options);",
        "routeState.updateEntries(entries, {",
        "matchesMode: entryMatchesMode,",
        "routeState.setActiveFilter(",
        "setActiveMode(\"catalog\", { updateUrl: false });",
        "routeState.setSelectedEntryKey(",
        "routeState.setFocusedTarget(normalizedTarget);",
    ):
        assert snippet in source


def test_all_settings_route_state_runtime_filters_entries_by_mode_and_filter():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));

        const state = window.BPMProfilesAllSettingsState.create({{ activeMode: "bogus" }});
        if (state.getSnapshot().activeMode !== "review") throw new Error("invalid mode fallback");

        const entries = [
            {{ kind: "policy", id: "ReviewOnly", configured: true, attentionFlags: {{ reviewRequired: true }} }},
            {{ kind: "policy", id: "ConfiguredOnly", configured: true, attentionFlags: {{ reviewRequired: false }} }},
            {{ kind: "policy", id: "CatalogOnly", configured: false, attentionFlags: {{ reviewRequired: false }} }},
        ];
        const entryKey = (entry) => `${{entry.kind}}:${{entry.id}}`;
        const matchesMode = (entry, mode) => {{
            if (mode === "review") return Boolean(entry.attentionFlags.reviewRequired);
            if (mode === "configured") return entry.configured;
            return true;
        }};
        const matchesFilter = (entry, filter) => filter === "configured" ? entry.configured : true;
        const matchesCategory = (entry, category, mode) => mode !== "configured" || category === "all" || entry.categoryId === category;
        state.updateEntries(entries, {{
            entryKey,
            filterValues: ["all", "configured"],
            matchesMode,
            matchesCategory,
            matchesFilter,
        }});
        if (state.getModeEntries().length !== 1) throw new Error("review mode entries");
        if (state.getVisibleEntries()[0].id !== "ReviewOnly") throw new Error("review selection");

        state.setActiveMode("configured");
        state.updateEntries(entries, {{
            entryKey,
            filterValues: ["all", "configured"],
            matchesMode,
            matchesCategory,
            matchesFilter,
        }});
        if (state.getSnapshot().counts.mode !== 2) throw new Error("configured mode count");
        if (state.getVisibleEntries().length !== 2) throw new Error("configured visible entries");
        if (state.getSnapshot().activeCategory !== "all") throw new Error("configured mode changed all category");

        state.setSelectedEntryKey("policy:ConfiguredOnly", {{
            categoryId: "browser",
            target: "all-settings-entry:policy:ConfiguredOnly",
        }});
        if (state.getSnapshot().activeCategory !== "all") throw new Error("row selection changed all category");
        if (state.getSnapshot().focusedTarget !== "all-settings-entry:policy:ConfiguredOnly") throw new Error("row target not stored");

        state.setActiveMode("catalog");
        state.setActiveFilter("configured");
        state.updateEntries(entries, {{
            entryKey,
            filterValues: ["all", "configured"],
            matchesMode,
            matchesCategory,
            matchesFilter,
        }});
        if (state.getSnapshot().counts.mode !== 3) throw new Error("catalog mode count");
        if (state.getSnapshot().counts.visible !== 2) throw new Error("catalog filtered count");

        state.setActiveMode("configured");
        state.setActiveCategory("privacy");
        state.setActiveFilter("all");
        entries[0].categoryId = "privacy";
        entries[1].categoryId = "browser";
        entries[2].categoryId = "browser";
        state.updateEntries(entries, {{
            entryKey,
            filterValues: ["all", "configured"],
            matchesMode,
            matchesCategory,
            matchesFilter,
        }});
        if (state.getCategoryEntries().length !== 1) throw new Error("configured category entries");
        if (state.getSnapshot().counts.category !== 1) throw new Error("configured category count");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_all_settings_list_runtime_budgets_long_visible_lists_per_mode():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

        const translations = {{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_value_not_configured": "Not configured",
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
            "profiles.settings_review_summary_attention": "Review: {{count}}",
            "profiles.settings_review_summary_clear": "Clear",
            "profiles.settings_review_open": "Open review",
            "profiles.settings_review_clear": "No items",
            "profiles.settings_review_success_title": "Nothing needs review",
            "profiles.settings_review_success_body": "Nothing to review.",
            "profiles.settings_review_success_configured": "Configured",
            "profiles.settings_review_success_catalog": "Catalog",
            "profiles.settings_review_empty_group": "No entries in this queue.",
            "profiles.settings_review_more": "+{{count}} more",
            "profiles.settings_review_source_manual": "Manual",
            "profiles.settings_review_path": "Path: {{path}}",
            "profiles.settings_review_reason_attention": "Needs review",
            "profiles.settings_review_reason_invalid": "Validation issues: {{count}}",
            "profiles.settings_review_reason_cis_empty": "CIS decision needs review",
            "profiles.settings_review_reason_unknown": "Outside active schema",
            "profiles.settings_review_reason_deprecated": "Deprecated policy",
            "profiles.settings_review_reason_raw": "Raw JSON fallback",
            "profiles.settings_review_cis_title": "CIS",
            "profiles.settings_review_cis_body": "CIS body",
            "profiles.settings_review_unknown_title": "Unknown",
            "profiles.settings_review_unknown_body": "Unknown body",
            "profiles.settings_review_deprecated_title": "Deprecated",
            "profiles.settings_review_deprecated_body": "Deprecated body",
            "profiles.settings_review_raw_title": "Raw",
            "profiles.settings_review_raw_body": "Raw body",
            "profiles.settings_review_invalid_title": "Invalid",
            "profiles.settings_review_invalid_body": "Invalid body",
        }};
        const t = (key) => translations[key] || key;

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
                clickToggle: function() {{
                    const groupId = this.currentGroup();
                    clickHandler?.({{
                        target: {{
                            closest: (selector) => selector === "[data-settings-list-budget-toggle]"
                                ? {{ disabled: false, dataset: {{ settingsListBudgetToggle: groupId }} }}
                                : null,
                        }},
                    }});
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

        let sourceData = {{ fixture: "short" }};
        let currentEntries = Array.from({{ length: 9 }}, (_, index) => ({{
            id: `Policy${{index + 1}}`,
            label: `Policy ${{index + 1}}`,
            kind: "policy",
            categoryId: "browser",
            configured: true,
            invalid: true,
            value: "Configured",
            sources: ["manual"],
            attentionFlags: {{ reviewRequired: true, validationIssueCount: 1 }},
        }}));
        const routeState = window.BPMProfilesAllSettingsState.create();
        const listEl = fakeListElement();
        const budgetEl = fakeBudgetElement();

        const list = window.BPMProfilesAllSettingsList.create({{
            documentRef: {{}},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsReviewSummaryEl: fakeElement(),
                allSettingsReviewActionsEl: fakeElement(),
                allSettingsListEl: listEl,
                allSettingsListEmptyEl: fakeElement(),
                allSettingsListBudgetEl: budgetEl,
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                readWizardSchemaSource: () => ({{ ok: true, data: sourceData }}),
                onSelectionChange: () => {{}},
                allSettingsRouteState: routeState,
                settingsInventory: {{ collect: () => currentEntries }},
            }},
        }});

        list.render();
        if (routeState.getSnapshot().activeMode !== "review") throw new Error("review default mode");
        if (routeState.getVisibleEntries().length !== 9) throw new Error("review full visible count lost");
        if (listEl.visibleRows() !== 7) throw new Error(`review budget rows: ${{listEl.visibleRows()}}`);
        if (budgetEl.hidden) throw new Error("review budget control hidden");
        if (!budgetEl.innerHTML.includes("Showing 7 of 9.")) throw new Error("review budget count missing");
        if (!budgetEl.innerHTML.includes("Show 2 more")) throw new Error("review show-more label missing");

        budgetEl.clickToggle();
        if (listEl.visibleRows() !== 9) throw new Error("review expansion did not show all rows");
        if (!budgetEl.innerHTML.includes("Show fewer")) throw new Error("review collapse label missing");

        routeState.setActiveMode("configured");
        routeState.setActiveFilter("all");
        list.render();
        if (listEl.visibleRows() !== 7) throw new Error("configured mode inherited review expansion");
        if (!budgetEl.innerHTML.includes("Showing 7 of 9.")) throw new Error("configured budget count missing");

        routeState.setActiveMode("catalog");
        routeState.setActiveFilter("all");
        list.render();
        if (listEl.visibleRows() !== 7) throw new Error("catalog mode did not budget rows");
        if (!budgetEl.innerHTML.includes("Show 2 more")) throw new Error("catalog show-more label missing");

        sourceData = {{ fixture: "large" }};
        currentEntries = Array.from({{ length: 120 }}, (_, index) => ({{
            id: `CatalogPolicy${{index + 1}}`,
            label: `Catalog policy ${{index + 1}}`,
            kind: "policy",
            categoryId: "browser",
            configured: false,
            value: "Not configured",
            sources: ["catalog"],
            attentionFlags: {{ reviewRequired: false }},
        }}));
        routeState.setActiveMode("catalog");
        routeState.setActiveFilter("all");
        list.render();
        if (routeState.getVisibleEntries().length !== 120) throw new Error("catalog route state lost full inventory");
        if (listEl.renderedRows() !== 7) throw new Error(`catalog collapsed DOM rows: ${{listEl.renderedRows()}}`);
        if (!budgetEl.innerHTML.includes("Show 113 more")) throw new Error("catalog large show-more label missing");

        budgetEl.clickAction("expand");
        if (listEl.renderedRows() !== 50) throw new Error(`catalog expanded DOM rows: ${{listEl.renderedRows()}}`);
        if (!budgetEl.innerHTML.includes("Showing 1-50 of 120.")) throw new Error("catalog first page range missing");
        if (!budgetEl.innerHTML.includes("Next")) throw new Error("catalog next page missing");

        budgetEl.clickAction("next");
        if (listEl.renderedRows() !== 50) throw new Error("catalog next page DOM window changed size");
        if (!budgetEl.innerHTML.includes("Showing 51-100 of 120.")) throw new Error("catalog second page range missing");
        if (!budgetEl.innerHTML.includes("Previous")) throw new Error("catalog previous page missing");

        budgetEl.clickAction("next");
        if (listEl.renderedRows() !== 20) throw new Error(`catalog last page DOM rows: ${{listEl.renderedRows()}}`);
        if (!budgetEl.innerHTML.includes("Showing 101-120 of 120.")) throw new Error("catalog last page range missing");
        if (budgetEl.innerHTML.includes("Next</button>")) throw new Error("catalog last page still exposes next");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_all_settings_list_runtime_caches_inventory_until_source_dependencies_change():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

        const translations = {{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_list_summary": "{{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_summary_filtered": "{{visible}} shown of {{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_empty": "Empty",
            "profiles.settings_list_filtered_empty": "Filtered empty",
            "profiles.settings_review_reason_invalid": "Validation issues: {{count}}",
        }};
        const t = (key) => translations[key] || key;

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

        let sourceData = {{ DisableTelemetry: true }};
        let schemaVersion = "release-152";
        let validationIssues = [];
        let currentLang = "en";
        let complianceInfo = {{ decisions: [] }};
        let manualEdits = [];
        let collectCalls = 0;
        const routeState = window.BPMProfilesAllSettingsState.create();

        const list = window.BPMProfilesAllSettingsList.create({{
            documentRef: {{ documentElement: {{ lang: currentLang }} }},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsListEl: fakeElement(),
                allSettingsListEmptyEl: fakeElement(),
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                getActiveWizardSchemaVersion: () => schemaVersion,
                readWizardSchemaSource: () => ({{ ok: true, data: sourceData }}),
                getValidationIssues: () => validationIssues,
                getComplianceInfo: () => complianceInfo,
                getManualEdits: () => manualEdits,
                getCurrentLang: () => currentLang,
                onSelectionChange: () => {{}},
                allSettingsRouteState: routeState,
                settingsInventory: {{
                    collect: () => {{
                        collectCalls += 1;
                        return [{{
                            id: "DisableTelemetry",
                            label: "DisableTelemetry",
                            kind: "policy",
                            categoryId: "privacy",
                            configured: true,
                            invalid: true,
                            value: "true",
                            sources: ["manual"],
                            attentionFlags: {{ reviewRequired: true, validationIssueCount: validationIssues.length }},
                        }}];
                    }},
                }},
            }},
        }});

        function renderAndExpect(expected, label) {{
            list.render();
            if (collectCalls !== expected) {{
                throw new Error(`${{label}} expected ${{expected}} collect calls, got ${{collectCalls}}`);
            }}
        }}

        renderAndExpect(1, "initial render");
        renderAndExpect(1, "same render");
        routeState.setActiveMode("catalog");
        renderAndExpect(1, "mode change");
        routeState.setActiveFilter("configured");
        renderAndExpect(1, "filter change");

        sourceData = {{ DisableTelemetry: false }};
        renderAndExpect(2, "source data change");
        schemaVersion = "esr-140";
        renderAndExpect(3, "schema change");
        validationIssues = [{{ policy: "DisableTelemetry", path: ["DisableTelemetry"], message: "bad" }}];
        renderAndExpect(4, "validation change");
        currentLang = "ru";
        renderAndExpect(5, "locale change");
        complianceInfo = {{ decisions: [{{ path: ["DisableTelemetry"], decision: "added_from_cis" }}] }};
        renderAndExpect(6, "CIS metadata change");
        manualEdits = [{{ path: ["DisableTelemetry"], operation: "set" }}];
        renderAndExpect(7, "manual edits change");
        renderAndExpect(7, "stable final render");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)
