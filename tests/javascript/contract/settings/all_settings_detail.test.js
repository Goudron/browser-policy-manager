import assert from "node:assert/strict";
import test from "node:test";

import { create as createDetail } from "../../../../app/static/profiles_all_settings_detail.js";
import { create as createSchemaActions } from "../../../../app/static/profiles_schema_shell_actions.js";
import { createFakeElement, eventTargetFor } from "../../support/dom_harness.js";

const translations = {
    "profiles.settings_preferences_add": "Add preference",
    "profiles.settings_preferences_title": "Preferences",
    "profiles.settings_list_kind_policy": "Policy",
    "profiles.settings_list_kind_preference": "Managed preference",
    "profiles.settings_list_state_configured": "Configured",
    "profiles.settings_list_state_available": "Available",
    "profiles.settings_list_value_not_configured": "Not configured",
    "profiles.settings_source_baseline": "Baseline",
    "profiles.settings_source_cis": "CIS",
    "profiles.settings_source_manual": "Manual",
    "profiles.settings_source_imported": "Imported",
    "profiles.settings_source_raw": "Raw",
    "profiles.settings_review_source_unknown": "Unknown",
    "profiles.settings_review_source_catalog": "Catalog",
    "profiles.settings_filter_guided_covered": "Guided-covered",
    "profiles.settings_filter_all_settings_only": "All settings only",
    "profiles.settings_filter_invalid": "Invalid",
    "profiles.settings_filter_deprecated": "Deprecated",
    "profiles.settings_filter_raw": "Raw fallback",
    "profiles.settings_filter_unknown": "Unknown",
    "profiles.settings_detail_empty": "Select a setting to inspect and edit it.",
    "profiles.settings_detail_current_value": "Current value",
    "profiles.settings_detail_open_location": "Open in catalog",
    "profiles.settings_detail_reset_editor": "Reset editor",
    "profiles.settings_detail_remove": "Remove from profile",
    "profiles.settings_detail_apply": "Apply changes",
    "profiles.settings_detail_applied": "Setting updated.",
    "profiles.settings_detail_removed": "Setting removed from the profile.",
    "profiles.settings_detail_apply_failed": "Could not update the setting: {detail}",
    "profiles.settings_detail_raw_value": "Raw value",
    "profiles.settings_detail_raw_json_error": "Raw values must be valid JSON.",
    "profiles.settings_detail_validation_title": "Validation issues",
    "profiles.settings_detail_validation_clear": "No validation issues for this setting.",
    "profiles.settings_detail_validation_unknown": "Unknown validation issue.",
    "profiles.settings_detail_meta_kind": "Kind",
    "profiles.settings_detail_meta_category": "Category",
    "profiles.settings_detail_meta_source": "Source",
    "profiles.settings_detail_meta_location": "Location",
    "profiles.settings_detail_meta_widget": "Editor",
    "profiles.settings_detail_meta_complexity": "Complexity",
    "profiles.settings_detail_meta_support": "Coverage",
    "profiles.settings_detail_support_mapped": "Mapped",
    "profiles.settings_detail_support_fallback": "Raw fallback",
    "profiles.wizard_shell_widget_toggle": "Toggle",
    "profiles.wizard_shell_meta_basic": "Basic",
    "profiles.wizard_shell_meta_advanced": "Advanced",
    "profiles.wizard_preferences_field_name": "Name",
    "profiles.wizard_preferences_name_placeholder": "Preference name",
    "profiles.wizard_preferences_field_status": "Status",
    "profiles.wizard_preferences_field_type": "Type",
    "profiles.wizard_preferences_field_value": "Value",
    "profiles.wizard_preferences_status_default": "Default",
    "profiles.wizard_preferences_status_locked": "Locked",
    "profiles.wizard_preferences_status_user": "User",
    "profiles.wizard_preferences_status_clear": "Clear",
    "profiles.wizard_preferences_type_auto_option": "Auto",
    "profiles.wizard_preferences_type_boolean": "Boolean",
    "profiles.wizard_preferences_type_number": "Number",
    "profiles.wizard_preferences_type_string": "String",
    "profiles.wizard_preferences_boolean_true": "True",
    "profiles.wizard_preferences_boolean_false": "False",
    "profiles.wizard_preferences_error_name": "Preference name required",
    "profiles.wizard_preferences_error_value": "Preference value required",
};

const t = (key) => translations[key] || key;
const escapeHtml = (value) => String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

function detailDependencies(overrides = {}) {
    return {
        t,
        escapeHtml,
        normalizePreferenceName: (value) => String(value || "").trim(),
        serializePreferenceValue: (value) => String(value ?? ""),
        serializePreferenceSelectValue: (value) => String(value ?? ""),
        parsePreferenceValue: (value) => ({ ok: true, value }),
        fromEditorValue: (value) => value,
        toEditorValue: (value) => JSON.stringify(value),
        renderSchemaPolicyEditorCard: () => "",
        renderSchemaPolicyReviewState: () => {},
        onDocumentChange: () => {},
        setStatus: () => {},
        ...overrides,
    };
}

function preferenceEntry(overrides = {}) {
    return {
        id: "browser.startup.homepage",
        label: "browser.startup.homepage",
        kind: "preference",
        kindLabel: "Managed preference",
        categoryLabel: "Home & startup",
        configured: true,
        guided: false,
        target: "known-preference:browser.startup.homepage",
        sources: ["manual"],
        sourceDetails: { path: ["Preferences", "browser.startup.homepage"] },
        issues: [],
        editor: {
            knownPreference: { pref: "browser.startup.homepage", type: "string" },
        },
        ...overrides,
    };
}

test("detail renders policy and preference context, validation, and actions", () => {
    const sourceData = {
        DisableTelemetry: true,
        Preferences: {
            "browser.startup.homepage": {
                Status: "locked",
                Type: "string",
                Value: "https://example.test",
            },
        },
    };
    const panel = createFakeElement("section");
    let activeMode = "review";
    const detail = createDetail({
        documentRef: {},
        elements: { allSettingsDetailPanelEl: panel },
        dependencies: detailDependencies({
            readWizardSchemaSource: () => ({ ok: true, data: sourceData }),
            getAllSettingsMode: () => activeMode,
        }),
        state: { getEditor: () => null, setCurrentRaw: () => {} },
    });
    const policy = {
        id: "DisableTelemetry",
        label: "DisableTelemetry",
        kind: "policy",
        kindLabel: "Policy",
        categoryLabel: "Security & privacy",
        configured: true,
        guided: true,
        target: "policy:DisableTelemetry",
        sources: ["baseline", "cis"],
        sourceDetails: { path: ["DisableTelemetry"] },
        issues: [{ path: ["DisableTelemetry"], message: "Must be boolean" }],
        schemaItem: { widget: "toggle", complexity: "basic", support_level: "mapped" },
    };

    detail.render(policy);
    assert.equal(panel.dataset.settingsDetailKind, "policy");
    assert.equal(panel.dataset.settingsDetailId, "DisableTelemetry");
    assert.match(panel.innerHTML, /data-settings-detail-source/);
    assert.match(panel.innerHTML, /Baseline, CIS/);
    assert.match(panel.innerHTML, /data-settings-detail-location/);
    assert.match(panel.innerHTML, /Current value/);
    assert.match(panel.innerHTML, />true</);
    assert.match(panel.innerHTML, /Validation issues/);
    assert.match(panel.innerHTML, /Must be boolean/);
    assert.doesNotMatch(panel.innerHTML, /data-settings-search-target="policy:DisableTelemetry"/);
    assert.match(panel.innerHTML, /data-settings-detail-reset/);
    assert.match(panel.innerHTML, /data-settings-detail-remove/);
    assert.match(panel.innerHTML, /data-settings-detail-apply-raw/);

    activeMode = "catalog";
    detail.render(policy);
    assert.match(panel.innerHTML, /data-settings-search-target="policy:DisableTelemetry"/);

    activeMode = "review";
    detail.render(preferenceEntry());
    assert.equal(panel.dataset.settingsDetailKind, "preference");
    assert.match(panel.innerHTML, /Manual/);
    assert.match(panel.innerHTML, /Preferences\.browser\.startup\.homepage/);
    assert.match(panel.innerHTML, /No validation issues for this setting\./);
    assert.match(panel.innerHTML, /data-settings-detail-apply-preference/);
    assert.match(panel.innerHTML, /data-settings-detail-reset/);
    assert.match(panel.innerHTML, /data-settings-detail-remove/);
});

test("applying a detail preference updates the editor document and notifies inventory", () => {
    const controls = {
        status: { value: "locked" },
        type: { value: "string" },
        input: { value: "https://new.example.test", hidden: false, disabled: false },
        select: { value: "", hidden: true, disabled: true },
    };
    const preferenceEditor = {
        querySelector(selector) {
            return {
                "[data-settings-detail-pref-status]": controls.status,
                "[data-settings-detail-pref-type]": controls.type,
                "[data-settings-detail-pref-value-input]": controls.input,
                "[data-settings-detail-pref-value-select]": controls.select,
            }[selector] || null;
        },
    };
    const panel = createFakeElement("section", {
        query: { "[data-settings-detail-preference-editor]": preferenceEditor },
    });
    let editorValue = JSON.stringify({
        Preferences: {
            "browser.startup.homepage": {
                Status: "default",
                Type: "string",
                Value: "https://old.example.test",
            },
        },
    });
    const changedDocuments = [];
    const detail = createDetail({
        documentRef: { getElementById: (id) => id === "mode" ? { value: "json" } : null },
        elements: { allSettingsDetailPanelEl: panel },
        dependencies: detailDependencies({
            fromEditorValue: (value) => JSON.parse(value || "{}"),
            readWizardSchemaSource: () => ({ ok: true, data: JSON.parse(editorValue) }),
            onDocumentChange: (document) => changedDocuments.push(document),
        }),
        state: {
            getEditor: () => ({
                getValue: () => editorValue,
                setValue: (value) => { editorValue = value; },
            }),
            setCurrentRaw: () => {},
        },
    });

    detail.render(preferenceEntry());
    panel.emit("click", { target: eventTargetFor("[data-settings-detail-apply-preference]") });

    assert.equal(changedDocuments.length, 1);
    assert.equal(
        changedDocuments[0].Preferences["browser.startup.homepage"].Value,
        "https://new.example.test",
    );
    assert.equal(JSON.parse(editorValue).Preferences["browser.startup.homepage"].Status, "locked");
});

test("schema detail cards notify document refresh only inside the detail panel", () => {
    let editorValue = JSON.stringify({ DisableTelemetry: false });
    const changedDocuments = [];
    const actions = createSchemaActions({
        documentRef: { getElementById: (id) => id === "mode" ? { value: "json" } : null },
        dependencies: {
            t: (key) => key,
            escapeHtml,
            fromEditorValue: (value) => JSON.parse(value || "{}"),
            toEditorValue: (value) => JSON.stringify(value),
            setStatus: () => {},
            parseBooleanSelectValue: (value) => value === "true" ? true : value === "false" ? false : null,
            onDocumentChange: (document) => changedDocuments.push(document),
        },
        state: {
            getEditor: () => ({
                getValue: () => editorValue,
                setValue: (value) => { editorValue = value; },
            }),
            setCurrentRaw: () => {},
        },
        helpers: {
            parseSchemaPolicyFieldValue: () => ({ ok: true, hasValue: false }),
            readSchemaNestedFieldSpecs: () => [],
            renderWizardSchemaNestedArrayRow: () => "",
            renderWizardSchemaNestedDictionaryRow: () => "",
        },
    });
    const card = (inDetail) => ({
        dataset: { schemaPolicyId: "DisableTelemetry", schemaPolicyKind: "boolean-select" },
        querySelector: (selector) => selector === '[data-schema-policy-field="__value__"]'
            ? { value: "true" }
            : null,
        closest: (selector) => inDetail && selector === "#all-settings-detail-panel" ? {} : null,
    });

    actions.applySchemaPolicyFromCard(card(true));
    assert.equal(changedDocuments.length, 1);
    assert.equal(changedDocuments[0].DisableTelemetry, true);
    assert.equal(JSON.parse(editorValue).DisableTelemetry, true);

    actions.applySchemaPolicyFromCard(card(false));
    assert.equal(changedDocuments.length, 1);
});

test("detail reset, removal, and new-preference workflow preserve document state", () => {
    let sourceData = { DisableTelemetry: true };
    const changedDocuments = [];
    const statuses = [];
    const nameInput = createFakeElement("input");
    nameInput.value = "browser.new.pref";
    const controls = {
        status: { value: "locked" },
        type: { value: "string" },
        input: { value: "enabled", hidden: false, disabled: false },
        select: { value: "", hidden: true, disabled: true },
    };
    const preferenceEditor = {
        querySelector(selector) {
            return {
                "[data-settings-detail-pref-status]": controls.status,
                "[data-settings-detail-pref-type]": controls.type,
                "[data-settings-detail-pref-value-input]": controls.input,
                "[data-settings-detail-pref-value-select]": controls.select,
            }[selector] || null;
        },
    };
    const panel = createFakeElement("section", {
        query: {
            "[data-settings-detail-pref-name]": nameInput,
            "[data-settings-detail-preference-editor]": preferenceEditor,
        },
    });
    const addPreference = createFakeElement("button");
    const detail = createDetail({
        documentRef: {},
        elements: {
            allSettingsDetailPanelEl: panel,
            allSettingsAddPreferenceEl: addPreference,
        },
        dependencies: detailDependencies({
            readWizardSchemaSource: () => ({ ok: true, data: sourceData }),
            onDocumentChange: (document) => {
                sourceData = document;
                changedDocuments.push(structuredClone(document));
            },
            setStatus: (message, tone) => statuses.push([message, tone]),
        }),
        state: {
            getEditor: () => null,
            setCurrentRaw: (document) => { sourceData = document; },
        },
    });

    detail.render({
        id: "DisableTelemetry",
        label: "DisableTelemetry",
        kind: "policy",
        kindLabel: "Policy",
        categoryLabel: "Security & privacy",
        configured: true,
        guided: false,
        target: "policy:DisableTelemetry",
        sources: ["manual"],
        sourceDetails: { path: ["DisableTelemetry"] },
        issues: [],
        schemaItem: null,
    });
    panel.innerHTML = "dirty editor";
    panel.emit("click", { target: eventTargetFor("[data-settings-detail-reset]") });
    assert.match(panel.innerHTML, /DisableTelemetry/);
    assert.match(panel.innerHTML, /data-settings-detail-raw-value/);

    panel.emit("click", { target: eventTargetFor("[data-settings-detail-remove]") });
    assert.equal(changedDocuments.length, 1);
    assert.equal(changedDocuments[0].DisableTelemetry, undefined);
    assert.deepEqual(statuses.at(-1), ["Setting removed from the profile.", "info"]);

    addPreference.click();
    assert.equal(nameInput.state.focused, true);
    assert.match(panel.innerHTML, /data-settings-detail-new="true"/);

    panel.emit("click", { target: eventTargetFor("[data-settings-detail-apply-preference]") });
    assert.equal(changedDocuments.length, 2);
    assert.equal(changedDocuments[1].Preferences["browser.new.pref"].Status, "locked");
    assert.equal(changedDocuments[1].Preferences["browser.new.pref"].Value, "enabled");
    assert.match(panel.innerHTML, /data-settings-detail-new="false"/);
    assert.doesNotMatch(
        panel.innerHTML,
        /data-settings-search-target="known-preference:browser\.new\.pref"/,
    );
});
