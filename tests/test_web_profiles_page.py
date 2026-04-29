import asyncio
import importlib
import re
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from fastapi.responses import HTMLResponse
from starlette.requests import Request

from app.core.config import get_settings
from app.main import app
from tests.support import assert_contains_all, build_profile_payload, make_test_client

PROFILES_PAGE_EDITOR_TOKENS = (
    "Browser profile manager",
    "Profile library",
    "Advanced profile document",
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
    'id="workspace-scope-guided"',
    'id="workspace-scope-advanced"',
    'id="workspace-scope-summary"',
    'id="workspace-scope-summary-title"',
    'id="workspace-scope-summary-copy"',
    'id="workspace-scope-guided-card"',
    'id="workspace-scope-advanced-card"',
    'id="advanced-handoff-panel"',
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
    'id="wizard-step-4-default-search"',
    'id="wizard-step-4-managed-engines"',
    'id="wizard-step-4-suggestions"',
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
    'data-search-engine-preset="docs_portal"',
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
    'profiles.wizard_step_six_index_title',
    'id="wizard-step-6-accounts"',
    'id="wizard-step-6-language"',
    'id="wizard-step-6-extensions"',
    'id="wizard-step-6-bookmarks"',
    'id="wizard-step-6-websites"',
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
    'id="wizard-ai-providers-open-advanced"',
    'id="wizard-ai-providers-handoff"',
    'id="wizard-ai-providers-section-status"',
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
    'id="wizard-export-guided-group-network"',
    'id="wizard-export-guided-group-home"',
    'id="wizard-export-guided-group-search"',
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
    'id="dock-state-summary"',
    'id="dock-state-title"',
    'id="dock-state-copy"',
    'id="advanced-context-panel"',
    'id="advanced-context-step"',
    'id="advanced-context-copy"',
    'id="advanced-context-list"',
    'id="advanced-context-empty"',
    'id="advanced-context-return"',
    'data-advanced-start-action="details"',
    'data-advanced-start-action="editor"',
    'data-advanced-start-action="validate"',
    'id="advanced-utility-details"',
    'id="advanced-utility-editor"',
    'id="advanced-utility-validate"',
    'id="advanced-download-strip"',
    'id="advanced-review-strip"',
    'id="advanced-review-save-state"',
    'id="advanced-review-validation-state"',
    'id="advanced-review-download-state"',
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
    "Guided setup",
    "Advanced editor",
    "Save, validate, download",
    "Download policies.json",
    "Latest edits",
    "Final validation",
    "Ready to download",
    "About this profile",
    "What people will notice",
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
    return client.get("/profiles")


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
    assert locale_json["profiles.docs_placeholder_status"] == "Docs placeholder"
    assert locale_json["profiles.docs_placeholder_advanced_title"] == "Advanced editor guide"
    assert locale_json["profiles.docs_placeholder_policy_title"] == "Policy reference"
    assert locale_json["profiles.docs_placeholder_boundaries_title"] == "Boundary notes"
    assert locale_json["profiles.wizard_context_existing"].startswith("You are editing")
    assert locale_json["profiles.wizard_step_one"] == "Start"
    assert locale_json["profiles.wizard_step_two"] == "Network & browser basics"
    assert locale_json["profiles.wizard_step_four"] == "Search & navigation"
    assert locale_json["profiles.wizard_step_five"] == "Privacy & security"
    assert locale_json["profiles.wizard_step_six"] == "Accounts, languages, add-ons & sites"
    assert locale_json["profiles.wizard_step_seven"] == "AI & smart features"
    assert locale_json["profiles.wizard_step_eight"] == "Review & export"
    assert locale_json["profiles.workspace_scope_guided"] == "Guided setup"
    assert locale_json["profiles.workspace_scope_advanced"] == "Advanced editor"
    assert locale_json["profiles.workspace_scope_current_label"] == "Current mode"
    assert locale_json["profiles.workspace_scope_guided_title"] == (
        "Best for most profile work"
    )
    assert locale_json["profiles.workspace_scope_advanced_title"] == (
        "Only when guided setup is not enough"
    )
    assert locale_json["profiles.advanced_context_title"] == "Continue in Advanced editor"
    assert locale_json["profiles.advanced_context_return"] == "Back to this guided step"
    assert locale_json["profiles.advanced_context_empty_title"] == (
        "Starting here without a step handoff?"
    )
    assert locale_json["profiles.advanced_context_action_editor"] == "Open full policies.json"
    assert locale_json["profiles.advanced_utility_title"] == "Advanced workflow"
    assert locale_json["profiles.advanced_utility_editor_body"] == (
        "Use the full Firefox policies.json when you already know the lower-level keys you need to manage."
    )
    assert locale_json["profiles.advanced_downloads_title"] == "Download policies.json"
    assert locale_json["profiles.editor_section_hint"] == (
        "Edit the full Firefox policies.json document here when guided setup is not enough."
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
        "Review {count} CIS conflict(s) where the base scenario stayed in place."
    )
    assert locale_json["profiles.wizard_cis_review_manual_title"] == (
        "CIS manual review: {path}"
    )
    assert locale_json["profiles.wizard_cis_exceptions_count"] == (
        "{count} CIS exception(s) need notes."
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
    assert locale_json["profiles.dock_group_primary"] == "Main actions"
    assert locale_json["profiles.reload"] == "Refresh list"
    assert locale_json["profiles.import_firefox_policies_json"] == "Import policies.json"
    assert locale_json["profiles.import_firefox_policies_ready"].startswith("Choose a Firefox")
    assert locale_json["profiles.status_import_firefox_policies_done"] == "Imported {name}."
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
    assert locale_json["profiles.wizard_ai_controls_title"] == "Firefox 150 AI policy controls"
    assert locale_json["profiles.wizard_general_policy_section_state_download_prompt_on"] == (
        "Ask where to save downloads"
    )
    assert locale_json["profiles.wizard_settings_map_label"] == "Firefox Settings areas"
    assert locale_json["profiles.wizard_settings_covered_title"] == "Settings covered"
    assert locale_json["profiles.wizard_preferences_covered_title"] == "Advanced preference coverage"
    assert locale_json["profiles.wizard_preferences_general_handoff_title"] == (
        "Advanced General preferences"
    )
    assert locale_json["profiles.wizard_preferences_search_handoff_title"] == (
        "Advanced Search preferences"
    )
    assert locale_json["profiles.wizard_preferences_handoff_count"] == "{count} configured"
    assert locale_json["profiles.wizard_settings_controls_label"] == "What you can change here"
    assert locale_json["profiles.wizard_settings_filter_all"] == "All"
    assert locale_json["profiles.wizard_settings_search_label"] == "Find a setting"
    assert locale_json["profiles.wizard_settings_search_clear"] == "Clear"
    assert locale_json["profiles.sort_updated_at"] == "Updated"
    assert locale_json["profiles.order_desc"] == "DESC"
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
    assert locale_json["profiles.wizard_step_four_index_title"] == "Search step map"
    assert locale_json["profiles.wizard_step_four_index_engines"] == "Managed engines"
    assert locale_json["profiles.wizard_step_six_index_title"] == "Step map"
    assert locale_json["profiles.wizard_step_six_index_extensions"] == "Extensions"
    assert locale_json["profiles.wizard_step_six_index_websites"] == "Websites"
    assert locale_json["profiles.wizard_disclosure_show"] == "Show details"
    assert locale_json["profiles.wizard_disclosure_hide"] == "Hide details"
    assert locale_json["profiles.wizard_review_filter_changed"] == "Changed"
    assert locale_json["profiles.wizard_review_filter_attention"] == "Needs attention"
    assert locale_json["profiles.wizard_review_filter_advanced"] == "Advanced-only"
    assert locale_json["profiles.wizard_review_filter_all"] == "All"
    assert locale_json["profiles.wizard_review_empty_changed"] == "No changed items here yet."
    assert locale_json["profiles.wizard_review_empty_advanced"] == "No advanced-only items here right now."
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
    assert locale_json["profiles.wizard_privacy_review_title"] == (
        "How strict site access will be"
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
        "{count} remaining"
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
    assert locale_json["profiles.wizard_export_section_changes_title"] == "What changed"
    assert locale_json["profiles.wizard_export_section_technical_title"] == (
        "Technical details"
    )
    assert locale_json["profiles.wizard_export_title"] == "Save, validate, download"
    assert locale_json["profiles.wizard_export_workspace_state"] == "Latest edits"
    assert locale_json["profiles.wizard_export_validation_state"] == "Final validation"
    assert locale_json["profiles.wizard_export_ready_state"] == "Ready to download"
    assert locale_json["profiles.wizard_export_ready_title"] == "Download policies.json"
    assert locale_json["profiles.wizard_export_basics_title"] == "About this profile"
    assert locale_json["profiles.wizard_export_guided_summary_title"] == (
        "What people will notice"
    )
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
    assert locale_json["profiles.wizard_ai_providers_state_empty"] == (
        "No provider or model policy fields exist in the current Firefox 150 template."
    )
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
    assert locale_json["profiles.wizard_extensions_advanced_count"] == "{count} configured"
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
    assert locale_json["profiles.docs_placeholder_status"] == "Место для документации"
    assert locale_json["profiles.docs_placeholder_advanced_title"] == "Руководство по расширенному редактору"
    assert locale_json["profiles.docs_placeholder_policy_title"] == "Справочник политик"
    assert locale_json["profiles.docs_placeholder_boundaries_title"] == "Границы мастера"
    assert locale_json["profiles.wizard_step_one"] == "Старт"
    assert locale_json["profiles.wizard_step_two"] == "Сеть и базовые настройки"
    assert locale_json["profiles.wizard_step_four"] == "Поиск и навигация"
    assert locale_json["profiles.wizard_step_five"] == "Приватность и защита"
    assert locale_json["profiles.wizard_step_six"] == "Аккаунты, языки, дополнения и сайты"
    assert locale_json["profiles.wizard_step_seven"] == "ИИ и умные функции"
    assert locale_json["profiles.wizard_step_eight"] == "Проверка и выгрузка"
    assert locale_json["profiles.workspace_scope_guided"] == "Пошаговая настройка"
    assert locale_json["profiles.workspace_scope_advanced"] == "Расширенный редактор"
    assert locale_json["profiles.workspace_scope_current_label"] == "Текущий режим"
    assert locale_json["profiles.workspace_scope_guided_title"] == (
        "Лучший путь для большей части работы"
    )
    assert locale_json["profiles.workspace_scope_advanced_title"] == (
        "Только когда Пошаговой настройки уже недостаточно"
    )
    assert locale_json["profiles.advanced_context_title"] == "Продолжение в расширенном редакторе"
    assert locale_json["profiles.advanced_context_return"] == "Вернуться к этому шагу"
    assert locale_json["profiles.advanced_context_empty_title"] == (
        "Открыли это место без перехода из шага?"
    )
    assert locale_json["profiles.advanced_context_action_editor"] == (
        "Открыть полный policies.json"
    )
    assert locale_json["profiles.advanced_utility_title"] == (
        "Работа в расширенном редакторе"
    )
    assert locale_json["profiles.advanced_utility_editor_body"] == (
        "Используйте полный Firefox policies.json, когда уже знаете, какими низкоуровневыми ключами нужно управлять."
    )
    assert locale_json["profiles.advanced_downloads_title"] == "Скачать policies.json"
    assert locale_json["profiles.editor_section_hint"] == (
        "Редактируйте здесь полный Firefox policies.json, когда Пошаговой настройки уже недостаточно."
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
    assert locale_json["profiles.dock_group_primary"] == "Главные действия"
    assert locale_json["profiles.reload"] == "Обновить список"
    assert locale_json["profiles.import_firefox_policies_json"] == "Импортировать policies.json"
    assert locale_json["profiles.import_firefox_policies_ready"].startswith("Выберите файл")
    assert locale_json["profiles.status_import_firefox_policies_done"] == (
        "Импортирован профиль «{name}»."
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
    assert locale_json["profiles.wizard_preferences_covered_title"] == "Покрытие расширенных параметров"
    assert locale_json["profiles.wizard_preferences_general_handoff_title"] == (
        "Расширенные параметры раздела «Основные»"
    )
    assert locale_json["profiles.wizard_preferences_search_handoff_title"] == (
        "Расширенные параметры поиска"
    )
    assert locale_json["profiles.wizard_preferences_handoff_count"] == "Настроено: {count}"
    assert locale_json["profiles.wizard_settings_controls_label"] == "Что можно изменить здесь"
    assert locale_json["profiles.wizard_settings_filter_all"] == "Все"
    assert locale_json["profiles.wizard_settings_search_label"] == "Найти настройку"
    assert locale_json["profiles.wizard_settings_search_clear"] == "Очистить"
    assert locale_json["profiles.sort_updated_at"] == "Обновлено"
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
    assert locale_json["profiles.wizard_step_four_index_title"] == "Карта шага поиска"
    assert locale_json["profiles.wizard_step_four_index_engines"] == "Управляемые поисковики"
    assert locale_json["profiles.wizard_step_six_index_title"] == "Карта шага"
    assert locale_json["profiles.wizard_step_six_index_extensions"] == "Дополнения"
    assert locale_json["profiles.wizard_step_six_index_websites"] == "Сайты"
    assert locale_json["profiles.wizard_disclosure_show"] == "Показать детали"
    assert locale_json["profiles.wizard_disclosure_hide"] == "Скрыть детали"
    assert locale_json["profiles.wizard_review_filter_changed"] == "Изменённые"
    assert locale_json["profiles.wizard_review_filter_attention"] == "Требуют внимания"
    assert locale_json["profiles.wizard_review_filter_advanced"] == "Только расширенный редактор"
    assert locale_json["profiles.wizard_review_filter_all"] == "Все"
    assert locale_json["profiles.wizard_review_empty_changed"] == "Здесь пока нет изменённых пунктов."
    assert locale_json["profiles.wizard_review_empty_advanced"] == "Сейчас здесь нет пунктов только для расширенного редактора."
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
    assert locale_json["profiles.wizard_privacy_review_title"] == (
        "Насколько строгими будут правила для сайтов"
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
    assert locale_json["profiles.wizard_search_preset_docs_title"] == "Портал документации"
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
    assert locale_json["profiles.wizard_home_step_summary_title"] == "Итог настройки Home"
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
        "Управляемый allowlist"
    )
    assert locale_json["profiles.wizard_extensions_governance_curated_title"] == (
        "Курируемая раскатка"
    )
    assert locale_json["profiles.wizard_extensions_governance_title"] == (
        "Сценарий управления дополнениями"
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
    assert locale_json["profiles.wizard_export_section_changes_title"] == "Что изменилось"
    assert locale_json["profiles.wizard_export_section_technical_title"] == (
        "Технические детали"
    )
    assert locale_json["profiles.wizard_export_title"] == "Сохранить, проверить, скачать"
    assert locale_json["profiles.wizard_export_workspace_state"] == "Последние правки"
    assert locale_json["profiles.wizard_export_validation_state"] == "Финальная проверка"
    assert locale_json["profiles.wizard_export_ready_state"] == "Готово к скачиванию"
    assert locale_json["profiles.wizard_export_ready_title"] == "Скачать policies.json"
    assert locale_json["profiles.wizard_export_basics_title"] == "О профиле"
    assert locale_json["profiles.wizard_export_guided_summary_title"] == (
        "Что заметят пользователи"
    )
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
        "Открыть расширенные"
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
    assert locale_json["profiles.wizard_ai_controls_title"] == "Политики ИИ Firefox 150"
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
        "Контролов: {controls} • Правил хостов: {rules}"
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
        "Что сознательно остаётся в расширенном редакторе"
    )
    assert locale_json["profiles.wizard_export_drilldown_title"] == (
        "Детальный технический разбор"
    )
    assert locale_json["profiles.wizard_certificates_state_with_roots"] == (
        "Установлено: {count} • Включены корпоративные корневые сертификаты"
    )
    assert locale_json["profiles.wizard_doh_state_provider"] == "Свой поставщик"
    assert locale_json["profiles.wizard_ai_providers_state_empty"] == (
        "В текущем шаблоне Firefox 150 нет полей политик для поставщиков или моделей."
    )
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
    assert 'data-profiles-route-mode="library"' in response.text
    assert 'data-profiles-template-kind="library"' in response.text
    assert_contains_all(response.text, PROFILES_PAGE_EDITOR_TOKENS)
    assert 'id="download-json"' not in response.text
    assert 'id="download-yaml"' not in response.text
    assert 'id="wizard-export-json"' not in response.text
    assert 'id="wizard-export-yaml"' not in response.text


def test_firefox_policies_import_and_final_export_ui_contract():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert 'id="import-firefox-policies"' in response.text
    assert 'id="import-firefox-policies-file"' in response.text
    assert 'accept=".json,application/json"' in response.text
    assert 'id="wizard-export-firefox-policies"' in response.text

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
        assert token not in response.text

    client = make_test_client(app)
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
    assert 'getActiveWizardSchemaVersion() === "release-150"' in source
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

    assert 'id="wizard-ai-policy-controls"' in template
    assert 'id="wizard-ai-esr-empty-state"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_title"' in template
    assert 'data-i18n="profiles.wizard_ai_esr_body"' in template
    assert 'id="wizard-ai-posture-presets"' in template
    assert 'id="wizard-ai-controls-card"' in template
    assert 'data-settings-target="policy:AIControls"' in template
    assert 'id="wizard-generative-ai-card"' in template
    assert 'data-settings-target="policy:GenerativeAI"' in template
    assert 'id="wizard-visual-search-enabled-card"' in template
    assert 'data-settings-target="policy:VisualSearchEnabled"' in template
    assert 'data-ai-outcome-group="feature-controls"' in template
    assert 'data-ai-outcome-group="adjacent-controls"' in template
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
        'id="wizard-settings-docs-',
        'id="wizard-preferences-general-groups"',
        'id="wizard-preferences-home-groups"',
        'id="wizard-preferences-search-groups"',
        'id="wizard-preferences-privacy-groups"',
        'id="wizard-preferences-sync-groups"',
        'id="wizard-preferences-general-docs"',
        'id="wizard-preferences-home-docs"',
        'id="wizard-preferences-search-docs"',
        'id="wizard-preferences-privacy-docs"',
        'id="wizard-preferences-sync-docs"',
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
    assert 'documentRef.querySelector(`[data-settings-target="${targetKey}"]`)' in settings_search_source


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
    assert 'id="wizard-name"' in response.text
    assert 'id="wizard-schema"' in response.text
    assert 'data-scenario-key="corporate_default" aria-pressed="true"' in response.text
    assert 'data-scenario-key="targeted_edits" aria-pressed="false"' in response.text
    assert 'data-starter-key="basic_corporate" aria-pressed="true"' in response.text
    assert 'data-starter-key="blank" aria-pressed="false"' in response.text
    assert 'data-cis-layer-key="cis_l2" aria-pressed="false"' in response.text
    assert 'id="wizard-baseline-override-panel" hidden' in response.text

    removed_default_blocks = (
        'class="wizard-impact-panel',
        'id="wizard-scenario-summary-copy"',
        'id="wizard-shared-device-workflow-copy"',
        'id="wizard-baseline-preview-copy"',
        'id="wizard-baseline-summary-copy"',
    )
    for token in removed_default_blocks:
        assert token not in response.text

    assert 'let wizardScenario = "corporate_default";' in flow_source
    assert 'let wizardStarter = "basic_corporate";' in flow_source
    assert 'button.classList.toggle("wizard-starter-card--active", isActive);' in flow_source
    assert 'button.setAttribute("aria-pressed", isActive ? "true" : "false");' in flow_source
    assert 'box-shadow:\n                inset 4px 0 0 rgba(15, 118, 110, 0.82)' in css_source

    baseline_override_index = setup_template.index('"wizard-baseline-override-panel"')
    secondary_index = setup_template.index('wizard-starter-grid--secondary')
    cis_index = setup_template.index('data-cis-layer-key="cis_l2"')
    assert baseline_override_index < secondary_index < cis_index


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

    removed_tokens = (
        'id="wizard-schema-shell-step-2"',
        'href="#wizard-step-2-basics"',
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


def test_step_three_default_path_is_actionable_home_and_startup():
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
        'id="wizard-home-summary-homepage"',
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


def test_step_four_default_path_is_actionable_search_and_navigation():
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
        'id="wizard-step-4-default-search"',
        'id="wizard-search-defaults-presets"',
        'data-search-defaults-preset="managed_default"',
        'id="wizard-search-default-engine"',
        'id="wizard-search-defaults-section-status"',
        'id="wizard-step-4-managed-engines"',
        'id="wizard-search-engine-add"',
        'id="wizard-search-engine-list"',
        'data-search-engine-preset="docs_portal"',
        'data-search-engine-preset="duckduckgo"',
        'data-search-engine-field="Name"',
        'data-search-engine-field="URLTemplate"',
        'data-search-engine-field="Alias"',
        'data-search-engine-advanced',
        'data-search-engine-field="Method"',
        'data-search-engine-field="PostData"',
        'id="wizard-step-4-suggestions"',
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
        'id="wizard-search-summary-defaults"',
        'id="wizard-search-summary-suggest-jump"',
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


def test_step_five_default_path_is_actionable_privacy_and_protection():
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
        'data-hardening-preset="balanced"',
        'data-hardening-preset="strict"',
        'id="wizard-hardening-section-status"',
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


def test_step_six_default_path_is_compact_accounts_extensions_and_sites():
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
        'id="wizard-step-6-accounts"',
        'id="wizard-sync-focus-presets"',
        'data-sync-focus-preset="accounts"',
        'id="wizard-sync-section-status"',
        'id="wizard-sync-fine-tuning-toggle"',
        'id="wizard-user-messaging-card"',
        'id="wizard-step-6-language"',
        'id="wizard-language-presets"',
        'data-language-preset="translation_off"',
        'id="wizard-requested-locales-card"',
        'id="wizard-translate-enabled-card"',
        'id="wizard-language-section-status"',
        'id="wizard-language-ai-handoff"',
        'id="wizard-step-6-extensions"',
        'id="wizard-extension-governance-presets"',
        'data-extension-governance-preset="managed"',
        'id="wizard-extension-default-mode"',
        'id="wizard-extension-section-status"',
        'id="wizard-extension-fine-tuning-toggle"',
        'id="wizard-extension-curated-section"',
        'id="wizard-step-6-bookmarks"',
        'data-bookmarks-handoff',
        'id="wizard-bookmarks-open-advanced"',
        'id="wizard-bookmarks-section-status"',
        'id="wizard-step-6-websites"',
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


def test_profiles_page_uses_request_locale_for_initial_render():
    client = make_test_client(app)

    response = client.get(
        "/profiles",
        headers={"Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
    )

    assert response.status_code == 200
    assert '<html lang="ru">' in response.text
    assert "Пошаговый мастер" in response.text
    assert "Менеджер профилей браузера" in response.text
    assert "Поисковик" in response.text
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
            "headers": [(b"accept-language", b"fr;q=1, ru;q=oops, en;q=0.5")],
            "query_string": b"",
        }
    )

    assert reloaded._resolve_request_locale(request) == "en"


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

    assert head_bootstrap.is_file()
    assert page_bootstrap.is_file()
    assert 'window.__BPM_INITIAL_LOCALE__ = JSON.parse(payloadText);' in page_bootstrap.read_text(encoding="utf-8")


def test_web_profiles_module_wires_templates_and_route():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    assert reloaded.templates.env.loader.searchpath == [str(reloaded.settings.TEMPLATES_DIR)]
    assert any(route.path == "/profiles" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/new" for route in reloaded.router.routes)
    assert any(route.path == "/profiles/{profile_id}/edit" for route in reloaded.router.routes)
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
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")
    missing_response = client.get("/profiles/999999/edit")
    missing_advanced_response = client.get("/profiles/999999/advanced")

    assert new_response.status_code == 200
    assert edit_response.status_code == 200
    assert advanced_response.status_code == 200
    assert missing_response.status_code == 404
    assert missing_advanced_response.status_code == 404
    assert "<title>New profile draft — Browser Policy Manager</title>" in new_response.text
    assert (
        "<title>Route Skeleton Profile — Profile editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert (
        "<title>Route Skeleton Profile — Advanced editor — Browser Policy Manager</title>"
        in advanced_response.text
    )
    assert 'data-profiles-route-mode="new"' in new_response.text
    assert 'data-profiles-route-mode="edit"' in edit_response.text
    assert 'data-profiles-route-mode="advanced"' in advanced_response.text
    assert 'data-profiles-template-kind="editor"' in new_response.text
    assert 'data-profiles-template-kind="editor"' in edit_response.text
    assert 'data-profiles-template-kind="advanced"' in advanced_response.text
    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text
    assert f'data-editing-profile-id="{profile_id}"' in advanced_response.text
    assert_contains_all(new_response.text, ('id="wizard-panel"', 'id="wizard-schema"'))
    assert_contains_all(edit_response.text, ('id="wizard-panel"', 'id="wizard-schema"'))
    assert_contains_all(
        advanced_response.text,
        (
            'id="editor-panel"',
            'id="editor"',
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="download-firefox-policies"',
        ),
    )


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
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")

    assert library_response.status_code == 200
    assert new_response.status_code == 200
    assert edit_response.status_code == 200

    assert_contains_all(
        library_response.text,
        (
            'data-profiles-route-mode="library"',
            'data-profiles-template-kind="library"',
            'id="library-panel"',
            'id="search"',
            'id="create-profile-link"',
            'href="/profiles/new"',
            'id="list"',
            'id="compare-panel"',
        ),
    )
    assert 'data-editing-profile-id="' not in library_response.text

    for response, route_mode in ((new_response, "new"), (edit_response, "edit")):
        assert_contains_all(
            response.text,
            (
                f'data-profiles-route-mode="{route_mode}"',
                'data-profiles-template-kind="editor"',
                'id="wizard-panel"',
                'id="wizard-schema"',
                'id="wizard-starter-catalog"',
                'id="command-deck"',
            ),
        )

    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text


def test_visual_editor_routes_hide_inline_advanced_surface():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Inline Advanced Split Profile"),
    )
    profile_id = create_response.json()["id"]

    new_response = client.get("/profiles/new")
    edit_response = client.get(f"/profiles/{profile_id}/edit")
    advanced_response = client.get(f"/profiles/{profile_id}/advanced")

    assert 'class="content-grid grid gap-4 support-hidden"' in new_response.text
    assert 'class="content-grid grid gap-4 support-hidden"' in edit_response.text
    assert 'class="content-grid grid gap-4 support-hidden"' not in advanced_response.text
    assert f'href="/profiles/{profile_id}/advanced?return=/profiles/{profile_id}/edit"' in edit_response.text
    assert_contains_all(
        advanced_response.text,
        (
            'data-profiles-route-mode="advanced"',
            'data-profiles-template-kind="advanced"',
            'id="details-panel"',
            'id="editor-panel"',
            'id="advanced-download-strip"',
            'id="advanced-review-strip"',
        ),
    )


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

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profiles",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_page(request))

    assert response.status_code == 200
    assert captured["name"] == "profiles_library.html"
    assert captured["context"]["title"] == "Profile library — Browser Policy Manager"
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


def test_profile_editor_routes_use_editor_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    async def fake_get(session, profile_id, include_deleted=False):
        return SimpleNamespace(id=profile_id, name="Template Split Profile")

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


def test_profile_advanced_route_uses_advanced_template(monkeypatch):
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)
    captured: dict[str, object] = {}

    async def fake_get(session, profile_id, include_deleted=False):
        return SimpleNamespace(id=profile_id, name="Advanced Split Profile")

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
            "path": "/profiles/8/advanced",
            "headers": [],
            "query_string": b"return=/profiles/8/edit&focus=policy:DisableTelemetry",
        }
    )

    response = asyncio.run(reloaded.profiles_advanced_page(request, 8, SimpleNamespace()))

    assert response.status_code == 200
    assert captured["name"] == "profiles_advanced.html"
    assert captured["context"]["title"] == (
        "Advanced Split Profile — Advanced editor — Browser Policy Manager"
    )
    assert captured["context"]["profiles_route_mode"] == "advanced"
    assert captured["context"]["editing_profile_id"] == 8
    assert captured["context"]["return_url"] == "/profiles/8/edit"
    assert captured["context"]["focus_target"] == "policy:DisableTelemetry"


def test_profile_editor_route_context_bootstraps_frontend_state():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function readProfilesRouteContext()" in source
    assert "bodyEl?.dataset.profilesRouteMode" in source
    assert "bodyEl?.dataset.editingProfileId" in source
    assert "async function bootstrapProfileRouteState()" in source
    assert '(routeMode === "edit" || routeMode === "advanced") && editingProfileId' in source
    assert "await loadProfile(editingProfileId, { skipConfirm: true });" in source
    assert "await resetDraft(true);" in source
    assert "await reloadList();" in source


def test_profile_advanced_route_context_bootstraps_advanced_scope():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert 'routeMode === "advanced"' in source
    assert "await loadProfile(editingProfileId, { skipConfirm: true });" in source
    assert "setAdvancedHandoffContext(null);" in source
    assert 'applyWorkspaceScope("advanced", { focus: true, persist: false });' in source
    assert "applyAdvancedFocusTarget(focusTarget);" in source


def test_profile_advanced_route_renders_return_and_focus_context():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Advanced Focus Profile"),
    )
    profile_id = create_response.json()["id"]

    response = client.get(
        f"/profiles/{profile_id}/advanced?return=/profiles/{profile_id}/edit&focus=policy:DisableTelemetry"
    )
    unsafe_response = client.get(
        f"/profiles/{profile_id}/advanced?return=https://example.com/phish&focus=policy:DisableTelemetry"
    )

    assert response.status_code == 200
    assert f'data-advanced-return-url="/profiles/{profile_id}/edit"' in response.text
    assert 'data-advanced-focus-target="policy:DisableTelemetry"' in response.text
    assert f'id="advanced-return-link"' in response.text
    assert f'href="/profiles/{profile_id}/edit"' in response.text
    assert 'id="advanced-return-link"' not in unsafe_response.text


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

    assert web_profiles._build_profile_advanced_href(
        8,
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/advanced?focus=policy:DisableTelemetry"
    assert web_profiles._build_profile_advanced_href(
        8,
        return_url="/profiles/8/edit",
        focus_target="policy:DisableTelemetry",
    ) == "/profiles/8/advanced?return=/profiles/8/edit&focus=policy:DisableTelemetry"


def test_profile_advanced_route_regression_contract():
    client = make_test_client(app)
    create_response = client.post(
        "/api/profiles",
        json=build_profile_payload(name="Advanced Regression Profile"),
    )
    profile_id = create_response.json()["id"]

    advanced_response = client.get(
        f"/profiles/{profile_id}/advanced?return=/profiles/{profile_id}/edit&focus=editor"
    )
    visual_response = client.get(f"/profiles/{profile_id}/edit")

    assert advanced_response.status_code == 200
    assert "<title>Advanced Regression Profile — Advanced editor — Browser Policy Manager</title>" in advanced_response.text
    assert 'data-profiles-route-mode="advanced"' in advanced_response.text
    assert 'data-profiles-template-kind="advanced"' in advanced_response.text
    assert f'data-editing-profile-id="{profile_id}"' in advanced_response.text
    assert f'data-advanced-return-url="/profiles/{profile_id}/edit"' in advanced_response.text
    assert 'data-advanced-focus-target="editor"' in advanced_response.text
    assert_contains_all(
        advanced_response.text,
        (
            'id="command-deck"',
            'id="save"',
            'id="validate"',
            'id="format"',
            'id="details-panel"',
            'id="editor-panel"',
            'id="editor"',
            'id="download-firefox-policies"',
            'id="advanced-review-strip"',
        ),
    )

    assert visual_response.status_code == 200
    assert 'data-profiles-template-kind="editor"' in visual_response.text
    assert 'class="content-grid grid gap-4 support-hidden"' in visual_response.text


def test_visual_advanced_actions_route_to_advanced_destination():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function buildAdvancedRouteHref(profileId, focusTarget = \"\")" in source
    assert "function getAdvancedRouteHref(focusTarget = \"\")" in source
    assert "function deriveAdvancedFocusTarget(targetEl, fallback = \"\")" in source
    assert "function openAdvancedRouteFromVisual(event = null, focusTarget = \"\")" in source
    assert "href.searchParams.set(\"return\", `/profiles/${profileId}/edit`);" in source
    assert 'href.searchParams.set("focus", focusTarget);' in source
    assert 'if (routeMode === "advanced") return false;' in source
    assert "if (!confirmRouteNavigationIfDirty())" in source
    assert 'windowRef.location.assign(href);' in source
    assert "function resolveAdvancedFocusTarget(focusTarget)" in source
    assert "return findSettingsTarget(target) || documentRef.getElementById(target) || null;" in source
    assert 'savedWorkspaceScope === "advanced" ? "guided" : savedWorkspaceScope' in source


def test_profile_route_navigation_warns_when_editor_is_dirty():
    source = (
        Path(__file__).resolve().parents[1] / "app" / "static" / "profiles_runtime.js"
    ).read_text(encoding="utf-8")

    assert "function isGuardedProfileRouteHref(anchorEl)" in source
    assert 'href.startsWith("#")' in source
    assert 'anchorEl.target && anchorEl.target !== "_self"' in source
    assert 'url.pathname === "/profiles" || url.pathname.startsWith("/profiles/")' in source
    assert "function confirmRouteNavigationIfDirty()" in source
    assert "if (!currentSnapshotState().dirty) return true;" in source
    assert 'windowRef.confirm(t("profiles.confirm_discard"))' in source
    assert "function guardProfileRouteNavigation(event)" in source
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
    assert 'href="{{ advanced_href }}&focus=policy:GenerativeAI"' in ai_template
    assert 'href="{{ advanced_href }}&focus=download"' in export_template


def test_ai_step_locales_describe_esr_empty_state():
    client = make_test_client(app)
    en_catalog = client.get("/i18n/en.json").json()
    ru_catalog = client.get("/i18n/ru.json").json()

    assert en_catalog["profiles.wizard_ai_esr_title"] == "No AI controls on Firefox ESR"
    assert en_catalog["profiles.wizard_ai_esr_state"] == (
        "No AI settings are available on this step for Firefox ESR."
    )
    assert ru_catalog["profiles.wizard_ai_esr_title"] == "Для Firefox ESR здесь нет настроек ИИ"
    assert ru_catalog["profiles.wizard_ai_esr_state"] == (
        "Для Firefox ESR на этом шаге нет настроек ИИ."
    )


def test_documentation_placeholders_are_stable_and_optional():
    root = Path(__file__).resolve().parents[1]
    macro_source = (
        root / "app" / "templates" / "profiles" / "_wizard_macros.html"
    ).read_text(encoding="utf-8")
    workspace_template = (
        root / "app" / "templates" / "profiles" / "_page_workspace.html"
    ).read_text(encoding="utf-8")
    export_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_export.html"
    ).read_text(encoding="utf-8")
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    response = _profiles_page_response()

    assert 'data-doc-placeholder="{{ doc_id }}"' in macro_source
    assert 'aria-disabled="true"' in macro_source
    assert 'href="#docs-{{ doc_id }}"' in macro_source
    assert 'render_doc_placeholder("advanced-editor"' in workspace_template
    assert 'render_doc_placeholder("policy-boundaries"' in export_template
    assert 'render_doc_placeholder("guided-schema-shell"' in macro_source
    assert ".wizard-doc-placeholder" in css_source
    assert 'data-doc-placeholder="advanced-editor"' in response.text
    assert 'data-doc-placeholder="policy-boundaries"' in response.text
    assert 'href="#docs-advanced-editor"' in response.text
    assert 'href="#docs-policy-boundaries"' in response.text


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
        root / "app" / "templates" / "profiles" / "_page_workspace.html"
    ).read_text(encoding="utf-8")

    assert "@media (max-width: 560px)" in css_source
    assert ".library-panel-toolbar #create-profile-link" in css_source
    assert ".library-panel-toolbar #import-firefox-policies" in css_source
    assert ".library-table-shell" in css_source
    assert "overflow-x: hidden;" in css_source
    assert ".library-row-meta::before" in css_source
    assert 'content: "Schema";' in css_source
    assert ".library-row-updated::before" in css_source
    assert 'content: "Updated";' in css_source
    assert ".library-row-status-wrap::before" in css_source
    assert 'content: "Status";' in css_source
    assert ".library-row-actions .button-base" in css_source
    assert 'id="search"' in template
    assert 'id="create-profile-link"' in template
    assert 'id="import-firefox-policies"' in template


def test_visual_editor_narrow_viewport_contract():
    root = Path(__file__).resolve().parents[1]
    css_source = (root / "app" / "static" / "profiles.css").read_text(
        encoding="utf-8"
    )
    command_deck = (
        root / "app" / "templates" / "profiles" / "_page_command_deck.html"
    ).read_text(encoding="utf-8")
    workspace_template = (
        root / "app" / "templates" / "profiles" / "_page_workspace.html"
    ).read_text(encoding="utf-8")

    assert "@media (max-width: 560px)" in css_source
    assert ".workspace-dock" in css_source
    assert ".dock-actions-grid--primary" in css_source
    assert ".dock-actions .button-base" in css_source
    assert ".wizard-header" in css_source
    assert ".wizard-settings-search-row" in css_source
    assert ".wizard-layout" in css_source
    assert ".wizard-stepper" in css_source
    assert "grid-auto-columns: minmax(142px, 76vw);" in css_source
    assert ".wizard-panel" in css_source
    assert "overflow-wrap: anywhere;" in css_source
    assert ".wizard-nav-actions" in css_source
    assert "#advanced-handoff-panel .editor-header" in css_source
    assert "#advanced-handoff-open" in css_source
    assert 'id="save"' in command_deck
    assert 'id="validate"' in command_deck
    assert 'id="advanced-handoff-open"' in workspace_template


def test_profile_library_actions_use_editor_route_links():
    root = Path(__file__).resolve().parents[1]
    template = (root / "app" / "templates" / "profiles" / "_page_workspace.html").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )

    assert 'id="create-profile-link"' in template
    assert 'href="/profiles/new"' in template
    assert 'const editHref = `/profiles/${profile.id}/edit`;' in workspace_source
    assert '<a class="library-row-title-button" href="${editHref}">' in workspace_source
    assert (
        '<a class="button-base library-row-open-button ${selected ? "library-row-open-button--selected" : ""}" href="${editHref}">'
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

    assert '(routeMode === "edit" || routeMode === "advanced") && editingProfileId' in runtime_source
    assert "await loadProfile(editingProfileId, { skipConfirm: true });" in runtime_source
    assert 'applyWorkspaceScope("advanced", { focus: true, persist: false });' in runtime_source
    assert "saveButtonEl.addEventListener(\"click\", saveCurrent);" in runtime_source
    assert "saveCurrent();" in runtime_source
    assert "setSaveCurrent(workspace.saveCurrent);" in bootstrap_source
    assert "const revision = Number(getCurrentProfile()?.revision);" in workspace_source
    assert "includeExpectedRevision ? buildExpectedRevisionPayload() : {}" in workspace_source
    assert "if (isRevisionConflictError(e))" in workspace_source


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

    assert "<title>Profile library — Browser Policy Manager</title>" in library_response.text
    assert "<title>New profile draft — Browser Policy Manager</title>" in new_response.text
    assert (
        "<title>Finance Laptop Baseline — Profile editor — Browser Policy Manager</title>"
        in edit_response.text
    )
    assert (
        "<title>Finance Laptop Baseline — Advanced editor — Browser Policy Manager</title>"
        in advanced_response.text
    )
