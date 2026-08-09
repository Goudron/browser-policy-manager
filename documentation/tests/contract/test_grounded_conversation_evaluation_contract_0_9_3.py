from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-evaluation-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_07_keeps_its_scope_honest_and_reports_no_content_or_runtime_model_use() -> None:
    contract = _contract()

    assert (
        "does not start, benchmark, select or make a language-quality claim about Qwen3"
        in contract["scope"]["does_not_prove"]
    )
    assert contract["boundaries"] == {
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "cross_locale_retrieval_calls": 0,
        "chat_model_started": False,
        "fixture_conversation_content_retained": False,
        "report_location": "documentation/.cache/bpm093-m7-07/",
    }
    assert contract["progress"]["stream"] == "stdout"
    assert contract["progress"]["flush"] is True
