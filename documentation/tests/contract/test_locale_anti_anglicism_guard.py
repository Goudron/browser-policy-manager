from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
GUARD = DOC_ROOT / "config" / "locale-anti-anglicism-guard-0.9.1.json"
AUTHORITY = DOC_ROOT / "config" / "locale-terminology-authority-0.9.1.json"
REPLACEMENT = DOC_ROOT / "config" / "locale-anglicism-replacement-0.9.1.json"
SOURCE_I18N = ROOT / "app" / "i18n_src"
RUNTIME_I18N = ROOT / "app" / "i18n"

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _catalog_text(locale: str) -> str:
    chunks: list[str] = []
    for path in sorted((SOURCE_I18N / locale).glob("*.json")):
        chunks.extend(value for value in _json(path).values() if isinstance(value, str))
    chunks.extend(
        value for value in _json(RUNTIME_I18N / f"{locale}.json").values() if isinstance(value, str)
    )
    return "\n".join(chunks)


def _documentation_text(locale: str, guard: dict) -> str:
    chunks: list[str] = []
    for source in guard["enforcement"]["documentation_sources"]:
        relative_path = Path(source.format(locale=locale))
        chunks.append((ROOT / relative_path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _strip_allowed(text: str, authority: dict) -> str:
    cleaned = text
    for category in authority["allowlist"].values():
        for example in category["examples"]:
            cleaned = cleaned.replace(example, " ")
    for pattern in (
        r"\{[A-Za-z0-9_]+\}",
        r"https?://\S+",
        r"\b[A-Z]+ /api/[A-Za-z0-9_./-]+",
        r"\b[a-zA-Z][\w-]*(?:\.[\w-]+)+\b",
        r"\babout:[A-Za-z0-9_.-]+\b",
    ):
        cleaned = re.sub(pattern, " ", cleaned)
    return cleaned


def _violations(text: str, guard: dict, authority: dict) -> list[str]:
    cleaned = _strip_allowed(text, authority)
    fragments = set(guard["ordinary_english_fragments"])
    fragments.update(guard["enforcement"]["documentation_forbidden_fragments"])
    for locale_fragments in _json(REPLACEMENT)["forbidden_fragments_by_locale"].values():
        fragments.update(locale_fragments)
    return sorted(fragment for fragment in fragments if fragment in cleaned)


def test_locale_anti_anglicism_guard_declares_release_scope() -> None:
    guard = _json(GUARD)
    authority = _json(AUTHORITY)

    assert guard["schema_version"] == 1
    assert guard["backlog_item"] == "BPM091-M7-04"
    assert guard["target_bpm_version"] == "0.9.1"
    assert guard["status"] == "accepted"
    assert guard["locales"] == ["ru", "de", "zh-CN", "fr", "es-ES"]
    assert guard["allowlist_categories"] == list(authority["allowlist"])
    assert "not converted into allowlist" in guard["enforcement"]["known_debt_policy"]


def test_locale_anti_anglicism_guard_protects_product_catalog_replacements() -> None:
    replacement = _json(REPLACEMENT)

    for locale, fragments in replacement["forbidden_fragments_by_locale"].items():
        if locale == "ru":
            continue
        catalog_text = _catalog_text(locale)
        for fragment in fragments:
            assert fragment not in catalog_text, (locale, fragment)


def test_locale_anti_anglicism_guard_protects_documentation_strings() -> None:
    guard = _json(GUARD)

    for locale in guard["locales"]:
        if locale == "en":
            continue
        documentation_text = _documentation_text(locale, guard)
        for fragment in guard["enforcement"]["documentation_forbidden_fragments"]:
            assert fragment not in documentation_text, (locale, fragment)


def test_locale_anti_anglicism_guard_rejects_ordinary_english_fixtures() -> None:
    guard = _json(GUARD)
    authority = _json(AUTHORITY)

    for fixture in guard["fixture_expectations"]["reject"]:
        violations = _violations(fixture["text"], guard, authority)
        assert fixture["expected_fragment"] in violations


def test_locale_anti_anglicism_guard_accepts_allowlisted_technical_fixtures() -> None:
    guard = _json(GUARD)
    authority = _json(AUTHORITY)

    for fixture in guard["fixture_expectations"]["accept"]:
        assert _violations(fixture["text"], guard, authority) == []
