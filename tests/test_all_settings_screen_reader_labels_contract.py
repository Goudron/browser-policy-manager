import json
from pathlib import Path

from app.core.locales import ACTIVE_CATALOG_LOCALES
from tests.web_profiles_page_helpers import static_source, template_source

REPO_ROOT = Path(__file__).resolve().parents[1]
I18N_DIR = REPO_ROOT / "app" / "i18n"

A11Y_KEYS = (
    "profiles.settings_a11y_count",
    "profiles.settings_a11y_filter_count",
    "profiles.settings_a11y_source_filter",
    "profiles.settings_a11y_entry_source",
    "profiles.settings_a11y_entry_state",
    "profiles.settings_a11y_entry_kind",
    "profiles.settings_a11y_entry_category",
    "profiles.settings_a11y_domain_card",
    "profiles.settings_a11y_review_card",
    "profiles.settings_a11y_review_queue",
    "profiles.settings_a11y_review_more",
    "profiles.settings_a11y_list_previous_page",
    "profiles.settings_a11y_list_next_page",
    "profiles.settings_a11y_list_show_more",
    "profiles.settings_a11y_list_show_less",
)


def _catalog(locale: str) -> dict[str, str]:
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))


def test_all_settings_screen_reader_label_keys_exist_in_active_catalogs():
    for locale in ACTIVE_CATALOG_LOCALES:
        catalog = _catalog(locale)
        missing = [key for key in A11Y_KEYS if key not in catalog]

        assert missing == []


def test_all_settings_screen_reader_labels_are_wired_to_modes_counts_and_badges():
    settings_template = template_source("_page_settings_workspace.html")
    list_source = static_source("profiles_all_settings_list.js")

    for snippet in (
        'aria-label="{{ tr(mode_key) }}. {{ tr(mode_body_key) }}"',
        'aria-label="{{ tr(\'profiles.settings_modes_label\', \'All settings modes\') }}"',
        'aria-live="polite"',
        'aria-label="{{ tr(\'profiles.settings_configured_domains_label\', \'Configured setting domains\') }}"',
        'aria-label="{{ tr(\'profiles.settings_source_filters_label\', \'Source filters\') }}"',
    ):
        assert snippet in settings_template

    for snippet in (
        'formatText("profiles.settings_a11y_entry_source", { source: label })',
        'formatText("profiles.settings_a11y_entry_state", { state })',
        'formatText("profiles.settings_a11y_entry_kind", { kind })',
        'formatText("profiles.settings_a11y_entry_category", { category })',
        'formatText("profiles.settings_a11y_domain_card",',
        'formatText("profiles.settings_a11y_source_filter", { source: label, count })',
        'formatText("profiles.settings_a11y_filter_count", { filter: label, count })',
        'formatText("profiles.settings_a11y_count", { count })',
        'formatReviewText("profiles.settings_a11y_review_card",',
        'formatText("profiles.settings_a11y_review_queue",',
        'formatReviewText("profiles.settings_a11y_review_more", { count: hiddenCount })',
        't("profiles.settings_a11y_list_previous_page")',
        't("profiles.settings_a11y_list_next_page")',
        'formatText("profiles.settings_a11y_list_show_more", { count: total - shown })',
        't("profiles.settings_a11y_list_show_less")',
    ):
        assert snippet in list_source

    for snippet in (
        'aria-label="${escapeHtml(cardLabel)}"',
        'aria-label="${escapeHtml(formatText("profiles.settings_a11y_entry_source", { source: label }))}"',
        'aria-label="${escapeHtml(formatReviewText("profiles.settings_a11y_review_more", { count: hiddenCount }))}"',
        'aria-label="${escapeHtml(t("profiles.settings_a11y_list_previous_page"))}"',
        'aria-label="${escapeHtml(t("profiles.settings_a11y_list_next_page"))}"',
    ):
        assert snippet in list_source
