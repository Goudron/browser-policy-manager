from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPO_ROOT / "documentation"
BUILD_DOCS = DOCUMENTATION_ROOT / "tools/build_docs.py"
SEARCH_UI_CONTRACT = DOCUMENTATION_ROOT / "config/search-ui-filter-contract-0.9.1.json"
SEARCH_RANKING = DOCUMENTATION_ROOT / "config/search-ranking-typo-0.9.0.json"
SEARCH_FACETS = DOCUMENTATION_ROOT / "config/search-facets-filters-0.9.0.json"
SEARCH_QUALITY = DOCUMENTATION_ROOT / "config/search-quality-performance-0.9.0.json"
SEARCH_INTEGRITY = DOCUMENTATION_ROOT / "config/search-integrity-drift-0.9.0.json"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"

SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _js_block(source: str, start_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index("\n  };", start) + len("\n  };")
    return source[start:end]


def test_compact_search_ui_explicitly_inherits_existing_deterministic_contracts() -> None:
    contract = _json(SEARCH_UI_CONTRACT)

    assert contract["search_mode"] == "deterministic-local-static"
    assert contract["inherits_from"] == [
        "documentation/config/search-corpus-and-results-0.9.0.json",
        "documentation/config/search-facets-filters-0.9.0.json",
        "documentation/config/search-quality-performance-0.9.0.json",
        "documentation/config/search-integrity-drift-0.9.0.json",
    ]
    assert "ranking, corpus generation, static indexes" in contract["non_ai_boundary"]["note"]
    assert "This contract does not change search ranking" in contract["non_goals"]
    assert "change deterministic ranking" in contract["expansion_behavior"]["must_not"]


def test_build_time_ranking_filter_url_and_empty_state_fixtures_remain_authoritative() -> None:
    ranking = _json(SEARCH_RANKING)
    facets = _json(SEARCH_FACETS)
    quality = _json(SEARCH_QUALITY)
    integrity = _json(SEARCH_INTEGRITY)

    assert ranking["contract_id"] == "bpm-doc-search-ranking-typo-0.9.0"
    assert ranking["ranking_order"] == [
        "exact_identifier",
        "title",
        "alias",
        "heading",
        "body",
        "bounded_typo",
    ]
    assert ranking["weights"]["recency"] == 0
    assert ranking["tie_breakers"] == [
        "score_desc",
        "exact_identifier_desc",
        "title_desc",
        "alias_desc",
        "guide_id",
        "topic_id",
    ]
    assert facets["url_state"]["parameters"]["guide_id"] == "guide"
    assert facets["url_state"]["parameters"]["api_area"] == "api_area"
    assert set(facets["empty_result"]["messages"]) == set(build_docs.LOCALES)
    assert quality["contract_id"] == "bpm-doc-search-quality-performance-0.9.0"
    assert integrity["contract_id"] == "bpm-doc-search-integrity-drift-0.9.0"


def test_compact_search_toggle_does_not_mutate_query_filters_ranking_or_url_state() -> None:
    script = _source(SEARCH_SCRIPT)
    toggle_start = script.index('root.querySelector("[data-search-advanced-toggle]")?.addEventListener("click"')
    toggle_block = script[toggle_start : script.index("\n    });", toggle_start) + len("\n    });")]
    set_expanded_block = _js_block(script, "const setSearchExpanded = (root, expanded) => {")

    for forbidden in (
        "input.value",
        "selectedFilters",
        "queryTokens",
        "scoreDocument",
        "documentMatchesFilters",
        "renderResults",
        "updateUrlState",
        "window.history.replaceState",
        "fetch(",
    ):
        assert forbidden not in toggle_block
        assert forbidden not in set_expanded_block

    assert "panel.hidden = !expanded;" in set_expanded_block
    assert 'toggle.setAttribute("aria-expanded", expanded ? "true" : "false");' in set_expanded_block
    assert "setSearchExpanded(root, !expanded);" in toggle_block


def test_compact_search_preserves_existing_result_url_highlight_and_empty_state_paths() -> None:
    script = _source(SEARCH_SCRIPT)

    for required in (
        "const safeResultUrl = (locale, url) => {",
        "const localeRoot = `/help/${locale}/`;",
        "!resolved.pathname.startsWith(localeRoot)",
        "const appendMarkedText = (parent, text, tokens, normalization) => {",
        'const mark = document.createElement("mark");',
        "status.textContent = root.dataset.labelReady || \"Search ready.\";",
        "status.textContent = root.dataset.labelNoResults || \"No results.\";",
        "status.textContent = root.dataset.labelResultSingular || \"1 result\";",
        "status.textContent = `${result.resultCount} ${root.dataset.labelResultPlural || \"results\"}`;",
        "renderResults(root, locale, result.documents, result.tokens, index);",
        "updateUrlState(root, result, index);",
    ):
        assert required in script
