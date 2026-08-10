import assert from "node:assert/strict";
import test from "node:test";

import { create as createList } from "../../../../app/static/profiles_all_settings_list.js";
import { create as createRouteState } from "../../../../app/static/profiles_all_settings_state.js";
import { createFakeElement } from "../../support/dom_harness.js";
import { installListWindow, translate } from "../../support/settings_harness.js";

const entries = [
    { id: "KnownPolicy", label: "KnownPolicy", kind: "policy", categoryId: "general", configured: true, value: "true", unknown: false, rawFallback: false, sources: [] },
    { id: "MissingPolicy", label: "MissingPolicy", kind: "policy", categoryId: "general", configured: true, value: "true", unknown: false, rawFallback: false, sources: [] },
    { id: "UnknownPolicy", label: "UnknownPolicy", kind: "policy", categoryId: "raw-unmapped", configured: true, value: "true", unknown: true, rawFallback: false, sources: ["unknown"] },
    { id: "raw.preference", label: "raw.preference", kind: "preference", categoryId: "raw-unmapped", configured: true, value: "true", unknown: false, rawFallback: true, knownPreference: null, sources: ["raw-fallback"] },
];
const labels = {
    "profiles.all_settings.row_help.open": "Open {setting}",
    "profiles.all_settings.row_help.missing": "Missing {setting}",
    "profiles.all_settings.row_help.unavailable": "Unavailable {setting}",
    "profiles.all_settings.row_help.raw_not_applicable": "Raw {setting}",
    "profiles.all_settings.row_help.unknown_not_supported": "Unknown {setting}",
};

function render(status, links) {
    const listElement = createFakeElement();
    createList({
        documentRef: { documentElement: { lang: "en" } },
        elements: {
            allSettingsListSummaryEl: createFakeElement(),
            allSettingsListEl: listElement,
            allSettingsListEmptyEl: createFakeElement(),
            allSettingsFilterButtons: [],
            allSettingsSourceFilterButtons: [],
        },
        dependencies: {
            t: translate(labels),
            escapeHtml: (value) => String(value || ""),
            getCurrentLang: () => "en",
            readWizardSchemaSource: () => ({ ok: true, data: {} }),
            allSettingsRouteState: createRouteState({ activeMode: "catalog" }),
            settingsInventory: { collect: () => entries },
            documentationRowHelpLinks: links,
            documentationRowHelpStatus: status,
            onSelectionChange: () => {},
        },
    }).render();
    return listElement.innerHTML;
}

test("row help emits only available links and localized noninteractive dispositions", (context) => {
    installListWindow(context);
    const available = render("available", {
        "policy:KnownPolicy": { en: "/help/en/known-policy" },
    });
    assert.equal((available.match(/\shref=/g) || []).length, 1);
    assert.match(available, /data-settings-entry-help-disposition="linked"/);
    assert.match(available, /data-settings-entry-help-disposition="missing_documentation"/);
    assert.match(available, /data-settings-entry-help-disposition="unsupported_unknown"/);
    assert.match(available, /data-settings-entry-help-disposition="not_applicable_raw"/);
    assert.equal((available.match(/role="img"/g) || []).length, 3);

    for (const status of [
        "artifact_unavailable",
        "artifact_stale",
        "artifact_incomplete",
        "artifact_incompatible",
    ]) {
        const unavailable = render(status, {});
        assert.equal((unavailable.match(/\shref=/g) || []).length, 0);
        assert.ok(unavailable.includes(`data-settings-entry-help-disposition="${status}"`));
        assert.match(unavailable, /Unavailable MissingPolicy/);
        assert.match(unavailable, /data-settings-entry-help-disposition="unsupported_unknown"/);
        assert.match(unavailable, /data-settings-entry-help-disposition="not_applicable_raw"/);
    }
});
