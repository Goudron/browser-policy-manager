from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import conversation_context, conversation_stream

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-conversation-retention-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m8_06_pins_prior_private_boundaries_and_freezes_memory_retention() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M8-06"
    assert contract["status"] == "implemented-memory-only-no-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    retention = contract["retention"]
    assert retention["storage"] == "process-memory only"
    assert retention["persistence"] is False
    assert retention["telemetry"] is False
    assert retention["content_logging"] is False
    assert retention["idle_session_ttl_seconds"] == conversation_context.IDLE_SESSION_TTL_SECONDS
    assert retention["absolute_session_ttl_seconds"] == conversation_context.ABSOLUTE_SESSION_TTL_SECONDS
    assert retention["context_pairs_max"] == conversation_context.MAX_CONTEXT_PAIRS
    assert retention["context_turns_max"] == conversation_context.MAX_CONTEXT_TURNS


def test_m8_06_expires_private_stream_state_and_keeps_diagnostics_content_free() -> None:
    contract = _contract()

    stream = contract["completed_stream"]
    assert stream["completed_record_retention_seconds"] == (
        conversation_stream.COMPLETED_RECORD_RETENTION_SECONDS
    )
    assert stream["completed_records_max"] == conversation_stream.MAX_COMPLETED_REQUESTS
    assert "dropped" in stream["request_content"]
    assert "opaque" in stream["source_handles"]
    assert "Prompts" in contract["diagnostics"]
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_storage": False,
        "database": False,
        "disk": False,
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "personalization": False,
        "cross_locale_context": False,
    }
