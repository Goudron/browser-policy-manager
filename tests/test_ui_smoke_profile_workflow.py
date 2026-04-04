from __future__ import annotations

import uuid

from app.main import app
from tests.support import assert_contains_all, assert_has_keys, make_test_client

UI_SHELL_TOKENS = (
    'id="profile-name"',
    'id="profile-owner"',
    'id="profile-description"',
    'id="lang"',
    'id="wizard-panel"',
    'id="wizard-starter-catalog"',
    'id="wizard-shared-device-workflow-copy"',
    'id="wizard-shared-device-workflow-list"',
    'id="wizard-clone-handoff-panel"',
    'id="wizard-clone-handoff-copy" role="status" aria-live="polite"',
    'id="wizard-clone-handoff-list" role="list"',
    'id="profile-derived-note"',
    'id="profile-clone-handoff-panel"',
    'id="profile-clone-handoff-copy" role="status" aria-live="polite"',
    'id="profile-clone-handoff-list" role="list"',
    'id="profile-lifecycle-panel"',
    'id="profile-lifecycle-copy"',
    'id="profile-lifecycle-list"',
    'id="compare-panel"',
    'id="compare-clear"',
    'id="compare-empty"',
    'id="compare-active"',
    'id="compare-current-name"',
    'id="compare-other-name"',
    'id="compare-changes-list"',
    'id="compare-guided-areas-copy"',
    'id="compare-guided-areas-list" class="compare-changes-list" role="list"',
    'id="list-summary"',
    'id="list-total-summary"',
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
    'id="wizard-settings-map-general"',
    'id="wizard-settings-docs-general"',
    'id="wizard-settings-map-privacy"',
    'id="wizard-settings-docs-privacy"',
    'id="wizard-settings-map-extensions"',
    'id="hard-delete"',
    'id="reset-library"',
    'data-starter-key="basic_corporate"',
    'data-starter-key="classroom_kiosk"',
    'data-starter-key="soc_hard"',
    'id="wizard-summary-starter"',
    'id="wizard-homepage-url"',
    'id="wizard-homepage-shared-presets"',
    'id="wizard-search-bar"',
    'id="wizard-search-default-engine"',
    'id="wizard-search-engine-add"',
    'id="wizard-search-engine-list"',
    'id="wizard-preferences-general-add"',
    'id="wizard-preferences-home-add"',
    'id="wizard-preferences-search-add"',
    'id="wizard-preferences-privacy-add"',
    'id="wizard-preferences-sync-add"',
    'id="wizard-preferences-general-groups"',
    'id="wizard-preferences-sync-groups"',
    'id="wizard-preferences-general-docs"',
    'id="wizard-preferences-sync-docs"',
    'id="wizard-preference-row-template"',
    'id="wizard-preferences-known-list"',
    'id="wizard-preferences-general-bundles"',
    'id="wizard-preferences-home-bundles"',
    'id="wizard-preferences-search-bundles"',
    'id="wizard-preferences-privacy-bundles"',
    'id="wizard-preferences-sync-bundles"',
    'id="wizard-preferences-general-known"',
    'id="wizard-preferences-home-known"',
    'id="wizard-preferences-search-known"',
    'id="wizard-preferences-privacy-known"',
    'id="wizard-preferences-sync-known"',
    "wizard-search-engine-preset-status",
    'data-settings-target="policy:DisableTelemetry"',
    'data-settings-target="field:wizard-proxy-mode"',
    'data-settings-target="pref-section:general"',
    'data-settings-target="pref-section:sync"',
    'data-settings-target="search-engine-preset:duckduckgo"',
    'data-preference-section="general"',
    'data-preference-section="sync"',
    'data-search-engine-preset="docs_portal"',
    'data-search-engine-preset="ticket_queue"',
    'data-search-engine-preset="wiki_portal"',
    'data-search-engine-preset="duckduckgo"',
    'data-search-engine-preset-status',
    'data-search-engine-field="Name"',
    'data-search-engine-field="URLTemplate"',
    'data-search-engine-summary',
    'data-search-engine-warning',
    'id="wizard-new-tab-page"',
    'id="wizard-override-first-run"',
    'data-firefox-home-key="Search"',
    'id="wizard-website-filter-shared-presets"',
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
    'id="wizard-trust-auth-workflow-copy"',
    'id="wizard-trust-auth-workflow-list"',
    'id="wizard-upkeep-governance-copy"',
    'id="wizard-upkeep-governance-list"',
    'id="wizard-home-summary-homepage"',
    'id="wizard-home-summary-overrides"',
    'id="wizard-home-summary-firefox-home"',
    'id="wizard-home-summary-user-messaging"',
    'id="wizard-home-summary-homepage-jump"',
    'id="wizard-home-summary-overrides-jump"',
    'id="wizard-home-summary-firefox-home-jump"',
    'id="wizard-home-summary-user-messaging-jump"',
    'id="wizard-homepage-section-status"',
    'id="wizard-home-overrides-section-status"',
    'id="wizard-firefox-home-section-status"',
    'id="wizard-home-surfaces-workflow-copy"',
    'id="wizard-home-surfaces-workflow-list"',
    'id="wizard-search-summary-defaults"',
    'id="wizard-search-summary-hidden"',
    'id="wizard-search-summary-custom"',
    'id="wizard-search-summary-suggest"',
    'id="wizard-search-summary-defaults-jump"',
    'id="wizard-search-summary-hidden-jump"',
    'id="wizard-search-summary-custom-jump"',
    'id="wizard-search-summary-suggest-jump"',
    'id="wizard-search-defaults-section-status"',
    'id="wizard-firefox-suggest-section-status"',
    'id="wizard-search-surfaces-workflow-copy"',
    'id="wizard-search-surfaces-workflow-list"',
    'id="wizard-language-governance-copy"',
    'id="wizard-language-governance-list"',
    'id="wizard-privacy-summary-permissions-configured"',
    'id="wizard-privacy-summary-permissions-locked"',
    'id="wizard-privacy-summary-cookies"',
    'id="wizard-privacy-summary-permissions-configured-jump"',
    'id="wizard-privacy-summary-permissions-locked-jump"',
    'id="wizard-privacy-summary-cookies-jump"',
    'id="wizard-extension-default-mode"',
    'id="wizard-extension-install"',
    'id="wizard-extension-locked"',
    'id="wizard-extension-uninstall"',
    'id="wizard-extension-summary-curated"',
    'id="wizard-extension-summary-arbitrary"',
    'id="wizard-extension-summary-custom-urls"',
    'id="wizard-extension-summary-curated-jump"',
    'id="wizard-extension-summary-arbitrary-jump"',
    'id="wizard-extension-summary-custom-urls-jump"',
    'id="wizard-bookmark-summary-links"',
    'id="wizard-bookmark-summary-folders"',
    'id="wizard-bookmark-summary-nested"',
    'id="wizard-bookmark-summary-links-jump"',
    'id="wizard-bookmark-summary-folders-jump"',
    'id="wizard-bookmark-summary-nested-jump"',
    'id="wizard-ai-summary-availability"',
    'id="wizard-ai-summary-providers"',
    'id="wizard-ai-summary-surfaces"',
    'id="wizard-ai-summary-availability-jump"',
    'id="wizard-ai-summary-providers-jump"',
    'id="wizard-ai-summary-surfaces-jump"',
    'id="wizard-website-access-summary-blocked"',
    'id="wizard-website-access-summary-exceptions"',
    'id="wizard-website-access-summary-handlers"',
    'id="wizard-website-access-summary-blocked-jump"',
    'id="wizard-website-access-summary-exceptions-jump"',
    'id="wizard-website-access-summary-handlers-jump"',
    'id="wizard-website-governance-workflow"',
    'id="wizard-website-governance-copy"',
    'id="wizard-website-governance-list"',
    'id="wizard-website-governance-open-advanced"',
    'id="wizard-website-next-filter"',
    'id="wizard-website-next-handlers"',
    'id="wizard-website-next-fine-tuning"',
    'id="wizard-install-addons-permission-card"',
    'id="wizard-extension-settings-card"',
    'id="wizard-ai-section-status"',
    'id="wizard-ai-providers-section-status"',
    'id="wizard-ai-surfaces-section-status"',
    'id="wizard-ai-fine-tuning-toggle"',
    'id="wizard-ai-fine-tuning-panel"',
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
    'data-extension-profile-status="uBlock0@raymondhill.net"',
    'data-extension-profile-status="adguardadblocker@adguard.com"',
    'data-extension-profile-status="https-everywhere@eff.org"',
    'data-policy-key="DisableTelemetry"',
    'data-policy-key="DisableFirefoxAccounts"',
    'data-policy-key="BlockAboutProfiles"',
    'data-policy-key="DisableAppUpdate"',
    'id="editor"',
    'id="save"',
    'id="validate"',
    'id="download-json"',
    'id="download-yaml"',
    'id="download-firefox-policies"',
    'id="workspace-signal"',
    "/api/profiles",
    "/api/export/profiles",
    "/api/validate/",
    "/i18n/${lang}.json",
    "resolveBrowserLanguage",
    "Ctrl/Cmd+S to save",
)

UI_LOCALE_KEYS = (
    "profiles.title",
    "profiles.create_submit",
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
    "profiles.wizard_step_six",
    "profiles.wizard_step_seven",
    "profiles.wizard_step_eight",
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
    "profiles.wizard_privacy_review_permissions_locked",
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
    "profiles.wizard_ai_governance_title",
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
    "profiles.wizard_website_filter_shared_preset_allow_only_title",
    "profiles.wizard_homepage_section_state_invalid",
    "profiles.wizard_firefox_home_section_state_configured",
    "profiles.wizard_search_defaults_section_state_conflict",
    "profiles.wizard_firefox_suggest_section_state_conflict",
    "profiles.wizard_search_title",
    "profiles.wizard_search_add_title",
    "profiles.wizard_search_presets_title",
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
    "profiles.wizard_bookmarks_review_title",
    "profiles.wizard_bookmarks_review_nested",
    "profiles.wizard_bookmarks_review_open",
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
    'id="advanced-handoff-panel"',
    'id="advanced-context-panel"',
    'id="advanced-context-return"',
    'id="wizard-guided-coverage-step-2"',
    'id="wizard-guided-coverage-step-8"',
    'id="wizard-hardening-section-status"',
    'id="wizard-cleanup-section-status"',
    'id="wizard-hardening-governance-workflow"',
    'id="wizard-hardening-governance-copy"',
    'id="wizard-hardening-governance-list"',
    'id="wizard-hardening-governance-open-advanced"',
    'id="wizard-hardening-next-posture"',
    'id="wizard-hardening-next-cleanup"',
    'id="wizard-hardening-next-sites"',
    'id="wizard-privacy-summary-user-data"',
    'id="wizard-privacy-summary-cleanup"',
    'id="wizard-extension-rollout-presets"',
    'id="wizard-extension-governance-workflow"',
    'id="wizard-extension-governance-copy"',
    'id="wizard-extension-governance-list"',
    'id="wizard-extension-governance-open-advanced"',
    'id="wizard-extension-next-rollout"',
    'id="wizard-extension-next-curated"',
    'id="wizard-extension-next-fine-tuning"',
    'id="wizard-extension-focus-presets"',
    'id="wizard-language-ai-handoff"',
    'id="wizard-ai-focus-presets"',
    'id="wizard-ai-governance-copy"',
    'id="wizard-ai-governance-list"',
    'id="wizard-export-baseline-copy"',
    'id="wizard-export-baseline-list"',
    'id="wizard-export-next-steps"',
    'id="wizard-export-ready-now"',
    'id="wizard-export-included-now"',
    'id="wizard-export-missing-now"',
    'id="wizard-export-review-now"',
    'id="wizard-export-download-hint"',
    'data-hardening-preset="balanced"',
    'data-cleanup-preset="shared"',
    'data-extension-rollout-preset="managed"',
    'data-extension-focus-preset="mixed"',
    'data-ai-focus-preset="mixed"',
)

P2_3_LOCALE_KEYS = (
    "profiles.advanced_context_title",
    "profiles.advanced_context_return",
    "profiles.wizard_hardening_preset_balanced_title",
    "profiles.wizard_hardening_governance_title",
    "profiles.wizard_cleanup_preset_shared_title",
    "profiles.wizard_privacy_review_user_data",
    "profiles.wizard_privacy_review_cleanup",
    "profiles.wizard_extensions_preset_managed_title",
    "profiles.wizard_extensions_governance_title",
    "profiles.wizard_language_ai_handoff_optional",
    "profiles.wizard_export_baseline_summary_title",
    "profiles.wizard_export_download_hint_unsaved_existing",
    "profiles.wizard_export_shareable_title",
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
    "profiles.wizard_step_memory_step_network",
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
        "schema_version": "esr-140.9",
        "owner": "ops@example.org",
        "flags": {
            "DisableTelemetry": True,
            "DisablePrivateBrowsing": True,
        },
    }


def test_profiles_ui_shell_exposes_public_hooks():
    client = make_test_client(app)

    page = client.get("/profiles")
    assert page.status_code == 200, page.text
    assert page.headers["content-type"].startswith("text/html")
    assert_contains_all(page.text, UI_SHELL_TOKENS)


def test_profiles_ui_shell_exposes_recent_ux_regression_hooks():
    client = make_test_client(app)

    page = client.get("/profiles")
    assert page.status_code == 200, page.text
    assert page.headers["content-type"].startswith("text/html")
    assert_contains_all(page.text, P2_3_UX_REGRESSION_TOKENS)


def test_profiles_ui_shell_keeps_guided_first_viewport_order_contract():
    client = make_test_client(app)

    page = client.get("/profiles")
    assert page.status_code == 200, page.text
    html = page.text

    wizard_index = html.index('id="wizard-panel"')
    command_deck_index = html.index('id="command-deck"')
    overview_index = html.index('id="overview-panel"')
    search_index = html.index('id="wizard-settings-search-input"')
    first_step_index = html.index('id="wizard-step-1"')

    assert wizard_index < command_deck_index < overview_index
    assert wizard_index < search_index < command_deck_index
    assert wizard_index < first_step_index < command_deck_index


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

    assert locale_en_json["profiles.advanced_context_title"] == "Continue in Advanced document"
    assert locale_en_json["profiles.wizard_export_baseline_summary_title"] == "Baseline guardrails"
    assert locale_en_json["profiles.wizard_export_shareable_title"] == "Shareable summary"
    assert locale_en_json["profiles.wizard_export_included_title"] == (
        "Included in the files you download now"
    )
    assert locale_ru_json["profiles.advanced_context_title"] == "Продолжение в Техдокументе"
    assert locale_ru_json["profiles.advanced_context_return"] == "Вернуться к этому шагу"
    assert locale_ru_json["profiles.wizard_export_shareable_title"] == "Выжимка для передачи"
    assert locale_ru_json["profiles.wizard_export_missing_title"] == (
        "Что пока не попадёт в скачивание"
    )


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
        "The current file needs fixes. Download links still point to the last saved version."
    )
    assert locale_en_json["profiles.wizard_export_download_hint_ready"] == (
        "These download buttons already use the latest saved version."
    )
    assert locale_ru_json["profiles.wizard_export_state_unsaved_new"] == (
        "Сначала сохраните этот профиль."
    )
    assert locale_ru_json["profiles.wizard_export_download_hint_archived"] == (
        "Восстановите архивный профиль, чтобы снова включить скачивание."
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
    assert locale_ru_json["profiles.wizard_step_memory_step_network"] == (
        "Изменены поддержка браузера, прокси или корпоративный сетевой доступ."
    )
    assert locale_ru_json["profiles.wizard_step_memory_open"] == "Открыть шаг"
    assert locale_ru_json["profiles.wizard_step_memory_current"] == "Вы уже здесь"
    assert locale_ru_json["profiles.wizard_export_drilldown_raw_title"] == (
        "Только для Техдокумента: {label}"
    )


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
    assert updated["flags"]["DisableTelemetry"] is False
    assert updated["flags"]["DisablePrivateBrowsing"] is True

    list_response = client.get("/api/profiles", params={"q": payload["name"]})
    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == profile_id for item in list_response.json())

    export_json = client.get(f"/api/export/profiles/{profile_id}.json")
    assert export_json.status_code == 200, export_json.text
    assert export_json.json()["id"] == profile_id

    export_yaml = client.get(f"/api/export/profiles/{profile_id}?fmt=yaml")
    assert export_yaml.status_code == 200, export_yaml.text
    assert "DisableTelemetry" in export_yaml.text

    delete_response = client.delete(f"/api/profiles/{profile_id}")
    assert delete_response.status_code == 204

    hidden_export = client.get(f"/api/export/profiles/{profile_id}?fmt=json")
    assert hidden_export.status_code == 404

    restore_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restore_response.status_code == 200, restore_response.text
    restored = restore_response.json()
    assert restored["is_deleted"] is False

    restored_export = client.get(f"/api/export/profiles/{profile_id}.yaml")
    assert restored_export.status_code == 200, restored_export.text
    assert "DisablePrivateBrowsing" in restored_export.text

    hard_delete_response = client.delete(f"/api/profiles/{profile_id}/hard")
    assert hard_delete_response.status_code == 204

    deleted_get = client.get(f"/api/profiles/{profile_id}")
    assert deleted_get.status_code == 404

    reset_response = client.delete("/api/profiles/reset")
    assert reset_response.status_code == 200, reset_response.text
    assert "deleted" in reset_response.json()


def test_profiles_lifecycle_markers_stay_consistent_for_review_surfaces():
    client = make_test_client(app)
    payload = _make_payload()

    created_response = client.post("/api/profiles", json=payload)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    profile_id = created["id"]

    assert created["is_deleted"] is False
    assert created["created_at"]
    assert created["updated_at"]

    first_created_at = created["created_at"]
    first_updated_at = created["updated_at"]

    patched_response = client.patch(
        f"/api/profiles/{profile_id}",
        json={"description": "Lifecycle regression update"},
    )
    assert patched_response.status_code == 200, patched_response.text
    patched = patched_response.json()
    assert patched["created_at"] == first_created_at
    assert patched["updated_at"] >= first_updated_at
    assert patched["description"] == "Lifecycle regression update"

    archived_response = client.delete(f"/api/profiles/{profile_id}")
    assert archived_response.status_code == 204

    archived_hidden = client.get(f"/api/profiles/{profile_id}")
    assert archived_hidden.status_code == 404, archived_hidden.text

    archived_with_deleted = client.get(
        f"/api/export/profiles/{profile_id}?fmt=json&include_deleted=true"
    )
    assert archived_with_deleted.status_code == 200, archived_with_deleted.text
    archived = archived_with_deleted.json()
    assert archived["is_deleted"] is True

    restored_response = client.post(f"/api/profiles/{profile_id}/restore")
    assert restored_response.status_code == 200, restored_response.text
    restored = restored_response.json()
    assert restored["is_deleted"] is False
    assert restored["created_at"] == first_created_at
    assert restored["updated_at"] >= first_updated_at
