import assert from "node:assert/strict";
import test from "node:test";

import { create as createList } from "../../../../app/static/profiles_all_settings_list.js";
import { create as createRouteState } from "../../../../app/static/profiles_all_settings_state.js";
import { create as createInventory } from "../../../../app/static/profiles_settings_inventory.js";
import { createFakeElement } from "../../support/dom_harness.js";
import {
    createBudgetElement,
    createFilterButton,
    createListElement,
    installListWindow,
    loadAllSettingsFixture,
    translate,
} from "../../support/settings_harness.js";

const fixture = loadAllSettingsFixture();
const escapeHtml = (value) => String(value || "");

function basicElements(overrides = {}) {
    return {
        allSettingsListSummaryEl: createFakeElement(),
        allSettingsReviewSummaryEl: createFakeElement(),
        allSettingsReviewActionsEl: createFakeElement(),
        allSettingsListEl: createFakeElement(),
        allSettingsListEmptyEl: createFakeElement(),
        allSettingsFilterButtons: [],
        allSettingsSourceFilterButtons: [],
        ...overrides,
    };
}

function createListWithEntries({ entries, routeState = createRouteState(), elements = {}, dependencies = {} }) {
    const resolvedElements = basicElements(elements);
    const list = createList({
        documentRef: {},
        elements: resolvedElements,
        dependencies: {
            t: translate(),
            escapeHtml,
            readWizardSchemaSource: () => ({ ok: true, data: {} }),
            onSelectionChange: () => {},
            allSettingsRouteState: routeState,
            settingsInventory: { collect: () => entries },
            ...dependencies,
        },
    });
    return { list, routeState, elements: resolvedElements };
}

function enterpriseInventory() {
    const enterprise = fixture.enterprise;
    return createInventory({
        dependencies: {
            t: translate(),
            getActiveWizardSchemaVersion: () => enterprise.schema_version,
            getValidationIssues: () => [],
            getComplianceInfo: () => enterprise.compliance,
            getManualEdits: () => [],
        },
        allSettingsCategoryCatalog: fixture.all_settings_category_catalog,
        wizardPreferencesCatalog: fixture.wizard_preferences_catalog,
        wizardSchemaShellCatalog: fixture.wizard_schema_shell_catalog,
    });
}

function actionElement(dataset, matchingSelector) {
    const action = new Element();
    action.disabled = false;
    action.dataset = dataset;
    action.closest = (selector) => selector === matchingSelector ? action : null;
    return action;
}

test("configured mode renders domain summaries, source filters, and drill-down", (context) => {
    installListWindow(context);
    const inventory = enterpriseInventory();
    const entries = inventory.collect(fixture.enterprise.flags);
    const configured = entries.filter((entry) => entry.configured);
    const available = entries.filter((entry) => !entry.configured);
    const routeState = createRouteState({ activeMode: "configured" });
    const configuredSummary = createFakeElement();
    const listElement = createFakeElement();
    const listSummary = createFakeElement();
    const sourceFilters = createFakeElement();
    const sourceTags = {
        "source:baseline": "baseline",
        "source:cis": "cis",
        "source:manual": "manual",
        "source:imported": "imported",
        "source:raw": "raw-fallback",
    };
    const sourceButtons = Object.fromEntries(
        Object.keys(sourceTags).map((filter) => [filter, createFilterButton({ settingsSourceFilter: filter })]),
    );
    const listFilters = Object.fromEntries(
        ["all", "configured", "available", "guided-covered", "all-settings-only", "invalid", "deprecated", "raw", "unknown"]
            .map((filter) => [filter, createFilterButton({ settingsListFilter: filter })]),
    );
    let selected = null;
    const list = createList({
        documentRef: {
            getElementById: (id) => id === "all-settings-list-panel" ? createFakeElement() : null,
        },
        elements: basicElements({
            allSettingsConfiguredSummaryEl: configuredSummary,
            allSettingsSourceFiltersEl: sourceFilters,
            allSettingsListSummaryEl: listSummary,
            allSettingsListEl: listElement,
            allSettingsFilterButtons: Object.values(listFilters),
            allSettingsSourceFilterButtons: Object.values(sourceButtons),
        }),
        dependencies: {
            t: translate({
                "profiles.wizard_shell_badge_mapped": "Mapped",
                "profiles.wizard_shell_badge_raw": "Raw",
                "profiles.wizard_shell_badge_deprecated": "Deprecated",
            }),
            escapeHtml,
            readWizardSchemaSource: () => ({ ok: true, data: { policies: fixture.enterprise.flags } }),
            onSelectionChange: (entry) => { selected = entry; },
            allSettingsRouteState: routeState,
            settingsInventory: inventory,
        },
        allSettingsCategoryCatalog: fixture.all_settings_category_catalog,
        wizardPreferencesCatalog: fixture.wizard_preferences_catalog,
        wizardSchemaShellCatalog: fixture.wizard_schema_shell_catalog,
    });
    list.render();

    assert.equal(configuredSummary.hidden, false);
    assert.equal(sourceFilters.hidden, false);
    assert.equal(routeState.getSnapshot().activeCategory, "all");
    assert.equal(routeState.getSnapshot().counts.mode, configured.length);
    assert.equal(routeState.getVisibleEntries().length, configured.length);
    assert.ok(routeState.getVisibleEntries().every((entry) => entry.configured));
    assert.match(listSummary.textContent, new RegExp(`${configured.length} shown of ${entries.length} entries`));
    assert.equal(listFilters.configured.hidden, true);
    assert.equal(listFilters.available.hidden, true);
    assert.equal(listFilters.all.hidden, false);
    assert.equal(listFilters.all.countElement.textContent, String(configured.length));
    assert.equal(listFilters.all.state.classes["is-active"], true);

    const expectedByCategory = Object.fromEntries(
        fixture.all_settings_category_catalog.categories.map((category) => {
            const categoryEntries = configured.filter((entry) => entry.categoryId === category.id);
            const policyEntries = entries.filter((entry) => entry.kind === "policy" && entry.categoryId === category.id);
            return [category.id, {
                configured: categoryEntries.length,
                available: available.filter((entry) => entry.categoryId === category.id).length,
                attention: categoryEntries.filter((entry) => entry.attentionFlags?.reviewRequired).length,
                mapped: policyEntries.filter((entry) => !entry.rawFallback).length,
                raw: policyEntries.filter((entry) => entry.rawFallback).length,
                deprecated: policyEntries.filter((entry) => entry.deprecated).length,
            }];
        }),
    );
    for (const categoryId of ["browser-access", "privacy-security", "users-addons-sites", "raw-unmapped"]) {
        const expected = expectedByCategory[categoryId];
        assert.match(configuredSummary.innerHTML, new RegExp(`data-settings-domain-card="${categoryId}"`));
        assert.match(configuredSummary.innerHTML, new RegExp(`data-settings-domain-configured-count="${expected.configured}"`));
        assert.match(configuredSummary.innerHTML, new RegExp(`data-settings-domain-hidden-available-count="${expected.available}"`));
        assert.match(configuredSummary.innerHTML, new RegExp(`data-settings-domain-raw-count="${expected.raw}"`));
    }
    assert.match(listElement.innerHTML, /data-settings-entry-state-badge=/);
    assert.match(listElement.innerHTML, /data-settings-entry-category-badge=/);
    assert.match(listElement.innerHTML, /data-settings-entry-source=/);

    configuredSummary.emit("click", {
        target: actionElement(
            { settingsDomainCard: "privacy-security" },
            "[data-settings-domain-card]",
        ),
    });
    assert.equal(routeState.getSnapshot().activeCategory, "privacy-security");
    assert.ok(routeState.getVisibleEntries().every((entry) => entry.categoryId === "privacy-security"));
    assert.equal(selected?.categoryId, "privacy-security");

    const firstCisEntry = configured.find((entry) => entry.sources.includes("cis"));
    routeState.setActiveCategory(firstCisEntry.categoryId);
    routeState.setSelectedEntryKey(`${firstCisEntry.kind}:${firstCisEntry.id}`);
    list.render();
    sourceButtons["source:cis"].click();
    assert.equal(routeState.getSnapshot().activeFilter, "source:cis");
    assert.ok(routeState.getVisibleEntries().every((entry) => entry.sources.includes("cis")));
});

test("heavy enterprise catalog bounds rendered rows and help links", (context) => {
    installListWindow(context);
    const inventory = enterpriseInventory();
    const routeState = createRouteState({ activeMode: "catalog" });
    const listElement = createListElement();
    const budgetElement = createBudgetElement();
    const list = createList({
        documentRef: { documentElement: { lang: "en" } },
        elements: basicElements({
            allSettingsListEl: listElement,
            allSettingsListBudgetEl: budgetElement,
        }),
        dependencies: {
            t: translate(),
            escapeHtml,
            getActiveWizardSchemaVersion: () => fixture.enterprise.schema_version,
            readWizardSchemaSource: () => ({ ok: true, data: fixture.enterprise.flags }),
            getValidationIssues: () => [],
            getComplianceInfo: () => fixture.enterprise.compliance,
            getManualEdits: () => [],
            getCurrentLang: () => "en",
            onSelectionChange: () => {},
            allSettingsRouteState: routeState,
            settingsInventory: inventory,
            documentationRowHelpLinks: fixture.documentation_row_help_links,
        },
    });
    list.render();
    assert.ok(routeState.getVisibleEntries().length >= 145);
    assert.ok(listElement.renderedRows() <= 7);
    assert.equal(listElement.renderedHelpLinks(), listElement.renderedRows());
    budgetElement.clickAction("expand");
    assert.ok(listElement.renderedRows() <= 50);
    assert.equal(listElement.renderedHelpLinks(), listElement.renderedRows());
    budgetElement.clickAction("next");
    assert.ok(listElement.renderedRows() <= 50);

    routeState.setActiveMode("configured");
    routeState.setActiveFilter("all");
    list.render();
    assert.equal(routeState.getSnapshot().counts.configured, fixture.enterprise.configured_count);
    assert.ok(routeState.getVisibleEntries().length > 7);
    assert.ok(listElement.renderedRows() <= 7);
});

test("review mode shows configured attention queues before catalog-only entries", (context) => {
    installListWindow(context);
    const entries = [
        {
            id: "Proxy", label: "Proxy", kind: "policy", kindLabel: "Policy",
            categoryId: "browser-access", categoryLabel: "Browser", configured: true,
            value: "system", sources: ["baseline", "cis"],
            sourceDetails: { recommendationIds: ["1.2.3"], decisions: [{ path: ["Proxy", "Mode"], recommendation_ids: ["1.2.3"], review_required: true, reason: "Proxy mode is environment-specific." }] },
            attentionFlags: { reviewRequired: true, cisReviewRequired: true },
        },
        { id: "RawPolicy", label: "RawPolicy", kind: "policy", kindLabel: "Policy", categoryId: "raw-unmapped", categoryLabel: "Raw", configured: true, rawFallback: true, value: "{}", sources: ["raw-fallback"], attentionFlags: { reviewRequired: true } },
        { id: "AvailableOnly", label: "AvailableOnly", kind: "policy", configured: false, attentionFlags: { reviewRequired: false } },
        { id: "AvailableRaw", label: "AvailableRaw", kind: "policy", configured: false, rawFallback: true, sources: ["catalog", "raw-fallback"], attentionFlags: { reviewRequired: true, rawFallback: true } },
        { id: "AvailableDeprecated", label: "AvailableDeprecated", kind: "policy", configured: false, deprecated: true, sources: ["catalog"], attentionFlags: { reviewRequired: true, deprecated: true } },
        { id: "AvailableInvalid", label: "AvailableInvalid", kind: "policy", configured: false, invalid: true, sources: ["catalog"], attentionFlags: { reviewRequired: true, invalid: true } },
    ];
    let selected = null;
    const reviewSummary = createFakeElement();
    const reviewActions = createFakeElement();
    const { list, routeState } = createListWithEntries({
        entries,
        elements: { allSettingsReviewSummaryEl: reviewSummary, allSettingsReviewActionsEl: reviewActions },
        dependencies: { onSelectionChange: (entry) => { selected = entry; } },
    });
    list.render();

    assert.equal(routeState.getVisibleEntries().length, 2);
    assert.ok(routeState.getVisibleEntries().every((entry) => entry.configured));
    assert.equal(selected?.id, "Proxy");
    assert.match(reviewSummary.textContent, /2/);
    assert.match(reviewActions.innerHTML, /data-settings-review-filter="cis-review"/);
    assert.match(reviewActions.innerHTML, /data-settings-review-entry="cis-review:Proxy"/);
    assert.match(reviewActions.innerHTML, /Path: Proxy\.Mode/);
    assert.match(reviewActions.innerHTML, /CIS 1\.2\.3: Proxy mode is environment-specific\./);
    assert.match(reviewActions.innerHTML, /data-settings-review-queue="raw"/);
    assert.doesNotMatch(reviewActions.innerHTML, /raw:AvailableRaw/);

    routeState.setActiveMode("catalog");
    routeState.setActiveFilter("all");
    list.render();
    assert.equal(routeState.getVisibleEntries().length, entries.length);
});

test("clean review state exposes configured and catalog navigation actions", (context) => {
    installListWindow(context);
    const entries = [
        { id: "DisableTelemetry", label: "DisableTelemetry", kind: "policy", configured: true, value: "true", attentionFlags: { reviewRequired: false } },
        { id: "AvailableOnly", label: "AvailableOnly", kind: "policy", configured: false, attentionFlags: { reviewRequired: false } },
    ];
    const reviewSummary = createFakeElement();
    const reviewActions = createFakeElement();
    const modeChanges = [];
    const { list, routeState } = createListWithEntries({
        entries,
        elements: { allSettingsReviewSummaryEl: reviewSummary, allSettingsReviewActionsEl: reviewActions },
        dependencies: { onModeChange: (mode, options) => modeChanges.push([mode, options.updateUrl]) },
    });
    list.render();

    assert.equal(routeState.getVisibleEntries().length, 0);
    assert.equal(reviewSummary.textContent, "Clear");
    assert.match(reviewActions.innerHTML, /Nothing needs review/);
    assert.match(reviewActions.innerHTML, /data-settings-review-empty-state/);
    assert.match(reviewActions.innerHTML, /data-settings-review-mode="configured"/);
    assert.doesNotMatch(reviewActions.innerHTML, /data-settings-review-filter=/);

    reviewActions.emit("click", {
        target: actionElement({ settingsReviewMode: "configured" }, "[data-settings-review-mode]"),
    });
    assert.equal(routeState.getSnapshot().activeMode, "configured");
    assert.deepEqual(modeChanges.at(-1), ["configured", true]);
    reviewActions.emit("click", {
        target: actionElement({ settingsReviewMode: "catalog" }, "[data-settings-review-mode]"),
    });
    assert.equal(routeState.getSnapshot().activeMode, "catalog");
});

test("review mode groups invalid entries and selects the first filtered entry", (context) => {
    installListWindow(context);
    const entries = [
        { id: "DisableTelemetry", label: "DisableTelemetry", kind: "policy", configured: true, invalid: true, validationIssueCount: 2, sources: ["manual"], attentionFlags: { reviewRequired: true, invalid: true, validationIssueCount: 2 } },
        { id: "browser.example.invalid", label: "browser.example.invalid", kind: "preference", configured: true, invalid: true, validationIssueCount: 1, sources: ["manual"], attentionFlags: { reviewRequired: true, invalid: true, validationIssueCount: 1 } },
        { id: "CleanPolicy", label: "CleanPolicy", kind: "policy", configured: true, attentionFlags: { reviewRequired: false } },
    ];
    const reviewActions = createFakeElement();
    let selected = null;
    const { list, routeState } = createListWithEntries({
        entries,
        elements: { allSettingsReviewActionsEl: reviewActions },
        dependencies: { onSelectionChange: (entry) => { selected = entry; } },
    });
    list.render();
    assert.equal(routeState.getVisibleEntries().length, 2);
    assert.match(reviewActions.innerHTML, /data-settings-review-filter="invalid"/);
    assert.match(reviewActions.innerHTML, /data-settings-review-count="2"/);
    assert.match(reviewActions.innerHTML, /Validation issues: 2/);
    assert.match(reviewActions.innerHTML, /Validation issues: 1/);

    const action = actionElement(
        { settingsReviewFilter: "invalid" },
        "[data-settings-review-filter]",
    );
    reviewActions.emit("click", { target: action });
    assert.equal(routeState.getSnapshot().activeFilter, "invalid");
    assert.equal(selected?.id, "DisableTelemetry");
    assert.equal(routeState.getVisibleEntries().length, 2);
});

test("enterprise review exposes exact CIS path, recommendation, and reason", (context) => {
    installListWindow(context);
    const inventory = enterpriseInventory();
    const reviewActions = createFakeElement();
    const routeState = createRouteState();
    const list = createList({
        documentRef: {},
        elements: basicElements({ allSettingsReviewActionsEl: reviewActions }),
        dependencies: {
            t: translate(), escapeHtml,
            readWizardSchemaSource: () => ({ ok: true, data: fixture.enterprise.flags }),
            onSelectionChange: () => {},
            allSettingsRouteState: routeState,
            settingsInventory: inventory,
        },
    });
    list.render();
    assert.match(reviewActions.innerHTML, /data-settings-review-filter="cis-review"/);
    assert.match(reviewActions.innerHTML, new RegExp(`data-settings-review-count="${fixture.enterprise.manual_review_count}"`));
    assert.ok(reviewActions.innerHTML.includes(`Path: ${fixture.enterprise.expected_path}`));
    assert.ok(reviewActions.innerHTML.includes(`CIS ${fixture.enterprise.expected_recommendation}: ${fixture.enterprise.expected_reason}`));
    assert.ok(routeState.getEntries().some((entry) => entry.id === "AppAutoUpdate" && entry.attentionFlags?.cisReviewRequired));
});
