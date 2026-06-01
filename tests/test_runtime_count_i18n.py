import json
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"
STATIC_DIR = REPO_ROOT / "app" / "static"


COUNT_LABEL_KEYS = {
    "profiles.settings_search_match_one",
    "profiles.settings_search_match_many",
    "profiles.settings_list_value_object",
    "profiles.settings_list_value_array",
    "profiles.wizard_settings_search_match_count",
    "profiles.wizard_preferences_handoff_count",
    "profiles.advanced_context_more",
    "profiles.wizard_hardening_governance_remaining_count",
    "profiles.wizard_hardening_governance_item_sites_ready",
    "profiles.wizard_hardening_governance_item_deeper_ready",
    "profiles.wizard_review_allowed_exceptions_short",
    "profiles.wizard_review_blocked_sites_short",
    "profiles.wizard_extensions_advanced_count",
    "profiles.wizard_extensions_governance_item_rollout_ready",
    "profiles.wizard_extensions_governance_item_deeper_ready",
    "profiles.wizard_export_guided_network_dns",
    "profiles.wizard_export_guided_network_auth",
    "profiles.wizard_export_guided_network_certificates",
    "profiles.wizard_export_guided_home_homepage",
    "profiles.wizard_export_guided_home_overrides",
    "profiles.wizard_export_guided_home_firefox_home",
    "profiles.wizard_export_guided_home_user_messaging",
    "profiles.wizard_export_guided_search_defaults",
    "profiles.wizard_export_guided_search_hidden",
    "profiles.wizard_export_guided_search_custom",
    "profiles.wizard_export_guided_search_suggest",
    "profiles.wizard_export_guided_features_locales",
    "profiles.wizard_export_guided_features_addons",
    "profiles.wizard_export_guided_features_addons_curated",
    "profiles.wizard_export_guided_features_addons_arbitrary",
    "profiles.wizard_export_guided_features_addons_urls",
    "profiles.wizard_export_guided_features_websites",
    "profiles.wizard_export_guided_features_bookmarks",
    "profiles.wizard_export_guided_ai_controls",
    "profiles.wizard_export_guided_ai_feature_controls",
    "profiles.wizard_export_guided_privacy_permissions",
    "profiles.wizard_export_guided_privacy_locked",
    "profiles.wizard_export_guided_privacy_cookies",
    "profiles.wizard_export_guided_privacy_lockdown",
}


EXPECTED_LIBRARY_LABELS = {
    "en": {
        "profiles.library_count_one": "Profile in library",
        "profiles.library_count_few": "Profiles in library",
        "profiles.library_count_many": "Profiles in library",
    },
    "ru": {
        "profiles.library_count_one": "Профиль в библиотеке",
        "profiles.library_count_few": "Профиля в библиотеке",
        "profiles.library_count_many": "Профилей в библиотеке",
    },
    "de": {
        "profiles.library_count_one": "Profil in der Bibliothek",
        "profiles.library_count_few": "Profile in der Bibliothek",
        "profiles.library_count_many": "Profile in der Bibliothek",
    },
    "zh-CN": {
        "profiles.library_count_one": "库中的配置档案",
        "profiles.library_count_few": "库中的配置档案",
        "profiles.library_count_many": "库中的配置档案",
    },
    "fr": {
        "profiles.library_count_one": "Profil dans la bibliothèque",
        "profiles.library_count_few": "Profils dans la bibliothèque",
        "profiles.library_count_many": "Profils dans la bibliothèque",
    },
    "es-ES": {
        "profiles.library_count_one": "Perfil en la biblioteca",
        "profiles.library_count_few": "Perfiles en la biblioteca",
        "profiles.library_count_many": "Perfiles en la biblioteca",
    },
}


def _read_locale(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def test_runtime_count_labels_use_catalog_backed_label_first_shape():
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = _read_locale(locale)
        for key in COUNT_LABEL_KEYS:
            value = catalog[key]
            assert "{count}" in value
            assert not value.startswith("{count}")


def test_guided_editor_search_count_is_not_hardcoded_per_language():
    source = (STATIC_DIR / "profiles_settings_search.js").read_text(encoding="utf-8")

    assert "profiles.wizard_settings_search_match_count" in source
    assert 'getCurrentLang() === "ru"' not in source
    assert "match} in the wizard" not in source
    assert "совпадений" not in source


def test_library_counter_labels_are_defined_for_all_active_locale_forms():
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = _read_locale(locale)
        expected = EXPECTED_LIBRARY_LABELS[locale]
        for key, value in expected.items():
            assert catalog[key] == value
