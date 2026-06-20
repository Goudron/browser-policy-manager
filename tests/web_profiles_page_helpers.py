# ruff: noqa: F401
import asyncio
import importlib
import json
import re
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from types import SimpleNamespace

from bs4 import BeautifulSoup
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from app.core.config import get_settings
from app.main import app
from app.web.firefox_wizard_steps import get_wizard_steps
from tests.support import assert_contains_all, build_profile_payload, make_test_client
from tools import build_profiles_css

REPO_ROOT = Path(__file__).resolve().parents[1]


@cache
def source_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def static_source(filename: str) -> str:
    return source_text(f"app/static/{filename}")


def template_source(filename: str) -> str:
    return source_text(f"app/templates/profiles/{filename}")


def css_source() -> str:
    return static_source("profiles.css")


def css_block(selector: str) -> str:
    source = css_source()
    block_start = source.index(f"{selector} {{")
    block_end = source.index("}", block_start)
    return source[block_start:block_end]


def assert_source_contains_all(source: str, snippets: tuple[str, ...]) -> None:
    assert_contains_all(source, snippets)


def assert_source_excludes_all(source: str, snippets: tuple[str, ...]) -> None:
    unexpected = [snippet for snippet in snippets if snippet in source]
    assert not unexpected, "Unexpected source snippets found: " + ", ".join(
        repr(snippet) for snippet in unexpected
    )


def assert_sources_exclude_all(sources: tuple[str, ...], snippets: tuple[str, ...]) -> None:
    for source in sources:
        assert_source_excludes_all(source, snippets)


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
    'id="wizard-bookmarks-open-settings"',
    'id="wizard-bookmarks-configured-actions"',
    'id="wizard-bookmarks-links-jump"',
    'id="wizard-bookmarks-folders-jump"',
    'id="wizard-bookmarks-nested-jump"',
    'id="wizard-permissions-card"',
    'id="wizard-cookies-card"',
)

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

@cache
def _profiles_page_response():
    client = make_test_client(app)
    return client.get("/profiles/new")

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
    assert locale_json["profiles.workspace_scope_settings"] == "All settings"
    assert locale_json["profiles.workspace_scope_current_label"] == "Current mode"
    assert locale_json["profiles.workspace_scope_guided_title"] == (
        "Best for most profile work"
    )
    assert locale_json["profiles.workspace_scope_settings_title"] == (
        "Only when Guided editor is not enough"
    )
    assert locale_json["profiles.settings_context_title"] == "Continue in All settings"
    assert locale_json["profiles.settings_context_empty_title"] == (
        "Starting here without a step handoff?"
    )
    assert locale_json["profiles.settings_context_action_editor"] == "Open full policies.json"
    assert locale_json["profiles.settings_utility_title"] == "All settings workflow"
    assert locale_json["profiles.settings_utility_editor_body"] == (
        "Use the full Firefox policies.json when you already know the lower-level keys you need to manage."
    )
    assert locale_json["profiles.json_downloads_title"] == "Download policies.json"
    assert locale_json["profiles.editor_section_hint"] == (
        "Edit the full Firefox policies.json document here when Guided editor and All settings are not enough."
    )
    assert locale_json["profiles.json_review_save_title"] == "Latest edits"
    assert locale_json["profiles.json_review_download_title"] == "Ready to download"
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
    assert locale_json["profiles.library_column_context"] == "Note"
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
    assert locale_json["profiles.compare_route_title"] == "Compare profile settings"
    assert locale_json["profiles.compare_action"] == "Compare here"
    assert locale_json["profiles.clone_handoff_title"] == (
        "Recommended checks for this derived draft"
    )
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
    assert locale_json["profiles.wizard_ai_controls_title"] == "Firefox 152 AI policy controls"
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
    assert locale_json["profiles.wizard_review_filter_settings"] == "Outside Guided editor"
    assert locale_json["profiles.wizard_review_filter_all"] == "All"
    assert locale_json["profiles.wizard_review_empty_changed"] == "No changed items here yet."
    assert locale_json["profiles.wizard_review_empty_settings"] == (
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
    assert locale_json["profiles.workspace_scope_settings"] == "Все настройки"
    assert locale_json["profiles.workspace_scope_current_label"] == "Текущий режим"
    assert locale_json["profiles.workspace_scope_guided_title"] == (
        "Лучший путь для большей части работы"
    )
    assert locale_json["profiles.workspace_scope_settings_title"] == (
        "Только когда Пошагового редактора уже недостаточно"
    )
    assert locale_json["profiles.settings_context_title"] == "Продолжение во Всех настройках"
    assert locale_json["profiles.settings_context_empty_title"] == (
        "Открыли это место без перехода из шага?"
    )
    assert locale_json["profiles.settings_context_action_editor"] == (
        "Открыть полный policies.json"
    )
    assert locale_json["profiles.settings_utility_title"] == (
        "Работа во Всех настройках"
    )
    assert locale_json["profiles.settings_utility_editor_body"] == (
        "Используйте полный Firefox policies.json, когда уже знаете, какими низкоуровневыми ключами нужно управлять."
    )
    assert locale_json["profiles.json_downloads_title"] == "Скачать policies.json"
    assert locale_json["profiles.editor_section_hint"] == (
        "Редактируйте здесь полный Firefox policies.json, когда Пошагового редактора и Всех настроек уже недостаточно."
    )
    assert locale_json["profiles.json_review_save_title"] == "Последние правки"
    assert locale_json["profiles.json_review_download_title"] == (
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
    assert locale_json["profiles.library_column_context"] == "Заметка"
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
    assert locale_json["profiles.compare_route_title"] == "Сравнить настройки профилей"
    assert locale_json["profiles.compare_action"] == "Сравнить здесь"
    assert locale_json["profiles.clone_handoff_title"] == (
        "Что обычно стоит проверить в производной копии"
    )
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
    assert locale_json["profiles.wizard_review_filter_settings"] == "Вне Пошагового редактора"
    assert locale_json["profiles.wizard_review_filter_all"] == "Все"
    assert locale_json["profiles.wizard_review_empty_changed"] == "Здесь пока нет изменённых пунктов."
    assert locale_json["profiles.wizard_review_empty_settings"] == (
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
    assert locale_json["profiles.wizard_ai_controls_title"] == "Политики ИИ Firefox 152"
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

__all__ = [name for name in globals() if not name.startswith("__")]
