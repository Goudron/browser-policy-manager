import assert from "node:assert/strict";
import test from "node:test";

import * as compare from "../../../../app/static/profiles_modules/compare_state.mjs";
import * as dirty from "../../../../app/static/profiles_modules/dirty_route_guard.mjs";
import * as listUrl from "../../../../app/static/profiles_modules/profile_list_url.mjs";
import * as navigationUrl from "../../../../app/static/profiles_modules/navigation_url.mjs";
import * as certificatePolicy from "../../../../app/static/profiles_modules/certificate_policy.mjs";
import * as policy from "../../../../app/static/profiles_modules/policy_document.mjs";
import * as preference from "../../../../app/static/profiles_modules/preference_values.mjs";
import * as review from "../../../../app/static/profiles_modules/review_state.mjs";
import * as websiteFilter from "../../../../app/static/profiles_modules/website_filter.mjs";
import * as workspace from "../../../../app/static/profiles_modules/workspace_state.mjs";
import { create as createCertificateTrust } from "../../../../app/static/profiles_certificate_trust.js";

const context = {
    location: { origin: "https://bpm.test" },
    confirm: () => false,
    addEventListener: () => {},
};
globalThis.window = context;

function certificateChoice(initialValue = "") {
    const listeners = new Map();
    return {
        value: initialValue,
        disabled: false,
        classList: { toggle: () => {} },
        closest: () => ({ classList: { toggle: () => {} } }),
        addEventListener: (name, callback) => listeners.set(name, callback),
        change: () => listeners.get("change")(),
    };
}

const legacy = {
    compare: await import("../../../../app/static/profiles_compare_state.js"),
    workspace: await import("../../../../app/static/profiles_workspace_state.js"),
    policy: await import("../../../../app/static/profiles_data.js"),
    preference: (await import("../../../../app/static/profiles_utils.js")).utils,
    review: await import("../../../../app/static/profiles_review_state.js"),
};

test("pure modules match their runtime adapters", () => {
    const left = { SearchBar: "unified", Preferences: { "browser.z": false } };
    const right = { DisableTelemetry: true, Preferences: { "browser.a": true } };
    assert.deepEqual(compare.collectProfileSettingKeys(left, right), legacy.compare.collectProfileSettingKeys(left, right));
    assert.deepEqual(
        compare.collectDiffPaths({ A: { z: 1, a: 2 } }, { A: { z: 3 } }),
        legacy.compare.collectDiffPaths({ A: { z: 1, a: 2 } }, { A: { z: 3 } }),
    );
    assert.equal(
        compare.snapshotToString({ z: 1, a: { z: false, a: true } }),
        legacy.compare.snapshotToString({ z: 1, a: { z: false, a: true } }),
    );

    const labels = {
        archivedTitle: "Archived", archivedCopy: "a", emptyTitle: "Empty", emptyCopy: "e",
        draftTitle: "Draft", draftCopy: "d", invalidTitle: "Invalid", invalidCopy: "i",
        dirtyTitle: "Dirty", dirtyCopy: "x", readyTitle: "Ready", readyCopy: "r",
    };
    const lifecycle = {
        dirty: true, invalid: false, currentId: 7, currentProfile: { is_deleted: false },
        hasDraftName: true, labels,
    };
    assert.deepEqual(workspace.getWorkflowLifecycleState(lifecycle), legacy.workspace.getWorkflowLifecycleState(lifecycle));
    assert.deepEqual(
        workspace.buildUpdatePayload(
            { description: "d", schemaVersion: "release-153" },
            { A: true }, { score: 1 }, { expected_revision: 2 },
        ),
        legacy.workspace.buildUpdatePayload(
            { description: "d", schemaVersion: "release-153" },
            { A: true }, { score: 1 }, { expected_revision: 2 },
        ),
    );

    const flags = { DisableTelemetry: true };
    assert.equal(policy.toEditorValue(flags), legacy.policy.toEditorValue(flags));
    assert.deepEqual(
        policy.fromEditorValue('{"policies":{"BlockAboutConfig":true}}'),
        legacy.policy.fromEditorValue('{"policies":{"BlockAboutConfig":true}}'),
    );
    assert.deepEqual(
        policy.parseEditorPolicyDocument('{"policies":{"Nested":{"B":2,"A":1}}}'),
        { policies: { Nested: { B: 2, A: 1 } } },
    );
    assert.throws(() => policy.fromEditorValue("[]"), /Expected policies\.json root object/);
    assert.throws(() => policy.fromEditorValue('{"policies":[]}'), /Expected policies to be an object/);

    const filters = {
        q: "Finance", lifecycle: "archived", includeDeleted: true,
        sort: "name", order: "asc", limit: 40,
    };
    assert.equal(
        listUrl.buildProfileListUrl(filters, "https://bpm.test").toString(),
        legacy.policy.buildProfileListUrl(filters, { origin: "https://bpm.test" }, null).toString(),
    );
    assert.deepEqual(
        preference.parsePreferenceValue("false", "", (key, fallback) => `${key}:${fallback}`),
        legacy.preference.parsePreferenceValue("false", "", (key, fallback) => `${key}:${fallback}`),
    );
    assert.deepEqual(
        preference.parsePreferenceValue("invalid", "number", (key) => key),
        legacy.preference.parsePreferenceValue("invalid", "number", (key) => key),
    );
    assert.equal(
        preference.serializePreferenceSelectValue({ nested: true }),
        legacy.preference.serializePreferenceSelectValue({ nested: true }),
    );
    assert.equal(
        review.countConfiguredObjectEntries({ A: false, B: " ", C: { D: 1 } }),
        legacy.review.countConfiguredObjectEntries({ A: false, B: " ", C: { D: 1 } }),
    );

    const anchor = { getAttribute: () => "/profiles/7", target: "_self" };
    const event = {
        target: { closest: () => anchor }, button: 0,
        preventDefault: () => {}, stopPropagation: () => {},
    };
    assert.equal(dirty.isGuardedProfileRouteHref(anchor, "https://bpm.test"), true);
    assert.equal(dirty.isCrossTabProfileRouteIntent(event, anchor), false);
    const guard = dirty.createDirtyRouteGuard({
        windowRef: context,
        currentSnapshotState: () => ({ dirty: true }),
    });
    assert.equal(guard.guardProfileRouteNavigation(event), true);
});

test("certificate trust posture maps exact fields and preserves imported siblings", () => {
    const systemTrust = certificateChoice();
    const enterpriseRoots = certificateChoice();
    const certificateBypass = certificateChoice();
    const windowsSso = certificateChoice();
    const entraSso = certificateChoice();
    const entraRow = { hidden: false };
    const schemaStatus = { textContent: "" };
    const editor = {
        value: JSON.stringify({
            Preferences: { "security.enterprise_roots.enabled": { Status: "locked", Type: "boolean", Value: false } },
            Certificates: { Install: ["/managed/root.pem"], ImportEnterpriseRoots: false },
            DisableSecurityBypass: { SafeBrowsing: true, InvalidCertificate: false },
            WindowsSSO: true,
            MicrosoftEntraSSO: true,
        }),
        getValue() { return this.value; },
        setValue(value) { this.value = value; },
    };
    let raw;
    const trust = createCertificateTrust({
        documentRef: { getElementById: () => ({ value: "" }) },
        elements: {
            wizardCertificateSystemTrustEl: systemTrust,
            wizardCertificateEnterpriseRootsEl: enterpriseRoots,
            wizardCertificateErrorBypassEl: certificateBypass,
            wizardCertificateWindowsSsoEl: windowsSso,
            wizardCertificateEntraSsoEl: entraSso,
            wizardCertificateEntraRowEl: entraRow,
            wizardCertificateTrustSchemaStatusEl: schemaStatus,
        },
        dependencies: {
            t: (key) => key,
            fromEditorValue: JSON.parse,
            toEditorValue: JSON.stringify,
            getActiveWizardSchemaVersion: () => "release-153",
            setStatus: () => {},
        },
        state: { getEditor: () => editor, setCurrentRaw: (value) => { raw = value; } },
        wizardSchemaShellCatalog: {
            channels: {
                "release-153": {
                    certificate_trust_posture: {
                        policy_ids: ["Certificates", "DisableSecurityBypass", "WindowsSSO", "MicrosoftEntraSSO"],
                    },
                },
            },
        },
    });

    trust.syncFromEditor();
    assert.equal(systemTrust.value, "false");
    assert.equal(enterpriseRoots.value, "false");
    assert.equal(certificateBypass.value, "false");
    assert.equal(windowsSso.value, "true");
    assert.equal(entraSso.value, "true");

    systemTrust.value = "true";
    systemTrust.change();
    enterpriseRoots.value = "true";
    enterpriseRoots.change();
    certificateBypass.value = "true";
    certificateBypass.change();
    windowsSso.value = "false";
    windowsSso.change();
    const changed = JSON.parse(editor.getValue());
    assert.equal(changed.Preferences["security.enterprise_roots.enabled"].Status, "locked");
    assert.equal(changed.Preferences["security.enterprise_roots.enabled"].Value, true);
    assert.deepEqual(changed.Certificates, { Install: ["/managed/root.pem"], ImportEnterpriseRoots: true });
    assert.deepEqual(changed.DisableSecurityBypass, { SafeBrowsing: true, InvalidCertificate: true });
    assert.equal(changed.WindowsSSO, false);
    assert.deepEqual(raw, changed);

    enterpriseRoots.value = "";
    enterpriseRoots.change();
    assert.deepEqual(JSON.parse(editor.getValue()).Certificates, { Install: ["/managed/root.pem"] });

    editor.value = JSON.stringify({ Certificates: { ImportEnterpriseRoots: true, UnknownImportShape: "keep" } });
    trust.syncFromEditor();
    assert.equal(enterpriseRoots.value, "custom");
    assert.equal(enterpriseRoots.disabled, true);
    enterpriseRoots.change();
    assert.deepEqual(JSON.parse(editor.getValue()), {
        Certificates: { ImportEnterpriseRoots: true, UnknownImportShape: "keep" },
    });
});

test("comparison helpers retain deterministic values for every supported setting shape", () => {
    assert.equal(compare.isPlainObject({}), true);
    assert.equal(compare.isPlainObject([]), false);
    assert.equal(compare.isPlainObject(null), false);
    assert.equal(compare.isPlainObject("text"), false);
    assert.deepEqual(compare.normalizeValue([{ z: 1, a: [true] }]), [{ a: [true], z: 1 }]);
    assert.deepEqual(compare.collectDiffPaths({ same: 1 }, { same: 1 }), []);
    assert.deepEqual(compare.collectDiffPaths({ left: 1 }, { right: 2 }), [["left"], ["right"]]);
    assert.deepEqual(compare.collectDiffPaths({ left: 1 }, 1), [["left"]]);
    assert.deepEqual(compare.collectDiffPaths(1, { right: 2 }), [["right"]]);
    assert.deepEqual(
        compare.collectProfileSettingKeys(null, { A: true, Preferences: { "browser.a": true } }),
        [
            { id: "policy:A", kind: "policy", label: "A", policyId: "A", settingKey: "A" },
            {
                id: "preference:browser.a",
                kind: "preference",
                label: "browser.a",
                preferenceName: "browser.a",
                settingKey: "Preferences.browser.a",
            },
        ],
    );
    assert.deepEqual(compare.readSettingValue({ Preferences: { "browser.a": false } }, {
        kind: "preference", preferenceName: "browser.a",
    }), { present: true, value: false });
    assert.deepEqual(compare.readSettingValue({ A: null }, { policyId: "A" }), { present: true, value: null });
    assert.equal(compare.formatCompareValue({ present: false }), "Not set");
    assert.equal(compare.formatCompareValue({ present: false }, { missingLabel: "Missing" }), "Missing");
    assert.equal(compare.formatCompareValue({ present: true, value: "text" }), "text");
    assert.equal(compare.formatCompareValue({ present: true, value: null }), "null");
    assert.equal(compare.formatCompareValue({ present: true, value: 2 }), "2");
    assert.equal(compare.formatCompareValue({ present: true, value: true }), "true");
    assert.equal(compare.formatCompareValue({ present: true, value: { z: 1, a: 2 } }), '{"a":2,"z":1}');
    assert.equal(compare.formatCompareValue({ present: true, value: [] }), "[]");
});

test("dirty-route helpers distinguish local navigation, cross-tab intent, and discard confirmation", () => {
    const local = { getAttribute: () => "/profiles", target: "_self" };
    assert.equal(dirty.isGuardedProfileRouteHref({ getAttribute: () => "" }, "https://bpm.test"), false);
    assert.equal(dirty.isGuardedProfileRouteHref({ getAttribute: () => "#section" }, "https://bpm.test"), false);
    assert.equal(dirty.isGuardedProfileRouteHref({ getAttribute: () => "https://elsewhere.test/profiles" }, "https://bpm.test"), false);
    assert.equal(dirty.isGuardedProfileRouteHref({ getAttribute: () => "http://[" }, "https://bpm.test"), false);
    assert.equal(dirty.isGuardedProfileRouteHref(local, "https://bpm.test"), true);
    assert.equal(dirty.isCrossTabProfileRouteIntent(null, local), false);
    assert.equal(dirty.isCrossTabProfileRouteIntent({}, {}), false);
    assert.equal(dirty.isCrossTabProfileRouteIntent({ ctrlKey: true }, local), true);
    assert.equal(dirty.isCrossTabProfileRouteIntent({ shiftKey: true }, local), true);
    assert.equal(dirty.isCrossTabProfileRouteIntent({ button: 1 }, local), true);
    assert.equal(dirty.isCrossTabProfileRouteIntent({}, { ...local, target: "_blank" }), true);
    assert.throws(() => dirty.createDirtyRouteGuard(), /requires a windowRef/);

    let listener;
    let stopped = false;
    let prevented = false;
    const windowRef = {
        location: { origin: "https://bpm.test" },
        confirm: () => true,
        addEventListener: (_name, callback) => { listener = callback; },
    };
    const guard = dirty.createDirtyRouteGuard({
        windowRef,
        currentSnapshotState: () => ({ dirty: true }),
        confirmDiscard: () => "Discard?",
    });
    const event = {
        target: { closest: () => local },
        button: 0,
        preventDefault: () => { prevented = true; },
        stopPropagation: () => { stopped = true; },
    };
    assert.equal(guard.confirmRouteNavigationIfDirty(), true);
    assert.equal(guard.isGuardedProfileRouteHref(local), true);
    assert.equal(guard.guardProfileRouteNavigation(event), false);
    assert.equal(guard.guardProfileRouteNavigation({ ...event, target: { closest: () => null } }), false);
    guard.bindBeforeUnload();
    const unload = { preventDefault: () => { prevented = true; } };
    listener(unload);
    assert.equal(unload.returnValue, "");

    const declined = dirty.createDirtyRouteGuard({
        windowRef: { ...windowRef, confirm: () => false },
        currentSnapshotState: () => ({ dirty: true }),
    });
    assert.equal(declined.guardProfileRouteNavigation(event), true);
    assert.equal(prevented, true);
    assert.equal(stopped, true);
    const clean = dirty.createDirtyRouteGuard({
        windowRef: {
            ...windowRef,
            addEventListener: (_name, callback) => { listener = callback; },
        },
        currentSnapshotState: () => ({ dirty: false }),
    });
    assert.equal(clean.confirmRouteNavigationIfDirty(), true);
    clean.bindBeforeUnload();
    listener({ preventDefault: () => { throw new Error("a clean profile must not prevent unload"); } });
    const defaultStateGuard = dirty.createDirtyRouteGuard({ windowRef });
    assert.equal(defaultStateGuard.confirmRouteNavigationIfDirty(), true);
});

test("policy-document helpers reject malformed roots and preserve complete policies documents", () => {
    assert.equal(policy.isPlainObject({}), true);
    assert.equal(policy.isPlainObject([]), false);
    assert.equal(policy.isPlainObject(null), false);
    assert.deepEqual(policy.toFirefoxPoliciesDocument({ policies: { A: true } }), { policies: { A: true } });
    assert.deepEqual(policy.toFirefoxPoliciesDocument([]), { policies: {} });
    assert.deepEqual(policy.toInternalFlags(null), {});
    assert.deepEqual(policy.toInternalFlags(undefined), {});
    assert.deepEqual(policy.toInternalFlags({ A: true }), { A: true });
    assert.throws(() => policy.toInternalFlags([]), /Expected policies\.json root object/);
    assert.throws(() => policy.toInternalFlags({ policies: [] }), /Expected policies to be an object/);
    assert.deepEqual(policy.fromSerializedEditorValue(""), {});
    assert.deepEqual(policy.fromSerializedEditorValue("  \n "), {});
    assert.throws(() => policy.fromSerializedEditorValue("{"), SyntaxError);
    assert.deepEqual(policy.parseEditorPolicyDocument('{"A":true}'), { policies: { A: true } });
    assert.deepEqual(policy.fromEditorValue('{"policies":{"A":true}}'), { A: true });
    assert.equal(policy.getPolicyValue({ policies: { A: true } }, "A"), true);
    assert.deepEqual(policy.setPolicyValue({ A: true }, "A", undefined), {});
    assert.deepEqual(policy.setPolicyValue({ A: true }, "B", false), { A: true, B: false });
});

test("preference helpers cover typed, inferred, serializable, and malformed values", () => {
    const circular = {};
    circular.circular = circular;
    assert.equal(preference.cloneJsonValue(undefined, "fallback"), "fallback");
    assert.deepEqual(preference.cloneJsonValue({ nested: [1] }, null), { nested: [1] });
    assert.notEqual(preference.cloneJsonValue({ nested: true }, null), preference.cloneJsonValue({ nested: true }, null));
    assert.equal(preference.cloneJsonValue(circular, "fallback"), "fallback");
    assert.deepEqual(preference.textToList(" one, two\n \nthree "), ["one", "two", "three"]);
    assert.equal(preference.formatBooleanSelectValue(true), "true");
    assert.equal(preference.formatBooleanSelectValue(false), "false");
    assert.equal(preference.formatBooleanSelectValue("true"), "");
    assert.equal(preference.parseBooleanSelectValue("true"), true);
    assert.equal(preference.parseBooleanSelectValue("false"), false);
    assert.equal(preference.parseBooleanSelectValue(""), null);
    assert.equal(preference.stablePreferenceValueKey(undefined), "__undefined__");
    assert.equal(preference.stablePreferenceValueKey({ a: true }), '{"a":true}');
    assert.equal(preference.stablePreferenceValueKey(circular), "[object Object]");
    assert.equal(preference.serializePreferenceValue("text"), "text");
    assert.equal(preference.serializePreferenceValue(3), "3");
    assert.equal(preference.serializePreferenceValue(false), "false");
    assert.equal(preference.serializePreferenceValue({ a: true }), '{"a":true}');
    assert.equal(preference.serializePreferenceValue(circular), "");
    assert.deepEqual(preference.parsePreferenceValue("true", "boolean"), { ok: true, value: true });
    assert.deepEqual(preference.parsePreferenceValue("false", "boolean"), { ok: true, value: false });
    assert.deepEqual(preference.parsePreferenceValue("yes", "boolean", (key) => key), {
        ok: false, message: "profiles.wizard_preferences_error_boolean",
    });
    assert.deepEqual(preference.parsePreferenceValue("yes", "boolean"), {
        ok: false, message: "Boolean values must be true or false.",
    });
    assert.deepEqual(preference.parsePreferenceValue("12.5", "number"), { ok: true, value: 12.5 });
    assert.deepEqual(preference.parsePreferenceValue("", "number", (key) => key), {
        ok: false, message: "profiles.wizard_preferences_error_number",
    });
    assert.deepEqual(preference.parsePreferenceValue("not-a-number", "number"), {
        ok: false, message: "Number values must be valid numeric input.",
    });
    assert.deepEqual(preference.parsePreferenceValue("x", "string"), { ok: true, value: "x" });
    assert.deepEqual(preference.parsePreferenceValue("true", ""), { ok: true, value: true });
    assert.deepEqual(preference.parsePreferenceValue("false", ""), { ok: true, value: false });
    assert.deepEqual(preference.parsePreferenceValue("-2", ""), { ok: true, value: -2 });
    assert.deepEqual(preference.parsePreferenceValue('{"a":true}', ""), { ok: true, value: { a: true } });
    assert.deepEqual(preference.parsePreferenceValue("[]", ""), { ok: true, value: [] });
    assert.deepEqual(preference.parsePreferenceValue("{bad}", ""), { ok: true, value: "{bad}" });
    assert.equal(preference.serializePreferenceSelectValue(true), "true");
    assert.equal(preference.serializePreferenceSelectValue(false), "false");
    assert.equal(preference.serializePreferenceSelectValue(4), "4");
    assert.equal(preference.serializePreferenceSelectValue("value"), "value");
    assert.equal(preference.serializePreferenceSelectValue(null), "");
    assert.equal(preference.serializePreferenceSelectValue({ a: true }), '{"a":true}');
    assert.equal(preference.serializePreferenceSelectValue(circular), "[object Object]");
    assert.equal(preference.normalizePreferenceName("  browser.a  "), "browser.a");
    assert.equal(preference.normalizePreferenceName(3), "");
});

test("URL, review, and workspace helpers retain every lifecycle and filtering branch", () => {
    assert.equal(listUrl.buildProfileListUrl({}, "https://bpm.test").toString(),
        "https://bpm.test/api/profiles?lifecycle=active&sort=updated_at&order=desc");
    assert.equal(listUrl.buildProfileListUrl({ lifecycle: "all", includeDeleted: true, q: "A", schemaVersion: "release-153", validationState: "valid", limit: 10, sort: "name", order: "asc" }, "https://bpm.test").toString(),
        "https://bpm.test/api/profiles?q=A&schema_version=release-153&validation_state=valid&limit=10&lifecycle=all&include_deleted=true&sort=name&order=asc");
    assert.equal(listUrl.buildProfileListUrl({ lifecycle: "archived" }, "https://bpm.test").searchParams.get("include_deleted"), "true");
    assert.equal(review.hasMeaningfulValue(false), true);
    assert.equal(review.hasMeaningfulValue(0), true);
    assert.equal(review.hasMeaningfulValue("  "), false);
    assert.equal(review.hasMeaningfulValue(["", { A: 1 }]), true);
    assert.equal(review.hasMeaningfulValue({ A: [] }), false);
    assert.equal(review.hasMeaningfulValue(null), false);
    assert.equal(review.countConfiguredObjectEntries(null), 0);
    assert.equal(review.countConfiguredObjectEntries([]), 0);
    assert.equal(review.countConfiguredObjectEntries({ A: "", B: true }), 1);
    assert.equal(workspace.isPlainObject({}), true);
    assert.equal(workspace.isPlainObject([]), false);
    assert.equal(workspace.isPlainObject(null), false);
    assert.deepEqual(workspace.normalizeValue([{ z: 1, a: true }]), [{ a: true, z: 1 }]);
    assert.equal(workspace.snapshotToString({ z: 1, a: true }), '{"a":true,"z":1}');
    const labels = Object.fromEntries([
        "archived", "empty", "draft", "invalid", "dirty", "ready",
    ].flatMap((state) => [[`${state}Title`, `${state} title`], [`${state}Copy`, `${state} copy`]]));
    const cases = [
        [{ currentProfile: { is_deleted: true } }, "archived"],
        [{ currentId: null, hasDraftName: false }, "empty"],
        [{ currentId: null, hasDraftName: true }, "draft"],
        [{ currentId: 1, invalid: true }, "invalid"],
        [{ currentId: 1, dirty: true }, "dirty"],
        [{ currentId: 1 }, "ready"],
    ];
    for (const [state, expected] of cases) {
        assert.deepEqual(workspace.getWorkflowLifecycleState({ dirty: false, invalid: false, currentId: null, currentProfile: null, hasDraftName: false, labels, ...state }), {
            selectionState: expected === "archived" ? "archived" : expected === "empty" || expected === "draft" ? expected : "active",
            workflowState: expected,
            title: labels[`${expected}Title`],
            copy: labels[`${expected}Copy`],
        });
    }
    const form = { name: "Original", description: "Description", schemaVersion: "release-153" };
    assert.deepEqual(workspace.buildUpdatePayload(form, { A: true }, { score: 1 }), {
        description: "Description", flags: { A: true }, compliance: { score: 1 },
    });
    assert.deepEqual(workspace.buildCreatePayload(form, { A: true }, { score: 1 }), {
        name: "Original", description: "Description", schema_version: "release-153", flags: { A: true }, compliance: { score: 1 },
    });
    assert.equal(workspace.buildCreatePayload(form, {}, {}, { name: "Override" }).name, "Override");
});

test("WebsiteFilter preserves safe patterns, exposes unsafe imports, and never repairs ordering", () => {
    const exactPatterns = [
        "<all_urls>",
        "*://*.example.test/*",
        "https://пример.рф:8443/*",
        "file:///managed/*",
        "https://[2001:db8::1]:443/path/*",
    ];
    for (const pattern of exactPatterns) {
        assert.deepEqual(websiteFilter.validateWebsiteFilterPattern(pattern).valid, true, pattern);
    }
    for (const pattern of [
        " javascript:alert(1)",
        "data:text/plain,no",
        "https://user:secret@example.test/*",
        "https://example.test:70000/*",
        "https://example.test/path with spaces",
    ]) {
        assert.equal(websiteFilter.validateWebsiteFilterPattern(pattern).valid, false, pattern);
    }

    const imported = {
        Block: ["https://пример.рф:8443/*", "javascript:alert(1)", "https://пример.рф:8443/*"],
        Exceptions: ["https://пример.рф:8443/*", "<all_urls>"],
    };
    const inspection = websiteFilter.inspectImportedWebsiteFilter(imported);
    assert.deepEqual(inspection.value, imported);
    assert.deepEqual(inspection.rawEntries, [{ field: "Block", index: 1, value: "javascript:alert(1)", code: "unsafe_scheme" }]);
    const analysis = websiteFilter.analyzeWebsiteFilterLists(imported);
    assert.deepEqual(analysis.duplicates, [{
        field: "Block", first: 0, index: 2, value: "https://пример.рф:8443/*",
    }]);
    assert.deepEqual(analysis.conflicts, [
        { kind: "overlap", value: "https://пример.рф:8443/*", blockIndex: 0, exceptionIndex: 0 },
        { kind: "overlap", value: "https://пример.рф:8443/*", blockIndex: 2, exceptionIndex: 0 },
        { kind: "allow_all", value: "<all_urls>", exceptionIndex: 1 },
    ]);

    assert.deepEqual(
        websiteFilter.inspectImportedWebsiteFilter({ Block: ["https://example.test/*"], Extra: true }),
        { kind: "raw_fallback", reason: "unknown_field", value: { Block: ["https://example.test/*"], Extra: true } },
    );
    assert.deepEqual(
        websiteFilter.inspectImportedWebsiteFilter({ Block: ["https://example.test/*", 1] }),
        { kind: "raw_fallback", reason: "not_string", value: { Block: ["https://example.test/*", 1] } },
    );

    const ordered = {
        Block: ["https://first.test/*", "https://second.test/*"],
        Exceptions: ["https://allow.test/*"],
    };
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture(ordered, "allow_only"), {
        ok: true,
        value: {
            Block: ["<all_urls>", "https://first.test/*", "https://second.test/*"],
            Exceptions: ["https://allow.test/*"],
        },
    });
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture({
        Block: ["<all_urls>", "https://first.test/*", "<all_urls>"],
        Exceptions: ["https://allow.test/*"],
    }, "block_some"), {
        ok: true,
        value: {
            Block: ["https://first.test/*"],
            Exceptions: ["https://allow.test/*"],
        },
    });
});

test("WebsiteFilter rejects every unsafe shape and covers raw, posture, and omission boundaries", () => {
    assert.equal(websiteFilter.isPlainObject({}), true);
    assert.equal(websiteFilter.isPlainObject([]), false);
    assert.equal(websiteFilter.isPlainObject(null), false);
    assert.equal(websiteFilter.isPlainObject("value"), false);

    const invalidPatterns = new Map([
        [1, "not_string"],
        ["", "empty"],
        [" https://example.test/*", "whitespace"],
        ["https://example\u0000.test/*", "whitespace"],
        ["https://example.test/a b", "whitespace"],
        ["x".repeat(2049), "too_long"],
        ["vbscript:alert(1)", "unsafe_scheme"],
        ["https:/example.test/*", "shape"],
        ["https://example.test", "shape"],
        ["gopher://example.test/*", "unsupported_scheme"],
        ["https://user@example.test/*", "unsafe_authority"],
        ["https://example\\.test/*", "unsafe_authority"],
        ["https:///*", "unsafe_authority"],
        ["file://host/*", "file_host"],
        ["https://[]/*", "ipv6"],
        ["https://[::1]suffix/*", "port"],
        ["https://[not-ip]/*", "ipv6"],
        ["https://:443/*", "host"],
        ["https://bad..example/*", "host"],
        ["https://bad!example/*", "host"],
        ["https://example.test:port/*", "port"],
        ["https://example.test:0/*", "port"],
    ]);
    for (const [pattern, code] of invalidPatterns) {
        assert.equal(websiteFilter.validateWebsiteFilterPattern(pattern).code, code, String(pattern));
    }
    assert.deepEqual(websiteFilter.validateWebsiteFilterPattern("HTTP://Example.Test:65535/*"), {
        valid: true,
        kind: "pattern",
        idn: false,
        scheme: "http",
        host: "Example.Test",
        port: "65535",
    });
    assert.equal(websiteFilter.validateWebsiteFilterPattern("https://example.test:*/*").port, "*");
    assert.equal(websiteFilter.validateWebsiteFilterPattern("file://*/*").valid, true);

    assert.deepEqual(websiteFilter.inspectImportedWebsiteFilter(undefined), {
        kind: "typed", value: { Block: [], Exceptions: [] }, rawEntries: [],
    });
    assert.deepEqual(websiteFilter.inspectImportedWebsiteFilter(null), {
        kind: "raw_fallback", reason: "not_object", value: null,
    });
    assert.deepEqual(websiteFilter.inspectImportedWebsiteFilter({ Block: "not-a-list" }), {
        kind: "raw_fallback", reason: "not_array", value: { Block: "not-a-list" },
    });
    assert.deepEqual(websiteFilter.inspectImportedWebsiteFilter({ Block: [], Exceptions: "not-a-list" }), {
        kind: "raw_fallback", reason: "not_array", value: { Block: [], Exceptions: "not-a-list" },
    });
    assert.deepEqual(websiteFilter.analyzeWebsiteFilterLists([]), {
        kind: "raw_fallback", reason: "not_object", value: [], duplicates: [], conflicts: [],
    });

    const postures = new Map([
        [{}, "defaults"],
        [{ Block: ["<all_urls>"], Exceptions: ["https://allow.test/*"] }, "allow_only"],
        [{ Block: ["<all_urls>"] }, "allow_only"],
        [{ Block: ["https://block.test/*"], Exceptions: ["https://allow.test/*"] }, "mixed"],
        [{ Block: ["https://block.test/*"] }, "block_some"],
        [{ Exceptions: ["https://allow.test/*"] }, "exceptions_only"],
        [null, "raw"],
    ]);
    for (const [value, posture] of postures) {
        assert.equal(websiteFilter.resolveWebsiteFilterPosture(value), posture);
    }
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture(null, "allow_only"), {
        ok: false, reason: "raw_fallback", value: null,
    });
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture({}, "defaults"), {
        ok: true, value: undefined,
    });
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture({ Block: ["<all_urls>"] }, "allow_only"), {
        ok: true, value: { Block: ["<all_urls>"] },
    });
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture({ Exceptions: ["https://allow.test/*"] }, "mixed"), {
        ok: true, value: { Exceptions: ["https://allow.test/*"] },
    });
    assert.deepEqual(websiteFilter.applyWebsiteFilterPosture({}, "unsupported"), {
        ok: false, value: {},
    });
    assert.deepEqual(websiteFilter.omitEmptyWebsiteFilterFields({ Block: [], Exceptions: "wrong" }), {});
});

test("certificate policy lists preserve Firefox references, order, duplicates, raw fallback, and platform paths", () => {
    const windowsPath = "C:\\Program Files\\Vendor\\device.dll";
    const uncPath = "\\\\server\\security modules\\pkcs11.dll";
    const posixPath = "/usr/lib64/pkcs11/vendor.so";
    const relativeCertificate = "company-root.pem";

    for (const reference of [windowsPath, uncPath, posixPath, relativeCertificate]) {
        assert.deepEqual(certificatePolicy.validateCertificateReference(reference), { valid: true }, reference);
    }
    for (const [reference, code] of [["", "empty"], [" root.pem", "outer_whitespace"], ["root.pem\u0000", "control_character"]]) {
        assert.equal(certificatePolicy.validateCertificateReference(reference).code, code);
    }
    assert.equal(certificatePolicy.validateSecurityDeviceName("Corporate PKCS#11").valid, true);
    assert.equal(certificatePolicy.validateAuthenticationHost("https://intranet.example").valid, true);
    assert.equal(certificatePolicy.validateAuthenticationHost("host name").code, "whitespace");

    const certificates = certificatePolicy.inspectCertificates({
        Install: [relativeCertificate, windowsPath, relativeCertificate], ImportEnterpriseRoots: true,
    });
    assert.equal(certificates.kind, "typed");
    assert.deepEqual(certificates.duplicates, [{ value: relativeCertificate, first: 0, index: 2 }]);
    assert.deepEqual(certificatePolicy.moveListEntry(certificates.value.Install, 1, -1), {
        ok: true, value: [windowsPath, relativeCertificate, relativeCertificate],
    });
    assert.deepEqual(certificatePolicy.moveListEntry(certificates.value.Install, 0, -1), {
        ok: false, value: [relativeCertificate, windowsPath, relativeCertificate],
    });
    assert.deepEqual(certificatePolicy.omitEmptyCertificateFields({ Install: [], ImportEnterpriseRoots: false }), {
        ImportEnterpriseRoots: false,
    });
    assert.deepEqual(certificatePolicy.inspectCertificates({ Install: ["root.pem"], Unknown: true }), {
        kind: "raw_fallback", reason: "unknown_or_non_object", value: { Install: ["root.pem"], Unknown: true },
    });

    const devices = certificatePolicy.inspectSecurityDevices({
        Add: { "Corporate token": windowsPath, "Linux token": posixPath },
        Delete: ["Old token", "Old token"],
    });
    assert.equal(devices.kind, "typed");
    assert.deepEqual(devices.value.Add, { "Corporate token": windowsPath, "Linux token": posixPath });
    assert.deepEqual(devices.duplicates, [{ value: "Old token", first: 0, index: 1 }]);
    assert.deepEqual(certificatePolicy.omitEmptySecurityDeviceFields({ Add: {}, Delete: [] }), undefined);
    assert.deepEqual(certificatePolicy.inspectSecurityDevices({ "Legacy direct name": windowsPath }), {
        kind: "raw_fallback", reason: "unknown_or_non_object", value: { "Legacy direct name": windowsPath },
    });

    const authentication = certificatePolicy.inspectAuthentication({
        SPNEGO: ["intranet.example", "intranet.example"],
        NTLM: [],
        AllowNonFQDN: { "fileserver": true },
        AllowProxies: { "proxy.example": true },
        Locked: false,
        PrivateBrowsing: true,
    });
    assert.equal(authentication.kind, "typed");
    assert.deepEqual(authentication.duplicates.SPNEGO, [{ value: "intranet.example", first: 0, index: 1 }]);
    assert.deepEqual(certificatePolicy.omitEmptyAuthenticationFields({ NTLM: [], Locked: false }), { Locked: false });
    assert.deepEqual(certificatePolicy.inspectAuthentication({ NTLM: ["host"], Extra: true }), {
        kind: "raw_fallback", reason: "unknown_or_non_object", value: { NTLM: ["host"], Extra: true },
    });
});

test("certificate policy helpers reject every typed failure boundary without repairing imported data", () => {
    for (const [value, code] of [
        [1, "not_string"],
        ["", "empty"],
        ["root.pem\u0000", "control_character"],
        [" root.pem", "outer_whitespace"],
        ["x".repeat(4097), "too_long"],
    ]) {
        assert.equal(certificatePolicy.validateCertificateReference(value).code, code);
    }
    for (const validator of [
        certificatePolicy.validateSecurityDeviceName,
        certificatePolicy.validateAuthenticationHost,
    ]) {
        assert.equal(validator(1).code, "not_string");
        assert.equal(validator("").code, "empty");
        assert.equal(validator("invalid\u0000").code, "control_character");
        assert.equal(validator(" invalid").code, "outer_whitespace");
    }
    assert.equal(certificatePolicy.validateSecurityDeviceName("x".repeat(257)).code, "too_long");
    assert.equal(certificatePolicy.validateAuthenticationHost("host name").code, "whitespace");
    assert.equal(certificatePolicy.validateAuthenticationHost("x".repeat(2049)).code, "too_long");

    assert.deepEqual(certificatePolicy.inspectCertificates(undefined), { kind: "typed", value: {} });
    assert.deepEqual(certificatePolicy.inspectCertificates(null), {
        kind: "raw_fallback", reason: "unknown_or_non_object", value: null,
    });
    assert.equal(certificatePolicy.inspectCertificates({ Install: [1] }).reason, "install_not_string_list");
    assert.equal(certificatePolicy.inspectCertificates({ ImportEnterpriseRoots: "true" }).reason, "enterprise_roots_not_boolean");
    assert.deepEqual(certificatePolicy.inspectCertificates({ Install: [] }), {
        kind: "typed", value: { Install: [] }, duplicates: [], invalidReferences: [],
    });
    assert.deepEqual(certificatePolicy.inspectCertificates({ ImportEnterpriseRoots: false }), {
        kind: "typed", value: { ImportEnterpriseRoots: false }, duplicates: [], invalidReferences: [],
    });
    assert.deepEqual(certificatePolicy.inspectSecurityDevices(undefined), { kind: "typed", value: {} });
    assert.deepEqual(certificatePolicy.inspectSecurityDevices({}), {
        kind: "typed", value: {}, duplicates: [], duplicateNames: [], invalidAdd: [], invalidDelete: [],
    });
    assert.equal(certificatePolicy.inspectSecurityDevices({ Add: [] }).reason, "add_not_string_map");
    assert.equal(certificatePolicy.inspectSecurityDevices({ Delete: {} }).reason, "delete_not_string_list");
    assert.deepEqual(certificatePolicy.inspectSecurityDevices({ Add: {}, Delete: [] }), {
        kind: "typed", value: { Add: {}, Delete: [] }, duplicates: [], duplicateNames: [], invalidAdd: [], invalidDelete: [],
    });
    assert.deepEqual(certificatePolicy.inspectAuthentication(undefined), { kind: "typed", value: {} });
    assert.deepEqual(certificatePolicy.inspectAuthentication({}), {
        kind: "typed", value: {}, duplicates: { SPNEGO: [], Delegated: [], NTLM: [] }, invalidHosts: [],
    });
    assert.equal(certificatePolicy.inspectAuthentication({ SPNEGO: {} }).reason, "host_list_not_string_list");
    assert.equal(certificatePolicy.inspectAuthentication({ AllowProxies: { proxy: false } }).reason, "host_map_not_true_map");
    assert.equal(certificatePolicy.inspectAuthentication({ Locked: "yes" }).reason, "boolean_not_boolean");
    assert.deepEqual(certificatePolicy.inspectAuthentication({
        SPNEGO: [], Delegated: [], NTLM: [], AllowNonFQDN: {}, AllowProxies: {}, Locked: true, PrivateBrowsing: false,
    }), {
        kind: "typed",
        value: {
            SPNEGO: [], Delegated: [], NTLM: [], AllowNonFQDN: {}, AllowProxies: {}, Locked: true, PrivateBrowsing: false,
        },
        duplicates: { SPNEGO: [], Delegated: [], NTLM: [] },
        invalidHosts: [],
    });
    assert.deepEqual(certificatePolicy.omitEmptyCertificateFields({ Install: ["root.pem"] }), {
        Install: ["root.pem"],
    });
    assert.deepEqual(certificatePolicy.omitEmptySecurityDeviceFields({ Add: { token: "module.so" } }), {
        Add: { token: "module.so" },
    });
    assert.deepEqual(certificatePolicy.omitEmptySecurityDeviceFields({ Delete: ["legacy token"] }), {
        Delete: ["legacy token"],
    });
    assert.deepEqual(certificatePolicy.omitEmptyAuthenticationFields({
        SPNEGO: ["intranet.example"], AllowNonFQDN: { fileserver: true }, PrivateBrowsing: false,
    }), {
        SPNEGO: ["intranet.example"], AllowNonFQDN: { fileserver: true }, PrivateBrowsing: false,
    });

    assert.deepEqual(certificatePolicy.moveListEntry("not-a-list", 0, 1), {
        ok: false, value: "not-a-list",
    });
    assert.deepEqual(certificatePolicy.moveListEntry(["one"], 0, 2), {
        ok: false, value: ["one"],
    });
    assert.deepEqual(certificatePolicy.moveListEntry(["one"], 1, -1), {
        ok: false, value: ["one"],
    });
});

test("navigation URL guards preserve Firefox spelling while separating typed input, raw fallback, and external links", () => {
    assert.equal(navigationUrl.getNavigationInputKind(null, null), null);
    assert.equal(navigationUrl.getNavigationInputKind("AllowedDomainsForApps"), "domain-list");
    assert.equal(navigationUrl.getNavigationInputKind("AutoLaunchProtocolsFromOrigins", "handlers.allowed_origins"), "http-origin");
    assert.equal(navigationUrl.getNavigationInputKind("Homepage", "unexpected"), "navigation-url");
    assert.equal(navigationUrl.getNavigationInputKind("Bookmarks", "URL"), "external-url");
    assert.equal(navigationUrl.getNavigationInputKind("ManagedBookmarks", "children.url"), "external-url");
    assert.equal(navigationUrl.getNavigationInputKind("Handlers", "schemes.mailto.handlers.uriTemplate"), "https-template");
    assert.equal(navigationUrl.getNavigationInputKind("HttpAllowlist", "__value__"), "http-origin");
    assert.equal(navigationUrl.getNavigationInputKind("HttpAllowlist", "unexpected"), null);
    assert.equal(navigationUrl.getNavigationInputKind("Certificates", "Install"), null);

    const exact = "HTTPS://Example.Test:8443/Path?exact=One#Fragment";
    assert.deepEqual(navigationUrl.validateNavigationValue(exact, "navigation-url"), {
        valid: true,
        kind: "navigation-url",
        protocol: "https:",
        host: "example.test",
        idn: false,
    });
    assert.deepEqual(navigationUrl.getSafeExternalLink(exact), {
        href: exact,
        target: "_blank",
        rel: "noopener noreferrer",
        referrerPolicy: "no-referrer",
    });
    assert.equal(navigationUrl.validateNavigationValue("about:home", "navigation-url").valid, true);
    assert.equal(navigationUrl.validateNavigationValue("about:config", "navigation-url").code, "about_page");
    assert.equal(navigationUrl.validateNavigationValue("file:///opt/start.html", "navigation-url").valid, true);
    assert.equal(navigationUrl.validateNavigationValue("https://origin.example/", "http-origin").valid, true);
    assert.equal(navigationUrl.validateNavigationValue("https://example.test/%s", "https-template").kind, "https-template");
    const URLConstructor = globalThis.URL;
    globalThis.URL = class {
        protocol = "https:";
        username = "";
        password = "";
        pathname = "/";
        search = "";
        hash = "";
        host = "";
        hostname = "";
    };
    try {
        assert.equal(navigationUrl.validateNavigationValue("https://no-host.test/", "external-url").code, "host");
    } finally {
        globalThis.URL = URLConstructor;
    }

    for (const [value, kind, code] of [
        [null, "navigation-url", "not_string"],
        ["", "navigation-url", "empty"],
        ["x".repeat(2049), "navigation-url", "too_long"],
        ["not-a-url", "https-template", "shape"],
        ["http://[broken", "external-url", "shape"],
        ["javascript:alert(1)", "navigation-url", "unsafe_scheme"],
        ["data:text/html,<svg/onload=alert(1)>", "external-url", "unsafe_scheme"],
        ["https://user:secret@example.test/", "external-url", "credentials"],
        ["https://example.test/path", "http-origin", "origin_path"],
        ["https://example.test/?query", "http-origin", "origin_path"],
        ["https://exam\u202Eple.test/", "external-url", "unicode_control"],
        ["http://example.test, https://second.test", "domain-list", "whitespace"],
        ["https://example.test/search?q=term", "https-template", "placeholder"],
        ["http://example.test/?q=%s", "https-template", "unsupported_scheme"],
        ["example.test,,other.test", "domain-list", "domain"],
        ["example.test/path", "domain-list", "domain"],
        ["https://example.test/", "unsupported", "unsupported_kind"],
        ["mailto:help@example.test", "navigation-url", "unsupported_scheme"],
        ["about:blank", "external-url", "unsupported_scheme"],
        ["ftp://example.test/", "http-origin", "unsupported_scheme"],
        ["file://server/managed", "navigation-url", "file_host"],
    ]) {
        assert.equal(navigationUrl.validateNavigationValue(value, kind).code, code, `${kind}: ${value}`);
        assert.equal(navigationUrl.getSafeExternalLink(value, kind), null, `no external link for ${value}`);
    }

    const unicodeHost = "https://раypal.example/";
    assert.equal(navigationUrl.validateNavigationValue(unicodeHost, "external-url").valid, true);
    assert.equal(navigationUrl.validateNavigationValue(unicodeHost, "external-url").idn, true);
    assert.equal(navigationUrl.getSafeExternalLink(unicodeHost), null, "ambiguous IDN is never a generated external link");
    assert.equal(navigationUrl.validateNavigationValue("xn--e1afmkfd.xn--p1ai,пример.рф", "domain-list").valid, true);
    assert.equal(navigationUrl.validateWebsiteFilterPattern("https://exam\u202Eple.test/*").code, "unicode_control");
    assert.equal(navigationUrl.validateNavigationValue("https://example.test/*", "website-filter").valid, true);

    const imported = "data:text/html,<script>alert(1)</script>";
    assert.deepEqual(navigationUrl.inspectImportedNavigationValue(imported, "navigation-url"), {
        kind: "raw_fallback",
        value: imported,
        verdict: { valid: false, code: "unsafe_scheme" },
    });
    assert.equal(navigationUrl.inspectImportedNavigationValue("https://example.test/", "navigation-url").kind, "typed");
    assert.equal(navigationUrl.retainsImportedRawNavigationValue(imported, imported, "navigation-url"), true);
    assert.equal(navigationUrl.retainsImportedRawNavigationValue("https://changed.example/", imported, "navigation-url"), false);
    assert.equal(navigationUrl.formatNavigationValidationMessage(
        () => "{field}: rejected by URL safety rule “{rule}”. It has not been applied.",
        "Bookmark URL",
        { code: "unsafe_scheme" },
    ), "Bookmark URL: rejected by URL safety rule “unsafe-scheme”. It has not been applied.");
    assert.equal(navigationUrl.formatNavigationValidationMessage(
        () => "{field}:{rule}",
        "",
        undefined,
    ), "URL:invalid-value");
});
