import json
import re
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES, SOURCE_LOCALE

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"
I18N_SOURCE_DIR = REPO_ROOT / "app" / "i18n_src"
PLACEHOLDER_RE = re.compile(r"\{[A-Za-z0-9_]+\}")


def _runtime_catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def _settings_source_catalog(locale: str) -> dict[str, str]:
    return json.loads(
        (I18N_SOURCE_DIR / locale / "settings.json").read_text(encoding="utf-8")
    )


def _placeholders(value: str) -> list[str]:
    return sorted(PLACEHOLDER_RE.findall(value))


def test_all_settings_locale_catalogs_keep_key_order_placeholders_and_runtime_parity():
    en_settings = _settings_source_catalog(SOURCE_LOCALE)

    for locale in ACTIVE_CATALOG_LOCALES:
        source_settings = _settings_source_catalog(locale)
        runtime_catalog = _runtime_catalog(locale)

        assert list(source_settings) == list(en_settings)
        assert all(runtime_catalog[key] == value for key, value in source_settings.items())

        placeholder_mismatches = {
            key: (_placeholders(en_settings[key]), _placeholders(value))
            for key, value in source_settings.items()
            if _placeholders(en_settings[key]) != _placeholders(value)
        }
        assert placeholder_mismatches == {}


def test_all_settings_mode_copy_is_localized_in_all_active_catalogs():
    expected_mode_bodies = {
        "en": {
            "profiles.settings_mode_review_body": "Fix items that need attention first.",
            "profiles.settings_mode_configured_body": "See what this profile applies.",
            "profiles.settings_mode_catalog_body": "Find any available setting.",
        },
        "ru": {
            "profiles.settings_mode_review_body": "Сначала исправьте элементы, требующие внимания.",
            "profiles.settings_mode_configured_body": "Посмотрите, что применяет этот профиль.",
            "profiles.settings_mode_catalog_body": "Найдите любую доступную настройку.",
        },
        "de": {
            "profiles.settings_mode_review_body": "Beheben Sie zuerst Einträge, die Aufmerksamkeit brauchen.",
            "profiles.settings_mode_configured_body": "Sehen Sie, was dieses Profil anwendet.",
            "profiles.settings_mode_catalog_body": "Finden Sie jede verfügbare Einstellung.",
        },
        "zh-CN": {
            "profiles.settings_mode_review_body": "先修复需要注意的项目。",
            "profiles.settings_mode_configured_body": "查看此配置档案应用的内容。",
            "profiles.settings_mode_catalog_body": "查找任何可用设置。",
        },
        "fr": {
            "profiles.settings_mode_review_body": "Corrigez d'abord les éléments qui demandent attention.",
            "profiles.settings_mode_configured_body": "Voyez ce que ce profil applique.",
            "profiles.settings_mode_catalog_body": "Trouvez tout paramètre disponible.",
        },
        "es-ES": {
            "profiles.settings_mode_review_body": "Corrige primero los elementos que requieren atención.",
            "profiles.settings_mode_configured_body": "Ve qué aplica este perfil.",
            "profiles.settings_mode_catalog_body": "Encuentra cualquier ajuste disponible.",
        },
    }

    assert tuple(expected_mode_bodies) == ACTIVE_CATALOG_LOCALES

    for locale, expected in expected_mode_bodies.items():
        runtime_catalog = _runtime_catalog(locale)
        source_settings = _settings_source_catalog(locale)

        for key, value in expected.items():
            assert source_settings[key] == value
            assert runtime_catalog[key] == value
