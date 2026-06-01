import asyncio
import importlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from app.core.config import get_settings
from app.main import app
from app.web.firefox_wizard_steps import get_wizard_steps
from tests.support import assert_contains_all, build_profile_payload, make_test_client

PROFILES_PAGE_EDITOR_TOKENS = (
    "Browser profile manager",
    "Library",
    "JSON editor",
    'id="list-summary"',
    'id="list-total-summary"',
    'id="import-firefox-policies"',
    'id="import-firefox-policies-file"',
    'accept=".json,application/json"',
    'id="wizard-panel"',
    'id="wizard-starter-catalog"',
    'class="wizard-baseline-stack"',
    'id="compare-panel"',
    'id="compare-clear"',
    'id="compare-empty"',
    'id="compare-active"',
    'id="compare-current-name"',
    'id="compare-other-name"',
    'id="compare-changes-list"',
    'id="compare-guided-areas-copy"',
    'id="compare-guided-areas-list"',
    'data-scenario-key="corporate_default"',
    'data-scenario-key="shared_devices"',
    'data-scenario-key="hardened"',
    'data-scenario-key="extension_rollout"',
    'data-scenario-key="targeted_edits"',
    'id="wizard-settings-search-input"',
    'id="wizard-settings-search-results"',
    'id="wizard-settings-catalog"',
    'id="wizard-manual-policy-controls"',
    'id="wizard-schema-shell-catalog"',
    'id="wizard-schema"',
    'id="wizard-mode"',
    'id="wizard-finish"',
    'id="wizard-step-memory-copy"',
    'id="wizard-step-memory-list"',
    'id="hard-delete"',
    'id="reset-library"',
    'id="wizard-general-policy-presets"',
    'data-general-policy-preset="defaults"',
    'data-general-policy-preset="updates"',
    'data-general-policy-preset="browser_prompt"',
    'data-general-policy-preset="downloads"',
    'data-general-policy-preset="managed"',
    'id="wizard-general-policy-section-status"',
    'data-starter-key="basic_corporate"',
    'data-starter-key="classroom_kiosk"',
    'data-starter-key="soc_hard"',
    'id="profile-derived-note"',
    'data-cis-layer-key="none"',
    'data-cis-layer-key="cis_l1"',
    'data-cis-layer-key="cis_l2"',
    'id="profile-clone-handoff-panel"',
    'id="profile-clone-handoff-copy" role="status" aria-live="polite"',
    'id="profile-clone-handoff-list" role="list"',
    'id="profile-lifecycle-panel"',
    'id="profile-lifecycle-copy"',
    'id="profile-lifecycle-list"',
    'id="wizard-summary-starter"',
    'id="wizard-summary-cis"',
    'id="wizard-summary-derived-row"',
    'id="wizard-summary-derived"',
    'id="wizard-summary-lifecycle-list"',
    'id="wizard-step-actions"',
    'id="wizard-step-actions-copy"',
    'id="wizard-step-undo"',
    'id="wizard-step-reset"',
    'id="wizard-homepage-url"',
    'id="wizard-home-surface-startup"',
    'id="wizard-home-surface-new-tab"',
    'id="wizard-home-surface-firefox-home"',
    'id="wizard-homepage-presets"',
    'data-homepage-preset="defaults"',
    'data-homepage-preset="portal"',
    'data-homepage-preset="session"',
    'data-homepage-preset="locked"',
    'id="wizard-homepage-shared-presets"',
    'data-homepage-shared-preset="portal_locked"',
    'data-homepage-shared-preset="return_session"',
    'id="wizard-firefox-home-presets"',
    'data-firefox-home-preset="defaults"',
    'data-firefox-home-preset="shortcuts"',
    'data-firefox-home-preset="focused"',
    'data-firefox-home-preset="managed"',
    'id="wizard-firefox-home-recommendations-panel"',
    'id="wizard-firefox-home-snippets-panel"',
    'id="wizard-firefox-home-layout-panel"',
    'id="wizard-search-bar"',
    'id="wizard-step-2-default-search"',
    'id="wizard-step-2-managed-engines"',
    'id="wizard-step-2-suggestions"',
    'id="wizard-search-defaults-presets"',
    'data-search-defaults-preset="defaults"',
    'data-search-defaults-preset="managed_default"',
    'data-search-defaults-preset="custom_engines"',
    'data-search-defaults-preset="restricted"',
    'id="wizard-search-default-engine"',
    'id="wizard-firefox-suggest-presets"',
    'data-firefox-suggest-preset="defaults"',
    'data-firefox-suggest-preset="private"',
    'data-firefox-suggest-preset="managed"',
    'data-firefox-suggest-preset="locked_down"',
    'id="wizard-search-engine-add"',
    'id="wizard-search-engine-list"',
    'id="wizard-preference-row-template"',
    'id="wizard-preferences-known-list"',
    'wizard-preferences-known-list',
    'data-preference-value-select',
    'data-privacy-outcome-group="cookies-permissions"',
    'data-settings-target="policy:DisableTelemetry"',
    'data-settings-target="field:wizard-proxy-mode"',
    'data-settings-target="search-engine-preset:duckduckgo"',
    'data-search-engine-preset="ticket_queue"',
    'data-search-engine-preset="wiki_portal"',
    'data-search-engine-preset="duckduckgo"',
    'data-search-engine-presets-menu',
    'data-search-engine-preset-status',
    'data-search-engine-field="Name"',
    'data-search-engine-field="URLTemplate"',
    'data-search-engine-field="Alias"',
    'data-search-engine-advanced',
    'data-search-engine-field="Method"',
    'data-search-engine-field="PostData"',
    'data-search-engine-summary',
    'data-search-engine-warning',
    'data-policy-select-key="HttpsOnlyMode"',
    'id="wizard-new-tab-page"',
    'id="wizard-home-overrides-presets"',
    'data-home-overrides-preset="defaults"',
    'data-home-overrides-preset="new_tab"',
    'data-home-overrides-preset="first_run"',
    'data-home-overrides-preset="managed"',
    'id="wizard-override-first-run"',
    'data-firefox-home-key="Search"',
    'data-firefox-suggest-key="WebSuggestions"',
    'id="wizard-proxy-mode"',
    'id="wizard-proxy-section-status"',
    'id="wizard-proxy-presets"',
    'data-proxy-preset="defaults"',
    'data-proxy-preset="none"',
    'data-proxy-preset="system"',
    'data-proxy-preset="autoConfig"',
    'data-proxy-preset="manual"',
    'data-network-enterprise-preset="defaults"',
    'data-network-enterprise-preset="sso"',
    'data-network-enterprise-preset="roots"',
    'data-network-enterprise-preset="managed"',
    'id="wizard-network-enterprise-presets"',
    'id="wizard-network-enterprise-section-status"',
    'id="wizard-network-enterprise-fine-tuning-toggle"',
    'id="wizard-network-enterprise-fine-tuning-panel"',
    'id="wizard-language-presets"',
    'data-language-preset="defaults"',
    'data-language-preset="locales"',
    'data-language-preset="translation_off"',
    'data-language-preset="managed"',
    'id="wizard-dns-over-https-card"',
    'id="wizard-authentication-card"',
    'id="wizard-certificates-card"',
    'id="wizard-requested-locales-card"',
    'id="wizard-generative-ai-card"',
    'id="wizard-user-messaging-card"',
    'profiles.wizard_user_environment_map_title',
    'id="wizard-step-4-accounts"',
    'id="wizard-step-4-language"',
    'id="wizard-step-4-extensions"',
    'id="wizard-step-4-bookmarks"',
    'id="wizard-step-4-websites"',
    'id="wizard-sync-focus-presets"',
    'data-sync-focus-preset="defaults"',
    'data-sync-focus-preset="accounts"',
    'data-sync-focus-preset="guidance"',
    'data-sync-focus-preset="managed"',
    'id="wizard-sync-section-status"',
    'id="wizard-sync-fine-tuning-toggle"',
    'id="wizard-sync-fine-tuning-panel"',
    'id="wizard-language-section-status"',
    'id="wizard-language-ai-handoff"',
    'id="wizard-ai-section-status"',
    'id="wizard-ai-policy-controls"',
    'id="wizard-ai-governance-copy"',
    'id="wizard-ai-posture-presets"',
    'data-ai-posture-preset="defaults"',
    'data-ai-posture-preset="disable"',
    'data-ai-posture-preset="availability"',
    'data-ai-posture-preset="mixed"',
    'id="wizard-visual-search-enabled-card"',
    'id="wizard-website-filter-card"',
    'id="wizard-website-access-decision"',
    'id="wizard-website-access-posture"',
    'data-website-access-posture="defaults"',
    'data-website-access-posture="block_some"',
    'data-website-access-posture="allow_only"',
    'data-website-access-posture="mixed"',
    'id="wizard-website-access-handlers"',
    'data-website-access-handlers="defaults"',
    'data-website-access-handlers="files"',
    'data-website-access-handlers="protocols"',
    'data-website-access-handlers="both"',
    'id="wizard-handlers-card"',
    'id="wizard-website-section-status"',
    'id="wizard-website-fine-tuning-toggle"',
    'id="wizard-website-fine-tuning-panel"',
    'data-bookmarks-handoff',
    'id="wizard-bookmarks-section-status"',
    'id="wizard-bookmarks-open-advanced"',
    'id="wizard-bookmarks-configured-actions"',
    'id="wizard-bookmarks-links-jump"',
    'id="wizard-bookmarks-folders-jump"',
    'id="wizard-bookmarks-nested-jump"',
    'id="wizard-permissions-card"',
    'id="wizard-cookies-card"',
)


def test_guided_wizard_step_catalog_uses_six_step_model():
    wizard_steps = get_wizard_steps()

    assert [(step["step"], step["id"]) for step in wizard_steps] == [
        (1, "start"),
        (2, "browser_defaults"),
        (3, "privacy"),
        (4, "users_features"),
        (5, "ai"),
        (6, "review"),
    ]
    assert [step["label_fallback"] for step in wizard_steps] == [
        "Profile & baseline",
        "Browser access & defaults",
        "Security & privacy",
        "Users, add-ons & sites",
        "AI & smart features",
        "Review & export",
    ]
    assert wizard_steps[-1]["progress_fallback"] == "Step 6 of 6: Review & export"


def test_guided_wizard_stepper_renders_six_navigation_steps():
    client = make_test_client(app)
    response = client.get("/profiles/new")

    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    step_buttons = soup.select("#wizard-stepper .wizard-step")

    assert [button.get("data-step") for button in step_buttons] == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    ]
    assert soup.select_one('#wizard-stepper .wizard-step[data-step="7"]') is None
    assert soup.select_one('#wizard-stepper .wizard-step[data-step="8"]') is None

PROFILES_PAGE_REVIEW_TOKENS = (
    'id="wizard-network-summary-authentication"',
    'id="wizard-network-summary-certificates"',
    'id="wizard-network-summary-dns"',
    'id="wizard-network-summary-windows-sso"',
    'id="wizard-network-summary-authentication-jump"',
    'id="wizard-network-summary-certificates-jump"',
    'id="wizard-network-summary-dns-jump"',
    'id="wizard-network-summary-windows-sso-jump"',
    'id="wizard-homepage-section-status"',
    'id="wizard-home-overrides-section-status"',
    'id="wizard-firefox-home-section-status"',
    'id="wizard-search-defaults-section-status"',
    'id="wizard-firefox-suggest-section-status"',
    'id="wizard-privacy-summary-permissions"',
    'id="wizard-privacy-summary-cookies"',
    'id="wizard-privacy-summary-user-data"',
    'id="wizard-privacy-summary-cleanup"',
    'id="wizard-privacy-summary-user-data-jump"',
    'id="wizard-privacy-summary-cleanup-jump"',
    'id="wizard-privacy-summary-permissions-jump"',
    'id="wizard-privacy-summary-cookies-jump"',
    'data-hardening-preset="defaults"',
    'data-hardening-preset="balanced"',
    'data-hardening-preset="strict"',
    'id="wizard-hardening-section-status"',
    'data-hardening-cleanup-subchoice',
    'data-hardening-subposture-menu="cleanup"',
    'data-cleanup-preset="defaults"',
    'data-cleanup-preset="shared"',
    'data-cleanup-preset="strict"',
    'id="wizard-cleanup-section-status"',
    'id="wizard-privacy-site-section-status"',
    'data-site-data-preset="defaults"',
    'data-site-data-preset="balanced"',
    'data-site-data-preset="strict"',
    'id="wizard-site-data-fine-tuning-toggle"',
    'id="wizard-site-data-fine-tuning-panel"',
    'data-privacy-outcome-group="cookies-permissions"',
    'id="wizard-extension-default-mode"',
    'id="wizard-extension-governance-presets"',
    'data-extension-governance-preset="open"',
    'data-extension-governance-preset="blocked"',
    'data-extension-governance-preset="managed"',
    'data-extension-governance-preset="curated"',
    'data-extension-governance-preset="mixed"',
    'id="wizard-extension-install"',
    'data-extension-rule-group="install"',
    'id="wizard-extension-install-summary"',
    'id="wizard-extension-install-toggle"',
    'id="wizard-extension-install-panel"',
    'id="wizard-extension-locked"',
    'data-extension-rule-group="locked"',
    'id="wizard-extension-locked-summary"',
    'id="wizard-extension-locked-toggle"',
    'id="wizard-extension-locked-panel"',
    'id="wizard-extension-uninstall"',
    'data-extension-rule-group="uninstall"',
    'id="wizard-extension-uninstall-summary"',
    'id="wizard-extension-uninstall-toggle"',
    'id="wizard-extension-uninstall-panel"',
    'id="wizard-extension-section-status"',
    'id="wizard-extension-curated-toggle"',
    'id="wizard-extension-curated-panel"',
    'id="wizard-install-addons-permission-card"',
    'id="wizard-extension-settings-card"',
)

PROFILES_PAGE_SCHEMA_EXPORT_TOKENS = (
    "data-wizard-disclosure-toggle",
    'id="wizard-schema-shell-step-5-raw"',
    'id="wizard-schema-shell-step-7-badges"',
    'id="wizard-schema-shell-step-8-coverage"',
    'id="wizard-schema-shell-step-8-badges"',
    "data-schema-dict-add",
    "data-schema-dict-remove",
    "data-schema-dict-key",
    "data-schema-dict-status",
    "data-schema-array-status",
    "data-schema-nested-field",
    "data-schema-nested-status",
    "data-schema-nested-array-add",
    "data-schema-nested-dict-add",
    "data-schema-object-status",
    "data-schema-branch-mode",
    'id="wizard-summary-extensions"',
    'id="wizard-export-section-ready"',
    'id="wizard-export-section-changes"',
    'id="wizard-export-section-technical"',
    "wizard-export-primary-card",
    'id="wizard-export-final-checklist"',
    'id="wizard-export-technical-alerts"',
    'id="wizard-export-raw-summary-jump"',
    'id="wizard-export-deprecated-summary-jump"',
    'id="wizard-export-unknown-summary-jump"',
    'id="wizard-export-profile-state"',
    'id="wizard-export-workspace-state"',
    'id="wizard-export-validation-state"',
    'id="wizard-export-ready-state"',
    'id="wizard-export-policy-count"',
    'id="wizard-export-preferences-count"',
    'id="wizard-export-raw-count"',
    'id="wizard-export-deprecated-count"',
    'id="wizard-export-unknown-count"',
    'id="wizard-export-raw-jump"',
    'id="wizard-export-deprecated-jump"',
    'id="wizard-export-unknown-jump"',
    'id="wizard-export-boundary-register"',
    'id="wizard-export-drilldown"',
    'id="wizard-export-ready-copy"',
    'id="wizard-export-checklist"',
    'id="wizard-export-baseline-copy"',
    'id="wizard-export-baseline-list"',
    'id="wizard-cis-final-summary"',
    'id="wizard-cis-exceptions-count"',
    'id="wizard-cis-exceptions-reasons"',
    'id="wizard-cis-exceptions-details"',
    'id="wizard-export-next-steps"',
    'id="wizard-export-ready-now"',
    'id="wizard-export-included-now"',
    'id="wizard-export-missing-now"',
    'id="wizard-export-review-now"',
    'id="wizard-export-summary-network"',
    'id="wizard-export-guided-summary-list"',
    'id="wizard-export-guided-group-profile"',
    'id="wizard-export-guided-group-browser"',
    'id="wizard-export-guided-group-privacy"',
    'id="wizard-export-guided-group-features"',
    'id="wizard-export-guided-group-ai"',
    'id="wizard-export-summary-home"',
    'id="wizard-export-summary-search"',
    'id="wizard-export-summary-features"',
    'id="wizard-export-summary-ai"',
    'id="wizard-export-summary-privacy"',
    'id="wizard-export-summary-network-jump"',
    'id="wizard-export-summary-home-jump"',
    'id="wizard-export-summary-search-jump"',
    'id="wizard-export-summary-features-jump"',
    'id="wizard-export-summary-ai-jump"',
    'id="wizard-export-summary-privacy-jump"',
    'id="wizard-export-shareable-text"',
    'id="wizard-export-shareable-details"',
    'id="wizard-export-shareable-generate"',
    'id="wizard-export-shareable-copy"',
    'id="wizard-export-shareable-status"',
    'id="wizard-export-save-action"',
    'id="wizard-export-validate-action"',
    'id="wizard-export-firefox-policies"',
    'id="wizard-export-download-hint"',
    'id="wizard-export-ready-card"',
    'data-extension-profile="uBlock0@raymondhill.net"',
    'data-extension-profile="adguardadblocker@adguard.com"',
    'data-extension-profile="https-everywhere@eff.org"',
    'wizard-extension-profile-row',
    'wizard-extension-profile-status',
    'data-extension-profile-status="uBlock0@raymondhill.net"',
    'data-extension-profile-status="adguardadblocker@adguard.com"',
    'data-extension-profile-status="https-everywhere@eff.org"',
)

PROFILES_PAGE_GUIDED_UX_REGRESSION_TOKENS = (
    "Guided editor",
    "All settings",
    "Task-first setup",
    "Full visual catalog",
    "Raw policies.json editing",
    "Save, validate, download",
    "Download policies.json",
    "Latest edits",
    "Final validation",
    "Ready to download",
    "Review by area",
    'id="wizard-extension-fine-tuning-toggle"',
    'id="wizard-extension-fine-tuning-panel"',
    'data-extension-profile-toggle="uBlock0@raymondhill.net"',
    'data-extension-profile-toggle="adguardadblocker@adguard.com"',
    'data-extension-profile-toggle="https-everywhere@eff.org"',
    'aria-controls="wizard-extension-fine-tuning-panel"',
    'aria-controls="wizard-extension-profile-details-ublock"',
    'aria-controls="wizard-extension-profile-details-adguard"',
    'aria-controls="wizard-extension-profile-details-https-everywhere"',
)

PROFILES_PAGE_FOOTER_TOKENS = (
    'id="lang"',
    'rel="icon" href="/favicon.ico?v=',
    'id="theme"',
    'value="system"',
    'value="light"',
    'value="dark"',
    "resolveBrowserLanguage",
    '/static/profiles_head_bootstrap.js',
    "Valery Ledovskoy",
    "https://www.mozilla.org/MPL/2.0/",
    "/api/profiles",
)


def _profiles_page_response():
    client = make_test_client(app)
    return client.get("/profiles/new")


def test_profiles_page_locale_picker_displays_target_locale_metadata():
    response = _profiles_page_response()
    soup = BeautifulSoup(response.text, "html.parser")
    lang_select = soup.find(id="lang")
    options = {option.get("value"): option for option in lang_select.find_all("option")}

    assert list(options) == ["system", "en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert options["en"].get_text(strip=True) == "English"
    assert options["ru"].get_text(strip=True) == "Русский"
    assert options["de"].get_text(strip=True) == "Deutsch"
    assert options["zh-CN"].get_text(strip=True) == "简体中文"
    assert options["fr"].get_text(strip=True) == "Français"
    assert options["es-ES"].get_text(strip=True) == "Español"
    assert options["zh-CN"]["data-locale-bcp47"] == "zh-CN"
    assert options["es-ES"]["data-locale-code"] == "es-ES"

    assert options["en"]["data-locale-has-catalog"] == "true"
    assert options["ru"]["data-locale-has-catalog"] == "true"
    assert options["de"]["data-locale-has-catalog"] == "true"
    assert options["zh-CN"]["data-locale-has-catalog"] == "true"
    assert options["fr"]["data-locale-has-catalog"] == "true"
    assert options["es-ES"]["data-locale-has-catalog"] == "true"
    assert not options["de"].has_attr("disabled")
    assert not options["zh-CN"].has_attr("disabled")
    assert not options["fr"].has_attr("disabled")
    assert not options["es-ES"].has_attr("disabled")


def test_theme_safe_surface_cards_and_dark_white_override_contract():
    css = Path("app/static/profiles.css").read_text(encoding="utf-8")
    editor_template = Path("app/templates/profiles/_page_editor_chrome.html").read_text(encoding="utf-8")
    settings_template = Path("app/templates/profiles/_page_settings_workspace.html").read_text(encoding="utf-8")

    assert ".theme-subcard {" in css
    assert 'html[data-theme="dark"] .theme-subcard,' in css
    assert ".editor-chrome-status-item {" in css
    assert 'html[data-theme="dark"] .editor-chrome-status-item,' in css
    assert 'html[data-theme="dark"] [class~="bg-white/80"]' in css
    assert 'html[data-theme="dark"] [class~="border-white/70"]' in css
    assert 'html[data-theme="dark"] [class~="border-slate-200"]' in css
    assert 'html[data-theme="dark"] [class~="decoration-slate-300"]' in css
    assert 'html[data-theme="dark"] [class~="hover:text-slate-900"]:hover' in css
    assert ".wizard-search-engine-preset:hover {" in css
    assert "background: rgba(255, 255, 255, 0.86);" in css
    assert "appearance: none;" in css
    assert "color-scheme: light;" in css
    assert "color-scheme: dark;" in css
    assert 'url("data:image/svg+xml,' in css
    assert editor_template.count("editor-chrome-status-item") >= 4
    assert settings_template.count("theme-subcard") >= 4


def _assert_en_locale_catalog(locale_json: dict[str, str]) -> None:
    assert locale_json["profiles.title"] == "Browser profile manager"
    assert locale_json["profiles.workspace_overview"] == "Profile setup overview"
    assert locale_json["profiles.footer_owner"] == "Valery Ledovskoy"
    assert locale_json["profiles.footer_license_prefix"] == "Licensed under"
    assert locale_json["profiles.footer_license_label"] == "Mozilla Public License 2.0"
    assert locale_json["profiles.theme_system"] == "System"
    assert locale_json["profiles.locale_system"] == "Browser"
    assert locale_json["profiles.locale_option_en"] == "English"
    assert locale_json["profiles.locale_option_ru"] == "Russian"
    assert locale_json["profiles.locale_option_de"] == "German"
    assert locale_json["profiles.locale_option_zh_cn"] == "Simplified Chinese"
    assert locale_json["profiles.locale_option_fr"] == "French"
    assert locale_json["profiles.locale_option_es_es"] == "Spanish"
    assert locale_json["profiles.editor_chrome_title"] == "Guided editor"
    assert locale_json["profiles.editor_chrome_profile_id"] == "Profile ID"
    assert locale_json["profiles.editor_chrome_validation"] == "Validation"
    assert locale_json["profiles.editor_chrome_modes_title"] == "Open another mode"
    assert locale_json["profiles.editor_chrome_settings_link"] == "All settings"
    assert locale_json["profiles.editor_chrome_guided_body"].startswith("Task-first setup")
    assert locale_json["profiles.editor_chrome_settings_body"].startswith("Full visual catalog")
    assert locale_json["profiles.editor_chrome_json_body"].startswith("Raw policies.json editing")
    assert locale_json["profiles.editor_chrome_json_link"] == "JSON editor"
    assert locale_json["profiles.wizard_context_existing"].startswith("You are editing")
    assert locale_json["profiles.wizard_step_one"] == "Profile & baseline"
    assert locale_json["profiles.wizard_step_two"] == "Browser access & defaults"
    assert locale_json["profiles.wizard_step_three"] == "Security & privacy"
    assert locale_json["profiles.wizard_step_four"] == "Users, add-ons & sites"
    assert locale_json["profiles.wizard_step_five"] == "AI & smart features"
    assert locale_json["profiles.wizard_step_six"] == "Review & export"
    assert locale_json["profiles.wizard_profile_identity_title"] == "Profile identity"
    assert locale_json["profiles.wizard_profile_identity_body"].startswith(
        "Name the profile and choose the Firefox schema channel"
    )
    assert locale_json["profiles.workspace_scope_guided"] == "Guided editor"
    assert locale_json["profiles.workspace_scope_advanced"] == "All settings"
    assert locale_json["profiles.workspace_scope_current_label"] == "Current mode"
    assert locale_json["profiles.workspace_scope_guided_title"] == (
        "Best for most profile work"
    )
    assert locale_json["profiles.workspace_scope_advanced_title"] == (
        "Only when Guided editor is not enough"
    )
    assert locale_json["profiles.advanced_context_title"] == "Continue in All settings"
    assert locale_json["profiles.advanced_context_empty_title"] == (
        "Starting here without a step handoff?"
    )
    assert locale_json["profiles.advanced_context_action_editor"] == "Open full policies.json"
    assert locale_json["profiles.advanced_utility_title"] == "All settings workflow"
    assert locale_json["profiles.advanced_utility_editor_body"] == (
        "Use the full Firefox policies.json when you already know the lower-level keys you need to manage."
    )
    assert locale_json["profiles.advanced_downloads_title"] == "Download policies.json"
    assert locale_json["profiles.editor_section_hint"] == (
        "Edit the full Firefox policies.json document here when Guided editor and All settings are not enough."
    )
    assert locale_json["profiles.advanced_review_save_title"] == "Latest edits"
    assert locale_json["profiles.advanced_review_download_title"] == "Ready to download"
    assert locale_json["profiles.wizard_starter_basic_label"] == "Basic corporate"
    assert locale_json["profiles.wizard_scenarios_title"] == "What are you setting up?"
    assert locale_json["profiles.wizard_scenario_summary_title"] == "Best starting path"
    assert locale_json["profiles.wizard_setup_impact_title"] == "What this will apply"
    assert locale_json["profiles.wizard_baseline_recommended_title"] == "Change suggested baseline"
    assert locale_json["profiles.wizard_baseline_secondary_title"] == "Start another way"
    assert locale_json["profiles.wizard_baseline_summary_title"] == "This baseline will preconfigure"
    assert locale_json["profiles.wizard_cis_title"] == "CIS benchmark overlay"
    assert locale_json["profiles.wizard_cis_l2_copy"] == (
        "Applies Level 1 and the stricter Level 2 controls for hardened environments."
    )
    assert locale_json["profiles.wizard_export_review_cis_manual"] == (
        "Review CIS conflicts where the base scenario stayed in place: {count}."
    )
    assert locale_json["profiles.wizard_cis_review_manual_title"] == (
        "CIS manual review: {path}"
    )
    assert locale_json["profiles.wizard_cis_exceptions_count"] == (
        "CIS exceptions needing notes: {count}."
    )
    assert locale_json["profiles.wizard_cis_exceptions_show_full"] == (
        "Show full CIS exception notes"
    )
    assert locale_json["profiles.wizard_baseline_preview_title"] == (
        "Preview changes before you apply"
    )
    assert locale_json["profiles.wizard_step_undo"] == "Undo this step"
    assert locale_json["profiles.wizard_step_reset"] == "Reset this step"
    assert locale_json["profiles.wizard_export_shareable_title"] == "Shareable summary"
    assert locale_json["profiles.wizard_export_shareable_generate"] == (
        "Generate/copy shareable summary"
    )
    assert locale_json["profiles.wizard_export_shareable_copy"] == "Copy summary"
    assert locale_json["profiles.wizard_baseline_preview_addons"] == (
        "Managed add-on rollout rules would change"
    )
    assert locale_json["profiles.hard_delete"] == "Delete permanently"
    assert locale_json["profiles.reset_library"] == "Clear profile library"
    assert locale_json["profiles.library_filtered_short"] == "Filtered"
    assert locale_json["profiles.library_total_short"] == "Library"
    assert locale_json["profiles.library_column_context"] == "Owner / note"
    assert locale_json["profiles.library_action_all_settings"] == "All settings"
    assert locale_json["profiles.library_action_duplicate"] == "Duplicate"
    assert locale_json["profiles.library_profile_archived"] == "Profile {name} archived."
    assert locale_json["profiles.library_filter_all_schemas"] == "All schemas"
    assert locale_json["profiles.library_filter_archived"] == "Archived"
    assert locale_json["profiles.library_validation_invalid"] == "Failed"
    assert locale_json["profiles.library_validation_not_validated"] == "Not validated"
    assert locale_json["profiles.library_sort_by"] == "Sort by"
    assert locale_json["profiles.dock_group_primary"] == "Main actions"
    assert locale_json["profiles.reload"] == "Refresh list"
    assert locale_json["profiles.import_firefox_policies_json"] == "Import policies.json"
    assert locale_json["profiles.import_firefox_policies_ready"].startswith("Choose a Firefox")
    assert locale_json["profiles.status_import_firefox_policies_done"] == (
        "Imported new profile {name}. Schema: {schema}. Validation: {validation}."
    )
    assert locale_json["profiles.error_import_firefox_policies"].startswith("Import error")
    assert locale_json["profiles.none_selected"] == "Choose a profile"
    assert locale_json["profiles.list_open"] == "Open profile"
    assert locale_json["profiles.list_selected_hint"] == "This profile is currently open."
    assert locale_json["profiles.compare_title"] == "Compare two profiles"
    assert locale_json["profiles.compare_action"] == "Compare here"
    assert locale_json["profiles.clone_action"] == "Clone and adjust"
    assert locale_json["profiles.clone_handoff_title"] == (
        "Recommended checks for this derived draft"
    )
    assert locale_json["profiles.clone_handoff_compare"] == "Compare now"
    assert locale_json["profiles.compare_summary_policies"] == "Changed policy areas"
    assert locale_json["profiles.compare_guided_areas_title"] == "Differences by guided area"
    assert locale_json["profiles.wizard_summary_derived"] == "Based on"
    assert locale_json["profiles.lifecycle_review_title"] == "Lifecycle review"
    assert locale_json["profiles.selection_empty_status"] == "Choose a profile or start a new draft to begin."
    assert locale_json["profiles.confirm_hard_delete"].startswith("Delete this profile permanently")
    assert locale_json["profiles.confirm_reset_library"].startswith("Delete every profile")
    assert locale_json["profiles.wizard_search_title"] == "Search defaults"
    assert locale_json["profiles.wizard_search_surfaces_workflow_title"] == "Search experience workflow"
    assert locale_json["profiles.wizard_general_policy_title"] == "General browser behavior"
    assert locale_json["profiles.wizard_general_policy_preset_managed_title"] == (
        "Managed browser upkeep"
    )
    assert locale_json["profiles.wizard_upkeep_governance_title"] == "Browser upkeep workflow"
    assert locale_json["profiles.wizard_home_surfaces_workflow_title"] == "Home and startup workflow"
    assert locale_json["profiles.wizard_language_governance_title"] == "Language governance workflow"
    assert locale_json["profiles.wizard_ai_controls_title"] == "Firefox 151 AI policy controls"
    assert locale_json["profiles.wizard_general_policy_section_state_download_prompt_on"] == (
        "Ask where to save downloads"
    )
    assert locale_json["profiles.wizard_settings_map_label"] == "Firefox Settings areas"
    assert locale_json["profiles.wizard_settings_covered_title"] == "Settings covered"
    assert locale_json["profiles.wizard_preferences_covered_title"] == "All settings preference coverage"
    assert locale_json["profiles.wizard_preferences_general_handoff_title"] == (
        "All settings for General preferences"
    )
    assert locale_json["profiles.wizard_preferences_search_handoff_title"] == (
        "All settings for Search preferences"
    )
    assert locale_json["profiles.wizard_preferences_handoff_count"] == "Configured: {count}"
    assert locale_json["profiles.wizard_settings_controls_label"] == "What you can change here"
    assert locale_json["profiles.wizard_settings_filter_all"] == "All"
    assert locale_json["profiles.wizard_settings_search_label"] == "Find a setting"
    assert locale_json["profiles.wizard_settings_search_clear"] == "Clear"
    assert locale_json["profiles.sort_updated_at"] == "Updated"
    assert locale_json["profiles.sort_schema"] == "Schema"
    assert locale_json["profiles.order_desc"] == "Descending"
    assert locale_json["profiles.status_draft_ready"].startswith("Draft ready")
    assert locale_json["profiles.editor_formatted"] == "Document formatted."
    assert locale_json["profiles.wizard_settings_search_kind_preference_preset"] == "Preference preset"
    assert locale_json["profiles.wizard_settings_search_kind_preference_bundle"] == "Preference bundle"
    assert locale_json["profiles.wizard_settings_search_kind_known_preference"] == "Known preference"
    assert locale_json["profiles.wizard_settings_search_kind_policy_blueprint"] == "Schema policy"
    assert locale_json["profiles.wizard_section_network_access"] == "Network and enterprise access"
    assert locale_json["profiles.wizard_shell_title"] == "Technical coverage for this step"
    assert locale_json["profiles.wizard_home_surface_open"] == "Open"
    assert locale_json["profiles.wizard_step_two_index_title"] == "Step map"
    assert locale_json["profiles.wizard_step_two_index_proxy"] == "Proxy"
    assert locale_json["profiles.wizard_browser_defaults_map_title"] == "Step map"
    assert locale_json["profiles.wizard_browser_defaults_review_title"] == "Local review"
    assert locale_json["profiles.wizard_step_four_index_title"] == "Search step map"
    assert locale_json["profiles.wizard_step_four_index_engines"] == "Managed engines"
    assert locale_json["profiles.wizard_user_environment_map_title"] == (
        "User environment map"
    )
    assert locale_json["profiles.wizard_user_environment_map_extensions"] == "Extensions"
    assert locale_json["profiles.wizard_user_environment_map_websites"] == "Websites"
    assert locale_json["profiles.wizard_disclosure_show"] == "Show details"
    assert locale_json["profiles.wizard_disclosure_hide"] == "Hide details"
    assert locale_json["profiles.wizard_review_filter_changed"] == "Changed"
    assert locale_json["profiles.wizard_review_filter_attention"] == "Needs attention"
    assert locale_json["profiles.wizard_review_filter_advanced"] == "Outside Guided editor"
    assert locale_json["profiles.wizard_review_filter_all"] == "All"
    assert locale_json["profiles.wizard_review_empty_changed"] == "No changed items here yet."
    assert locale_json["profiles.wizard_review_empty_advanced"] == (
        "No items outside Guided editor are listed here right now."
    )
    assert locale_json["profiles.wizard_long_list_show_all"] == "Show all {count}"
    assert locale_json["profiles.wizard_long_list_show_fewer"] == "Show fewer"
    assert locale_json["profiles.wizard_shell_badge_raw"] == "Raw fallback"
    assert locale_json["profiles.wizard_shell_boolean_true"] == "Enabled"
    assert locale_json["profiles.wizard_shell_branch_mode_simple"] == "Simple on/off"
    assert locale_json["profiles.wizard_shell_true_map_hint"] == "One hostname or origin per line."
    assert locale_json["profiles.wizard_shell_array_add"] == "Add item"
    assert locale_json["profiles.wizard_shell_json_error"] == "Nested values must be valid JSON."
    assert locale_json["profiles.wizard_shell_nested_unsupported"] == (
        "Some nested fields still fall back to raw JSON."
    )
    assert locale_json["profiles.wizard_shell_dictionary_add"] == "Add entry"
    assert locale_json["profiles.wizard_shell_dictionary_key_label"] == "Entry key"
    assert locale_json["profiles.wizard_schema_policy_applied"] == "Schema-driven policy updated."
    assert locale_json["profiles.wizard_settings_general_updates"] == "Updates"
    assert locale_json["profiles.wizard_settings_privacy_passwords"] == "Passwords"
    assert locale_json["profiles.wizard_settings_sync_account"] == "Firefox Account"
    assert locale_json["profiles.wizard_preferences_general_title"] == (
        "Managed Preferences for General"
    )
    assert locale_json["profiles.wizard_preferences_general_focus_startup_title"] == (
        "Startup and restore"
    )
    assert locale_json["profiles.wizard_preferences_bundles_title"] == "Quick bundles"
    assert locale_json["profiles.wizard_preferences_bundles_body"].startswith("Apply a small")
    assert locale_json["profiles.wizard_preferences_known_title"] == "Known Firefox preferences"
    assert locale_json["profiles.wizard_preferences_known_body"].startswith("Add a known key")
    assert locale_json["profiles.wizard_preferences_gui_label"] == "Firefox Settings areas"
    assert locale_json["profiles.wizard_preferences_add_button"] == "Add preference"
    assert locale_json["profiles.wizard_preferences_value_custom"] == "Custom: {value}"
    assert locale_json["profiles.wizard_preferences_hint_known"] == (
        "Known preference with a suggested managed default."
    )
    assert locale_json["profiles.wizard_preferences_preset_applied"] == "Preference preset added."
    assert locale_json["profiles.wizard_preferences_bundle_applied"] == "Preference bundle added."
    assert locale_json["profiles.wizard_preferences_known_applied"] == "Known preference added."
    assert locale_json["profiles.wizard_preferences_bundle_state_applied"] == "Already applied"
    assert locale_json["profiles.wizard_preferences_bundle_state_partial"] == (
        "Partially applied: {matched}/{total}"
    )
    assert locale_json["profiles.wizard_preferences_bundle_state_conflict"] == (
        "Conflicting values: {conflicts}"
    )
    assert locale_json["profiles.wizard_preferences_bundle_state_missing"] == "Not applied yet"
    assert locale_json["profiles.wizard_preferences_known_state_suggested"] == (
        "Using suggested default"
    )
    assert locale_json["profiles.wizard_preferences_known_state_present"] == "Already present"
    assert locale_json["profiles.wizard_preferences_known_state_overridden"] == (
        "Overridden manually"
    )
    assert locale_json["profiles.wizard_preferences_known_state_missing"] == "Not added yet"
    assert locale_json["profiles.wizard_preferences_preset_privacy_https_only_title"] == (
        "Enable HTTPS-Only Mode"
    )
    assert locale_json["profiles.wizard_preferences_preset_sync_passwords_off_title"] == (
        "Do not sync passwords"
    )
    assert locale_json["profiles.wizard_security_map_title"] == "Security posture map"
    assert locale_json["profiles.wizard_privacy_review_title"] == (
        "Security posture at a glance"
    )
    assert locale_json["profiles.wizard_privacy_review_user_data"] == (
        "Privacy and saved credentials"
    )
    assert locale_json["profiles.wizard_privacy_review_cleanup"] == "Shutdown cleanup"
    assert locale_json["profiles.wizard_hardening_preset_balanced_title"] == (
        "Balanced hardening"
    )
    assert locale_json["profiles.wizard_hardening_impact_cleanup"] == "Shutdown cleanup"
    assert locale_json["profiles.wizard_hardening_subposture_privacy"] == (
        "Adjust privacy data posture"
    )
    assert locale_json["profiles.wizard_privacy_outcome_telemetry_title"] == (
        "Telemetry and studies"
    )
    assert locale_json["profiles.wizard_privacy_outcome_site_data_title"] == (
        "Cookies and permissions"
    )
    assert locale_json["profiles.wizard_hardening_governance_title"] == (
        "Hardening workflow"
    )
    assert locale_json["profiles.wizard_hardening_governance_next_label"] == (
        "Next recommendation"
    )
    assert locale_json["profiles.wizard_hardening_governance_remaining_count"] == (
        "Remaining: {count}"
    )
    assert locale_json["profiles.wizard_privacy_review_permissions"] == "Permissions"
    assert locale_json["profiles.wizard_privacy_review_permissions_subcounts"] == (
        "{configured} configured • {locked} strict"
    )
    assert locale_json["profiles.wizard_privacy_review_cookies"] == "Cookie behavior"
    assert locale_json["profiles.wizard_network_review_title"] == (
        "What Firefox will use for network access"
    )
    assert locale_json["profiles.wizard_network_review_windows_sso"] == "Windows sign-in"
    assert locale_json["profiles.wizard_home_review_title"] == (
        "What users will see at startup"
    )
    assert locale_json["profiles.wizard_home_review_user_messaging"] == (
        "Tips and recommendations"
    )
    assert locale_json["profiles.wizard_search_review_title"] == "How search will work"
    assert locale_json["profiles.wizard_search_review_custom"] == "Custom search engines"
    assert locale_json["profiles.wizard_homepage_section_state_invalid"] == (
        "Startup expects a homepage URL."
    )
    assert locale_json["profiles.wizard_firefox_home_section_state_configured"] == (
        "Show: {show} • Hide: {hide}"
    )
    assert locale_json["profiles.wizard_search_defaults_section_state_conflict"] == (
        "Search suggestions are off while Firefox Suggest surfaces stay enabled"
    )
    assert locale_json["profiles.wizard_firefox_suggest_section_state_conflict"] == (
        "Dependent surfaces need web suggestions"
    )
    assert locale_json["profiles.wizard_preferences_remove_button"] == "Remove"
    assert locale_json["profiles.wizard_preferences_field_name"] == "Preference key"
    assert locale_json["profiles.wizard_preferences_field_status"] == "Status"
    assert locale_json["profiles.wizard_preferences_field_type"] == "Value type"
    assert locale_json["profiles.wizard_preferences_field_value"] == "Value"
    assert locale_json["profiles.wizard_preferences_status_default"] == "default"
    assert locale_json["profiles.wizard_preferences_type_auto_option"] == "Infer"
    assert locale_json["profiles.wizard_preferences_meta_target"] == "Firefox settings"
    assert locale_json["profiles.wizard_preferences_summary_default"].startswith(
        "Set the preference key"
    )
    assert locale_json["profiles.wizard_preferences_bundle_home_focus_title"] == (
        "Focused Firefox Home"
    )
    assert locale_json["profiles.wizard_preferences_bundle_permissions_title"] == (
        "Lock down site permissions"
    )
    assert locale_json["profiles.wizard_search_add_title"] == "Managed custom search engines"
    assert locale_json["profiles.wizard_search_add_button"] == "Add engine"
    assert locale_json["profiles.wizard_search_presets_title"] == "Quick presets"
    assert locale_json["profiles.wizard_search_presets_menu_title"] == "Add preset engine"
    assert locale_json["profiles.wizard_search_defaults_preset_restricted_title"] == (
        "Restricted search surfaces"
    )
    assert locale_json["profiles.wizard_search_preset_ddg_title"] == "DuckDuckGo"
    assert locale_json["profiles.wizard_search_preset_applied"] == "Search engine preset added."
    assert locale_json["profiles.wizard_search_preset_state_applied"] == (
        "Preset matches current engine"
    )
    assert locale_json["profiles.wizard_search_preset_state_partial"] == "Preset partially applied"
    assert locale_json["profiles.wizard_search_preset_state_conflict"] == (
        "Preset differs from current engine"
    )
    assert locale_json["profiles.wizard_search_preset_state_missing"] == "Preset not added yet"
    assert locale_json["profiles.wizard_search_engine_summary_default"].startswith(
        "GET by default"
    )
    assert locale_json["profiles.wizard_search_engine_warning_required"].startswith(
        "Required for a valid engine"
    )
    assert locale_json["profiles.wizard_search_engine_method_post"] == "POST"
    assert locale_json["profiles.wizard_search_engine_advanced_title"] == "Advanced fields"
    assert locale_json["profiles.wizard_firefox_home_title"] == "Firefox Home cards"
    assert locale_json["profiles.wizard_firefox_home_preset_focused_title"] == (
        "Focused Firefox Home"
    )
    assert locale_json["profiles.wizard_firefox_home_recommendations_title"] == (
        "Stories and sponsored content"
    )
    assert locale_json["profiles.wizard_home_step_summary_title"] == "Home setup summary"
    assert locale_json["profiles.wizard_firefox_suggest_title"] == "Firefox Suggest"
    assert locale_json["profiles.wizard_firefox_suggest_preset_locked_down_title"] == (
        "Strict suggestions off"
    )
    assert locale_json["profiles.wizard_homepage_preset_locked_title"] == (
        "Locked homepage"
    )
    assert locale_json["profiles.wizard_home_overrides_preset_managed_title"] == (
        "Managed landing flow"
    )
    assert locale_json["profiles.wizard_proxy_mode_manual"] == "Manual proxy"
    assert locale_json["profiles.wizard_extension_profile_mode_force"] == "Force install"
    assert locale_json["profiles.wizard_extension_profile_ublock_title"] == "uBlock Origin"
    assert locale_json["profiles.wizard_extension_profile_state_missing"] == "No explicit rule"
    assert locale_json["profiles.wizard_extension_profile_state_catalog_url"] == (
        "Uses store download link"
    )
    assert locale_json["profiles.wizard_extension_profile_state_configured"] == "Configured"
    assert locale_json["profiles.wizard_extension_profile_state_custom_url"] == "Custom download link"
    assert locale_json["profiles.wizard_extensions_review_title"] == (
        "How add-ons will be managed"
    )
    assert locale_json["profiles.wizard_sync_focus_managed_title"] == (
        "Account access and guidance"
    )
    assert locale_json["profiles.wizard_extensions_preset_managed_title"] == (
        "Managed rollout"
    )
    assert locale_json["profiles.wizard_extensions_governance_selector_hint"].startswith(
        "Choose the extension governance"
    )
    assert locale_json["profiles.wizard_extensions_governance_managed_title"] == (
        "Managed allowlist"
    )
    assert locale_json["profiles.wizard_extensions_governance_curated_title"] == (
        "Curated rollout"
    )
    assert locale_json["profiles.wizard_extensions_governance_title"] == (
        "Extension governance workflow"
    )
    assert locale_json["profiles.wizard_extensions_review_body"].startswith("Quick check")
    assert locale_json["profiles.wizard_extensions_review_curated"] == "Known add-ons"
    assert locale_json["profiles.wizard_extensions_review_arbitrary"] == (
        "Extra add-on rules"
    )
    assert locale_json["profiles.wizard_extensions_review_custom_urls"] == (
        "Custom install sources"
    )
    assert locale_json["profiles.wizard_extensions_review_open"] == "Open"
    assert locale_json["profiles.wizard_extension_rule_show"] == "Show list"
    assert locale_json["profiles.wizard_extensions_rule_count"] == "Entries: {count}"
    assert locale_json["profiles.wizard_export_compatibility_title"] == "Technical coverage"
    assert locale_json["profiles.wizard_shared_device_workflow_title"] == "Shared-device workflow"
    assert locale_json["profiles.wizard_export_section_ready_title"] == "Final checklist"
    assert locale_json["profiles.wizard_export_section_changes_title"] == "Review before handoff"
    assert locale_json["profiles.wizard_export_section_technical_title"] == (
        "Technical details"
    )
    assert locale_json["profiles.wizard_export_title"] == "Save, validate, download"
    assert locale_json["profiles.wizard_export_workspace_state"] == "Latest edits"
    assert locale_json["profiles.wizard_export_validation_state"] == "Final validation"
    assert locale_json["profiles.wizard_export_ready_state"] == "Ready to download"
    assert locale_json["profiles.wizard_export_ready_title"] == "Download policies.json"
    assert locale_json["profiles.wizard_export_guided_summary_title"] == "Review by area"
    assert locale_json["profiles.wizard_export_guided_ai"] == "AI and smart features"
    assert locale_json["profiles.wizard_cleanup_preset_shared_title"] == (
        "Shared-device cleanup"
    )
    assert locale_json["profiles.wizard_homepage_shared_preset_portal_title"] == (
        "Locked shared-device portal"
    )
    assert locale_json["profiles.wizard_website_filter_shared_preset_allow_only_title"] == (
        "Allow only managed destinations"
    )
    assert locale_json["profiles.wizard_export_next_steps_title"] == "Before you download"
    assert locale_json["profiles.wizard_export_ready_now_title"] == "Already ready"
    assert locale_json["profiles.wizard_cis_final_summary_title"] == "CIS final summary"
    assert locale_json["profiles.wizard_cis_final_summary_manual"] == "Manual review"
    assert locale_json["profiles.wizard_export_included_title"] == (
        "Included in the policies.json you download now"
    )
    assert locale_json["profiles.wizard_export_missing_title"] == (
        "Not in the downloaded policies.json yet"
    )
    assert locale_json["profiles.wizard_export_review_title"] == (
        "Still worth reviewing before handoff"
    )
    assert locale_json["profiles.wizard_export_baseline_summary_title"] == "Baseline guardrails"
    assert locale_json["profiles.wizard_export_shareable_title"] == "Shareable summary"
    assert locale_json["profiles.wizard_export_shareable_generate"] == (
        "Generate/copy shareable summary"
    )
    assert locale_json["profiles.wizard_export_shareable_copy"] == "Copy summary"
    assert locale_json["profiles.wizard_export_guided_privacy_shutdown_cleanup"] == (
        "Shutdown cleanup enabled"
    )
    assert locale_json["profiles.wizard_export_download_hint_ready"] == (
        "The policies.json download already uses the latest saved version."
    )
    assert locale_json["profiles.dock_state_kicker"] == "Current flow"
    assert locale_json["profiles.dock_state_dirty_title"] == "Save the latest edits"
    assert locale_json["profiles.dock_state_archived_title"] == (
        "Restore this archived profile"
    )
    assert locale_json["profiles.wizard_export_profile_saved"] == "Saved profile #{id}"
    assert locale_json["profiles.wizard_export_state_unsaved_existing"] == (
        "Save the latest edits before downloading."
    )
    assert locale_json["profiles.download_firefox_policies_json"] == (
        "Download Firefox policies.json"
    )
    assert locale_json["profiles.wizard_export_state_ready"] == (
        "Everything is ready for download."
    )
    assert locale_json["profiles.wizard_export_ready_saved"] == (
        "This saved version is ready for Firefox policies.json download."
    )
    assert locale_json["profiles.wizard_export_unknown_count"] == "Unknown top-level keys"
    assert locale_json["profiles.wizard_export_check_ready"] == "Ready to download"
    assert locale_json["profiles.wizard_export_check_unsaved"] == "Unsaved edits"
    assert locale_json["profiles.wizard_bookmarks_review_title"] == (
        "How managed bookmarks are set up"
    )
    assert locale_json["profiles.wizard_bookmarks_review_nested"] == (
        "Nested bookmark trees"
    )
    assert locale_json["profiles.wizard_bookmarks_review_open"] == "Open"
    assert locale_json["profiles.wizard_bookmarks_handoff_title"] == "Bookmark editor"
    assert locale_json["profiles.wizard_bookmarks_open_action"] == "Open advanced"
    assert locale_json["profiles.wizard_bookmarks_row_state_toolbar"] == "Toolbar bookmark"
    assert locale_json["profiles.wizard_managed_bookmarks_row_state_invalid"] == (
        "Children JSON needs attention"
    )
    assert locale_json["profiles.wizard_website_access_review_title"] == (
        "How websites and links will behave"
    )
    assert locale_json["profiles.wizard_website_access_review_handlers"] == (
        "File and link handlers"
    )
    assert locale_json["profiles.wizard_website_governance_title"] == "Site access workflow"
    assert locale_json["profiles.wizard_website_access_decision_title"] == "Website access"
    assert locale_json["profiles.wizard_website_access_posture_label"] == (
        "Site access posture"
    )
    assert locale_json["profiles.wizard_website_access_handlers_label"] == (
        "Handler management"
    )
    assert locale_json["profiles.wizard_website_filter_preset_mixed_title"] == (
        "Blocked sites and exceptions"
    )
    assert locale_json["profiles.wizard_website_handlers_preset_protocols_title"] == (
        "Protocol links"
    )
    assert locale_json["profiles.wizard_website_filter_state_configured"] == (
        "Blocked: {blocked} • Exceptions: {exceptions}"
    )
    assert locale_json["profiles.wizard_authentication_state_configured"] == (
        "Controls: {controls} • Host rules: {rules}"
    )
    assert locale_json["profiles.wizard_certificates_state_with_roots"] == (
        "Installed: {count} • Enterprise roots enabled"
    )
    assert locale_json["profiles.wizard_doh_state_provider"] == "Custom provider"
    assert locale_json["profiles.wizard_proxy_preset_system_title"] == "Follow system proxy"
    assert locale_json["profiles.wizard_proxy_preset_pac_title"] == "PAC file"
    assert locale_json["profiles.wizard_network_enterprise_detail_title"] == (
        "Authentication and certificate details"
    )
    assert locale_json["profiles.wizard_network_enterprise_preset_managed_title"] == (
        "Managed enterprise access"
    )
    assert locale_json["profiles.wizard_language_preset_managed_title"] == (
        "Managed language baseline"
    )
    assert locale_json["profiles.wizard_language_ai_handoff_skip"].startswith(
        "Language and translation are already covered here."
    )
    assert locale_json["profiles.wizard_ai_posture_title"] == "AI posture"
    assert locale_json["profiles.wizard_ai_posture_disable_title"] == "Disable AI"
    assert locale_json["profiles.wizard_ai_generative_controls_title"] == "Generative AI settings"
    assert locale_json["profiles.wizard_network_enterprise_section_state_managed_preset"] == (
        "Windows SSO and enterprise roots enabled"
    )
    assert locale_json["profiles.wizard_trust_auth_workflow_title"] == (
        "Corporate trust and sign-in workflow"
    )
    assert locale_json["profiles.wizard_step_memory_title"] == (
        "Recently changed"
    )
    assert locale_json["profiles.wizard_step_memory_open"] == "Open step"
    assert locale_json["profiles.wizard_step_memory_current"] == "You are here"
    assert locale_json["profiles.wizard_export_boundary_register_title"] == (
        "What still stays advanced on purpose"
    )
    assert locale_json["profiles.wizard_export_drilldown_title"] == (
        "Detailed technical review"
    )
    assert locale_json["profiles.wizard_permissions_state_strict"] == (
        "Configured: {configured} • Strict: {strict}"
    )
    assert locale_json["profiles.wizard_permissions_nested_default"] == "Default: {value}"
    assert locale_json["profiles.wizard_cookies_state_strict"] == (
        "Cookie rules: {count} • Restricted"
    )
    assert locale_json["profiles.wizard_handlers_state_configured"] == (
        "Mappings: {total} • MIME: {mime} • Schemes: {schemes} • Extensions: {extensions}"
    )
    assert locale_json["profiles.wizard_handlers_nested_array_configured"] == (
        "Helper apps: {count}"
    )
    assert locale_json["profiles.wizard_user_messaging_state_configured"] == (
        "Enabled: {enabled} • Hidden: {disabled}"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_missing"] == (
        "No managed fields yet"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_catalog_url"] == (
        "Uses store download link"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_custom_url"] == (
        "Custom download link"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_install_url"] == (
        "Download link rule"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_mode_only"] == "Mode-only rule"
    assert locale_json["profiles.wizard_extension_settings_row_state_flags_only"] == (
        "Behavior flags only"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_configured"] == (
        "Rule configured"
    )
    assert locale_json["profiles.wizard_extensions_mode_blocked"] == "Block installs"
    assert locale_json["profiles.wizard_extensions_advanced_title"] == (
        "Advanced extension rules"
    )
    assert locale_json["profiles.wizard_extensions_advanced_install_permissions"] == (
        "Install source exceptions"
    )
    assert locale_json["profiles.wizard_extensions_advanced_arbitrary_rules"] == (
        "Arbitrary ExtensionSettings"
    )
    assert locale_json["profiles.wizard_extensions_advanced_count"] == "Configured: {count}"
    assert locale_json["profiles.status_revision_conflict"] == (
        "This profile changed in another tab. Reload it before saving again."
    )
    assert locale_json["profiles.conflict_title"] == "Save conflict"
    assert locale_json["profiles.conflict_reload_latest"] == "Reload latest"
    assert locale_json["profiles.conflict_save_as_copy"] == "Save as copy"
    assert locale_json["profiles.conflict_copy_name"] == (
        "{name} conflict copy from r{revision} at {time}"
    )
    assert locale_json["profiles.conflict_copy_created"] == "Saved local draft as {name}."
    assert locale_json["profiles.conflict_overwrite"] == "Overwrite anyway"
    assert locale_json["profiles.conflict_overwrite_confirm"].startswith("Overwrite the newer")


def _assert_ru_locale_catalog(locale_json: dict[str, str]) -> None:
    assert locale_json["profiles.title"] == "Менеджер профилей браузера"
    assert locale_json["profiles.workspace_overview"] == "Сводка по настройке профиля"
    assert locale_json["profiles.footer_owner"] == "Валерий Ледовской"
    assert locale_json["profiles.footer_license_prefix"] == "Лицензия"
    assert locale_json["profiles.footer_license_label"] == "Mozilla Public License 2.0"
    assert locale_json["profiles.theme_dark"] == "Тёмная"
    assert locale_json["profiles.locale_system"] == "По браузеру"
    assert locale_json["profiles.locale_option_en"] == "Английский"
    assert locale_json["profiles.locale_option_ru"] == "Русский"
    assert locale_json["profiles.locale_option_de"] == "Немецкий"
    assert locale_json["profiles.locale_option_zh_cn"] == "Китайский упрощённый"
    assert locale_json["profiles.locale_option_fr"] == "Французский"
    assert locale_json["profiles.locale_option_es_es"] == "Испанский"
    assert locale_json["profiles.editor_chrome_title"] == "Пошаговый редактор"
    assert locale_json["profiles.editor_chrome_profile_id"] == "ID профиля"
    assert locale_json["profiles.editor_chrome_validation"] == "Проверка"
    assert locale_json["profiles.editor_chrome_modes_title"] == "Открыть другой режим"
    assert locale_json["profiles.editor_chrome_settings_link"] == "Все настройки"
    assert locale_json["profiles.editor_chrome_guided_body"].startswith("Сценарная настройка")
    assert locale_json["profiles.editor_chrome_settings_body"].startswith("Полный визуальный каталог")
    assert locale_json["profiles.editor_chrome_json_body"].startswith("Редактирование сырого policies.json")
    assert locale_json["profiles.editor_chrome_json_link"] == "JSON-редактор"
    assert locale_json["profiles.wizard_step_one"] == "Профиль и основа"
    assert locale_json["profiles.wizard_step_two"] == "Доступ к браузеру и значения по умолчанию"
    assert locale_json["profiles.wizard_step_three"] == "Защита и приватность"
    assert locale_json["profiles.wizard_step_four"] == "Пользователи, дополнения и сайты"
    assert locale_json["profiles.wizard_step_five"] == "ИИ и умные функции"
    assert locale_json["profiles.wizard_step_six"] == "Проверка и выгрузка"
    assert locale_json["profiles.workspace_scope_guided"] == "Пошаговый редактор"
    assert locale_json["profiles.workspace_scope_advanced"] == "Все настройки"
    assert locale_json["profiles.workspace_scope_current_label"] == "Текущий режим"
    assert locale_json["profiles.workspace_scope_guided_title"] == (
        "Лучший путь для большей части работы"
    )
    assert locale_json["profiles.workspace_scope_advanced_title"] == (
        "Только когда Пошагового редактора уже недостаточно"
    )
    assert locale_json["profiles.advanced_context_title"] == "Продолжение во Всех настройках"
    assert locale_json["profiles.advanced_context_empty_title"] == (
        "Открыли это место без перехода из шага?"
    )
    assert locale_json["profiles.advanced_context_action_editor"] == (
        "Открыть полный policies.json"
    )
    assert locale_json["profiles.advanced_utility_title"] == (
        "Работа во Всех настройках"
    )
    assert locale_json["profiles.advanced_utility_editor_body"] == (
        "Используйте полный Firefox policies.json, когда уже знаете, какими низкоуровневыми ключами нужно управлять."
    )
    assert locale_json["profiles.advanced_downloads_title"] == "Скачать policies.json"
    assert locale_json["profiles.editor_section_hint"] == (
        "Редактируйте здесь полный Firefox policies.json, когда Пошагового редактора и Всех настроек уже недостаточно."
    )
    assert locale_json["profiles.advanced_review_save_title"] == "Последние правки"
    assert locale_json["profiles.advanced_review_download_title"] == (
        "Готово к скачиванию"
    )
    assert locale_json["profiles.status_revision_conflict"] == (
        "Этот профиль изменился в другой вкладке. Обновите его перед повторным сохранением."
    )
    assert locale_json["profiles.conflict_title"] == "Конфликт сохранения"
    assert locale_json["profiles.conflict_reload_latest"] == "Загрузить свежую"
    assert locale_json["profiles.conflict_save_as_copy"] == "Сохранить как копию"
    assert locale_json["profiles.conflict_copy_name"] == (
        "{name} — конфликтная копия с r{revision} от {time}"
    )
    assert locale_json["profiles.conflict_copy_created"] == (
        "Локальный черновик сохранён как «{name}»."
    )
    assert locale_json["profiles.conflict_overwrite"] == "Всё равно заменить"
    assert locale_json["profiles.conflict_overwrite_confirm"].startswith("Заменить более новый")
    assert locale_json["profiles.wizard_starter_basic_label"] == "Базовый корпоративный"
    assert locale_json["profiles.wizard_scenarios_title"] == "Какую задачу вы решаете?"
    assert locale_json["profiles.wizard_scenario_summary_title"] == "Лучший стартовый путь"
    assert locale_json["profiles.wizard_setup_impact_title"] == "Что будет применено"
    assert locale_json["profiles.wizard_baseline_recommended_title"] == "Изменить предложенную базу"
    assert locale_json["profiles.wizard_baseline_secondary_title"] == "Другие способы начать"
    assert locale_json["profiles.wizard_baseline_summary_title"] == "Что будет настроено сразу"
    assert locale_json["profiles.wizard_cis_title"] == "Наложение CIS Benchmark"
    assert locale_json["profiles.wizard_cis_l2_copy"] == (
        "Применяет Level 1 и более строгие Level 2 политики для усиленных сред."
    )
    assert locale_json["profiles.wizard_export_review_cis_manual"] == (
        "Проверьте CIS-конфликты, где значение базового сценария осталось в силе: {count}."
    )
    assert locale_json["profiles.wizard_cis_review_manual_title"] == (
        "CIS требует проверки: {path}"
    )
    assert locale_json["profiles.wizard_cis_exceptions_count"] == (
        "Исключений CIS с пояснениями: {count}."
    )
    assert locale_json["profiles.wizard_cis_exceptions_show_full"] == (
        "Показать все комментарии к исключениям"
    )
    assert locale_json["profiles.wizard_baseline_preview_title"] == (
        "Предпросмотр изменений до применения"
    )
    assert locale_json["profiles.wizard_step_undo"] == "Откатить шаг"
    assert locale_json["profiles.wizard_step_reset"] == "Сбросить шаг"
    assert locale_json["profiles.wizard_export_shareable_title"] == "Выжимка для передачи"
    assert locale_json["profiles.wizard_export_shareable_generate"] == (
        "Сформировать/скопировать выжимку"
    )
    assert locale_json["profiles.wizard_export_shareable_copy"] == "Скопировать выжимку"
    assert locale_json["profiles.wizard_baseline_preview_addons"] == (
        "Изменятся управляемые правила дополнений"
    )
    assert locale_json["profiles.hard_delete"] == "Удалить навсегда"
    assert locale_json["profiles.reset_library"] == "Очистить библиотеку профилей"
    assert locale_json["profiles.library_filtered_short"] == "Отфильтровано"
    assert locale_json["profiles.library_total_short"] == "Всего"
    assert locale_json["profiles.library_column_context"] == "Владелец / заметка"
    assert locale_json["profiles.library_action_all_settings"] == "Все настройки"
    assert locale_json["profiles.library_action_duplicate"] == "Дублировать"
    assert locale_json["profiles.library_profile_archived"] == "Профиль «{name}» отправлен в архив."
    assert locale_json["profiles.library_filter_all_schemas"] == "Все схемы"
    assert locale_json["profiles.library_filter_archived"] == "Архивные"
    assert locale_json["profiles.library_validation_invalid"] == "Не пройдена"
    assert locale_json["profiles.library_validation_not_validated"] == "Не проверена"
    assert locale_json["profiles.library_sort_by"] == "Сортировать по"
    assert locale_json["profiles.dock_group_primary"] == "Главные действия"
    assert locale_json["profiles.reload"] == "Обновить список"
    assert locale_json["profiles.import_firefox_policies_json"] == "Импортировать policies.json"
    assert locale_json["profiles.import_firefox_policies_ready"].startswith("Выберите файл")
    assert locale_json["profiles.status_import_firefox_policies_done"] == (
        "Импортирован новый профиль «{name}». Схема: {schema}. Проверка: {validation}."
    )
    assert locale_json["profiles.error_import_firefox_policies"].startswith("Ошибка импорта")
    assert locale_json["profiles.none_selected"] == "Выберите профиль"
    assert locale_json["profiles.list_open"] == "Открыть профиль"
    assert locale_json["profiles.list_selected_hint"] == "Этот профиль сейчас открыт."
    assert locale_json["profiles.compare_title"] == "Сравнение двух профилей"
    assert locale_json["profiles.compare_action"] == "Сравнить здесь"
    assert locale_json["profiles.clone_action"] == "Клонировать и доработать"
    assert locale_json["profiles.clone_handoff_title"] == (
        "Что обычно стоит проверить в производной копии"
    )
    assert locale_json["profiles.clone_handoff_compare"] == "Сравнить сейчас"
    assert locale_json["profiles.compare_summary_policies"] == "Изменённые области политик"
    assert locale_json["profiles.compare_guided_areas_title"] == "Различия по шагам мастера"
    assert locale_json["profiles.wizard_summary_derived"] == "Основан на"
    assert locale_json["profiles.lifecycle_review_title"] == "Жизненный цикл профиля"
    assert locale_json["profiles.selection_empty_status"] == "Выберите профиль или начните новый черновик, чтобы начать."
    assert locale_json["profiles.confirm_hard_delete"].startswith("Удалить этот профиль навсегда")
    assert locale_json["profiles.confirm_reset_library"].startswith("Удалить навсегда все профили")
    assert locale_json["profiles.wizard_search_title"] == "Поисковые настройки"
    assert locale_json["profiles.wizard_general_policy_title"] == "Общее поведение браузера"
    assert locale_json["profiles.wizard_general_policy_preset_managed_title"] == (
        "Управляемое поведение браузера"
    )
    assert locale_json["profiles.wizard_upkeep_governance_title"] == (
        "Сценарий ежедневного управления браузером"
    )
    assert locale_json["profiles.wizard_general_policy_section_state_download_prompt_on"] == (
        "Спрашивать место сохранения загрузок"
    )
    assert locale_json["profiles.wizard_settings_map_label"] == "Разделы настроек Firefox"
    assert locale_json["profiles.wizard_settings_covered_title"] == "Покрытые настройки"
    assert locale_json["profiles.wizard_preferences_covered_title"] == "Покрытие параметров во всех настройках"
    assert locale_json["profiles.wizard_preferences_general_handoff_title"] == (
        "Все настройки для раздела «Основные»"
    )
    assert locale_json["profiles.wizard_preferences_search_handoff_title"] == (
        "Все настройки поиска"
    )
    assert locale_json["profiles.wizard_preferences_handoff_count"] == "Настроено: {count}"
    assert locale_json["profiles.wizard_settings_controls_label"] == "Что можно изменить здесь"
    assert locale_json["profiles.wizard_settings_filter_all"] == "Все"
    assert locale_json["profiles.wizard_settings_search_label"] == "Найти настройку"
    assert locale_json["profiles.wizard_settings_search_clear"] == "Очистить"
    assert locale_json["profiles.sort_updated_at"] == "Обновлено"
    assert locale_json["profiles.sort_schema"] == "Схема"
    assert locale_json["profiles.order_desc"] == "По убыванию"
    assert locale_json["profiles.status_draft_ready"].startswith("Черновик готов")
    assert locale_json["profiles.editor_formatted"] == "Документ отформатирован."
    assert locale_json["profiles.wizard_settings_search_kind_preference_preset"] == (
        "Готовый набор параметра"
    )
    assert locale_json["profiles.wizard_settings_search_kind_preference_bundle"] == (
        "Набор параметров"
    )
    assert locale_json["profiles.wizard_settings_search_kind_known_preference"] == (
        "Известный параметр"
    )
    assert locale_json["profiles.wizard_settings_search_kind_policy_blueprint"] == (
        "Политика схемы"
    )
    assert locale_json["profiles.wizard_section_network_access"] == "Сеть и корпоративный доступ"
    assert locale_json["profiles.wizard_shell_title"] == "Техническое покрытие шага"
    assert locale_json["profiles.wizard_home_surface_open"] == "Открыть"
    assert locale_json["profiles.wizard_step_two_index_title"] == "Карта шага"
    assert locale_json["profiles.wizard_step_two_index_proxy"] == "Прокси"
    assert locale_json["profiles.wizard_browser_defaults_map_title"] == "Карта шага"
    assert locale_json["profiles.wizard_browser_defaults_review_title"] == "Локальная проверка"
    assert locale_json["profiles.wizard_step_four_index_title"] == "Карта шага поиска"
    assert locale_json["profiles.wizard_step_four_index_engines"] == "Управляемые поисковики"
    assert locale_json["profiles.wizard_user_environment_map_title"] == (
        "Карта пользовательского окружения"
    )
    assert locale_json["profiles.wizard_user_environment_map_extensions"] == "Дополнения"
    assert locale_json["profiles.wizard_user_environment_map_websites"] == "Сайты"
    assert locale_json["profiles.wizard_disclosure_show"] == "Показать детали"
    assert locale_json["profiles.wizard_disclosure_hide"] == "Скрыть детали"
    assert locale_json["profiles.wizard_review_filter_changed"] == "Изменённые"
    assert locale_json["profiles.wizard_review_filter_attention"] == "Требуют внимания"
    assert locale_json["profiles.wizard_review_filter_advanced"] == "Вне Пошагового редактора"
    assert locale_json["profiles.wizard_review_filter_all"] == "Все"
    assert locale_json["profiles.wizard_review_empty_changed"] == "Здесь пока нет изменённых пунктов."
    assert locale_json["profiles.wizard_review_empty_advanced"] == (
        "Сейчас здесь нет пунктов вне Пошагового редактора."
    )
    assert locale_json["profiles.wizard_long_list_show_all"] == "Показать все: {count}"
    assert locale_json["profiles.wizard_long_list_show_fewer"] == "Свернуть"
    assert locale_json["profiles.wizard_shell_badge_raw"] == "Через резервный JSON-блок"
    assert locale_json["profiles.wizard_shell_boolean_true"] == "Включено"
    assert locale_json["profiles.wizard_shell_branch_mode_simple"] == "Простое вкл/выкл"
    assert locale_json["profiles.wizard_shell_true_map_hint"] == (
        "По одному имени хоста или источнику на строку."
    )
    assert locale_json["profiles.wizard_shell_array_add"] == "Добавить элемент"
    assert locale_json["profiles.wizard_shell_json_error"] == (
        "Вложенные значения должны быть валидным JSON."
    )
    assert locale_json["profiles.wizard_shell_nested_unsupported"] == (
        "Часть вложенных полей пока остаётся через резервный JSON-блок."
    )
    assert locale_json["profiles.wizard_shell_dictionary_add"] == "Добавить запись"
    assert locale_json["profiles.wizard_shell_dictionary_key_label"] == "Ключ записи"
    assert locale_json["profiles.wizard_schema_policy_applied"] == (
        "Политика, управляемая схемой, обновлена."
    )
    assert locale_json["profiles.wizard_settings_general_updates"] == "Обновления"
    assert locale_json["profiles.wizard_settings_privacy_passwords"] == "Пароли"
    assert locale_json["profiles.wizard_settings_sync_account"] == "Аккаунт Mozilla"
    assert locale_json["profiles.wizard_preferences_general_title"] == (
        "Управляемые параметры для раздела «Основные»"
    )
    assert locale_json["profiles.wizard_preferences_general_focus_startup_title"] == (
        "Запуск и восстановление"
    )
    assert locale_json["profiles.wizard_preferences_bundles_title"] == "Быстрые наборы"
    assert locale_json["profiles.wizard_preferences_bundles_body"].startswith("Применяйте небольшую")
    assert locale_json["profiles.wizard_preferences_known_title"] == (
        "Известные параметры Firefox"
    )
    assert locale_json["profiles.wizard_preferences_known_body"].startswith(
        "Добавляйте известный ключ"
    )
    assert locale_json["profiles.wizard_preferences_gui_label"] == "Разделы настроек Firefox"
    assert locale_json["profiles.wizard_preferences_add_button"] == "Добавить параметр"
    assert locale_json["profiles.wizard_preferences_value_custom"] == "Своё значение: {value}"
    assert locale_json["profiles.wizard_preferences_remove_button"] == "Удалить"
    assert locale_json["profiles.wizard_preferences_field_name"] == "Ключ параметра"
    assert locale_json["profiles.wizard_preferences_field_status"] == "Статус"
    assert locale_json["profiles.wizard_preferences_field_type"] == "Тип значения"
    assert locale_json["profiles.wizard_preferences_field_value"] == "Значение"
    assert locale_json["profiles.wizard_preferences_status_default"] == "по умолчанию"
    assert locale_json["profiles.wizard_preferences_status_locked"] == "заблокировано"
    assert locale_json["profiles.wizard_preferences_status_user"] == "пользовательское"
    assert locale_json["profiles.wizard_preferences_status_clear"] == "очистить"
    assert locale_json["profiles.wizard_preferences_type_auto_option"] == (
        "Определить автоматически"
    )
    assert locale_json["profiles.wizard_preferences_type_boolean"] == "логическое"
    assert locale_json["profiles.wizard_preferences_type_number"] == "число"
    assert locale_json["profiles.wizard_preferences_type_string"] == "строка"
    assert locale_json["profiles.wizard_preferences_meta_target"] == "параметры Firefox"
    assert locale_json["profiles.wizard_preferences_summary_default"].startswith(
        "Укажите ключ параметра"
    )
    assert locale_json["profiles.wizard_preferences_hint_known"] == (
        "Известный параметр с рекомендуемым управляемым значением по умолчанию."
    )
    assert locale_json["profiles.wizard_preferences_hint_clear"] == (
        "Если выбран статус «очистить», управляемое значение будет удалено и отдельное значение не нужно."
    )
    assert locale_json["profiles.wizard_preferences_hint_known_multiple"] == (
        "Известный параметр с несколькими вариантами готовых наборов. Укажите статус и значение явно."
    )
    assert locale_json["profiles.wizard_preferences_error_value"] == (
        "Нужно указать значение параметра, если не выбран статус «очистить»."
    )
    assert locale_json["profiles.wizard_preferences_error_boolean"] == (
        "Для логического значения допустимы только true или false."
    )
    assert locale_json["profiles.wizard_preferences_error_number"] == (
        "Для числового значения нужно указать корректное число."
    )
    assert locale_json["profiles.wizard_preferences_warning_required"].startswith(
        "Нужно указать ключ параметра"
    )
    assert locale_json["profiles.wizard_preferences_preset_applied"] == "Готовый набор параметра добавлен."
    assert locale_json["profiles.wizard_preferences_bundle_applied"] == "Набор параметров добавлен."
    assert locale_json["profiles.wizard_preferences_known_applied"] == "Известный параметр добавлен."
    assert locale_json["profiles.wizard_preferences_bundle_state_applied"] == "Уже применён"
    assert locale_json["profiles.wizard_preferences_bundle_state_partial"] == (
        "Применён частично: {matched}/{total}"
    )
    assert locale_json["profiles.wizard_preferences_bundle_state_conflict"] == (
        "Есть конфликтующие значения: {conflicts}"
    )
    assert locale_json["profiles.wizard_preferences_bundle_state_missing"] == "Пока не применён"
    assert locale_json["profiles.wizard_preferences_known_state_suggested"] == (
        "Используется рекомендуемое значение"
    )
    assert locale_json["profiles.wizard_preferences_known_state_present"] == "Уже добавлен"
    assert locale_json["profiles.wizard_preferences_known_state_overridden"] == (
        "Переопределён вручную"
    )
    assert locale_json["profiles.wizard_preferences_known_state_missing"] == "Пока не добавлен"
    assert locale_json["profiles.wizard_preferences_preset_privacy_https_only_title"] == (
        "Включить режим «Только HTTPS»"
    )
    assert locale_json["profiles.wizard_preferences_preset_sync_passwords_off_title"] == (
        "Не синхронизировать пароли"
    )
    assert locale_json["profiles.wizard_security_map_title"] == "Карта защитного режима"
    assert locale_json["profiles.wizard_privacy_review_title"] == (
        "Краткая сводка защитного режима"
    )
    assert locale_json["profiles.wizard_privacy_review_user_data"] == (
        "Приватность и сохранённые учётные данные"
    )
    assert locale_json["profiles.wizard_privacy_review_cleanup"] == (
        "Очистка при завершении"
    )
    assert locale_json["profiles.wizard_hardening_preset_balanced_title"] == (
        "Сбалансированное усиление защиты"
    )
    assert locale_json["profiles.wizard_hardening_impact_cleanup"] == (
        "Очистка при завершении"
    )
    assert locale_json["profiles.wizard_hardening_subposture_privacy"] == (
        "Изменить режим данных приватности"
    )
    assert locale_json["profiles.wizard_privacy_outcome_telemetry_title"] == (
        "Телеметрия и исследования"
    )
    assert locale_json["profiles.wizard_privacy_outcome_site_data_title"] == (
        "Куки и разрешения"
    )
    assert locale_json["profiles.wizard_hardening_governance_title"] == (
        "Сценарий усиления защиты"
    )
    assert locale_json["profiles.wizard_hardening_governance_next_label"] == (
        "Следующая рекомендация"
    )
    assert locale_json["profiles.wizard_hardening_governance_remaining_count"] == (
        "Осталось: {count}"
    )
    assert locale_json["profiles.wizard_privacy_review_permissions"] == "Разрешения"
    assert locale_json["profiles.wizard_privacy_review_permissions_subcounts"] == (
        "Настроено: {configured} • строгих: {locked}"
    )
    assert locale_json["profiles.wizard_privacy_review_cookies"] == "Поведение куки"
    assert locale_json["profiles.wizard_network_review_title"] == (
        "Как Firefox будет выходить в сеть"
    )
    assert locale_json["profiles.wizard_network_review_windows_sso"] == "Единый вход Windows"
    assert locale_json["profiles.wizard_home_review_title"] == (
        "Что пользователь увидит при запуске"
    )
    assert locale_json["profiles.wizard_home_review_user_messaging"] == (
        "Подсказки и рекомендации"
    )
    assert locale_json["profiles.wizard_search_review_title"] == (
        "Как будет работать поиск"
    )
    assert locale_json["profiles.wizard_search_review_custom"] == (
        "Пользовательские поисковики"
    )
    assert locale_json["profiles.wizard_homepage_section_state_invalid"] == (
        "Для выбранного режима запуска нужен URL домашней страницы."
    )
    assert locale_json["profiles.wizard_firefox_home_section_state_configured"] == (
        "Показать: {show} • Скрыть: {hide}"
    )
    assert locale_json["profiles.wizard_search_defaults_section_state_conflict"] == (
        "Поисковые подсказки выключены, но поверхности Firefox Suggest остаются включены"
    )
    assert locale_json["profiles.wizard_firefox_suggest_section_state_conflict"] == (
        "Для зависимых поверхностей нужны веб-подсказки"
    )
    assert locale_json["profiles.wizard_preferences_bundle_home_focus_title"] == (
        "Минималистичная домашняя страница Firefox"
    )
    assert locale_json["profiles.wizard_preferences_bundle_permissions_title"] == (
        "Ужесточить разрешения сайтов"
    )
    assert locale_json["profiles.wizard_search_add_title"] == (
        "Управляемые пользовательские поисковики"
    )
    assert locale_json["profiles.wizard_search_add_button"] == "Добавить поисковик"
    assert locale_json["profiles.wizard_search_presets_title"] == "Быстрые готовые наборы"
    assert locale_json["profiles.wizard_search_presets_menu_title"] == (
        "Добавить поисковик из готового набора"
    )
    assert locale_json["profiles.wizard_search_defaults_preset_restricted_title"] == (
        "Ограниченный поиск"
    )
    assert locale_json["profiles.wizard_search_preset_applied"] == "Готовый набор поисковика добавлен."
    assert locale_json["profiles.wizard_search_preset_state_applied"] == (
        "Готовый набор совпадает с текущим поисковиком"
    )
    assert locale_json["profiles.wizard_search_preset_state_partial"] == "Готовый набор применён частично"
    assert locale_json["profiles.wizard_search_preset_state_conflict"] == (
        "Готовый набор расходится с текущим поисковиком"
    )
    assert locale_json["profiles.wizard_search_preset_state_missing"] == "Готовый набор пока не добавлен"
    assert locale_json["profiles.wizard_search_engine_summary_default"].startswith(
        "По умолчанию используется GET"
    )
    assert locale_json["profiles.wizard_search_engine_warning_required"].startswith(
        "Для валидного поисковика нужны"
    )
    assert locale_json["profiles.wizard_search_engine_method_default"] == "GET (по умолчанию)"
    assert locale_json["profiles.wizard_search_engine_advanced_title"] == "Расширенные поля"
    assert locale_json["profiles.wizard_firefox_home_title"] == "Карточки домашней страницы Firefox"
    assert locale_json["profiles.wizard_firefox_home_preset_focused_title"] == (
        "Сфокусированная домашняя страница"
    )
    assert locale_json["profiles.wizard_firefox_home_recommendations_title"] == (
        "Истории и рекламный контент"
    )
    assert (
        locale_json["profiles.wizard_home_step_summary_title"]
        == "Итог настройки домашней страницы"
    )
    assert locale_json["profiles.wizard_firefox_suggest_title"] == "Firefox Suggest"
    assert locale_json["profiles.wizard_firefox_suggest_preset_locked_down_title"] == (
        "Подсказки жёстко отключены"
    )
    assert locale_json["profiles.wizard_homepage_preset_locked_title"] == (
        "Зафиксированная домашняя страница"
    )
    assert locale_json["profiles.wizard_home_overrides_preset_managed_title"] == (
        "Управляемый стартовый сценарий"
    )
    assert locale_json["profiles.wizard_proxy_mode_manual"] == "Ручная настройка"
    assert locale_json["profiles.wizard_proxy_preset_system_title"] == "Системный прокси"
    assert locale_json["profiles.wizard_proxy_preset_pac_title"] == "PAC-файл"
    assert locale_json["profiles.wizard_network_enterprise_detail_title"] == (
        "Детали аутентификации и сертификатов"
    )
    assert locale_json["profiles.wizard_language_preset_managed_title"] == (
        "Управляемая языковая база"
    )
    assert locale_json["profiles.wizard_language_ai_handoff_skip"].startswith(
        "Язык и перевод уже покрыты здесь."
    )
    assert locale_json["profiles.wizard_ai_posture_title"] == "Сценарий ИИ"
    assert locale_json["profiles.wizard_ai_posture_disable_title"] == "Отключить ИИ"
    assert locale_json["profiles.wizard_network_enterprise_preset_managed_title"] == (
        "Управляемый корпоративный доступ"
    )
    assert locale_json["profiles.wizard_network_enterprise_section_state_managed_preset"] == (
        "Windows SSO и корневые сертификаты организации включены"
    )
    assert locale_json["profiles.wizard_extension_profile_mode_force"] == (
        "Принудительно установить"
    )
    assert locale_json["profiles.wizard_extension_profile_ublock_title"] == "uBlock Origin"
    assert locale_json["profiles.wizard_extension_profile_state_missing"] == "Явного правила нет"
    assert locale_json["profiles.wizard_extension_profile_state_catalog_url"] == (
        "Используется ссылка на загрузку из магазина"
    )
    assert locale_json["profiles.wizard_extension_profile_state_configured"] == "Настроено"
    assert locale_json["profiles.wizard_extension_profile_state_custom_url"] == (
        "Своя ссылка на загрузку"
    )
    assert locale_json["profiles.wizard_extensions_review_title"] == (
        "Как будут управляться дополнения"
    )
    assert locale_json["profiles.wizard_sync_focus_managed_title"] == (
        "Доступ и подсказки"
    )
    assert locale_json["profiles.wizard_extensions_preset_managed_title"] == (
        "Управляемая раскатка"
    )
    assert locale_json["profiles.wizard_extensions_governance_selector_hint"].startswith(
        "Выберите модель управления"
    )
    assert locale_json["profiles.wizard_extensions_governance_managed_title"] == (
        "Управляемый список разрешённых источников"
    )
    assert locale_json["profiles.wizard_extensions_governance_curated_title"] == (
        "Курируемая раскатка"
    )
    assert locale_json["profiles.wizard_extensions_governance_title"] == (
        "Сценарий управления дополнениями"
    )
    assert locale_json["profiles.wizard_profile_identity_title"] == (
        "Идентификация профиля"
    )
    assert locale_json["profiles.wizard_profile_identity_body"].startswith(
        "Задайте имя профиля и выберите канал схемы Firefox"
    )
    assert locale_json["profiles.wizard_extensions_review_body"].startswith(
        "Быстрая проверка"
    )
    assert locale_json["profiles.wizard_extensions_review_curated"] == (
        "Известные дополнения"
    )
    assert locale_json["profiles.wizard_extensions_review_arbitrary"] == (
        "Дополнительные правила дополнений"
    )
    assert locale_json["profiles.wizard_extensions_review_custom_urls"] == (
        "Свои источники установки"
    )
    assert locale_json["profiles.wizard_extensions_review_open"] == "Открыть"
    assert locale_json["profiles.wizard_website_handlers_preset_protocols_title"] == (
        "Ссылки протоколов"
    )
    assert locale_json["profiles.wizard_extension_rule_show"] == "Показать список"
    assert locale_json["profiles.wizard_extensions_rule_count"] == "Записей: {count}"
    assert locale_json["profiles.wizard_export_compatibility_title"] == "Техническое покрытие"
    assert locale_json["profiles.wizard_shared_device_workflow_title"] == "Сценарий общего устройства"
    assert locale_json["profiles.wizard_export_section_ready_title"] == "Финальный чеклист"
    assert locale_json["profiles.wizard_export_section_changes_title"] == "Проверка перед передачей"
    assert locale_json["profiles.wizard_export_section_technical_title"] == (
        "Технические детали"
    )
    assert locale_json["profiles.wizard_export_title"] == "Сохранить, проверить, скачать"
    assert locale_json["profiles.wizard_export_workspace_state"] == "Последние правки"
    assert locale_json["profiles.wizard_export_validation_state"] == "Финальная проверка"
    assert locale_json["profiles.wizard_export_ready_state"] == "Готово к скачиванию"
    assert locale_json["profiles.wizard_export_ready_title"] == "Скачать policies.json"
    assert locale_json["profiles.wizard_export_guided_summary_title"] == "Проверка по областям"
    assert locale_json["profiles.wizard_export_guided_ai"] == "ИИ и умные функции"
    assert locale_json["profiles.wizard_cleanup_preset_shared_title"] == (
        "Очистка для общих устройств"
    )
    assert locale_json["profiles.wizard_homepage_shared_preset_portal_title"] == (
        "Зафиксированный портал общего устройства"
    )
    assert locale_json["profiles.wizard_website_filter_shared_preset_allow_only_title"] == (
        "Только управляемые сайты"
    )
    assert locale_json["profiles.wizard_website_access_decision_title"] == (
        "Доступ к сайтам"
    )
    assert locale_json["profiles.wizard_website_access_posture_label"] == (
        "Сценарий доступа к сайтам"
    )
    assert locale_json["profiles.wizard_website_access_handlers_label"] == (
        "Управление обработчиками"
    )
    assert locale_json["profiles.wizard_export_next_steps_title"] == "Перед скачиванием"
    assert locale_json["profiles.wizard_export_ready_now_title"] == "Уже готово"
    assert locale_json["profiles.wizard_cis_final_summary_title"] == "Финальная сводка CIS"
    assert locale_json["profiles.wizard_cis_final_summary_manual"] == "Ручная проверка"
    assert locale_json["profiles.wizard_export_included_title"] == (
        "Что войдёт в скачиваемый policies.json"
    )
    assert locale_json["profiles.wizard_export_missing_title"] == (
        "Что пока не попадёт в скачанный policies.json"
    )
    assert locale_json["profiles.wizard_export_review_title"] == (
        "Что ещё стоит проверить перед передачей"
    )
    assert locale_json["profiles.wizard_export_baseline_summary_title"] == "Базовые ограничения"
    assert locale_json["profiles.wizard_export_shareable_title"] == "Выжимка для передачи"
    assert locale_json["profiles.wizard_export_shareable_generate"] == (
        "Сформировать/скопировать выжимку"
    )
    assert locale_json["profiles.wizard_export_shareable_copy"] == "Скопировать выжимку"
    assert locale_json["profiles.wizard_export_guided_privacy_shutdown_cleanup"] == (
        "Очистка при завершении включена"
    )
    assert locale_json["profiles.wizard_export_download_hint_ready"] == (
        "Скачивание policies.json уже использует последнюю сохранённую версию."
    )
    assert locale_json["profiles.dock_state_kicker"] == "Текущий этап"
    assert locale_json["profiles.dock_state_dirty_title"] == "Сохраните последние правки"
    assert locale_json["profiles.dock_state_archived_title"] == (
        "Восстановите архивный профиль"
    )
    assert locale_json["profiles.wizard_export_profile_saved"] == "Сохранённый профиль #{id}"
    assert locale_json["profiles.wizard_export_state_unsaved_existing"] == (
        "Сначала сохраните последние правки перед скачиванием."
    )
    assert locale_json["profiles.wizard_export_unknown_count"] == (
        "Неизвестные ключи верхнего уровня"
    )
    assert locale_json["profiles.wizard_export_check_ready"] == "Готово к скачиванию"
    assert locale_json["profiles.wizard_export_check_unsaved"] == "Есть несохранённые правки"
    assert locale_json["profiles.wizard_bookmarks_review_title"] == (
        "Как настроены управляемые закладки"
    )
    assert locale_json["profiles.wizard_bookmarks_review_nested"] == (
        "Вложенные деревья закладок"
    )
    assert locale_json["profiles.wizard_bookmarks_review_open"] == "Открыть"
    assert locale_json["profiles.wizard_bookmarks_handoff_title"] == "Редактор закладок"
    assert locale_json["profiles.wizard_bookmarks_open_action"] == (
        "Открыть Все настройки"
    )
    assert locale_json["profiles.wizard_bookmarks_row_state_toolbar"] == "Закладка на панели"
    assert locale_json["profiles.wizard_managed_bookmarks_row_state_invalid"] == (
        "JSON во вложенных элементах требует внимания"
    )
    assert locale_json["profiles.wizard_website_access_review_title"] == (
        "Как будут вести себя сайты и ссылки"
    )
    assert locale_json["profiles.wizard_website_access_review_handlers"] == (
        "Обработчики файлов и ссылок"
    )
    assert locale_json["profiles.wizard_website_governance_title"] == "Сценарий доступа к сайтам"
    assert locale_json["profiles.wizard_home_surfaces_workflow_title"] == (
        "Сценарий старта и стартовых поверхностей"
    )
    assert locale_json["profiles.wizard_language_governance_title"] == (
        "Сценарий управления языком"
    )
    assert locale_json["profiles.wizard_ai_controls_title"] == "Политики ИИ Firefox 151"
    assert locale_json["profiles.wizard_search_surfaces_workflow_title"] == (
        "Сценарий поискового опыта"
    )
    assert locale_json["profiles.wizard_website_filter_preset_mixed_title"] == (
        "Блокировки и исключения"
    )
    assert locale_json["profiles.wizard_website_filter_state_configured"] == (
        "Блокировок: {blocked} • Исключений: {exceptions}"
    )
    assert locale_json["profiles.wizard_authentication_state_configured"] == (
        "Элементов управления: {controls} • Правил хостов: {rules}"
    )
    assert locale_json["profiles.wizard_trust_auth_workflow_title"] == (
        "Сценарий корпоративного доверия и входа"
    )
    assert locale_json["profiles.wizard_step_memory_title"] == (
        "Недавно изменено"
    )
    assert locale_json["profiles.wizard_step_memory_open"] == "Открыть шаг"
    assert locale_json["profiles.wizard_step_memory_current"] == "Вы уже здесь"
    assert locale_json["profiles.wizard_export_boundary_register_title"] == (
        "Что сознательно остаётся во Всех настройках"
    )
    assert locale_json["profiles.wizard_export_drilldown_title"] == (
        "Детальный технический разбор"
    )
    assert locale_json["profiles.wizard_certificates_state_with_roots"] == (
        "Установлено: {count} • Включены корпоративные корневые сертификаты"
    )
    assert locale_json["profiles.wizard_doh_state_provider"] == "Свой поставщик"
    assert locale_json["profiles.wizard_ai_generative_controls_title"] == "Настройки генеративного ИИ"
    assert locale_json["profiles.wizard_permissions_state_strict"] == (
        "Настроено: {configured} • Строгих: {strict}"
    )
    assert locale_json["profiles.wizard_permissions_nested_default"] == "По умолчанию: {value}"
    assert locale_json["profiles.wizard_cookies_state_strict"] == (
        "Правил куки: {count} • Ограничено"
    )
    assert locale_json["profiles.wizard_handlers_state_configured"] == (
        "Связок: {total} • MIME: {mime} • Схемы: {schemes} • Расширения: {extensions}"
    )
    assert locale_json["profiles.wizard_handlers_nested_array_configured"] == (
        "Вспомогательных приложений: {count}"
    )
    assert locale_json["profiles.wizard_user_messaging_state_configured"] == (
        "Включено: {enabled} • Скрыто: {disabled}"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_missing"] == (
        "Управляемые поля пока не заданы"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_catalog_url"] == (
        "Используется ссылка на загрузку из магазина"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_custom_url"] == (
        "Своя ссылка на загрузку"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_install_url"] == (
        "Правило со ссылкой на загрузку"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_mode_only"] == (
        "Только режим установки"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_flags_only"] == (
        "Только поведенческие флаги"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_configured"] == (
        "Правило настроено"
    )
    assert locale_json["profiles.wizard_extensions_mode_blocked"] == "Запретить установку"
    assert locale_json["profiles.wizard_extensions_advanced_title"] == (
        "Расширенные правила для расширений"
    )
    assert locale_json["profiles.wizard_extensions_advanced_install_permissions"] == (
        "Исключения источников установки"
    )
    assert locale_json["profiles.wizard_extensions_advanced_arbitrary_rules"] == (
        "Произвольные ExtensionSettings"
    )
    assert locale_json["profiles.wizard_extensions_advanced_count"] == "Настроено: {count}"


def test_profiles_page_renders_editor_shell():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'data-profiles-route-mode="new"' in response.text
    assert 'data-profiles-template-kind="editor"' in response.text
    assert_contains_all(
        response.text,
        (
            "Browser Policy Manager",
            "Guided editor",
            "All settings",
            "JSON editor",
            'id="overview-panel"',
            'id="wizard-panel"',
            'id="profile-name"',
            'id="profile-type"',
            'id="save"',
            'id="validate"',
        ),
    )
    assert 'id="download-json"' not in response.text
    assert 'id="download-yaml"' not in response.text
    assert 'id="wizard-export-json"' not in response.text
    assert 'id="wizard-export-yaml"' not in response.text


def test_firefox_policies_import_and_final_export_ui_contract():
    client = make_test_client(app)
    library_response = client.get("/profiles")
    editor_response = _profiles_page_response()

    assert library_response.status_code == 200
    assert editor_response.status_code == 200
    assert 'id="import-firefox-policies"' in library_response.text
    assert 'id="import-firefox-policies-file"' in library_response.text
    assert 'accept=".json,application/json"' in library_response.text
    assert 'id="wizard-export-firefox-policies"' in editor_response.text

    removed_export_controls = (
        'id="download-json"',
        'id="download-yaml"',
        'id="wizard-export-json"',
        'id="wizard-export-yaml"',
        "Download JSON",
        "Download YAML",
        "Download files",
        "Скачать файлы",
    )
    for token in removed_export_controls:
        assert token not in library_response.text
        assert token not in editor_response.text

    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()
    assert en_catalog["profiles.wizard_export_ready_title"] == "Download policies.json"
    assert en_catalog["profiles.wizard_export_ready_saved"] == (
        "This saved version is ready for Firefox policies.json download."
    )
    assert ru_catalog["profiles.wizard_export_ready_title"] == "Скачать policies.json"
    assert ru_catalog["profiles.wizard_export_ready_saved"] == (
        "Эта сохранённая версия готова к скачиванию Firefox policies.json."
    )


def test_ai_wizard_presets_update_managed_policy_values():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_extensions.js"
    ).read_text(encoding="utf-8")

    assert "function applyAiPosturePreset(presetKey)" in source
    assert "function isAiWizardAvailable()" in source
    assert "function hasUsableAiPolicyCard(policyCardEl)" in source
    assert 'setText(wizardAiSectionStatusEl, t("profiles.wizard_ai_esr_state"))' in source
    assert 'normalized.AIControls = buildAiControlsValue(presetKey);' in source
    assert 'Value: "blocked"' in source
    assert 'Value: "available"' in source
    assert "SidebarChatbot" in source
    assert "SmartWindow" in source
    assert "normalized.VisualSearchEnabled = false" in source
    assert "profiles.wizard_ai_controls_active" in source
    assert "applyAiPosturePreset(presetKey);" in source


def test_ai_wizard_exposes_current_firefox_150_controls_in_standard_step():
    template = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "templates"
        / "profiles"
        / "_page_wizard_step_ai.html"
    ).read_text(encoding="utf-8")

    assert 'id="wizard-ai-release-content" hidden' in template
    assert 'id="wizard-ai-policy-controls"' in template
    assert 'id="wizard-ai-esr-empty-state"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_title"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_body"' in template
    assert 'id="wizard-ai-map-title"' in template
    assert 'href="#wizard-step-5-posture"' in template
    assert 'href="#wizard-step-5-availability"' in template
    assert 'href="#wizard-step-5-surfaces"' in template
    assert 'id="wizard-ai-posture-presets"' in template
    assert 'id="wizard-ai-controls-card"' in template
    assert 'data-settings-target="policy:AIControls"' in template
    assert 'id="wizard-generative-ai-card"' in template
    assert 'data-settings-target="policy:GenerativeAI"' in template
    assert 'id="wizard-visual-search-enabled-card"' in template
    assert 'data-settings-target="policy:VisualSearchEnabled"' in template
    assert 'data-ai-outcome-group="feature-controls"' in template
    assert 'data-ai-outcome-group="generative-controls"' in template
    assert 'data-ai-outcome-group="surface-controls"' in template
    assert 'data-ai-posture-preset="providers"' not in template
    assert 'id="wizard-ai-fine-tuning-panel"' not in template


def test_final_step_renders_compact_cis_summary_without_full_decision_list():
    root = Path(__file__).resolve().parents[1]
    template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")
    source = (root / "app" / "static" / "profiles_review.js").read_text(
        encoding="utf-8"
    )

    assert 'id="wizard-cis-final-summary"' in template
    assert "function renderCisFinalSummary(complianceInfo)" in source
    assert '["added_from_cis", "cis_replaced_base"]' in source
    assert '"already_satisfied"' in source
    assert '["kept_base_stricter", "kept_base_only"]' in source
    assert '"review_required"' in source
    assert "renderCisExceptionNotes(manualCisDecisions);" in source
    assert "renderCisExceptionNotes(complianceDecisions);" not in source


def test_profiles_page_renders_review_sections():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_REVIEW_TOKENS)


def test_profiles_page_renders_schema_export_footer_and_headers():
    current_year = datetime.now(UTC).year
    footer_year_range = "2025" if current_year <= 2025 else f"2025-{current_year}"

    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_SCHEMA_EXPORT_TOKENS)
    assert_contains_all(response.text, PROFILES_PAGE_FOOTER_TOKENS)
    assert footer_year_range in response.text
    assert 'data-i18n="profiles.footer_label"' not in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "Content-Security-Policy" in response.headers


def test_default_wizard_path_does_not_render_guided_coverage_blocks():
    root = Path(__file__).resolve().parents[1]
    macro_source = (
        root / "app" / "templates" / "profiles" / "_wizard_macros.html"
    ).read_text(encoding="utf-8")
    shell_source = (
        root / "app" / "static" / "profiles_schema_shell_sections.js"
    ).read_text(encoding="utf-8")
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    response = _profiles_page_response()

    assert response.status_code == 200
    assert 'id="wizard-guided-coverage-step-' not in response.text
    assert 'data-guided-coverage-open-step="' not in response.text
    assert 'class="wizard-guided-coverage surface-soft-box"' not in macro_source
    assert "renderWizardGuidedCoverage(" not in shell_source
    assert "data-guided-coverage-open-step" not in runtime_source
    assert "wizard-guided-coverage-step" not in dom_source
    assert ".wizard-guided-coverage" not in css_source
    assert 'id="wizard-schema-shell-step-2"' not in response.text
    assert 'id="wizard-schema-shell-step-8"' in response.text


def test_default_wizard_path_does_not_render_settings_map_blocks():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    macro_source = (
        root / "app" / "templates" / "profiles" / "_wizard_macros.html"
    ).read_text(encoding="utf-8")
    template_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "app" / "templates" / "profiles").glob("_page_wizard_step_*.html"))
    )
    settings_search_source = (
        root / "app" / "static" / "profiles_settings_search.js"
    ).read_text(encoding="utf-8")

    assert response.status_code == 200
    assert 'id="wizard-settings-search-input"' in response.text
    assert 'id="wizard-settings-search-results"' in response.text
    assert 'id="wizard-settings-catalog"' in response.text
    assert 'data-settings-target="policy:DisableTelemetry"' in response.text
    assert 'data-settings-target="field:wizard-proxy-mode"' in response.text
    assert 'data-settings-target="search-engine-preset:duckduckgo"' in response.text

    removed_tokens = (
        'id="wizard-settings-map-',
        'id="wizard-settings-controls-',
        'id="wizard-preferences-general-groups"',
        'id="wizard-preferences-home-groups"',
        'id="wizard-preferences-search-groups"',
        'id="wizard-preferences-privacy-groups"',
        'id="wizard-preferences-sync-groups"',
        'id="wizard-preferences-general-controls"',
        'id="wizard-preferences-home-controls"',
        'id="wizard-preferences-search-controls"',
        'id="wizard-preferences-privacy-controls"',
        'id="wizard-preferences-sync-controls"',
        'data-settings-nav',
        'data-settings-jump-target',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_settings_reference" not in macro_source
    assert "render_settings_reference(" not in template_sources
    assert "function renderResults()" in settings_search_source
    assert "function findTarget(targetKey)" in settings_search_source
    assert "button.dataset.settingsSearchTarget = entry.target;" in settings_search_source
    assert 'documentRef.querySelector(`[data-settings-target="${normalizedTarget}"]`)' in settings_search_source
    assert 'documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`)' in settings_search_source


def test_setup_step_defaults_to_corporate_baseline_and_active_preset_states():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    setup_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_setup.html"
    ).read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    assert 'data-i18n="profiles.wizard_profile_identity_title"' in response.text
    assert 'id="wizard-name"' in response.text
    assert 'id="wizard-schema"' in response.text
    assert 'data-scenario-key="corporate_default" aria-pressed="true"' in response.text
    assert 'data-scenario-key="targeted_edits" aria-pressed="false"' in response.text
    assert 'data-starter-key="basic_corporate" aria-pressed="true"' in response.text
    assert 'data-starter-key="blank" aria-pressed="false"' in response.text
    assert 'data-cis-layer-key="cis_l2" aria-pressed="false"' in response.text
    assert 'id="wizard-baseline-override-panel" hidden' in response.text

    assert 'id="wizard-scenario-summary-copy"' in response.text
    assert 'id="wizard-scenario-summary-list"' in response.text
    assert 'id="wizard-baseline-summary-copy"' in response.text
    assert 'id="wizard-baseline-summary-list"' in response.text
    assert 'class="wizard-impact-panel' not in response.text
    assert 'id="wizard-shared-device-workflow-copy"' not in response.text
    assert 'id="wizard-baseline-preview-copy"' not in response.text

    assert 'let wizardScenario = "corporate_default";' in flow_source
    assert 'let wizardStarter = "basic_corporate";' in flow_source
    assert 'button.classList.toggle("wizard-starter-card--active", isActive);' in flow_source
    assert 'button.setAttribute("aria-pressed", isActive ? "true" : "false");' in flow_source
    assert 'box-shadow:\n                inset 4px 0 0 rgba(15, 118, 110, 0.82)' in css_source

    identity_index = setup_template.index("profiles.wizard_profile_identity_title")
    scenario_summary_index = setup_template.index('"wizard-scenario-summary-copy"')
    baseline_summary_index = setup_template.index('"wizard-baseline-summary-copy"')
    baseline_override_index = setup_template.index('"wizard-baseline-override-panel"')
    secondary_index = setup_template.index('wizard-starter-grid--secondary')
    cis_index = setup_template.index('data-cis-layer-key="cis_l2"')
    assert identity_index < scenario_summary_index < baseline_summary_index < baseline_override_index < secondary_index < cis_index


def test_step_two_default_path_is_actionable_network_basics():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    general_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_general.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-step-2-basics"',
        'id="wizard-general-policy-presets"',
        'data-general-policy-preset="updates"',
        'data-general-policy-preset="downloads"',
        'id="wizard-proxy-presets"',
        'data-proxy-preset="system"',
        'data-proxy-preset="autoConfig"',
        'data-settings-target="field:wizard-proxy-mode"',
        'id="wizard-network-enterprise-presets"',
        'data-network-enterprise-preset="sso"',
        'data-network-enterprise-preset="roots"',
        'id="wizard-dns-over-https-card"',
        'id="wizard-windows-sso-card"',
        'id="wizard-authentication-card"',
        'id="wizard-certificates-card"',
        'id="wizard-network-summary-authentication"',
        'id="wizard-network-summary-certificates"',
    )
    for token in core_tokens:
        assert token in response.text

    added_tokens = (
        'id="wizard-browser-defaults-map-title"',
        'href="#wizard-step-2-basics"',
        'href="#wizard-home-surface-startup"',
        'href="#wizard-step-2-default-search"',
        'href="#wizard-step-2-review"',
        'id="wizard-home-summary-homepage"',
        'id="wizard-search-summary-defaults"',
    )
    for token in added_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-2"',
        'id="wizard-upkeep-governance-copy"',
        'id="wizard-trust-auth-workflow-copy"',
        'id="wizard-step-2-advanced-preferences"',
        'id="wizard-preferences-general-handoff-panel"',
        'data-general-preferences-focus="downloads"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(2)" not in general_template
    assert "wizardUpkeepGovernance" not in dom_source
    assert "wizardTrustAuthWorkflow" not in dom_source
    assert "renderUpkeepGovernanceWorkflow" not in network_source
    assert "renderTrustAuthWorkflow" not in network_source
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_two_contains_actionable_home_and_startup_sections():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    home_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_home.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-home-surface-startup"',
        'id="wizard-homepage-presets"',
        'data-homepage-preset="portal"',
        'data-homepage-shared-preset="portal_locked"',
        'id="wizard-homepage-url"',
        'id="wizard-homepage-start-page"',
        'id="wizard-home-surface-new-tab"',
        'id="wizard-home-overrides-presets"',
        'id="wizard-new-tab-page"',
        'id="wizard-override-first-run"',
        'id="wizard-home-surface-firefox-home"',
        'id="wizard-firefox-home-presets"',
        'data-firefox-home-key="Search"',
        'data-firefox-home-key="TopSites"',
        'id="wizard-firefox-home-fine-tuning-toggle"',
        'id="wizard-firefox-home-fine-tuning-panel"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-3"',
        'class="wizard-home-step-summary"',
        'id="wizard-home-surfaces-workflow-copy"',
        'id="wizard-home-summary-user-messaging"',
        'id="wizard-preferences-home-add"',
        'id="wizard-preferences-home-bundles"',
        'id="wizard-preferences-home-known"',
        'data-settings-target="pref-section:home"',
        'data-preference-section="home"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(3)" not in home_template
    assert "wizardHomeSurfacesWorkflow" not in dom_source
    assert "renderHomeSurfacesWorkflow" not in network_source
    assert 'renderPresetButtonState(homepagePresetButtons, resolveHomepagePreset(parsed), "homepagePreset");' in network_source
    assert 'renderPresetButtonState(homeOverridesPresetButtons, resolveHomeOverridesPreset(parsed), "homeOverridesPreset");' in network_source
    assert 'renderPresetButtonState(firefoxHomePresetButtons, resolveFirefoxHomePreset(parsed), "firefoxHomePreset");' in network_source


def test_step_two_contains_actionable_search_and_navigation_sections():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    search_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_search.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-step-2-default-search"',
        'id="wizard-search-defaults-presets"',
        'data-search-defaults-preset="managed_default"',
        'id="wizard-search-default-engine"',
        'id="wizard-search-defaults-section-status"',
        'id="wizard-step-2-managed-engines"',
        'id="wizard-search-engine-add"',
        'id="wizard-search-engine-list"',
        'data-search-engine-preset="duckduckgo"',
        'data-search-engine-field="Name"',
        'data-search-engine-field="URLTemplate"',
        'data-search-engine-field="Alias"',
        'data-search-engine-advanced',
        'data-search-engine-field="Method"',
        'data-search-engine-field="PostData"',
        'id="wizard-step-2-suggestions"',
        'id="wizard-firefox-suggest-presets"',
        'data-firefox-suggest-preset="private"',
        'data-firefox-suggest-key="WebSuggestions"',
        'id="wizard-firefox-suggest-section-status"',
        'id="wizard-search-suggest-fine-tuning-toggle"',
        'id="wizard-search-suggest-fine-tuning-panel"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-4"',
        'href="#wizard-step-4-default-search"',
        'id="wizard-step-4-review"',
        'id="wizard-search-surfaces-workflow-copy"',
        'id="wizard-step-4-advanced-preferences"',
        'id="wizard-preferences-search-handoff-panel"',
        'id="wizard-preferences-search-add"',
        'id="wizard-preferences-search-bundles"',
        'id="wizard-preferences-search-known"',
        'data-settings-target="pref-section:search"',
        'data-preference-section="search"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(4)" not in search_template
    assert "wizardSearchSurfacesWorkflow" not in dom_source
    assert "renderSearchSurfacesWorkflow" not in network_source
    assert 'renderPresetButtonState(searchDefaultsPresetButtons, resolveSearchDefaultsPreset(parsed), "searchDefaultsPreset");' in network_source
    assert 'renderPresetButtonState(firefoxSuggestPresetButtons, resolveFirefoxSuggestPreset(parsed), "firefoxSuggestPreset");' in network_source
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_three_default_path_is_actionable_privacy_and_protection():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    privacy_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_privacy.html"
    ).read_text(encoding="utf-8")
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-hardening-presets"',
        'id="wizard-security-map-title"',
        'href="#wizard-step-3-posture"',
        'href="#wizard-step-3-cleanup"',
        'href="#wizard-step-3-site-data"',
        'href="#wizard-step-3-vpn"',
        'href="#wizard-step-3-review"',
        'data-hardening-preset="balanced"',
        'data-hardening-preset="strict"',
        'id="wizard-hardening-section-status"',
        'id="wizard-privacy-user-data-section-status"',
        'id="wizard-lockdown-section-status"',
        'data-hardening-cleanup-subchoice',
        'id="wizard-cleanup-presets"',
        'data-cleanup-preset="shared"',
        'data-cleanup-preset="strict"',
        'id="wizard-cleanup-section-status"',
        'id="wizard-privacy-site-section-status"',
        'id="wizard-site-data-presets"',
        'data-site-data-preset="balanced"',
        'data-site-data-preset="strict"',
        'id="wizard-site-data-fine-tuning-toggle"',
        'id="wizard-site-data-fine-tuning-panel"',
        'id="wizard-permissions-card"',
        'id="wizard-cookies-card"',
        'id="wizard-privacy-vpn-section-status"',
        'id="wizard-ip-protection-available-card"',
        'data-privacy-outcome-group="cookies-permissions"',
        'id="wizard-privacy-summary-user-data"',
        'id="wizard-privacy-summary-cleanup"',
        'id="wizard-privacy-summary-permissions"',
        'id="wizard-privacy-summary-cookies"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-schema-shell-step-5"',
        'data-hardening-impact-summary',
        'id="wizard-hardening-governance-workflow"',
        'id="wizard-hardening-governance-list"',
        'id="wizard-hardening-next-posture"',
        'data-hardening-subposture-menu="privacy"',
        'data-hardening-subposture-menu="lockdown"',
        'data-hardening-subposture-menu="site-data"',
        'id="wizard-privacy-user-data-presets"',
        'id="wizard-privacy-fine-tuning-panel"',
        'id="wizard-lockdown-presets"',
        'id="wizard-lockdown-fine-tuning-panel"',
        'data-privacy-outcome-group="telemetry"',
        'data-privacy-outcome-group="passwords-private-browsing"',
        'data-privacy-outcome-group="lockdown"',
        'id="wizard-preferences-privacy-add"',
        'id="wizard-preferences-privacy-bundles"',
        'id="wizard-preferences-privacy-known"',
        'data-settings-target="pref-section:privacy"',
        'data-preference-section="privacy"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(5)" not in privacy_template
    assert "render_outcome_policy_group" not in privacy_template
    assert "renderHardeningGovernanceWorkflow" not in flow_source
    assert "openHardeningGovernanceAdvanced" not in flow_source
    assert "wizard-hardening-next-posture" not in runtime_source
    assert "wizard-search-engine-preset--applied" in css_source


def test_step_four_default_path_is_compact_accounts_extensions_and_sites():
    root = Path(__file__).resolve().parents[1]
    response = _profiles_page_response()
    sync_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_sync.html"
    ).read_text(encoding="utf-8")
    extensions_source = (
        root / "app" / "static" / "profiles_extensions.js"
    ).read_text(encoding="utf-8")

    assert response.status_code == 200
    core_tokens = (
        'id="wizard-user-environment-map-title"',
        'href="#wizard-step-4-accounts"',
        'href="#wizard-step-4-language"',
        'href="#wizard-step-4-extensions"',
        'href="#wizard-step-4-bookmarks"',
        'href="#wizard-step-4-websites"',
        'id="wizard-step-4-accounts"',
        'id="wizard-sync-focus-presets"',
        'data-sync-focus-preset="accounts"',
        'id="wizard-sync-section-status"',
        'id="wizard-sync-fine-tuning-toggle"',
        'id="wizard-user-messaging-card"',
        'id="wizard-step-4-language"',
        'id="wizard-language-presets"',
        'data-language-preset="translation_off"',
        'id="wizard-requested-locales-card"',
        'id="wizard-translate-enabled-card"',
        'id="wizard-language-section-status"',
        'id="wizard-language-ai-handoff"',
        'id="wizard-step-4-extensions"',
        'id="wizard-extension-governance-presets"',
        'data-extension-governance-preset="managed"',
        'id="wizard-extension-default-mode"',
        'id="wizard-extension-section-status"',
        'id="wizard-extension-fine-tuning-toggle"',
        'id="wizard-extension-curated-section"',
        'id="wizard-step-4-bookmarks"',
        'data-bookmarks-handoff',
        'id="wizard-bookmarks-open-advanced"',
        'id="wizard-bookmarks-section-status"',
        'id="wizard-step-4-websites"',
        'id="wizard-website-access-decision"',
        'id="wizard-website-access-posture"',
        'data-website-access-posture="allow_only"',
        'id="wizard-website-access-handlers"',
        'id="wizard-website-filter-card"',
        'id="wizard-website-fine-tuning-toggle"',
        'id="wizard-handlers-card"',
    )
    for token in core_tokens:
        assert token in response.text

    removed_tokens = (
        'id="wizard-language-governance-copy"',
        'id="wizard-language-governance-list"',
        'id="wizard-extension-governance-workflow"',
        'id="wizard-extension-governance-copy"',
        'id="wizard-extension-governance-list"',
        'id="wizard-extension-governance-open-advanced"',
        'id="wizard-extension-summary-curated"',
        'id="wizard-bookmark-summary-links"',
        'id="wizard-website-access-summary-blocked"',
        'id="wizard-website-governance-workflow"',
        'id="wizard-website-governance-copy"',
        'id="wizard-website-governance-list"',
        'id="wizard-website-governance-open-advanced"',
        'id="wizard-website-next-filter"',
        'id="wizard-website-next-handlers"',
    )
    for token in removed_tokens:
        assert token not in response.text

    assert "render_wizard_schema_shell(6)" not in sync_template
    assert "renderLanguageGovernanceWorkflow" not in extensions_source
    assert "renderExtensionGovernanceWorkflow" not in extensions_source
    assert "renderWebsiteGovernanceWorkflow" not in extensions_source
    assert "openWebsiteGovernanceAdvanced" not in extensions_source
    assert "openExtensionGovernanceAdvanced" not in extensions_source


def test_profiles_page_preserves_final_guided_ux_contract():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert_contains_all(response.text, PROFILES_PAGE_GUIDED_UX_REGRESSION_TOKENS)


def test_profiles_page_uses_local_js_yaml_asset():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<script src="/static/vendor/js-yaml.js?v=' in response.text
    assert "https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js" not in response.text


def test_profiles_page_uses_local_monaco_assets():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' in response.text
    assert '<script src="/static/vendor/monaco/vs/loader.js"></script>' not in response.text
    assert "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs" not in response.text


def test_profiles_page_uses_local_tailwind_stylesheet():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<link rel="stylesheet" href="/static/vendor/profiles_tailwind.css?v=' in response.text
    assert "https://cdn.tailwindcss.com" not in response.text
    assert "tailwind.config =" not in response.text


def test_profiles_page_uses_local_bootstrap_assets_without_inline_scripts():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert '<script src="/static/profiles_page_bootstrap.js?v=' in response.text
    assert '<script id="profiles-initial-locale" type="application/json">' in response.text
    assert "<script>" not in response.text
    assert "window.__BPM_INITIAL_LANG__ =" not in response.text
    assert "window.__BPM_INITIAL_LOCALE__ =" not in response.text


def test_existing_profile_routes_embed_initial_profile_payload():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(
            name="Initial Profile Embed Contract",
            schema_version="release-151",
            flags={"DisableTelemetry": True},
        ),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")

    assert response.status_code == 200
    assert '<script id="profiles-initial-profile" type="application/json">' in response.text
    assert '"name": "Initial Profile Embed Contract"' in response.text
    assert '"schema_version": "release-151"' in response.text
    assert '"DisableTelemetry": true' in response.text

    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find(id="current-name").get_text(strip=True) == "Initial Profile Embed Contract"
    assert soup.find(id="save").get_text(strip=True) == "Save"
    assert soup.find(id="profile-name").get("value") == "Initial Profile Embed Contract"
    assert soup.find(id="editor-profile-id").get_text(strip=True).startswith("#")


def test_profiles_library_page_uses_library_only_assets():
    client = make_test_client(app)

    response = client.get("/profiles")

    assert response.status_code == 200
    assert '<script src="/static/profiles_head_bootstrap.js?v=' in response.text
    assert '<script src="/static/profiles_utils.js?v=' in response.text
    assert '<script src="/static/profiles_shared.js?v=' in response.text
    assert '<script src="/static/profiles_platform.js?v=' in response.text
    assert '<script src="/static/profiles_data.js?v=' in response.text
    assert '<script src="/static/profiles_library_bootstrap.js?v=' in response.text
    assert '<script src="/static/profiles_library.js?v=' in response.text
    assert 'id="schema-channels-catalog"' in response.text
    assert '<script src="/static/vendor/js-yaml.js?v=' not in response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in response.text
    assert '<script src="/static/profiles_catalogs.js?v=' not in response.text
    assert '<script src="/static/profiles_page_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_runtime.js?v=' not in response.text
    assert '<script src="/static/profiles_bootstrap.js?v=' not in response.text
    assert '<script src="/static/profiles_guided.js?v=' not in response.text
    assert '<script src="/static/profiles_settings.js?v=' not in response.text
    assert '<script src="/static/profiles_advanced.js?v=' not in response.text
    assert '<script src="/static/profiles.js?v=' not in response.text
    assert 'id="wizard-starter-catalog"' not in response.text
    assert 'id="wizard-settings-catalog"' not in response.text
    assert 'id="wizard-preferences-catalog"' not in response.text
    assert 'id="wizard-manual-policy-controls"' not in response.text
    assert 'id="wizard-schema-shell-catalog"' not in response.text


def test_profiles_editor_modes_use_mode_specific_entrypoints():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Mode Entrypoint Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get("/profiles/new")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")

    assert guided_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert advanced_response.status_code == 307
    assert '<script src="/static/profiles_guided.js?v=' in guided_response.text
    assert '<script src="/static/profiles_advanced.js?v=' not in guided_response.text
    assert '<script src="/static/profiles_settings.js?v=' not in guided_response.text
    assert '<script src="/static/profiles_library.js?v=' not in guided_response.text
    assert '<script src="/static/profiles.js?v=' not in guided_response.text
    assert '<script src="/static/profiles_settings.js?v=' in settings_response.text
    assert '<script src="/static/profiles_guided.js?v=' not in settings_response.text
    assert '<script src="/static/profiles_advanced.js?v=' not in settings_response.text
    assert '<link rel="stylesheet" href="/static/vendor/profiles_monaco.css?v=' not in settings_response.text
    assert '<script src="/static/vendor/profiles_monaco.js?v=' not in settings_response.text
    assert '<script src="/static/profiles_json.js?v=' in json_response.text
    assert '<script src="/static/profiles_guided.js?v=' not in json_response.text
    assert '<script src="/static/profiles_settings.js?v=' not in json_response.text
    assert '<script src="/static/profiles_library.js?v=' not in json_response.text
    assert '<script src="/static/profiles.js?v=' not in json_response.text
    assert advanced_response.headers["location"] == f"/profiles/{profile_id}/json"


def test_profiles_page_uses_request_locale_for_initial_render():
    client = make_test_client(app)

    response = client.get(
        "/profiles",
        headers={"Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
    )

    assert response.status_code == 200
    assert '<html lang="ru">' in response.text
    assert "Библиотека" in response.text
    assert "Менеджер профилей браузера" in response.text
    assert "Поиск по имени профиля" in response.text
    assert "Сравнение двух профилей" in response.text
    assert "Пошаговый мастер" not in response.text
    assert "Search engine" not in response.text
    assert "Engine name" not in response.text
    assert "Search URL template" not in response.text
    assert "Required for a valid engine" not in response.text
    assert "Privacy and user data" not in response.text
    assert "Sync and Firefox Accounts" not in response.text
    assert "Homepage and startup" not in response.text
    assert "Controls in this area" not in response.text
    assert "Top-level policies" not in response.text
    assert "Control Room" not in response.text


def test_resolve_request_locale_skips_unsupported_languages_and_bad_weights():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"pt-BR;q=1, ;q=0.9, ru;q=oops, en;q=0.5")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


def test_resolve_request_locale_uses_matrix_backed_regional_fallbacks(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded,
        "settings",
        SimpleNamespace(
            SUPPORTED_LOCALES=("en", "ru", "de", "zh-CN", "fr", "es-ES"),
            DEFAULT_LOCALE="en",
        ),
    )

    cases = (
        (b"de-AT,de;q=0.9,en;q=0.1", "de"),
        (b"fr-CA,fr;q=0.9,en;q=0.1", "fr"),
        (b"es-MX,es;q=0.9,en;q=0.1", "es-ES"),
        (b"zh-Hans-CN,zh;q=0.9,en;q=0.1", "zh-CN"),
    )
    for header, expected_locale in cases:
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/profiles",
                "headers": [(b"accept-language", header)],
                "query_string": b"",
            }
        )
        assert reloaded._resolve_request_locale(request) == expected_locale


def test_resolve_request_locale_falls_back_to_active_catalog_for_target_only_locales(
    monkeypatch,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded.settings,
        "SUPPORTED_LOCALES",
        ("en", "ru", "de", "zh-CN", "fr"),
    )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"es-MX,es;q=0.9,en;q=0.1")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


def test_resolve_request_locale_prefers_next_active_catalog_before_default_fallback(
    monkeypatch,
):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    monkeypatch.setattr(
        reloaded.settings,
        "SUPPORTED_LOCALES",
        ("en", "ru", "de", "zh-CN", "fr"),
    )

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [(b"accept-language", b"es-MX,es;q=0.9,ru-RU;q=0.8,en;q=0.1")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "ru"


def test_load_locale_catalog_returns_empty_mapping_for_missing_locale(tmp_path, monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    reloaded._load_locale_catalog.cache_clear()
    monkeypatch.setattr(
        reloaded,
        "settings",
        SimpleNamespace(
            ROOT_DIR=tmp_path,
            I18N_DIR="i18n",
            SUPPORTED_LOCALES=("en", "ru"),
            TEMPLATES_DIR=web_profiles.settings.TEMPLATES_DIR,
        ),
    )

    assert reloaded._load_locale_catalog("de") == {}


def test_en_i18n_catalog_contains_expected_copy():
    client = make_test_client(app)

    locale_response = client.get("/i18n/en.json")
    assert locale_response.status_code == 200
    assert locale_response.headers["content-type"].startswith("application/json")
    _assert_en_locale_catalog(locale_response.json())


def test_ru_i18n_catalog_contains_expected_copy():
    client = make_test_client(app)

    locale_response = client.get("/i18n/ru.json")
    assert locale_response.status_code == 200
    _assert_ru_locale_catalog(locale_response.json())


def test_profiles_js_has_no_inline_english_fallback_copy():
    static_dir = Path(__file__).resolve().parents[1] / "app" / "static"
    fallback_pattern = re.compile(r'\bt\(\s*"profiles\.[^"]+"\s*,\s*"[^"]+"\s*\)')
    raw_status_pattern = re.compile(r"\b(?:setStatus|setDraftState|setValidationPreview)\(\s*[\"`]")
    confirm_fallback_pattern = re.compile(r'windowRef\.confirm\(\s*t\(\s*"profiles\.[^"]+"\s*,')

    fallback_hits: list[str] = []
    raw_status_hits: list[str] = []
    confirm_hits: list[str] = []

    for path in sorted(static_dir.glob("profiles*.js")):
        text = path.read_text(encoding="utf-8")
        if fallback_pattern.search(text):
            fallback_hits.append(path.name)
        if raw_status_pattern.search(text):
            raw_status_hits.append(path.name)
        if confirm_fallback_pattern.search(text):
            confirm_hits.append(path.name)

    assert not fallback_hits, f"inline translation fallbacks remain in: {fallback_hits}"
    assert not raw_status_hits, f"raw status strings remain in: {raw_status_hits}"
    assert not confirm_hits, f"confirm fallbacks remain in: {confirm_hits}"


def test_static_assets_are_served():
    client = make_test_client(app)
    settings = get_settings()

    favicon_response = client.get("/favicon.ico")
    assert favicon_response.status_code == 200
    assert favicon_response.headers["content-type"].startswith("image/x-icon")
    assert favicon_response.content == (settings.STATIC_DIR / "favicon.ico").read_bytes()


def test_static_vendor_js_yaml_asset_exists():
    asset_path = Path(__file__).resolve().parents[1] / "app" / "static" / "vendor" / "js-yaml.js"
    asset_text = asset_path.read_text(encoding="utf-8")

    assert asset_path.is_file()
    assert "js-yaml 4.1.0" in asset_text
    assert ".jsyaml={}" in asset_text or ".jsyaml=" in asset_text


def test_static_vendor_monaco_assets_exist():
    vendor_root = Path(__file__).resolve().parents[1] / "app" / "static" / "vendor"
    bundle_path = vendor_root / "profiles_monaco.js"
    bundle_css_path = vendor_root / "profiles_monaco.css"
    editor_worker_path = vendor_root / "monaco-editor.worker.js"
    json_worker_path = vendor_root / "monaco-json.worker.js"
    license_path = vendor_root / "monaco.LICENSE"

    assert bundle_path.is_file()
    assert bundle_css_path.is_file()
    assert editor_worker_path.is_file()
    assert json_worker_path.is_file()
    assert license_path.is_file()
    assert "eval(" not in bundle_path.read_text(encoding="utf-8")
    assert "new Function" not in bundle_path.read_text(encoding="utf-8")
    assert "Microsoft Corporation" in license_path.read_text(encoding="utf-8")


def test_json_editor_runtime_uses_profile_loaded_status_and_custom_monaco_theme_contract():
    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert 'function getMonacoThemeName(resolvedTheme)' in runtime_source
    assert 'monacoRef.editor.defineTheme("bpm-vs-light"' in runtime_source
    assert 'monacoRef.editor.defineTheme("bpm-vs-dark"' in runtime_source
    assert 'windowRef.monaco.editor.setTheme(getMonacoThemeName(resolvedTheme));' in runtime_source
    assert 'lineNumbersMinChars: 4' in runtime_source
    assert 'lineDecorationsWidth: 18' in runtime_source
    assert 'vertical: "visible"' in runtime_source
    assert 'horizontal: "auto"' in runtime_source
    assert (
        'fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"'
        in runtime_source
    )
    assert 'await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });' in runtime_source
    assert (
        'setStatus(t("profiles.status_profile_loaded").replace("{name}", hydratedProfile.name), "success");'
        in runtime_source
    )
    assert "const { announceStatus = hasLibrarySurface } = options;" in workspace_source
    assert "syncLibrary = hasLibrarySurface" in workspace_source
    assert "announceLoaded = true" in workspace_source
    assert '.editor-frame .monaco-editor .margin-view-overlays .line-numbers {' in css_source
    assert '.editor-frame .monaco-scrollable-element > .scrollbar.vertical {' in css_source
    assert '.editor-frame .monaco-scrollable-element > .scrollbar > .slider {' in css_source


def test_static_vendor_tailwind_replacement_asset_exists():
    asset_path = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "vendor" / "profiles_tailwind.css"
    )
    asset_text = asset_path.read_text(encoding="utf-8")

    assert asset_path.is_file()
    assert ".min-h-screen" in asset_text
    assert ".shadow-soft" in asset_text
    assert ".hover\\:bg-slate-50:hover" in asset_text


def test_static_profiles_bootstrap_assets_exist():
    static_root = Path(__file__).resolve().parents[1] / "app" / "static"
    head_bootstrap = static_root / "profiles_head_bootstrap.js"
    page_bootstrap = static_root / "profiles_page_bootstrap.js"
    library_bootstrap = static_root / "profiles_library_bootstrap.js"
    library_entry = static_root / "profiles_library.js"
    guided_entry = static_root / "profiles_guided.js"
    settings_entry = static_root / "profiles_settings.js"
    json_entry = static_root / "profiles_json.js"

    assert head_bootstrap.is_file()
    assert page_bootstrap.is_file()
    assert library_bootstrap.is_file()
    assert library_entry.is_file()
    assert guided_entry.is_file()
    assert settings_entry.is_file()
    assert json_entry.is_file()
    assert 'window.__BPM_INITIAL_LOCALE__ = JSON.parse(payloadText);' in page_bootstrap.read_text(encoding="utf-8")


def test_web_profiles_module_wires_templates_and_route():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    assert reloaded.templates.env.loader.searchpath == [str(reloaded.settings.TEMPLATES_DIR)]
    assert any(route.path == "/profiles" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/new" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/{profile_id}/edit" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/{profile_id}/settings" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/{profile_id}/json" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/{profile_id}/advanced" for route in reloaded.router.routes)


def test_profile_editor_routes_render_wizard_shells():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Route Skeleton Profile"),
    )
    profile_id = create_response.json()["id"]

    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")
    missing_response = client.get("/profiles/999999/edit")
    missing_settings_response = client.get("/profiles/999999/settings")
    missing_json_response = client.get("/profiles/999999/json")
    missing_advanced_response = client.get("/profiles/999999/advanced")

    assert new_response.status_code == 200
    assert edit_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert advanced_response.status_code == 307
    assert missing_response.status_code == 404
    assert missing_settings_response.status_code == 404
    assert missing_json_response.status_code == 404
    assert missing_advanced_response.status_code == 404
    assert "<title>New profile draft — Guided editor — Browser Policy Manager</title>" in new_response.text
    assert (
        "<title>Route Skeleton Profile — Guided editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert (
        "<title>Route Skeleton Profile — All settings — Browser Policy Manager</title>"
        in settings_response.text
    )
    assert "Advanced settings" not in settings_response.text
    assert "Search mapped controls and apply policy changes without opening the JSON editor." in settings_response.text
    assert "<title>Route Skeleton Profile — JSON editor — Browser Policy Manager</title>" in json_response.text
    assert 'data-profiles-route-mode="new"' in new_response.text
    assert 'data-profiles-route-mode="edit"' in edit_response.text
    assert 'data-profiles-route-mode="settings"' in settings_response.text
    assert 'data-profiles-route-mode="json"' in json_response.text
    assert 'data-profiles-template-kind="editor"' in new_response.text
    assert 'data-profiles-template-kind="editor"' in edit_response.text
    assert 'data-profiles-template-kind="settings"' in settings_response.text
    assert 'data-profiles-template-kind="json"' in json_response.text
    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text
    assert f'data-editing-profile-id="{profile_id}"' in settings_response.text
    assert f'data-editing-profile-id="{profile_id}"' in json_response.text
    assert_contains_all(new_response.text, ('id="wizard-panel"', 'id="wizard-schema"', 'id="editor-mode-settings"'))
    assert_contains_all(edit_response.text, ('id="wizard-panel"', 'id="wizard-schema"', 'id="editor-mode-settings"'))
    assert 'id="format"' not in new_response.text
    assert 'id="format"' not in edit_response.text
    assert_contains_all(
        settings_response.text,
        (
            'id="settings-panel"',
            'id="all-settings-review-panel"',
            'id="all-settings-review-summary"',
            'id="all-settings-review-actions"',
            'id="all-settings-list-panel"',
            'id="all-settings-list-summary"',
            'id="all-settings-list"',
            'id="all-settings-detail-panel"',
            'id="all-settings-add-preference"',
            'data-settings-list-filter="all"',
            'data-settings-list-filter="configured"',
            'data-settings-list-filter="available"',
            'data-settings-list-filter="guided-covered"',
            'data-settings-list-filter="all-settings-only"',
            'data-settings-list-filter="invalid"',
            'data-settings-list-filter="deprecated"',
            'data-settings-list-filter="raw"',
            'data-settings-list-filter="unknown"',
            'id="settings-category-browser-access"',
            'id="settings-category-home-startup"',
            'id="settings-category-search-navigation"',
            'id="settings-category-privacy-security"',
            'id="settings-category-users-addons-sites"',
            'id="settings-category-ai-smart-features"',
            'id="settings-category-raw-unmapped"',
            'data-settings-category-link="browser-access"',
            'id="wizard-settings-search-input"',
            'id="settings-schema-shell-step-2"',
            'data-settings-nav',
            'id="settings-preferences-general"',
            'id="wizard-preferences-general-presets"',
            'id="editor-mode-guided"',
            'id="editor-mode-settings"',
            'id="editor-mode-json"',
            'id="save"',
            'id="validate"',
        ),
    )
    assert 'id="wizard-panel"' not in settings_response.text
    assert 'id="editor-panel"' not in settings_response.text
    assert 'id="editor"' not in settings_response.text
    assert 'id="format"' not in settings_response.text
    assert 'id="editor-panel"' not in new_response.text
    assert 'id="editor-panel"' not in edit_response.text
    assert 'id="editor"' not in new_response.text
    assert 'id="editor"' not in edit_response.text
    assert 'id="details-panel"' not in new_response.text
    assert 'id="details-panel"' not in edit_response.text
    assert_contains_all(
        json_response.text,
        (
            'id="editor-mode-guided"',
            'id="editor-mode-settings"',
            'id="editor-mode-json"',
            'id="editor-panel"',
            'id="editor"',
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="download-firefox-policies"',
            'rel="noopener"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="advanced-context-panel"' not in json_response.text
    assert 'id="advanced-download-strip"' not in json_response.text
    assert 'id="advanced-review-strip"' not in json_response.text
    assert advanced_response.headers["location"] == f"/profiles/{profile_id}/json"


def test_profile_workspace_routes_smoke_dom_contracts():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Route Smoke Profile"),
    )
    profile_id = create_response.json()["id"]

    library_response = client.get("/profiles")
    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")

    assert library_response.status_code == 200
    assert new_response.status_code == 200
    assert edit_response.status_code == 200
    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert advanced_response.status_code == 307

    assert_contains_all(
        library_response.text,
        (
            'data-profiles-route-mode="library"',
            'data-profiles-template-kind="library"',
            'id="library-panel"',
            'id="search"',
            'id="library-schema-filter"',
            'id="library-lifecycle-filter"',
            'id="library-validation-filter"',
            'id="sort"',
            'id="order"',
            'id="create-profile-link"',
            'id="status"',
            'href="/profiles/new"',
            'id="list"',
            'id="compare-panel"',
        ),
    )
    assert 'data-editing-profile-id="' not in library_response.text
    assert 'id="overview-panel"' not in library_response.text
    assert 'id="current-name"' not in library_response.text
    assert 'id="profile-state-badge"' not in library_response.text
    assert 'id="workspace-signal"' not in library_response.text
    assert 'id="profile-clone-handoff-panel"' not in library_response.text
    assert 'id="profile-lifecycle-panel"' not in library_response.text
    assert 'id="profile-compliance-panel"' not in library_response.text
    assert 'id="wizard-panel"' not in library_response.text
    assert 'id="command-deck"' not in library_response.text
    assert 'id="editor-panel"' not in library_response.text
    for response, route_mode in ((new_response, "new"), (edit_response, "edit")):
        assert_contains_all(
            response.text,
            (
                f'data-profiles-route-mode="{route_mode}"',
                'data-profiles-template-kind="editor"',
                'id="wizard-panel"',
                'id="wizard-schema"',
                'id="wizard-starter-catalog"',
                'id="editor-mode-settings"',
            ),
        )
        assert 'id="library-panel"' not in response.text
        assert 'id="search"' not in response.text
        assert 'id="create-profile-link"' not in response.text
        assert 'id="list"' not in response.text
        assert 'id="compare-panel"' not in response.text
        assert 'id="details-panel"' not in response.text
        assert 'id="editor-panel"' not in response.text
        assert 'id="editor"' not in response.text
    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text
    assert_contains_all(
        settings_response.text,
        (
            'data-profiles-route-mode="settings"',
            'data-profiles-template-kind="settings"',
            'id="settings-panel"',
            'id="all-settings-review-panel"',
            'id="all-settings-review-summary"',
            'id="all-settings-review-actions"',
            'id="all-settings-list-panel"',
            'id="all-settings-list-summary"',
            'id="all-settings-list"',
            'id="all-settings-detail-panel"',
            'data-settings-list-filter="all"',
            'data-settings-list-filter="configured"',
            'data-settings-list-filter="available"',
            'data-settings-list-filter="guided-covered"',
            'data-settings-list-filter="all-settings-only"',
            'data-settings-list-filter="invalid"',
            'data-settings-list-filter="deprecated"',
            'data-settings-list-filter="raw"',
            'data-settings-list-filter="unknown"',
            'id="settings-category-browser-access"',
            'id="settings-category-home-startup"',
            'id="settings-category-search-navigation"',
            'id="settings-category-privacy-security"',
            'id="settings-category-users-addons-sites"',
            'id="settings-category-ai-smart-features"',
            'id="settings-category-raw-unmapped"',
            'id="wizard-settings-search-input"',
            'id="settings-schema-shell-step-2"',
            'data-settings-nav',
            'id="settings-preferences-general"',
            'id="wizard-preferences-general-presets"',
            'id="save"',
            'id="validate"',
        ),
    )
    assert 'id="wizard-panel"' not in settings_response.text
    assert 'id="editor-panel"' not in settings_response.text
    assert 'id="editor"' not in settings_response.text
    assert_contains_all(
        json_response.text,
        (
            'data-profiles-route-mode="json"',
            'data-profiles-template-kind="json"',
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="editor-panel"',
            'id="editor"',
            'id="download-firefox-policies"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="advanced-context-panel"' not in json_response.text
    assert 'id="advanced-download-strip"' not in json_response.text
    assert 'id="advanced-review-strip"' not in json_response.text
    assert advanced_response.headers["location"] == f"/profiles/{profile_id}/json"


def test_profile_library_exposes_complete_manager_control_surface():
    client = make_test_client(app)
    response = client.get("/profiles")

    assert response.status_code == 200
    assert_contains_all(
        response.text,
        (
            'id="library-schema-filter"',
            'id="library-lifecycle-filter"',
            'id="library-validation-filter"',
            'value="not_validated"',
            'id="sort"',
            'id="order"',
            'id="import-firefox-policies"',
            'id="import-firefox-policies-status"',
            'id="compare-panel"',
            'id="status"',
        ),
    )


def test_duplicate_route_marks_existing_profile_as_clone_source():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Duplicate Route Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/new?clone_from={profile_id}")

    assert response.status_code == 200
    assert 'data-profiles-route-mode="new"' in response.text
    assert f'data-clone-source-id="{profile_id}"' in response.text


def test_profile_editor_modes_explicitly_exclude_unrelated_ui_surfaces():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Mode Absence Contract Profile"),
    )
    profile_id = create_response.json()["id"]

    library_response = client.get("/profiles")
    guided_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    for token in (
        'id="wizard-panel"',
        'id="settings-panel"',
        'id="editor-panel"',
        'id="editor"',
        'id="download-firefox-policies"',
    ):
        assert token not in library_response.text

    for token in (
        'id="library-panel"',
        'id="search"',
        'id="compare-panel"',
        'id="settings-panel"',
        'id="editor-panel"',
        'id="editor"',
        'id="download-firefox-policies"',
        'id="format"',
    ):
        assert token not in guided_response.text

    for token in (
        'id="library-panel"',
        'id="compare-panel"',
        'id="wizard-panel"',
        'id="wizard-step-actions"',
        'id="editor-panel"',
        'id="editor"',
        'id="download-firefox-policies"',
        'id="format"',
    ):
        assert token not in settings_response.text

    for token in (
        'id="library-panel"',
        'id="compare-panel"',
        'id="wizard-panel"',
        'id="settings-panel"',
        'id="wizard-settings-search-input"',
        'id="settings-preferences-general"',
        'id="wizard-preferences-general-presets"',
        'id="advanced-context-panel"',
        'id="advanced-download-strip"',
        'id="advanced-review-strip"',
    ):
        assert token not in json_response.text


def test_shared_editor_chrome_dom_contract_is_present_across_editor_modes():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Shared Editor Chrome Contract Profile"),
    )
    profile_id = create_response.json()["id"]

    guided_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")

    shared_tokens = (
        'id="overview-panel"',
        'id="current-name"',
        'id="profile-state-badge"',
        'id="workspace-signal"',
        'id="save"',
        'id="validate"',
        'id="profile-name"',
        'id="profile-type"',
        'id="editor-profile-id"',
        'id="overview-schema"',
        'id="validation-preview"',
        'id="overview-context"',
        'id="editor-mode-guided"',
        'id="editor-mode-settings"',
        'id="editor-mode-json"',
    )

    for response in (guided_response, settings_response, json_response):
        assert response.status_code == 200
        assert_contains_all(response.text, shared_tokens)


def test_visual_editor_routes_hide_inline_advanced_surface():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Inline Advanced Split Profile"),
    )
    profile_id = create_response.json()["id"]

    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    settings_response = client.get(f"/profiles/{profile_id}/settings")
    json_response = client.get(f"/profiles/{profile_id}/json")
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")

    assert 'class="content-grid grid gap-4 support-hidden"' not in new_response.text
    assert 'class="content-grid grid gap-4 support-hidden"' not in edit_response.text
    assert f'href="/profiles/{profile_id}/json?focus=editor"' in edit_response.text
    assert f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit"' in edit_response.text
    assert 'id="settings-panel"' in settings_response.text
    assert 'data-settings-runtime-backing' not in settings_response.text
    assert 'id="wizard-panel"' not in settings_response.text
    assert 'id="details-panel"' not in settings_response.text
    assert 'id="editor-panel"' not in settings_response.text
    assert 'id="editor"' not in settings_response.text
    assert 'id="details-panel"' not in new_response.text
    assert 'id="details-panel"' not in edit_response.text
    assert 'id="editor-panel"' not in new_response.text
    assert 'id="editor-panel"' not in edit_response.text
    assert 'id="editor"' not in new_response.text
    assert 'id="editor"' not in edit_response.text
    assert_contains_all(
        json_response.text,
        (
            'data-profiles-route-mode="json"',
            'data-profiles-template-kind="json"',
            'id="editor-panel"',
            'id="download-firefox-policies"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="advanced-context-panel"' not in json_response.text
    assert 'id="advanced-download-strip"' not in json_response.text
    assert 'id="advanced-review-strip"' not in json_response.text
    assert advanced_response.headers["location"] == f"/profiles/{profile_id}/json"


def test_deleted_profile_routes_require_include_deleted_and_preserve_archived_chrome():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Route Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]
    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    hidden_response = client.get(f"/profiles/{profile_id}/edit")
    archived_response = client.get(f"/profiles/{profile_id}/edit?include_deleted=true")
    archived_settings_response = client.get(f"/profiles/{profile_id}/settings?include_deleted=true")
    archived_json_response = client.get(f"/profiles/{profile_id}/json?include_deleted=true")

    assert hidden_response.status_code == 404
    assert archived_response.status_code == 200
    assert archived_settings_response.status_code == 200
    assert archived_json_response.status_code == 200
    assert 'data-include-deleted="true"' in archived_response.text
    assert 'data-i18n="profiles.badge_deleted"' in archived_response.text
    assert 'href="/profiles/' + str(profile_id) + '/edit?include_deleted=true"' in archived_response.text
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue"'
        in archived_response.text
    )
    assert (
        f'href="/profiles/{profile_id}/json?include_deleted=true&amp;focus=editor"'
        in archived_response.text
    )

    archived_soup = BeautifulSoup(archived_response.text, "html.parser")
    assert archived_soup.find(id="current-name").get_text(strip=True) == "Archived Route Profile"
    assert archived_soup.find(id="profile-state-badge").get_text(strip=True) == "Deleted"
    assert archived_soup.find(id="overview-context").get_text(strip=True) == "Archived profile"

    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200
    restored_response = client.get(f"/profiles/{profile_id}/edit")
    assert restored_response.status_code == 200
    restored_soup = BeautifulSoup(restored_response.text, "html.parser")
    assert restored_soup.find(id="profile-state-badge").get_text(strip=True) == "Active"
    assert restored_soup.find(id="overview-context").get_text(strip=True) == "Saved profile"


def test_guided_wizard_ai_step_stays_separate_from_users_addons_sites_step():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Wizard Step Seven Structure Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    wizard_panels = soup.find("div", class_="wizard-panels")
    step_four = soup.find(id="wizard-step-4")
    step_five = soup.find(id="wizard-step-5")
    bookmarks = soup.find(id="wizard-step-4-bookmarks")
    websites = soup.find(id="wizard-step-4-websites")

    assert wizard_panels is not None
    assert step_four is not None
    assert step_five is not None
    assert bookmarks is not None
    assert websites is not None
    assert step_four in wizard_panels.find_all("section", recursive=False)
    assert step_five in wizard_panels.find_all("section", recursive=False)
    assert bookmarks in step_four.descendants
    assert websites in step_four.descendants
    assert step_five not in step_four.descendants


def test_guided_wizard_all_steps_stay_as_direct_wizard_panels_and_keep_own_subsections():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Wizard Structure Audit Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    wizard_panels = soup.find("div", class_="wizard-panels")
    assert wizard_panels is not None

    direct_panel_ids = [
        child.get("id")
        for child in wizard_panels.find_all(recursive=False)
        if getattr(child, "name", None) == "section" and child.get("id", "").startswith("wizard-step-")
    ]
    assert direct_panel_ids == [f"wizard-step-{step}" for step in range(1, 7)]

    step_expected_descendants = {
        1: ("wizard-name", "wizard-schema", "wizard-starter-grid"),
        2: (
            "wizard-step-2-basics",
            "wizard-step-2-proxy",
            "wizard-step-2-trust",
            "wizard-home-surface-startup",
            "wizard-home-surface-new-tab",
            "wizard-home-surface-firefox-home",
            "wizard-step-2-default-search",
            "wizard-step-2-managed-engines",
            "wizard-step-2-suggestions",
            "wizard-step-2-review",
        ),
        3: ("wizard-hardening-presets", "wizard-cleanup-presets", "wizard-site-data-presets"),
        4: ("wizard-step-4-accounts", "wizard-step-4-language", "wizard-step-4-extensions", "wizard-step-4-bookmarks", "wizard-step-4-websites"),
        5: ("wizard-ai-posture-presets", "wizard-ai-policy-controls", "wizard-visual-search-enabled-card"),
        6: ("wizard-export-ready-card", "wizard-export-summary-ai", "wizard-export-summary-features"),
    }

    top_level_panels = {
        step: soup.find(id=f"wizard-step-{step}")
        for step in range(1, 7)
    }
    for step, panel in top_level_panels.items():
        assert panel is not None
        assert panel.parent is wizard_panels
        for descendant_id in step_expected_descendants[step]:
            descendant = soup.find(id=descendant_id)
            assert descendant is not None
            assert descendant in panel.descendants

    for step, panel in top_level_panels.items():
        other_step_prefixes = tuple(f"wizard-step-{other}-" for other in range(1, 7) if other != step)
        leaking_ids = [
            descendant.get("id")
            for descendant in panel.find_all(attrs={"id": True})
            if descendant.get("id", "").startswith(other_step_prefixes)
        ]
        assert leaking_ids == [], f"Unexpected cross-step ids inside wizard-step-{step}: {leaking_ids}"


def test_profiles_page_uses_single_year_footer_for_2025(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FrozenDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, tzinfo=tz or UTC)

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded, "datetime", FrozenDateTime)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)
    monkeypatch.setattr(
        reloaded,
        "normalize_legacy_profile_schema_versions",
        lambda session: _noop_async(),
    )

    class FakeSession:
        async def commit(self):
            return None

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_page(request, FakeSession()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_library.html"
    assert captured["context"]["title"] == "Library — Browser Policy Manager"
    assert captured["context"]["profiles_route_mode"] == "library"
    assert captured["context"]["editing_profile_id"] is None
    assert captured["context"]["app_name"] == "Browser Policy Manager"
    assert captured["context"]["app_version"] == reloaded.settings.APP_VERSION
    assert captured["context"]["footer_year_range"] == "2025"
    assert captured["context"]["tr"]("profiles.missing", "Fallback") == "Fallback"
    assert "wizard_settings_catalog" in captured["context"]
    assert "wizard_preferences_catalog" in captured["context"]
    assert "wizard_manual_policy_controls" in captured["context"]
    assert "wizard_starter_catalog" in captured["context"]
    assert "wizard_schema_shell_catalog" in captured["context"]


async def _noop_async():
    return None


def test_profiles_library_route_normalizes_schema_versions_before_render(monkeypatch):
    import app.web.profiles as web_profiles

    captured: dict[str, object] = {}
    events: list[str] = []

    class FakeSession:
        async def commit(self):
            events.append("commit")

    async def fake_normalize(session):
        captured["session"] = session
        events.append("normalize")

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        events.append("render")
        return HTMLResponse("ok")

    monkeypatch.setattr(web_profiles, "normalize_legacy_profile_schema_versions", fake_normalize)
    monkeypatch.setattr(web_profiles.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [],
            "query_string": b"",
        }
    )
    session = FakeSession()

    response = asyncio.run(web_profiles.profiles_page(request, session))

    assert response.status_code == 200
    assert captured["session"] is session
    assert captured["name"] == "profiles_library.html"
    assert events == ["normalize", "commit", "render"]


def test_profile_editor_routes_use_editor_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FakeProfile(SimpleNamespace):
        def model_dump(self, mode="python"):
            return {
                "id": self.id,
                "name": self.name,
                "schema_version": self.schema_version,
                "flags": self.flags,
            }

    async def fake_get(session, profile_id, include_deleted=False):
        return FakeProfile(
            id=profile_id,
            name="Template Split Profile",
            schema_version="release-151",
            flags={"DisableTelemetry": True},
        )

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/7/edit",
            "headers": [],
            "query_string": b"",
        }
    )

    response = asyncio.run(reloaded.profiles_edit_page(request, 7, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_editor.html"
    assert captured["context"]["profiles_route_mode"] == "edit"
    assert captured["context"]["editing_profile_id"] == 7
    assert captured["context"]["editing_profile_schema_version"] == "release-151"
    assert captured["context"]["editing_profile_initial"] == {
        "id": 7,
        "name": "Template Split Profile",
        "schema_version": "release-151",
        "flags": {"DisableTelemetry": True},
    }


def test_profile_settings_route_uses_settings_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FakeProfile(SimpleNamespace):
        def model_dump(self, mode="python"):
            return {
                "id": self.id,
                "name": self.name,
                "schema_version": self.schema_version,
                "flags": self.flags,
            }

    async def fake_get(session, profile_id, include_deleted=False):
        return FakeProfile(
            id=profile_id,
            name="Settings Split Profile",
            schema_version="esr-140.11",
            flags={"DisableTelemetry": True},
        )

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/8/settings",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_settings_page(request, 8, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_settings.html"
    assert captured["context"]["title"] == (
        "Settings Split Profile — All settings — Browser Policy Manager"
    )
    assert captured["context"]["profiles_route_mode"] == "settings"
    assert captured["context"]["editing_profile_id"] == 8
    assert captured["context"]["editing_profile_schema_version"] == "esr-140.11"
    assert captured["context"]["editing_profile_initial"] == {
        "id": 8,
        "name": "Settings Split Profile",
        "schema_version": "esr-140.11",
        "flags": {"DisableTelemetry": True},
    }
    assert captured["context"]["return_url"] == "/profiles/8/edit"
    assert captured["context"]["focus_target"] == "policy:DisableTelemetry"
    assert captured["context"]["settings_href"] == (
        "/profiles/8/settings?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    )
    assert captured["context"]["json_href"] == "/profiles/8/json?focus=policy:DisableTelemetry"


def test_profile_json_route_uses_json_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    class FakeProfile(SimpleNamespace):
        def model_dump(self, mode="python"):
            return {
                "id": self.id,
                "name": self.name,
                "schema_version": self.schema_version,
                "flags": self.flags,
            }

    async def fake_get(session, profile_id, include_deleted=False):
        return FakeProfile(
            id=profile_id,
            name="JSON Split Profile",
            schema_version="release-151",
            flags={"DisableTelemetry": True},
        )

    def fake_template_response(request, name, context):
        captured["request"] = request
        captured["name"] = name
        captured["context"] = context
        return HTMLResponse("ok")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)
    monkeypatch.setattr(reloaded.templates, "TemplateResponse", fake_template_response)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/8/json",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_json_page(request, 8, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_json.html"
    assert captured["context"]["title"] == (
        "JSON Split Profile — JSON editor — Browser Policy Manager"
    )
    assert captured["context"]["profiles_route_mode"] == "json"
    assert captured["context"]["editing_profile_id"] == 8
    assert captured["context"]["editing_profile_schema_version"] == "release-151"
    assert captured["context"]["editing_profile_initial"] == {
        "id": 8,
        "name": "JSON Split Profile",
        "schema_version": "release-151",
        "flags": {"DisableTelemetry": True},
    }
    assert captured["context"]["return_url"] == "/profiles/8/edit"
    assert captured["context"]["focus_target"] == "policy:DisableTelemetry"
    assert captured["context"]["settings_href"] == (
        "/profiles/8/settings?return=/profiles/8/json&focus=policy:DisableTelemetry"
    )


def test_profile_advanced_route_redirects_to_json(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    async def fake_get(session, profile_id, include_deleted=False):
        return SimpleNamespace(id=profile_id, name="Redirect Split Profile")

    monkeypatch.setattr(reloaded.ProfileService, "get", fake_get)

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles/8/advanced",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_advanced_page(request, 8, SimpleNamespace()))

    assert response.status_code == 307
    assert response.headers["location"] == (
        "/profiles/8/json?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    )


def test_profile_editor_route_context_bootstraps_frontend_state():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function readProfilesRouteContext()" in source
    assert "bodyEl?.dataset.profilesRouteMode" in source
    assert "bodyEl?.dataset.editingProfileId" in source
    assert "async function bootstrapProfileRouteState()" in source
    assert '(routeMode === "edit" || routeMode === "settings" || routeMode === "json") && editingProfileId' in source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in source
    assert "await resetDraft(true);" in source
    assert "await reloadList();" in source


def test_profile_json_route_context_bootstraps_focus():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert 'routeMode === "json"' in source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in source
    assert "setAdvancedHandoffContext(null);" in source
    assert "applyAdvancedFocusTarget(focusTarget);" in source
    assert 'const savedWorkspaceScope = windowRef.localStorage.getItem(workspaceScopeStorageKey)' not in source


def test_profile_json_route_renders_return_and_focus_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Advanced Focus Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/edit&focus=policy:DisableTelemetry"
    )
    unsafe_response = client.get(
        f"/profiles/{profile_id}/advanced?return=https://example.com/phish&focus=policy:DisableTelemetry"
    )

    assert response.status_code == 200
    assert f'data-advanced-return-url="/profiles/{profile_id}/edit"' in response.text
    assert 'data-advanced-focus-target="policy:DisableTelemetry"' in response.text
    assert 'id="advanced-return-link"' not in response.text
    assert unsafe_response.status_code == 307
    assert unsafe_response.headers["location"] == f"/profiles/{profile_id}/json?focus=policy:DisableTelemetry"


def test_archived_profile_handoff_routes_preserve_include_deleted_return_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Handoff Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]
    assert client.delete(f"/api/profiles/{profile_id}").status_code == 204

    settings_response = client.get(
        f"/profiles/{profile_id}/settings?include_deleted=true&return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue&focus=policy:DisableTelemetry"
    )
    json_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=raw"
    )

    assert settings_response.status_code == 200
    assert json_response.status_code == 200
    assert 'data-include-deleted="true"' in settings_response.text
    assert f'data-advanced-return-url="/profiles/{profile_id}/edit?include_deleted=true"' in settings_response.text
    assert (
        f'href="/profiles/{profile_id}/json?include_deleted=true&amp;focus=policy:DisableTelemetry"'
        in settings_response.text
    )
    assert 'data-include-deleted="true"' in json_response.text
    assert f'data-advanced-return-url="/profiles/{profile_id}/settings?include_deleted=true"' in json_response.text
    assert f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"' in json_response.text
    assert 'id="advanced-return-link"' not in json_response.text


def test_archived_profile_semantic_focus_routes_preserve_include_deleted_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Archived Semantic Focus Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]
    assert client.delete(f"/api/profiles/{profile_id}").status_code == 204

    settings_policy_response = client.get(
        f"/profiles/{profile_id}/settings?include_deleted=true&return=/profiles/{profile_id}/edit%3Finclude_deleted%3Dtrue&focus=policy:DisableTelemetry"
    )
    json_raw_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=raw"
    )
    json_deprecated_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=deprecated:LegacyPolicy"
    )
    json_unknown_response = client.get(
        f"/profiles/{profile_id}/json?include_deleted=true&return=/profiles/{profile_id}/settings%3Finclude_deleted%3Dtrue&focus=unknown:FuturePolicy"
    )

    assert settings_policy_response.status_code == 200
    assert json_raw_response.status_code == 200
    assert json_deprecated_response.status_code == 200
    assert json_unknown_response.status_code == 200

    assert (
        f'href="/profiles/{profile_id}/json?include_deleted=true&amp;focus=policy:DisableTelemetry"'
        in settings_policy_response.text
    )
    assert 'id="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-controls="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-expanded="true"' in settings_policy_response.text
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"'
        in json_raw_response.text
    )
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"'
        in json_deprecated_response.text
    )
    assert (
        f'href="/profiles/{profile_id}/settings?include_deleted=true&amp;return=/profiles/{profile_id}/json%3Finclude_deleted%3Dtrue&amp;focus=settings-schema-shell-step-8"'
        in json_unknown_response.text
    )
    assert 'data-advanced-focus-target="raw"' in json_raw_response.text
    assert 'data-advanced-focus-target="deprecated:LegacyPolicy"' in json_deprecated_response.text
    assert 'data-advanced-focus-target="unknown:FuturePolicy"' in json_unknown_response.text


def test_active_profile_semantic_focus_routes_preopen_expected_settings_shell():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Active Semantic Focus Profile", schema_version="release-151"),
    )
    profile_id = create_response.json()["id"]

    settings_policy_response = client.get(
        f"/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit&focus=policy:DisableTelemetry"
    )
    json_raw_response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/settings&focus=raw"
    )

    assert settings_policy_response.status_code == 200
    assert json_raw_response.status_code == 200
    assert (
        f'href="/profiles/{profile_id}/json?focus=policy:DisableTelemetry"'
        in settings_policy_response.text
    )
    assert 'id="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-controls="settings-schema-shell-step-5-details"' in settings_policy_response.text
    assert 'aria-expanded="true"' in settings_policy_response.text
    assert (
        f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/json&amp;focus=settings-schema-shell-step-8"'
        in json_raw_response.text
    )


def test_profile_advanced_helpers_reject_unsafe_values_and_build_focus_only_href():
    import app.web.profiles as web_profiles

    assert web_profiles._resolve_safe_profiles_return_url(None) is None
    assert web_profiles._resolve_safe_profiles_return_url("//profiles/8/edit") is None
    assert (
        web_profiles._resolve_safe_profiles_return_url("/profiles?return=https://evil.test")
        is None
    )
    assert web_profiles._resolve_safe_profiles_return_url("/profiles/8/edit") == (
        "/profiles/8/edit"
    )

    assert web_profiles._resolve_focus_target("   ") is None
    assert web_profiles._resolve_focus_target("x" * 161) is None
    assert web_profiles._resolve_focus_target("  policy:DisableTelemetry  ") == (
        "policy:DisableTelemetry"
    )
    assert web_profiles._resolve_positive_int("not-a-number") is None
    assert web_profiles._resolve_json_focus_target_from_settings_focus(
        "settings-schema-shell-step-8"
    ) == "raw"
    assert web_profiles._resolve_json_focus_target_from_settings_focus(
        "policy:DisableTelemetry"
    ) == "policy:DisableTelemetry"
    assert web_profiles._resolve_settings_focus_target_from_json_focus("raw") == (
        "settings-schema-shell-step-8"
    )
    assert web_profiles._resolve_settings_focus_target_from_json_focus(
        "deprecated:LegacyPolicy"
    ) == "settings-schema-shell-step-8"
    assert web_profiles._resolve_settings_focus_target_from_json_focus(
        "policy:DisableTelemetry"
    ) == "policy:DisableTelemetry"
    shell_catalog = web_profiles.get_wizard_schema_shell_catalog(
        web_profiles.get_wizard_preferences_catalog(web_profiles.get_wizard_settings_catalog())
    )
    assert web_profiles._resolve_settings_shell_focus_step(
        "policy:DisableTelemetry",
        "release-151",
        shell_catalog,
    ) == 5
    assert web_profiles._resolve_settings_shell_focus_step(
        "policy:LocalNetworkAccess",
        "release-151",
        shell_catalog,
    ) == 5
    assert web_profiles._resolve_settings_shell_focus_step(
        "deprecated:LegacyPolicy",
        "release-151",
        shell_catalog,
    ) == 8
    assert web_profiles._resolve_settings_shell_focus_step(
        "shell-policy:8:DisableProfileRefresh",
        "release-151",
        shell_catalog,
    ) == 8
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "shell-policy:not-a-step:DisableTelemetry",
            "release-151",
            shell_catalog,
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "shell-policy:8",
            "release-151",
            shell_catalog,
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:   ",
            "release-151",
            shell_catalog,
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:DefinitelyNotInTheCatalog",
            "release-151",
            shell_catalog,
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-151",
            {
                "channels": {
                    "release-151": {
                        "steps": {
                            "not-a-step": {
                                "recommended": [{"id": "MatchedPolicy"}],
                            }
                        }
                    }
                }
            },
        )
        is None
    )
    assert web_profiles._resolve_json_focus_target_from_settings_focus("   ") is None
    assert web_profiles._resolve_json_focus_target_from_settings_focus("custom-target") is None
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-151",
            {"channels": []},
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-151",
            {"channels": {"release-151": []}},
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-151",
            {"channels": {"release-151": {"steps": []}}},
        )
        is None
    )
    assert (
        web_profiles._resolve_settings_shell_focus_step(
            "policy:MatchedPolicy",
            "release-151",
            {
                "channels": {
                    "release-151": {
                        "steps": {
                            "5": ["not-a-dict"],
                        }
                    }
                }
            },
        )
        is None
    )
    assert web_profiles._resolve_settings_focus_target_from_json_focus("custom-target") == (
        "custom-target"
    )

    assert web_profiles._build_profile_json_href(
        8,
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/json?focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_json_href(
        8,
        return_url="/profiles/8/edit",
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/json?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_json_href(
        8,
        return_url="/profiles/8/edit?include_deleted=true",
        focus_target="deprecated:LegacyPolicy",
        include_deleted=True,
    ) == "/profiles/8/json?include_deleted=true&return=/profiles/8/edit%3Finclude_deleted%3Dtrue&focus=deprecated:LegacyPolicy"
    assert web_profiles._build_profile_advanced_href(
        8,
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/advanced?focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_advanced_href(
        8,
        return_url="/profiles/8/edit",
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/advanced?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_advanced_href(
        8,
        return_url="/profiles/8/edit",
    ) == "/profiles/8/advanced?return=/profiles/8/edit"
    assert web_profiles._build_profile_advanced_href(
        8,
        focus_target="policy:DisableTelemetry",
        include_deleted=True,
    ) == "/profiles/8/advanced?include_deleted=true&focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_settings_href(
        8,
        return_url="/profiles/8/edit",
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/settings?return=/profiles/8/edit&focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_settings_href(
        8,
        return_url="/profiles/8/json?include_deleted=true",
        focus_target="settings-schema-shell-step-8",
        include_deleted=True,
    ) == "/profiles/8/settings?include_deleted=true&return=/profiles/8/json%3Finclude_deleted%3Dtrue&focus=settings-schema-shell-step-8"
    assert web_profiles._build_profile_route_path(8, "settings") == "/profiles/8/settings"
    assert web_profiles._build_profile_route_path(8, "settings", include_deleted=True) == (
        "/profiles/8/settings?include_deleted=true"
    )


def test_profile_json_route_regression_contract():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Advanced Regression Profile"),
    )
    profile_id = create_response.json()["id"]

    json_response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/edit&focus=editor"
    )
    visual_response = client.get(f"/profiles/{profile_id}/edit")

    assert json_response.status_code == 200
    assert "<title>Advanced Regression Profile — JSON editor — Browser Policy Manager</title>" in json_response.text
    assert 'data-profiles-route-mode="json"' in json_response.text
    assert 'data-profiles-template-kind="json"' in json_response.text
    assert f'data-editing-profile-id="{profile_id}"' in json_response.text
    assert f'data-advanced-return-url="/profiles/{profile_id}/edit"' in json_response.text
    assert 'data-advanced-focus-target="editor"' in json_response.text
    assert_contains_all(
        json_response.text,
        (
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="editor-panel"',
            'id="editor"',
            'id="download-firefox-policies"',
        ),
    )
    assert 'id="wizard-panel"' not in json_response.text
    assert 'id="settings-panel"' not in json_response.text
    assert 'id="details-panel"' not in json_response.text
    assert 'id="advanced-context-panel"' not in json_response.text
    assert 'id="advanced-download-strip"' not in json_response.text
    assert 'id="advanced-review-strip"' not in json_response.text

    assert visual_response.status_code == 200
    assert 'data-profiles-template-kind="editor"' in visual_response.text
    assert 'id="editor-mode-settings"' in visual_response.text
    assert 'id="details-panel"' not in visual_response.text
    assert 'id="editor-panel"' not in visual_response.text
    assert 'id="editor"' not in visual_response.text
    assert 'id="workspace-scope-panel"' not in visual_response.text
    assert 'id="workspace-scope-guided"' not in visual_response.text
    assert 'id="workspace-scope-advanced"' not in visual_response.text


def test_visual_advanced_actions_route_to_advanced_destination():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function buildProfileRoutePath(profileId, modeKey, includeDeleted = false)" in source
    assert 'basePath = `/profiles/${profileId}/settings`;' in source
    assert 'basePath = `/profiles/${profileId}/json`;' in source
    assert "function buildEditorReturnPath(profileId, routeMode, includeDeleted = false)" in source
    assert 'if (routeMode === "settings") {' in source
    assert 'if (routeMode === "json") {' in source
    assert "function normalizeSettingsFocusTarget(focusTarget)" in source
    assert 'return "settings-panel";' in source
    assert 'return "settings-schema-shell-step-8";' in source
    assert 'normalizedTarget === "raw"' in source
    assert 'normalizedTarget.startsWith("deprecated:")' in source
    assert "function normalizeJsonFocusTarget(focusTarget)" in source
    assert 'if (normalizedTarget === "settings-schema-shell-step-8") return "raw";' in source
    assert "function buildSettingsRouteHref(profileId, focusTarget = \"\")" in source
    assert 'href.searchParams.set("return", buildEditorReturnPath(profileId, routeMode, includeDeleted));' in source
    assert "const normalizedFocusTarget = normalizeSettingsFocusTarget(focusTarget);" in source
    assert 'href.searchParams.set("focus", normalizedFocusTarget);' in source
    assert "function getSettingsRouteHref(focusTarget = \"\")" in source
    assert "function buildAdvancedRouteHref(profileId, focusTarget = \"\")" in source
    assert "const normalizedFocusTarget = normalizeJsonFocusTarget(focusTarget);" in source
    assert "function getAdvancedRouteHref(focusTarget = \"\")" in source
    assert "function parseJsonFocusTarget(focusTarget)" in source
    assert "function applyJsonEditorFocusTarget(focusTarget)" in source
    assert 'const jsonTarget = routeMode === "json" ? parseJsonFocusTarget(target) : null;' in source
    assert "function deriveAdvancedFocusTarget(targetEl, fallback = \"\")" in source
    assert "function openAdvancedRouteFromVisual(event = null, focusTarget = \"\")" in source
    assert 'if (routeMode === "json") return false;' in source
    assert 'const openJsonRoute = normalizedFocusTarget === "editor"' in source
    assert '|| normalizedFocusTarget === "unknown"' in source
    assert '|| normalizedFocusTarget.startsWith("unknown:");' in source
    assert 'getAdvancedRouteHref(normalizedFocusTarget || "editor")' in source
    assert "getSettingsRouteHref(normalizedFocusTarget)" in source
    assert 'const advancedWindow = windowRef.open(href, "_blank", "noopener");' in source
    assert "advancedWindow.opener = null;" in source
    assert "function resolveAdvancedFocusTarget(focusTarget)" in source
    assert 'if (target === "settings-panel") return documentRef.getElementById("settings-panel");' in source
    assert 'if (target === "settings-schema-shell-step-8") return documentRef.getElementById("settings-schema-shell-step-8");' in source
    assert "return findSettingsTarget(target)" in source
    assert 'documentRef.querySelector(`[data-wizard-shell-policy-id="${policyId}"]`)' in source
    assert "|| documentRef.getElementById(target)" in source
    assert "bpm-workspace-scope" not in source


def test_export_technical_alert_strip_has_direct_dom_refresh_contract():
    root = Path(__file__).resolve().parents[1]
    export_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")
    review_source = (root / "app" / "static" / "profiles_review.js").read_text(
        encoding="utf-8"
    )

    assert 'id="wizard-export-technical-alerts"' in export_template
    assert 'id="wizard-export-raw-summary-jump"' in export_template
    assert 'id="wizard-export-deprecated-summary-jump"' in export_template
    assert 'id="wizard-export-unknown-summary-jump"' in export_template
    assert 'id="wizard-export-raw-summary-count"' in export_template
    assert 'id="wizard-export-deprecated-summary-count"' in export_template
    assert 'id="wizard-export-unknown-summary-count"' in export_template
    assert "function renderFinalExportTechnicalAlerts(summary)" in review_source
    assert 'documentRef.getElementById("wizard-export-technical-alerts")' in review_source
    assert 'documentRef.getElementById("wizard-export-raw-summary-jump")' in review_source
    assert 'documentRef.getElementById("wizard-export-deprecated-summary-jump")' in review_source
    assert 'documentRef.getElementById("wizard-export-unknown-summary-jump")' in review_source
    assert 'documentRef.getElementById("wizard-export-raw-summary-count")' in review_source
    assert 'documentRef.getElementById("wizard-export-deprecated-summary-count")' in review_source
    assert 'documentRef.getElementById("wizard-export-unknown-summary-count")' in review_source
    assert "technicalAlertsContainerEl.hidden = visibleCount <= 0;" in review_source


def test_unknown_export_review_jump_routes_to_json_contract():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert 'if (jumpKind === "unknown") {' in source
    assert 'const semanticFocusTarget = jumpKey ? `${jumpKind}:${jumpKey}` : jumpKind;' in source
    assert "applyAdvancedContextForFinalReviewSelection(selection);" in source
    assert "if (openAdvancedRouteFromVisual(event, semanticFocusTarget)) {" in source
    assert 'const openJsonRoute = normalizedFocusTarget === "editor"' in source
    assert '|| normalizedFocusTarget === "unknown"' in source
    assert '|| normalizedFocusTarget.startsWith("unknown:");' in source
    assert '? getAdvancedRouteHref(normalizedFocusTarget || "editor")' in source
    assert ': getSettingsRouteHref(normalizedFocusTarget);' in source
    assert 'const jumpKey = finalReviewJumpButton.dataset.finalReviewKey || "";' in source


def test_library_table_resets_list_spacing_contract():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles.css"
    ).read_text(encoding="utf-8")

    library_table_block_start = source.index(".library-table {")
    library_table_block_end = source.index("}", library_table_block_start)
    library_table_block = source[library_table_block_start:library_table_block_end]

    assert "display: grid;" in library_table_block
    assert "gap: 10px;" in library_table_block
    assert "margin: 0;" in library_table_block
    assert "padding: 0;" in library_table_block


def test_library_table_head_and_rows_share_column_contract():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles.css"
    ).read_text(encoding="utf-8")

    assert "--library-table-columns:" in source
    assert "--library-table-columns-compact:" in source
    assert "grid-template-columns: var(--library-table-columns);" in source
    assert "grid-template-columns: var(--library-table-columns-compact);" in source


def test_library_title_button_uses_wrapping_width_contract():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles.css"
    ).read_text(encoding="utf-8")

    block_start = source.index(".library-row-title-button {")
    block_end = source.index("}", block_start)
    block = source[block_start:block_end]

    assert "width: 100%;" in block
    assert "max-width: 100%;" in block
    assert "min-width: 0;" in block
    assert "width: fit-content;" not in block


def test_library_row_button_uses_border_box_contract():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles.css"
    ).read_text(encoding="utf-8")

    block_start = source.index(".profile-list-button {")
    block_end = source.index("}", block_start)
    block = source[block_start:block_end]

    assert "box-sizing: border-box;" in block
    assert "width: 100%;" in block


def test_library_action_buttons_use_border_box_contract():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles.css"
    ).read_text(encoding="utf-8")

    block_start = source.index(".library-row-actions .button-base {")
    block_end = source.index("}", block_start)
    block = source[block_start:block_end]

    assert "box-sizing: border-box;" in block
    assert "width: 100%;" in block


def test_library_action_buttons_do_not_break_russian_words():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles.css"
    ).read_text(encoding="utf-8")

    button_block_start = source.index(".library-row-actions .button-base {")
    button_block_end = source.index("}", button_block_start)
    button_block = source[button_block_start:button_block_end]

    grid_block_start = source.index(".library-row-action-grid {")
    grid_block_end = source.index("}", grid_block_start)
    grid_block = source[grid_block_start:grid_block_end]

    assert "overflow-wrap: anywhere;" not in button_block
    assert "overflow-wrap: normal;" in button_block
    assert "word-break: normal;" in button_block
    assert "minmax(168px, 1fr)" in grid_block


def test_library_compare_contract_selects_two_profiles_explicitly():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_library_bootstrap.js"
    ).read_text(encoding="utf-8")

    assert 'const compareBaseStorageKey = "bpm-library-compare-base";' not in source
    assert "let compareFirstProfileState = null;" in source
    assert "let compareSecondProfileState = null;" in source
    assert "function buildCompareState(profile)" in source
    assert "function renderComparePanel()" in source
    assert "windowRef.__BPM_LIBRARY_ITEMS__ = Array.isArray(items) ? items : [];" in source
    assert "async function selectProfileForComparison(id)" in source
    assert "await selectProfileForComparison(profile.id);" in source
    assert 't("profiles.library_compare_select_first")' in source
    assert 't("profiles.library_compare_select_second")' in source
    assert 't("profiles.library_compare_use_as_second")' in source
    assert 'windowRef.localStorage?.setItem(compareBaseStorageKey, JSON.stringify({' not in source
    assert 'windowRef.addEventListener?.("storage", (event) => {' not in source
    assert 'windowRef.addEventListener?.("focus", refreshCompareBaselineUi);' not in source


def test_compare_diff_recurses_into_missing_object_branches_contract():
    root = Path(__file__).resolve().parents[1]
    library_source = (root / "app" / "static" / "profiles_library_bootstrap.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )

    for source in (library_source, workspace_source):
        assert "if (isPlainObject(normalizedBase) || isPlainObject(normalizedOther)) {" in source
        assert "const baseObject = isPlainObject(normalizedBase) ? normalizedBase : {};" in source
        assert "const otherObject = isPlainObject(normalizedOther) ? normalizedOther : {};" in source
        assert "collectDiffPaths(baseObject[key], otherObject[key], [...path, key], changes);" in source


def test_profile_runtime_and_wizard_bootstrap_guard_optional_inputs_contract():
    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    shared_source = (root / "app" / "static" / "profiles_shared.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )
    extension_source = (root / "app" / "static" / "profiles_extensions.js").read_text(
        encoding="utf-8"
    )
    wizard_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )

    assert 'nameInput?.addEventListener("input", () => {' in runtime_source
    assert 'ownerInput?.addEventListener("input", () => {' in runtime_source
    assert 'descriptionInput?.addEventListener("input", () => {' in runtime_source
    assert 'profileTypeEl?.addEventListener("change", () => {' in runtime_source
    assert "if (nameInput) {" in runtime_source
    assert "if (profileTypeEl) {" in runtime_source

    assert "if (!input) return;" in shared_source
    assert "if (!input) return;" in network_source
    assert "!wizardHomepageUrlEl" in network_source
    assert "!wizardProxyUseDnsEl" in network_source
    assert "managedExtensionFields.filter(Boolean).forEach((input) => {" in extension_source
    assert "].filter(Boolean).forEach((input) => {" in extension_source
    assert "if (wizardNameEl && nameInput) {" in wizard_source
    assert "const profileTypeInput = documentRef.getElementById(\"profile-type\");" in wizard_source


def test_profile_route_navigation_warns_when_editor_is_dirty():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function isGuardedProfileRouteHref(anchorEl)" in source
    assert 'href.startsWith("#")' in source
    assert 'url.pathname === "/profiles" || url.pathname.startsWith("/profiles/")' in source
    assert "function isCrossTabProfileRouteIntent(event, anchorEl)" in source
    assert 'anchorEl?.target && anchorEl.target !== "_self"' in source
    assert "if (event.metaKey || event.ctrlKey || event.shiftKey) return true;" in source
    assert 'if (typeof event.button === "number" && event.button !== 0) return true;' in source
    assert "function confirmRouteNavigationIfDirty()" in source
    assert "if (!currentSnapshotState().dirty) return true;" in source
    assert 'windowRef.confirm(t("profiles.confirm_discard"))' in source
    assert "function guardProfileRouteNavigation(event)" in source
    assert "if (isCrossTabProfileRouteIntent(event, anchorEl)) return false;" in source
    assert "event.preventDefault();" in source
    assert "event.stopPropagation();" in source
    assert "if (guardProfileRouteNavigation(event)) return;" in source
    assert 'windowRef.addEventListener("beforeunload"' in source


def test_guided_advanced_handoffs_use_route_links_with_focus():
    root = Path(__file__).resolve().parents[1]
    ai_template = (root / "app" / "templates" / "profiles" / "_page_wizard_step_ai.html").read_text(
        encoding="utf-8"
    )
    export_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")

    assert 'data-workspace-scope-target="advanced"' not in ai_template
    assert 'data-workspace-scope-target="advanced"' not in export_template
    assert 'id="wizard-ai-providers-handoff"' not in ai_template
    assert 'id="wizard-ai-providers-open-advanced"' not in ai_template
    assert 'href="{{ settings_href }}&focus=settings-schema-shell-step-8"' in export_template
    assert 'target="_blank"' in export_template
    assert 'rel="noopener"' in export_template


def test_editor_mode_links_preserve_route_aware_returns_and_settings_focus():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_workspace.js"
    ).read_text(encoding="utf-8")

    assert "function normalizeSettingsModeFocusTarget(focusTarget)" in source
    assert "function normalizeJsonModeFocusTarget(focusTarget)" in source
    assert "function isJsonModeFocusTarget(focusTarget)" in source
    assert 'const returnPath = routeMode === "settings"' in source
    assert '`/profiles/${currentId}/settings${includeDeleted ? `?${includeDeletedSuffix}` : ""}`' in source
    assert '`/profiles/${currentId}/json${includeDeleted ? `?${includeDeletedSuffix}` : ""}`' in source
    assert '`/profiles/${currentId}/edit${includeDeleted ? `?${includeDeletedSuffix}` : ""}`' in source
    assert 'const settingsFocusTarget = normalizeSettingsModeFocusTarget(advancedFocusTarget);' in source
    assert 'return `/profiles/${currentId}/settings?${params.join("&")}`;' in source
    assert 'const jsonFocusTarget = normalizeJsonModeFocusTarget(advancedFocusTarget);' in source
    assert 'return `/profiles/${currentId}/json?${params.join("&")}`;' in source
    assert 'const advancedMode = routeMode === "settings"' in source
    assert 'active: routeMode === "settings" || (routeMode === "json" && advancedMode === "settings")' in source
    assert 'el.setAttribute("title", t("profiles.editor_chrome_save_first"));' in source
    assert 'el.removeAttribute("title");' in source


def test_unsaved_guided_route_explicitly_disables_settings_and_json_handoffs():
    client = make_test_client(app)
    response = client.get("/profiles/new")

    assert response.status_code == 200
    assert 'id="editor-mode-settings"' in response.text
    assert 'id="editor-mode-json"' in response.text
    assert response.text.count('aria-disabled="true"') >= 2
    assert response.text.count('title="Save the profile first to open All settings or JSON in a separate tab."') >= 2
    assert 'id="editor-mode-links-hint"' in response.text
    assert 'role="status"' in response.text
    assert 'Save the profile first to open All settings or JSON in a separate tab.' in response.text


def test_saved_guided_route_enables_settings_and_json_handoffs_after_first_save():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Saved Handoff Availability Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(f"/profiles/{profile_id}/edit")

    assert response.status_code == 200
    assert f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit"' in response.text
    assert f'href="/profiles/{profile_id}/json?focus=editor"' in response.text
    assert 'title="Save the profile first to open All settings or JSON in a separate tab."' not in response.text
    assert 'id="editor-mode-links-hint"' in response.text
    assert 'support-hidden' in response.text


def test_profile_settings_route_preserves_step8_json_handoff():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="JSON Step 8 Handoff Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/settings?return=/profiles/{profile_id}/edit&focus=settings-schema-shell-step-8"
    )

    assert response.status_code == 200
    assert (
        f'href="/profiles/{profile_id}/json?focus=raw"'
        in response.text
    )


def test_profile_json_route_maps_semantic_focus_back_to_settings():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="JSON Semantic Focus Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/settings&focus=deprecated:LegacyPolicy"
    )

    assert response.status_code == 200
    assert (
        f'href="/profiles/{profile_id}/settings?return=/profiles/{profile_id}/json&amp;focus=settings-schema-shell-step-8"'
        in response.text
    )


def test_ai_step_locales_describe_esr_empty_state():
    client = make_test_client(app)
    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()

    assert en_catalog["profiles.wizard_ai_esr_title"] == (
        "This schema does not support AI settings"
    )
    assert en_catalog["profiles.wizard_ai_esr_state"] == (
        "This schema does not support AI settings."
    )
    assert ru_catalog["profiles.wizard_ai_esr_title"] == (
        "Эта схема не поддерживает настройки ИИ"
    )
    assert ru_catalog["profiles.wizard_ai_esr_state"] == (
        "Эта схема не поддерживает настройки ИИ."
    )


def test_documentation_placeholders_are_removed_from_ui():
    root = Path(__file__).resolve().parents[1]
    macro_source = (
        root / "app" / "templates" / "profiles" / "_wizard_macros.html"
    ).read_text(encoding="utf-8")
    export_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    response = _profiles_page_response()
    client = make_test_client(app)
    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()
    en_catalog_text = json.dumps(en_catalog, ensure_ascii=False)
    ru_catalog_text = json.dumps(ru_catalog, ensure_ascii=False)

    removed_tokens = (
        "docs_placeholder",
        "wizard-doc-placeholder",
        "data-doc-placeholder",
        "render_doc_placeholder",
        "docs-guided-schema-shell",
        "docs-policy-boundaries",
        "Future docs",
        "Будущая документация",
    )
    for token in removed_tokens:
        assert token not in macro_source
        assert token not in export_template
        assert token not in css_source
        assert token not in response.text
        assert token not in en_catalog_text
        assert token not in ru_catalog_text


def test_wizard_step_navigation_scrolls_only_for_normal_navigation():
    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    settings_search_source = (
        root / "app" / "static" / "profiles_settings_search.js"
    ).read_text(encoding="utf-8")

    assert "function scrollWizardStepToTop(stepNumber)" in runtime_source
    assert 'targetEl.scrollIntoView({ behavior: "smooth", block: "start" });' in runtime_source
    assert "function navigateWizardStep(nextStep)" in runtime_source
    assert 'button.addEventListener("click", () => navigateWizardStep(button.dataset.step));' in runtime_source
    assert 'wizardPrevEl?.addEventListener("click", () => navigateWizardStep(getWizardStep() - 1));' in runtime_source
    assert "navigateWizardStep(getWizardStep() + 1);" in runtime_source
    assert "setWizardStep(nextStep);" in settings_search_source
    assert 'targetEl.scrollIntoView({ behavior: "smooth", block: "center" });' in settings_search_source
    assert "navigateWizardStep(" not in settings_search_source


def test_profile_library_narrow_viewport_contract():
    root = Path(__file__).resolve().parents[1]
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    template = (
        root / "app" / "templates" / "profiles" / "_page_library_workspace.html"
    ).read_text(encoding="utf-8")

    assert "@media (max-width: 560px)" in css_source
    assert ".library-panel-toolbar #create-profile-link" in css_source
    assert ".library-panel-toolbar #import-firefox-policies" in css_source
    assert ".library-table-shell" in css_source
    assert "overflow-x: hidden;" in css_source
    assert ".library-row-facts" in css_source
    assert "grid-template-areas:" in css_source
    assert ".library-row-meta::before" in css_source
    assert "content: attr(data-label);" in css_source
    assert ".library-row-updated::before" in css_source
    assert ".library-row-status-wrap::before" in css_source
    assert ".library-row-actions .button-base" in css_source
    assert ".library-import-feedback" in css_source
    assert 'id="search"' in template
    assert 'id="create-profile-link"' in template
    assert 'id="import-firefox-policies"' in template
    assert 'id="import-firefox-policies-status"' in template
    assert 'class="library-import-feedback"' in template


def test_visual_editor_narrow_viewport_contract():
    root = Path(__file__).resolve().parents[1]
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    workspace_template = (
        root / "app" / "templates" / "profiles" / "_page_workspace.html"
    ).read_text(encoding="utf-8")

    assert "@media (max-width: 560px)" in css_source
    assert ".wizard-header" in css_source
    assert ".wizard-settings-search-row" in css_source
    assert ".wizard-layout" in css_source
    assert ".wizard-stepper" in css_source
    assert "grid-auto-columns: minmax(142px, 76vw);" in css_source
    assert ".wizard-panel" in css_source
    assert "overflow-wrap: anywhere;" in css_source
    assert ".wizard-nav-actions" in css_source
    assert 'id="editor-mode-settings"' not in workspace_template
    assert 'id="workspace-scope-panel"' not in workspace_template


def test_compact_toolbar_narrow_viewport_contract():
    root = Path(__file__).resolve().parents[1]
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    header_template = (
        root / "app" / "templates" / "profiles" / "_page_header.html"
    ).read_text(encoding="utf-8")

    assert '<header class="compact-toolbar surface-panel fade-up mb-4">' in header_template
    assert ".compact-toolbar {" in css_source
    assert "max-inline-size: 100%;" in css_source
    assert "overflow-x: clip;" in css_source
    assert ".compact-toolbar-title {" in css_source
    assert "overflow-wrap: anywhere;" in css_source
    assert "font-size: 2.45rem;" in css_source
    assert "font-size: 1.9rem;" in css_source
    assert "font-size: 1.62rem;" in css_source
    assert ".compact-toolbar-control select.soft-input" in css_source
    assert "max-width: 100%;" in css_source
    assert "@media (max-width: 820px)" in css_source
    assert ".app-shell" in css_source
    assert "padding-inline: 12px;" in css_source
    assert "@media (max-width: 560px)" in css_source
    assert "padding-inline: 10px;" in css_source


def test_profile_ui_decorative_density_contract():
    root = Path(__file__).resolve().parents[1]
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    template_sources = "\n".join(
        (root / path).read_text(encoding="utf-8")
        for path in [
            "app/templates/profiles/_page_library_workspace.html",
            "app/templates/profiles/_page_settings_workspace.html",
            "app/templates/profiles/_page_json_workspace.html",
            "app/templates/profiles/_page_footer.html",
        ]
    )

    for token in (
        "rounded-[30px]",
        "rounded-[28px]",
        "rounded-[26px]",
        "rounded-[22px]",
        "shadow-soft",
        "shadow-inner",
    ):
        assert token not in template_sources

    assert "box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);" in css_source
    assert "backdrop-filter: blur(8px);" in css_source
    assert "border-radius: 16px;" in css_source
    assert ".panel-card {" in css_source
    assert ".button-base:hover {\n            border-color: rgba(15, 118, 110, 0.28);" in css_source
    assert "html[data-theme=\"dark\"] .workspace-scope-mode-card--active" in css_source
    assert "box-shadow: none;" in css_source


def test_profiles_css_custom_properties_are_declared():
    root = Path(__file__).resolve().parents[1]
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    used_tokens = set(re.findall(r"var\((--[a-zA-Z0-9_-]+)", css_source))
    declared_tokens = set(
        re.findall(r"^\s*(--[a-zA-Z0-9_-]+)\s*:", css_source, flags=re.MULTILINE)
    )

    assert used_tokens <= declared_tokens
    assert "--ink-muted" in declared_tokens
    assert "--ink-soft" in declared_tokens
    assert "--line-soft" in declared_tokens


def test_settings_workspace_hides_guided_step_numbers_and_centers_mapped_controls():
    root = Path(__file__).resolve().parents[1]
    settings_workspace = (
        root / "app" / "templates" / "profiles" / "_page_settings_workspace.html"
    ).read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert '<div class="section-kicker">{{ step.step }}</div>' not in settings_workspace
    assert "guided_source_section_ids" not in settings_workspace
    assert "guided_source_shell_steps" not in settings_workspace
    assert "{% for step in wizard_steps if step.step > 1 %}" not in settings_workspace
    assert "{% for category in all_settings_categories %}" in settings_workspace
    assert 'id="settings-category-{{ category.id }}"' in settings_workspace
    assert 'data-settings-category-link="{{ category.id }}"' in settings_workspace
    assert 'id="all-settings-list-panel"' in settings_workspace
    assert 'id="all-settings-review-panel"' in settings_workspace
    assert 'id="all-settings-review-summary"' in settings_workspace
    assert 'id="all-settings-review-actions"' in settings_workspace
    assert 'id="all-settings-list-summary"' in settings_workspace
    assert 'id="all-settings-list"' in settings_workspace
    assert 'id="all-settings-detail-panel"' in settings_workspace
    assert 'id="all-settings-add-preference"' in settings_workspace
    assert '("all", "profiles.settings_filter_all")' in settings_workspace
    assert '("configured", "profiles.settings_filter_configured")' in settings_workspace
    assert '("available", "profiles.settings_filter_available")' in settings_workspace
    assert '("guided-covered", "profiles.settings_filter_guided_covered")' in settings_workspace
    assert '("all-settings-only", "profiles.settings_filter_all_settings_only")' in settings_workspace
    assert '("invalid", "profiles.settings_filter_invalid")' in settings_workspace
    assert '("deprecated", "profiles.settings_filter_deprecated")' in settings_workspace
    assert '("raw", "profiles.settings_filter_raw")' in settings_workspace
    assert '("unknown", "profiles.settings_filter_unknown")' in settings_workspace
    assert 'profiles_all_settings_list.js' in (
        root / "app" / "templates" / "profiles" / "_page_document.html"
    ).read_text(encoding="utf-8")
    assert 'profiles_all_settings_detail.js' in (
        root / "app" / "templates" / "profiles" / "_page_document.html"
    ).read_text(encoding="utf-8")
    settings_search_source = (
        root / "app" / "static" / "profiles_settings_search.js"
    ).read_text(encoding="utf-8")
    all_settings_list_source = (
        root / "app" / "static" / "profiles_all_settings_list.js"
    ).read_text(encoding="utf-8")
    all_settings_detail_source = (
        root / "app" / "static" / "profiles_all_settings_detail.js"
    ).read_text(encoding="utf-8")
    runtime_source = (
        root / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")
    bootstrap_core_source = (
        root / "app" / "static" / "profiles_bootstrap_core.js"
    ).read_text(encoding="utf-8")
    assert "buildAllSettingsInventoryEntries" in settings_search_source
    assert "all-settings-entry:${entry.kind}:${entry.id}" in settings_search_source
    assert "findAllSettingsEntryTarget?.(normalizedTarget)" in settings_search_source
    assert 'entry.rawFallback ? t("profiles.settings_filter_raw")' in settings_search_source
    assert "getSearchEntries" in all_settings_list_source
    assert "findTarget" in all_settings_list_source
    assert "data-settings-entry-raw" in all_settings_list_source
    assert "const sourceState = readWizardSchemaSource();" in all_settings_detail_source
    assert 'documentRef.getElementById("mode")?.value || "json"' in all_settings_detail_source
    assert "onDocumentChange(normalized);" in all_settings_detail_source
    assert "getAllSettingsSearchEntries: () => allSettingsList.getSearchEntries()" in bootstrap_core_source
    assert "handleAllSettingsDocumentChange = () =>" in bootstrap_core_source
    assert "settingsSearch.buildIndex();" in bootstrap_core_source
    assert "workspace.updateActionState();" in bootstrap_core_source
    assert "buildWizardSettingsSearchIndex();" in runtime_source
    assert "renderWizardSettingsSearchResults();" in runtime_source
    assert ".wizard-search-engine-preset {" in css_source
    assert ".button-base.wizard-search-engine-preset {" in css_source
    assert "display: flex;" in css_source
    assert "flex-direction: column;" in css_source
    assert "align-items: flex-start;" in css_source
    assert "justify-content: center;" in css_source


def test_profile_library_actions_use_editor_route_links():
    root = Path(__file__).resolve().parents[1]
    template = (root / "app" / "templates" / "profiles" / "_page_library_workspace.html").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )

    assert 'id="create-profile-link"' in template
    assert 'href="/profiles/new"' in template
    assert 'target="_blank"' in template
    assert 'rel="noopener"' in template
    assert 'const editHref = `/profiles/${profile.id}/edit`;' in workspace_source
    assert '<a class="library-row-title-button" href="${editHref}" target="_blank" rel="noopener">' in workspace_source
    assert (
        '<a class="button-base library-row-open-button ${selected ? "library-row-open-button--selected" : ""}" href="${editHref}" target="_blank" rel="noopener">'
        in workspace_source
    )
    assert "loadProfile(profile.id)" not in workspace_source


def test_visual_editor_save_uses_revision_token_contract():
    root = Path(__file__).resolve().parents[1]
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    data_source = (root / "app" / "static" / "profiles_data.js").read_text(
        encoding="utf-8"
    )

    assert "function buildExpectedRevisionPayload()" in workspace_source
    assert "const revision = Number(getCurrentProfile()?.revision);" in workspace_source
    assert "return { expected_revision: revision };" in workspace_source
    assert "function buildUpdatePayload(form, parsedFlags, compliancePayload, options = {})" in workspace_source
    assert "includeExpectedRevision ? buildExpectedRevisionPayload() : {}" in workspace_source
    assert "function isRevisionConflictError(error)" in workspace_source
    assert "return Number(error?.status) === 409;" in workspace_source
    assert 't("profiles.status_revision_conflict")' in workspace_source
    assert 'setValidationPreview(message, "error");' in workspace_source
    assert "error.status = res.status;" in data_source
    assert "error.detail = payload.detail;" in data_source
    assert "if (!res.ok) throw await profileRequestError(res);" in data_source


def test_advanced_editor_save_uses_revision_token_contract():
    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    bootstrap_source = (
        root / "app" / "static" / "profiles_bootstrap_core.js"
    ).read_text(encoding="utf-8")
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )

    assert '(routeMode === "edit" || routeMode === "settings" || routeMode === "json") && editingProfileId' in runtime_source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in runtime_source
    assert "setAdvancedHandoffContext(null);" in runtime_source
    assert "applyAdvancedFocusTarget(focusTarget);" in runtime_source
    assert "saveButtonEl.addEventListener(\"click\", saveCurrent);" in runtime_source
    assert "saveCurrent();" in runtime_source
    assert "setSaveCurrent(workspace.saveCurrent);" in bootstrap_source
    assert "const revision = Number(getCurrentProfile()?.revision);" in workspace_source
    assert "includeExpectedRevision ? buildExpectedRevisionPayload() : {}" in workspace_source
    assert "if (isRevisionConflictError(e))" in workspace_source


def test_guided_route_no_longer_exposes_workspace_scope_switch_contract():
    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    workspace_template = (
        root / "app" / "templates" / "profiles" / "_page_workspace.html"
    ).read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )

    assert 'id="workspace-scope-guided"' not in workspace_template
    assert 'id="workspace-scope-advanced"' not in workspace_template
    assert 'id="workspace-scope-summary"' not in workspace_template
    assert "bpm-workspace-scope" not in runtime_source
    assert "applyWorkspaceScope(" not in runtime_source
    assert 'body[data-profiles-template-kind="editor"] [data-workspace-scope-panel="advanced"]' in css_source
    assert 'body[data-profiles-template-kind="advanced"] [data-workspace-scope-panel="guided"]' in css_source


def test_guided_route_uses_headless_editor_contract_without_monaco_surface():
    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    workspace_template = (
        root / "app" / "templates" / "profiles" / "_page_workspace.html"
    ).read_text(encoding="utf-8")

    assert "function createHeadlessEditorAdapter(initialValue = \"{}\")" in runtime_source
    assert 'const needsEditorRuntime = templateKind === "editor" || templateKind === "settings" || templateKind === "json";' in runtime_source
    assert 'if (!editorEl && !needsEditorRuntime) {' in runtime_source
    assert ': createHeadlessEditorAdapter("{}");' in runtime_source
    assert "{% if profiles_template_kind == 'editor' %}" in workspace_template


def test_settings_route_uses_visible_catalog_sections_without_hidden_wizard_backing():
    root = Path(__file__).resolve().parents[1]
    settings_shell = (
        root / "app" / "templates" / "profiles" / "_settings_shell.html"
    ).read_text(encoding="utf-8")
    settings_workspace = (
        root / "app" / "templates" / "profiles" / "_page_settings_workspace.html"
    ).read_text(encoding="utf-8")
    settings_search_source = (
        root / "app" / "static" / "profiles_settings_search.js"
    ).read_text(encoding="utf-8")
    catalogs_source = (root / "app" / "static" / "profiles_catalogs.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    wizard_flow_source = (
        root / "app" / "static" / "profiles_wizard_flow.js"
    ).read_text(encoding="utf-8")

    assert '_page_settings_preference_support.html' in settings_shell
    assert '_page_settings_wizard_backing.html' not in settings_shell
    assert 'data-settings-nav' in settings_workspace
    assert 'data-settings-jump-target="{{ control.target }}"' in settings_workspace
    assert 'data-settings-target="pref-section:{{ preference_section.id }}"' in settings_workspace
    assert 'id="wizard-preferences-{{ preference_section.id }}-presets"' in settings_workspace
    assert "settingsTargetAliases" in catalogs_source
    assert "function resolveTargetAlias(target)" in settings_search_source
    assert 'shellPolicyTargetByAlias[normalizedTarget]' in settings_search_source
    assert 'documentRef.querySelector(`[data-settings-target="${resolveTargetAlias(normalizedTarget)}"]`)' in settings_search_source
    assert 'wizardSearchEngineAddButtonEl?.addEventListener("click"' in runtime_source
    assert "if (!hasWizardUi) {" in wizard_flow_source
    assert "wizardSummaryNameEl && (wizardSummaryNameEl.textContent = form.name || \"—\");" in wizard_flow_source


def test_shared_save_conflict_ui_contract():
    root = Path(__file__).resolve().parents[1]
    command_deck = (
        root / "app" / "templates" / "profiles" / "_page_command_deck.html"
    ).read_text(encoding="utf-8")
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )

    assert 'id="save-conflict-panel"' in command_deck
    assert 'role="alert"' in command_deck
    assert 'id="save-conflict-reload"' in command_deck
    assert 'id="save-conflict-save-copy"' in command_deck
    assert 'id="save-conflict-overwrite"' in command_deck
    assert 'data-i18n="profiles.conflict_overwrite"' in command_deck
    assert 'saveConflictPanelEl: byId("save-conflict-panel")' in dom_source
    assert "let saveConflictState = null;" in workspace_source
    assert "function showSaveConflictState(error)" in workspace_source
    assert "saveConflictReloadEl?.addEventListener(\"click\"" in workspace_source
    assert "saveConflictSaveCopyEl?.addEventListener(\"click\"" in workspace_source
    assert "saveConflictOverwriteEl?.addEventListener(\"click\"" in workspace_source
    assert "await saveCurrent({ overwriteRevision: true });" in workspace_source
    assert "buildUpdatePayload(form, parsedFlags, compliancePayload" in workspace_source


def test_json_editor_chrome_exposes_format_action_without_command_deck():
    root = Path(__file__).resolve().parents[1]
    editor_chrome = (
        root / "app" / "templates" / "profiles" / "_page_editor_chrome.html"
    ).read_text(encoding="utf-8")
    command_deck = (
        root / "app" / "templates" / "profiles" / "_page_command_deck.html"
    ).read_text(encoding="utf-8")
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )

    assert '{% if profiles_route_mode == "json" %}' in editor_chrome
    assert 'id="format"' in editor_chrome
    assert 'id="command-deck"' not in command_deck
    assert 'formatButtonEl?.addEventListener("click", () => {' in runtime_source
    assert 'softDeleteButtonEl?.addEventListener("click", doSoftDelete);' in runtime_source
    assert 'hardDeleteButtonEl?.addEventListener("click", doHardDelete);' in runtime_source
    assert 'restoreButtonEl?.addEventListener("click", doRestore);' in runtime_source
    assert 'resetLibraryButtonEl?.addEventListener("click", doResetLibrary);' in runtime_source


def test_conflict_save_as_copy_creates_new_profile_contract():
    root = Path(__file__).resolve().parents[1]
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )

    assert "async function saveConflictAsCopy()" in workspace_source
    assert "const copyName = buildConflictCopyName(form);" in workspace_source
    assert "function buildCreatePayload(form, parsedFlags, compliancePayload, options = {})" in workspace_source
    assert "buildCreatePayload(form, parsedFlags, compliancePayload, { name: copyName })" in workspace_source
    assert "const created = await createProfile(" in workspace_source
    assert "await loadProfile(created.id, { skipConfirm: true });" in workspace_source
    assert 't("profiles.conflict_copy_created").replace("{name}", created.name)' in workspace_source
    assert "saveConflictSaveCopyEl?.addEventListener(\"click\", async () =>" in workspace_source
    assert "await saveConflictAsCopy();" in workspace_source


def test_profile_routes_use_specific_page_titles():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Finance Laptop Baseline"),
    )
    profile_id = create_response.json()["id"]

    library_response = client.get("/profiles")
    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")

    assert "<title>Library — Browser Policy Manager</title>" in library_response.text
    assert "<title>New profile draft — Guided editor — Browser Policy Manager</title>" in new_response.text
    assert (
        "<title>Finance Laptop Baseline — Guided editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert (
        advanced_response.headers["location"] == f"/profiles/{profile_id}/json"
    )
