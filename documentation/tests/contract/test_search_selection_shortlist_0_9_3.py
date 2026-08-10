from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SHORTLIST_PATH = ROOT / "documentation/config/search-selection-shortlist-0.9.3.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")

pytestmark = pytest.mark.docs_contract


def _shortlist() -> dict:
    return json.loads(SHORTLIST_PATH.read_text(encoding="utf-8"))


def test_search_selection_shortlist_freezes_public_gates_and_exact_weights() -> None:
    shortlist = _shortlist()

    assert shortlist["schema_version"] == 1
    assert shortlist["backlog_item"] == "BPM093-M3-01"
    assert shortlist["target_bpm_version"] == "0.9.3"
    assert shortlist["status"] == "accepted-shortlist-not-benchmarked"
    assert tuple(shortlist["selection_inputs"]["locales"]) == LOCALES
    assert (
        shortlist["gate_rule"]["visibility"]
        == "All entry gates are explicit in this contract; there are no hidden vetoes."
    )
    assert [gate["id"] for gate in shortlist["entry_gates"]] == [
        "SG093-E1",
        "SG093-E2",
        "SG093-E3",
        "SG093-E4",
        "SG093-E5",
        "SG093-E6",
    ]

    dimensions = shortlist["weighted_matrix"]["dimensions"]
    assert {dimension["id"]: dimension["weight_percent"] for dimension in dimensions} == {
        "relevance": 35,
        "locale_parity": 20,
        "resource_performance": 15,
        "offline_csp_accessibility": 10,
        "facet_integration": 10,
        "license_security_operations_maintenance": 10,
    }
    assert sum(dimension["weight_percent"] for dimension in dimensions) == 100
    assert shortlist["weighted_matrix"]["score_scale"] == {
        "minimum": 0,
        "maximum": 5,
        "meaning": "0 is no demonstrated fit; 5 is demonstrated fit on the frozen evidence.",
    }
    assert (
        "at least 4/5 for relevance and locale parity"
        in shortlist["weighted_matrix"]["selection_rule"]
    )


def test_search_selection_shortlist_admits_only_control_pagefind_and_community_meilisearch() -> (
    None
):
    shortlist = _shortlist()
    candidates = {candidate["id"]: candidate for candidate in shortlist["candidates"]}

    assert set(candidates) == {"current-static-control", "pagefind-1.5.2", "meilisearch-ce-1.45.1"}
    assert candidates["current-static-control"]["entry_status"] == "admitted-control"
    assert "browser scorer is simpler" in candidates["current-static-control"]["known_constraint"]

    pagefind = candidates["pagefind-1.5.2"]
    assert pagefind["license"] == "MIT"
    assert pagefind["version"] == "1.5.2"
    assert pagefind["entry_status"] == "admitted-to-prototype"
    assert any("pagefind.app/docs/multilingual" in source for source in pagefind["sources"])
    assert any("Pagefind default UI" in condition for condition in pagefind["prototype_conditions"])

    meilisearch = candidates["meilisearch-ce-1.45.1"]
    assert meilisearch["license"] == "MIT (Community Edition only)"
    assert meilisearch["version"] == "1.45.1"
    assert meilisearch["entry_status"] == "admitted-to-prototype-with-isolation-condition"
    assert any(
        "browser never contacts the daemon" in condition
        for condition in meilisearch["prototype_conditions"]
    )
    assert any(
        "LAN/public listener" in condition for condition in meilisearch["prototype_conditions"]
    )
    assert "No additional candidate is admitted" in shortlist["additional_candidate_policy"]


def test_search_selection_shortlist_does_not_invent_benchmark_scores_or_a_selection() -> None:
    shortlist = _shortlist()

    assert "does not select, install, or replace a search engine" in shortlist["decision_boundary"]
    for candidate in shortlist["candidates"]:
        scorecard = candidate["scorecard"]
        assert scorecard["status"] == "unmeasured"
        assert scorecard["total"] is None
        assert all(score is None for score in scorecard["dimension_scores"].values())
