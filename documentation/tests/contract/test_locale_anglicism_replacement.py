from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
REPLACEMENT = DOC_ROOT / "config" / "locale-anglicism-replacement-0.9.1.json"
INVENTORY = DOC_ROOT / "config" / "locale-visible-english-inventory-0.9.1.json"
SOURCE_DIR = ROOT / "app" / "i18n_src"
RUNTIME_DIR = ROOT / "app" / "i18n"

LOCALES = ("de", "zh-CN", "fr", "es-ES")
PLACEHOLDER_RE = re.compile(r"\{[A-Za-z0-9_]+\}")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_catalog(locale: str) -> dict[str, str]:
    catalog: dict[str, str] = {}
    for path in sorted((SOURCE_DIR / locale).glob("*.json")):
        catalog.update(_json(path))
    return catalog


def _runtime_catalog(locale: str) -> dict[str, str]:
    return _json(RUNTIME_DIR / f"{locale}.json")


def _visible_text(catalog: dict[str, str]) -> str:
    return "\n".join(value for value in catalog.values() if isinstance(value, str))


def test_locale_anglicism_replacement_closes_all_inventory_replace_findings() -> None:
    replacement = _json(REPLACEMENT)
    inventory = _json(INVENTORY)

    assert replacement["schema_version"] == 1
    assert replacement["backlog_item"] == "BPM091-M7-03"
    assert replacement["target_bpm_version"] == "0.9.1"
    assert replacement["status"] == "accepted"
    assert "make build-locale-catalogs" in replacement["scope"]["generated_by"]

    replace_finding_ids = {
        finding["id"] for finding in inventory["findings"] if finding["classification"] == "replace"
    }
    assert set(replacement["closed_findings"]) == replace_finding_ids


def test_locale_anglicism_replacement_removes_forbidden_fragments_from_sources_and_runtime() -> (
    None
):
    replacement = _json(REPLACEMENT)

    for locale in LOCALES:
        combined_text = "\n".join(
            (
                _visible_text(_source_catalog(locale)),
                _visible_text(_runtime_catalog(locale)),
            )
        )
        for fragment in replacement["forbidden_fragments_by_locale"][locale]:
            assert fragment not in combined_text, (locale, fragment)

        exact_values = replacement["exact_value_absent_by_locale"].get(locale, [])
        if exact_values:
            values = set(_source_catalog(locale).values()) | set(_runtime_catalog(locale).values())
            for exact_value in exact_values:
                assert exact_value not in values, (locale, exact_value)


def test_locale_anglicism_replacement_keeps_source_and_runtime_catalogs_in_sync() -> None:
    for locale in LOCALES:
        source = _source_catalog(locale)
        runtime = _runtime_catalog(locale)

        for key, value in source.items():
            assert runtime[key] == value, (locale, key)


def test_locale_anglicism_replacement_preserves_placeholders() -> None:
    replacement = _json(REPLACEMENT)

    for locale in LOCALES:
        source = _source_catalog(locale)
        runtime = _runtime_catalog(locale)
        for key in replacement["placeholder_preservation_keys"]:
            if key not in source:
                continue
            assert PLACEHOLDER_RE.findall(source[key]) == PLACEHOLDER_RE.findall(runtime[key])


def test_locale_anglicism_replacement_records_representative_terms() -> None:
    replacement = _json(REPLACEMENT)

    for locale, expected_values in replacement["representative_replacements"].items():
        runtime = _runtime_catalog(locale)
        for key, expected_value in expected_values.items():
            assert runtime[key] == expected_value
