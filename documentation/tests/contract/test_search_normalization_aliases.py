from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
SEARCH_NORMALIZATION_ALIASES = DOCUMENTATION_ROOT / "config/search-normalization-aliases-0.9.0.json"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _config() -> dict[str, object]:
    return json.loads(SEARCH_NORMALIZATION_ALIASES.read_text(encoding="utf-8"))


def test_search_normalization_contract_defines_locale_rules_and_non_ai_boundary() -> None:
    config = _config()

    assert config["schema_version"] == 1
    assert config["contract_id"] == "bpm-doc-search-normalization-aliases-0.9.0"
    assert config["backlog_item"] == "BPM096-M10-04"
    assert config["status"] == "accepted"
    assert config["locales"] == list(build_docs.LOCALES)
    assert config["non_ai_boundary"] == "no-ai-no-rag-no-embeddings-no-generative-answers"

    normalization = config["normalization"]
    assert normalization["unicode_form"] == "NFKC"
    assert normalization["casefold"] is True
    assert normalization["strip_diacritics"] is True
    assert "CJK" in normalization["cjk_tokenization"]
    assert "do not translate identifiers" in normalization["identifier_policy"]


def test_search_alias_groups_are_reviewed_for_all_six_locales() -> None:
    config = _config()
    locales = set(build_docs.LOCALES)
    alias_ids = {alias_group["alias_id"] for alias_group in config["alias_groups"]}

    assert alias_ids == {
        "profile-library",
        "firefox-ai-controls",
        "api-validation",
        "cis-baseline",
        "json-import-export",
        "firefox-esr-lifecycle-and-conversion",
        "profile-preparation",
        "guided-urls-sites-navigation",
        "guided-certificates-trust",
        "guided-extensions",
    }
    for alias_group in config["alias_groups"]:
        assert set(alias_group["terms"]) == locales
        assert alias_group["target_topic_ids"] or alias_group["target_ids"]
        assert alias_group["technical_identifiers"]
        for locale in build_docs.LOCALES:
            assert alias_group["terms"][locale]


def test_search_normalizer_handles_case_diacritics_cjk_paths_and_identifiers() -> None:
    config = _config()

    assert "bibliotheque" in build_docs._normalize_search_text("fr", "Bibliothèque", config)
    assert "validacion" in build_docs._normalize_search_text("es-ES", "validación API", config)
    assert "профилей" in build_docs._normalize_search_text("ru", "Библиотека профилей", config)

    cjk_tokens = build_docs._normalize_search_text("zh-CN", "配置档案库", config)
    assert {"配置档案库", "配", "置", "配置", "档案"} <= set(cjk_tokens)

    identifier_tokens = build_docs._normalize_search_text(
        "en",
        "AIControls policy:AIControls API-VAL-001 /api/validation/firefox",
        config,
    )
    assert {
        "aicontrols",
        "policy:aicontrols",
        "api-val-001",
        "/api/validation/firefox",
    } <= set(identifier_tokens)


def test_reviewed_query_fixtures_resolve_without_ai_or_identifier_translation() -> None:
    config = _config()
    fixture_locales = {fixture["locale"] for fixture in config["query_fixtures"]}
    alias_ids = {alias_group["alias_id"] for alias_group in config["alias_groups"]}

    assert fixture_locales == set(build_docs.LOCALES)
    for fixture in config["query_fixtures"]:
        locale = fixture["locale"]
        tokens = set(build_docs._normalize_search_text(locale, fixture["query"], config))
        resolved_aliases = set(
            build_docs._resolve_search_query_aliases(locale, fixture["query"], config)
        )
        assert set(fixture["expected_tokens"]) <= tokens, fixture["fixture_id"]
        assert set(fixture["expected_alias_ids"]) <= resolved_aliases, fixture["fixture_id"]
        assert set(fixture["expected_alias_ids"]) <= alias_ids
