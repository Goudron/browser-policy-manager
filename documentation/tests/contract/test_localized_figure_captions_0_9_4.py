"""Source contract for localized BPM 0.9.4 figure captions."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from documentation.buildlib import pdf

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation/src/dita"
PORTAL_CSS = ROOT / "documentation/assets/theme/bpm-docs.css"
PRINT_CSS = ROOT / "documentation/assets/pdf/bpm-guide-print.css"
PDF_TOOL = ROOT / "documentation/buildlib/pdf.py"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDE_MAPS = {
    "user": "user-guide.ditamap",
    "admin": "administrator-guide.ditamap",
    "firefox": "firefox-policy-guide.ditamap",
    "cis": "cis-settings-guide.ditamap",
}
MANUAL_FIGURE_PREFIXES = {
    "en": "Figure {number}. ",
    "ru": "Рисунок {number}. ",
    "de": "Abbildung {number}. ",
    "zh-CN": "图 {number}. ",
    "fr": "Figure {number}. ",
    "es-ES": "Figura {number}. ",
}
USER_GUIDE_FIGURE_IDS = (
    "screenshot-preparation-create",
    "screenshot-guided-editor-overview",
    "screenshot-guided-step-6-extensions",
    "screenshot-guided-settings-search",
    "screenshot-guided-step-2-urls-sites-navigation",
    "screenshot-guided-step-4-certificates-trust",
    "screenshot-all-settings-review",
    "screenshot-json-editor",
    "screenshot-library-overview",
    "screenshot-preparation-duplicate",
    "screenshot-compare-profiles",
)

pytestmark = pytest.mark.docs_contract


def _text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def _keydefs(locale: str) -> dict[str, str]:
    root = ET.parse(DITA_ROOT / locale / "maps/keys.ditamap").getroot()
    return {
        keydef.attrib["keys"]: keydef.attrib["href"]
        for keydef in root.findall("keydef")
        if keydef.attrib.get("href", "").endswith(".dita")
    }


def _map_topics(locale: str, guide: str) -> list[Path]:
    locale_root = (DITA_ROOT / locale).resolve()
    map_path = locale_root / "maps" / GUIDE_MAPS[guide]
    keydefs = _keydefs(locale)
    topics: list[Path] = []
    for topicref in ET.parse(map_path).getroot().iter("topicref"):
        href = topicref.attrib.get("href") or keydefs.get(topicref.attrib.get("keyref", ""))
        if not href or not href.endswith(".dita"):
            continue
        topic = (map_path.parent / href).resolve()
        assert topic.is_relative_to(locale_root), topic
        if topic not in topics:
            topics.append(topic)
    return topics


def _figures(paths: list[Path]) -> list[tuple[Path, ET.Element]]:
    return [
        (path, figure) for path in paths for figure in ET.parse(path).getroot().findall(".//fig")
    ]


def test_all_maintained_figures_are_mapped_labeled_and_locale_complete() -> None:
    for locale in LOCALES:
        for guide in GUIDE_MAPS:
            topic_root = DITA_ROOT / locale / guide
            maintained = _figures(sorted(topic_root.glob("*.dita")))
            mapped = _figures(_map_topics(locale, guide))

            assert {(path, figure.attrib.get("id")) for path, figure in maintained} == {
                (path, figure.attrib.get("id")) for path, figure in mapped
            }
            ids = [figure.attrib.get("id") for _path, figure in mapped]
            assert all(ids)
            assert len(ids) == len(set(ids))

            if guide != "user":
                assert ids == []
                continue

            assert ids == list(USER_GUIDE_FIGURE_IDS)
            for _number, (_path, figure) in enumerate(mapped, start=1):
                title = _text(figure.find("title"))
                image = figure.find("image")
                assert title
                assert not any(
                    title.startswith(prefix.format(number=number))
                    for prefix in MANUAL_FIGURE_PREFIXES.values()
                    for number in range(1, len(USER_GUIDE_FIGURE_IDS) + 1)
                ), title
                assert image is not None
                assert image.attrib.get("keyref")
                assert _text(image.find("alt"))


def test_figure_caption_styles_are_visible_and_keep_source_images_printable() -> None:
    portal_css = PORTAL_CSS.read_text(encoding="utf-8")
    print_css = PRINT_CSS.read_text(encoding="utf-8")
    pdf_tool = PDF_TOOL.read_text(encoding="utf-8")

    assert ".bpm-docs-main figcaption" in portal_css
    assert ".bpm-docs-main .figcap" in portal_css
    assert "figcaption," in print_css
    assert ".figcap," in print_css
    assert "display: block;" in print_css
    assert "text-align: center;" in print_css
    assert "page-break-inside: avoid;" in print_css
    assert "max-width: 100%;" in print_css
    assert "max-height: 210mm;" in print_css
    assert "assets/pdf/bpm-guide-print.css" in pdf_tool
    assert "def _number_pdf_figure_captions" in pdf_tool
    assert "PDF_USER_GUIDE_FIGURE_COUNT = 11" in pdf_tool


def test_rendered_pdf_figure_caption_sequences_are_consecutive_in_every_locale() -> None:
    expected = list(range(1, len(USER_GUIDE_FIGURE_IDS) + 1))
    for locale, prefix in pdf.PDF_FIGURE_CAPTION_PREFIXES.items():
        label = f"{prefix} {{number}}. "
        article = "".join(
            f'<figcaption><span class="fig--title-label">{label.format(number=1)}</span>'
            f"caption {number}</figcaption>"
            for number in expected
        )
        numbered, next_number = pdf._number_pdf_figure_captions(
            article, locale=locale, first_number=1
        )
        assert next_number == len(expected) + 1
        for number in expected:
            assert label.format(number=number) in numbered

        rendered_pdf = ET.fromstring(
            "<doc><page>"
            + "".join(
                "<line>"
                f'<word xMin="0" xMax="1">{pdf.PDF_FIGURE_CAPTION_PREFIXES[locale]}</word>'
                f'<word xMin="2" xMax="3">{number}.</word>'
                "</line>"
                for number in expected
            )
            + "</page></doc>"
        )
        assert pdf._pdf_figure_caption_numbers(list(rendered_pdf), locale) == expected
