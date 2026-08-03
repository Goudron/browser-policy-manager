from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import topic_scope

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-topic-scope-gate-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_02_pins_taxonomy_and_implements_only_pre_generation_scope_admission() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M8-02"
    assert contract["status"] == "implemented-no-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "ordinary_search_import": False,
        "network_calls": 0,
        "retrieval_before_decision": False,
        "llm_before_decision": False,
        "cross_locale_retrieval": False,
        "prompt_only_scope_authority": False,
    }
    source = (ROOT / "app/documentation/topic_scope.py").read_text(encoding="utf-8")
    assert "ordinary_search" not in source
    assert "from fastapi" not in source
    assert topic_scope._POLICY_SHAPED_IDENTIFIER.pattern


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
