from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = doc_path_from_index(
    "locale_switching_regression_audit_2026-05-31.md", status="audit"
)
BROWSER_TEST_PATH = REPO_ROOT / "tests" / "test_ui_browser_tabs.py"
TEMPLATE_PATHS = (
    REPO_ROOT / "app" / "templates" / "profiles" / "_page_library_workspace.html",
    REPO_ROOT / "app" / "templates" / "profiles" / "_page_workspace.html",
    REPO_ROOT / "app" / "templates" / "profiles" / "_page_settings_workspace.html",
    REPO_ROOT / "app" / "templates" / "profiles" / "_page_json_workspace.html",
)


def test_locale_switching_regression_audit_records_gloc_604_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-604`" in audit_doc
    assert "runtime locale switching" in audit_doc
    assert "without stale text from the previous locale" in audit_doc
    assert 'data-i18n="profiles.library_ready"' in audit_doc
    assert 'data-i18n="profiles.workspace_ready"' in audit_doc
    for locale in ("ru", "zh-CN"):
        assert f"`{locale}`" in audit_doc
    for route_name in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert route_name in audit_doc


def test_locale_switching_browser_test_uses_smoke_locale_pair():
    browser_test_source = BROWSER_TEST_PATH.read_text(encoding="utf-8")

    assert "def test_browser_smoke_primary_routes_render_in_ru_and_zh_cn" in browser_test_source
    assert 'SMOKE_LOCALES = ("ru", "zh-CN")' in browser_test_source
    for selector in ("#list", "#wizard-panel", "#settings-panel", "#editor-panel"):
        assert selector in browser_test_source
    for probe in (
        "document.documentElement.lang",
        "_set_locale",
        "_body_text",
    ):
        assert probe in browser_test_source


def test_locale_switching_status_surfaces_are_runtime_i18n_bound():
    template_sources = "\n".join(path.read_text(encoding="utf-8") for path in TEMPLATE_PATHS)

    assert 'id="status"' in template_sources
    assert 'data-i18n="profiles.library_ready"' in template_sources
    assert template_sources.count('data-i18n="profiles.workspace_ready"') == 3
