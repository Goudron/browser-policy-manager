from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-topic-scope-taxonomy-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


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
