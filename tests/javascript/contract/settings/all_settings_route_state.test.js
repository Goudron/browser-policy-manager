import assert from "node:assert/strict";
import test from "node:test";

import { create as createList } from "../../../../app/static/profiles_all_settings_list.js";
import { create as createRouteState } from "../../../../app/static/profiles_all_settings_state.js";
import { createFakeElement } from "../../support/dom_harness.js";
import {
    createBudgetElement,
    createListElement,
    installListWindow,
    translate,
} from "../../support/settings_harness.js";

const escapeHtml = (value) => String(value || "");

function listElements({ listElement = createFakeElement(), budgetElement } = {}) {
    return {
        allSettingsListSummaryEl: createFakeElement(),
        allSettingsReviewSummaryEl: createFakeElement(),
        allSettingsReviewActionsEl: createFakeElement(),
        allSettingsListEl: listElement,
        allSettingsListEmptyEl: createFakeElement(),
        allSettingsListBudgetEl: budgetElement,
        allSettingsFilterButtons: [],
    };
}

test("route state filters entries by mode, category, and filter", () => {
    const state = createRouteState({ activeMode: "bogus" });
    assert.equal(state.getSnapshot().activeMode, "review");

    const entries = [
        { kind: "policy", id: "ReviewOnly", configured: true, categoryId: "privacy", attentionFlags: { reviewRequired: true } },
        { kind: "policy", id: "ConfiguredOnly", configured: true, categoryId: "browser", attentionFlags: { reviewRequired: false } },
        { kind: "policy", id: "CatalogOnly", configured: false, categoryId: "browser", attentionFlags: { reviewRequired: false } },
    ];
    const options = {
        entryKey: (entry) => `${entry.kind}:${entry.id}`,
        filterValues: ["all", "configured"],
        matchesMode: (entry, mode) => mode === "review"
            ? Boolean(entry.attentionFlags.reviewRequired)
            : mode === "configured" ? entry.configured : true,
        matchesCategory: (entry, category, mode) => (
            mode !== "configured" || category === "all" || entry.categoryId === category
        ),
        matchesFilter: (entry, filter) => filter !== "configured" || entry.configured,
    };

    state.updateEntries(entries, options);
    assert.deepEqual(state.getVisibleEntries().map((entry) => entry.id), ["ReviewOnly"]);

    state.setActiveMode("configured");
    state.updateEntries(entries, options);
    assert.equal(state.getSnapshot().counts.mode, 2);
    assert.equal(state.getSnapshot().activeCategory, "all");

    state.setSelectedEntryKey("policy:ConfiguredOnly", {
        categoryId: "browser",
        target: "all-settings-entry:policy:ConfiguredOnly",
    });
    assert.equal(state.getSnapshot().activeCategory, "all");
    assert.equal(state.getSnapshot().focusedTarget, "all-settings-entry:policy:ConfiguredOnly");

    state.setActiveMode("catalog");
    state.setActiveFilter("configured");
    state.updateEntries(entries, options);
    assert.equal(state.getSnapshot().counts.mode, 3);
    assert.equal(state.getSnapshot().counts.visible, 2);

    state.setActiveMode("configured");
    state.setActiveCategory("privacy");
    state.setActiveFilter("all");
    state.updateEntries(entries, options);
    assert.equal(state.getCategoryEntries().length, 1);
    assert.equal(state.getSnapshot().counts.category, 1);
});

test("list budgets long rows independently for each mode", (context) => {
    installListWindow(context);
    let sourceData = { fixture: "short" };
    let currentEntries = Array.from({ length: 9 }, (_, index) => ({
        id: `Policy${index + 1}`,
        label: `Policy ${index + 1}`,
        kind: "policy",
        categoryId: "browser",
        configured: true,
        invalid: true,
        value: "Configured",
        sources: ["manual"],
        attentionFlags: { reviewRequired: true, validationIssueCount: 1 },
    }));
    const routeState = createRouteState();
    const listElement = createListElement();
    const budgetElement = createBudgetElement();
    const list = createList({
        documentRef: {},
        elements: listElements({ listElement, budgetElement }),
        dependencies: {
            t: translate(),
            escapeHtml,
            readWizardSchemaSource: () => ({ ok: true, data: sourceData }),
            onSelectionChange: () => {},
            allSettingsRouteState: routeState,
            settingsInventory: { collect: () => currentEntries },
        },
    });

    list.render();
    assert.equal(routeState.getSnapshot().activeMode, "review");
    assert.equal(routeState.getVisibleEntries().length, 9);
    assert.equal(listElement.visibleRows(), 7);
    assert.match(budgetElement.innerHTML, /Showing 7 of 9\./);
    assert.match(budgetElement.innerHTML, /Show 2 more/);

    budgetElement.clickAction();
    assert.equal(listElement.visibleRows(), 9);
    assert.match(budgetElement.innerHTML, /Show fewer/);

    routeState.setActiveMode("configured");
    routeState.setActiveFilter("all");
    list.render();
    assert.equal(listElement.visibleRows(), 7);

    routeState.setActiveMode("catalog");
    routeState.setActiveFilter("all");
    list.render();
    assert.equal(listElement.visibleRows(), 7);

    sourceData = { fixture: "large" };
    currentEntries = Array.from({ length: 120 }, (_, index) => ({
        id: `CatalogPolicy${index + 1}`,
        label: `Catalog policy ${index + 1}`,
        kind: "policy",
        categoryId: "browser",
        configured: false,
        value: "Not configured",
        sources: ["catalog"],
        attentionFlags: { reviewRequired: false },
    }));
    list.render();
    assert.equal(routeState.getVisibleEntries().length, 120);
    assert.equal(listElement.renderedRows(), 7);
    assert.match(budgetElement.innerHTML, /Show 113 more/);

    budgetElement.clickAction("expand");
    assert.equal(listElement.renderedRows(), 50);
    assert.match(budgetElement.innerHTML, /Showing 1-50 of 120\./);
    budgetElement.clickAction("next");
    assert.equal(listElement.renderedRows(), 50);
    assert.match(budgetElement.innerHTML, /Showing 51-100 of 120\./);
    budgetElement.clickAction("next");
    assert.equal(listElement.renderedRows(), 20);
    assert.match(budgetElement.innerHTML, /Showing 101-120 of 120\./);
    assert.doesNotMatch(budgetElement.innerHTML, /Next<\/button>/);
});

test("list caches inventory until a source dependency changes", (context) => {
    installListWindow(context);
    let sourceData = { DisableTelemetry: true };
    let schemaVersion = "release-152";
    let validationIssues = [];
    let currentLang = "en";
    let complianceInfo = { decisions: [] };
    let manualEdits = [];
    let collectCalls = 0;
    const routeState = createRouteState();
    const list = createList({
        documentRef: { documentElement: { lang: currentLang } },
        elements: listElements(),
        dependencies: {
            t: translate(),
            escapeHtml,
            getActiveWizardSchemaVersion: () => schemaVersion,
            readWizardSchemaSource: () => ({ ok: true, data: sourceData }),
            getValidationIssues: () => validationIssues,
            getComplianceInfo: () => complianceInfo,
            getManualEdits: () => manualEdits,
            getCurrentLang: () => currentLang,
            onSelectionChange: () => {},
            allSettingsRouteState: routeState,
            settingsInventory: {
                collect: () => {
                    collectCalls += 1;
                    return [{
                        id: "DisableTelemetry",
                        label: "DisableTelemetry",
                        kind: "policy",
                        categoryId: "privacy",
                        configured: true,
                        invalid: true,
                        value: "true",
                        sources: ["manual"],
                        attentionFlags: {
                            reviewRequired: true,
                            validationIssueCount: validationIssues.length,
                        },
                    }];
                },
            },
        },
    });
    const renderAndExpect = (expected) => {
        list.render();
        assert.equal(collectCalls, expected);
    };

    renderAndExpect(1);
    renderAndExpect(1);
    routeState.setActiveMode("catalog");
    renderAndExpect(1);
    routeState.setActiveFilter("configured");
    renderAndExpect(1);
    sourceData = { DisableTelemetry: false };
    renderAndExpect(2);
    schemaVersion = "esr-140";
    renderAndExpect(3);
    validationIssues = [{ policy: "DisableTelemetry", path: ["DisableTelemetry"], message: "bad" }];
    renderAndExpect(4);
    currentLang = "ru";
    renderAndExpect(5);
    complianceInfo = { decisions: [{ path: ["DisableTelemetry"], decision: "added_from_cis" }] };
    renderAndExpect(6);
    manualEdits = [{ path: ["DisableTelemetry"], operation: "set" }];
    renderAndExpect(7);
    renderAndExpect(7);
});
