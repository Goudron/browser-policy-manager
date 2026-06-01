import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "locale_screenshot_pack_audit_2026-05-30.md"
SCREENSHOT_DIR = REPO_ROOT / "docs" / "screenshots" / "gloc603_2026-05-30"


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
    manifest = json.loads((SCREENSHOT_DIR / "manifest.json").read_text(encoding="utf-8"))

    assert len(manifest) == 48
    assert {entry["locale"] for entry in manifest} == {"en", "ru", "de", "zh-CN", "fr", "es-ES"}
    assert {entry["route"] for entry in manifest} == {"library", "guided", "all-settings", "json"}
    assert {entry["viewport"] for entry in manifest} == {"desktop", "mobile"}

    for entry in manifest:
        image_path = REPO_ROOT / entry["file"]
        assert image_path.exists(), entry
        assert image_path.stat().st_size > 0, entry
        assert entry["scrollWidth"] <= entry["width"], entry
        assert entry["lang"] == entry["locale"], entry


def test_locale_screenshot_pack_contact_sheets_exist_for_every_locale():
    for locale in ("en", "ru", "de", "zh-cn", "fr", "es-es"):
        for suffix in ("html", "png"):
            contact_sheet = SCREENSHOT_DIR / f"contact_{locale}.{suffix}"
            assert contact_sheet.exists()
            assert contact_sheet.stat().st_size > 0
