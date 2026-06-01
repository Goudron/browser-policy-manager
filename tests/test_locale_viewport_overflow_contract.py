from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "locale_viewport_overflow_assertions_audit_2026-05-30.md"
BROWSER_TEST_PATH = REPO_ROOT / "tests" / "test_ui_browser_tabs.py"


def test_locale_viewport_overflow_audit_records_gloc_602_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-602`" in audit_doc
    assert "viewport overflow assertions" in audit_doc
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in audit_doc
    for route_name in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert route_name in audit_doc


def test_locale_viewport_overflow_browser_test_covers_all_locales_and_routes():
    browser_test_source = BROWSER_TEST_PATH.read_text(encoding="utf-8")

    assert (
        "def test_locale_viewport_overflow_browser_regression_fits_all_locales_and_primary_routes"
        in browser_test_source
    )
    assert 'target_locales = ("en", "ru", "de", "zh-CN", "fr", "es-ES")' in browser_test_source
    for selector in ("#list", "#wizard-panel", "#settings-panel", "#editor-panel"):
        assert selector in browser_test_source
    for probe in (
        "documentWidth",
        "viewportWidth",
        "window.innerWidth",
        "document.documentElement.lang",
        "_assert_document_width_fits_viewport(driver)",
    ):
        assert probe in browser_test_source
