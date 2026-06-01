from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = REPO_ROOT / "app" / "static" / "profiles.css"
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "es_es_overflow_audit_2026-05-30.md"


def test_spanish_overflow_audit_document_records_clean_primary_surfaces():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-503`" in audit_doc
    assert "Spanish (`es-ES`)" in audit_doc
    for surface in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert surface in audit_doc
    assert "desktop/mobile: clean" in audit_doc
    assert "/tmp/bpm-gloc503-es-audit" in audit_doc


def test_spanish_pass_keeps_generic_locale_layout_guards():
    css = CSS_PATH.read_text(encoding="utf-8")
    search_shell_rule = css.split(".wizard-settings-search-shell {", 1)[1].split("}", 1)[0]
    step_copy_rule = css.split(".wizard-step-copy {", 1)[1].split("}", 1)[0]

    assert "box-sizing: border-box;" in search_shell_rule
    assert "width: 100%;" in search_shell_rule
    assert "display: block;" in step_copy_rule
    assert "overflow-wrap: anywhere;" in step_copy_rule
    assert "-webkit-line-clamp" not in step_copy_rule
