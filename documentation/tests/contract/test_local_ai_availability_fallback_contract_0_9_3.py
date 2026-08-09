from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/local-ai-availability-fallback-contract-0.9.3.json"
LOCALES = ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
STATE_IDS = [
    "disabled",
    "not-installed",
    "downloading",
    "indexing",
    "loading",
    "ready",
    "busy",
    "cancelled",
    "degraded",
    "incompatible",
    "crashed",
    "web-offline",
]

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _states(contract: dict) -> dict[str, dict]:
    return {state["id"]: state for state in contract["states"]}


def test_availability_contract_is_architecture_only_and_has_exact_state_set() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-local-ai-availability-fallback-0.9.3"
    assert contract["backlog_item"] == "BPM093-M2-06"
    assert contract["target_bpm_version"] == "0.9.3"
    assert contract["status"] == "accepted-architecture-only"
    assert contract["locales"] == LOCALES
    assert contract["implementation_boundary"]["implemented_now"] is False
    assert "not routes implemented" in contract["implementation_boundary"]["rule"]
    assert list(_states(contract)) == STATE_IDS


def test_readiness_is_independent_truthful_and_preserves_lexical_search() -> None:
    contract = _contract()
    readiness = contract["independent_readiness"]
    states = _states(contract)

    assert "only core BPM readiness" in readiness["core_bpm_health"]
    assert "must remain true" in readiness["core_bpm_health"]
    assert "True only" in readiness["assistant_ready"]
    assert "Always true" in readiness["lexical_search_ready"]
    assert "never makes assistant_ready true" in readiness["partial_artifact_rule"]
    assert states["ready"]["assistant_ready"] is True
    assert states["web-offline"]["assistant_ready"] is True
    for state_id in set(STATE_IDS) - {"ready", "web-offline"}:
        assert states[state_id]["assistant_ready"] is False
    assert "partial artifacts" in states["indexing"]["ui_behavior"]
    assert "never silently select a different model/index" in states["incompatible"]["ui_behavior"]


def test_every_state_has_localized_ui_and_stable_api_contract() -> None:
    contract = _contract()
    localization = contract["localization"]
    status = contract["status_api"]
    states = _states(contract)

    assert localization["fallback_policy"].startswith("fail closed")
    assert "English fallback is forbidden" in localization["fallback_policy"]
    assert "Human reviewers" in localization["review_required_before_release"]
    patterns = localization["required_key_pattern"]
    assert len(patterns) == 5
    expanded_keys = {
        pattern.format(state=state_id)
        for pattern in patterns
        for state_id in states
        for _locale in LOCALES
    }
    assert len(expanded_keys) == len(STATE_IDS) * 5
    assert status["required_fields"] == [
        "state",
        "assistant_ready",
        "lexical_search_ready",
        "locale",
        "message_key",
        "action_key",
        "reason_code",
        "state_epoch",
    ]
    status_rules = " ".join(status["rules"])
    assert "visible prose may not fall back to English" in status_rules
    assert "state_epoch changes" in status_rules
    assert "never claims" in status_rules
    for state in states.values():
        assert state["chat_http_status"] in {200, 202, 409, 503}
        assert state["reason_code"].startswith("assistant_")
        assert state["allowed_actions"]
        assert state["ui_behavior"]
        assert state["api_behavior"]
        assert state["fallback"]


def test_busy_cancelled_degraded_and_web_offline_have_safe_distinct_behavior() -> None:
    states = _states(_contract())

    assert states["busy"]["chat_http_status"] == 202
    assert "429 when the queue is full" in states["busy"]["api_behavior"]
    assert "unbounded retries" in states["busy"]["ui_behavior"]
    assert states["cancelled"]["kind"] == "terminal_operation_outcome"
    assert "terminal cancellation event" in states["cancelled"]["api_behavior"]
    assert states["degraded"]["assistant_ready"] is False
    assert (
        "grounding, security, privacy, or resource guard is degraded"
        in states["degraded"]["ui_behavior"]
    )
    assert states["web-offline"]["assistant_ready"] is True
    assert "local-only" in states["web-offline"]["ui_behavior"]
    assert "no further provider call" in states["web-offline"]["api_behavior"]


def test_transition_guards_reject_partial_artifacts_and_silent_work() -> None:
    contract = _contract()
    transitions = contract["transitions"]

    assert set(transitions) == set(STATE_IDS)
    for source, targets in transitions.items():
        assert targets, source
        assert set(targets) <= set(STATE_IDS)
    assert transitions["downloading"] == ["not-installed", "indexing", "incompatible", "crashed"]
    assert "ready" in transitions["loading"]
    assert "web-offline" in transitions["ready"]
    guards = " ".join(contract["transition_guards"])
    for requirement in (
        "Only explicit user consent",
        "never ready",
        "partial artifacts are quarantined",
        "no-listener",
        "may not be used to conceal a core local artifact",
    ):
        assert requirement in guards
    background = contract["background_operations"]
    assert background["allowed_on_ready"] == ["indexing", "verified_artifact_download"]
    assert "never serve requests until complete validation" in background["rule"]
    non_goals = " ".join(contract["non_goals"])
    assert "silent network access" in non_goals
    assert "lexical-search dependency on AI" in non_goals
