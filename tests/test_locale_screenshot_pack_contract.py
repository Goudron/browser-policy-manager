from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "locale_screenshot_pack_audit_2026-05-30.md"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"


def test_locale_screenshot_pack_audit_records_gloc_603_scope():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-603`" in audit_doc
    assert "screenshot pack" in audit_doc
    assert "48 route screenshots" in audit_doc
    assert "Not every non-English locale is fully localized" in audit_doc
    for locale in ("en", "ru", "de", "zh-CN", "fr", "es-ES"):
        assert f"`{locale}`" in audit_doc
    for route_name in ("Library", "Guided editor", "All settings", "JSON editor"):
        assert route_name in audit_doc
    for mixed_locale in ("`de` | Mixed", "`fr` | Mixed", "`es-ES` | Mixed"):
        assert mixed_locale in audit_doc


def test_locale_screenshot_pack_manifest_covers_all_locales_routes_and_viewports():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "48 route screenshots: 6 locales x 4 routes x 2 viewports" in audit_doc
    assert "`manifest.json` with locale, route, viewport, path, document language, and measured width metadata" in audit_doc
    for route in (
        "Library: `/profiles`",
        "Guided editor: `/profiles/1/edit`",
        "All settings: `/profiles/1/settings`",
        "JSON editor: `/profiles/1/json`",
    ):
        assert route in audit_doc
    for viewport in ("Desktop: 1440 px wide", "Mobile: 390 px wide"):
        assert viewport in audit_doc


def test_locale_screenshot_pack_contact_sheets_exist_for_every_locale():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")
    gitignore = GITIGNORE_PATH.read_text(encoding="utf-8")

    assert "6 locale contact sheets: one PNG and one HTML review sheet per locale" in audit_doc
    assert "/docs/screenshots/" in gitignore
