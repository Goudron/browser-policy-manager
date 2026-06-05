from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = doc_path_from_index(
    "chromium_locale_smoke_matrix_audit_2026-05-30.md", status="audit"
)
BROWSER_TEST_PATH = REPO_ROOT / "tests" / "test_ui_browser_tabs.py"


def test_chromium_locale_smoke_matrix_audit_records_gloc_601_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-601`" in audit_doc
    assert "Chromium browser smoke matrix" in audit_doc
    assert "`zh-CN`" in audit_doc
    for route_name in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert route_name in audit_doc


def test_chromium_locale_smoke_matrix_browser_test_covers_ru_zh_smoke_routes():
    browser_test_source = BROWSER_TEST_PATH.read_text(encoding="utf-8")

    assert "def test_browser_smoke_primary_routes_render_in_ru_and_zh_cn" in browser_test_source
    assert 'SMOKE_LOCALES = ("ru", "zh-CN")' in browser_test_source
    for selector in ("#list", "#wizard-panel", "#settings-panel", "#editor-panel"):
        assert selector in browser_test_source
    for key in (
        "profiles.title",
        "profiles.nav_library",
        "profiles.workspace_scope_guided",
        "profiles.editor_chrome_settings_link",
        "profiles.editor_chrome_json_link",
        "profiles.editor_title_section",
    ):
        assert key in browser_test_source
    assert "return document.documentElement.lang;" in browser_test_source
