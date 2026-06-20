from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from tests.web_profiles_page_helpers import static_source

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def test_all_settings_detail_primary_editor_contract_is_wired():
    detail_source = static_source("profiles_all_settings_detail.js")
    list_source = static_source("profiles_all_settings_list.js")
    bootstrap_source = static_source("profiles_bootstrap_core.js")
    runtime_source = static_source("profiles_runtime.js")

    for snippet in (
        "function renderEntryMetadata(entry, extraRows = [])",
        "function sourceSummary(entry)",
        "function locationSummary(entry)",
        "onDocumentChange(normalized);",
        "data-settings-detail-primary-focus",
        "data-settings-detail-${escapeHtml(key)}",
        "profiles.settings_detail_meta_source",
        "profiles.settings_detail_meta_location",
        "renderEntryMetadata(entry)",
        "data-settings-detail-reset",
        "data-settings-detail-remove",
        "data-settings-detail-apply-raw",
        "data-settings-detail-apply-preference",
        'getAllSettingsMode = () => "review"',
        'getAllSettingsMode() === "catalog"',
    ):
        assert snippet in detail_source

    assert "routeState.setSelectedEntryKey(entryKey(" in list_source
    assert "function revealTargetForSelectedRow(row)" in list_source
    assert 'documentRef.getElementById("all-settings-detail-panel") || row' in list_source
    assert "onSelectionChange: (entry) => allSettingsDetail.render(entry)" in bootstrap_source
    assert "findAllSettingsEntryTarget: (target) => allSettingsList.findTarget(target)" in bootstrap_source
    assert "onDocumentChange: (...args) => handleAllSettingsDocumentChange(...args)" in bootstrap_source
    assert "getAllSettingsMode: () => allSettingsRouteState.getSnapshot().activeMode" in bootstrap_source
    assert "[data-settings-detail-primary-focus], .all-settings-detail-editor [data-schema-policy-field]" in runtime_source


def test_all_settings_detail_runtime_renders_context_value_validation_and_editor_actions():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const assert = require("assert");
        global.document = {{}};
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_detail.js"}", "utf8"));

        function fakePanel() {{
            return {{
                dataset: {{}},
                _innerHTML: "",
                listeners: {{}},
                addEventListener(eventName, handler) {{
                    this.listeners[eventName] = handler;
                }},
                querySelectorAll(selector) {{
                    return selector === "[data-schema-policy-card]" ? [] : [];
                }},
                querySelector() {{
                    return null;
                }},
                get innerHTML() {{
                    return this._innerHTML;
                }},
                set innerHTML(value) {{
                    this._innerHTML = String(value);
                }},
            }};
        }}

        const translations = {{
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
            "profiles.settings_detail_apply_failed": "Could not update the setting: {{detail}}",
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
        }};
        const t = (key) => translations[key] || key;
        const escapeHtml = (value) => String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
        const sourceData = {{
            DisableTelemetry: true,
            Preferences: {{
                "browser.startup.homepage": {{
                    Status: "locked",
                    Type: "string",
                    Value: "https://example.test",
                }},
            }},
        }};
        const panel = fakePanel();
        let activeMode = "review";
        const detail = window.BPMProfilesAllSettingsDetail.create({{
            elements: {{ allSettingsDetailPanelEl: panel }},
            dependencies: {{
                t,
                escapeHtml,
                normalizePreferenceName: (value) => String(value || "").trim(),
                serializePreferenceValue: (value) => String(value ?? ""),
                serializePreferenceSelectValue: (value) => String(value ?? ""),
                parsePreferenceValue: (value) => ({{ ok: true, value }}),
                fromEditorValue: (value) => value,
                toEditorValue: (value) => JSON.stringify(value),
                readWizardSchemaSource: () => ({{ ok: true, data: sourceData }}),
                renderSchemaPolicyEditorCard: () => "",
                renderSchemaPolicyReviewState: () => {{}},
                onDocumentChange: () => {{}},
                setStatus: () => {{}},
                getAllSettingsMode: () => activeMode,
            }},
            state: {{
                getEditor: () => null,
                setCurrentRaw: () => {{}},
            }},
        }});

        detail.render({{
            id: "DisableTelemetry",
            label: "DisableTelemetry",
            kind: "policy",
            kindLabel: "Policy",
            categoryLabel: "Security & privacy",
            configured: true,
            guided: true,
            target: "policy:DisableTelemetry",
            sources: ["baseline", "cis"],
            sourceDetails: {{ path: ["DisableTelemetry"] }},
            issues: [{{ path: ["DisableTelemetry"], message: "Must be boolean" }}],
            schemaItem: {{ widget: "toggle", complexity: "basic", support_level: "mapped" }},
        }});
        assert.equal(panel.dataset.settingsDetailKind, "policy");
        assert.equal(panel.dataset.settingsDetailId, "DisableTelemetry");
        assert(panel.innerHTML.includes("data-settings-detail-source"));
        assert(panel.innerHTML.includes("Baseline, CIS"));
        assert(panel.innerHTML.includes("data-settings-detail-location"));
        assert(panel.innerHTML.includes("DisableTelemetry"));
        assert(panel.innerHTML.includes("Current value"));
        assert(panel.innerHTML.includes(">true<"));
        assert(panel.innerHTML.includes("Validation issues"));
        assert(panel.innerHTML.includes("Must be boolean"));
        assert(!panel.innerHTML.includes("data-settings-search-target=\\"policy:DisableTelemetry\\""));
        assert(panel.innerHTML.includes("data-settings-detail-reset"));
        assert(panel.innerHTML.includes("data-settings-detail-remove"));
        assert(panel.innerHTML.includes("data-settings-detail-apply-raw"));

        activeMode = "catalog";
        detail.render({{
            id: "DisableTelemetry",
            label: "DisableTelemetry",
            kind: "policy",
            kindLabel: "Policy",
            categoryLabel: "Security & privacy",
            configured: true,
            guided: true,
            target: "policy:DisableTelemetry",
            sources: ["baseline", "cis"],
            sourceDetails: {{ path: ["DisableTelemetry"] }},
            issues: [{{ path: ["DisableTelemetry"], message: "Must be boolean" }}],
            schemaItem: {{ widget: "toggle", complexity: "basic", support_level: "mapped" }},
        }});
        assert(panel.innerHTML.includes("data-settings-search-target=\\"policy:DisableTelemetry\\""));
        activeMode = "review";

        detail.render({{
            id: "browser.startup.homepage",
            label: "browser.startup.homepage",
            kind: "preference",
            kindLabel: "Managed preference",
            categoryLabel: "Home & startup",
            configured: true,
            guided: false,
            target: "known-preference:browser.startup.homepage",
            sources: ["manual"],
            sourceDetails: {{ path: ["Preferences", "browser.startup.homepage"] }},
            issues: [],
            editor: {{
                knownPreference: {{ pref: "browser.startup.homepage", type: "string" }},
            }},
        }});
        assert.equal(panel.dataset.settingsDetailKind, "preference");
        assert(panel.innerHTML.includes("data-settings-detail-source"));
        assert(panel.innerHTML.includes("Manual"));
        assert(panel.innerHTML.includes("data-settings-detail-location"));
        assert(panel.innerHTML.includes("Preferences.browser.startup.homepage"));
        assert(panel.innerHTML.includes("No validation issues for this setting."));
        assert(panel.innerHTML.includes("data-settings-detail-apply-preference"));
        assert(panel.innerHTML.includes("data-settings-detail-reset"));
        assert(panel.innerHTML.includes("data-settings-detail-remove"));
        """
    )

    subprocess.run(["node", "-e", script], cwd=REPO_ROOT, check=True)


def test_all_settings_detail_preference_apply_notifies_inventory_and_search_refresh():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const assert = require("assert");
        global.document = {{}};
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_detail.js"}", "utf8"));

        const translations = {{
            "profiles.settings_list_kind_preference": "Managed preference",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_filter_all_settings_only": "All settings only",
            "profiles.settings_detail_current_value": "Current value",
            "profiles.settings_detail_open_location": "Open in catalog",
            "profiles.settings_detail_reset_editor": "Reset editor",
            "profiles.settings_detail_remove": "Remove from profile",
            "profiles.settings_detail_apply": "Apply changes",
            "profiles.settings_detail_applied": "Setting updated.",
            "profiles.settings_detail_removed": "Setting removed from the profile.",
            "profiles.settings_detail_apply_failed": "Could not update the setting: {{detail}}",
            "profiles.settings_detail_validation_clear": "No validation issues for this setting.",
            "profiles.settings_detail_meta_kind": "Kind",
            "profiles.settings_detail_meta_category": "Category",
            "profiles.settings_detail_meta_source": "Source",
            "profiles.settings_detail_meta_location": "Location",
            "profiles.settings_source_manual": "Manual",
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
        }};
        const t = (key) => translations[key] || key;
        const escapeHtml = (value) => String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
        const controls = {{
            status: {{ value: "locked" }},
            type: {{ value: "string" }},
            input: {{ value: "https://new.example.test", hidden: false, disabled: false }},
            select: {{ value: "", hidden: true, disabled: true }},
        }};
        const editorEl = {{
            querySelector(selector) {{
                if (selector === "[data-settings-detail-pref-status]") return controls.status;
                if (selector === "[data-settings-detail-pref-type]") return controls.type;
                if (selector === "[data-settings-detail-pref-value-input]") return controls.input;
                if (selector === "[data-settings-detail-pref-value-select]") return controls.select;
                return null;
            }},
        }};
        const panel = {{
            dataset: {{}},
            _innerHTML: "",
            listeners: {{}},
            addEventListener(eventName, handler) {{
                this.listeners[eventName] = handler;
            }},
            querySelector(selector) {{
                if (selector === "[data-settings-detail-preference-editor]") return editorEl;
                return null;
            }},
            querySelectorAll() {{
                return [];
            }},
            get innerHTML() {{
                return this._innerHTML;
            }},
            set innerHTML(value) {{
                this._innerHTML = String(value);
            }},
        }};
        const documentRef = {{
            getElementById: (id) => id === "mode" ? {{ value: "json" }} : null,
        }};
        let editorValue = JSON.stringify({{
            Preferences: {{
                "browser.startup.homepage": {{
                    Status: "default",
                    Type: "string",
                    Value: "https://old.example.test",
                }},
            }},
        }});
        const changedDocuments = [];
        const detail = window.BPMProfilesAllSettingsDetail.create({{
            documentRef,
            elements: {{ allSettingsDetailPanelEl: panel }},
            dependencies: {{
                t,
                escapeHtml,
                normalizePreferenceName: (value) => String(value || "").trim(),
                serializePreferenceValue: (value) => String(value ?? ""),
                serializePreferenceSelectValue: (value) => String(value ?? ""),
                parsePreferenceValue: (value) => ({{ ok: true, value }}),
                fromEditorValue: (value) => JSON.parse(value || "{{}}"),
                toEditorValue: (value) => JSON.stringify(value),
                readWizardSchemaSource: () => ({{ ok: true, data: JSON.parse(editorValue) }}),
                renderSchemaPolicyEditorCard: () => "",
                renderSchemaPolicyReviewState: () => {{}},
                onDocumentChange: (nextDocument) => changedDocuments.push(nextDocument),
                setStatus: () => {{}},
            }},
            state: {{
                getEditor: () => ({{
                    getValue: () => editorValue,
                    setValue: (value) => {{ editorValue = value; }},
                }}),
                setCurrentRaw: () => {{}},
            }},
        }});
        detail.render({{
            id: "browser.startup.homepage",
            label: "browser.startup.homepage",
            kind: "preference",
            kindLabel: "Managed preference",
            categoryLabel: "Home & startup",
            configured: true,
            guided: false,
            target: "known-preference:browser.startup.homepage",
            sources: ["manual"],
            sourceDetails: {{ path: ["Preferences", "browser.startup.homepage"] }},
            issues: [],
            editor: {{ knownPreference: {{ pref: "browser.startup.homepage", type: "string" }} }},
        }});
        panel.listeners.click({{
            target: {{
                closest(selector) {{
                    return selector === "[data-settings-detail-apply-preference]" ? {{}} : null;
                }},
            }},
        }});

        assert.equal(changedDocuments.length, 1);
        assert.equal(
            changedDocuments[0].Preferences["browser.startup.homepage"].Value,
            "https://new.example.test",
        );
        assert.equal(
            JSON.parse(editorValue).Preferences["browser.startup.homepage"].Status,
            "locked",
        );
        """
    )

    subprocess.run(["node", "-e", script], cwd=REPO_ROOT, check=True)


def test_schema_shell_detail_cards_notify_all_settings_refresh_after_apply():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const assert = require("assert");
        global.document = {{}};
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_schema_shell_actions.js"}", "utf8"));

        const documentRef = {{
            getElementById: (id) => id === "mode" ? {{ value: "json" }} : null,
        }};
        let editorValue = JSON.stringify({{ DisableTelemetry: false }});
        const changedDocuments = [];
        const actions = window.BPMProfilesSchemaShellActions.create({{
            documentRef,
            dependencies: {{
                t: (key) => key,
                escapeHtml: (value) => String(value ?? ""),
                fromEditorValue: (value) => JSON.parse(value || "{{}}"),
                toEditorValue: (value) => JSON.stringify(value),
                setStatus: () => {{}},
                parseBooleanSelectValue: (value) => value === "true" ? true : value === "false" ? false : null,
                onDocumentChange: (nextDocument) => changedDocuments.push(nextDocument),
            }},
            state: {{
                getEditor: () => ({{
                    getValue: () => editorValue,
                    setValue: (value) => {{ editorValue = value; }},
                }}),
                setCurrentRaw: () => {{}},
            }},
            helpers: {{
                parseSchemaPolicyFieldValue: () => ({{ ok: true, hasValue: false }}),
                readSchemaNestedFieldSpecs: () => [],
                renderWizardSchemaNestedArrayRow: () => "",
                renderWizardSchemaNestedDictionaryRow: () => "",
            }},
        }});

        function card(inDetail) {{
            return {{
                dataset: {{
                    schemaPolicyId: "DisableTelemetry",
                    schemaPolicyKind: "boolean-select",
                }},
                querySelector(selector) {{
                    if (selector === '[data-schema-policy-field="__value__"]') return {{ value: "true" }};
                    return null;
                }},
                closest(selector) {{
                    return inDetail && selector === "#all-settings-detail-panel" ? {{}} : null;
                }},
            }};
        }}

        actions.applySchemaPolicyFromCard(card(true));
        assert.equal(changedDocuments.length, 1);
        assert.equal(changedDocuments[0].DisableTelemetry, true);
        assert.equal(JSON.parse(editorValue).DisableTelemetry, true);

        actions.applySchemaPolicyFromCard(card(false));
        assert.equal(changedDocuments.length, 1);
        """
    )

    subprocess.run(["node", "-e", script], cwd=REPO_ROOT, check=True)


def test_all_settings_detail_remove_reset_and_new_preference_workflow():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const assert = require("assert");
        global.document = {{}};
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_all_settings_detail.js"}", "utf8"));

        const translations = {{
            "profiles.settings_preferences_add": "Add preference",
            "profiles.settings_preferences_title": "Preferences",
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Managed preference",
            "profiles.settings_list_state_configured": "Configured",
            "profiles.settings_list_state_available": "Available",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_filter_guided_covered": "Guided-covered",
            "profiles.settings_filter_all_settings_only": "All settings only",
            "profiles.settings_detail_current_value": "Current value",
            "profiles.settings_detail_open_location": "Open in catalog",
            "profiles.settings_detail_reset_editor": "Reset editor",
            "profiles.settings_detail_remove": "Remove from profile",
            "profiles.settings_detail_apply": "Apply changes",
            "profiles.settings_detail_applied": "Setting updated.",
            "profiles.settings_detail_removed": "Setting removed from the profile.",
            "profiles.settings_detail_apply_failed": "Could not update the setting: {{detail}}",
            "profiles.settings_detail_raw_value": "Raw value",
            "profiles.settings_detail_validation_clear": "No validation issues for this setting.",
            "profiles.settings_detail_meta_kind": "Kind",
            "profiles.settings_detail_meta_category": "Category",
            "profiles.settings_detail_meta_source": "Source",
            "profiles.settings_detail_meta_location": "Location",
            "profiles.settings_source_manual": "Manual",
            "profiles.settings_review_source_catalog": "Catalog",
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
            "profiles.wizard_preferences_error_name": "Preference name required",
            "profiles.wizard_preferences_error_value": "Preference value required",
        }};
        const t = (key) => translations[key] || key;
        const escapeHtml = (value) => String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
        let sourceData = {{ DisableTelemetry: true }};
        const changedDocuments = [];
        const statuses = [];
        const prefNameInput = {{
            value: "browser.new.pref",
            focused: false,
            focus() {{ this.focused = true; }},
        }};
        const controls = {{
            status: {{ value: "locked" }},
            type: {{ value: "string" }},
            input: {{ value: "enabled", hidden: false, disabled: false }},
            select: {{ value: "", hidden: true, disabled: true }},
        }};
        const preferenceEditorEl = {{
            querySelector(selector) {{
                if (selector === "[data-settings-detail-pref-status]") return controls.status;
                if (selector === "[data-settings-detail-pref-type]") return controls.type;
                if (selector === "[data-settings-detail-pref-value-input]") return controls.input;
                if (selector === "[data-settings-detail-pref-value-select]") return controls.select;
                return null;
            }},
        }};
        const panel = {{
            dataset: {{}},
            listeners: {{}},
            _innerHTML: "",
            addEventListener(eventName, handler) {{
                this.listeners[eventName] = handler;
            }},
            querySelector(selector) {{
                if (selector === "[data-settings-detail-pref-name]") return prefNameInput;
                if (selector === "[data-settings-detail-preference-editor]") return preferenceEditorEl;
                return null;
            }},
            querySelectorAll() {{
                return [];
            }},
            get innerHTML() {{
                return this._innerHTML;
            }},
            set innerHTML(value) {{
                this._innerHTML = String(value);
            }},
        }};
        const addPreference = {{
            listener: null,
            addEventListener(eventName, handler) {{
                if (eventName === "click") this.listener = handler;
            }},
            click() {{
                this.listener?.();
            }},
        }};
        const detail = window.BPMProfilesAllSettingsDetail.create({{
            elements: {{
                allSettingsDetailPanelEl: panel,
                allSettingsAddPreferenceEl: addPreference,
            }},
            dependencies: {{
                t,
                escapeHtml,
                normalizePreferenceName: (value) => String(value || "").trim(),
                serializePreferenceValue: (value) => String(value ?? ""),
                serializePreferenceSelectValue: (value) => String(value ?? ""),
                parsePreferenceValue: (value) => ({{ ok: true, value }}),
                fromEditorValue: (value) => value,
                toEditorValue: (value) => JSON.stringify(value),
                readWizardSchemaSource: () => ({{ ok: true, data: sourceData }}),
                renderSchemaPolicyEditorCard: () => "",
                renderSchemaPolicyReviewState: () => {{}},
                onDocumentChange: (nextDocument) => {{
                    sourceData = nextDocument;
                    changedDocuments.push(JSON.parse(JSON.stringify(nextDocument)));
                }},
                setStatus: (message, tone) => statuses.push([message, tone]),
            }},
            state: {{
                getEditor: () => null,
                setCurrentRaw: (nextDocument) => {{ sourceData = nextDocument; }},
            }},
        }});

        detail.render({{
            id: "DisableTelemetry",
            label: "DisableTelemetry",
            kind: "policy",
            kindLabel: "Policy",
            categoryLabel: "Security & privacy",
            configured: true,
            guided: false,
            target: "policy:DisableTelemetry",
            sources: ["manual"],
            sourceDetails: {{ path: ["DisableTelemetry"] }},
            issues: [],
            schemaItem: null,
        }});
        panel.innerHTML = "dirty editor";
        panel.listeners.click({{
            target: {{
                closest(selector) {{
                    return selector === "[data-settings-detail-reset]" ? {{}} : null;
                }},
            }},
        }});
        assert(panel.innerHTML.includes("DisableTelemetry"));
        assert(panel.innerHTML.includes("data-settings-detail-raw-value"));

        panel.listeners.click({{
            target: {{
                closest(selector) {{
                    return selector === "[data-settings-detail-remove]" ? {{}} : null;
                }},
            }},
        }});
        assert.equal(changedDocuments.length, 1);
        assert.equal(changedDocuments[0].DisableTelemetry, undefined);
        assert.deepEqual(statuses.at(-1), ["Setting removed from the profile.", "info"]);

        addPreference.click();
        assert.equal(prefNameInput.focused, true);
        assert(panel.innerHTML.includes("data-settings-detail-new=\\"true\\""));

        panel.listeners.click({{
            target: {{
                closest(selector) {{
                    return selector === "[data-settings-detail-apply-preference]" ? {{}} : null;
                }},
            }},
        }});
        assert.equal(changedDocuments.length, 2);
        assert.equal(changedDocuments[1].Preferences["browser.new.pref"].Status, "locked");
        assert.equal(changedDocuments[1].Preferences["browser.new.pref"].Value, "enabled");
        assert(panel.innerHTML.includes("data-settings-detail-new=\\"false\\""));
        assert(!panel.innerHTML.includes("data-settings-search-target=\\"known-preference:browser.new.pref\\""));
        """
    )

    subprocess.run(["node", "-e", script], cwd=REPO_ROOT, check=True)
