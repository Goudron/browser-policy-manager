from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation import conversation_stream

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/bpm-conversation-retention-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


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
