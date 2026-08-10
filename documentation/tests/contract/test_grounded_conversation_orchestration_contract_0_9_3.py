from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation import conversation

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-orchestration-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_02_freezes_pipeline_locale_evidence_web_and_citation_guards() -> None:
    contract = _contract()

    assert contract["pipeline"] == [
        "validate_request",
        "scope_gate",
        "optional_web_consent_boundary",
        "same_locale_e5_encode",
        "exact_locale_retrieval",
        "evidence_pack",
        "local_worker",
        "parse_and_support_check",
        "server_citation_binding",
    ]
    assert "fails closed before encoding, retrieval, worker, or web action" in contract["scope"]
    assert "cross-locale merge, retry, and ordinary search are forbidden" in contract["locale"]
    assert "does not invoke generation" in contract["evidence"]
    assert "no raw model text is returned" in contract["generation"]
    assert "unique citation IDs" in contract["citation"]
    assert "without encoding, retrieval, worker, or provider calls" in contract["web"]
    assert "neither imported, called, ranked, nor changed" in contract["ordinary_search"]
    assert conversation.MAX_REQUEST_BYTES == 49_152
    assert conversation.MAX_RETRIEVAL_CANDIDATES == 5
