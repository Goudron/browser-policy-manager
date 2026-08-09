import assert from "node:assert/strict";
import test from "node:test";

import * as compareState from "../../../../app/static/profiles_compare_state.js";

test("normalizes nested objects and arrays", () => {
    const normalized = compareState.normalizeValue({
        beta: [{ z: 1, a: 2 }],
        alpha: { z: true, a: false },
    });

    assert.deepEqual(Object.keys(normalized), ["alpha", "beta"]);
    assert.deepEqual(Object.keys(normalized.alpha), ["a", "z"]);
    assert.deepEqual(Object.keys(normalized.beta[0]), ["a", "z"]);
    assert.deepEqual(normalized, {
        alpha: { a: false, z: true },
        beta: [{ a: 2, z: 1 }],
    });
});

test("collects missing branches and array changes", () => {
    assert.deepEqual(
        compareState.collectDiffPaths(
            {
                Homepage: { URL: "https://example.test" },
                SearchEngines: {
                    Add: [{ Name: "Internal", URLTemplate: "https://a.test" }],
                },
            },
            {
                SearchEngines: {
                    Add: [{ Name: "Internal", URLTemplate: "https://b.test" }],
                },
            },
        ),
        [["Homepage", "URL"], ["SearchEngines", "Add"]],
    );
});

test("collects policies and preferences in stable order", () => {
    const rows = compareState.collectProfileSettingKeys(
        {
            SearchBar: "unified",
            DisableTelemetry: true,
            Preferences: {
                "browser.tabs.warnOnClose": false,
                "browser.startup.homepage": "https://left.test",
            },
        },
        {
            Homepage: { URL: "https://right.test" },
            Preferences: {
                "browser.startup.homepage": "https://right.test",
            },
        },
    );

    assert.deepEqual(rows.map((row) => row.id), [
        "policy:DisableTelemetry",
        "policy:Homepage",
        "policy:SearchBar",
        "preference:browser.startup.homepage",
        "preference:browser.tabs.warnOnClose",
    ]);
    assert.equal(rows[0].settingKey, "DisableTelemetry");
    assert.equal(rows[3].settingKey, "Preferences.browser.startup.homepage");
});

test("reads and formats policy and preference values", () => {
    const flags = {
        DisableTelemetry: true,
        Homepage: { Locked: true, URL: "https://example.test" },
        Preferences: { "browser.tabs.warnOnClose": false },
    };
    const policy = compareState.collectProfileSettingKeys(flags, {})[0];
    const preference = {
        kind: "preference",
        preferenceName: "browser.tabs.warnOnClose",
    };
    const missing = {
        kind: "preference",
        preferenceName: "browser.startup.homepage",
    };

    assert.deepEqual({
        policy: compareState.formatCompareValue(compareState.readSettingValue(flags, policy)),
        objectValue: compareState.formatCompareValue(
            compareState.readSettingValue(flags, { kind: "policy", policyId: "Homepage" }),
        ),
        preference: compareState.formatCompareValue(
            compareState.readSettingValue(flags, preference),
        ),
        missing: compareState.formatCompareValue(compareState.readSettingValue(flags, missing)),
    }, {
        policy: "true",
        objectValue: '{"Locked":true,"URL":"https://example.test"}',
        preference: "false",
        missing: "Not set",
    });
});
