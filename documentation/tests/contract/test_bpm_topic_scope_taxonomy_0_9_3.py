from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-topic-scope-taxonomy-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_01_pins_scope_authority_and_has_no_runtime_implementation() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M8-01"
    assert contract["status"] == "accepted-architecture-only"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["implementation_boundary"] == {
        "scope_gate_implemented": False,
        "model_or_embedding_loaded": False,
        "retrieval_or_inference_called": False,
        "network_calls": 0,
        "rule": "This taxonomy defines deterministic inputs, stable reason families and precedence for M8-02. Prompt wording and a guard model are not scope authority.",
    }


def test_m8_01_covers_allowed_adjacent_refused_and_no_evidence_precedence() -> None:
    contract = _contract()

    assert set(contract["decision_states"]) == {
        "allow",
        "clarify",
        "refuse",
        "abstain_after_evidence",
    }
    assert {intent["id"] for intent in contract["allowed_intents"]} == {
        "bpm_product_workflows",
        "managed_firefox_policy",
        "bpm_administration_operation",
        "bpm_api_and_cis",
        "active_bpm_follow_up",
    }
    assert {intent["id"] for intent in contract["clarification_intents"]} == {
        "generic_firefox_ambiguity",
        "underspecified_reference",
        "active_chat_greeting",
        "policy_shaped_unknown_identifier",
    }
    assert {intent["id"] for intent in contract["refusal_intents"]} == {
        "general_non_bpm_assistance",
        "privileged_or_destructive_action",
        "control_override_or_prompt_extraction",
    }
    precedence = " ".join(contract["precedence"])
    assert "refuse even if the text also contains BPM or Firefox terms" in precedence
    assert "evidence policy—not taxonomy" in precedence
    assert "No prompt can promote" in precedence
    coverage = set(contract["mandatory_fixture_coverage"])
    assert any("code-switched" in item for item in coverage)
    assert any("policy/API/CIS" in item for item in coverage)
    assert any("active same-locale chat" in item for item in coverage)
