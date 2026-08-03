from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import conversation_stream as stream

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-streaming-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_05_pins_streaming_to_the_existing_safe_pipeline_without_a_route() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M7-05"
    assert contract["status"] == "implemented-memory-only-no-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_ui": False,
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "raw_model_token_streaming": False,
        "persistence": False,
        "telemetry": False,
    }
    source = (ROOT / "app/documentation/conversation_stream.py").read_text(encoding="utf-8")
    assert "from fastapi" not in source
    assert "@router." not in source


def test_m7_05_freezes_safe_events_serialization_cancellation_and_backpressure() -> None:
    contract = _contract()

    assert contract["lifecycle"]["event_types"] == [
        "accepted",
        "progress",
        "final",
        "cancelled",
        "error",
    ]
    assert contract["lifecycle"]["progress_states"] == [
        "scope_check",
        "evidence_check",
        "generating",
        "validating",
    ]
    assert contract["bounds"]["active_requests_max"] == stream.MAX_ACTIVE_REQUESTS == 1
    assert contract["bounds"]["queued_requests_max"] == stream.MAX_QUEUED_REQUESTS == 1
    assert contract["bounds"]["event_buffer_max"] == stream.MAX_EVENT_BUFFER == 8
    assert contract["bounds"]["completed_request_records_max"] == stream.MAX_COMPLETED_REQUESTS == 4
    assert contract["bounds"]["request_timeout_seconds"] == stream.REQUEST_TIMEOUT_SECONDS
    assert (
        "exactly one incomplete terminal cancellation event" in contract["bounds"]["cancellation"]
    )
    assert "never block inference" in contract["bounds"]["backpressure"]
    assert "never enter the event stream" in contract["lifecycle"]["rule"]
    assert "never reveals the evidence citation ID" in contract["source_handles"]
