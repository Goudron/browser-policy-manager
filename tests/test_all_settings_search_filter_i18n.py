import json
import re
from pathlib import Path

from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"
STATIC_DIR = REPO_ROOT / "app" / "static"
ACTIVE_LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def _load_catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def _to_snake_case(value: str) -> str:
    return re.sub(r"[-:\s]+", "_", re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)).lower()


def _collect_schema_shell_locale_keys() -> set[str]:
    catalog = get_wizard_schema_shell_catalog(get_wizard_preferences_catalog())
    keys = {
        "profiles.wizard_shell_preferences_meta",
        "profiles.wizard_shell_meta_basic",
        "profiles.wizard_shell_meta_advanced",
    }

    for channel in catalog["channels"].values():
        for step in channel["steps"].values():
            for bucket_name in ("recommended", "advanced", "raw_fallback"):
                for item in step.get(bucket_name, []):
                    keys.add(f"profiles.shell_policy_{_to_snake_case(item['id'])}")
                    if item.get("subsection"):
                        keys.add(f"profiles.wizard_shell_subsection_{item['subsection']}")
                    if item.get("widget"):
                        keys.add(f"profiles.wizard_shell_widget_{item['widget']}")
                    for tag in item.get("tags") or []:
                        keys.add(f"profiles.wizard_shell_tag_{tag}")

                    stack = [item.get("inline_editor") or {}]
                    while stack:
                        current = stack.pop()
                        if isinstance(current, dict):
                            if current.get("label_key"):
                                keys.add(current["label_key"])
                            stack.extend(current.values())
                        elif isinstance(current, list):
                            stack.extend(current)

            for item in step.get("preferences", []):
                if item.get("title_key"):
                    keys.add(item["title_key"])

    return keys


def test_all_settings_schema_shell_labels_are_catalog_backed_for_active_locales():
    required_keys = _collect_schema_shell_locale_keys()

    for locale in ACTIVE_LOCALES:
        catalog = _load_catalog(locale)
        missing = sorted(key for key in required_keys if key not in catalog)

        assert missing == []


def test_all_settings_review_and_detail_labels_exist_in_active_catalogs():
    en_catalog = _load_catalog("en")
    required_prefixes = (
        "profiles.settings_a11y_",
        "profiles.settings_filter_",
        "profiles.settings_review_",
        "profiles.settings_detail_",
        "profiles.wizard_settings_search_",
    )
    required_keys = {
        key
        for key in en_catalog
        if key.startswith(required_prefixes)
    }

    for locale in ACTIVE_LOCALES:
        catalog = _load_catalog(locale)
        missing = sorted(key for key in required_keys if key not in catalog)

        assert missing == []


def test_all_settings_schema_shell_avoids_english_translation_fallbacks():
    source = (STATIC_DIR / "profiles_schema_shell_sections.js").read_text(encoding="utf-8")

    assert "t(copySpec.key," not in source
    assert "t(`profiles.shell_policy_${toSnakeCase(policyId)}`," not in source
    assert "t(`profiles.wizard_shell_subsection_${normalized}`," not in source
    assert "t(`profiles.wizard_shell_widget_${normalized}`," not in source
    assert "t(`profiles.wizard_shell_tag_${normalized}`," not in source
    assert "t(field.label_key," not in source
    assert "t(\"profiles.wizard_shell_preferences_meta\"," not in source
