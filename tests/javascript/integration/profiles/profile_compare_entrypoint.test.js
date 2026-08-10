import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import * as compare from "../../../../app/static/profiles_compare.js";
import * as compareState from "../../../../app/static/profiles_compare_state.js";

test("builds active profile search filters", () => {
    assert.deepEqual(compare.buildProfileSearchFilters("  Finance  "), {
        q: "Finance",
        lifecycle: "active",
        includeDeleted: false,
        limit: 40,
        sort: "updated_at",
        order: "desc",
    });
});

test("initializes independent selection sides", () => {
    const state = compare.createInitialState();
    state.left.selected = { id: 1, name: "Left" };

    assert.equal(state.left.selected.name, "Left");
    assert.equal(state.right.selected, null);
    assert.notEqual(state.left, state.right);
});

test("resolves optional preselected profile IDs", () => {
    assert.deepEqual(compare.resolvePreselectedProfileIds({
        href: "http://bpm.test/profiles/compare?left=7&right=abc&extra=9",
    }), { left: 7, right: null });
    assert.deepEqual(compare.resolvePreselectedProfileIds({
        href: "http://bpm.test/profiles/compare?left=-1&right=0",
    }), { left: null, right: null });
});

test("formats profile summary and escapes HTML", () => {
    assert.equal(
        compare.formatProfileSummary(
            { schema_version: "release-153", updated_at: "2026-06-05T12:00:00Z" },
            (value) => `Firefox ${value}`,
        ),
        "Firefox release-153 • 2026-06-05T12:00:00Z",
    );
    assert.equal(
        compare.escapeHtml("<b>Managed & safe</b>"),
        "&lt;b&gt;Managed &amp; safe&lt;/b&gt;",
    );
});

test("builds two-column setting rows", async () => {
    const contract = JSON.parse(await readFile(
        new URL("../../../fixtures/profile_compare_contract.json", import.meta.url),
        "utf8",
    ));
    const rows = compare.buildCompareRows(
        contract.profiles.left,
        contract.profiles.right,
        compareState,
    ).map((row) => ({
        id: row.id,
        kind: row.kind,
        settingKey: row.settingKey,
        leftState: row.left.state,
        leftStateLabel: row.left.stateLabel,
        leftDisplay: row.left.displayValue,
        rightState: row.right.state,
        rightStateLabel: row.right.stateLabel,
        rightDisplay: row.right.displayValue,
        changed: row.changed,
    }));

    assert.deepEqual(rows.map((row) => row.id), [
        "policy:DisableTelemetry",
        "policy:Homepage",
        "policy:SearchBar",
        "preference:browser.startup.homepage",
        "preference:browser.tabs.warnOnClose",
    ]);
    assert.deepEqual(rows[0], {
        id: "policy:DisableTelemetry",
        kind: "policy",
        settingKey: "DisableTelemetry",
        leftState: "equal",
        leftStateLabel: "Same value",
        leftDisplay: "true",
        rightState: "equal",
        rightStateLabel: "Same value",
        rightDisplay: "true",
        changed: false,
    });
    assert.deepEqual(
        [rows[1].leftState, rows[1].leftStateLabel, rows[1].rightState, rows[1].rightStateLabel, rows[1].rightDisplay],
        ["different", "Different value", "missing", "Missing", "Missing"],
    );
    assert.deepEqual([rows[2].leftState, rows[2].rightState], ["missing", "different"]);
    assert.deepEqual([rows[3].leftState, rows[3].rightState], ["different", "different"]);
    assert.deepEqual([rows[4].leftState, rows[4].rightState], ["equal", "equal"]);
});

test("labels managed preferences as first-class settings", () => {
    const preferenceLabels = compare.buildPreferenceLabelLookup(
        {
            known_preferences: [
                {
                    pref: "browser.startup.homepage",
                    label_key: "",
                    fallback: "Homepage URL",
                },
                {
                    pref: "browser.tabs.warnOnClose",
                    label_key: "profiles.warn_tabs",
                    fallback: "browser.tabs.warnOnClose",
                },
            ],
        },
        { "profiles.warn_tabs": "Warn before closing tabs" },
    );
    const rows = compare.buildCompareRows(
        {
            flags: {
                Preferences: {
                    "browser.startup.homepage": {
                        Status: "locked",
                        Value: "https://left.test",
                    },
                    "unknown.preference": { Status: "default", Value: true },
                },
            },
        },
        {
            flags: {
                Preferences: {
                    "browser.tabs.warnOnClose": { Status: "default", Value: true },
                },
            },
        },
        compareState,
        { preferenceLabels, preferenceKindLabel: "Managed preference", policyKindLabel: "Policy" },
    ).map((row) => ({
        id: row.id,
        kind: row.kind,
        kindLabel: row.kindLabel,
        label: row.label,
        settingKey: row.settingKey,
    }));

    assert.deepEqual(rows, [
        {
            id: "preference:browser.startup.homepage",
            kind: "preference",
            kindLabel: "Managed preference",
            label: "Homepage URL",
            settingKey: "Preferences.browser.startup.homepage",
        },
        {
            id: "preference:browser.tabs.warnOnClose",
            kind: "preference",
            kindLabel: "Managed preference",
            label: "Warn before closing tabs",
            settingKey: "Preferences.browser.tabs.warnOnClose",
        },
        {
            id: "preference:unknown.preference",
            kind: "preference",
            kindLabel: "Managed preference",
            label: "unknown.preference",
            settingKey: "Preferences.unknown.preference",
        },
    ]);
});

test("omits duplicate setting identity metadata", () => {
    const policy = compare.resolveSettingPresentation({
        kind: "policy",
        label: "AIControls",
        settingKey: "AIControls",
    });
    const preference = compare.resolveSettingPresentation(
        {
            kind: "preference",
            preferenceName: "browser.tabs.warnOnClose",
            label: "browser.tabs.warnOnClose",
            settingKey: "Preferences.browser.tabs.warnOnClose",
        },
        { preferenceLabels: { "browser.tabs.warnOnClose": "browser.tabs.warnOnClose" } },
    );
    const policyIdentity = compare.renderSettingIdentity({
        kind: "policy",
        kindLabel: policy.kindLabel,
        label: policy.label,
        settingKey: policy.settingKey,
    });
    const preferenceIdentity = compare.renderSettingIdentity({
        kind: "preference",
        kindLabel: preference.kindLabel,
        label: preference.label,
        settingKey: preference.settingKey,
    });

    assert.deepEqual(policy, { label: "AIControls", kindLabel: "Policy", settingKey: "AIControls" });
    assert.deepEqual(preference, {
        label: "browser.tabs.warnOnClose",
        kindLabel: "Managed preference",
        settingKey: "Preferences.browser.tabs.warnOnClose",
    });
    assert.match(policyIdentity, /data-compare-setting-label/);
    assert.doesNotMatch(policyIdentity, /data-compare-setting-key/);
    assert.equal(policyIdentity.split("AIControls").length - 1, 1);
    assert.match(preferenceIdentity, /data-compare-setting-key/);
    assert.equal(preferenceIdentity.split("browser.tabs.warnOnClose").length - 1, 2);
});

test("renders long setting identity and values safely", () => {
    const longPreference = "browser.enterprise.really.long.preference.name.with.many.sections.and.<unsafe>";
    const rows = compare.buildCompareRows(
        {
            flags: {
                Preferences: {
                    [longPreference]: {
                        Status: "locked",
                        Value: `https://example.test/${"a".repeat(90)}`,
                    },
                },
            },
        },
        {
            flags: {
                Preferences: {
                    [longPreference]: {
                        Status: "default",
                        Value: `https://example.test/${"b".repeat(90)}`,
                    },
                },
            },
        },
        compareState,
        {
            preferenceLabels: {
                [longPreference]: `Readable <long> enterprise preference label ${"x".repeat(80)}`,
            },
            preferenceKindLabel: "Managed preference",
            stateLabels: { missing: "Missing", equal: "Same value", different: "Different value" },
        },
    );
    const row = rows[0];
    const identity = compare.renderSettingIdentity(row);

    assert.match(row.id, /^preference:browser\.enterprise\.really\.long\.preference/);
    assert.equal(row.kind, "preference");
    assert.deepEqual([row.left.state, row.right.state], ["different", "different"]);
    assert.match(row.settingKey, /^Preferences\.browser\.enterprise\.really\.long/);
    assert.match(row.label, /^Readable <long> enterprise preference label/);
    assert.match(identity, /&lt;long&gt;/);
    assert.match(identity, /&lt;unsafe&gt;/);
    assert.match(identity, /data-compare-setting-label/);
    assert.match(identity, /data-compare-setting-key/);
    assert.match(row.left.displayValue, /"Status":"locked"/);
    assert.match(row.right.displayValue, /"Status":"default"/);
    assert.ok(row.left.displayValue.length > 120);
    assert.ok(row.right.displayValue.length > 120);
});

test("supports accessible value state labels", () => {
    const rows = compare.buildCompareRows(
        { flags: { DisableTelemetry: true, Homepage: { URL: "https://left.test" } } },
        { flags: { DisableTelemetry: true, SearchBar: "separate" } },
        compareState,
        { stateLabels: { missing: "Missing", equal: "Same", different: "Changed" } },
    ).map((row) => ({
        id: row.id,
        leftState: row.left.state,
        leftLabel: row.left.stateLabel,
        rightState: row.right.state,
        rightLabel: row.right.stateLabel,
    }));

    assert.deepEqual(rows, [
        {
            id: "policy:DisableTelemetry",
            leftState: "equal",
            leftLabel: "Same",
            rightState: "equal",
            rightLabel: "Same",
        },
        {
            id: "policy:Homepage",
            leftState: "different",
            leftLabel: "Changed",
            rightState: "missing",
            rightLabel: "Missing",
        },
        {
            id: "policy:SearchBar",
            leftState: "missing",
            leftLabel: "Missing",
            rightState: "different",
            rightLabel: "Changed",
        },
    ]);
});
