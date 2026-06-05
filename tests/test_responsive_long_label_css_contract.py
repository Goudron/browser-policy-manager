from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = REPO_ROOT / "app" / "static" / "profiles.css"
AUDIT_DOC_PATH = doc_path_from_index(
    "responsive_long_label_css_audit_2026-05-30.md", status="audit"
)


def _css_source() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _block(selector: str) -> str:
    source = _css_source()
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def _block_containing(selector: str, text: str) -> str:
    source = _css_source()
    start = 0
    while True:
        start = source.find(selector, start)
        if start == -1:
            raise AssertionError(f"No CSS block for {selector!r} contains {text!r}")
        end = source.index("}", start)
        block = source[start:end]
        if text in block:
            return block
        start = end + 1


def test_responsive_long_label_audit_document_records_generic_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-506`" in audit_doc
    assert "Responsive CSS fixes for long labels" in audit_doc
    for surface in ("buttons", "segmented controls", "cards", "table cells", "review panels"):
        assert surface in audit_doc
    assert "No locale-specific selectors" in audit_doc


def test_base_buttons_allow_wrapping_without_forcing_horizontal_overflow():
    block = _block_containing(".button-base {", "min-height: 48px;")

    for declaration in (
        "box-sizing: border-box;",
        "min-width: 0;",
        "max-width: 100%;",
        "line-height: 1.2;",
        "text-align: center;",
        "white-space: normal;",
        "overflow-wrap: normal;",
        "word-break: normal;",
    ):
        assert declaration in block


def test_review_cards_and_filters_have_long_label_guards():
    review_card = _block(".all-settings-review-card {")
    review_title = _block(".all-settings-review-card-title {")
    review_body = _block(".all-settings-review-card-body {")
    filter_button = _block(".all-settings-filter-button {")
    review_filter = _block(".wizard-review-filter {")

    assert "min-width: 0;" in review_card
    assert "overflow-wrap: anywhere;" in review_card
    assert "min-width: 0;" in review_title
    assert "overflow-wrap: anywhere;" in review_title
    assert "min-width: 0;" in review_body
    assert "overflow-wrap: anywhere;" in review_body
    assert "white-space: normal;" in filter_button
    assert "white-space: normal;" in review_filter


def test_wizard_cards_and_segmented_controls_are_width_bounded():
    starter_card = _block(".wizard-starter-card {")
    starter_badge = _block_containing(".wizard-starter-badge {", "width: fit-content;")
    cis_selector = _block(".wizard-cis-selector {")
    proxy_selector = _block(".wizard-proxy-mode-selector {")
    search_preset = _block(".wizard-search-engine-preset {")

    for block in (starter_card, starter_badge, cis_selector, proxy_selector, search_preset):
        assert "max-width: 100%;" in block

    assert "min-width: 0;" in starter_card
    assert "overflow-wrap: anywhere;" in starter_card
    assert "white-space: normal;" in starter_badge
    assert "min-width: 0;" in cis_selector
    assert "min-width: 0;" in proxy_selector
    assert "overflow-wrap: anywhere;" in search_preset


def test_summary_and_export_review_rows_can_wrap_long_values():
    summary_card = _block(".wizard-summary-card,\n        .wizard-actions-card {")
    summary_key = _block(".wizard-summary-key {")
    summary_value = _block(".wizard-summary-value {")
    export_item = _block(".wizard-export-plan-item {")
    export_copy = _block_containing(".wizard-export-plan-copy {", "font-size: 0.92rem;")

    assert "min-width: 0;" in summary_card
    assert "overflow-wrap: anywhere;" in summary_card
    assert "min-width: 0;" in summary_key
    assert "overflow-wrap: anywhere;" in summary_key
    assert "min-width: 0;" in summary_value
    assert "overflow-wrap: anywhere;" in summary_value
    assert "min-width: 0;" in export_item
    assert "min-width: 0;" in export_copy
    assert "overflow-wrap: anywhere;" in export_copy


def test_table_cell_contracts_remain_mobile_friendly():
    source = _css_source()
    all_settings_cell = _block(".all-settings-list-cell {")
    library_action = _block(".library-row-actions .button-base {")

    assert "overflow-wrap: anywhere;" in all_settings_cell
    assert "box-sizing: border-box;" in library_action
    assert "width: 100%;" in library_action
    assert "@media (max-width: 820px)" in source
    assert ".all-settings-list-row" in source
    assert "grid-template-columns: 1fr;" in source
