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
from tests.web_profiles_page_helpers import static_source, template_source

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def test_all_settings_configured_mode_domain_summary_contract_is_wired():
    settings_template = template_source("_page_settings_workspace.html")
    dom_source = static_source("profiles_dom.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")
    list_source = static_source("profiles_all_settings_list.js")
    css_source = static_source("profiles_css/20-editor-wizard.css")

    for snippet in (
        'id="all-settings-configured-summary"',
        'id="all-settings-source-filters"',
        "profiles.settings_configured_domains_label",
        "profiles.settings_source_filters_label",
    ):
        assert snippet in settings_template
    assert 'id="all-settings-category-summary"' not in settings_template
    assert "all-settings-state-summary" not in settings_template

    assert 'allSettingsCategorySummaryEl: byId("all-settings-category-summary")' not in dom_source
    assert 'allSettingsConfiguredSummaryEl: byId("all-settings-configured-summary")' in dom_source
    assert 'allSettingsSourceFiltersEl: byId("all-settings-source-filters")' in dom_source
    assert 'allSettingsSourceFilterButtons: all("[data-settings-source-filter]")' in dom_source
    assert "allSettingsCategorySummaryEl," not in bootstrap_source
    assert "allSettingsConfiguredSummaryEl," in bootstrap_source
    assert "allSettingsSourceFiltersEl," in bootstrap_source
    assert "allSettingsSourceFilterButtons," in bootstrap_source

    for snippet in (
        "function buildConfiguredDomainSummaries(entries)",
        "function buildCategorySummaries(entries)",
        "function renderDomainSummaryCards(container, summaries, snapshot, options = {})",
        "function renderConfiguredSummary()",
        "function updateSourceFilterButtons()",
        "snapshot.activeMode !== \"configured\"",
        "filterHiddenInMode(snapshot.activeFilter, snapshot.activeMode)",
        "data-settings-domain-card",
        "data-settings-domain-configured-count",
        "data-settings-domain-hidden-available-count",
        "data-settings-domain-attention-count",
        "data-settings-domain-mapped-count",
        "data-settings-domain-raw-count",
        "data-settings-domain-deprecated-count",
        "profiles.wizard_shell_badge_mapped",
        "profiles.wizard_shell_badge_raw",
        "profiles.wizard_shell_badge_deprecated",
        "data-settings-source-filter",
        "raw-fallback",
        "profiles.settings_configured_domain_configured",
        "profiles.settings_configured_domain_attention",
        "profiles.settings_configured_domain_available",
        "function sourceLabel(source)",
        "function entryAttentionBadges(entry)",
        "function renderEntryBadges(entry)",
        "data-settings-entry-state-badge",
        "data-settings-entry-category-badge",
        "data-settings-entry-source",
        "data-settings-entry-attention",
    ):
        assert snippet in list_source
    assert "source:cis" in settings_template

    for snippet in (
        ".all-settings-domain-summary",
        ".all-settings-domain-card",
        ".all-settings-domain-card-coverage",
        ".all-settings-domain-card-count.has-attention",
        ".all-settings-source-filter-bar",
        ".all-settings-source-filter-button",
        ".all-settings-list-badges",
        ".all-settings-list-badge",
        ".all-settings-list-badge.has-attention",
    ):
        assert snippet in css_source


def test_all_settings_configured_mode_runtime_renders_domain_summary_cards_for_enterprise_profile():
    fixture = build_corporate_cis_l2_profile_fixture(schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL)
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        global.Element = class {{}};
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

        function fakeButton(dataset) {{
            const countEl = {{ textContent: "", attrs: {{}}, setAttribute: (name, value) => {{ countEl.attrs[name] = String(value); }} }};
            const state = {{ classes: {{}}, attrs: {{}}, click: null }};
            return {{
                dataset,
                disabled: false,
                hidden: false,
                classList: {{
                    toggle: (name, active) => {{ state.classes[name] = Boolean(active); }},
                }},
                setAttribute: (name, value) => {{ state.attrs[name] = String(value); }},
                querySelector: (selector) => (
                    selector === "[data-settings-source-filter-count]"
                    || selector === "[data-settings-list-filter-count]"
                ) ? countEl : null,
                addEventListener: (eventName, handler) => {{
                    if (eventName === "click") state.click = handler;
                }},
                click: () => state.click?.(),
                state,
                countEl,
            }};
        }}

        const fixture = {json.dumps({
            "schema_version": fixture.schema_version,
            "flags": fixture.flags,
            "compliance": fixture.compliance,
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
            "profiles.settings_configured_domain_configured": "configured",
            "profiles.settings_configured_domain_attention": "attention",
            "profiles.settings_configured_domain_available": "available",
            "profiles.settings_source_baseline": "Baseline",
            "profiles.settings_source_cis": "CIS",
            "profiles.settings_source_manual": "Manual",
            "profiles.settings_source_imported": "Imported",
            "profiles.settings_source_raw": "Raw",
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
            "profiles.wizard_shell_badge_mapped": "Mapped",
            "profiles.wizard_shell_badge_raw": "Raw",
            "profiles.wizard_shell_badge_deprecated": "Deprecated",
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
        const entries = inventory.collect(fixture.flags);
        const configuredEntries = entries.filter((entry) => entry.configured);
        const availableEntries = entries.filter((entry) => !entry.configured);
        const sourceTags = {{
            "source:baseline": "baseline",
            "source:cis": "cis",
            "source:manual": "manual",
            "source:imported": "imported",
            "source:raw": "raw-fallback",
        }};
        const expectedBySource = Object.fromEntries(
            Object.entries(sourceTags).map(([filterValue, source]) => [
                filterValue,
                configuredEntries.filter((entry) => Array.isArray(entry.sources) && entry.sources.includes(source)).length,
            ])
        );
        const expectedByCategory = Object.fromEntries(
            allSettingsCategoryCatalog.categories.map((category) => {{
                const categoryEntries = configuredEntries.filter((entry) => entry.categoryId === category.id);
                const available = availableEntries.filter((entry) => entry.categoryId === category.id).length;
                const policyEntries = entries.filter((entry) => entry.kind === "policy" && entry.categoryId === category.id);
                const mapped = policyEntries.filter((entry) => !entry.rawFallback).length;
                const raw = policyEntries.filter((entry) => entry.rawFallback).length;
                const deprecated = policyEntries.filter((entry) => entry.deprecated).length;
                const attention = categoryEntries.filter((entry) => Boolean(
                    entry.attentionFlags?.reviewRequired
                    || entry.invalid
                    || entry.deprecated
                    || entry.rawFallback
                    || entry.unknown
                )).length;
                return [category.id, {{ configured: categoryEntries.length, available, attention, mapped, raw, deprecated }}];
            }})
        );

        const routeState = window.BPMProfilesAllSettingsState.create();
        routeState.setActiveMode("configured");
        const configuredSummary = fakeElement();
        const allSettingsList = fakeElement();
        const listSummary = fakeElement();
        const sourceFilters = fakeElement();
        const sourceFilterButtons = Object.fromEntries(
            Object.keys(sourceTags).map((filterValue) => [filterValue, fakeButton({{ settingsSourceFilter: filterValue }})])
        );
        const listFilterButtons = Object.fromEntries(
            ["all", "configured", "available", "guided-covered", "all-settings-only", "invalid", "deprecated", "raw", "unknown"]
                .map((filterValue) => [filterValue, fakeButton({{ settingsListFilter: filterValue }})])
        );
        let summaryClick = null;
        configuredSummary.addEventListener = (eventName, handler) => {{
            if (eventName === "click") summaryClick = handler;
        }};
        let selected = null;

        const list = window.BPMProfilesAllSettingsList.create({{
            documentRef: {{
                getElementById: (id) => id === "all-settings-list-panel"
                    ? {{ scrollIntoView: () => {{}} }}
                    : null,
            }},
            elements: {{
                allSettingsConfiguredSummaryEl: configuredSummary,
                allSettingsSourceFiltersEl: sourceFilters,
                allSettingsListSummaryEl: listSummary,
                allSettingsReviewSummaryEl: fakeElement(),
                allSettingsReviewActionsEl: fakeElement(),
                allSettingsListEl: allSettingsList,
                allSettingsListEmptyEl: fakeElement(),
                allSettingsFilterButtons: Object.values(listFilterButtons),
                allSettingsSourceFilterButtons: Object.values(sourceFilterButtons),
            }},
            dependencies: {{
                t,
                escapeHtml: (value) => String(value || ""),
                readWizardSchemaSource: () => ({{ ok: true, data: {{ policies: fixture.flags }} }}),
                onSelectionChange: (entry) => {{ selected = entry; }},
                allSettingsRouteState: routeState,
                settingsInventory: inventory,
            }},
            allSettingsCategoryCatalog,
            wizardPreferencesCatalog,
            wizardSchemaShellCatalog,
        }});
        list.render();

        if (configuredSummary.hidden) throw new Error("configured summary hidden");
        if (sourceFilters.hidden) throw new Error("source filters hidden");
        const initialSnapshot = routeState.getSnapshot();
        const initialCategory = initialSnapshot.activeCategory;
        if (initialCategory !== "all") throw new Error("configured mode should start with all configured entries");
        if (initialSnapshot.counts.mode !== configuredEntries.length) throw new Error("configured mode count mismatch");
        if (initialSnapshot.counts.category !== configuredEntries.length) throw new Error("configured category count mismatch");
        if (routeState.getModeEntries().length !== configuredEntries.length) throw new Error("configured mode entries mismatch");
        if (routeState.getVisibleEntries().length !== configuredEntries.length) throw new Error("configured mode should show every configured entry first");
        if (!listSummary.textContent.includes(`${{configuredEntries.length}} shown of ${{entries.length}} entries`)) {{
            throw new Error(`configured summary did not expose configured scope: ${{listSummary.textContent}}`);
        }}
        if (!listFilterButtons.configured.hidden) throw new Error("configured state filter should be hidden in configured mode");
        if (!listFilterButtons.available.hidden) throw new Error("available state filter should be hidden in configured mode");
        if (listFilterButtons.all.hidden) throw new Error("all filter should remain visible in configured mode");
        if (listFilterButtons.all.countEl.textContent !== String(configuredEntries.length)) {{
            throw new Error("all filter should show every configured entry");
        }}
        if (!listFilterButtons.all.state.classes["is-active"]) throw new Error("all filter should remain active");
        if (listFilterButtons["guided-covered"].countEl.textContent !== String(configuredEntries.filter((entry) => entry.guided).length)) {{
            throw new Error("guided filter should show configured mode count");
        }}
        if (!routeState.getVisibleEntries().every((entry) => entry.configured)) {{
            throw new Error("initial configured mode leaked available entries");
        }}
        ["browser-access", "privacy-security", "users-addons-sites", "raw-unmapped"].forEach((categoryId) => {{
            const expected = expectedByCategory[categoryId] || {{ configured: 0, attention: 0 }};
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-card="${{categoryId}}"`)) {{
                throw new Error(`domain card missing ${{categoryId}}`);
            }}
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-configured-count="${{expected.configured}}"`)) {{
                throw new Error(`configured count missing ${{categoryId}}`);
            }}
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-hidden-available-count="${{expected.available}}"`)) {{
                throw new Error(`hidden available count missing ${{categoryId}}`);
            }}
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-attention-count="${{expected.attention}}"`)) {{
                throw new Error(`attention count missing ${{categoryId}}`);
            }}
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-mapped-count="${{expected.mapped}}"`)) {{
                throw new Error(`mapped count missing ${{categoryId}}`);
            }}
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-raw-count="${{expected.raw}}"`)) {{
                throw new Error(`raw count missing ${{categoryId}}`);
            }}
            if (!configuredSummary.innerHTML.includes(`data-settings-domain-deprecated-count="${{expected.deprecated}}"`)) {{
                throw new Error(`deprecated count missing ${{categoryId}}`);
            }}
        }});
        if ((expectedByCategory["browser-access"]?.configured || 0) <= 0) throw new Error("browser access fixture count");
        if ((expectedByCategory["privacy-security"]?.attention || 0) <= 0) throw new Error("privacy attention fixture count");
        if ((expectedByCategory["users-addons-sites"]?.configured || 0) <= 0) throw new Error("users/addons fixture count");
        const activeCategory = routeState.getSnapshot().activeCategory;
        Object.entries(sourceTags).forEach(([filterValue, source]) => {{
            const scopedSourceCount = configuredEntries.filter((entry) =>
                (activeCategory === "all" || entry.categoryId === activeCategory)
                && Array.isArray(entry.sources)
                && entry.sources.includes(source)
            ).length;
            if (sourceFilterButtons[filterValue].countEl.textContent !== String(scopedSourceCount)) {{
                throw new Error(`source count missing ${{filterValue}}`);
            }}
        }});
        if (expectedBySource["source:cis"] <= 0) throw new Error("CIS source fixture count");
        if (expectedBySource["source:baseline"] <= 0) throw new Error("baseline source fixture count");
        const attentionEntry = configuredEntries.find((entry) => Boolean(
            entry.attentionFlags?.reviewRequired
            || entry.invalid
            || entry.deprecated
            || entry.rawFallback
            || entry.unknown
        ));
        if (!allSettingsList.innerHTML.includes("data-settings-entry-state-badge=")) throw new Error("row state badge missing");
        if (!allSettingsList.innerHTML.includes("data-settings-entry-category-badge=")) throw new Error("row category badge missing");
        if (!allSettingsList.innerHTML.includes("data-settings-entry-source=")) throw new Error("row source badge missing");
        if (attentionEntry && !allSettingsList.innerHTML.includes("data-settings-entry-attention=")) {{
            throw new Error("row attention badge missing");
        }}

        class DomainCardAction extends Element {{
            constructor(categoryId) {{
                super();
                this.disabled = false;
                this.dataset = {{ settingsDomainCard: categoryId }};
            }}
            closest(selector) {{
                return selector === "[data-settings-domain-card]" ? this : null;
            }}
        }}
        summaryClick({{ target: new DomainCardAction("privacy-security") }});
        if (routeState.getSnapshot().activeCategory !== "privacy-security") throw new Error("domain card did not set active category");
        if (routeState.getSnapshot().activeFilter !== "all") throw new Error("domain card did not reset filter");
        if (selected?.categoryId !== "privacy-security") throw new Error("domain card did not select first category entry");
        if (!routeState.getVisibleEntries().every((entry) => entry.categoryId === "privacy-security" && entry.configured)) {{
            throw new Error("domain drilldown leaked outside selected category");
        }}
        if (routeState.getVisibleEntries().length !== expectedByCategory["privacy-security"].configured) {{
            throw new Error("domain drilldown configured count mismatch");
        }}

        const firstCisEntry = configuredEntries.find((entry) => entry.sources.includes("cis"));
        routeState.setActiveCategory(firstCisEntry.categoryId);
        routeState.setSelectedEntryKey(`${{firstCisEntry.kind}}:${{firstCisEntry.id}}`, {{
            categoryId: firstCisEntry.categoryId,
            target: `all-settings-entry:${{firstCisEntry.kind}}:${{firstCisEntry.id}}`,
        }});
        list.render();
        sourceFilterButtons["source:cis"].click();
        if (routeState.getSnapshot().activeFilter !== "source:cis") throw new Error("CIS source filter not active");
        if (routeState.getSnapshot().activeCategory !== firstCisEntry.categoryId) throw new Error("source filter lost category context");
        if (routeState.getSnapshot().selectedEntryKey !== `${{firstCisEntry.kind}}:${{firstCisEntry.id}}`) throw new Error("source filter lost selected entry");
        if (!routeState.getVisibleEntries().every((entry) =>
            entry.configured && entry.categoryId === firstCisEntry.categoryId && entry.sources.includes("cis")
        )) throw new Error("source filter leaked outside selected configured category");
        if (!sourceFilterButtons["source:cis"].state.classes["is-active"]) throw new Error("CIS source chip not active");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)
