import assert from "node:assert/strict";
import test from "node:test";

import * as compare from "../../../../app/static/profiles_modules/compare_state.mjs";
import * as dirty from "../../../../app/static/profiles_modules/dirty_route_guard.mjs";
import * as listUrl from "../../../../app/static/profiles_modules/profile_list_url.mjs";
import * as policy from "../../../../app/static/profiles_modules/policy_document.mjs";
import * as preference from "../../../../app/static/profiles_modules/preference_values.mjs";
import * as review from "../../../../app/static/profiles_modules/review_state.mjs";
import * as workspace from "../../../../app/static/profiles_modules/workspace_state.mjs";

const context = {
    location: { origin: "https://bpm.test" },
    confirm: () => false,
    addEventListener: () => {},
};
globalThis.window = context;

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
        description: "Description", schema_version: "release-153", flags: { A: true }, compliance: { score: 1 },
    });
    assert.deepEqual(workspace.buildCreatePayload(form, { A: true }, { score: 1 }), {
        name: "Original", description: "Description", schema_version: "release-153", flags: { A: true }, compliance: { score: 1 },
    });
    assert.equal(workspace.buildCreatePayload(form, {}, {}, { name: "Override" }).name, "Override");
});
