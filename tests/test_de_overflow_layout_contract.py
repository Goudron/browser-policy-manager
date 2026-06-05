from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = REPO_ROOT / "app" / "static" / "profiles.css"
AUDIT_DOC_PATH = doc_path_from_index("de_overflow_audit_2026-05-30.md", status="audit")


def _css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def test_german_overflow_audit_document_records_checked_surfaces():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-501`" in audit_doc
    for surface in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert surface in audit_doc
    assert "no page-width offenders" in audit_doc


def test_settings_search_shell_uses_border_box_for_mobile_width():
    css = _css()
    shell_rule = css.split(".wizard-settings-search-shell {", 1)[1].split("}", 1)[0]

    assert "box-sizing: border-box;" in shell_rule
    assert "width: 100%;" in shell_rule
    assert "max-width: 360px;" in shell_rule


def test_all_settings_list_columns_keep_reasonable_minimums_for_long_german_labels():
    css = _css()
    list_grid_rule = css.split(".all-settings-list-head,\n        .all-settings-list-row {", 1)[1].split("}", 1)[0]

    assert "minmax(170px, 1.45fr)" in list_grid_rule
    assert "minmax(110px, 0.72fr)" in list_grid_rule
    assert "minmax(150px, 1fr)" in list_grid_rule
    assert "minmax(96px, 0.62fr)" in list_grid_rule
    assert "minmax(140px, 1fr)" in list_grid_rule


def test_wizard_step_copy_wraps_instead_of_clamping_locale_text():
    css = _css()
    step_copy_rule = css.split(".wizard-step-copy {", 1)[1].split("}", 1)[0]

    assert "display: block;" in step_copy_rule
    assert "overflow-wrap: anywhere;" in step_copy_rule
    assert "hyphens: auto;" in step_copy_rule
    assert "-webkit-line-clamp" not in step_copy_rule
