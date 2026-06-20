from __future__ import annotations

import json
import subprocess
import textwrap
from dataclasses import asdict
from pathlib import Path

from app.core.schema_channels import CURRENT_RELEASE_SCHEMA_CHANNEL
from app.web.firefox_all_settings_categories import get_all_settings_category_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_starter_presets import build_wizard_starter_document
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from tests.support import (
    build_all_settings_inventory_counts,
    build_all_settings_source_state_regression_fixtures,
    build_corporate_cis_l2_profile_fixture,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"


def _static_source(filename: str) -> str:
    return (STATIC_ROOT / filename).read_text(encoding="utf-8")


def test_settings_inventory_frontend_module_exposes_stable_entry_model():
    source = _static_source("profiles_settings_inventory.js")

    for snippet in (
        "window.BPMProfilesSettingsInventory = { create };",
        "function collect(sourceData = {})",
        "function formatPreviewItem(value)",
        "function appendPreview(summary, values)",
        "function formatStructuredValue(value)",
        "function normalizeSourceData(sourceData = {})",
        "function buildPolicyEntries(sourceData)",
        "function buildPreferenceEntries(sourceData)",
        "function buildUnknownPolicyEntries(sourceData, knownPolicyIds)",
        "function finalizeEntry(entry)",
        "state,",
        "source: sources[0] || \"\",",
        "sources,",
        "cis,",
        "sourceDetails: {",
        "function buildSourceAttribution(entry)",
        "function decisionSources(decision)",
        "function cisDecisionKey(decision)",
        "function getCisDecisionMetadata(entryOrDecisions)",
        "function sourceTags(entry, attribution = {})",
        "getComplianceInfo,",
        "getManualEdits,",
        "attentionFlags: attention,",
        "validationPaths: entry.validationPaths || [],",
        "validationIssueCount: Number(entry.validationIssueCount || 0),",
        "valueSummary,",
        "editor: {",
        "schemaItem: entry.schemaItem || null,",
        "knownPreference: entry.knownPreference || null,",
        "preferenceSectionId: entry.preferenceSectionId || \"\",",
        "preferenceSection: entry.preferenceSection || null,",
        "preferenceValue: entry.preferenceValue ?? null,",
        "schemaBucket: bucketKey,",
        "schemaStepId: stepMeta.id || \"\",",
        "schemaStepNumber: stepMeta.step || 0,",
        "function getPreferenceSection(sectionId)",
        "function getKnownPreference(prefName)",
        "function validationPathsForEntry(entry)",
        "function issueMatchesEntry(issue, entry)",
        "function getIssuesByEntryKey(entries)",
    ):
        assert snippet in source


def test_all_settings_list_uses_settings_inventory_as_collection_source():
    list_source = _static_source("profiles_all_settings_list.js")
    bootstrap_source = _static_source("profiles_bootstrap_core.js")
    asset_source = (REPO_ROOT / "app/templates/profiles/_page_route_assets.html").read_text(
        encoding="utf-8"
    )

    assert '"/static/profiles_settings_inventory.js"' in asset_source
    assert asset_source.index('"/static/profiles_all_settings_state.js"') < asset_source.index(
        '"/static/profiles_settings_inventory.js"'
    )
    assert asset_source.index('"/static/profiles_settings_inventory.js"') < asset_source.index(
        '"/static/profiles_all_settings_list.js"'
    )
    assert "const settingsInventory = window.BPMProfilesSettingsInventory.create({" in bootstrap_source
    assert "settingsInventory," in bootstrap_source
    assert "settingsInventory?.collect?.(sourceData) || []" in list_source


def test_policy_entry_collection_is_not_duplicated_in_all_settings_consumers():
    inventory_source = _static_source("profiles_settings_inventory.js")
    list_source = _static_source("profiles_all_settings_list.js")
    search_source = _static_source("profiles_settings_search.js")

    assert "function buildPolicyEntries(sourceData)" in inventory_source
    assert "function buildPolicyEntries(sourceData)" not in list_source
    assert "function buildPolicyEntries(sourceData)" not in search_source
    assert "wizardSchemaShellCatalog.steps" not in list_source
    assert "wizardSchemaShellCatalog.steps" not in search_source
    assert "stepData.recommended" not in search_source
    assert "stepData.additional" not in search_source
    assert "stepData.raw_fallback" not in search_source
    assert "function buildPolicyBlueprintSearchEntries(allSettingsEntries = [])" in search_source
    assert ".filter((entry) => entry?.kind === \"policy\" && entry.schemaItem)" in search_source
    assert "buildShellPolicyTargetIndex(allSettingsEntries);" in search_source


def test_preference_entry_collection_is_not_duplicated_in_all_settings_consumers():
    inventory_source = _static_source("profiles_settings_inventory.js")
    detail_source = _static_source("profiles_all_settings_detail.js")

    assert "function buildPreferenceEntries(sourceData)" in inventory_source
    assert "function buildPreferenceEntries(sourceData)" not in detail_source
    assert "wizardPreferencesCatalog.known_preferences" not in detail_source
    assert "settingsInventory?.getKnownPreference?.(prefName)" in detail_source
    assert "entry.editor?.knownPreference" in detail_source


def test_settings_inventory_runtime_collects_policy_preference_unknown_and_attention_entries():
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_inventory.js"}", "utf8"));

        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_list_value_object": "{{count}} keys",
            "profiles.settings_list_value_array": "{{count}} items",
        }}[key] || key);

        const inventory = window.BPMProfilesSettingsInventory.create({{
            dependencies: {{
                t,
                getActiveWizardSchemaVersion: () => "release-test",
                getValidationIssues: () => [
                    {{ policy: "DisableTelemetry", path: ["DisableTelemetry"] }},
                    {{ policy: "Preferences", path: ["Preferences", "browser.test.pref", "Value"] }},
                    {{ policy: "Preferences", path: ["Preferences", "company.unknown"] }},
                ],
                getComplianceInfo: () => ({{
                    layer: "cis_l2",
                    decisions: [
                        {{
                            path: ["DisableTelemetry"],
                            decision: "already_satisfied",
                            selected_source: "base",
                            recommendation_ids: ["1.1.35"],
                        }},
                        {{
                            path: ["CisPolicy"],
                            decision: "added_from_cis",
                            selected_source: "cis",
                            recommendation_ids: ["fixture.cis"],
                        }},
                        {{
                            path: ["ReviewPolicy", "Mode"],
                            decision: "manual_review_kept_base",
                            selected_source: "base",
                            recommendation_ids: ["fixture.review"],
                            review_required: true,
                        }},
                        {{
                            path: ["Preferences"],
                            decision: "added_from_cis",
                            selected_source: "cis",
                        }},
                    ],
                }}),
                getManualEdits: () => [
                    {{
                        path: ["DisableTelemetry"],
                        previous_value: false,
                        current_value: true,
                    }},
                ],
            }},
            allSettingsCategoryCatalog: {{
                categories: [
                    {{ id: "browser-access" }},
                    {{ id: "raw-unmapped" }},
                ],
                categories_by_id: {{
                    "browser-access": {{
                        id: "browser-access",
                        title_key: "category.browser",
                        fallback: "Browser",
                    }},
                    "raw-unmapped": {{
                        id: "raw-unmapped",
                        title_key: "category.raw",
                        fallback: "Raw",
                    }},
                }},
                policy_section_to_category_id: {{ browser_behavior: "browser-access" }},
                preference_section_to_category_id: {{ general: "browser-access" }},
            }},
            wizardPreferencesCatalog: {{
                known_preferences: [
                    {{ pref: "browser.test.pref", section_id: "general" }},
                ],
                sections: [
                    {{ id: "general", prefixes: ["browser."] }},
                ],
            }},
            wizardSchemaShellCatalog: {{
                steps: [{{ step: 2 }}],
                channels: {{
                    "release-test": {{
                        steps: {{
                            "2": {{
                                recommended: [
                                    {{
                                        id: "DisableTelemetry",
                                        section_id: "browser_behavior",
                                        target: "policy:DisableTelemetry",
                                    }},
                                ],
                                additional: [
                                    {{
                                        id: "CisPolicy",
                                        section_id: "browser_behavior",
                                    }},
                                    {{
                                        id: "CatalogOnly",
                                        section_id: "browser_behavior",
                                    }},
                                    {{
                                        id: "ReviewPolicy",
                                        section_id: "browser_behavior",
                                    }},
                                ],
                                raw_fallback: [
                                    {{
                                        id: "RawPolicy",
                                        section_id: "browser_behavior",
                                        support_level: "fallback",
                                    }},
                                ],
                            }},
                        }},
                    }},
                }},
            }},
        }});

        const entries = inventory.collect({{
            DisableTelemetry: true,
            CisPolicy: true,
            ReviewPolicy: {{ Mode: "manual" }},
            RawPolicy: {{ Enabled: true }},
            CustomPolicy: true,
            Preferences: {{
                "browser.test.pref": {{
                    Value: true,
                    Status: "default",
                    Type: "boolean",
                }},
                "company.unknown": {{
                    Value: "locked",
                    Status: "locked",
                    Type: "string",
                }},
            }},
        }});

        const byId = Object.fromEntries(entries.map((entry) => [entry.id, entry]));
        if (byId.DisableTelemetry.state !== "configured") throw new Error("policy state");
        if (byId.DisableTelemetry.schemaStepId !== "") throw new Error("missing shell step id fallback");
        if (byId.DisableTelemetry.schemaStepNumber !== 2) throw new Error("policy step number");
        if (byId.DisableTelemetry.schemaBucket !== "recommended") throw new Error("policy bucket");
        if (byId.DisableTelemetry.validationIssueCount !== 1) throw new Error("policy issue mapping");
        if (byId.DisableTelemetry.attentionFlags.validationIssueCount !== 1) throw new Error("policy attention count");
        if (byId.DisableTelemetry.validationPaths[0][0] !== "DisableTelemetry") throw new Error("policy validation path");
        if (!byId.DisableTelemetry.sources.includes("manual")) throw new Error("policy source");
        if (!byId.DisableTelemetry.sources.includes("baseline")) throw new Error("baseline source");
        if (!byId.DisableTelemetry.sources.includes("cis")) throw new Error("satisfied CIS source");
        if (byId.DisableTelemetry.sourceDetails.recommendationIds[0] !== "1.1.35") throw new Error("source recommendation ids");
        if (byId.DisableTelemetry.cis.primaryDecisionType !== "already_satisfied") throw new Error("primary CIS decision type");
        if (byId.DisableTelemetry.cis.primarySelectedSource !== "base") throw new Error("primary CIS selected source");
        if (!byId.DisableTelemetry.cis.decisionKeys.includes("cis:1.1.35")) throw new Error("CIS decision key");
        if (inventory.cisDecisionKey(byId.DisableTelemetry.cis.primaryDecision) !== "cis:1.1.35") throw new Error("exported CIS key helper");
        if (inventory.getCisDecisionMetadata(byId.DisableTelemetry).recommendationIds[0] !== "1.1.35") throw new Error("exported CIS metadata helper");
        if (byId.DisableTelemetry.attentionFlags.manualEdit !== true) throw new Error("manual edit flag");
        if (!byId.CisPolicy.sources.includes("cis")) throw new Error("cis source");
        if (byId.CisPolicy.cis.selectedSources[0] !== "cis") throw new Error("cis selected source");
        if (byId.ReviewPolicy.attentionFlags.cisReviewRequired !== true) throw new Error("CIS review attention flag");
        if (byId.ReviewPolicy.cis.reviewRequired !== true) throw new Error("CIS review metadata");
        if (!byId.ReviewPolicy.cis.decisionTypes.includes("manual_review_kept_base")) throw new Error("CIS review decision type");
        if (byId.ReviewPolicy.value !== "1 keys (Mode)") throw new Error(`policy object summary: ${{byId.ReviewPolicy.value}}`);
        if (byId.ReviewPolicy.value.includes("{{")) throw new Error("policy summary leaked JSON object");
        if (!byId.CatalogOnly.sources.includes("catalog")) throw new Error("catalog source");
        if (byId.RawPolicy.attentionFlags.rawFallback !== true) throw new Error("raw flag");
        if (!byId.RawPolicy.sources.includes("raw-fallback")) throw new Error("raw source");
        if (byId.RawPolicy.value !== "1 keys (Enabled)") throw new Error(`raw policy object summary: ${{byId.RawPolicy.value}}`);
        if (byId.CustomPolicy.unknown !== true) throw new Error("unknown policy");
        if (!byId.CustomPolicy.sources.includes("imported")) throw new Error("unknown policy source");
        if (!byId.CustomPolicy.sources.includes("unknown")) throw new Error("unknown source");
        if (byId["browser.test.pref"].kind !== "preference") throw new Error("known preference");
        if (!byId["browser.test.pref"].sources.includes("cis")) throw new Error("preference cis source");
        if (byId["browser.test.pref"].preferenceSectionId !== "general") throw new Error("preference section");
        if (!byId["browser.test.pref"].preferenceSection) throw new Error("preference section metadata");
        if (!byId["browser.test.pref"].editor.knownPreference) throw new Error("known preference metadata");
        if (byId["browser.test.pref"].editor.preferenceValue.Value !== true) throw new Error("preference value metadata");
        if (byId["browser.test.pref"].validationIssueCount !== 1) throw new Error("known preference issue mapping");
        if (byId["browser.test.pref"].validationPaths[0].join(".") !== "Preferences.browser.test.pref") throw new Error("known preference validation path");
        if (byId["company.unknown"].attentionFlags.invalid !== true) throw new Error("preference issue");
        if (byId["company.unknown"].validationIssueCount !== 1) throw new Error("unknown preference issue count");
        if (byId["company.unknown"].editor.preference !== "company.unknown") throw new Error("editor metadata");
        if (byId["company.unknown"].unknown !== true) throw new Error("unknown preference flag");
        if (byId["company.unknown"].editor.knownPreference !== null) throw new Error("unknown preference metadata");
        if (!byId["company.unknown"].valueSummary.includes("locked")) throw new Error("value summary");
        if (byId["company.unknown"].value.includes("{{")) throw new Error("preference summary leaked JSON object");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_settings_inventory_runtime_maps_source_state_regression_fixtures():
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    cases = [
        {
            "id": fixture.id,
            "schema_version": fixture.schema_version,
            "flags": fixture.flags,
            "compliance": fixture.compliance,
            "expectation": asdict(fixture.expectation),
            "manual_edits": [asdict(edit) for edit in fixture.manual_edits],
        }
        for fixture in build_all_settings_source_state_regression_fixtures()
    ]
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_inventory.js"}", "utf8"));

        const cases = {json.dumps(cases)};
        const allSettingsCategoryCatalog = {json.dumps(get_all_settings_category_catalog())};
        const wizardPreferencesCatalog = {json.dumps(wizard_preferences_catalog)};
        const wizardSchemaShellCatalog = {json.dumps(get_wizard_schema_shell_catalog(wizard_preferences_catalog))};
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_list_value_object": "{{count}} keys",
            "profiles.settings_list_value_array": "{{count}} items",
        }}[key] || key);

        cases.forEach((testCase) => {{
            const inventory = window.BPMProfilesSettingsInventory.create({{
                dependencies: {{
                    t,
                    getActiveWizardSchemaVersion: () => testCase.schema_version,
                    getValidationIssues: () => [],
                    getComplianceInfo: () => testCase.compliance,
                    getManualEdits: () => testCase.manual_edits,
                }},
                allSettingsCategoryCatalog,
                wizardPreferencesCatalog,
                wizardSchemaShellCatalog,
            }});
            const entries = inventory.collect(testCase.flags);
            const expected = testCase.expectation;
            const entry = entries.find((item) =>
                item.id === expected.entry_id && item.kind === expected.kind
            );
            if (!entry) throw new Error(`${{testCase.id}} missing expected entry`);
            expected.expected_sources.forEach((source) => {{
                if (!entry.sources.includes(source)) {{
                    throw new Error(`${{testCase.id}} missing source ${{source}}`);
                }}
            }});
            if (expected.decision && !entry.sourceDetails.decisions.some((decision) =>
                decision.decision === expected.decision
            )) {{
                throw new Error(`${{testCase.id}} missing decision attribution`);
            }}
            if (expected.decision && !entry.cis.decisionTypes.includes(expected.decision)) {{
                throw new Error(`${{testCase.id}} missing CIS decision metadata`);
            }}
            if (entry.sourceDetails.decisionKeys.length !== entry.cis.decisionKeys.length) {{
                throw new Error(`${{testCase.id}} mismatched CIS decision keys`);
            }}
            if (expected.review_required && entry.attentionFlags.cisReviewRequired !== true) {{
                throw new Error(`${{testCase.id}} missing CIS review flag`);
            }}
            if (expected.raw_fallback && !entry.sources.includes("raw-fallback")) {{
                throw new Error(`${{testCase.id}} missing raw fallback source`);
            }}
            if (expected.imported_unknown && entry.unknown !== true) {{
                throw new Error(`${{testCase.id}} missing unknown flag`);
            }}
            if (expected.manually_edited && entry.attentionFlags.manualEdit !== true) {{
                throw new Error(`${{testCase.id}} missing manual edit flag`);
            }}
        }});
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)


def test_settings_inventory_runtime_constructs_core_profile_variants():
    schema_version = CURRENT_RELEASE_SCHEMA_CHANNEL
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    known_pref = next(
        item["pref"]
        for item in wizard_preferences_catalog.get("known_preferences", [])
        if item.get("pref")
    )
    source_state_fixtures = {
        fixture.id: fixture
        for fixture in build_all_settings_source_state_regression_fixtures(
            schema_version=schema_version
        )
    }
    basic_corporate_flags = build_wizard_starter_document("basic_corporate", schema_version)
    corporate_cis = build_corporate_cis_l2_profile_fixture(schema_version=schema_version)
    unknown_flags = {
        "DisableTelemetry": True,
        "CustomEnterprisePolicy": {"enabled": True},
        "Preferences": {
            known_pref: {
                "Value": True,
                "Status": "default",
                "Type": "boolean",
            },
            "company.managed.preference": {
                "Value": "strict",
                "Status": "locked",
                "Type": "string",
            },
        },
    }
    invalid_flags = {
        "DisableTelemetry": True,
        "Preferences": {
            known_pref: {
                "Value": True,
                "Status": "default",
                "Type": "boolean",
            },
        },
    }
    raw_fallback_fixture = source_state_fixtures["raw-fallback-policy"]
    cases = {
        "blank": {
            "schema_version": schema_version,
            "flags": {},
            "counts": build_all_settings_inventory_counts(
                schema_version=schema_version,
                flags={},
            ).as_dict(),
        },
        "basicCorporate": {
            "schema_version": schema_version,
            "flags": basic_corporate_flags,
            "counts": build_all_settings_inventory_counts(
                schema_version=schema_version,
                flags=basic_corporate_flags,
            ).as_dict(),
        },
        "cisL2": {
            "schema_version": schema_version,
            "flags": corporate_cis.flags,
            "compliance": corporate_cis.compliance,
            "counts": build_all_settings_inventory_counts(
                schema_version=schema_version,
                flags=corporate_cis.flags,
            ).as_dict(),
            "manual_review_count": corporate_cis.manual_review_count,
        },
        "unknownImport": {
            "schema_version": schema_version,
            "flags": unknown_flags,
            "counts": build_all_settings_inventory_counts(
                schema_version=schema_version,
                flags=unknown_flags,
            ).as_dict(),
            "known_pref": known_pref,
        },
        "rawFallback": {
            "schema_version": schema_version,
            "flags": raw_fallback_fixture.flags,
            "compliance": raw_fallback_fixture.compliance,
            "raw_id": raw_fallback_fixture.expectation.entry_id,
        },
        "invalid": {
            "schema_version": schema_version,
            "flags": invalid_flags,
            "issues": [
                {"policy": "DisableTelemetry", "path": ["DisableTelemetry"]},
                {"policy": "Preferences", "path": ["Preferences", known_pref, "Value"]},
            ],
            "known_pref": known_pref,
        },
    }
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        global.window = {{}};
        eval(fs.readFileSync("{STATIC_ROOT / "profiles_settings_inventory.js"}", "utf8"));

        const cases = {json.dumps(cases)};
        const allSettingsCategoryCatalog = {json.dumps(get_all_settings_category_catalog())};
        const wizardPreferencesCatalog = {json.dumps(wizard_preferences_catalog)};
        const wizardSchemaShellCatalog = {json.dumps(get_wizard_schema_shell_catalog(wizard_preferences_catalog))};
        const t = (key) => ({{
            "profiles.settings_list_kind_policy": "Policy",
            "profiles.settings_list_kind_preference": "Preference",
            "profiles.settings_list_value_not_configured": "Not configured",
            "profiles.settings_list_value_object": "{{count}} keys",
            "profiles.settings_list_value_array": "{{count}} items",
        }}[key] || key);

        function collect(testCase) {{
            const inventory = window.BPMProfilesSettingsInventory.create({{
                dependencies: {{
                    t,
                    getActiveWizardSchemaVersion: () => testCase.schema_version,
                    getValidationIssues: () => testCase.issues || [],
                    getComplianceInfo: () => testCase.compliance || {{}},
                    getManualEdits: () => testCase.manual_edits || [],
                }},
                allSettingsCategoryCatalog,
                wizardPreferencesCatalog,
                wizardSchemaShellCatalog,
            }});
            return inventory.collect(testCase.flags || {{}});
        }}

        function keyFor(entry) {{
            return `${{entry.kind}}:${{entry.id}}`;
        }}

        function byKey(entries) {{
            return Object.fromEntries(entries.map((entry) => [keyFor(entry), entry]));
        }}

        function counts(entries) {{
            return {{
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
            }};
        }}

        function assertCounts(label, entries, expected) {{
            const actual = counts(entries);
            Object.entries(expected).forEach(([key, value]) => {{
                if (key === "schema_version") return;
                if (actual[key] !== value) {{
                    throw new Error(`${{label}} count ${{key}} expected ${{value}} got ${{actual[key]}}`);
                }}
            }});
        }}

        const blank = collect(cases.blank);
        assertCounts("blank", blank, cases.blank.counts);
        if (!blank.every((entry) => entry.state === "available")) throw new Error("blank available states");
        if (!blank.every((entry) => entry.sources.includes("catalog"))) throw new Error("blank catalog source");

        const basic = collect(cases.basicCorporate);
        assertCounts("basic corporate", basic, cases.basicCorporate.counts);
        const basicByKey = byKey(basic);
        if (basicByKey["policy:DisableTelemetry"].state !== "configured") throw new Error("basic configured policy");
        if (!basicByKey["policy:DisableTelemetry"].sources.includes("manual")) throw new Error("basic manual source");
        if (basicByKey["policy:DisableTelemetry"].cis.hasDecision) throw new Error("basic unexpected CIS decision");

        const cis = collect(cases.cisL2);
        assertCounts("cis l2", cis, cases.cisL2.counts);
        const cisWrapped = collect({{ ...cases.cisL2, flags: {{ policies: cases.cisL2.flags }} }});
        assertCounts("cis l2 wrapped policies document", cisWrapped, cases.cisL2.counts);
        const cisByKey = byKey(cis);
        if (!cisByKey["policy:DisableTelemetry"].cis.hasDecision) throw new Error("CIS decision missing");
        if (!cisByKey["policy:DisableTelemetry"].sources.includes("cis")) throw new Error("CIS source missing");
        [
            "browser.safebrowsing.malware.enabled",
            "browser.safebrowsing.phishing.enabled",
            "browser.search.update",
            "dom.allow_scripts_to_close_windows",
            "dom.disable_window_flip",
            "dom.disable_window_move_resize",
            "extensions.blocklist.enabled",
            "media.peerconnection.enabled",
            "network.IDN_show_punycode",
            "security.mixed_content.block_active_content",
        ].forEach((pref) => {{
            const entry = cisByKey[`preference:${{pref}}`];
            if (!entry) throw new Error(`CIS preference missing ${{pref}}`);
            if (entry.unknown) throw new Error(`CIS preference marked unknown ${{pref}}`);
            if (entry.sources.includes("imported")) throw new Error(`CIS preference marked imported ${{pref}}`);
            if (!entry.sources.includes("cis")) throw new Error(`CIS preference missing CIS source ${{pref}}`);
            if (!entry.editor.knownPreference) throw new Error(`CIS preference missing known metadata ${{pref}}`);
        }});
        if (cisByKey["policy:Preferences"] && cisByKey["policy:Preferences"].state !== "available") throw new Error("Preferences container configured twice");
        const cisReviewCount = cis.filter((entry) => entry.attentionFlags.cisReviewRequired).length;
        if (cisReviewCount !== cases.cisL2.manual_review_count) throw new Error("CIS manual review count");

        const unknown = collect(cases.unknownImport);
        assertCounts("unknown import", unknown, cases.unknownImport.counts);
        const unknownByKey = byKey(unknown);
        if (!unknownByKey["policy:CustomEnterprisePolicy"].sources.includes("unknown")) throw new Error("unknown policy source");
        if (!unknownByKey["preference:company.managed.preference"].sources.includes("imported")) throw new Error("unknown preference import source");
        if (unknownByKey[`preference:${{cases.unknownImport.known_pref}}`].unknown) throw new Error("known preference marked unknown");

        const raw = collect(cases.rawFallback);
        const rawByKey = byKey(raw);
        const rawEntry = rawByKey[`policy:${{cases.rawFallback.raw_id}}`];
        if (!rawEntry) throw new Error("raw fallback entry missing");
        if (!rawEntry.rawFallback) throw new Error("raw fallback flag missing");
        if (!rawEntry.sources.includes("raw-fallback")) throw new Error("raw fallback source missing");

        const invalid = collect(cases.invalid);
        const invalidByKey = byKey(invalid);
        if (invalid.filter((entry) => entry.attentionFlags.invalid).length !== 2) throw new Error("invalid entry count");
        if (invalidByKey["policy:DisableTelemetry"].validationIssueCount !== 1) throw new Error("policy invalid issue count");
        if (invalidByKey[`preference:${{cases.invalid.known_pref}}`].validationIssueCount !== 1) throw new Error("preference invalid issue count");
        if (!invalidByKey[`preference:${{cases.invalid.known_pref}}`].attentionFlags.reviewRequired) throw new Error("invalid preference review flag");
        """
    )

    subprocess.run(["node", "-"], input=script, text=True, cwd=REPO_ROOT, check=True)
