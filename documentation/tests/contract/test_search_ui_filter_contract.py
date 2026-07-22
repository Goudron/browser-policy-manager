from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
SEARCH_UI_CONTRACT = DOCUMENTATION_ROOT / "config/search-ui-filter-contract-0.9.1.json"
FACETS_CONTRACT = DOCUMENTATION_ROOT / "config/search-facets-filters-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_search_ui_filter_contract_is_scoped_to_091_and_preserves_static_search() -> None:
    contract = _json(SEARCH_UI_CONTRACT)

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-doc-search-ui-filter-contract-0.9.1"
    assert contract["backlog_item"] == "BPM091-M2-04"
    assert contract["target_bpm_version"] == "0.9.1"
    assert contract["status"] == "accepted"
    assert contract["search_mode"] == "deterministic-local-static"
    assert contract["non_ai_boundary"]["mode"] == "no-ai-no-rag-no-embeddings-no-generative-answers"

    inherited = set(contract["inherits_from"])
    assert {
        "documentation/config/search-corpus-and-results-0.9.0.json",
        "documentation/config/search-facets-filters-0.9.0.json",
        "documentation/config/search-quality-performance-0.9.0.json",
        "documentation/config/search-integrity-drift-0.9.0.json",
    } <= inherited
    assert "ranking, corpus generation, static indexes" in contract["non_ai_boundary"]["note"]
    assert "This contract does not change search ranking" in contract["non_goals"]


def test_search_default_state_is_one_line_and_advanced_options_are_explicit() -> None:
    contract = _json(SEARCH_UI_CONTRACT)

    default_state = contract["default_state"]
    assert default_state["layout"] == "one-line-compact"
    assert default_state["visible_controls"] == [
        "query_input",
        "submit",
        "clear",
        "advanced_toggle",
    ]
    assert "expanded facet grid" in default_state["must_not_show_by_default"]
    assert "multi-row filter panel" in default_state["must_not_show_by_default"]
    assert "single toolbar row" in default_state["height_rule"]

    expansion = contract["expansion_behavior"]
    assert expansion["trigger"] == "explicit advanced-options disclosure control"
    assert "preserves the current disclosure state" in expansion["submission_behavior"]
    assert "preserves the collapsed filter panel" in expansion["url_restore_behavior"]
    assert "query text" in expansion["preserve_on_expand"]
    assert "selected filters" in expansion["preserve_on_collapse"]
    assert "change deterministic ranking" in expansion["must_not"]
    assert "expand a collapsed filter panel when submitting a query" in expansion["must_not"]
    assert "trap keyboard focus" in expansion["must_not"]


def test_visible_facets_match_existing_facets_and_require_locale_owned_labels() -> None:
    contract = _json(SEARCH_UI_CONTRACT)
    facets = _json(FACETS_CONTRACT)["facet_fields"]
    labels = contract["localized_labels"]

    assert labels["hidden_facets"] == ["locale", "bpm_version"]
    visible = set(labels["visible_facets"])
    assert visible == set(facets) - {"locale", "bpm_version"}
    assert "fail closed for visible labels" in labels["fallback_policy"]
    assert "English fallback is not allowed in non-English locales" in labels["fallback_policy"]

    required_keys = set(labels["required_locale_keys"])
    for field in visible:
        assert f"search.filter.{field}" in required_keys
    assert "search.value.*" in required_keys


def test_label_examples_cover_all_locales_without_raw_facet_labels() -> None:
    contract = _json(SEARCH_UI_CONTRACT)
    facets = _json(FACETS_CONTRACT)["facet_fields"]
    examples = contract["label_examples"]
    visible = contract["localized_labels"]["visible_facets"]
    english_field_labels = examples["en"]["field_labels"]

    assert tuple(examples) == LOCALES
    for locale in LOCALES:
        locale_examples = examples[locale]
        assert set(locale_examples["field_labels"]) == set(visible)
        assert locale_examples["field_labels"].keys() <= facets.keys()
        assert locale_examples["value_labels"]["guide_id.user-guide"]
        assert locale_examples["value_labels"]["topic_kind.task"]
        assert locale_examples["value_labels"]["api_area.validation"]

    for locale in LOCALES:
        if locale == "en":
            continue
        for field, label in examples[locale]["field_labels"].items():
            assert label != field
            assert label != facets[field]["label"]
            assert label != english_field_labels[field]


def test_persistence_keyboard_empty_recovery_and_verification_are_covered() -> None:
    contract = _json(SEARCH_UI_CONTRACT)

    persistence = contract["facet_persistence"]
    assert "repeat-parameter URL contract" in persistence["query_parameter_contract"]
    assert "localized summary with a clear-all action" in persistence["compact_summary"]
    assert "direct links to filtered search states" in persistence["must_preserve"]

    keyboard = " ".join(contract["keyboard_access"]["requirements"])
    for requirement in (
        "Tab order",
        "Enter submits",
        "Space and Enter toggle",
        "Escape collapses",
        "polite live region",
        "removable with a keyboard",
    ):
        assert requirement in keyboard

    empty_recovery = contract["empty_result_recovery"]
    assert "clear-filter and clear-all controls" in empty_recovery["with_filters"]
    assert "keep the query editable" in empty_recovery["without_filters"]
    assert "offer AI answers" in empty_recovery["must_not"]
    assert "send the query to a network service" in empty_recovery["must_not"]

    assert contract["implementation_tasks"] == [
        "BPM091-M4-01",
        "BPM091-M4-02",
        "BPM091-M4-03",
        "BPM091-M4-07",
    ]
    assert "make test-docs-browser" in contract["verification"]["release_gates"]
