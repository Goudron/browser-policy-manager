from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DITA_ROOT = ROOT / "documentation/src/dita"
CONTRACT = ROOT / "documentation/config/semantic-ui-markup-0.9.4.json"
SITE_THEME = ROOT / "documentation/assets/theme/bpm-docs.css"
PDF_THEME = ROOT / "documentation/assets/pdf/bpm-guide-print.css"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _topics(locale: str) -> list[Path]:
    return sorted((DITA_ROOT / locale).rglob("*.dita"))


def _matches(text: str, value: str, *, locale: str) -> bool:
    if locale == "zh-CN":
        return value in text
    return re.search(rf"(?<![\w-]){re.escape(value)}(?![\w-])", text) is not None


def _outside_text(
    root: ET.Element,
    excluded: set[str],
    *,
    exclude_notes: bool = False,
) -> Iterable[str]:
    def visit(element: ET.Element, blocked: bool = False) -> Iterable[str]:
        current_blocked = blocked or element.tag == "uicontrol" or element.tag in excluded
        if exclude_notes and element.tag == "note":
            current_blocked = True
        if element.text and not current_blocked:
            yield element.text
        for child in element:
            yield from visit(child, current_blocked)
            if child.tail and not current_blocked:
                yield child.tail

    return visit(root)


def test_semantic_ui_contract_is_global_scoped_and_owned() -> None:
    contract = _json(CONTRACT)

    assert contract["schema_version"] == 1
    assert contract["backlog_item"] == "BPM094-M11-03"
    assert contract["status"] == "implemented"
    assert contract["locales"] == list(LOCALES)
    assert len(contract["global_catalog_keys"]) >= 28
    assert len(contract["scoped_catalog_keys"]) >= 30
    assert (
        "profiles.locale_system"
        in contract["scoped_catalog_keys"]["user/ug-task-change-interface-language.dita"]
    )
    assert "profiles.nav_library" in contract["ambiguous_exclusions"]
    assert (
        "profiles.nav_library"
        in contract["scoped_catalog_keys"]["user/ug-task-use-profile-library.dita"]
    )
    assert set(contract["excluded_elements"]) >= {
        "title",
        "navtitle",
        "alt",
        "figdesc",
        "codeph",
        "filepath",
        "apiname",
    }


def test_registered_catalog_ui_names_are_never_bare_in_maintained_prose() -> None:
    contract = _json(CONTRACT)
    excluded = set(contract["excluded_elements"])
    ambiguous = set(contract["ambiguous_exclusions"])
    findings: list[tuple[str, str, str, str]] = []

    for locale in LOCALES:
        catalog = _json(ROOT / f"app/i18n/{locale}.json")
        for path in _topics(locale):
            relative = path.relative_to(DITA_ROOT / locale).as_posix()
            root = ET.parse(path).getroot()
            global_text = "\n".join(_outside_text(root, excluded))
            for key in contract["global_catalog_keys"]:
                if key in ambiguous:
                    continue
                value = catalog[key]
                if _matches(global_text, value, locale=locale):
                    findings.append((locale, relative, key, value))

            scoped_keys = contract["scoped_catalog_keys"].get(relative, [])
            if scoped_keys:
                scoped_text = "\n".join(_outside_text(root, excluded, exclude_notes=True))
                for key in scoped_keys:
                    if key in ambiguous:
                        continue
                    value = catalog[key]
                    if _matches(scoped_text, value, locale=locale):
                        findings.append((locale, relative, key, value))

    assert findings == []


def test_uicontrol_markup_spans_the_maintained_corpus_without_semantic_collisions() -> None:
    contract = _json(CONTRACT)
    excluded = set(contract["excluded_elements"])

    for locale in LOCALES:
        control_topics = 0
        control_count = 0
        for path in _topics(locale):
            root = ET.parse(path).getroot()
            controls = root.findall(".//uicontrol")
            if controls:
                control_topics += 1
                control_count += len(controls)
            parent = {child: element for element in root.iter() for child in element}
            for control in controls:
                assert "".join(control.itertext()).strip(), (locale, path)
                ancestor = parent.get(control)
                while ancestor is not None:
                    assert ancestor.tag not in excluded, (locale, path, ancestor.tag)
                    ancestor = parent.get(ancestor)

        assert control_topics > 60, (locale, control_topics)
        assert control_count > 150, (locale, control_count)


def test_browser_locale_mode_uses_the_exact_runtime_catalog_label() -> None:
    topic_ids = (
        "ug-concept-language-detection-fallback",
        "ug-task-change-interface-language",
    )
    for locale in LOCALES:
        catalog = _json(ROOT / f"app/i18n/{locale}.json")
        expected = catalog["profiles.locale_system"]
        for topic_id in topic_ids:
            root = ET.parse(DITA_ROOT / locale / "user" / f"{topic_id}.dita").getroot()
            controls = {
                "".join(control.itertext()).strip() for control in root.findall(".//uicontrol")
            }
            assert expected in controls, (locale, topic_id, expected)


def test_every_admonition_is_semantic_and_all_locale_counts_match() -> None:
    counts: dict[str, int] = {}
    for locale in LOCALES:
        notes = [
            note for path in _topics(locale) for note in ET.parse(path).getroot().findall(".//note")
        ]
        counts[locale] = len(notes)
        assert notes
        assert all(note.get("type") == "warning" for note in notes)
        assert all("".join(note.itertext()).strip() for note in notes)

    assert len(set(counts.values())) == 1
    assert next(iter(counts.values())) >= 117


def test_site_and_pdf_themes_keep_ui_controls_and_admonition_titles_distinct() -> None:
    site_theme = SITE_THEME.read_text(encoding="utf-8")
    pdf_theme = PDF_THEME.read_text(encoding="utf-8")

    for theme in (site_theme, pdf_theme):
        assert ".uicontrol" in theme
        assert ".note__title" in theme
        assert "font-weight: 700" in theme

    assert "font-family: inherit" in site_theme
    assert "font-family: inherit" in pdf_theme
    assert "Cascadia Mono" in site_theme
    assert "DejaVu Sans Mono" in pdf_theme
