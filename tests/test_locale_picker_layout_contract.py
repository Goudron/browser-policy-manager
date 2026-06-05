from pathlib import Path

from bs4 import BeautifulSoup

from app.main import app
from tests.docs_index import doc_path_from_index
from tests.support import make_test_client

REPO_ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = REPO_ROOT / "app" / "static" / "profiles.css"
HEADER_TEMPLATE_PATH = REPO_ROOT / "app" / "templates" / "profiles" / "_page_header.html"
AUDIT_DOC_PATH = doc_path_from_index("locale_picker_layout_audit_2026-05-30.md", status="audit")


def test_locale_picker_layout_audit_document_records_all_active_locales():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-505`" in audit_doc
    assert "Locale picker layout pass" in audit_doc
    for locale_name in ("English", "Русский", "Deutsch", "简体中文", "Français", "Español"):
        assert locale_name in audit_doc
    assert "desktop/mobile: clean" in audit_doc


def test_locale_picker_renders_native_names_with_stable_metadata():
    client = make_test_client(app)
    response = client.get("/profiles/new")
    soup = BeautifulSoup(response.text, "html.parser")
    lang_select = soup.find(id="lang")
    options = {option.get("value"): option for option in lang_select.find_all("option")}

    assert list(options) == ["system", "en", "ru", "de", "zh-CN", "fr", "es-ES"]
    expected_native_names = {
        "en": "English",
        "ru": "Русский",
        "de": "Deutsch",
        "zh-CN": "简体中文",
        "fr": "Français",
        "es-ES": "Español",
    }
    for locale_code, native_name in expected_native_names.items():
        option = options[locale_code]
        assert option.get_text(strip=True) == native_name
        assert option["data-locale-native-name"] == native_name
        assert option["data-locale-code"] == locale_code
        assert option["data-locale-has-catalog"] == "true"
        assert not option.has_attr("disabled")

    assert options["zh-CN"]["lang"] == "zh-CN"
    assert options["es-ES"]["data-locale-bcp47"] == "es-ES"


def test_locale_picker_control_has_responsive_width_contract():
    header_template = HEADER_TEMPLATE_PATH.read_text(encoding="utf-8")
    css_source = CSS_PATH.read_text(encoding="utf-8")

    assert '<select id="lang" class="soft-input rounded-xl px-3 py-2 text-sm">' in header_template
    assert ".compact-toolbar-actions" in css_source
    assert ".compact-toolbar-control" in css_source
    assert ".compact-toolbar-control select.soft-input" in css_source

    select_rule_start = css_source.index(".compact-toolbar-control select.soft-input")
    select_rule_end = css_source.index("}", select_rule_start)
    select_rule = css_source[select_rule_start:select_rule_end]
    for declaration in (
        "box-sizing: border-box;",
        "width: 100%;",
        "min-width: 0;",
        "max-width: 100%;",
        "overflow: hidden;",
        "text-overflow: ellipsis;",
    ):
        assert declaration in select_rule

    assert "@media (max-width: 1100px)" in css_source
    assert "grid-template-columns: 1fr;" in css_source
