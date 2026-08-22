import assert from "node:assert/strict";
import test from "node:test";

import { create as createInventory } from "../../../../app/static/profiles_settings_inventory.js";
import { loadAllSettingsFixture, translate } from "../../support/settings_harness.js";

const fixture = loadAllSettingsFixture();

function inventoryFor(testCase = {}, catalogs = fixture) {
    return createInventory({
        dependencies: {
            t: translate(),
            getActiveWizardSchemaVersion: () => testCase.schema_version || fixture.schema_version,
            getValidationIssues: () => testCase.issues || [],
            getComplianceInfo: () => testCase.compliance || {},
            getManualEdits: () => testCase.manual_edits || [],
        },
        allSettingsCategoryCatalog: catalogs.all_settings_category_catalog,
        wizardPreferencesCatalog: catalogs.wizard_preferences_catalog,
        wizardSchemaShellCatalog: catalogs.wizard_schema_shell_catalog,
    });
}

const entryKey = (entry) => `${entry.kind}:${entry.id}`;
const byKey = (entries) => Object.fromEntries(entries.map((entry) => [entryKey(entry), entry]));

function inventoryCounts(entries) {
    return {
        total_entries: entries.length,
        policy_entries: entries.filter((entry) => entry.kind === "policy").length,
        preference_entries: entries.filter((entry) => entry.kind === "preference").length,
        configured_entries: entries.filter((entry) => entry.configured).length,
        configured_policy_entries: entries.filter((entry) => entry.kind === "policy" && entry.configured).length,
        configured_preference_entries: entries.filter((entry) => entry.kind === "preference" && entry.configured).length,
        unknown_policy_entries: entries.filter((entry) => entry.kind === "policy" && entry.unknown).length,
        imported_preference_entries: entries.filter((entry) => entry.kind === "preference" && entry.unknown).length,
        guided_policy_entries: entries.filter((entry) => entry.kind === "policy" && entry.guided).length,
        raw_fallback_policy_entries: entries.filter((entry) => entry.kind === "policy" && entry.rawFallback).length,
        deprecated_policy_entries: entries.filter((entry) => entry.kind === "policy" && entry.deprecated).length,
    };
}

function assertCounts(entries, expected) {
    const expectedCounts = Object.fromEntries(
        Object.entries(expected).filter(([key]) => key !== "schema_version"),
    );
    assert.deepEqual(inventoryCounts(entries), expectedCounts);
}

test("inventory collects policy, preference, unknown, source, and attention metadata", () => {
    const catalogs = {
        all_settings_category_catalog: {
            categories: [{ id: "browser-access" }, { id: "raw-unmapped" }],
            categories_by_id: {
                "browser-access": { id: "browser-access", title_key: "category.browser", fallback: "Browser" },
                "raw-unmapped": { id: "raw-unmapped", title_key: "category.raw", fallback: "Raw" },
            },
            policy_section_to_category_id: { browser_behavior: "browser-access" },
            preference_section_to_category_id: { general: "browser-access" },
        },
        wizard_preferences_catalog: {
            known_preferences: [{ pref: "browser.test.pref", section_id: "general" }],
            sections: [{ id: "general", prefixes: ["browser."] }],
        },
        wizard_schema_shell_catalog: {
            steps: [{ step: 2 }],
            channels: {
                "release-test": {
                    steps: {
                        2: {
                            recommended: [{ id: "DisableTelemetry", section_id: "browser_behavior", target: "policy:DisableTelemetry" }],
                            additional: [
                                { id: "CisPolicy", section_id: "browser_behavior" },
                                { id: "CatalogOnly", section_id: "browser_behavior" },
                                { id: "ReviewPolicy", section_id: "browser_behavior" },
                            ],
                            raw_fallback: [{ id: "RawPolicy", section_id: "browser_behavior", support_level: "fallback" }],
                        },
                    },
                },
            },
        },
    };
    const testCase = {
        schema_version: "release-test",
        issues: [
            { policy: "DisableTelemetry", path: ["DisableTelemetry"] },
            { policy: "Preferences", path: ["Preferences", "browser.test.pref", "Value"] },
            { policy: "Preferences", path: ["Preferences", "company.unknown"] },
        ],
        compliance: {
            layer: "cis_l2",
            decisions: [
                { path: ["DisableTelemetry"], decision: "already_satisfied", selected_source: "base", recommendation_ids: ["1.1.35"] },
                { path: ["CisPolicy"], decision: "added_from_cis", selected_source: "cis", recommendation_ids: ["fixture.cis"] },
                { path: ["ReviewPolicy", "Mode"], decision: "manual_review_kept_base", selected_source: "base", recommendation_ids: ["fixture.review"], review_required: true },
                { path: ["Preferences"], decision: "added_from_cis", selected_source: "cis" },
            ],
        },
        manual_edits: [{ path: ["DisableTelemetry"], previous_value: false, current_value: true }],
    };
    const entries = inventoryFor(testCase, catalogs).collect({
        DisableTelemetry: true,
        CisPolicy: true,
        ReviewPolicy: { Mode: "manual" },
        RawPolicy: { Enabled: true },
        CustomPolicy: true,
        Preferences: {
            "browser.test.pref": { Value: true, Status: "default", Type: "boolean" },
            "company.unknown": { Value: "locked", Status: "locked", Type: "string" },
        },
    });
    const entriesById = Object.fromEntries(entries.map((entry) => [entry.id, entry]));

    assert.equal(entriesById.DisableTelemetry.state, "configured");
    assert.equal(entriesById.DisableTelemetry.schemaStepNumber, 2);
    assert.equal(entriesById.DisableTelemetry.schemaBucket, "recommended");
    assert.equal(entriesById.DisableTelemetry.validationIssueCount, 1);
    assert.deepEqual(entriesById.DisableTelemetry.validationPaths[0], ["DisableTelemetry"]);
    assert.ok(entriesById.DisableTelemetry.sources.includes("manual"));
    assert.ok(entriesById.DisableTelemetry.sources.includes("baseline"));
    assert.ok(entriesById.DisableTelemetry.sources.includes("cis"));
    assert.deepEqual(entriesById.DisableTelemetry.sourceDetails.recommendationIds, ["1.1.35"]);
    assert.equal(entriesById.DisableTelemetry.cis.primaryDecisionType, "already_satisfied");
    assert.equal(entriesById.DisableTelemetry.cis.primarySelectedSource, "base");
    assert.ok(entriesById.DisableTelemetry.cis.decisionKeys.includes("cis:1.1.35"));
    assert.equal(entriesById.DisableTelemetry.attentionFlags.manualEdit, true);
    assert.ok(entriesById.CisPolicy.sources.includes("cis"));
    assert.equal(entriesById.ReviewPolicy.attentionFlags.cisReviewRequired, true);
    assert.equal(entriesById.ReviewPolicy.cis.reviewRequired, true);
    assert.equal(entriesById.ReviewPolicy.value, "1 keys (Mode)");
    assert.ok(entriesById.CatalogOnly.sources.includes("catalog"));
    assert.equal(entriesById.RawPolicy.attentionFlags.rawFallback, true);
    assert.ok(entriesById.RawPolicy.sources.includes("raw-fallback"));
    assert.equal(entriesById.CustomPolicy.unknown, true);
    assert.ok(entriesById.CustomPolicy.sources.includes("imported"));
    assert.equal(entriesById["browser.test.pref"].kind, "preference");
    assert.ok(entriesById["browser.test.pref"].sources.includes("cis"));
    assert.equal(entriesById["browser.test.pref"].preferenceSectionId, "general");
    assert.equal(entriesById["browser.test.pref"].editor.preferenceValue.Value, true);
    assert.equal(entriesById["company.unknown"].attentionFlags.invalid, true);
    assert.equal(entriesById["company.unknown"].unknown, true);
    assert.equal(entriesById["company.unknown"].editor.knownPreference, null);
});

test("inventory maps every Python-owned source-state regression fixture", () => {
    for (const testCase of fixture.source_state_cases) {
        const inventory = inventoryFor(testCase);
        const entries = inventory.collect(testCase.flags);
        const expected = testCase.expectation;
        const entry = entries.find((item) => item.id === expected.entry_id && item.kind === expected.kind);
        assert.ok(entry, `${testCase.id}: missing expected entry`);
        for (const source of expected.expected_sources) {
            assert.ok(entry.sources.includes(source), `${testCase.id}: missing source ${source}`);
        }
        if (expected.decision) {
            assert.ok(entry.sourceDetails.decisions.some((decision) => decision.decision === expected.decision));
            assert.ok(entry.cis.decisionTypes.includes(expected.decision));
        }
        assert.equal(entry.sourceDetails.decisionKeys.length, entry.cis.decisionKeys.length);
        if (expected.review_required) assert.equal(entry.attentionFlags.cisReviewRequired, true);
        if (expected.raw_fallback) assert.ok(entry.sources.includes("raw-fallback"));
        if (expected.imported_unknown) assert.equal(entry.unknown, true);
        if (expected.manually_edited) assert.equal(entry.attentionFlags.manualEdit, true);
    }
});

test("inventory constructs blank, corporate, CIS, unknown, raw, and invalid profiles", () => {
    const cases = fixture.profile_variants;
    const collect = (testCase) => inventoryFor(testCase).collect(testCase.flags || {});

    const blank = collect(cases.blank);
    assertCounts(blank, cases.blank.counts);
    assert.ok(blank.every((entry) => entry.state === "available"));
    assert.ok(blank.every((entry) => entry.sources.includes("catalog")));
    for (const policyId of [
        "Authentication",
        "Certificates",
        "DisableSecurityBypass",
        "SecurityDevices",
        "WindowsSSO",
    ]) {
        const entry = byKey(blank)[`policy:${policyId}`];
        assert.ok(entry, `${policyId}: certificate owner must stay visible in All settings`);
        assert.equal(entry.guided, true);
        assert.equal(entry.schemaStepNumber, 4);
        assert.equal(entry.schemaStepId, "certificates_trust");
    }

    const basic = collect(cases.basicCorporate);
    assertCounts(basic, cases.basicCorporate.counts);
    const basicByKey = byKey(basic);
    assert.equal(basicByKey["policy:DisableTelemetry"].state, "configured");
    assert.ok(basicByKey["policy:DisableTelemetry"].sources.includes("manual"));
    assert.equal(basicByKey["policy:DisableTelemetry"].cis.hasDecision, false);

    const cis = collect(cases.cisL2);
    assertCounts(cis, cases.cisL2.counts);
    const cisWrapped = inventoryFor(cases.cisL2).collect({ policies: cases.cisL2.flags });
    assertCounts(cisWrapped, cases.cisL2.counts);
    const cisByKey = byKey(cis);
    assert.equal(cisByKey["policy:DisableTelemetry"].cis.hasDecision, true);
    assert.ok(cisByKey["policy:DisableTelemetry"].sources.includes("cis"));
    assert.equal(
        cis.filter((entry) => entry.attentionFlags.cisReviewRequired).length,
        cases.cisL2.manual_review_count,
    );

    const unknown = collect(cases.unknownImport);
    assertCounts(unknown, cases.unknownImport.counts);
    const unknownByKey = byKey(unknown);
    assert.ok(unknownByKey["policy:CustomEnterprisePolicy"].sources.includes("unknown"));
    assert.ok(unknownByKey["preference:company.managed.preference"].sources.includes("imported"));
    assert.equal(unknownByKey[`preference:${cases.unknownImport.known_pref}`].unknown, false);

    const rawByKey = byKey(collect(cases.rawFallback));
    assert.equal(rawByKey[`policy:${cases.rawFallback.raw_id}`].rawFallback, true);
    assert.ok(rawByKey[`policy:${cases.rawFallback.raw_id}`].sources.includes("raw-fallback"));

    const invalid = collect(cases.invalid);
    const invalidByKey = byKey(invalid);
    assert.equal(invalid.filter((entry) => entry.attentionFlags.invalid).length, 2);
    assert.equal(invalidByKey["policy:DisableTelemetry"].validationIssueCount, 1);
    assert.equal(invalidByKey[`preference:${cases.invalid.known_pref}`].validationIssueCount, 1);
    assert.equal(invalidByKey[`preference:${cases.invalid.known_pref}`].attentionFlags.reviewRequired, true);
});
