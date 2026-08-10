from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-topic-scope-gate-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_02_freezes_alias_matrix_similarity_thresholds_and_quality_floors() -> None:
    contract = _contract()

    assert set(contract["lexical_aliases"]) == {"allowed", "clarify", "refuse"}
    for group in contract["lexical_aliases"].values():
        assert set(group) == set(contract["locales"])
        assert all(values for values in group.values())
    assert contract["semantic_thresholds"] == {"allow": 0.82, "clarify": 0.5}
    assert contract["decision_order"] == [
        "deterministic_refuse",
        "policy_identifier_allow",
        "deterministic_bpm_alias_allow",
        "bounded_context_follow_up_or_clarify",
        "adjacent_clarify",
        "compact_semantic_allow_or_clarify",
        "refuse",
    ]
    assert contract["acceptance_floors"] == {
        "in_scope_allow_rate_min": 1.0,
        "adjacent_clarify_rate_min": 1.0,
        "off_topic_refusal_rate_min": 1.0,
        "off_topic_downstream_calls_max": 0,
    }
    assert "six fixed normalized intent centroids" in contract["similarity"]["adapter"]
    assert "fails closed" in contract["similarity"]["failure"]
