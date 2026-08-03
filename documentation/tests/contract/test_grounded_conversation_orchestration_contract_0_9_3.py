from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import conversation

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/grounded-conversation-orchestration-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m7_02_pins_all_pre_generation_boundaries_and_has_no_route() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M7-02"
    assert contract["status"] == "implemented-no-http-route"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["implementation_boundary"] == {
        "http_route": False,
        "browser_ui": False,
        "session_persistence": False,
        "scope_classifier": False,
        "e5_runtime_loader": False,
        "output_schema_parser": False,
        "external_provider": False,
    }
    source = (ROOT / "app/documentation/conversation.py").read_text(encoding="utf-8")
    assert "from fastapi" not in source
    assert "@router." not in source


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
