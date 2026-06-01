from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "localized_import_edit_export_workflow_audit_2026-05-31.md"
BROWSER_TEST_PATH = REPO_ROOT / "tests" / "test_ui_browser_tabs.py"


def test_localized_import_edit_export_workflow_audit_records_gloc_605_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-605`" in audit_doc
    assert "import a Firefox" in audit_doc
    assert "Guided editor surface" in audit_doc
    assert "edit All settings" in audit_doc
    assert "validate" in audit_doc
    assert "export Firefox" in audit_doc
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in audit_doc
    for exported_policy in (
        "DisableTelemetry: true",
        "Preferences.browser.gloc605.<locale>: true",
    ):
        assert exported_policy in audit_doc


def test_localized_import_edit_export_browser_test_covers_full_locale_workflow():
    browser_test_source = BROWSER_TEST_PATH.read_text(encoding="utf-8")

    assert "def test_localized_import_edit_validate_export_workflow_browser_regression" in browser_test_source
    assert 'target_locales = ("en", "ru", "de", "zh-CN", "fr", "es-ES")' in browser_test_source
    for workflow_probe in (
        "import_profile_through_picker",
        "check_guided_editor_surface",
        "edit_all_settings_preference",
        "assert_json_export",
        "visible_text_contains",
        "import-firefox-policies-file",
        "wizard-schema",
        'data-settings-entry-id="NewTabPage"',
        "browser.gloc605",
        "download-firefox-policies",
        "/api/export/profiles/{profile_id}/firefox/policies.json",
    ):
        assert workflow_probe in browser_test_source
    for catalog_key in (
        "profiles.nav_library",
        "profiles.import_firefox_policies_json",
        "profiles.workspace_scope_guided",
        "profiles.editor_chrome_settings_link",
        "profiles.settings_review_title",
        "profiles.editor_chrome_json_link",
        "profiles.editor_title_section",
        "profiles.validation_ok",
    ):
        assert catalog_key in browser_test_source
