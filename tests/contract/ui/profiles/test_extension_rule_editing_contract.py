"""Focused BPM096-M7-05 contract for schema-aware Guided extension rule editing."""

from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE = REPO_ROOT / "app/templates/profiles/_page_wizard_step_extensions.html"
SYNC_TEMPLATE = REPO_ROOT / "app/templates/profiles/_page_wizard_step_sync.html"
SOURCE = REPO_ROOT / "app/static/profiles_extensions.js"
DOM_SOURCE = REPO_ROOT / "app/static/profiles_dom.js"
BOOTSTRAP_SOURCE = REPO_ROOT / "app/static/profiles_bootstrap_core.js"

RULE_KEYS = {
    "profiles.wizard_extension_rules_title",
    "profiles.wizard_extension_rule_guid_label",
    "profiles.wizard_extension_rule_add",
    "profiles.wizard_extension_rule_raw_required",
    "profiles.wizard_extension_rule_remove",
    "profiles.wizard_extension_rule_global_title",
    "profiles.wizard_extension_source_manual",
    "profiles.wizard_extension_source_cis",
    "profiles.wizard_extension_source_baseline",
    "profiles.wizard_extension_source_raw",
    "profiles.wizard_extension_rule_conflict_global_install",
    "profiles.wizard_extension_rule_conflict_uninstall",
    "profiles.wizard_extension_rule_conflict_install_url",
    "profiles.wizard_extension_rule_conflict_permission",
}


def test_extensions_step_has_one_accessible_typed_owner_and_rehomes_shared_controls() -> None:
    soup = BeautifulSoup(TEMPLATE.read_text(encoding="utf-8"), "html.parser")
    panel = soup.find("section", id="wizard-step-6")
    assert panel is not None
    assert panel.get("data-wizard-step-id") == "extensions"

    expected_targets = {
        "policy:ExtensionSettings",
        "policy:ExtensionUpdate",
        "policy:Extensions",
        "policy:InstallAddonsPermission",
    }
    assert {
        element.get("data-settings-target") for element in panel.select("[data-settings-target]")
    } == expected_targets

    for control_id in (
        "wizard-extension-rule-add-form",
        "wizard-extension-rule-guid",
        "wizard-extension-rule-status",
        "wizard-extension-rules",
        "wizard-extension-raw-rules",
        "wizard-extension-update",
        "wizard-extension-install-default",
        "wizard-extension-install-allow",
        "wizard-extension-install",
        "wizard-extension-locked",
        "wizard-extension-uninstall",
    ):
        assert soup.find(id=control_id) is not None

    sync_source = SYNC_TEMPLATE.read_text(encoding="utf-8")
    for retired_id in (
        "wizard-step-4-extensions",
        "wizard-extension-default-mode",
        "wizard-extension-governance-presets",
        "wizard-extension-curated-section",
    ):
        assert retired_id not in sync_source


def test_rule_editor_covers_supported_shapes_preserves_raw_values_and_marks_conflicts() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for token in (
        "function supportsExtension153Fields()",
        'channel === "release-153" || channel === "esr-153.0"',
        "function extensionRuleIsStructured(value)",
        "function renderTypedExtensionRule(guid, value, documentValue)",
        "function renderRawExtensionRule(guid, value",
        "function applyRawExtensionRule(textarea)",
        "function applyExtensionRuleEditor()",
        'function addExtensionRule(guid, installUrl = "")',
        "function removeExtensionRule(guid)",
        "CSS.escape(normalizedGuid)",
        "JSON.parse(textarea.value)",
        'card.dataset.extensionRuleConflict = "true"',
        "extensionRuleIsStructured(currentRule)",
    ):
        assert token in source

    for mode in ("allowed", "blocked", "force_installed", "normal_installed"):
        assert f'"{mode}"' in source
    for field in (
        "installation_mode",
        "install_url",
        "update_url",
        "updates_disabled",
        "private_browsing",
        "default_area",
        "temporarily_allow_weak_signatures",
        "blocked_install_message",
        "install_sources",
        "allowed_types",
        "restricted_domains",
        "allowed_permissions",
        "blocked_permissions",
        "runtime_allowed_hosts",
        "runtime_blocked_hosts",
        "Install",
        "Locked",
        "Uninstall",
    ):
        assert f'"{field}"' in source

    for token in (
        "installPermission.Allow",
        "nextPermissions.Default",
        "documentValue.ExtensionUpdate",
    ):
        assert token in source

    assert "return value.split(/\\r?\\n/).filter((entry) => entry.length > 0);" in source
    assert "textarea.value = JSON.stringify(value, null, 2);" in source
    assert "profiles.wizard_extension_rule_conflict_global_install" in source
    assert "profiles.wizard_extension_rule_conflict_uninstall" in source
    assert "profiles.wizard_extension_rule_conflict_install_url" in source
    assert "profiles.wizard_extension_rule_conflict_permission" in source


def test_rule_attribution_round_trips_from_manual_and_cis_metadata_without_provider_provenance() -> (
    None
):
    source = SOURCE.read_text(encoding="utf-8")
    bootstrap_source = BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
    dom_source = DOM_SOURCE.read_text(encoding="utf-8")

    for token in (
        "function extensionRuleSource(path, { raw = false } = {})",
        "getManualEdits",
        "getComplianceInfo",
        'selected === "cis"',
        'selected === "base" || selected === "baseline"',
        "card.dataset.extensionRuleSource",
        "profiles.wizard_extension_source_raw",
    ):
        assert token in source
    for token in (
        "getComplianceInfo: () => getAllSettingsComplianceInfo()",
        "getManualEdits: () => getAllSettingsManualEdits()",
        "wizardExtensionRuleAddFormEl",
        "wizardExtensionRulesEl",
        "wizardExtensionRawRulesEl",
    ):
        assert token in bootstrap_source
    for token in (
        "wizardExtensionRuleAddFormEl",
        "wizardExtensionRulesEl",
        "wizardExtensionRawRulesEl",
    ):
        assert token in dom_source


def test_all_locales_supply_rule_editing_and_attribution_copy() -> None:
    for locale in ACTIVE_CATALOG_LOCALES:
        authored = json.loads(
            (REPO_ROOT / "app/i18n_src" / locale / "wizard.json").read_text(encoding="utf-8")
        )
        generated = json.loads(
            (REPO_ROOT / "app/i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        for key in RULE_KEYS:
            assert isinstance(authored.get(key), str) and authored[key]
            assert generated.get(key) == authored[key]
