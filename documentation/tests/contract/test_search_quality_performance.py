from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
QUALITY_CONTRACT = DOCUMENTATION_ROOT / "config/search-quality-performance-0.9.0.json"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(QUALITY_CONTRACT.read_text(encoding="utf-8"))


def test_search_quality_contract_is_static_localized_and_non_ai() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-doc-search-quality-performance-0.9.0"
    assert contract["backlog_item"] == "BPM090-M10-07"
    assert contract["target_bpm_version"] == "0.9.0"
    assert contract["status"] == "accepted"
    assert contract["search_mode"] == "deterministic-local-static"
    assert contract["non_ai_boundary"] == "no-ai-no-rag-no-embeddings-no-generative-answers"
    assert contract["coverage_requirements"]["locales"] == list(build_docs.LOCALES)


def test_search_quality_fixtures_cover_required_categories_and_every_locale() -> None:
    contract = _contract()
    categories = set(contract["coverage_requirements"]["categories"])
    common_categories = categories - {"cjk"}
    fixtures = contract["quality_fixtures"]

    assert categories == {
        "exact",
        "natural_language",
        "typo",
        "synonym",
        "channel",
        "cis",
        "api",
        "cjk",
        "no_result",
        "adversarial",
    }
    assert {fixture["category"] for fixture in fixtures} == categories
    assert {fixture["locale"] for fixture in fixtures} == set(build_docs.LOCALES)
    for locale in build_docs.LOCALES:
        locale_categories = {
            fixture["category"]
            for fixture in fixtures
            if fixture["locale"] == locale
        }
        assert common_categories <= locale_categories
        assert len([fixture for fixture in fixtures if fixture["locale"] == locale]) >= 9
    assert any(
        fixture["locale"] == "zh-CN" and fixture["category"] == "cjk"
        for fixture in fixtures
    )
    build_docs._validate_quality_fixture_coverage(contract)


def test_search_quality_fixtures_define_expected_top_counts_filters_and_score_components() -> None:
    contract = _contract()
    fixtures = contract["quality_fixtures"]

    top_fixtures = [fixture for fixture in fixtures if fixture["category"] not in {"no_result", "adversarial"}]
    empty_fixtures = [fixture for fixture in fixtures if fixture["category"] in {"no_result", "adversarial"}]
    assert all(fixture.get("expected_top_topic_id") for fixture in top_fixtures)
    assert all(fixture.get("required_score_component") for fixture in top_fixtures)
    assert all(fixture.get("expected_count") == 0 for fixture in empty_fixtures)
    assert any(fixture["filters"].get("firefox_channel") == ["release-152"] for fixture in fixtures if "filters" in fixture)
    assert any(fixture["filters"].get("api_area") == ["validation"] for fixture in fixtures if "filters" in fixture)
    assert any(fixture["filters"].get("guide_id") == ["cis-settings-guide"] for fixture in fixtures if "filters" in fixture)


def test_search_performance_budget_is_deterministic_and_ci_stable() -> None:
    contract = _contract()
    budget = contract["performance_budget"]

    assert "wall-clock" in budget["latency_budget_proxy"]
    assert budget["max_index_bytes_per_locale"] == 4100000
    assert budget["max_documents_per_locale"] >= 122
    assert budget["max_quality_fixtures_per_locale"] >= 10
    assert budget["max_visible_results_per_query"] == 50
    assert budget["max_deterministic_scan_units_per_locale"] >= 1220
