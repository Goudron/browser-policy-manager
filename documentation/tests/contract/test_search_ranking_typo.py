from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
SEARCH_RANKING_TYPO = DOCUMENTATION_ROOT / "config/search-ranking-typo-0.9.0.json"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _config() -> dict[str, object]:
    return json.loads(SEARCH_RANKING_TYPO.read_text(encoding="utf-8"))


def test_search_ranking_contract_defines_explainable_non_ai_scoring() -> None:
    config = _config()

    assert config["schema_version"] == 1
    assert config["contract_id"] == "bpm-doc-search-ranking-typo-0.9.0"
    assert config["backlog_item"] == "BPM090-M10-04"
    assert config["status"] == "accepted"
    assert config["non_ai_boundary"] == "no-ai-no-rag-no-embeddings-no-generative-answers"
    assert config["ranking_order"] == [
        "exact_identifier",
        "title",
        "alias",
        "heading",
        "body",
        "bounded_typo",
    ]
    assert config["weights"]["exact_identifier"] > config["weights"]["title"]
    assert config["weights"]["title"] > config["weights"]["alias"]
    assert config["weights"]["alias"] > config["weights"]["heading"]
    assert config["weights"]["heading"] > config["weights"]["body"]
    assert config["weights"]["bounded_typo"] < config["weights"]["body"]
    assert config["weights"]["recency"] == 0


def test_search_typo_tolerance_is_bounded_and_excludes_identifiers() -> None:
    config = _config()
    tolerance = config["typo_tolerance"]

    assert tolerance["algorithm"] == "bounded-levenshtein"
    assert tolerance["min_token_length"] == 5
    assert tolerance["max_token_length"] == 32
    assert tolerance["fields"] == ["title", "aliases", "headings"]
    assert build_docs._bounded_levenshtein("profil", "profile", 1) == 1
    assert build_docs._bounded_levenshtein("profile", "policies", 1) is None
    assert build_docs._max_typo_distance("api", config) == 0
    assert build_docs._max_typo_distance("profile", config) == 1
    assert build_docs._max_typo_distance("validierungsendpunkt", config) == 2
    assert build_docs._is_typo_excluded("/api/validation/firefox", config) is True
    assert build_docs._is_typo_excluded("API-VAL-001", config) is True
    assert build_docs._is_typo_excluded("1.1.1.1", config) is True


def test_search_ranking_fixtures_cover_exact_alias_title_typo_and_all_locales() -> None:
    config = _config()
    fixture_ids = {fixture["fixture_id"] for fixture in config["ranking_fixtures"]}
    fixture_locales = {fixture["locale"] for fixture in config["ranking_fixtures"]}

    assert fixture_locales == set(build_docs.LOCALES)
    assert {
        "exact-policy-ai-controls",
        "exact-api-validation-operation",
        "exact-cis-recommendation",
        "title-api-validation",
        "alias-ru-ai-controls",
        "typo-en-profile-library",
        "typo-de-validation-endpoint",
    } <= fixture_ids
    assert {
        fixture["required_score_component"]
        for fixture in config["ranking_fixtures"]
    } >= {"exact_identifier", "title", "alias", "bounded_typo"}
