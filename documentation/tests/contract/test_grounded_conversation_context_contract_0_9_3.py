from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation import conversation_context as context

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-context-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_03_freezes_bounded_context_topic_reset_and_clear_semantics() -> None:
    contract = _contract()

    assert contract["retention"] == {
        "storage": "process-memory only",
        "max_context_pairs": 8,
        "max_context_turns": 16,
        "max_resolved_entities": 8,
        "max_entity_characters": 120,
        "eviction": (
            "Keep the newest eight completed user-question/assistant-answer pairs as sixteen chronological entries. No model-generated summary is created or persisted."
        ),
    }
    assert context.MAX_CONTEXT_PAIRS == 8
    assert context.MAX_CONTEXT_TURNS == 16
    assert context.MAX_RESOLVED_ENTITIES == 8
    assert "prior citations never become citations" in contract["follow_up"]
    assert (
        "retain bounded dialogue but discard stale resolved entities before worker generation"
        in contract["topic_and_citation_reset"]
    )
    assert (
        "Every answer binds only citations from its fresh current EvidencePack"
        in contract["topic_and_citation_reset"]
    )
    assert "removes the exact session" in contract["clear"]
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_storage": False,
        "database": False,
        "disk": False,
        "telemetry": False,
        "cross_locale_context": False,
        "ordinary_search_calls": 0,
        "summary_model": False,
    }
