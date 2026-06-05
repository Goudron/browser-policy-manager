from pathlib import Path

from tests.docs_index import doc_path_from_index

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = doc_path_from_index(
    "localized_import_edit_export_workflow_audit_2026-05-31.md", status="audit"
)
BROWSER_TEST_PATH = REPO_ROOT / "tests" / "test_ui_browser_tabs.py"


def test_localized_import_edit_export_workflow_audit_records_gloc_605_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-605`" in audit_doc
    assert "import a Firefox" in audit_doc
    assert "Guided editor surface" in audit_doc
    assert "export Firefox" in audit_doc
    for locale in ("ru", "zh-CN"):
        assert f"`{locale}`" in audit_doc
    for exported_policy in (
        "DisableTelemetry: true",
        "Preferences.browser.gloc605.<locale>: true",
    ):
        assert exported_policy in audit_doc


def test_localized_import_export_browser_test_covers_smoke_locale_workflow():
    browser_test_source = BROWSER_TEST_PATH.read_text(encoding="utf-8")

    assert "def test_browser_smoke_imports_firefox_policies_json_in_russian_library" in browser_test_source
    assert 'SMOKE_LOCALES = ("ru", "zh-CN")' in browser_test_source
    for workflow_probe in (
        "_import_profile_through_picker",
        "import-firefox-policies-file",
        "/api/export/profiles/{profile_id}/firefox/policies.json",
    ):
        assert workflow_probe in browser_test_source
    for catalog_key in (
        "profiles.nav_library",
        "profiles.import_firefox_policies_json",
    ):
        assert catalog_key in browser_test_source
