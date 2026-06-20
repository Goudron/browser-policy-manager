import json
import re
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = REPO_ROOT / "app" / "static"
TEMPLATES_DIR = REPO_ROOT / "app" / "templates"
I18N_DIR = REPO_ROOT / "app" / "i18n"
I18N_SOURCE_DIR = REPO_ROOT / "app" / "i18n_src"


def _read_locale(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def _read_source_namespace(locale: str, namespace: str) -> dict[str, str]:
    return json.loads((I18N_SOURCE_DIR / locale / f"{namespace}.json").read_text(encoding="utf-8"))


def _runtime_source_files() -> list[Path]:
    return [
        *sorted(STATIC_DIR.glob("*.js")),
        *sorted(TEMPLATES_DIR.rglob("*.html")),
    ]


def _runtime_i18n_keys() -> set[str]:
    keys: set[str] = set()
    for path in _runtime_source_files():
        source = path.read_text(encoding="utf-8")
        keys.update(
            re.findall(
                r"""(?:t|tr|translate)\(\s*["'](profiles\.[A-Za-z0-9_.-]+)["']""",
                source,
            )
        )
        keys.update(
            re.findall(
                r"""data-i18n(?:-[a-z-]+)?=["'](profiles\.[A-Za-z0-9_.-]+)["']""",
                source,
            )
        )
        keys.update(
            re.findall(r"""key:\s*["'](profiles\.[A-Za-z0-9_.-]+)["']""", source)
        )
        keys.update(
            re.findall(
                r"""dataset\.i18n[A-Za-z]*\s*=\s*["'](profiles\.[A-Za-z0-9_.-]+)["']""",
                source,
            )
        )
        keys.update(
            re.findall(
                r"""setAttribute\(\s*["']data-i18n(?:-[a-z-]+)?["']\s*,\s*["'](profiles\.[A-Za-z0-9_.-]+)["']""",
                source,
            )
        )
        keys.update(
            re.findall(
                r"""\[\s*["'](profiles\.[A-Za-z0-9_.-]+)["']\s*,""",
                source,
            )
        )
    return keys


def test_runtime_i18n_keys_exist_in_active_catalog_locales():
    runtime_keys = _runtime_i18n_keys()

    assert runtime_keys
    assert ACTIVE_CATALOG_LOCALES == ("en", "ru", "de", "zh-CN", "fr", "es-ES")

    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = _read_locale(locale)
        missing = sorted(runtime_keys - set(catalog))
        assert missing == []


def test_library_count_labels_are_locale_catalog_backed():
    platform_source = (STATIC_DIR / "profiles_platform.js").read_text(encoding="utf-8")
    workspace_source = (STATIC_DIR / "profiles_workspace.js").read_text(encoding="utf-8")
    library_source = (STATIC_DIR / "profiles_library_bootstrap.js").read_text(
        encoding="utf-8"
    )
    catalogs = {
        locale: _read_locale(locale)
        for locale in ACTIVE_CATALOG_LOCALES
    }

    for key in (
        "profiles.library_count_one",
        "profiles.library_count_many",
    ):
        for catalog in catalogs.values():
            assert key in catalog
        assert key in platform_source

    assert "profiles.library_count_few" in catalogs["ru"]
    assert "profiles.library_count_few" in platform_source
    assert "libraryCountLabel(total, getCurrentLang(), t)" in workspace_source
    assert "libraryCountLabel(total, getCurrentLang(), t)" in library_source


def test_compare_locale_keys_are_source_and_runtime_catalog_backed():
    expected_compare_keys = {
        key for key in _read_source_namespace("en", "library") if key.startswith("profiles.compare_")
    }

    assert expected_compare_keys == {
        "profiles.compare_action",
        "profiles.compare_kind_policy",
        "profiles.compare_kind_preference",
        "profiles.compare_left_column",
        "profiles.compare_left_label",
        "profiles.compare_profile_empty",
        "profiles.compare_right_column",
        "profiles.compare_right_label",
        "profiles.compare_route_eyebrow",
        "profiles.compare_route_title",
        "profiles.compare_search_empty",
        "profiles.compare_search_loading",
        "profiles.compare_search_placeholder",
        "profiles.compare_selected",
        "profiles.compare_selection_title",
        "profiles.compare_setting_column",
        "profiles.compare_settings_title",
        "profiles.compare_state_different",
        "profiles.compare_state_equal",
        "profiles.compare_state_missing",
        "profiles.compare_table_empty",
        "profiles.compare_table_no_settings",
    }

    for locale in ACTIVE_CATALOG_LOCALES:
        source_library = _read_source_namespace(locale, "library")
        runtime_catalog = _read_locale(locale)
        source_compare_keys = {
            key for key in source_library if key.startswith("profiles.compare_")
        }
        runtime_compare_keys = {
            key for key in runtime_catalog if key.startswith("profiles.compare_")
        }

        assert source_compare_keys == expected_compare_keys
        assert runtime_compare_keys == expected_compare_keys
        assert all(source_library[key] for key in expected_compare_keys)
        assert all(runtime_catalog[key] == source_library[key] for key in expected_compare_keys)


def test_runtime_i18n_scan_covers_js_template_and_attribute_key_shapes():
    runtime_keys = _runtime_i18n_keys()

    expected_runtime_keys = {
        "profiles.wizard_review_filter_changed",  # object key field in JS.
        "profiles.library_count_one",  # translate(...) helper fallback in JS.
        "profiles.wizard_cis_exceptions_count_empty",  # dataset.i18n assignment.
        "profiles.wizard_settings_search_match_count",  # dynamic Guided editor count text.
        "profiles.wizard_step_undo",  # data-i18n in templates.
        "profiles.wizard_preferences_name_placeholder",  # data-i18n-placeholder.
        "profiles.wizard_export_shareable_heading",  # t(...) call in generated text.
        "profiles.footer_license_label",  # tr(...) call/data-i18n in template.
    }

    assert expected_runtime_keys <= runtime_keys
