from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation import conversation_stream as stream

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-streaming-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


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
