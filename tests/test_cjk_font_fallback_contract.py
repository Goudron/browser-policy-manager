from pathlib import Path

from bs4 import BeautifulSoup

from app.main import app
from tests.support import make_test_client

REPO_ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = REPO_ROOT / "app" / "static" / "profiles.css"
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "cjk_font_fallback_audit_2026-05-30.md"


def _css_source() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _block(selector: str) -> str:
    source = _css_source()
    start = source.index(selector)
    end = source.index("}", start)
    return source[start:end]


def test_cjk_font_fallback_audit_document_records_expected_platforms():
    audit_doc = AUDIT_DOC_PATH.read_text(encoding="utf-8")

    assert "Backlog item: `GLOC-507`" in audit_doc
    assert "CJK font and fallback check" in audit_doc
    assert "Noto Sans CJK SC" in audit_doc
    assert "Microsoft YaHei" in audit_doc
    assert "PingFang SC" in audit_doc
    assert "tofu boxes" in audit_doc
    assert "line height" in audit_doc


def test_body_font_stack_includes_simplified_chinese_fallbacks():
    body_block = _block("body {")

    assert '"Avenir Next"' in body_block
    assert '"Segoe UI Variable"' in body_block
    assert '"Segoe UI"' in body_block
    assert '"Helvetica Neue"' in body_block
    assert '"Noto Sans CJK SC"' in body_block
    assert '"Microsoft YaHei"' in body_block
    assert '"PingFang SC"' in body_block
    assert body_block.index('"Noto Sans CJK SC"') < body_block.index("sans-serif")


def test_monospace_font_stacks_include_cjk_fallbacks():
    css_source = _css_source()
    mono_declarations = [
        line.strip()
        for line in css_source.splitlines()
        if 'font-family: "IBM Plex Mono"' in line
    ]

    assert mono_declarations
    for declaration in mono_declarations:
        assert '"Noto Sans Mono CJK SC"' in declaration
        assert '"Noto Sans CJK SC"' in declaration
        assert declaration.index('"Noto Sans Mono CJK SC"') < declaration.index("monospace")


def test_zh_cn_rendered_document_and_locale_option_expose_language_metadata():
    client = make_test_client(app)
    response = client.get(
        "/profiles/new",
        headers={"Accept-Language": "zh-Hans-CN,zh;q=0.9,en;q=0.1"},
    )
    soup = BeautifulSoup(response.text, "html.parser")
    zh_option = soup.find(id="lang").find("option", {"value": "zh-CN"})

    assert soup.find("html")["lang"] == "zh-CN"
    assert zh_option["lang"] == "zh-CN"
    assert zh_option["data-locale-bcp47"] == "zh-CN"
    assert zh_option.get_text(strip=True) == "简体中文"
