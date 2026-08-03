from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-api-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_01_pins_boundaries_and_does_not_add_a_route() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M7-01"
    assert contract["status"] == "accepted-architecture-only"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["implementation_boundary"] == {
        "routes_implemented_now": False,
        "worker_started_now": False,
        "network_calls_now": 0,
        "rule": "This is the frozen v1 API and request-state contract for later implementation. M7-01 adds neither a FastAPI router nor browser UI nor a model/controller invocation.",
    }
    assert "documentation-assistant" not in (ROOT / "app/main.py").read_text(encoding="utf-8")


def test_m7_01_freezes_versioned_same_origin_operations_and_limits() -> None:
    contract = _contract()

    assert contract["versioning"]["api_version"] == 1
    assert (
        contract["versioning"]["unsupported_version_error"] == "assistant_api_version_unsupported"
    )
    assert (
        "Every JSON response and every SSE event repeats api_version=1"
        in contract["versioning"]["compatibility_rule"]
    )
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert "same-origin BPM application routes only" in contract["transport"]["origin"]
    operations = contract["operations"]
    assert [
        (name, operation["method"], operation["path"]) for name, operation in operations.items()
    ] == [
        ("status", "GET", "/api/documentation-assistant/status"),
        ("ask", "POST", "/api/documentation-assistant/chat"),
        ("stream", "GET", "/api/documentation-assistant/chat/{request_id}/stream"),
        ("cancel", "POST", "/api/documentation-assistant/chat/{request_id}/cancel"),
        ("clear", "DELETE", "/api/documentation-assistant/conversation"),
        ("source", "GET", "/api/documentation-assistant/chat/{request_id}/sources/{source_id}"),
    ]
    assert contract["request_contract"]["limits"] == {
        "request_json_bytes_max": 49152,
        "question_unicode_characters_max": 4000,
        "active_requests_max": 1,
        "queued_requests_max": 1,
        "dialogue_turns_max": 16,
        "output_tokens_max": 512,
        "source_excerpt_unicode_characters_max": 1200,
    }
    assert contract["request_contract"]["web_modes"] == ["local_only", "request_web"]
    assert "zero network calls" in contract["request_contract"]["web_rule"]
    assert contract["operations"]["ask"]["response"][-1] == "time_preview"
    assert "whole seconds" in contract["operations"]["ask"]["rule"]


def test_m7_01_freezes_safe_state_sse_and_error_contracts() -> None:
    contract = _contract()

    machine = contract["request_state_machine"]
    assert machine["nonterminal"] == [
        "accepted",
        "scope_check",
        "evidence_check",
        "generating",
        "validating",
    ]
    assert machine["terminal"] == ["answer", "clarify", "abstain", "refuse", "cancelled", "error"]
    assert machine["transitions"]["validating"] == [
        "answer",
        "clarify",
        "abstain",
        "refuse",
        "error",
    ]
    assert all(machine["transitions"][state] == [] for state in machine["terminal"])
    rules = " ".join(machine["rules"])
    assert "never enter generation" in rules
    assert "Partial generation" in rules
    assert "state_epoch" in rules

    sse = contract["sse"]
    assert sse["event_types"] == ["accepted", "progress", "final", "cancelled", "error"]
    assert sse["required_fields"] == ["api_version", "request_id", "state", "state_epoch"]
    assert "no model tokens" in sse["progress_rule"]
    assert "approved opaque source IDs" in sse["final_rule"]
    assert "never expose raw exceptions" in contract["errors"]["rule"]
