"""Focused BPM096-M7-04 contract for the explicit, inert AMO search handoff."""

from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE = REPO_ROOT / "app/templates/profiles/_page_wizard_step_extensions.html"
EXTENSIONS_SOURCE = REPO_ROOT / "app/static/profiles_extensions.js"
DOM_SOURCE = REPO_ROOT / "app/static/profiles_dom.js"
BOOTSTRAP_SOURCE = REPO_ROOT / "app/static/profiles_bootstrap_core.js"

AMO_KEYS = {
    "profiles.wizard_extensions_amo_search_title",
    "profiles.wizard_extensions_amo_search_body",
    "profiles.wizard_extensions_amo_query_label",
    "profiles.wizard_extensions_amo_query_placeholder",
    "profiles.wizard_extensions_amo_search_action",
    "profiles.wizard_extensions_amo_query_disclosure",
    "profiles.wizard_extensions_amo_search_idle",
    "profiles.wizard_extensions_amo_query_required",
    "profiles.wizard_extensions_amo_search_loading",
    "profiles.wizard_extensions_amo_search_empty",
    "profiles.wizard_extensions_amo_search_unavailable",
    "profiles.wizard_extensions_amo_search_results",
    "profiles.wizard_extensions_amo_results_label",
    "profiles.wizard_extensions_amo_select_action",
    "profiles.wizard_extensions_amo_rule_created",
    "profiles.wizard_extensions_amo_rule_mode_label",
    "profiles.wizard_extensions_amo_version",
}


def test_search_is_an_explicit_accessible_form_with_localized_privacy_disclosure() -> None:
    soup = BeautifulSoup(TEMPLATE.read_text(encoding="utf-8"), "html.parser")
    form = soup.find("form", id="wizard-extension-amo-search-form")
    assert form is not None
    assert (
        form.find_parent("section", class_="wizard-panel").get("data-wizard-step-id")
        == "extensions"
    )
    assert form.get("novalidate") == ""
    assert soup.find("input", id="wizard-extension-amo-query", attrs={"type": "search"})
    assert soup.find("button", id="wizard-extension-amo-search-submit", attrs={"type": "submit"})
    status = soup.find(id="wizard-extension-amo-search-status")
    assert status is not None
    assert status.get("role") == "status"
    assert status.get("aria-live") == "polite"
    results = soup.find(id="wizard-extension-amo-search-results")
    assert results is not None
    assert results.get("role") == "list"
    disclosure = soup.find(id="wizard-extension-amo-search-disclosure")
    assert disclosure is not None
    assert disclosure.get("data-i18n") == "profiles.wizard_extensions_amo_query_disclosure"


def test_client_search_is_user_submitted_and_cannot_render_provider_values_as_markup_or_links() -> (
    None
):
    source = EXTENSIONS_SOURCE.read_text(encoding="utf-8")

    assert 'wizardExtensionAmoSearchFormEl?.addEventListener("submit"' in source
    assert "searchAmoByName();" in source
    assert 'wizardExtensionAmoQueryEl?.addEventListener("input"' not in source
    assert "/api/profiles/extensions/amo-search?q=${encodeURIComponent(query)}" in source
    assert 'credentials: "same-origin"' in source
    assert "AbortController" in source
    assert (
        'name.textContent = typeof result.name === "string" ? result.name : result.guid;' in source
    )
    assert 'meta.textContent = typeof result.version === "string" && result.version' in source
    assert 'documentRef.createElement("a")' not in source
    assert "innerHTML" not in source
    assert "latest.xpi" not in source


def test_only_verified_firefox_guid_results_can_create_the_minimal_editable_policy_handoff() -> (
    None
):
    source = EXTENSIONS_SOURCE.read_text(encoding="utf-8")

    assert "function isVerifiedFirefoxGuid(value)" in source
    assert "if (!result || !isVerifiedFirefoxGuid(result.guid)) return;" in source
    assert "card.dataset.extensionAmoRule = guid" in source
    assert "select.dataset.extensionAmoRuleMode = guid" in source
    assert "installation_mode: selectedMode" in source
    assert '["allowed", "blocked"].includes(selectedMode)' in source
    assert "fetch(" in source


def test_search_elements_are_owned_by_the_profiles_dom_and_extensions_bootstrap_boundary() -> None:
    dom_source = DOM_SOURCE.read_text(encoding="utf-8")
    bootstrap_source = BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
    for token in (
        "wizardExtensionAmoSearchFormEl",
        "wizardExtensionAmoQueryEl",
        "wizardExtensionAmoSearchSubmitEl",
        "wizardExtensionAmoSearchStatusEl",
        "wizardExtensionAmoSearchResultsEl",
        "wizardExtensionAmoSelectedRulesEl",
    ):
        assert token in dom_source
        assert token in bootstrap_source


def test_all_authored_and_generated_locales_supply_the_amo_search_copy() -> None:
    for locale in ACTIVE_CATALOG_LOCALES:
        authored = json.loads(
            (REPO_ROOT / "app/i18n_src" / locale / "wizard.json").read_text(encoding="utf-8")
        )
        generated = json.loads(
            (REPO_ROOT / "app/i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        for key in AMO_KEYS:
            assert isinstance(authored.get(key), str) and authored[key]
            assert generated.get(key) == authored[key]
