from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    ROOT / "documentation/config/grounded-conversation-answer-validation-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m13_06_requires_server_section_citation_binding_and_safe_downgrade() -> None:
    contract = _contract()

    resolution = contract["citation_resolution"]
    assert resolution["resolution_rate"] == 1.0
    rules = " ".join(resolution["rules"])
    assert "unique and exactly resolves" in rules
    assert "relative /help/{locale}/ URL" in rules
    assert "No user/model URL" in rules
    fallback = contract["fallback"]
    assert "unknown/duplicate citation" in fallback["invalid_output"]
    assert "excessive contiguous evidence quotation" in fallback["invalid_output"]
    assert "without showing evidence text or citations" in fallback["invalid_output"]
    assert (
        fallback["terminal"]
        == "No invalid generated text or raw evidence excerpt is returned as a confident BPM answer."
    )
    assert contract["boundaries"] == {
        "http_route": False,
        "browser_renderer": False,
        "ordinary_search_calls": 0,
        "network_calls": 0,
        "model_url_trust": False,
        "raw_model_output_exposed": False,
    }
