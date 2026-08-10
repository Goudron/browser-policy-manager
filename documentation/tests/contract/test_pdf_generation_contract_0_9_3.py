"""Contract guard for the deterministic six-locale PDF candidate generator."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "documentation/config/pdf-generation-contract-0.9.3.json"
PDF_TOOL = ROOT / "documentation/buildlib/pdf.py"
MAKEFILE = ROOT / "Makefile"
PDF_PRINT_CSS = ROOT / "documentation/assets/pdf/bpm-guide-print.css"
PDF_COVER_LOGO = ROOT / "documentation/assets/branding/bpm-logo.png"
PDF_RUNBOOK = ROOT / "documentation/runbooks/documentation-update-for-future-epics.md"
DITA_ROOT = ROOT / "documentation/src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
ZH_TITLE_ALLOWED_ASCII_TOKENS = frozenset({"Firefox", "policies.json", "JSON"})


def _zh_title_ascii_tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z][A-Za-z0-9._/-]*", text))


pytestmark = pytest.mark.docs_contract


def test_m14_08_pdf_generation_contract_covers_every_required_pdf() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert contract["backlog_item"] == "BPM093-M14-08"
    assert contract["target_bpm_version"] == "0.9.4"
    assert contract["candidate_root"] == "documentation/build/pdf"
    assert contract["candidate_path_layout"] == "{locale}/{filename}"
    assert contract["dita_format"] == "html5"
    assert contract["pdf_renderer"] == "chromium"
    assert contract["page_number_overlay_renderer"] == "native-pdf"
    assert contract["ui_footer_year"] == 2026
    assert contract["source_maps"] == ["user-guide.ditamap", "administrator-guide.ditamap"]
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["determinism"]["environment"]["SOURCE_DATE_EPOCH"] == "0"
    assert contract["determinism"]["pdf_metadata"]["creation_date"] == [
        "D:19700101000000Z",
        "D:19700101000000+00'00'",
    ]
    assert "qpdf --static-id" in contract["determinism"]["pdf_metadata"]["canonicalizer"]
    assert contract["determinism"]["pdf_metadata"]["xmp_timestamp"] == [
        "1970-01-01T00:00:00Z",
        "1970-01-01T00:00:00+00:00",
    ]
    assert contract["development_cache"] == {
        "schema_version": 1,
        "root": "documentation/.cache/pdf-pipeline",
        "unit": "locale-guide",
        "layers": ["dita-html5", "verified-pdf"],
        "hash_algorithm": "sha256",
        "reuse": "verified-only",
        "invalid_entry": "quarantine-and-rebuild",
        "promotion": "staged-and-atomic",
    }
    assert contract["parallelism"]["max_workers"] == 1
    assert contract["operator_commands"] == {
        "build": "make docs-pdf-build",
        "verify": "make docs-pdf-verify",
        "reproducibility": "make docs-pdf-reproducibility",
    }
    assert "BPM093-M14-09" in contract["safety"]["delivery_boundary"]


def test_pdf_generator_and_make_targets_preserve_the_delivery_boundary() -> None:
    tool = PDF_TOOL.read_text(encoding="utf-8")
    makefile = MAKEFILE.read_text(encoding="utf-8")

    assert "def build_pdf_tree" in tool
    assert "def publish_pdfs" in tool
    assert "def pdf_reproducibility_check" in tool
    assert 'progress.phase(f"{locale}/{guide_id} DITA HTML5")' in tool
    assert 'progress.phase(f"{locale}/{guide_id} Chromium PDF")' in tool
    assert "assets/pdf/bpm-guide-print.css" in tool
    assert "assets/branding/bpm-logo.png" in tool
    assert "def _write_pdf_print_guide" in tool
    assert "def _render_pdf_with_chromium" in tool
    assert "def _pdf_pair_source_hashes" in tool
    assert "def _reuse_pdf_cache_entry" in tool
    assert "def _store_pdf_cache_entry" in tool
    assert "build_pdf_tree(candidate, use_cache=False)" in tool
    assert "def _pdf_navigation_model" in tool
    assert "def _validate_pdf_print_contract" in tool
    assert "def _pdf_figure_caption_numbers" in tool
    assert "PDF_FIGURE_CAPTION_PREFIXES" in tool
    assert "PDF figure-caption sequence is invalid" in tool
    assert "def _overlay_pdf_page_numbers" in tool
    assert "PDF_UI_FOOTER_TEMPLATE" in tool
    assert '"--headless"' in tool
    assert '"--disable-background-networking"' in tool
    assert '"--print-to-pdf=' in tool
    assert "distributions/documentation" not in tool
    assert "docs-pdf-build:" in makefile
    assert "docs-pdf-verify:" in makefile
    assert "docs-pdf-reproducibility:" in makefile


def test_print_css_uses_a4_branding_and_constrains_every_user_guide_screenshot() -> None:
    css = PDF_PRINT_CSS.read_text(encoding="utf-8")
    logo = PDF_COVER_LOGO.read_bytes()

    assert "size: A4" in css
    assert ".bpm-pdf-cover" in css
    assert ".bpm-pdf-cover__logo" in css
    assert ".bpm-pdf-cover__copyright" in css
    assert ".bpm-pdf-toc__page" in css
    assert "max-width: 100%" in css
    assert "max-height: 210mm" in css
    assert "white-space: pre-wrap" in css
    assert logo.startswith(b"\x89PNG\r\n\x1a\n")
    for locale in LOCALES:
        for topic in (DITA_ROOT / locale / "user").glob("*.dita"):
            for image in ET.parse(topic).getroot().findall(".//image"):
                assert image.attrib.get("scalefit") == "yes" or "height" in image.attrib


def test_chinese_pdf_navigation_titles_do_not_mix_fallback_font_metrics() -> None:
    """Allow only reviewed product and data literals in Chinese navigation titles."""

    for topic in sorted((DITA_ROOT / "zh-CN").rglob("*.dita")) + sorted(
        (DITA_ROOT / "zh-CN").rglob("*.ditamap")
    ):
        root = ET.parse(topic).getroot()
        for tag in ("title", "navtitle"):
            for element in root.findall(f".//{tag}"):
                tokens = _zh_title_ascii_tokens("".join(element.itertext()))
                assert tokens <= ZH_TITLE_ALLOWED_ASCII_TOKENS, (topic, tokens)


def test_chinese_pdf_navigation_title_ascii_guard_allows_only_protected_literals() -> None:
    assert _zh_title_ascii_tokens("完整的 Firefox policies.json 文档") == {
        "Firefox",
        "policies.json",
    }
    assert _zh_title_ascii_tokens("使用 JSON 编辑器") == {"JSON"}
    assert _zh_title_ascii_tokens(
        "完整的 Firefox draft-policy 文档"
    ) - ZH_TITLE_ALLOWED_ASCII_TOKENS == {"draft-policy"}


def test_pdf_authoring_runbook_requires_binary_navigation_and_print_verification() -> None:
    runbook = " ".join(PDF_RUNBOOK.read_text(encoding="utf-8").split())

    for requirement in (
        "two-pass Chromium render",
        "actual named-destination page",
        "positioned `pdftotext` output",
        "absence of a page number on page 1",
        "Never edit generated PDFs manually",
    ):
        assert requirement in runbook
