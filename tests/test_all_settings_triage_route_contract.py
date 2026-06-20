from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.schema_channels import CURRENT_RELEASE_SCHEMA_CHANNEL
from app.main import app
from app.web.firefox_all_settings_categories import get_all_settings_category_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from tests.support import (
    build_corporate_cis_l2_profile_fixture,
    build_profile_payload,
    make_test_client,
)
from tests.web_profiles_page_helpers import static_source, template_source

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def test_all_settings_route_renders_triage_mode_controls_inside_current_surface():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="All Settings Triage Contract"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/settings")
    soup = BeautifulSoup(response.text, "html.parser")

    assert response.status_code == 200
    assert soup.select_one("#settings-panel")
    assert soup.select_one("#all-settings-review-panel")
    assert soup.select_one("#all-settings-list-panel")
    assert soup.select_one("#all-settings-detail-panel")

    mode_bar = soup.select_one("[data-settings-mode-bar]")
    assert mode_bar is not None
    assert mode_bar.get("role") == "group"

    mode_buttons = mode_bar.select("[data-settings-mode]")
    assert [button["data-settings-mode"] for button in mode_buttons] == [
        "review",
        "configured",
        "catalog",
    ]
    assert mode_buttons[0].get("aria-pressed") == "true"
    assert [button.get("aria-pressed") for button in mode_buttons[1:]] == ["false", "false"]

    rendered_links = [
        link.get("href", "")
        for link in soup.select("a[href]")
        if "/settings" in link.get("href", "")
    ]
    assert all("/settings/review" not in href for href in rendered_links)
    assert all("/settings/configured" not in href for href in rendered_links)
    assert all("/settings/catalog" not in href for href in rendered_links)


def test_all_settings_triage_mode_contract_is_backed_by_state_and_bootstrap():
    settings_template = template_source("_page_settings_workspace.html")
    state_source = static_source("profiles_all_settings_state.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")
    list_source = static_source("profiles_all_settings_list.js")

    for snippet in (
        "data-settings-mode-bar",
        '("review", "profiles.settings_mode_review", "profiles.settings_mode_review_body")',
        '("configured", "profiles.settings_mode_configured", "profiles.settings_mode_configured_body")',
        '("catalog", "profiles.settings_mode_catalog", "profiles.settings_mode_catalog_body")',
    ):
        assert snippet in settings_template

    for snippet in (
        'const DEFAULT_MODE = "review";',
        "activeMode: normalizeMode(initialState.activeMode)",
        "function setActiveMode(mode)",
        "setActiveMode,",
    ):
        assert snippet in state_source

    for snippet in (
        "function readAllSettingsModeFromUrl()",
        "function replaceAllSettingsModeUrl(mode)",
        'params.set("settingsMode", mode);',
        'params.delete("settingsMode");',
        'documentRef.querySelectorAll("[data-settings-mode]")',
        "function syncAllSettingsModeButtons()",
        "reviewPanel.hidden = activeMode !== \"review\";",
        "allSettingsCatalogAdvancedEl,",
        "allSettingsCatalogAdvancedEl.hidden = activeMode !== \"catalog\" && !focusOpen;",
        "allSettingsRouteState.setActiveMode(button.dataset.settingsMode || \"review\");",
        "allSettingsRouteState.setActiveFilter(\"all\");",
        "onModeChange: (mode, options = {}) => {",
        "if (options.updateUrl) {",
        "allSettingsList?.render?.();",
        "syncAllSettingsModeButtons();",
    ):
        assert snippet in bootstrap_source

    for snippet in (
        "entryMatchesReview(entry, reviewKind)",
        "reviewKind === \"cis-review\"",
        "profiles.settings_review_cis_title",
        "profiles.settings_review_cis_body",
        "function renderReviewQueue(item)",
        "function renderReviewSuccessState()",
        "data-settings-review-mode=\"configured\"",
        "data-settings-review-mode=\"catalog\"",
        "reviewSourceLabel(entry)",
        "reviewReasonLabel(entry, reviewKind)",
        "entryNeedsReview(entry)",
    ):
        assert snippet in list_source


def test_all_settings_review_mode_runtime_shows_attention_entries_first():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

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

        const routeState = window.BPMProfilesAllSettingsState.create();
        const reviewSummary = fakeElement();
        const reviewActions = fakeElement();
        const listEl = fakeElement();
        const emptyEl = fakeElement();
        let selected = null;
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_kind": "Kind",
            "profiles.settings_list_column_category": "Category",
            "profiles.settings_list_column_state": "State",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_summary": "{{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_summary_filtered": "{{visible}} shown of {{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_empty": "Empty",
            "profiles.settings_list_filtered_empty": "Filtered empty",
            "profiles.settings_review_summary_attention": "Review: {{count}}",
            "profiles.settings_review_summary_clear": "Clear",
            "profiles.settings_review_open": "Open",
            "profiles.settings_review_clear": "No items",
            "profiles.settings_review_success_title": "Nothing needs review",
            "profiles.settings_review_success_body": "No review work.",
            "profiles.settings_review_success_configured": "View configured",
            "profiles.settings_review_success_catalog": "Browse catalog",
            "profiles.settings_review_empty_group": "No entries in this queue.",
            "profiles.settings_review_more": "+{{count}} more",
            "profiles.settings_review_source_cis": "CIS",
            "profiles.settings_review_source_baseline": "Baseline",
            "profiles.settings_review_source_manual": "Manual",
            "profiles.settings_review_source_imported": "Imported",
            "profiles.settings_review_source_unknown": "Unknown",
            "profiles.settings_review_source_raw": "Raw",
            "profiles.settings_review_source_catalog": "Catalog",
            "profiles.settings_review_path": "Path: {{path}}",
            "profiles.settings_review_reason_attention": "Needs review",
            "profiles.settings_review_reason_cis_manual": "CIS {{ids}}: {{reason}}",
            "profiles.settings_review_reason_cis_manual_no_ids": "CIS manual review: {{reason}}",
            "profiles.settings_review_reason_cis": "CIS recommendations: {{ids}}",
            "profiles.settings_review_reason_cis_empty": "CIS decision needs review",
            "profiles.settings_review_reason_invalid": "Validation issues: {{count}}",
            "profiles.settings_review_reason_unknown": "Outside active schema",
            "profiles.settings_review_reason_deprecated": "Deprecated policy",
            "profiles.settings_review_reason_raw": "Raw JSON fallback",
            "profiles.settings_review_cis_title": "CIS manual review",
            "profiles.settings_review_cis_body": "CIS decisions need review.",
            "profiles.settings_review_unknown_title": "Unknown",
            "profiles.settings_review_unknown_body": "Unknown body",
            "profiles.settings_review_deprecated_title": "Deprecated",
            "profiles.settings_review_deprecated_body": "Deprecated body",
            "profiles.settings_review_raw_title": "Raw",
            "profiles.settings_review_raw_body": "Raw body",
            "profiles.settings_review_invalid_title": "Invalid",
            "profiles.settings_review_invalid_body": "Invalid body",
        }}[key] || key);

        const entries = [
            {{
                id: "Proxy",
                label: "Proxy",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "browser-access",
                categoryLabel: "Browser",
                configured: true,
                value: "system",
                sources: ["baseline", "cis"],
                sourceDetails: {{
                    recommendationIds: ["1.2.3"],
                    decisions: [{{
                        path: ["Proxy", "Mode"],
                        recommendation_ids: ["1.2.3"],
                        review_required: true,
                        reason: "Proxy mode is environment-specific.",
                    }}],
                }},
                attentionFlags: {{ reviewRequired: true, cisReviewRequired: true }},
            }},
            {{
                id: "RawPolicy",
                label: "RawPolicy",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "raw-unmapped",
                categoryLabel: "Raw",
                configured: true,
                rawFallback: true,
                value: "{{}}",
                sources: ["raw-fallback"],
                attentionFlags: {{ reviewRequired: true }},
            }},
            {{
                id: "AvailableOnly",
                label: "AvailableOnly",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "browser-access",
                categoryLabel: "Browser",
                configured: false,
                value: "Not configured",
                attentionFlags: {{ reviewRequired: false }},
            }},
            {{
                id: "AvailableRaw",
                label: "AvailableRaw",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "raw-unmapped",
                categoryLabel: "Raw",
                configured: false,
                rawFallback: true,
                value: "Not configured",
                sources: ["catalog", "raw-fallback"],
                attentionFlags: {{ reviewRequired: true, rawFallback: true }},
            }},
            {{
                id: "AvailableDeprecated",
                label: "AvailableDeprecated",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "raw-unmapped",
                categoryLabel: "Raw",
                configured: false,
                deprecated: true,
                value: "Not configured",
                sources: ["catalog"],
                attentionFlags: {{ reviewRequired: true, deprecated: true }},
            }},
            {{
                id: "AvailableInvalid",
                label: "AvailableInvalid",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "raw-unmapped",
                categoryLabel: "Raw",
                configured: false,
                invalid: true,
                value: "Not configured",
                sources: ["catalog"],
                attentionFlags: {{ reviewRequired: true, invalid: true }},
            }},
        ];

        const list = window.BPMProfilesAllSettingsList.create({{
            documentRef: {{}},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsReviewSummaryEl: reviewSummary,
                allSettingsReviewActionsEl: reviewActions,
                allSettingsListEl: listEl,
                allSettingsListEmptyEl: emptyEl,
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                readWizardSchemaSource: () => ({{ ok: true, data: {{}} }}),
                onSelectionChange: (entry) => {{ selected = entry; }},
                allSettingsRouteState: routeState,
                settingsInventory: {{ collect: () => entries }},
            }},
        }});

        list.render();
        if (routeState.getSnapshot().activeMode !== "review") throw new Error("review mode default");
        if (routeState.getVisibleEntries().length !== 2) throw new Error("review visible entries");
        if (routeState.getVisibleEntries().some((entry) => !entry.configured)) throw new Error("available leaked into review");
        if (selected?.id !== "Proxy") throw new Error("first attention entry selected");
        if (!reviewSummary.textContent.includes("2")) throw new Error("review summary count");
        if (!reviewActions.innerHTML.includes('data-settings-review-filter="cis-review"')) throw new Error("CIS review card");
        if (!reviewActions.innerHTML.includes('data-settings-review-count="1"')) throw new Error("CIS review count");
        if (!reviewActions.innerHTML.includes('data-settings-review-queue="cis-review"')) throw new Error("CIS review queue");
        if (!reviewActions.innerHTML.includes('data-settings-review-entry="cis-review:Proxy"')) throw new Error("CIS review entry");
        if (!reviewActions.innerHTML.includes("Path: Proxy.Mode")) throw new Error("CIS review path");
        if (!reviewActions.innerHTML.includes("CIS 1.2.3: Proxy mode is environment-specific.")) throw new Error("CIS review reason");
        if (!reviewActions.innerHTML.includes('all-settings-review-card-pill">CIS</span>')) throw new Error("CIS review source");
        if (!reviewActions.innerHTML.includes('data-settings-review-queue="raw"')) throw new Error("raw review queue");
        if (!reviewActions.innerHTML.includes("Raw JSON fallback")) throw new Error("raw review reason");
        if (reviewActions.innerHTML.includes('data-settings-review-entry="raw:AvailableRaw"')) throw new Error("available raw leaked into review queue");
        if (reviewActions.innerHTML.includes('data-settings-review-entry="deprecated:AvailableDeprecated"')) throw new Error("available deprecated leaked into review queue");
        if (reviewActions.innerHTML.includes('data-settings-review-entry="invalid:AvailableInvalid"')) throw new Error("available invalid leaked into review queue");
        if (!reviewActions.innerHTML.includes("No entries in this queue.")) throw new Error("empty review queue");

        routeState.setActiveMode("catalog");
        routeState.setActiveFilter("all");
        list.render();
        if (routeState.getVisibleEntries().length !== entries.length) throw new Error("catalog did not show full inventory");
        if (!routeState.getVisibleEntries().some((entry) => entry.id === "AvailableRaw")) throw new Error("catalog missing available raw");
        if (!routeState.getVisibleEntries().some((entry) => entry.id === "AvailableDeprecated")) throw new Error("catalog missing available deprecated");
        if (!routeState.getVisibleEntries().some((entry) => entry.id === "AvailableInvalid")) throw new Error("catalog missing available invalid");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_all_settings_review_mode_runtime_shows_clean_success_state_actions():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        global.Element = class {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

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

        const routeState = window.BPMProfilesAllSettingsState.create();
        const reviewSummary = fakeElement();
        const reviewActions = fakeElement();
        let reviewClick = null;
        reviewActions.addEventListener = (eventName, handler) => {{
            if (eventName === "click") reviewClick = handler;
        }};
        let modeChanges = [];
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_kind": "Kind",
            "profiles.settings_list_column_category": "Category",
            "profiles.settings_list_column_state": "State",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_summary": "{{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_summary_filtered": "{{visible}} shown of {{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_empty": "Empty",
            "profiles.settings_list_filtered_empty": "Filtered empty",
            "profiles.settings_review_summary_attention": "Review: {{count}}",
            "profiles.settings_review_summary_clear": "Clear",
            "profiles.settings_review_open": "Open",
            "profiles.settings_review_clear": "No items",
            "profiles.settings_review_success_title": "Nothing needs review",
            "profiles.settings_review_success_body": "No review work.",
            "profiles.settings_review_success_configured": "View configured",
            "profiles.settings_review_success_catalog": "Browse catalog",
            "profiles.settings_review_empty_group": "No entries in this queue.",
            "profiles.settings_review_more": "+{{count}} more",
            "profiles.settings_review_source_cis": "CIS",
            "profiles.settings_review_source_baseline": "Baseline",
            "profiles.settings_review_source_manual": "Manual",
            "profiles.settings_review_source_imported": "Imported",
            "profiles.settings_review_source_unknown": "Unknown",
            "profiles.settings_review_source_raw": "Raw",
            "profiles.settings_review_source_catalog": "Catalog",
            "profiles.settings_review_path": "Path: {{path}}",
            "profiles.settings_review_reason_attention": "Needs review",
            "profiles.settings_review_reason_cis_manual": "CIS {{ids}}: {{reason}}",
            "profiles.settings_review_reason_cis_manual_no_ids": "CIS manual review: {{reason}}",
            "profiles.settings_review_reason_cis": "CIS recommendations: {{ids}}",
            "profiles.settings_review_reason_cis_empty": "CIS decision needs review",
            "profiles.settings_review_reason_invalid": "Validation issues: {{count}}",
            "profiles.settings_review_reason_unknown": "Outside active schema",
            "profiles.settings_review_reason_deprecated": "Deprecated policy",
            "profiles.settings_review_reason_raw": "Raw JSON fallback",
            "profiles.settings_review_cis_title": "CIS manual review",
            "profiles.settings_review_cis_body": "CIS decisions need review.",
            "profiles.settings_review_unknown_title": "Unknown",
            "profiles.settings_review_unknown_body": "Unknown body",
            "profiles.settings_review_deprecated_title": "Deprecated",
            "profiles.settings_review_deprecated_body": "Deprecated body",
            "profiles.settings_review_raw_title": "Raw",
            "profiles.settings_review_raw_body": "Raw body",
            "profiles.settings_review_invalid_title": "Invalid",
            "profiles.settings_review_invalid_body": "Invalid body",
        }}[key] || key);

        const entries = [
            {{
                id: "DisableTelemetry",
                label: "DisableTelemetry",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "privacy",
                categoryLabel: "Privacy",
                configured: true,
                value: "true",
                attentionFlags: {{ reviewRequired: false }},
            }},
            {{
                id: "AvailableOnly",
                label: "AvailableOnly",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "browser-access",
                categoryLabel: "Browser",
                configured: false,
                value: "Not configured",
                attentionFlags: {{ reviewRequired: false }},
            }},
        ];

        window.BPMProfilesAllSettingsList.create({{
            documentRef: {{}},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsReviewSummaryEl: reviewSummary,
                allSettingsReviewActionsEl: reviewActions,
                allSettingsListEl: fakeElement(),
                allSettingsListEmptyEl: fakeElement(),
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                readWizardSchemaSource: () => ({{ ok: true, data: {{}} }}),
                onSelectionChange: () => {{}},
                onModeChange: (mode, options) => modeChanges.push([mode, options.updateUrl]),
                allSettingsRouteState: routeState,
                settingsInventory: {{ collect: () => entries }},
            }},
        }}).render();

        if (routeState.getSnapshot().activeMode !== "review") throw new Error("review mode default");
        if (routeState.getVisibleEntries().length !== 0) throw new Error("clean review visible entries");
        if (reviewSummary.textContent !== "Clear") throw new Error("clean review summary");
        if (!reviewActions.innerHTML.includes("Nothing needs review")) throw new Error("success title");
        if (!reviewActions.innerHTML.includes('data-settings-review-empty-state')) throw new Error("success state marker");
        if (!reviewActions.innerHTML.includes('data-settings-review-mode="configured"')) throw new Error("configured action");
        if (!reviewActions.innerHTML.includes('data-settings-review-mode="catalog"')) throw new Error("catalog action");
        if (reviewActions.innerHTML.includes('data-settings-review-filter="cis-review"')) throw new Error("review queues rendered for clean state");

        class ModeAction extends Element {{
            constructor(mode) {{
                super();
                this.disabled = false;
                this.dataset = {{ settingsReviewMode: mode }};
            }}
            closest(selector) {{
                return selector === "[data-settings-review-mode]" ? this : null;
            }}
        }}
        reviewClick({{ target: new ModeAction("configured") }});
        if (routeState.getSnapshot().activeMode !== "configured") throw new Error("configured action did not switch mode");
        if (modeChanges.at(-1)?.[0] !== "configured" || modeChanges.at(-1)?.[1] !== true) throw new Error("configured action did not request URL update");

        reviewClick({{ target: new ModeAction("catalog") }});
        if (routeState.getSnapshot().activeMode !== "catalog") throw new Error("catalog action did not switch mode");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_all_settings_review_mode_runtime_groups_invalid_entries():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        global.Element = class {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

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

        const routeState = window.BPMProfilesAllSettingsState.create();
        const reviewActions = fakeElement();
        const listEl = fakeElement();
        let reviewClick = null;
        let selected = null;
        reviewActions.addEventListener = (eventName, handler) => {{
            if (eventName === "click") reviewClick = handler;
        }};
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_kind": "Kind",
            "profiles.settings_list_column_category": "Category",
            "profiles.settings_list_column_state": "State",
            "profiles.settings_list_column_value": "Value",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_summary": "{{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_summary_filtered": "{{visible}} shown of {{total}} entries / {{configured}} configured / {{policies}} policies / {{preferences}} preferences",
            "profiles.settings_list_empty": "Empty",
            "profiles.settings_list_filtered_empty": "Filtered empty",
            "profiles.settings_review_summary_attention": "Review: {{count}}",
            "profiles.settings_review_summary_clear": "Clear",
            "profiles.settings_review_open": "Open",
            "profiles.settings_review_clear": "No items",
            "profiles.settings_review_success_title": "Nothing needs review",
            "profiles.settings_review_success_body": "No review work.",
            "profiles.settings_review_success_configured": "View configured",
            "profiles.settings_review_success_catalog": "Browse catalog",
            "profiles.settings_review_empty_group": "No entries in this queue.",
            "profiles.settings_review_more": "+{{count}} more",
            "profiles.settings_review_source_cis": "CIS",
            "profiles.settings_review_source_baseline": "Baseline",
            "profiles.settings_review_source_manual": "Manual",
            "profiles.settings_review_source_imported": "Imported",
            "profiles.settings_review_source_unknown": "Unknown",
            "profiles.settings_review_source_raw": "Raw",
            "profiles.settings_review_source_catalog": "Catalog",
            "profiles.settings_review_path": "Path: {{path}}",
            "profiles.settings_review_reason_attention": "Needs review",
            "profiles.settings_review_reason_cis_manual": "CIS {{ids}}: {{reason}}",
            "profiles.settings_review_reason_cis_manual_no_ids": "CIS manual review: {{reason}}",
            "profiles.settings_review_reason_cis": "CIS recommendations: {{ids}}",
            "profiles.settings_review_reason_cis_empty": "CIS decision needs review",
            "profiles.settings_review_reason_invalid": "Validation issues: {{count}}",
            "profiles.settings_review_reason_unknown": "Outside active schema",
            "profiles.settings_review_reason_deprecated": "Deprecated policy",
            "profiles.settings_review_reason_raw": "Raw JSON fallback",
            "profiles.settings_review_cis_title": "CIS manual review",
            "profiles.settings_review_cis_body": "CIS decisions need review.",
            "profiles.settings_review_unknown_title": "Unknown",
            "profiles.settings_review_unknown_body": "Unknown body",
            "profiles.settings_review_deprecated_title": "Deprecated",
            "profiles.settings_review_deprecated_body": "Deprecated body",
            "profiles.settings_review_raw_title": "Raw",
            "profiles.settings_review_raw_body": "Raw body",
            "profiles.settings_review_invalid_title": "Invalid",
            "profiles.settings_review_invalid_body": "Invalid body",
        }}[key] || key);

        const entries = [
            {{
                id: "DisableTelemetry",
                label: "DisableTelemetry",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "privacy",
                categoryLabel: "Privacy",
                configured: true,
                invalid: true,
                validationIssueCount: 2,
                value: "bad",
                sources: ["manual"],
                attentionFlags: {{ reviewRequired: true, invalid: true, validationIssueCount: 2 }},
            }},
            {{
                id: "browser.example.invalid",
                label: "browser.example.invalid",
                kind: "preference",
                kindLabel: "Preference",
                categoryId: "preferences",
                categoryLabel: "Preferences",
                configured: true,
                invalid: true,
                validationIssueCount: 1,
                value: "bad",
                sources: ["manual"],
                attentionFlags: {{ reviewRequired: true, invalid: true, validationIssueCount: 1 }},
            }},
            {{
                id: "CleanPolicy",
                label: "CleanPolicy",
                kind: "policy",
                kindLabel: "Policy",
                categoryId: "privacy",
                categoryLabel: "Privacy",
                configured: true,
                value: "true",
                attentionFlags: {{ reviewRequired: false }},
            }},
        ];

        window.BPMProfilesAllSettingsList.create({{
            documentRef: {{}},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsReviewSummaryEl: fakeElement(),
                allSettingsReviewActionsEl: reviewActions,
                allSettingsListEl: listEl,
                allSettingsListEmptyEl: fakeElement(),
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                readWizardSchemaSource: () => ({{ ok: true, data: {{}} }}),
                onSelectionChange: (entry) => {{ selected = entry; }},
                allSettingsRouteState: routeState,
                settingsInventory: {{ collect: () => entries }},
            }},
        }}).render();

        if (routeState.getSnapshot().activeMode !== "review") throw new Error("review mode default");
        if (routeState.getVisibleEntries().length !== 2) throw new Error("invalid review visible entries");
        if (routeState.getVisibleEntries().some((entry) => entry.id === "CleanPolicy")) throw new Error("clean entry leaked");
        if (!reviewActions.innerHTML.includes('data-settings-review-filter="invalid"')) throw new Error("invalid review card");
        if (!reviewActions.innerHTML.includes('data-settings-review-count="2"')) throw new Error("invalid review count");
        if (!reviewActions.innerHTML.includes('data-settings-review-entry="invalid:DisableTelemetry"')) throw new Error("invalid policy entry");
        if (!reviewActions.innerHTML.includes('data-settings-review-entry="invalid:browser.example.invalid"')) throw new Error("invalid preference entry");
        if (!reviewActions.innerHTML.includes("Validation issues: 2")) throw new Error("invalid policy reason");
        if (!reviewActions.innerHTML.includes("Validation issues: 1")) throw new Error("invalid preference reason");

        class ReviewFilterAction extends Element {{
            constructor() {{
                super();
                this.disabled = false;
                this.dataset = {{ settingsReviewFilter: "invalid" }};
            }}
            closest(selector) {{
                if (selector === "[data-settings-review-mode]") return null;
                if (selector === "[data-settings-review-filter]") return this;
                return null;
            }}
        }}
        reviewClick({{ target: new ReviewFilterAction() }});
        if (routeState.getSnapshot().activeFilter !== "invalid") throw new Error("invalid filter not selected");
        if (selected?.id !== "DisableTelemetry") throw new Error("first invalid entry not selected");
        if (routeState.getVisibleEntries().length !== 2) throw new Error("invalid filtered entries");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_all_settings_review_mode_exposes_corporate_cis_manual_review_path_and_reason():
    fixture = build_corporate_cis_l2_profile_fixture(schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL)
    expected_decision = next(
        decision
        for decision in fixture.decisions
        if decision.get("review_required") and decision.get("path") == ["AppAutoUpdate"]
    )
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_state.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_inventory.js"}", "utf8"));
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_list.js"}", "utf8"));

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

        const fixture = {json.dumps({
            "schema_version": fixture.schema_version,
            "flags": fixture.flags,
            "compliance": fixture.compliance,
            "manual_review_count": fixture.manual_review_count,
            "expected_path": ".".join(expected_decision["path"]),
            "expected_reason": expected_decision["reason"],
            "expected_recommendation": expected_decision["recommendation_ids"][0],
        })};
        const allSettingsCategoryCatalog = {json.dumps(get_all_settings_category_catalog())};
        const wizardPreferencesCatalog = {json.dumps(wizard_preferences_catalog)};
        const wizardSchemaShellCatalog = {json.dumps(get_wizard_schema_shell_catalog(wizard_preferences_catalog))};
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_column_setting": "Setting",
            "profiles.settings_list_column_kind": "Kind",
            "profiles.settings_list_column_category": "Category",
            "profiles.settings_list_column_state": "State",
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
            "profiles.settings_review_summary_attention": "Review: {{count}}",
            "profiles.settings_review_summary_clear": "Clear",
            "profiles.settings_review_open": "Open",
            "profiles.settings_review_clear": "No items",
            "profiles.settings_review_empty_group": "No entries in this queue.",
            "profiles.settings_review_more": "+{{count}} more",
            "profiles.settings_review_source_cis": "CIS",
            "profiles.settings_review_source_baseline": "Baseline",
            "profiles.settings_review_source_manual": "Manual",
            "profiles.settings_review_source_imported": "Imported",
            "profiles.settings_review_source_unknown": "Unknown",
            "profiles.settings_review_source_raw": "Raw",
            "profiles.settings_review_source_catalog": "Catalog",
            "profiles.settings_review_path": "Path: {{path}}",
            "profiles.settings_review_reason_attention": "Needs review",
            "profiles.settings_review_reason_cis_manual": "CIS {{ids}}: {{reason}}",
            "profiles.settings_review_reason_cis_manual_no_ids": "CIS manual review: {{reason}}",
            "profiles.settings_review_reason_cis": "CIS recommendations: {{ids}}",
            "profiles.settings_review_reason_cis_empty": "CIS decision needs review",
            "profiles.settings_review_reason_invalid": "Validation issues: {{count}}",
            "profiles.settings_review_reason_unknown": "Outside active schema",
            "profiles.settings_review_reason_deprecated": "Deprecated policy",
            "profiles.settings_review_reason_raw": "Raw JSON fallback",
            "profiles.settings_review_cis_title": "CIS manual review",
            "profiles.settings_review_cis_body": "CIS decisions need review.",
            "profiles.settings_review_unknown_title": "Unknown",
            "profiles.settings_review_unknown_body": "Unknown body",
            "profiles.settings_review_deprecated_title": "Deprecated",
            "profiles.settings_review_deprecated_body": "Deprecated body",
            "profiles.settings_review_raw_title": "Raw",
            "profiles.settings_review_raw_body": "Raw body",
            "profiles.settings_review_invalid_title": "Invalid",
            "profiles.settings_review_invalid_body": "Invalid body",
        }}[key] || key);

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
        const routeState = window.BPMProfilesAllSettingsState.create();
        const reviewActions = fakeElement();

        const list = window.BPMProfilesAllSettingsList.create({{
            documentRef: {{}},
            elements: {{
                allSettingsListSummaryEl: fakeElement(),
                allSettingsReviewSummaryEl: fakeElement(),
                allSettingsReviewActionsEl: reviewActions,
                allSettingsListEl: fakeElement(),
                allSettingsListEmptyEl: fakeElement(),
                allSettingsFilterButtons: [],
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                readWizardSchemaSource: () => ({{ ok: true, data: fixture.flags }}),
                onSelectionChange: () => {{}},
                allSettingsRouteState: routeState,
                settingsInventory: inventory,
            }},
        }});

        list.render();
        if (!reviewActions.innerHTML.includes('data-settings-review-filter="cis-review"')) throw new Error("CIS review card missing");
        if (!reviewActions.innerHTML.includes(`data-settings-review-count="${{fixture.manual_review_count}}"`)) throw new Error("CIS manual review count missing");
        if (!reviewActions.innerHTML.includes(`Path: ${{fixture.expected_path}}`)) throw new Error("CIS manual review path missing");
        if (!reviewActions.innerHTML.includes(`CIS ${{fixture.expected_recommendation}}: ${{fixture.expected_reason}}`)) throw new Error("CIS manual review reason missing");
        if (!routeState.getEntries().some((entry) => entry.id === "AppAutoUpdate" && entry.attentionFlags?.cisReviewRequired)) {{
            throw new Error("CIS manual review entry metadata missing");
        }}
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)
