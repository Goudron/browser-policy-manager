import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";

import { createFakeElement } from "./dom_harness.js";

const BASE_TRANSLATIONS = {
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
    "profiles.settings_list_value_object": "{count} keys",
    "profiles.settings_list_value_array": "{count} items",
    "profiles.settings_list_summary": "{total} entries / {configured} configured / {policies} policies / {preferences} preferences",
    "profiles.settings_list_summary_filtered": "{visible} shown of {total} entries / {configured} configured / {policies} policies / {preferences} preferences",
    "profiles.settings_list_empty": "Empty",
    "profiles.settings_list_filtered_empty": "Filtered empty",
    "profiles.settings_list_budget": "Showing {visible} of {total}.",
    "profiles.settings_list_window": "Showing {from}-{to} of {total}.",
    "profiles.settings_list_show_more": "Show {count} more",
    "profiles.settings_list_show_less": "Show fewer",
    "profiles.settings_list_previous_page": "Previous",
    "profiles.settings_list_next_page": "Next",
    "profiles.settings_review_summary_attention": "Review: {count}",
    "profiles.settings_review_summary_clear": "Clear",
    "profiles.settings_review_open": "Open review",
    "profiles.settings_review_clear": "No items",
    "profiles.settings_review_success_title": "Nothing needs review",
    "profiles.settings_review_success_body": "Nothing to review.",
    "profiles.settings_review_success_configured": "Configured",
    "profiles.settings_review_success_catalog": "Catalog",
    "profiles.settings_review_empty_group": "No entries in this queue.",
    "profiles.settings_review_more": "+{count} more",
    "profiles.settings_review_source_cis": "CIS",
    "profiles.settings_review_source_baseline": "Baseline",
    "profiles.settings_review_source_manual": "Manual",
    "profiles.settings_review_source_imported": "Imported",
    "profiles.settings_review_source_unknown": "Unknown",
    "profiles.settings_review_source_raw": "Raw",
    "profiles.settings_review_source_catalog": "Catalog",
    "profiles.settings_review_path": "Path: {path}",
    "profiles.settings_review_reason_attention": "Needs review",
    "profiles.settings_review_reason_cis_manual": "CIS {ids}: {reason}",
    "profiles.settings_review_reason_cis_manual_no_ids": "CIS manual review: {reason}",
    "profiles.settings_review_reason_cis": "CIS recommendations: {ids}",
    "profiles.settings_review_reason_cis_empty": "CIS decision needs review",
    "profiles.settings_review_reason_invalid": "Validation issues: {count}",
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
    "profiles.settings_configured_domain_configured": "configured",
    "profiles.settings_configured_domain_attention": "attention",
    "profiles.settings_configured_domain_available": "available",
    "profiles.settings_source_baseline": "Baseline",
    "profiles.settings_source_cis": "CIS",
    "profiles.settings_source_manual": "Manual",
    "profiles.settings_source_imported": "Imported",
    "profiles.settings_source_raw": "Raw",
};

let cachedFixture;

function loadAllSettingsFixture() {
    if (!cachedFixture) {
        const fixtureUrl = new URL("../fixtures/all_settings.json.gz", import.meta.url);
        cachedFixture = JSON.parse(gunzipSync(readFileSync(fixtureUrl)).toString("utf8"));
    }
    return cachedFixture;
}

function translate(overrides = {}) {
    const labels = { ...BASE_TRANSLATIONS, ...overrides };
    return (key, fallback = "") => labels[key] || fallback || key;
}

function createListElement() {
    const element = createFakeElement("div");
    let rows = [];
    let html = "";
    Object.defineProperty(element, "innerHTML", {
        configurable: true,
        get: () => html,
        set(value) {
            html = String(value || "");
            rows = Array.from(
                html.matchAll(
                    /data-settings-entry-select[\s\S]*?data-settings-entry-id="([^"]+)"[\s\S]*?data-settings-entry-kind="([^"]+)"/g,
                ),
                (match) => ({
                    hidden: false,
                    dataset: { settingsEntryId: match[1], settingsEntryKind: match[2] },
                }),
            );
        },
    });
    element.querySelectorAll = (selector) => (
        selector === "[data-settings-entry-id]" || selector === "[data-settings-entry-select]"
            ? rows
            : []
    );
    element.renderedRows = () => rows.length;
    element.visibleRows = () => rows.filter((row) => !row.hidden).length;
    element.renderedHelpLinks = () => Array.from(
        html.matchAll(/data-all-settings-help-target="([^"]+)"/g),
    ).length;
    return element;
}

function createBudgetElement() {
    const element = createFakeElement("div");
    element.hidden = true;
    element.currentGroup = () => (
        element.innerHTML.match(/data-settings-list-budget-toggle="([^"]+)"/) || []
    )[1] || "";
    element.clickAction = (actionName = "") => element.emit("click", {
        target: {
            closest: (selector) => selector === "[data-settings-list-budget-toggle]"
                ? {
                    disabled: false,
                    dataset: {
                        settingsListBudgetToggle: element.currentGroup(),
                        ...(actionName ? { settingsListBudgetAction: actionName } : {}),
                    },
                }
                : null,
        },
    });
    return element;
}

function createFilterButton(dataset) {
    const countElement = createFakeElement("span");
    const button = createFakeElement("button");
    button.dataset = dataset;
    button.querySelector = (selector) => (
        selector === "[data-settings-source-filter-count]"
        || selector === "[data-settings-list-filter-count]"
            ? countElement
            : null
    );
    button.countElement = countElement;
    return button;
}

function installListWindow(context) {
    const previousWindow = globalThis.window;
    const previousElement = globalThis.Element;
    globalThis.Element = class {};
    globalThis.window = {
        requestAnimationFrame(callback) {
            callback();
        },
    };
    context.after(() => {
        if (previousWindow === undefined) delete globalThis.window;
        else globalThis.window = previousWindow;
        if (previousElement === undefined) delete globalThis.Element;
        else globalThis.Element = previousElement;
    });
}

export {
    BASE_TRANSLATIONS,
    createBudgetElement,
    createFilterButton,
    createListElement,
    installListWindow,
    loadAllSettingsFixture,
    translate,
};
