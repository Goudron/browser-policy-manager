"""Focused BPM096-M7-06 contract for AMO-independent manual extension entry."""

from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE = REPO_ROOT / "app/templates/profiles/_page_wizard_step_extensions.html"
SOURCE = REPO_ROOT / "app/static/profiles_extensions.js"
DOM_SOURCE = REPO_ROOT / "app/static/profiles_dom.js"
BOOTSTRAP_SOURCE = REPO_ROOT / "app/static/profiles_bootstrap_core.js"

MANUAL_FALLBACK_KEYS = {
    "profiles.wizard_extensions_amo_search_unavailable",
    "profiles.wizard_extensions_amo_manual_action",
    "profiles.wizard_extension_rule_guid_label",
    "profiles.wizard_extension_rule_install_url_label",
    "profiles.wizard_extension_rule_install_url_placeholder",
}


def test_manual_guid_and_install_url_stay_available_without_amo() -> None:
    soup = BeautifulSoup(TEMPLATE.read_text(encoding="utf-8"), "html.parser")
    manual_form = soup.find("form", id="wizard-extension-rule-add-form")
    assert manual_form is not None
    assert manual_form.get("novalidate") == ""
    assert manual_form.find("input", id="wizard-extension-rule-guid", attrs={"type": "text"})
    assert manual_form.find("input", id="wizard-extension-rule-install-url", attrs={"type": "url"})

    recovery = soup.find("button", id="wizard-extension-amo-manual-focus")
    assert recovery is not None
    assert recovery.get("type") == "button"
    assert recovery.has_attr("hidden")
    assert recovery.get("data-i18n") == "profiles.wizard_extensions_amo_manual_action"


def test_every_amo_failure_uses_local_manual_recovery_without_a_profile_operation() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for token in (
        "function setAmoSearchUnavailable()",
        'setAmoSearchStatus("profiles.wizard_extensions_amo_search_unavailable")',
        "setAmoManualRecoveryVisible(true)",
        'if (!response.ok || payload?.availability !== "available")',
        "const payload = await response.json();",
        "catch (error)",
        "focusManualExtensionEntry()",
        'wizardExtensionAmoManualFocusEl?.addEventListener("click"',
        "wizardExtensionRuleAddFormEl?.scrollIntoView",
        "wizardExtensionRuleGuidEl?.focus({ preventScroll: true })",
    ):
        assert token in source

    # A fetch appears only inside the explicit submitted AMO-search function;
    # manual-rule submission writes the local editor document instead.
    assert source.index("async function searchAmoByName()") < source.index("fetch(")
    assert 'function addExtensionRule(guid, installUrl = "")' in source
    assert "install_url: normalizedInstallUrl" in source
    assert "writeExtensionPolicyDocument(editorState);" in source
    assert 'wizardExtensionAmoSearchFormEl?.addEventListener("submit"' in source
    assert 'wizardExtensionAmoQueryEl?.addEventListener("input"' not in source


def test_manual_fallback_dom_owners_and_all_locale_copy_are_complete() -> None:
    dom_source = DOM_SOURCE.read_text(encoding="utf-8")
    bootstrap_source = BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
    for token in (
        "wizardExtensionAmoManualFocusEl",
        "wizardExtensionRuleInstallUrlEl",
    ):
        assert token in dom_source
        assert token in bootstrap_source

    for locale in ACTIVE_CATALOG_LOCALES:
        authored = json.loads(
            (REPO_ROOT / "app/i18n_src" / locale / "wizard.json").read_text(encoding="utf-8")
        )
        generated = json.loads(
            (REPO_ROOT / "app/i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        for key in MANUAL_FALLBACK_KEYS:
            assert isinstance(authored.get(key), str) and authored[key]
            assert generated.get(key) == authored[key]
