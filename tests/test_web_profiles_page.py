import asyncio
import importlib
from datetime import UTC, datetime

from fastapi.responses import HTMLResponse
from starlette.requests import Request

from app.core.config import get_settings
from app.main import app
from tests.support import assert_contains_all, make_test_client

PROFILES_PAGE_EDITOR_TOKENS = (
    "Profiles Editor",
    "Profile library",
    "Policy document",
    'id="list-summary"',
    'id="list-total-summary"',
    'id="wizard-panel"',
    'id="wizard-starter-catalog"',
    'id="wizard-settings-search-input"',
    'id="wizard-settings-search-results"',
    'id="wizard-settings-catalog"',
    'id="wizard-manual-policy-controls"',
    'id="wizard-schema-shell-catalog"',
    'id="wizard-schema"',
    'id="wizard-mode"',
    'id="wizard-finish"',
    'id="hard-delete"',
    'id="reset-library"',
    'id="wizard-settings-map-general"',
    'id="wizard-settings-docs-general"',
    'id="wizard-settings-map-privacy"',
    'id="wizard-settings-docs-privacy"',
    'id="wizard-settings-map-sync"',
    'id="wizard-settings-docs-sync"',
    'data-starter-key="basic_corporate"',
    'data-starter-key="classroom_kiosk"',
    'data-starter-key="soc_hard"',
    'id="wizard-summary-starter"',
    'id="wizard-homepage-url"',
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
    'id="wizard-preferences-privacy-groups"',
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
    'wizard-preferences-known-list',
    'data-preference-value-select',
    'data-settings-target="policy:DisableTelemetry"',
    'data-settings-target="field:wizard-proxy-mode"',
    'data-settings-target="pref-section:general"',
    'data-settings-target="pref-section:privacy"',
    'data-settings-target="search-engine-preset:duckduckgo"',
    'data-preference-section="general"',
    'data-preference-section="privacy"',
    'data-search-engine-preset="docs_portal"',
    'data-search-engine-preset="ticket_queue"',
    'data-search-engine-preset="wiki_portal"',
    'data-search-engine-preset="duckduckgo"',
    'data-search-engine-preset-status',
    'data-search-engine-field="Name"',
    'data-search-engine-field="URLTemplate"',
    'data-search-engine-summary',
    'data-search-engine-warning',
    'data-policy-select-key="HttpsOnlyMode"',
    'id="wizard-new-tab-page"',
    'id="wizard-override-first-run"',
    'data-firefox-home-key="Search"',
    'data-firefox-suggest-key="WebSuggestions"',
    'id="wizard-proxy-mode"',
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
    'id="wizard-website-access-summary-blocked"',
    'id="wizard-website-access-summary-exceptions"',
    'id="wizard-website-access-summary-handlers"',
    'id="wizard-website-access-summary-blocked-jump"',
    'id="wizard-website-access-summary-exceptions-jump"',
    'id="wizard-website-access-summary-handlers-jump"',
    'id="wizard-install-addons-permission-card"',
    'id="wizard-extension-settings-card"',
)

PROFILES_PAGE_SCHEMA_EXPORT_TOKENS = (
    'id="wizard-schema-shell-step-2"',
    'id="wizard-schema-shell-step-2-recommended"',
    'id="wizard-schema-shell-step-5-raw"',
    'id="wizard-schema-shell-step-7-badges"',
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
    'id="wizard-export-ready-copy"',
    'id="wizard-export-checklist"',
    'id="wizard-export-save-action"',
    'id="wizard-export-validate-action"',
    'data-extension-profile="uBlock0@raymondhill.net"',
    'data-extension-profile="adguardadblocker@adguard.com"',
    'data-extension-profile="https-everywhere@eff.org"',
    'data-extension-profile-status="uBlock0@raymondhill.net"',
    'data-extension-profile-status="adguardadblocker@adguard.com"',
    'data-extension-profile-status="https-everywhere@eff.org"',
)

PROFILES_PAGE_FOOTER_TOKENS = (
    'id="lang"',
    'rel="icon" href="/favicon.ico"',
    'id="theme"',
    'value="system"',
    'value="light"',
    'value="dark"',
    "resolveBrowserLanguage",
    "prefers-color-scheme: dark",
    "Valery Ledovskoy",
    "/api/profiles",
)


def _profiles_page_response():
    client = make_test_client(app)
    return client.get("/profiles")


def _assert_en_locale_catalog(locale_json: dict[str, str]) -> None:
    assert locale_json["profiles.title"] == "Profiles Editor"
    assert locale_json["profiles.workspace_overview"] == "Workspace overview"
    assert locale_json["profiles.footer_owner"] == "Valery Ledovskoy"
    assert locale_json["profiles.theme_system"] == "System"
    assert locale_json["profiles.locale_system"] == "Browser"
    assert locale_json["profiles.wizard_context_existing"].startswith("You are editing")
    assert locale_json["profiles.wizard_step_one"] == "Profile setup"
    assert locale_json["profiles.wizard_step_two"] == "General"
    assert locale_json["profiles.wizard_step_four"] == "Search"
    assert locale_json["profiles.wizard_step_five"] == "Privacy & security"
    assert locale_json["profiles.wizard_step_six"] == "Sync and add-ons"
    assert locale_json["profiles.wizard_step_seven"] == "Export"
    assert locale_json["profiles.wizard_starter_basic_label"] == "Basic corporate"
    assert locale_json["profiles.hard_delete"] == "Hard delete"
    assert locale_json["profiles.reset_library"] == "Reset profile library"
    assert locale_json["profiles.library_filtered_short"] == "Filtered"
    assert locale_json["profiles.library_total_short"] == "Library"
    assert locale_json["profiles.confirm_hard_delete"].startswith("Dangerous operation")
    assert locale_json["profiles.confirm_reset_library"].startswith("Dangerous operation")
    assert locale_json["profiles.wizard_search_title"] == "Search defaults"
    assert locale_json["profiles.wizard_general_policy_title"] == "General browser behavior"
    assert locale_json["profiles.wizard_settings_map_label"] == "Firefox Settings areas"
    assert locale_json["profiles.wizard_settings_controls_label"] == "Controls in this area"
    assert locale_json["profiles.wizard_settings_filter_all"] == "All"
    assert locale_json["profiles.wizard_settings_search_label"] == "Find a setting"
    assert locale_json["profiles.wizard_settings_search_clear"] == "Clear"
    assert locale_json["profiles.wizard_settings_search_kind_preference_preset"] == "Preference preset"
    assert locale_json["profiles.wizard_settings_search_kind_preference_bundle"] == "Preference bundle"
    assert locale_json["profiles.wizard_settings_search_kind_known_preference"] == "Known preference"
    assert locale_json["profiles.wizard_settings_search_kind_policy_blueprint"] == "Schema policy"
    assert locale_json["profiles.wizard_section_network_access"] == "Network and enterprise access"
    assert locale_json["profiles.wizard_shell_title"] == "Schema-driven coverage for this step"
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
    assert locale_json["profiles.wizard_privacy_review_title"] == "Privacy controls review"
    assert locale_json["profiles.wizard_privacy_review_permissions_locked"] == (
        "Permission categories locked or blocking new requests"
    )
    assert locale_json["profiles.wizard_privacy_review_cookies"] == "Cookie rules configured"
    assert locale_json["profiles.wizard_network_review_title"] == "Network and enterprise review"
    assert locale_json["profiles.wizard_network_review_windows_sso"] == (
        "Explicit Windows SSO setting"
    )
    assert locale_json["profiles.wizard_home_review_title"] == "Home surfaces review"
    assert locale_json["profiles.wizard_home_review_user_messaging"] == (
        "User messaging controls active"
    )
    assert locale_json["profiles.wizard_search_review_title"] == "Search experience review"
    assert locale_json["profiles.wizard_search_review_custom"] == "Managed custom engines"
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
    assert locale_json["profiles.wizard_preferences_bundle_home_focus_title"] == (
        "Focused Firefox Home"
    )
    assert locale_json["profiles.wizard_preferences_bundle_permissions_title"] == (
        "Lock down site permissions"
    )
    assert locale_json["profiles.wizard_search_add_title"] == "Managed custom search engines"
    assert locale_json["profiles.wizard_search_add_button"] == "Add engine"
    assert locale_json["profiles.wizard_search_presets_title"] == "Quick presets"
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
    assert locale_json["profiles.wizard_firefox_home_title"] == "Firefox Home cards"
    assert locale_json["profiles.wizard_firefox_suggest_title"] == "Firefox Suggest"
    assert locale_json["profiles.wizard_proxy_mode_manual"] == "Manual proxy"
    assert locale_json["profiles.wizard_extension_profile_mode_force"] == "Force install"
    assert locale_json["profiles.wizard_extension_profile_ublock_title"] == "uBlock Origin"
    assert locale_json["profiles.wizard_extension_profile_state_missing"] == "No explicit rule"
    assert locale_json["profiles.wizard_extension_profile_state_catalog_url"] == (
        "Uses catalog install URL"
    )
    assert locale_json["profiles.wizard_extension_profile_state_configured"] == "Configured"
    assert locale_json["profiles.wizard_extension_profile_state_custom_url"] == "Custom install URL"
    assert locale_json["profiles.wizard_extensions_review_title"] == "Extension review summary"
    assert locale_json["profiles.wizard_extensions_review_body"].startswith("Quick totals")
    assert locale_json["profiles.wizard_extensions_review_curated"] == "Curated profile rules"
    assert locale_json["profiles.wizard_extensions_review_arbitrary"] == (
        "Arbitrary ExtensionSettings rules"
    )
    assert locale_json["profiles.wizard_extensions_review_custom_urls"] == "Custom install URLs"
    assert locale_json["profiles.wizard_extensions_review_open"] == "Open"
    assert locale_json["profiles.wizard_export_compatibility_title"] == "Compatibility"
    assert locale_json["profiles.wizard_export_profile_saved"] == "Saved profile #{id}"
    assert locale_json["profiles.wizard_export_state_unsaved_existing"] == (
        "Unsaved changes are not in the export yet. Save first."
    )
    assert locale_json["profiles.wizard_export_unknown_count"] == "Unknown top-level keys"
    assert locale_json["profiles.wizard_export_check_ready"] == "Ready for clean export"
    assert locale_json["profiles.wizard_export_check_unsaved"] == "Unsaved edits"
    assert locale_json["profiles.wizard_bookmarks_review_title"] == "Bookmarks review summary"
    assert locale_json["profiles.wizard_bookmarks_review_nested"] == "Rows with nested children"
    assert locale_json["profiles.wizard_bookmarks_review_open"] == "Open"
    assert locale_json["profiles.wizard_bookmarks_row_state_toolbar"] == "Toolbar bookmark"
    assert locale_json["profiles.wizard_managed_bookmarks_row_state_invalid"] == (
        "Children JSON needs attention"
    )
    assert locale_json["profiles.wizard_website_access_review_title"] == "Website access review"
    assert locale_json["profiles.wizard_website_access_review_handlers"] == "Handler mappings"
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
        "Uses catalog install URL"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_custom_url"] == (
        "Custom install URL"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_install_url"] == (
        "Install URL rule"
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


def _assert_ru_locale_catalog(locale_json: dict[str, str]) -> None:
    assert locale_json["profiles.footer_owner"] == "Валерий Ледовской"
    assert locale_json["profiles.theme_dark"] == "Тёмная"
    assert locale_json["profiles.locale_system"] == "По браузеру"
    assert locale_json["profiles.wizard_step_one"] == "Настройка профиля"
    assert locale_json["profiles.wizard_step_two"] == "Общие"
    assert locale_json["profiles.wizard_step_four"] == "Поиск"
    assert locale_json["profiles.wizard_step_five"] == "Приватность и безопасность"
    assert locale_json["profiles.wizard_step_six"] == "Sync и дополнения"
    assert locale_json["profiles.wizard_step_seven"] == "Выгрузка"
    assert locale_json["profiles.wizard_starter_basic_label"] == "Базовый корпоративный"
    assert locale_json["profiles.hard_delete"] == "Жёсткое удаление"
    assert locale_json["profiles.reset_library"] == "Сброс библиотеки профилей"
    assert locale_json["profiles.library_filtered_short"] == "Отфильтровано"
    assert locale_json["profiles.library_total_short"] == "Всего"
    assert locale_json["profiles.confirm_hard_delete"].startswith("Опасная операция")
    assert locale_json["profiles.confirm_reset_library"].startswith("Опасная операция")
    assert locale_json["profiles.wizard_search_title"] == "Поисковые настройки"
    assert locale_json["profiles.wizard_general_policy_title"] == "Общее поведение браузера"
    assert locale_json["profiles.wizard_settings_map_label"] == "Разделы Firefox Settings"
    assert locale_json["profiles.wizard_settings_controls_label"] == (
        "Элементы управления в этом разделе"
    )
    assert locale_json["profiles.wizard_settings_filter_all"] == "Все"
    assert locale_json["profiles.wizard_settings_search_label"] == "Найти настройку"
    assert locale_json["profiles.wizard_settings_search_clear"] == "Очистить"
    assert locale_json["profiles.wizard_settings_search_kind_preference_preset"] == (
        "Пресет preference"
    )
    assert locale_json["profiles.wizard_settings_search_kind_preference_bundle"] == (
        "Набор preferences"
    )
    assert locale_json["profiles.wizard_settings_search_kind_known_preference"] == (
        "Известный preference"
    )
    assert locale_json["profiles.wizard_settings_search_kind_policy_blueprint"] == (
        "Политика схемы"
    )
    assert locale_json["profiles.wizard_section_network_access"] == "Сеть и корпоративный доступ"
    assert locale_json["profiles.wizard_shell_title"] == "Покрытие шага по реальной схеме"
    assert locale_json["profiles.wizard_shell_badge_raw"] == "Через raw fallback"
    assert locale_json["profiles.wizard_shell_boolean_true"] == "Включено"
    assert locale_json["profiles.wizard_shell_branch_mode_simple"] == "Простое вкл/выкл"
    assert locale_json["profiles.wizard_shell_true_map_hint"] == (
        "По одному hostname или origin на строку."
    )
    assert locale_json["profiles.wizard_shell_array_add"] == "Добавить элемент"
    assert locale_json["profiles.wizard_shell_json_error"] == (
        "Вложенные значения должны быть валидным JSON."
    )
    assert locale_json["profiles.wizard_shell_nested_unsupported"] == (
        "Часть вложенных полей пока остаётся через raw JSON."
    )
    assert locale_json["profiles.wizard_shell_dictionary_add"] == "Добавить запись"
    assert locale_json["profiles.wizard_shell_dictionary_key_label"] == "Ключ записи"
    assert locale_json["profiles.wizard_schema_policy_applied"] == "Schema-driven политика обновлена."
    assert locale_json["profiles.wizard_settings_general_updates"] == "Обновления"
    assert locale_json["profiles.wizard_settings_privacy_passwords"] == "Пароли"
    assert locale_json["profiles.wizard_settings_sync_account"] == "Firefox Account"
    assert locale_json["profiles.wizard_preferences_general_title"] == (
        "Управляемые Preferences для General"
    )
    assert locale_json["profiles.wizard_preferences_bundles_title"] == "Быстрые наборы"
    assert locale_json["profiles.wizard_preferences_bundles_body"].startswith("Применяйте небольшую")
    assert locale_json["profiles.wizard_preferences_known_title"] == (
        "Известные Firefox preferences"
    )
    assert locale_json["profiles.wizard_preferences_known_body"].startswith(
        "Добавляйте известный ключ"
    )
    assert locale_json["profiles.wizard_preferences_gui_label"] == "Разделы Firefox Settings"
    assert locale_json["profiles.wizard_preferences_add_button"] == "Добавить preference"
    assert locale_json["profiles.wizard_preferences_value_custom"] == "Своё значение: {value}"
    assert locale_json["profiles.wizard_preferences_hint_known"] == (
        "Известный preference с рекомендуемым управляемым значением по умолчанию."
    )
    assert locale_json["profiles.wizard_preferences_preset_applied"] == "Пресет preference добавлен."
    assert locale_json["profiles.wizard_preferences_bundle_applied"] == "Набор preferences добавлен."
    assert locale_json["profiles.wizard_preferences_known_applied"] == "Известный preference добавлен."
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
        "Включить HTTPS-Only Mode"
    )
    assert locale_json["profiles.wizard_preferences_preset_sync_passwords_off_title"] == (
        "Не синхронизировать пароли"
    )
    assert locale_json["profiles.wizard_privacy_review_title"] == "Сводка по privacy-контролям"
    assert locale_json["profiles.wizard_privacy_review_permissions_locked"] == (
        "Категории разрешений с блокировкой или запретом новых запросов"
    )
    assert locale_json["profiles.wizard_privacy_review_cookies"] == "Настроенные cookie-правила"
    assert locale_json["profiles.wizard_network_review_title"] == (
        "Сводка по сети и enterprise-доступу"
    )
    assert locale_json["profiles.wizard_network_review_windows_sso"] == (
        "Явная настройка Windows SSO"
    )
    assert locale_json["profiles.wizard_home_review_title"] == "Сводка по home-поверхностям"
    assert locale_json["profiles.wizard_home_review_user_messaging"] == (
        "Активные настройки user messaging"
    )
    assert locale_json["profiles.wizard_search_review_title"] == "Сводка по поисковому опыту"
    assert locale_json["profiles.wizard_search_review_custom"] == "Управляемые custom engines"
    assert locale_json["profiles.wizard_homepage_section_state_invalid"] == (
        "Для выбранного режима запуска нужен homepage URL."
    )
    assert locale_json["profiles.wizard_firefox_home_section_state_configured"] == (
        "Показать: {show} • Скрыть: {hide}"
    )
    assert locale_json["profiles.wizard_search_defaults_section_state_conflict"] == (
        "Поисковые подсказки выключены, но поверхности Firefox Suggest остаются включены"
    )
    assert locale_json["profiles.wizard_firefox_suggest_section_state_conflict"] == (
        "Зависимым поверхностям нужны web suggestions"
    )
    assert locale_json["profiles.wizard_preferences_bundle_home_focus_title"] == (
        "Сфокусированный Firefox Home"
    )
    assert locale_json["profiles.wizard_preferences_bundle_permissions_title"] == (
        "Зажать site permissions"
    )
    assert locale_json["profiles.wizard_search_add_title"] == (
        "Управляемые пользовательские поисковики"
    )
    assert locale_json["profiles.wizard_search_add_button"] == "Добавить поисковик"
    assert locale_json["profiles.wizard_search_presets_title"] == "Быстрые пресеты"
    assert locale_json["profiles.wizard_search_preset_docs_title"] == "Портал документации"
    assert locale_json["profiles.wizard_search_preset_applied"] == "Пресет поисковика добавлен."
    assert locale_json["profiles.wizard_search_preset_state_applied"] == (
        "Пресет совпадает с текущим поисковиком"
    )
    assert locale_json["profiles.wizard_search_preset_state_partial"] == "Пресет применён частично"
    assert locale_json["profiles.wizard_search_preset_state_conflict"] == (
        "Пресет расходится с текущим поисковиком"
    )
    assert locale_json["profiles.wizard_search_preset_state_missing"] == "Пресет пока не добавлен"
    assert locale_json["profiles.wizard_search_engine_summary_default"].startswith(
        "По умолчанию используется GET"
    )
    assert locale_json["profiles.wizard_search_engine_warning_required"].startswith(
        "Для валидного поисковика нужны"
    )
    assert locale_json["profiles.wizard_search_engine_method_default"] == "GET (по умолчанию)"
    assert locale_json["profiles.wizard_firefox_home_title"] == "Карточки Firefox Home"
    assert locale_json["profiles.wizard_firefox_suggest_title"] == "Firefox Suggest"
    assert locale_json["profiles.wizard_proxy_mode_manual"] == "Ручная настройка"
    assert locale_json["profiles.wizard_extension_profile_mode_force"] == (
        "Принудительно установить"
    )
    assert locale_json["profiles.wizard_extension_profile_ublock_title"] == "uBlock Origin"
    assert locale_json["profiles.wizard_extension_profile_state_missing"] == "Явного правила нет"
    assert locale_json["profiles.wizard_extension_profile_state_catalog_url"] == (
        "Используется install URL из каталога"
    )
    assert locale_json["profiles.wizard_extension_profile_state_configured"] == "Настроено"
    assert locale_json["profiles.wizard_extension_profile_state_custom_url"] == "Свой install URL"
    assert locale_json["profiles.wizard_extensions_review_title"] == (
        "Сводка по правилам расширений"
    )
    assert locale_json["profiles.wizard_extensions_review_body"].startswith("Быстрые итоги")
    assert locale_json["profiles.wizard_extensions_review_curated"] == "Curated profile rules"
    assert locale_json["profiles.wizard_extensions_review_arbitrary"] == (
        "Arbitrary ExtensionSettings rules"
    )
    assert locale_json["profiles.wizard_extensions_review_custom_urls"] == "Custom install URLs"
    assert locale_json["profiles.wizard_extensions_review_open"] == "Открыть"
    assert locale_json["profiles.wizard_export_compatibility_title"] == "Совместимость"
    assert locale_json["profiles.wizard_export_profile_saved"] == "Сохранённый профиль #{id}"
    assert locale_json["profiles.wizard_export_state_unsaved_existing"] == (
        "Несохранённые изменения ещё не попали в export. Сначала сохраните профиль."
    )
    assert locale_json["profiles.wizard_export_unknown_count"] == (
        "Неизвестные ключи верхнего уровня"
    )
    assert locale_json["profiles.wizard_export_check_ready"] == "Готово к чистому export"
    assert locale_json["profiles.wizard_export_check_unsaved"] == "Есть несохранённые правки"
    assert locale_json["profiles.wizard_bookmarks_review_title"] == "Сводка по закладкам"
    assert locale_json["profiles.wizard_bookmarks_review_nested"] == "Строки с вложенными children"
    assert locale_json["profiles.wizard_bookmarks_review_open"] == "Открыть"
    assert locale_json["profiles.wizard_bookmarks_row_state_toolbar"] == "Закладка на панели"
    assert locale_json["profiles.wizard_managed_bookmarks_row_state_invalid"] == (
        "JSON в children требует внимания"
    )
    assert locale_json["profiles.wizard_website_access_review_title"] == (
        "Сводка по доступу к сайтам"
    )
    assert locale_json["profiles.wizard_website_access_review_handlers"] == "Связки Handlers"
    assert locale_json["profiles.wizard_website_filter_state_configured"] == (
        "Блокировок: {blocked} • Исключений: {exceptions}"
    )
    assert locale_json["profiles.wizard_authentication_state_configured"] == (
        "Контролов: {controls} • Правил хостов: {rules}"
    )
    assert locale_json["profiles.wizard_certificates_state_with_roots"] == (
        "Установлено: {count} • Включены enterprise roots"
    )
    assert locale_json["profiles.wizard_doh_state_provider"] == "Свой провайдер"
    assert locale_json["profiles.wizard_permissions_state_strict"] == (
        "Настроено: {configured} • Строгих: {strict}"
    )
    assert locale_json["profiles.wizard_permissions_nested_default"] == "По умолчанию: {value}"
    assert locale_json["profiles.wizard_cookies_state_strict"] == (
        "Cookie-правил: {count} • Ограничено"
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
        "Используется install URL из каталога"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_custom_url"] == (
        "Свой install URL"
    )
    assert locale_json["profiles.wizard_extension_settings_row_state_install_url"] == (
        "Правило с install URL"
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


def test_profiles_page_renders_editor_shell():
    response = _profiles_page_response()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert_contains_all(response.text, PROFILES_PAGE_EDITOR_TOKENS)


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


def test_static_assets_are_served():
    client = make_test_client(app)
    settings = get_settings()

    favicon_response = client.get("/favicon.ico")
    assert favicon_response.status_code == 200
    assert favicon_response.headers["content-type"].startswith("image/x-icon")
    assert favicon_response.content == (settings.STATIC_DIR / "favicon.ico").read_bytes()


def test_web_profiles_module_wires_templates_and_route():
    import app.web.profiles as web_profiles

    reloaded = importlib.reload(web_profiles)

    assert reloaded.templates.env.loader.searchpath == [str(reloaded.settings.TEMPLATES_DIR)]
    assert any(route.path == "/profiles" for route in reloaded.router.routes)


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
            "query_string": b"",
        }
    )

    response = asyncio.run(reloaded.profiles_page(request))

    assert response.status_code == 200
    assert captured["name"] == "profiles.html"
    assert captured["context"]["title"] == "Profiles — Browser Policy Manager"
    assert captured["context"]["footer_year_range"] == "2025"
    assert "wizard_settings_catalog" in captured["context"]
    assert "wizard_preferences_catalog" in captured["context"]
    assert "wizard_manual_policy_controls" in captured["context"]
    assert "wizard_starter_catalog" in captured["context"]
    assert "wizard_schema_shell_catalog" in captured["context"]
