from __future__ import annotations

import gzip
import json
from pathlib import Path

from tests.javascript.fixtures.generate_frontend_fixtures import build_payload

REPO_ROOT = Path(__file__).resolve().parents[3]
STATIC_ROOT = REPO_ROOT / "app" / "static"
FIXTURE_PATH = REPO_ROOT / "tests/javascript/fixtures/all_settings.json.gz"


def _static_source(filename: str) -> str:
    return (STATIC_ROOT / filename).read_text(encoding="utf-8")


def test_settings_inventory_frontend_module_exposes_stable_entry_model():
    source = _static_source("profiles_settings_inventory.js")

    for snippet in (
        "export { create };",
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
        'source: sources[0] || "",',
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
        'preferenceSectionId: entry.preferenceSectionId || "",',
        "preferenceSection: entry.preferenceSection || null,",
        "preferenceValue: entry.preferenceValue ?? null,",
        "schemaBucket: bucketKey,",
        'schemaStepId: stepMeta.id || "",',
        "schemaStepNumber: stepMeta.step || 0,",
        "function getPreferenceSection(sectionId)",
        "function getKnownPreference(prefName)",
        "function validationPathsForEntry(entry)",
        "function issueMatchesEntry(issue, entry)",
        "function getIssuesByEntryKey(entries)",
    ):
        assert snippet in source


def test_all_settings_list_imports_inventory_before_list_composition():
    list_source = _static_source("profiles_all_settings_list.js")
    bootstrap_source = _static_source("profiles_bootstrap.js")
    core_source = _static_source("profiles_bootstrap_core.js")

    state_import = (
        'import { create as createAllSettingsRouteState } from "./profiles_all_settings_state.js";'
    )
    inventory_import = (
        'import { create as createSettingsInventory } from "./profiles_settings_inventory.js";'
    )
    list_import = (
        'import { create as createAllSettingsList } from "./profiles_all_settings_list.js";'
    )

    assert bootstrap_source.index(state_import) < bootstrap_source.index(inventory_import)
    assert bootstrap_source.index(inventory_import) < bootstrap_source.index(list_import)
    assert "createSettingsInventory," in core_source
    assert "const settingsInventory = createSettingsInventory({" in core_source
    assert "settingsInventory," in core_source
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
    assert '.filter((entry) => entry?.kind === "policy" && entry.schemaItem)' in search_source
    assert "buildShellPolicyTargetIndex(allSettingsEntries);" in search_source


def test_preference_entry_collection_is_not_duplicated_in_all_settings_consumers():
    inventory_source = _static_source("profiles_settings_inventory.js")
    detail_source = _static_source("profiles_all_settings_detail.js")

    assert "function buildPreferenceEntries(sourceData)" in inventory_source
    assert "function buildPreferenceEntries(sourceData)" not in detail_source
    assert "wizardPreferencesCatalog.known_preferences" not in detail_source
    assert "settingsInventory?.getKnownPreference?.(prefName)" in detail_source
    assert "entry.editor?.knownPreference" in detail_source


def test_native_frontend_fixture_matches_python_contract_builders():
    actual = json.loads(gzip.decompress(FIXTURE_PATH.read_bytes()))
    expected = json.loads(json.dumps(build_payload(), ensure_ascii=False))

    assert actual == expected
