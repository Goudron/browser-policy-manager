from pathlib import Path

import app.core.locales as locales_module
from app.core.locales import (
    ACTIVE_CATALOG_LOCALES,
    DEFAULT_LOCALE,
    LOCALE_BROWSER_LANGUAGE_MATCHES,
    LOCALE_FALLBACKS,
    LOCALE_MATRIX,
    SOURCE_LOCALE,
    TARGET_UI_LOCALES,
    LocaleDefinition,
    resolve_active_catalog_locale_code,
    resolve_target_locale_code,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALE_LOADING_AUDIT_PATH = (
    REPO_ROOT / "docs" / "global_locale_loading_assumptions_audit_2026-05-21.md"
)
README_PATH = REPO_ROOT / "README.md"
DOCUMENTATION_PORTAL_ROADMAP_PATH = (
    REPO_ROOT / "docs" / "documentation_portal_roadmap_2026-05-21.md"
)


def test_global_locale_matrix_records_target_locale_set():
    assert SOURCE_LOCALE == "en"
    assert DEFAULT_LOCALE == "en"
    assert TARGET_UI_LOCALES == ("en", "ru", "de", "zh-CN", "fr", "es-ES")
    assert ACTIVE_CATALOG_LOCALES == ("en", "ru", "de", "zh-CN", "fr", "es-ES")


def test_global_locale_matrix_records_display_names_and_fallbacks():
    matrix_by_code = {locale.code: locale for locale in LOCALE_MATRIX}

    assert matrix_by_code["en"].native_name == "English"
    assert matrix_by_code["ru"].native_name == "Русский"
    assert matrix_by_code["de"].native_name == "Deutsch"
    assert matrix_by_code["zh-CN"].native_name == "简体中文"
    assert matrix_by_code["fr"].native_name == "Français"
    assert matrix_by_code["es-ES"].native_name == "Español"
    assert LOCALE_FALLBACKS == {
        "en": "en",
        "ru": "en",
        "de": "en",
        "zh-CN": "en",
        "fr": "en",
        "es-ES": "en",
    }


def test_global_locale_matrix_records_browser_language_matching_rules():
    assert LOCALE_BROWSER_LANGUAGE_MATCHES["de"] == ("de", "de-*")
    assert LOCALE_BROWSER_LANGUAGE_MATCHES["fr"] == ("fr", "fr-*")
    assert LOCALE_BROWSER_LANGUAGE_MATCHES["es-ES"] == ("es-ES", "es", "es-*")
    assert LOCALE_BROWSER_LANGUAGE_MATCHES["zh-CN"] == (
        "zh-CN",
        "zh-Hans",
        "zh-Hans-*",
        "zh",
    )


def test_locale_matrix_resolves_regional_browser_languages_to_target_codes():
    assert resolve_target_locale_code("de-AT") == "de"
    assert resolve_target_locale_code("fr-CA") == "fr"
    assert resolve_target_locale_code("es-MX") == "es-ES"
    assert resolve_target_locale_code("zh-Hans") == "zh-CN"
    assert resolve_target_locale_code("zh_CN") == "zh-CN"
    assert resolve_target_locale_code("pt-BR") == "en"


def test_locale_matrix_resolves_browser_languages_to_active_catalogs():
    assert resolve_active_catalog_locale_code("ru-RU") == "ru"
    assert resolve_active_catalog_locale_code("de-AT") == "de"
    assert resolve_active_catalog_locale_code("zh-Hans") == "zh-CN"
    assert resolve_active_catalog_locale_code("fr-CA") == "fr"
    assert resolve_active_catalog_locale_code("es-MX") == "es-ES"
    assert resolve_active_catalog_locale_code(
        "es-MX",
        ("en", "ru", "de", "zh-CN", "fr", "es-ES"),
    ) == "es-ES"


def test_locale_matrix_handles_empty_tags_and_catalog_fallback_edges():
    assert resolve_target_locale_code("") == "en"
    assert resolve_active_catalog_locale_code("fr-CA", ("en", "ru")) == "en"
    assert resolve_active_catalog_locale_code("fr-CA", ("ru",)) == "ru"
    assert resolve_active_catalog_locale_code("fr-CA", ()) == "en"


def test_locale_matrix_defaults_when_fallback_chain_cycles_to_inactive_locale(monkeypatch):
    cyclic_french = LocaleDefinition(
        code="fr",
        bcp47="fr",
        english_name="French",
        native_name="Français",
        fallback="fr",
        browser_language_matches=("fr", "fr-*"),
        has_catalog=True,
    )
    monkeypatch.setattr(
        locales_module,
        "_LOCALE_BY_CODE",
        {**locales_module._LOCALE_BY_CODE, "fr": cyclic_french},
    )

    assert resolve_active_catalog_locale_code("fr-CA", ("en",)) == "en"


def test_locale_loading_assumptions_audit_records_key_decisions():
    audit = LOCALE_LOADING_AUDIT_PATH.read_text(encoding="utf-8")

    required_fragments = (
        "Backlog item: `GLOC-002`",
        "`app/main.py`",
        "`app/web/profiles.py`",
        "`app/templates/profiles/_page_header.html`",
        "`app/static/profiles_runtime.js`",
        "`app/static/profiles_library_bootstrap.js`",
        "`app/static/profiles_platform.js`",
        "`tests/test_ui_runtime_i18n_contract.py`",
        "`tests/test_ru_locale_quality.py`",
        "`README.md`",
        "`GLOC-003`",
        "`GLOC-004`",
        "`GLOC-401`",
    )
    for fragment in required_fragments:
        assert fragment in audit


def test_client_locale_resolver_uses_matrix_backed_rules_and_enabled_modes():
    platform_source = (
        REPO_ROOT / "app" / "static" / "profiles_platform.js"
    ).read_text(encoding="utf-8")
    runtime_source = (REPO_ROOT / "app" / "static" / "profiles_runtime.js").read_text(
        encoding="utf-8"
    )
    library_source = (
        REPO_ROOT / "app" / "static" / "profiles_library_bootstrap.js"
    ).read_text(encoding="utf-8")

    for fragment in (
        '{ code: "de", fallback: "en", matches: ["de", "de-*"] }',
        '{ code: "zh-CN", fallback: "en", matches: ["zh-CN", "zh-Hans", "zh-Hans-*", "zh"] }',
        '{ code: "fr", fallback: "en", matches: ["fr", "fr-*"] }',
        '{ code: "es-ES", fallback: "en", matches: ["es-ES", "es", "es-*"] }',
        "function resolveTargetLanguage(languageTag)",
        "let fallbackLanguage = null;",
        "resolveTargetLanguage,",
    ):
        assert fragment in platform_source

    assert "resolveBrowserLanguage(windowRef.navigator, enabledLanguageModes)" in runtime_source
    assert "resolveBrowserLanguage(windowRef.navigator, enabledLanguageModes)" in library_source


def test_readme_documents_target_and_active_locale_sets():
    readme = README_PATH.read_text(encoding="utf-8")
    readme_single_line = " ".join(readme.split())

    assert "**Version:** `0.8.0`" in readme
    assert "English source UI with six active runtime locale catalogs." in readme
    assert "The primary project and UI source language is English." in readme
    assert "`app/i18n/en.json`" in readme
    assert "BPM 0.8.0 ships a six-locale UI matrix:" in readme
    assert "| `de` | Deutsch | Active localized catalog |" in readme
    assert "| `zh-CN` | 简体中文 | Active localized catalog |" in readme
    assert "| `fr` | Français | Active localized catalog |" in readme
    assert "| `es-ES` | Español | Active localized catalog |" in readme
    assert "Currently active runtime catalogs:" in readme
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"- `{locale}`" in readme
    assert "keeps key and placeholder parity with English" in readme
    assert "receives terminology review" in readme
    assert "currently `en`, `ru`, `de`, `zh-CN`, `fr`, or `es-ES`" in readme_single_line
    assert "Current locale ownership is single-maintainer and manual-review based." in readme
    assert "External/community translation intake is not a separate maintained workflow yet" in readme
    assert "Only emails with `[BPM]` in the subject line are reviewed." in readme
    assert "© 2025-2026 • Released under [Mozilla Public License 2.0](LICENSE)" in readme


def test_documentation_portal_roadmap_uses_six_locale_matrix():
    roadmap = DOCUMENTATION_PORTAL_ROADMAP_PATH.read_text(encoding="utf-8")

    expected_locales = '"locales": ["en", "ru", "de", "zh-CN", "fr", "es-ES"]'
    assert expected_locales in roadmap
    assert roadmap.count(expected_locales) == 2
    assert "locale-specific publishing for the BPM UI locale matrix" in roadmap
