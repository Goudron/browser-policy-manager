from __future__ import annotations

import json
import uuid
from pathlib import Path

from app.main import app
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from tests.support import assert_contains_all, assert_has_keys, make_test_client

UI_SHELL_TOKENS = (
    'id="profile-name"',
    'id="profile-owner"',
    'id="profile-description"',
    'id="lang"',
    'id="wizard-panel"',
    'id="wizard-starter-catalog"',
    'id="profile-derived-note"',
    'id="profile-compliance-panel"',
    'id="profile-compliance-copy"',
    'id="profile-compliance-list"',
    'id="profile-clone-handoff-panel"',
    'id="profile-clone-handoff-copy" role="status" aria-live="polite"',
    'id="profile-clone-handoff-list" role="list"',
    'id="profile-lifecycle-panel"',
    'id="profile-lifecycle-copy"',
    'id="profile-lifecycle-list"',
    'id="wizard-settings-search-input"',
    'id="wizard-settings-search-results"',
    'id="wizard-settings-catalog"',
    'id="wizard-schema"',
    'id="wizard-mode"',
    'id="wizard-finish"',
    'id="wizard-step-actions"',
    'id="wizard-step-actions-copy"',
    'id="wizard-step-undo"',
    'id="wizard-step-reset"',
    'data-starter-key="basic_corporate"',
    'data-starter-key="basic_corporate" aria-pressed="true"',
    'data-starter-key="classroom_kiosk"',
    'data-starter-key="soc_hard"',
    'data-scenario-key="corporate_default" aria-pressed="true"',
    'data-scenario-key="targeted_edits" aria-pressed="false"',
    'data-cis-layer-key="cis_l1"',
    'data-cis-layer-key="cis_l2"',
    'id="wizard-summary-starter"',
    'id="wizard-summary-cis"',
    'id="wizard-cis-exceptions-list"',
    'id="wizard-homepage-url"',
    'id="wizard-homepage-shared-presets"',
    'id="wizard-search-bar"',
    'id="wizard-step-2-default-search"',
    'id="wizard-step-2-managed-engines"',
    'id="wizard-step-2-suggestions"',
    'id="wizard-search-default-engine"',
    'id="wizard-search-engine-add"',
    'id="wizard-search-engine-list"',
    'id="wizard-preference-row-template"',
    'id="wizard-preferences-known-list"',
    "wizard-search-engine-preset-status",
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
    'id="wizard-new-tab-page"',
    'id="wizard-override-first-run"',
    'data-firefox-home-key="Search"',
    'id="wizard-website-access-decision"',
    'id="wizard-website-access-posture"',
    'data-website-access-posture="allow_only"',
    'id="wizard-website-access-handlers"',
    'data-website-access-handlers="protocols"',
    'data-firefox-suggest-key="WebSuggestions"',
    'id="wizard-proxy-mode"',
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
    'profiles.wizard_user_environment_map_title',
    'id="wizard-step-4-accounts"',
    'id="wizard-step-4-language"',
    'id="wizard-step-4-extensions"',
    'id="wizard-step-4-bookmarks"',
    'id="wizard-step-4-websites"',
    'id="wizard-privacy-summary-permissions"',
    'id="wizard-privacy-summary-cookies"',
    'id="wizard-privacy-summary-permissions-jump"',
    'id="wizard-privacy-summary-cookies-jump"',
    'id="wizard-extension-default-mode"',
    'id="wizard-extension-install"',
    'data-extension-rule-group="install"',
    'id="wizard-extension-locked"',
    'data-extension-rule-group="locked"',
    'id="wizard-extension-uninstall"',
    'data-extension-rule-group="uninstall"',
    'data-bookmarks-handoff',
    'id="wizard-bookmarks-open-settings"',
    'id="wizard-bookmarks-configured-actions"',
    'id="wizard-bookmarks-links-jump"',
    'id="wizard-bookmarks-folders-jump"',
    'id="wizard-bookmarks-nested-jump"',
    'id="wizard-install-addons-permission-card"',
    'id="wizard-extension-settings-card"',
    'id="wizard-ai-section-status"',
    'id="wizard-ai-esr-empty-state"',
    'id="wizard-ai-policy-controls"',
    'id="wizard-ai-governance-copy"',
    'id="wizard-visual-search-enabled-card"',
    'data-schema-dict-status',
    'data-schema-array-status',
    'data-schema-nested-field',
    'data-schema-nested-status',
    'data-schema-nested-array-add',
    'data-schema-nested-dict-add',
    'data-schema-object-status',
    'id="wizard-summary-extensions"',
    'id="wizard-step-memory-copy"',
    'id="wizard-step-memory-list"',
    'id="wizard-summary-derived-row"',
    'id="wizard-summary-derived"',
    'id="wizard-summary-lifecycle-list"',
    'id="wizard-cis-final-summary"',
    'id="wizard-cis-exceptions-count"',
    'id="wizard-cis-exceptions-reasons"',
    'id="wizard-cis-exceptions-details"',
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
    'id="wizard-export-guided-summary-list"',
    'id="wizard-export-guided-group-profile"',
    'id="wizard-export-guided-group-browser"',
    'id="wizard-export-guided-group-privacy"',
    'id="wizard-export-guided-group-features"',
    'id="wizard-export-guided-group-ai"',
    'id="wizard-export-summary-ai"',
    'id="wizard-export-summary-ai-jump"',
    'id="wizard-export-save-action"',
    'id="wizard-export-validate-action"',
    'id="wizard-export-firefox-policies"',
    'id="wizard-export-included-now"',
    'id="wizard-export-missing-now"',
    'id="wizard-export-review-now"',
    'data-extension-profile="uBlock0@raymondhill.net"',
    'data-extension-profile="adguardadblocker@adguard.com"',
    'data-extension-profile="https-everywhere@eff.org"',
    'wizard-extension-profile-row',
    'wizard-extension-profile-status',
    'data-extension-profile-status="uBlock0@raymondhill.net"',
    'data-extension-profile-status="adguardadblocker@adguard.com"',
    'data-extension-profile-status="https-everywhere@eff.org"',
    'data-policy-key="DisableTelemetry"',
    'data-policy-key="DisableFirefoxAccounts"',
    'data-policy-key="BlockAboutProfiles"',
    'data-policy-key="DisableAppUpdate"',
    'id="save"',
    'id="validate"',
    'id="workspace-signal"',
    "/api/profiles",
    "/api/export/profiles",
    "/api/validate/",
    "/i18n/${lang}.json",
    "resolveBrowserLanguage",
)

UI_LOCALE_KEYS = (
    "profiles.title",
    "profiles.create_submit",
    "profiles.editor_chrome_guided_body",
    "profiles.editor_chrome_settings_body",
    "profiles.editor_chrome_json_body",
    "profiles.signal_dirty",
    "profiles.validation_ok",
    "profiles.locale_system",
    "profiles.hard_delete",
    "profiles.reset_library",
    "profiles.library_filtered_short",
    "profiles.library_total_short",
    "profiles.confirm_hard_delete",
    "profiles.confirm_reset_library",
    "profiles.wizard_context_new",
    "profiles.wizard_step_one",
    "profiles.wizard_step_two",
    "profiles.wizard_step_three",
    "profiles.wizard_step_four",
    "profiles.wizard_step_five",
    "profiles.wizard_step_six",
    "profiles.wizard_user_environment_map_title",
    "profiles.wizard_user_environment_map_extensions",
    "profiles.wizard_user_environment_map_websites",
    "profiles.wizard_next_action_hardening_posture",
    "profiles.wizard_next_action_extensions_rollout",
    "profiles.wizard_next_action_website_filter",
    "profiles.wizard_settings_map_label",
    "profiles.wizard_settings_controls_label",
    "profiles.wizard_settings_filter_all",
    "profiles.wizard_settings_search_label",
    "profiles.wizard_settings_search_clear",
    "profiles.wizard_settings_search_kind_search_preset",
    "profiles.wizard_settings_search_kind_preference_bundle",
    "profiles.wizard_settings_general_updates",
    "profiles.wizard_settings_privacy_passwords",
    "profiles.wizard_settings_sync_account",
    "profiles.wizard_general_policy_title",
    "profiles.wizard_upkeep_governance_title",
    "profiles.wizard_shell_nested_unsupported",
    "profiles.wizard_shared_device_workflow_title",
    "profiles.compare_title",
    "profiles.compare_action",
    "profiles.clone_action",
    "profiles.clone_handoff_title",
    "profiles.clone_handoff_active",
    "profiles.clone_handoff_item_compare",
    "profiles.clone_handoff_open_step",
    "profiles.clone_handoff_compare",
    "profiles.compare_summary_policies",
    "profiles.wizard_summary_derived",
    "profiles.lifecycle_review_title",
    "profiles.wizard_preferences_general_title",
    "profiles.wizard_preferences_bundles_title",
    "profiles.wizard_preferences_bundle_applied",
    "profiles.wizard_preferences_bundle_state_applied",
    "profiles.wizard_preferences_bundle_state_conflict",
    "profiles.wizard_preferences_known_state_suggested",
    "profiles.wizard_preferences_known_state_overridden",
    "profiles.wizard_preferences_known_title",
    "profiles.wizard_preferences_known_applied",
    "profiles.wizard_preferences_gui_label",
    "profiles.wizard_preferences_add_button",
    "profiles.wizard_preferences_preset_applied",
    "profiles.wizard_preferences_preset_privacy_https_only_title",
    "profiles.wizard_preferences_preset_sync_passwords_off_title",
    "profiles.wizard_privacy_review_title",
    "profiles.wizard_privacy_review_permissions",
    "profiles.wizard_privacy_review_permissions_subcounts",
    "profiles.wizard_privacy_review_cookies",
    "profiles.wizard_network_review_title",
    "profiles.wizard_network_review_windows_sso",
    "profiles.wizard_home_review_title",
    "profiles.wizard_home_review_user_messaging",
    "profiles.wizard_home_surfaces_workflow_title",
    "profiles.wizard_search_review_title",
    "profiles.wizard_search_review_custom",
    "profiles.wizard_search_surfaces_workflow_title",
    "profiles.wizard_language_governance_title",
    "profiles.wizard_ai_posture_title",
    "profiles.wizard_ai_posture_disable_title",
    "profiles.wizard_ai_map_title",
    "profiles.wizard_ai_controls_title",
    "profiles.wizard_ai_esr_title",
    "profiles.wizard_ai_esr_body",
    "profiles.wizard_ai_esr_state",
    "profiles.wizard_export_compatibility_title",
    "profiles.wizard_export_profile_saved",
    "profiles.wizard_export_state_unsaved_existing",
    "profiles.wizard_export_unknown_count",
    "profiles.wizard_export_check_ready",
    "profiles.wizard_export_check_unsaved",
    "profiles.wizard_export_included_title",
    "profiles.wizard_export_missing_title",
    "profiles.wizard_export_review_title",
    "profiles.wizard_homepage_shared_preset_portal_title",
    "profiles.wizard_website_access_decision_title",
    "profiles.wizard_website_access_posture_label",
    "profiles.wizard_website_access_handlers_label",
    "profiles.wizard_website_filter_shared_preset_allow_only_title",
    "profiles.wizard_homepage_section_state_invalid",
    "profiles.wizard_firefox_home_section_state_configured",
    "profiles.wizard_search_defaults_section_state_conflict",
    "profiles.wizard_firefox_suggest_section_state_conflict",
    "profiles.wizard_search_title",
    "profiles.wizard_search_add_title",
    "profiles.wizard_search_presets_title",
    "profiles.wizard_search_presets_menu_title",
    "profiles.wizard_search_preset_ddg_title",
    "profiles.wizard_search_preset_state_applied",
    "profiles.wizard_search_preset_state_conflict",
    "profiles.wizard_search_engine_name_label",
    "profiles.wizard_search_engine_summary_default",
    "profiles.wizard_search_engine_warning_required",
    "profiles.wizard_firefox_home_title",
    "profiles.wizard_firefox_suggest_title",
    "profiles.wizard_step_four",
    "profiles.wizard_step_five",
    "profiles.wizard_starter_basic_label",
    "profiles.wizard_proxy_mode_manual",
    "profiles.wizard_extension_profile_mode_force",
    "profiles.wizard_extension_profile_ublock_title",
    "profiles.wizard_extension_profile_state_missing",
    "profiles.wizard_extension_profile_state_catalog_url",
    "profiles.wizard_extensions_review_title",
    "profiles.wizard_extensions_review_custom_urls",
    "profiles.wizard_extensions_review_open",
    "profiles.wizard_extensions_advanced_install_permissions",
    "profiles.wizard_extensions_advanced_arbitrary_rules",
    "profiles.wizard_extensions_advanced_count",
    "profiles.wizard_bookmarks_review_title",
    "profiles.wizard_bookmarks_review_nested",
    "profiles.wizard_bookmarks_review_open",
    "profiles.wizard_bookmarks_handoff_title",
    "profiles.wizard_bookmarks_open_action",
    "profiles.wizard_bookmarks_row_state_toolbar",
    "profiles.wizard_managed_bookmarks_row_state_invalid",
    "profiles.wizard_website_access_review_title",
    "profiles.wizard_website_access_review_handlers",
    "profiles.wizard_website_governance_title",
    "profiles.wizard_website_filter_state_configured",
    "profiles.wizard_authentication_state_configured",
    "profiles.wizard_step_memory_title",
    "profiles.wizard_step_memory_open",
    "profiles.wizard_step_memory_current",
    "profiles.wizard_trust_auth_workflow_title",
    "profiles.wizard_certificates_state_with_roots",
    "profiles.wizard_doh_state_provider",
    "profiles.wizard_permissions_state_strict",
    "profiles.wizard_permissions_nested_default",
    "profiles.wizard_cookies_state_strict",
    "profiles.wizard_handlers_state_configured",
    "profiles.wizard_handlers_nested_array_configured",
    "profiles.wizard_user_messaging_state_configured",
    "profiles.wizard_extension_settings_row_state_install_url",
    "profiles.wizard_extension_settings_row_state_configured",
    "profiles.wizard_extensions_mode_blocked",
)

P2_3_UX_REGRESSION_TOKENS = (
    'id="wizard-hardening-section-status"',
    'id="wizard-privacy-user-data-section-status"',
    'id="wizard-lockdown-section-status"',
    'data-hardening-cleanup-subchoice',
    'data-hardening-subposture-menu="cleanup"',
    'id="wizard-cleanup-section-status"',
    'id="wizard-privacy-summary-user-data"',
    'id="wizard-privacy-summary-cleanup"',
    'id="wizard-extension-governance-presets"',
    'id="wizard-language-ai-handoff"',
    'id="wizard-ai-posture-presets"',
    'data-ai-posture-preset="disable"',
    'data-ai-posture-preset="mixed"',
    'id="wizard-ai-governance-copy"',
    'id="wizard-ai-policy-controls"',
    'id="wizard-export-section-ready"',
    'id="wizard-export-section-changes"',
    'id="wizard-export-section-technical"',
    "wizard-export-primary-card",
    'id="wizard-export-final-checklist"',
    'id="wizard-export-technical-alerts"',
    'id="wizard-export-raw-summary-jump"',
    'id="wizard-export-deprecated-summary-jump"',
    'id="wizard-export-unknown-summary-jump"',
    'id="wizard-export-baseline-copy"',
    'id="wizard-export-baseline-list"',
    'id="wizard-export-next-steps"',
    'id="wizard-export-ready-now"',
    'id="wizard-export-included-now"',
    'id="wizard-export-missing-now"',
    'id="wizard-export-review-now"',
    'id="wizard-export-guided-summary-list"',
    'id="wizard-export-guided-group-profile"',
    'id="wizard-export-guided-group-browser"',
    'id="wizard-export-guided-group-privacy"',
    'id="wizard-export-guided-group-features"',
    'id="wizard-export-guided-group-ai"',
    'id="wizard-export-download-hint"',
    'data-hardening-preset="balanced"',
    'data-cleanup-preset="shared"',
    'data-extension-governance-preset="managed"',
    'data-extension-governance-preset="mixed"',
    'data-ai-posture-preset="mixed"',
)

P2_3_LOCALE_KEYS = (
    "profiles.settings_context_title",
    "profiles.wizard_hardening_preset_balanced_title",
    "profiles.wizard_hardening_governance_title",
    "profiles.wizard_cleanup_preset_shared_title",
    "profiles.wizard_privacy_review_user_data",
    "profiles.wizard_privacy_review_cleanup",
    "profiles.wizard_extensions_preset_managed_title",
    "profiles.wizard_extensions_governance_selector_hint",
    "profiles.wizard_extensions_governance_managed_title",
    "profiles.wizard_extensions_governance_curated_title",
    "profiles.wizard_extensions_governance_title",
    "profiles.wizard_language_ai_handoff_optional",
    "profiles.wizard_export_baseline_summary_title",
    "profiles.wizard_export_download_hint_unsaved_existing",
    "profiles.wizard_export_shareable_title",
    "profiles.wizard_export_shareable_generate",
    "profiles.wizard_export_shareable_copy",
    "profiles.wizard_export_included_title",
    "profiles.wizard_export_missing_title",
    "profiles.wizard_export_review_title",
    "profiles.wizard_export_boundary_register_title",
    "profiles.wizard_export_drilldown_title",
)

P2_3_EXPORT_LIFECYCLE_LOCALE_KEYS = (
    "profiles.wizard_export_state_unsaved_new",
    "profiles.wizard_export_state_unsaved_existing",
    "profiles.wizard_export_state_invalid_dirty",
    "profiles.wizard_export_download_hint_unsaved_new",
    "profiles.wizard_export_download_hint_unsaved_existing",
    "profiles.wizard_export_download_hint_invalid_dirty",
    "profiles.wizard_export_download_hint_archived",
    "profiles.wizard_export_download_hint_ready",
)

PR4_1_POST_ROADMAP_LOCALE_KEYS = (
    "profiles.compare_guided_areas_title",
    "profiles.compare_guided_areas_active",
    "profiles.compare_guided_area_step_one",
    "profiles.compare_guided_area_step_two",
    "profiles.compare_guided_area_step_three",
    "profiles.compare_guided_area_step_four",
    "profiles.compare_guided_area_step_five",
    "profiles.compare_guided_area_preview",
    "profiles.compare_guided_area_more",
    "profiles.clone_action",
    "profiles.clone_meta",
    "profiles.clone_source_value",
    "profiles.wizard_summary_derived",
    "profiles.wizard_summary_derived_value",
    "profiles.lifecycle_review_title",
    "profiles.lifecycle_item_created",
    "profiles.lifecycle_item_saved",
    "profiles.lifecycle_item_state",
    "profiles.lifecycle_item_state_saved",
    "profiles.lifecycle_item_state_archived",
    "profiles.lifecycle_item_state_clone_draft",
    "profiles.lifecycle_item_origin",
    "profiles.lifecycle_item_origin_clone",
    "profiles.lifecycle_item_recent",
    "profiles.lifecycle_item_recent_restored",
    "profiles.wizard_step_memory_title",
    "profiles.wizard_step_memory_active",
    "profiles.wizard_step_memory_step_browser",
    "profiles.wizard_step_memory_step_privacy",
    "profiles.wizard_export_boundary_register_title",
    "profiles.wizard_export_drilldown_title",
    "profiles.wizard_export_drilldown_raw_title",
    "profiles.wizard_export_drilldown_deprecated_title",
    "profiles.wizard_export_drilldown_unknown_title",
)


def _make_payload() -> dict:
    unique = uuid.uuid4().hex[:8]
    return {
        "name": f"UI-{unique}",
        "description": "UI smoke lifecycle profile",
        "schema_version": "esr-140.11",
        "owner": "ops@example.org",
        "flags": {
            "DisableTelemetry": True,
            "DisablePrivateBrowsing": True,
        },
    }


def test_profiles_ui_shell_exposes_public_hooks():
    client = make_test_client(app)

    page = client.get("/profiles/new")
    assert page.status_code == 200, page.text
    assert page.headers["content-type"].startswith("text/html")
    assert_contains_all(page.text, UI_SHELL_TOKENS)


def test_profiles_ui_shell_exposes_recent_ux_regression_hooks():
    client = make_test_client(app)

    page = client.get("/profiles/new")
    assert page.status_code == 200, page.text
    assert page.headers["content-type"].startswith("text/html")
    assert_contains_all(page.text, P2_3_UX_REGRESSION_TOKENS)


def test_profiles_ui_shell_keeps_guided_first_viewport_order_contract():
    client = make_test_client(app)

    page = client.get("/profiles/new")
    assert page.status_code == 200, page.text
    html = page.text

    wizard_index = html.index('id="wizard-panel"')
    overview_index = html.index('id="overview-panel"')
    search_index = html.index('id="wizard-settings-search-input"')
    first_step_index = html.index('id="wizard-step-1"')

    assert overview_index < wizard_index
    assert wizard_index < search_index
    assert wizard_index < first_step_index


def test_profiles_ui_shell_keeps_export_actions_before_technical_catalog():
    client = make_test_client(app)

    page = client.get("/profiles/new")
    assert page.status_code == 200, page.text
    html = page.text

    step_six_index = html.index('id="wizard-step-6"')
    ready_index = html.index('id="wizard-export-section-ready"')
    save_action_index = html.index('id="wizard-export-save-action"')
    download_action_index = html.index('id="wizard-export-firefox-policies"')
    technical_index = html.index('id="wizard-export-section-technical"')
    shell_index = html.index('id="wizard-schema-shell-step-8"')

    assert step_six_index < ready_index < save_action_index < download_action_index
    assert download_action_index < technical_index < shell_index


def test_profiles_ui_locale_catalog_exposes_required_keys():
    client = make_test_client(app)

    locale = client.get("/i18n/en.json")
    assert locale.status_code == 200, locale.text
    assert_has_keys(locale.json(), UI_LOCALE_KEYS)


def test_profiles_ui_locale_catalog_exposes_recent_ux_regression_keys():
    client = make_test_client(app)

    locale_en = client.get("/i18n/en.json")
    locale_ru = client.get("/i18n/ru.json")

    assert locale_en.status_code == 200, locale_en.text
    assert locale_ru.status_code == 200, locale_ru.text

    locale_en_json = locale_en.json()
    locale_ru_json = locale_ru.json()

    assert_has_keys(locale_en_json, P2_3_LOCALE_KEYS)
    assert_has_keys(locale_ru_json, P2_3_LOCALE_KEYS)

    assert locale_en_json["profiles.settings_context_title"] == "Continue in All settings"
    assert locale_en_json["profiles.wizard_export_baseline_summary_title"] == "Baseline guardrails"
    assert locale_en_json["profiles.wizard_export_shareable_title"] == "Shareable summary"
    assert locale_en_json["profiles.wizard_export_shareable_generate"] == (
        "Generate/copy shareable summary"
    )
    assert locale_en_json["profiles.wizard_export_included_title"] == (
        "Included in the policies.json you download now"
    )
    assert locale_ru_json["profiles.settings_context_title"] == "Продолжение во Всех настройках"
    assert locale_ru_json["profiles.wizard_export_shareable_title"] == "Выжимка для передачи"
    assert locale_ru_json["profiles.wizard_export_shareable_generate"] == (
        "Сформировать/скопировать выжимку"
    )
    assert locale_ru_json["profiles.wizard_export_missing_title"] == (
        "Что пока не попадёт в скачанный policies.json"
    )


def test_esr_ai_step_browser_regression_shows_empty_state_instead_of_release_controls():
    client = make_test_client(app)

    new_page = client.get("/profiles/new")
    assert new_page.status_code == 200, new_page.text
    assert_contains_all(
        new_page.text,
        (
            'id="wizard-step-5"',
            'id="wizard-ai-esr-empty-state"',
            'id="wizard-ai-release-content"',
            'id="wizard-ai-posture-presets"',
            'id="wizard-ai-policy-controls"',
            'data-settings-target="policy:AIControls"',
            'data-settings-target="policy:GenerativeAI"',
            'data-settings-target="policy:VisualSearchEnabled"',
        ),
    )

    payload = {
        "name": f"ESR AI Empty State-{uuid.uuid4().hex[:8]}",
        "description": "ESR AI empty-state regression",
        "owner": "desktop@example.org",
        "schema_version": "esr-140.11",
        "flags": {
            "DisableTelemetry": True,
        },
    }
    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()

    edit_page = client.get(f"/profiles/{created['id']}/edit")
    assert edit_page.status_code == 200, edit_page.text
    assert f'data-editing-profile-id="{created["id"]}"' in edit_page.text
    assert 'data-profiles-route-mode="edit"' in edit_page.text

    root = Path(__file__).resolve().parents[1]
    shared_source = (root / "app" / "static" / "profiles_shared.js").read_text(
        encoding="utf-8"
    )
    dom_source = (root / "app" / "static" / "profiles_dom.js").read_text(
        encoding="utf-8"
    )
    extensions_source = (
        root / "app" / "static" / "profiles_extensions.js"
    ).read_text(encoding="utf-8")
    bootstrap_source = (
        root / "app" / "static" / "profiles_bootstrap_core.js"
    ).read_text(encoding="utf-8")

    assert 'schemaVersion: "esr-140.11"' in shared_source
    assert "function getActiveWizardSchemaVersion()" in shared_source
    assert 'return documentRef.getElementById("profile-type")?.value' in shared_source
    assert "|| wizardSchemaEl?.value" in shared_source
    assert "|| currentProfile?.schema_version" in shared_source
    assert "|| currentProfile?.schemaVersion" in shared_source
    assert "|| defaultSchemaVersion;" in shared_source
    assert 'wizardAiEsrcEmptyStateEl: byId("wizard-ai-esr-empty-state")' in dom_source
    assert 'wizardAiReleaseContentEl: byId("wizard-ai-release-content")' in dom_source
    assert 'wizardAiPosturePresetsEl: byId("wizard-ai-posture-presets")' in dom_source
    assert 'wizardAiPolicyControlsEl: byId("wizard-ai-policy-controls")' in dom_source
    assert "function isAiWizardAvailable()" in extensions_source
    assert "function hasUsableAiPolicyCard(policyCardEl)" in extensions_source
    assert "wizardAiEsrcEmptyStateEl," in bootstrap_source
    assert "wizardAiReleaseContentEl," in bootstrap_source
    assert "wizardAiControlsCardEl," in bootstrap_source
    assert "wizardAiEsrcEmptyStateEl.hidden = releaseAiAvailable;" in extensions_source
    assert "wizardAiReleaseContentEl.hidden = !releaseAiAvailable;" in extensions_source
    assert "wizardAiPosturePresetsEl.hidden = !releaseAiAvailable;" in extensions_source
    assert "wizardAiPolicyControlsEl.hidden = !releaseAiAvailable;" in extensions_source
    assert 'setText(wizardAiSectionStatusEl, t("profiles.wizard_ai_esr_state"));' in extensions_source
    assert "wizardAiProvidersHandoffEl" not in extensions_source
    assert "aiProvidersSectionStatusEl" not in extensions_source
    assert 'wizardAiGovernanceCopyEl.textContent = t("profiles.wizard_ai_esr_body");' in extensions_source
    assert 'renderPresetButtonState(aiPosturePresetButtons, null, "aiPosturePreset");' in extensions_source


def test_release_ai_step_browser_regression_keeps_release_controls_available():
    client = make_test_client(app)

    payload = {
        "name": f"Release AI Controls-{uuid.uuid4().hex[:8]}",
        "description": "Release AI controls regression",
        "owner": "desktop@example.org",
        "schema_version": "release-151",
        "flags": {
            "DisableTelemetry": True,
            "AIControls": {
                "Default": {
                    "Value": "blocked",
                    "Locked": True,
                },
            },
            "VisualSearchEnabled": False,
        },
    }
    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()

    edit_page = client.get(f"/profiles/{created['id']}/edit")
    assert edit_page.status_code == 200, edit_page.text
    assert f'data-editing-profile-id="{created["id"]}"' in edit_page.text
    assert 'data-profiles-route-mode="edit"' in edit_page.text
    assert 'id="wizard-ai-esr-empty-state"' in edit_page.text
    assert 'id="wizard-ai-posture-presets"' in edit_page.text
    assert 'id="wizard-ai-policy-controls"' in edit_page.text
    assert 'data-settings-target="policy:AIControls"' in edit_page.text
    assert 'data-settings-target="policy:GenerativeAI"' in edit_page.text
    assert 'data-settings-target="policy:VisualSearchEnabled"' in edit_page.text

    validate_response = client.post(
        "/api/validate/release-151",
        json={"document": payload["flags"]},
    )
    assert validate_response.status_code == 200, validate_response.text
    assert validate_response.json()["ok"] is True

    export_response = client.get(
        f"/api/export/profiles/{created['id']}/firefox/policies.json"
    )
    assert export_response.status_code == 200, export_response.text
    exported = export_response.json()["policies"]
    assert exported["AIControls"]["Default"]["Value"] == "blocked"
    assert exported["AIControls"]["Default"]["Locked"] is True
    assert exported["VisualSearchEnabled"] is False

    root = Path(__file__).resolve().parents[1]
    extensions_source = (
        root / "app" / "static" / "profiles_extensions.js"
    ).read_text(encoding="utf-8")

    assert "const releaseAiAvailable = isAiWizardAvailable();" in extensions_source
    assert "wizardAiEsrcEmptyStateEl.hidden = releaseAiAvailable;" in extensions_source
    assert "wizardAiPostureBarEl.hidden = !releaseAiAvailable;" in extensions_source
    assert "wizardAiPostureBodyEl.hidden = !releaseAiAvailable;" in extensions_source
    assert "wizardAiPosturePresetsEl.hidden = !releaseAiAvailable;" in extensions_source
    assert "wizardAiPolicyControlsEl.hidden = !releaseAiAvailable;" in extensions_source
    assert 't("profiles.wizard_ai_section_state_feature_controls")' in extensions_source
    assert 't("profiles.wizard_ai_section_state_visual_search_disabled")' in extensions_source
    assert 'wizardAiGovernanceCopyEl.textContent = hasManagedAiPosture' in extensions_source
    assert '? t("profiles.wizard_ai_controls_active")' in extensions_source
    assert ': t("profiles.wizard_ai_controls_body");' in extensions_source


def test_release_guided_ai_and_vpn_browser_regression_can_save_and_export():
    client = make_test_client(app)

    new_page = client.get("/profiles/new")
    assert new_page.status_code == 200, new_page.text
    assert_contains_all(
        new_page.text,
        (
            'id="wizard-step-5"',
            'id="wizard-privacy-vpn-section-status"',
            'id="wizard-ip-protection-available-card"',
            'data-settings-target="policy:IPProtectionAvailable"',
            'id="wizard-step-5"',
            'id="wizard-ai-controls-card"',
            'data-settings-target="policy:AIControls"',
            'id="wizard-export-summary-ai-jump"',
            'id="wizard-export-firefox-policies"',
        ),
    )

    payload = {
        "name": f"Release Guided AI VPN-{uuid.uuid4().hex[:8]}",
        "description": "Firefox 151 guided AI and VPN regression",
        "owner": "desktop@example.org",
        "schema_version": "release-151",
        "flags": {
            "DisableTelemetry": True,
            "IPProtectionAvailable": False,
            "AIControls": {
                "Default": {
                    "Value": "available",
                    "Locked": True,
                },
                "SidebarChatbot": {
                    "Value": "blocked",
                    "Locked": True,
                },
                "SmartWindow": {
                    "Value": "blocked",
                    "Locked": True,
                },
            },
            "VisualSearchEnabled": False,
        },
    }

    validate_response = client.post(
        "/api/validate/release-151",
        json={"document": payload["flags"]},
    )
    assert validate_response.status_code == 200, validate_response.text
    assert validate_response.json()["ok"] is True

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["schema_version"] == "release-151"

    edit_page = client.get(f"/profiles/{created['id']}/edit")
    assert edit_page.status_code == 200, edit_page.text
    assert f'data-editing-profile-id="{created["id"]}"' in edit_page.text
    assert 'data-profiles-route-mode="edit"' in edit_page.text
    assert 'id="wizard-ip-protection-available-card"' in edit_page.text
    assert 'id="wizard-ai-controls-card"' in edit_page.text

    root = Path(__file__).resolve().parents[1]
    privacy_template = (
        root / "app" / "templates" / "profiles" / "_page_wizard_step_privacy.html"
    ).read_text(encoding="utf-8")
    review_source = (root / "app" / "static" / "profiles_review.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )

    assert 'id="wizard-privacy-vpn-section-status"' in privacy_template
    assert 'id="wizard-ip-protection-available-card"' in privacy_template
    assert 'id="wizard-local-network-access-card"' in privacy_template
    assert 'data-settings-target="policy:IPProtectionAvailable"' in privacy_template
    assert 'data-settings-target="policy:LocalNetworkAccess"' in privacy_template
    assert "ipProtectionManaged: typeof parsed?.IPProtectionAvailable === \"boolean\"" in review_source
    assert "ipProtectionAvailable: parsed?.IPProtectionAvailable === true" in review_source
    assert 'findSettingsTarget("policy:AIControls")' in review_source
    assert '[data-settings-target="policy:IPProtectionAvailable"]' in runtime_source
    assert '[data-settings-target="policy:AIControls"]' in runtime_source
    assert 'wizardLocalNetworkAccessCardEl' in (
        root / "app" / "static" / "profiles_schema_shell_sections.js"
    ).read_text(encoding="utf-8")
    assert '"IPProtectionAvailable",' in workspace_source
    assert '"LocalNetworkAccess",' in workspace_source
    assert '"XSLTEnabled",' in workspace_source
    assert 'if (["AIControls", "GenerativeAI", "VisualSearchEnabled"].includes(policyKey)) return "step_five";' in workspace_source
    assert '"IPProtectionAvailable",' in flow_source
    assert '"LocalNetworkAccess",' in flow_source
    assert '"XSLTEnabled",' in flow_source
    assert 'const siteDataManagedKeys = ["Permissions", "Cookies", "LocalNetworkAccess"];' in flow_source
    assert '"AIControls",' in flow_source

    update_flags = {
        **created["flags"],
        "IPProtectionAvailable": True,
        "AIControls": {
            **created["flags"]["AIControls"],
            "Translations": {
                "Value": "blocked",
                "Locked": True,
            },
        },
    }
    update_response = client.patch(
        f"/api/profiles/{created['id']}",
        json={
            "description": "Saved after guided AI and VPN review",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": update_flags,
            "expected_revision": created["revision"],
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["revision"] == created["revision"] + 1
    assert updated["flags"]["IPProtectionAvailable"] is True
    assert updated["flags"]["AIControls"]["Default"]["Value"] == "available"
    assert updated["flags"]["AIControls"]["Translations"]["Value"] == "blocked"
    assert updated["flags"]["AIControls"]["SidebarChatbot"]["Value"] == "blocked"
    assert updated["flags"]["VisualSearchEnabled"] is False

    export_response = client.get(
        f"/api/export/profiles/{created['id']}/firefox/policies.json?download=1"
    )
    assert export_response.status_code == 200, export_response.text
    exported = export_response.json()["policies"]
    assert exported["IPProtectionAvailable"] is True
    assert exported["AIControls"]["Default"] == {
        "Value": "available",
        "Locked": True,
    }
    assert exported["AIControls"]["Translations"] == {
        "Value": "blocked",
        "Locked": True,
    }
    assert exported["AIControls"]["SidebarChatbot"] == {
        "Value": "blocked",
        "Locked": True,
    }
    assert exported["AIControls"]["SmartWindow"] == {
        "Value": "blocked",
        "Locked": True,
    }
    assert exported["VisualSearchEnabled"] is False


def test_profiles_ui_locale_catalog_exposes_export_lifecycle_finish_line_copy():
    client = make_test_client(app)

    locale_en = client.get("/i18n/en.json")
    locale_ru = client.get("/i18n/ru.json")

    assert locale_en.status_code == 200, locale_en.text
    assert locale_ru.status_code == 200, locale_ru.text

    locale_en_json = locale_en.json()
    locale_ru_json = locale_ru.json()

    assert_has_keys(locale_en_json, P2_3_EXPORT_LIFECYCLE_LOCALE_KEYS)
    assert_has_keys(locale_ru_json, P2_3_EXPORT_LIFECYCLE_LOCALE_KEYS)

    assert locale_en_json["profiles.wizard_export_state_unsaved_existing"] == (
        "Save the latest edits before downloading."
    )
    assert locale_en_json["profiles.wizard_export_download_hint_invalid_dirty"] == (
        "The current file needs fixes. The policies.json download still points to the last saved version."
    )
    assert locale_en_json["profiles.wizard_export_download_hint_ready"] == (
        "The policies.json download already uses the latest saved version."
    )
    assert locale_ru_json["profiles.wizard_export_state_unsaved_new"] == (
        "Сначала сохраните этот профиль."
    )
    assert locale_ru_json["profiles.wizard_export_download_hint_archived"] == (
        "Восстановите архивный профиль, чтобы снова включить скачивание policies.json."
    )


def test_profiles_ui_locale_catalog_exposes_post_roadmap_review_and_history_copy():
    client = make_test_client(app)

    locale_en = client.get("/i18n/en.json")
    locale_ru = client.get("/i18n/ru.json")

    assert locale_en.status_code == 200, locale_en.text
    assert locale_ru.status_code == 200, locale_ru.text

    locale_en_json = locale_en.json()
    locale_ru_json = locale_ru.json()

    assert_has_keys(locale_en_json, PR4_1_POST_ROADMAP_LOCALE_KEYS)
    assert_has_keys(locale_ru_json, PR4_1_POST_ROADMAP_LOCALE_KEYS)

    assert locale_en_json["profiles.compare_guided_areas_title"] == "Differences by guided area"
    assert locale_en_json["profiles.clone_action"] == "Clone and adjust"
    assert locale_en_json["profiles.lifecycle_item_recent_restored"] == (
        "Restored in this session at {value}."
    )
    assert locale_en_json["profiles.wizard_step_memory_step_privacy"] == (
        "Changed privacy, hardening, site permissions, or cleanup posture."
    )
    assert locale_en_json["profiles.compare_guided_area_step_two"] == (
        "Browser access and defaults"
    )
    assert "profiles.compare_guided_area_step_six" not in locale_en_json
    assert "profiles.compare_guided_area_step_seven" not in locale_en_json
    assert locale_en_json["profiles.wizard_export_drilldown_unknown_title"] == (
        "Unknown key: {label}"
    )
    assert locale_en_json["profiles.wizard_step_memory_open"] == "Open step"
    assert locale_en_json["profiles.wizard_step_memory_current"] == "You are here"

    assert locale_ru_json["profiles.compare_guided_areas_title"] == "Различия по шагам мастера"
    assert locale_ru_json["profiles.clone_action"] == "Клонировать и доработать"
    assert locale_ru_json["profiles.clone_meta"] == (
        "Черновик на основе профиля «{name}». Сохраните его как отдельный профиль, когда будете готовы."
    )
    assert locale_ru_json["profiles.lifecycle_item_state_archived"] == (
        "Сейчас этот профиль находится в архиве."
    )
    assert locale_ru_json["profiles.wizard_step_memory_step_browser"] == (
        "Изменены доступ к браузеру, запуск, поиск или значения навигации по умолчанию."
    )
    assert locale_ru_json["profiles.compare_guided_area_step_four"] == (
        "Пользователи, дополнения и сайты"
    )
    assert "profiles.compare_guided_area_step_six" not in locale_ru_json
    assert "profiles.compare_guided_area_step_seven" not in locale_ru_json
    assert locale_ru_json["profiles.wizard_step_memory_open"] == "Открыть шаг"
    assert locale_ru_json["profiles.wizard_step_memory_current"] == "Вы уже здесь"
    assert locale_ru_json["profiles.wizard_export_drilldown_raw_title"] == (
        "Вне Пошагового редактора: {label}"
    )


def test_guided_runtime_mappings_follow_six_step_model():
    root = Path(__file__).resolve().parents[1]
    catalogs_source = (root / "app" / "static" / "profiles_catalogs.js").read_text(
        encoding="utf-8"
    )
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    library_source = (
        root / "app" / "static" / "profiles_library_bootstrap.js"
    ).read_text(encoding="utf-8")

    assert 'general: { step: 2, key: "profiles.wizard_step_two"' in catalogs_source
    assert 'home: { step: 2, key: "profiles.wizard_step_two"' in catalogs_source
    assert 'search: { step: 2, key: "profiles.wizard_step_two"' in catalogs_source
    assert "Array.from({ length: Math.max(0, wizardTotalSteps - 1) }, (_, index) => index + 1)" in flow_source
    assert '2: t("profiles.wizard_step_memory_step_browser")' in flow_source
    assert '"Step 1 of 6: Profile & baseline"' in flow_source
    assert 'return "step_six";' not in workspace_source
    assert 'return "step_seven";' not in workspace_source
    assert 'return "step_six";' not in library_source
    assert 'return "step_seven";' not in library_source


def test_guided_locale_catalog_drops_obsolete_eight_step_labels():
    root = Path(__file__).resolve().parents[1]
    locale_en_json = json.loads((root / "app" / "i18n" / "en.json").read_text(encoding="utf-8"))
    locale_ru_json = json.loads((root / "app" / "i18n" / "ru.json").read_text(encoding="utf-8"))

    for locale_json in (locale_en_json, locale_ru_json):
        assert "profiles.wizard_step_seven" not in locale_json
        assert "profiles.wizard_step_seven_copy" not in locale_json
        assert "profiles.wizard_step_eight" not in locale_json
        assert "profiles.wizard_step_eight_copy" not in locale_json


def test_profiles_public_workflow_smoke():
    client = make_test_client(app)
    payload = _make_payload()

    validate_before = client.post(
        f"/api/validate/{payload['schema_version']}",
        json={"document": payload["flags"]},
    )
    assert validate_before.status_code == 200, validate_before.text
    assert validate_before.json()["ok"] is True

    created_response = client.post("/api/profiles", json=payload)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    profile_id = created["id"]

    updated_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved from UI smoke",
            "owner": "sec@example.org",
            "flags": {"DisableTelemetry": False},
        },
    )
    assert updated_response.status_code == 200, updated_response.text
    updated = updated_response.json()
    assert updated["description"] == "Saved from UI smoke"
    assert updated["flags"] == {"DisableTelemetry": False}

    list_response = client.get("/api/profiles", params={"q": payload["name"]})
    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == profile_id for item in list_response.json())

    export_firefox = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert export_firefox.status_code == 200, export_firefox.text
    assert export_firefox.json() == {
        "policies": {
            "DisableTelemetry": False,
        }
    }

    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    hidden_export = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert hidden_export.status_code == 404

    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200, restore_response.text
    restored = restore_response.json()
    assert restored["is_deleted"] is False

    restored_export = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert restored_export.status_code == 200, restored_export.text
    assert restored_export.json()["policies"] == {"DisableTelemetry": False}

    hard_delete_response = client.delete(f"/api/profiles/{profile_id}/hard")
    assert hard_delete_response.status_code == 204

    deleted_get = client.get(f"/api/profiles/{profile_id}")
    assert deleted_get.status_code == 404

    reset_response = client.delete("/api/profiles/reset")
    assert reset_response.status_code == 200, reset_response.text
    assert "deleted" in reset_response.json()


def test_create_corporate_cis_l2_browser_regression_can_download_policies_json():
    client = make_test_client(app)

    new_page = client.get("/profiles/new")
    assert new_page.status_code == 200, new_page.text
    assert_contains_all(
        new_page.text,
        (
            'data-scenario-key="corporate_default" aria-pressed="true"',
            'data-starter-key="basic_corporate" aria-pressed="true"',
            'data-cis-layer-key="cis_l2"',
            'id="save"',
            'id="wizard-export-save-action"',
            'id="wizard-export-firefox-policies"',
        ),
    )

    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    flow_source = (root / "app" / "static" / "profiles_wizard_flow.js").read_text(
        encoding="utf-8"
    )

    assert 'let wizardScenario = "corporate_default";' in flow_source
    assert "setWizardComplianceLayer(button.dataset.cisLayerKey);" in runtime_source
    assert 'saveButtonEl.addEventListener("click", saveCurrent);' in runtime_source
    assert 'event.target.closest("#wizard-export-save-action")' in runtime_source
    assert "saveButtonEl.click();" in runtime_source
    assert "buildCreatePayload(form, parsedFlags, compliancePayload)" in workspace_source
    assert "setLinkHref(wizardExportFirefoxPoliciesEl, firefoxPoliciesHref);" in workspace_source

    schema_version = "release-151"
    catalog = get_wizard_starter_catalog()
    merged = catalog["compliance_merged_presets"]["basic_corporate"]["cis_l2"][
        schema_version
    ]
    flags = merged["policy_values"]
    metadata = catalog["compliance_metadata"]
    payload = {
        "name": f"Corporate CIS L2 Browser-{uuid.uuid4().hex[:8]}",
        "description": "Created by the browser regression path",
        "owner": "security@example.org",
        "schema_version": schema_version,
        "flags": flags,
        "compliance": {
            "framework": "cis",
            "benchmark_id": metadata.get("benchmark_id") or "cis-firefox-esr-gpo",
            "benchmark_version": metadata.get("upstream_version") or "1.0.0",
            "layer": "cis_l2",
            "summary": merged["summary"],
            "decisions": merged["decisions"],
        },
    }

    validate_response = client.post(
        f"/api/validate/{schema_version}",
        json={"document": payload["flags"]},
    )
    assert validate_response.status_code == 200, validate_response.text
    assert validate_response.json()["ok"] is True

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["schema_version"] == schema_version
    assert created["compliance"]["framework"] == "cis"
    assert created["compliance"]["layer"] == "cis_l2"
    assert created["flags"] == flags

    export_response = client.get(
        f"/api/export/profiles/{created['id']}/firefox/policies.json"
        "?download=1&pretty=1"
    )
    assert export_response.status_code == 200, export_response.text
    assert export_response.headers["content-type"].startswith("application/json")
    content_disposition = export_response.headers.get("content-disposition", "")
    assert "attachment" in content_disposition.lower()
    assert "policies.json" in content_disposition.lower()

    exported = export_response.json()
    assert exported == {"policies": flags}
    assert exported["policies"]["DisableTelemetry"] is True
    assert exported["policies"]["DisableFirefoxAccounts"] is True
    assert exported["policies"]["ExtensionSettings"]["*"]["installation_mode"] == "blocked"
    assert (
        exported["policies"]["Preferences"]["media.peerconnection.enabled"]["Value"]
        is False
    )


def test_library_to_editor_browser_regression_can_load_and_save_guided_homepage():
    client = make_test_client(app)
    original_homepage = "https://portal.example.local/"
    updated_homepage = "https://portal.example.local/finance/"
    payload = {
        "name": f"Library Editor Browser-{uuid.uuid4().hex[:8]}",
        "description": "Created before opening from the library",
        "owner": "desktop@example.org",
        "schema_version": "release-151",
        "flags": {
            "DisableTelemetry": True,
            "Homepage": {
                "URL": original_homepage,
                "Locked": True,
                "StartPage": "homepage-locked",
            },
        },
    }

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    profile_id = created["id"]

    library_response = client.get("/profiles")
    assert library_response.status_code == 200, library_response.text
    assert_contains_all(
        library_response.text,
        (
            'data-profiles-route-mode="library"',
            'data-profiles-template-kind="library"',
            'id="library-panel"',
            'id="search"',
            'id="create-profile-link"',
        ),
    )
    list_response = client.get("/api/profiles", params={"q": payload["name"]})
    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == profile_id for item in list_response.json())

    root = Path(__file__).resolve().parents[1]
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    network_source = (root / "app" / "static" / "profiles_network.js").read_text(
        encoding="utf-8"
    )

    assert "const editHref = `/profiles/${profile.id}/edit`;" in workspace_source
    assert '<a class="library-row-title-button" href="${editHref}" target="_blank" rel="noopener">' in workspace_source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in runtime_source
    assert "editor.setValue(toEditorValue(getCurrentRaw(), documentRef.getElementById(\"mode\").value));" in workspace_source
    assert "syncWizardNetworkFromEditor();" in workspace_source
    assert "const homepageUrl = wizardHomepageUrlEl.value.trim();" in network_source
    assert "if (homepageUrl) nextHomepage.URL = homepageUrl;" in network_source
    assert "buildUpdatePayload(form, parsedFlags, compliancePayload" in workspace_source

    edit_response = client.get(f"/profiles/{profile_id}/edit")
    assert edit_response.status_code == 200, edit_response.text
    assert f'data-editing-profile-id="{profile_id}"' in edit_response.text
    assert 'data-profiles-route-mode="edit"' in edit_response.text
    assert 'data-profiles-template-kind="editor"' in edit_response.text
    assert f"<title>{payload['name']} — Guided editor — Browser Policy Manager</title>" in edit_response.text

    next_flags = {
        **created["flags"],
        "Homepage": {
            **created["flags"]["Homepage"],
            "URL": updated_homepage,
        },
    }
    update_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved after guided homepage edit",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": next_flags,
            "expected_revision": created["revision"],
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["revision"] == created["revision"] + 1
    assert updated["flags"]["Homepage"]["URL"] == updated_homepage
    assert updated["flags"]["Homepage"]["Locked"] is True

    export_response = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert export_response.status_code == 200, export_response.text
    assert export_response.json()["policies"]["Homepage"]["URL"] == updated_homepage


def test_visual_and_json_same_profile_regression_can_save_without_conflict():
    client = make_test_client(app)
    payload = {
        "name": f"Visual JSON Browser-{uuid.uuid4().hex[:8]}",
        "description": "Shared visual and JSON route regression",
        "owner": "platform@example.org",
        "schema_version": "release-151",
        "flags": {
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
            },
        },
    }

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    profile_id = created["id"]

    root = Path(__file__).resolve().parents[1]
    runtime_source = (root / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    bootstrap_source = (
        root / "app" / "static" / "profiles_bootstrap_core.js"
    ).read_text(encoding="utf-8")

    assert '(routeMode === "edit" || routeMode === "settings" || routeMode === "json") && editingProfileId' in runtime_source
    assert "await loadProfile(editingProfileId, { skipConfirm: true, syncLibrary: false });" in runtime_source
    assert "setJsonHandoffContext(null);" in runtime_source
    assert "applyJsonFocusTarget(focusTarget);" in runtime_source
    assert "saveButtonEl.addEventListener(\"click\", saveCurrent);" in runtime_source
    assert "saveCurrent();" in runtime_source
    assert "setSaveCurrent(workspace.saveCurrent);" in bootstrap_source
    assert "includeExpectedRevision ? buildExpectedRevisionPayload() : {}" in workspace_source

    visual_response = client.get(f"/profiles/{profile_id}/edit")
    assert visual_response.status_code == 200, visual_response.text
    assert f'data-editing-profile-id="{profile_id}"' in visual_response.text
    assert 'data-profiles-route-mode="edit"' in visual_response.text
    assert 'data-profiles-template-kind="editor"' in visual_response.text
    assert f'href="/profiles/{profile_id}/json?focus=editor"' in visual_response.text

    visual_flags = {
        **created["flags"],
        "Homepage": {
            **created["flags"]["Homepage"],
            "URL": "https://portal.example.local/visual/",
        },
    }
    visual_save_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved from visual editor route",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": visual_flags,
            "expected_revision": created["revision"],
        },
    )
    assert visual_save_response.status_code == 200, visual_save_response.text
    visual_saved = visual_save_response.json()
    assert visual_saved["revision"] == created["revision"] + 1
    assert visual_saved["flags"]["Homepage"]["URL"] == "https://portal.example.local/visual/"

    json_response = client.get(
        f"/profiles/{profile_id}/json?return=/profiles/{profile_id}/edit&focus=editor"
    )
    assert json_response.status_code == 200, json_response.text
    assert f'data-editing-profile-id="{profile_id}"' in json_response.text
    assert 'data-profiles-route-mode="json"' in json_response.text
    assert 'data-profiles-template-kind="json"' in json_response.text
    assert f'data-json-return-url="/profiles/{profile_id}/edit"' in json_response.text
    assert 'id="json-return-link"' not in json_response.text
    assert 'data-json-focus-target="editor"' in json_response.text
    assert f"<title>{payload['name']} — JSON editor — Browser Policy Manager</title>" in json_response.text

    json_flags = {
        **visual_saved["flags"],
        "DisableFirefoxStudies": True,
    }
    json_save_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved from JSON editor route",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": json_flags,
            "expected_revision": visual_saved["revision"],
        },
    )
    assert json_save_response.status_code == 200, json_save_response.text
    json_saved = json_save_response.json()
    assert json_saved["revision"] == visual_saved["revision"] + 1
    assert json_saved["flags"]["Homepage"]["URL"] == "https://portal.example.local/visual/"
    assert json_saved["flags"]["DisableFirefoxStudies"] is True

    export_response = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert export_response.status_code == 200, export_response.text
    exported = export_response.json()["policies"]
    assert exported["Homepage"]["URL"] == "https://portal.example.local/visual/"
    assert exported["DisableFirefoxStudies"] is True
    assert exported["DisableTelemetry"] is True


def test_stale_save_conflict_browser_regression_does_not_overwrite_profile():
    client = make_test_client(app)
    payload = {
        "name": f"Stale Save Browser-{uuid.uuid4().hex[:8]}",
        "description": "Initial shared tab state",
        "owner": "secops@example.org",
        "schema_version": "release-151",
        "flags": {
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
            },
        },
    }

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    profile_id = create_response.json()["id"]

    tab_a = client.get(f"/api/profiles/{profile_id}")
    tab_b = client.get(f"/api/profiles/{profile_id}")
    assert tab_a.status_code == 200, tab_a.text
    assert tab_b.status_code == 200, tab_b.text
    tab_a_profile = tab_a.json()
    tab_b_profile = tab_b.json()
    assert tab_a_profile["revision"] == tab_b_profile["revision"] == 1

    root = Path(__file__).resolve().parents[1]
    command_deck = (
        root / "app" / "templates" / "profiles" / "_page_command_deck.html"
    ).read_text(encoding="utf-8")
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    data_source = (root / "app" / "static" / "profiles_data.js").read_text(
        encoding="utf-8"
    )

    assert 'id="save-conflict-panel"' in command_deck
    assert 'role="alert"' in command_deck
    assert 'id="save-conflict-reload"' in command_deck
    assert 'id="save-conflict-save-copy"' in command_deck
    assert 'id="save-conflict-overwrite"' in command_deck
    assert "function isRevisionConflictError(error)" in workspace_source
    assert "return Number(error?.status) === 409;" in workspace_source
    assert "function showSaveConflictState(error)" in workspace_source
    assert "saveConflictPanelEl.hidden = false;" in workspace_source
    assert 't("profiles.conflict_revision_detail")' in workspace_source
    assert "showSaveConflictState(e);" in workspace_source
    assert "return false;" in workspace_source
    assert "error.status = res.status;" in data_source
    assert "error.detail = payload.detail;" in data_source

    tab_a_flags = {
        **tab_a_profile["flags"],
        "Homepage": {
            **tab_a_profile["flags"]["Homepage"],
            "URL": "https://portal.example.local/tab-a/",
        },
    }
    tab_a_save = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved by tab A",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": tab_a_flags,
            "expected_revision": tab_a_profile["revision"],
        },
    )
    assert tab_a_save.status_code == 200, tab_a_save.text
    tab_a_saved = tab_a_save.json()
    assert tab_a_saved["revision"] == tab_a_profile["revision"] + 1

    tab_b_flags = {
        **tab_b_profile["flags"],
        "Homepage": {
            **tab_b_profile["flags"]["Homepage"],
            "URL": "https://portal.example.local/tab-b-stale/",
        },
        "DisableFirefoxStudies": True,
    }
    stale_save = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Stale tab B should not persist",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": tab_b_flags,
            "expected_revision": tab_b_profile["revision"],
        },
    )
    assert stale_save.status_code == 409, stale_save.text
    assert stale_save.json()["detail"] == {
        "message": "Profile has been modified since it was loaded",
        "profile_id": profile_id,
        "current_revision": tab_a_saved["revision"],
        "expected_revision": tab_b_profile["revision"],
    }

    after_conflict = client.get(f"/api/profiles/{profile_id}")
    assert after_conflict.status_code == 200, after_conflict.text
    current = after_conflict.json()
    assert current["description"] == "Saved by tab A"
    assert current["revision"] == tab_a_saved["revision"]
    assert current["flags"]["Homepage"]["URL"] == "https://portal.example.local/tab-a/"
    assert "DisableFirefoxStudies" not in current["flags"]

    export_response = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
    assert export_response.status_code == 200, export_response.text
    exported = export_response.json()["policies"]
    assert exported["Homepage"]["URL"] == "https://portal.example.local/tab-a/"
    assert "DisableFirefoxStudies" not in exported


def test_save_as_copy_conflict_regression_preserves_local_draft_as_new_profile():
    client = make_test_client(app)
    original_name = f"Save Copy Browser-{uuid.uuid4().hex[:8]}"
    payload = {
        "name": original_name,
        "description": "Initial shared tab state",
        "owner": "secops@example.org",
        "schema_version": "release-151",
        "flags": {
            "DisableTelemetry": True,
            "Homepage": {
                "URL": "https://portal.example.local/",
                "Locked": True,
            },
        },
    }

    create_response = client.post("/api/profiles", json=payload)
    assert create_response.status_code == 201, create_response.text
    profile_id = create_response.json()["id"]

    tab_a_profile = client.get(f"/api/profiles/{profile_id}").json()
    tab_b_profile = client.get(f"/api/profiles/{profile_id}").json()
    assert tab_a_profile["revision"] == tab_b_profile["revision"] == 1

    root = Path(__file__).resolve().parents[1]
    workspace_source = (root / "app" / "static" / "profiles_workspace.js").read_text(
        encoding="utf-8"
    )
    command_deck = (
        root / "app" / "templates" / "profiles" / "_page_command_deck.html"
    ).read_text(encoding="utf-8")

    assert "async function saveConflictAsCopy()" in workspace_source
    assert "const copyName = buildConflictCopyName(form);" in workspace_source
    assert "buildCreatePayload(form, parsedFlags, compliancePayload, { name: copyName })" in workspace_source
    assert "const created = await createProfile(" in workspace_source
    assert "await loadProfile(created.id, { skipConfirm: true });" in workspace_source
    assert "clearSaveConflictState();" in workspace_source
    assert 't("profiles.conflict_copy_created").replace("{name}", created.name)' in workspace_source
    assert "saveConflictSaveCopyEl?.addEventListener(\"click\", async () =>" in workspace_source
    assert "await saveConflictAsCopy();" in workspace_source
    assert 'id="save-conflict-save-copy"' in command_deck
    assert 'data-i18n="profiles.conflict_save_as_copy"' in command_deck

    tab_a_flags = {
        **tab_a_profile["flags"],
        "Homepage": {
            **tab_a_profile["flags"]["Homepage"],
            "URL": "https://portal.example.local/tab-a/",
        },
    }
    tab_a_save = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Saved by tab A",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": tab_a_flags,
            "expected_revision": tab_a_profile["revision"],
        },
    )
    assert tab_a_save.status_code == 200, tab_a_save.text

    local_draft_flags = {
        **tab_b_profile["flags"],
        "Homepage": {
            **tab_b_profile["flags"]["Homepage"],
            "URL": "https://portal.example.local/tab-b-copy/",
        },
        "DisableFirefoxStudies": True,
    }
    stale_save = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Stale tab B should become a copy",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": local_draft_flags,
            "expected_revision": tab_b_profile["revision"],
        },
    )
    assert stale_save.status_code == 409, stale_save.text

    copy_name = f"{original_name} conflict copy from r{tab_b_profile['revision']} at test"
    copy_response = client.post(
        "/api/profiles",
        json={
            "name": copy_name,
            "description": "Stale tab B should become a copy",
            "owner": payload["owner"],
            "schema_version": payload["schema_version"],
            "flags": local_draft_flags,
        },
    )
    assert copy_response.status_code == 201, copy_response.text
    copied = copy_response.json()
    assert copied["id"] != profile_id
    assert copied["name"] == copy_name
    assert copied["revision"] == 1
    assert copied["flags"]["Homepage"]["URL"] == "https://portal.example.local/tab-b-copy/"
    assert copied["flags"]["DisableFirefoxStudies"] is True

    original_after_copy = client.get(f"/api/profiles/{profile_id}")
    assert original_after_copy.status_code == 200, original_after_copy.text
    original = original_after_copy.json()
    assert original["description"] == "Saved by tab A"
    assert original["flags"]["Homepage"]["URL"] == "https://portal.example.local/tab-a/"
    assert "DisableFirefoxStudies" not in original["flags"]

    listed_copy = client.get("/api/profiles", params={"q": copy_name})
    assert listed_copy.status_code == 200, listed_copy.text
    assert any(item["id"] == copied["id"] for item in listed_copy.json())

    copy_export = client.get(f"/api/export/profiles/{copied['id']}/firefox/policies.json")
    assert copy_export.status_code == 200, copy_export.text
    exported_copy = copy_export.json()["policies"]
    assert exported_copy["Homepage"]["URL"] == "https://portal.example.local/tab-b-copy/"
    assert exported_copy["DisableFirefoxStudies"] is True


def test_profiles_lifecycle_markers_stay_consistent_for_review_surfaces():
    client = make_test_client(app)
    payload = _make_payload()

    created_response = client.post("/api/profiles", json=payload)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    profile_id = created["id"]

    assert created["is_deleted"] is False
    assert created["revision"] == 1
    assert created["created_at"]
    assert created["updated_at"]

    first_created_at = created["created_at"]
    first_updated_at = created["updated_at"]

    patched_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={
            "description": "Lifecycle regression update",
            "expected_revision": created["revision"],
        },
    )
    assert patched_response.status_code == 200, patched_response.text
    patched = patched_response.json()
    assert patched["revision"] == created["revision"] + 1
    assert patched["created_at"] == first_created_at
    assert patched["updated_at"] >= first_updated_at
    assert patched["description"] == "Lifecycle regression update"

    archived_response = client.delete(f"/api/profiles/{profile_id}")
    assert archived_response.status_code == 204

    archived_hidden = client.get(f"/api/profiles/{profile_id}")
    assert archived_hidden.status_code == 404, archived_hidden.text

    archived_with_deleted = client.get(
        f"/api/export/profiles/{profile_id}/firefox/policies.json?include_deleted=true"
    )
    assert archived_with_deleted.status_code == 200, archived_with_deleted.text
    archived = archived_with_deleted.json()
    assert archived["policies"]["DisableTelemetry"] is True

    restored_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restored_response.status_code == 200, restored_response.text
    restored = restored_response.json()
    assert restored["is_deleted"] is False
    assert restored["created_at"] == first_created_at
    assert restored["updated_at"] >= first_updated_at
