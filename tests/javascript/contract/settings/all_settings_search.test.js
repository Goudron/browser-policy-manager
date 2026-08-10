import assert from "node:assert/strict";
import test from "node:test";

import { create as createSearch } from "../../../../app/static/profiles_settings_search.js";
import { createFakeElement, installImmediateWindow } from "../../support/dom_harness.js";

function resultTargets(resultsElement) {
    return resultsElement.children.flatMap((group) =>
        group.children.flatMap((child) =>
            child.dataset.settingsSearchTarget
                ? [child]
                : child.children.filter((nested) => nested.dataset.settingsSearchTarget),
        ),
    ).map((button) => button.dataset.settingsSearchTarget);
}

test("search indexes known-preference sections through the ESM API", () => {
    const search = createSearch({
        documentRef: { body: { dataset: { profilesTemplateKind: "settings" } } },
        dependencies: {
            t: (key, fallback = "") => fallback || key,
            escapeHtml: (value) => String(value || ""),
            humanizeIdentifier: (value) => String(value || ""),
            normalizeSearchText: (value) => String(value || "").toLowerCase(),
            setWizardStep: () => {},
            getAllSettingsSearchEntries: () => [],
            findAllSettingsEntryTarget: () => null,
        },
        wizardSettingsCatalog: {
            sections: [{
                id: "privacy",
                preferences: {
                    id: "privacy",
                    title_key: "privacy.title",
                    body_key: "privacy.body",
                    prefixes: ["browser.safebrowsing."],
                    gui_groups: [],
                    controls: [],
                    bundles: [],
                    known_preferences: [{
                        pref: "browser.safebrowsing.malware.enabled",
                        status: "locked",
                        type: "boolean",
                    }],
                },
            }],
        },
        wizardSearchSectionSteps: {
            privacy: { step: 4, key: "privacy.step", fallback: "Privacy" },
        },
    });

    assert.doesNotThrow(() => search.buildIndex());
});

test("search groups, scopes, deduplicates, and activates all-settings targets", (context) => {
    context.after(installImmediateWindow());

    let bundleClicks = 0;
    const listPanel = createFakeElement("section");
    const bundleAction = { click: () => { bundleClicks += 1; } };
    const documentRef = {
        body: { dataset: { profilesTemplateKind: "settings" } },
        createElement: (tagName) => createFakeElement(tagName),
        getElementById: (id) => id === "all-settings-list-panel" ? listPanel : null,
        querySelector: (selector) => selector === '[data-settings-target="preference-bundle:proxy_bundle"]'
            ? bundleAction
            : null,
    };
    const input = createFakeElement("input");
    input.value = "proxy";
    const results = createFakeElement("div");
    const clear = createFakeElement("button");
    const meta = createFakeElement("div");
    const scopeElement = createFakeElement("div");
    const scopeButtons = ["all", "review", "configured", "catalog"].map((scope) => {
        const button = createFakeElement("button");
        button.dataset.settingsSearchScope = scope;
        return button;
    });
    const routeState = {
        activeMode: "review",
        searchQuery: "",
        focusedTarget: "",
        setSearchQuery(query) {
            this.searchQuery = query;
        },
        setFocusedTarget(target) {
            this.focusedTarget = target;
        },
        getSnapshot() {
            return { activeMode: this.activeMode };
        },
    };
    const translations = {
        "profiles.settings_search_hint": "Hint",
        "profiles.settings_search_empty": "Empty",
        "profiles.settings_search_match_one": "One {count}",
        "profiles.settings_search_match_many": "Many {count}",
        "profiles.settings_search_group_configured": "Configured settings",
        "profiles.settings_search_group_available_policies": "Available policies",
        "profiles.settings_search_group_preferences": "Preferences",
        "profiles.settings_search_group_actions": "Actions",
        "profiles.settings_search_scope_all": "All",
        "profiles.settings_search_scope_review": "Review",
        "profiles.settings_search_scope_configured": "Configured",
        "profiles.settings_search_scope_catalog": "Catalog",
        "profiles.settings_list_state_configured": "Configured",
        "profiles.settings_list_state_available": "Available",
        "profiles.settings_list_value_not_configured": "Not configured",
        "profiles.settings_filter_guided_covered": "Guided",
        "profiles.settings_filter_all_settings_only": "All settings",
        "profiles.settings_filter_invalid": "Invalid",
        "profiles.settings_filter_deprecated": "Deprecated",
        "profiles.settings_filter_raw": "Raw",
        "profiles.settings_filter_unknown": "Unknown",
        "profiles.wizard_settings_search_step": "Step",
        "profiles.wizard_settings_search_kind_control": "Control",
        "profiles.wizard_settings_search_kind_preferences_section": "Preferences section",
        "profiles.wizard_settings_search_kind_preference_preset": "Preference preset",
        "profiles.wizard_settings_search_kind_preference_bundle": "Preference bundle",
        "profiles.wizard_settings_search_kind_known_preference": "Known preference",
        "profiles.wizard_settings_search_kind_search_preset": "Search preset",
        "profiles.wizard_settings_search_kind_policy_blueprint": "Schema policy",
        "profiles.wizard_settings_search_kind_all_settings_policy": "Policy setting",
        "profiles.wizard_settings_search_kind_all_settings_preference": "Managed preference",
    };
    const translate = (key, fallback = "") => translations[key] || fallback || key;
    const openedTargets = [];
    const detailPanel = createFakeElement("section");
    const search = createSearch({
        documentRef,
        elements: {
            wizardSettingsSearchInputEl: input,
            wizardSettingsSearchMetaEl: meta,
            wizardSettingsSearchResultsEl: results,
            wizardSettingsSearchClearEl: clear,
            wizardSettingsSearchScopeEl: scopeElement,
            wizardSettingsSearchScopeButtons: scopeButtons,
        },
        dependencies: {
            t: translate,
            escapeHtml: (value) => String(value || ""),
            humanizeIdentifier: (value) => String(value || "").replace(/([A-Z])/g, " $1"),
            normalizeSearchText: (value) => String(value || "").toLowerCase(),
            setWizardStep: () => {},
            findAllSettingsEntryTarget: (target) => {
                openedTargets.push(target);
                return detailPanel;
            },
            getAllSettingsSearchEntries: () => [
                {
                    id: "Proxy",
                    label: "Proxy",
                    kind: "policy",
                    kindLabel: "Policy",
                    categoryId: "browser-access",
                    categoryLabel: "Browser access",
                    configured: true,
                    value: "system",
                    attentionFlags: { reviewRequired: true },
                    target: "policy:Proxy",
                },
                {
                    id: "ProxyAvailable",
                    label: "Proxy available",
                    kind: "policy",
                    kindLabel: "Policy",
                    categoryId: "browser-access",
                    categoryLabel: "Browser access",
                    configured: false,
                    value: "Not configured",
                    target: "policy:ProxyAvailable",
                },
                {
                    id: "browser.proxy.type",
                    label: "browser.proxy.type",
                    kind: "preference",
                    kindLabel: "Managed preference",
                    categoryId: "privacy-security",
                    categoryLabel: "Security & privacy",
                    configured: true,
                    value: "locked",
                    target: "known-preference:browser.proxy.type",
                    editor: { preferenceSectionId: "network" },
                },
            ],
        },
        state: { allSettingsRouteState: routeState },
        wizardSettingsCatalog: {
            sections: [{
                id: "network",
                ui_maps: {
                    main: [{ id: "proxy", label_key: "area.proxy", fallback: "Proxy" }],
                },
                ui_controls: {
                    main: [
                        {
                            label_key: "control.proxy",
                            fallback: "Proxy",
                            area_id: "proxy",
                            target: "policy:Proxy",
                        },
                        {
                            label_key: "control.proxy.mode",
                            fallback: "Proxy mode action",
                            area_id: "proxy",
                            target: "policy:ProxyMode",
                        },
                    ],
                },
            }],
        },
        wizardSearchSectionSteps: {
            network: { step: 2, key: "step.network", fallback: "Network" },
            "browser-access": { step: 0, key: "category.browser", fallback: "Browser access" },
            "privacy-security": { step: 0, key: "category.privacy", fallback: "Security & privacy" },
        },
        settingsTargetAliases: {
            "policy:Proxy": "all-settings-entry:policy:Proxy",
        },
    });

    search.renderResults();

    assert.deepEqual(
        results.children.map((child) => child.dataset.settingsSearchGroup),
        ["configured_settings", "available_policies", "preferences", "actions"],
    );
    const targets = resultTargets(results);
    assert.equal(targets.filter((target) => target === "all-settings-entry:policy:Proxy").length, 1);
    assert.ok(targets.includes("all-settings-entry:policy:ProxyAvailable"));
    assert.ok(targets.includes("all-settings-entry:preference:browser.proxy.type"));
    assert.ok(targets.includes("policy:ProxyMode"));
    assert.equal(results.hidden, false);
    assert.match(meta.textContent, new RegExp(String(targets.length)));
    assert.equal(scopeElement.hidden, false);
    assert.equal(scopeButtons[0].state.classes["is-active"], true);

    const firstResult = results.querySelector("[data-settings-search-target]");
    const arrowDownEvent = {
        key: "ArrowDown",
        prevented: false,
        preventDefault() { this.prevented = true; },
    };
    input.emit("keydown", arrowDownEvent);
    assert.equal(arrowDownEvent.prevented, true);
    assert.equal(firstResult.state.focused, true);

    const enterEvent = {
        key: "Enter",
        prevented: false,
        preventDefault() { this.prevented = true; },
    };
    input.emit("keydown", enterEvent);
    assert.equal(enterEvent.prevented, true);
    assert.equal(openedTargets.at(-1), "all-settings-entry:policy:Proxy");
    assert.equal(routeState.focusedTarget, "all-settings-entry:policy:Proxy");
    assert.equal(detailPanel.state.scrolled, true);

    scopeButtons.find((button) => button.dataset.settingsSearchScope === "review").click();
    assert.equal(routeState.getSnapshot().activeMode, "review");
    assert.equal(
        scopeButtons.find((button) => button.dataset.settingsSearchScope === "review")
            .state.classes["is-active"],
        true,
    );
    assert.deepEqual(resultTargets(results), ["all-settings-entry:policy:Proxy"]);

    scopeButtons.find((button) => button.dataset.settingsSearchScope === "configured").click();
    const configuredTargets = resultTargets(results);
    assert.ok(configuredTargets.includes("all-settings-entry:policy:Proxy"));
    assert.ok(configuredTargets.includes("all-settings-entry:preference:browser.proxy.type"));
    assert.ok(!configuredTargets.includes("all-settings-entry:policy:ProxyAvailable"));
    assert.ok(!configuredTargets.includes("policy:ProxyMode"));

    scopeButtons.find((button) => button.dataset.settingsSearchScope === "catalog").click();
    const catalogTargets = resultTargets(results);
    assert.ok(catalogTargets.includes("all-settings-entry:policy:ProxyAvailable"));
    assert.ok(!catalogTargets.includes("policy:ProxyMode"));

    assert.equal(search.findTarget("policy:Proxy"), detailPanel);
    assert.equal(openedTargets.at(-1), "all-settings-entry:policy:Proxy");
    assert.equal(search.findTarget("known-preference:browser.proxy.type"), detailPanel);
    assert.equal(openedTargets.at(-1), "all-settings-entry:preference:browser.proxy.type");
    assert.equal(search.findTarget("pref-section:network"), detailPanel);
    assert.equal(openedTargets.at(-1), "all-settings-entry:preference:browser.proxy.type");
    assert.equal(search.findTarget("preference-bundle:proxy_bundle"), listPanel);
    assert.equal(bundleClicks, 1);
});
