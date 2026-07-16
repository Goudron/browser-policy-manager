import json
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES
from tests.web_profiles_page_helpers import static_source

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "app/i18n_src"
BUILT_ROOT = REPO_ROOT / "app/i18n"
KEYS = (
    "profiles.all_settings.row_help.open",
    "profiles.all_settings.row_help.missing",
    "profiles.all_settings.row_help.unavailable",
    "profiles.all_settings.row_help.raw_not_applicable",
    "profiles.all_settings.row_help.unknown_not_supported",
)


def _json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_row_help_labels_have_exact_six_locale_source_and_built_parity():
    for locale in ACTIVE_CATALOG_LOCALES:
        source = _json(SOURCE_ROOT / locale / "common.json")
        built = _json(BUILT_ROOT / f"{locale}.json")
        for key in KEYS:
            assert source[key]
            assert source[key].count("{setting}") == 1
            assert built[key] == source[key]


def test_non_english_row_help_labels_do_not_fall_back_to_english():
    english = _json(SOURCE_ROOT / "en/common.json")
    forbidden_english_fragments = (
        "Open documentation",
        "Documentation is",
        "Documentation for",
        "Documentation does",
        "unsupported setting",
    )

    for locale in ACTIVE_CATALOG_LOCALES:
        if locale == "en":
            continue
        localized = _json(SOURCE_ROOT / locale / "common.json")
        for key in KEYS:
            assert localized[key] != english[key], (locale, key)
            assert all(fragment not in localized[key] for fragment in forbidden_english_fragments)


def test_list_and_search_use_the_localized_open_label_template():
    list_source = static_source("profiles_all_settings_list.js")
    search_source = static_source("profiles_settings_search.js")

    assert 'return "profiles.all_settings.row_help.open"' in list_source
    assert "formatText(rowHelpLabelKey(state.disposition), {" in list_source
    assert '"profiles.all_settings.row_help.open"' in search_source
    assert 't("profiles.context_help_action")' not in list_source
    assert 't("profiles.context_help_action")' not in search_source
