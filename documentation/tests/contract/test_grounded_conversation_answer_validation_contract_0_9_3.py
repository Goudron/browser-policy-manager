from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.documentation import answer_validation as validator

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = (
    ROOT / "documentation/config/grounded-conversation-answer-validation-contract-0.9.3.json"
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_m13_06_pins_pipeline_and_freezes_strict_grounded_section_response_shape() -> None:
    contract = _contract()

    assert contract["backlog_item"] == "BPM093-M13-06"
    assert contract["status"] == "implemented-grounded-section-composition"
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]
    assert contract["generation_payload"]["fields"] == ["instruction", "user_question"]
    assert "exactly one JSON object" in contract["generation_payload"]["instruction_rule"]
    assert "own words" in contract["generation_payload"]["instruction_rule"]
    assert "without a word or paragraph target" in contract["generation_payload"]["instruction_rule"]
    rewrite = contract["excessive_quote_rewrite"]
    assert "one private local rewrite" in rewrite
    assert "never the EvidencePack or dialogue" in rewrite
    assert "validated again against the original EvidencePack" in rewrite
    assert contract["response_schema"] == {
        "exact_fields": ["disposition", "sections"],
        "section_exact_fields": ["text", "citation_ids"],
        "dispositions": ["answer", "clarify", "abstain", "refuse"],
        "model_response_bytes_max": 16384,
        "answer_unicode_characters_max": 4000,
        "sections_max": 6,
        "section_unicode_characters_max": 1200,
        "extractive_span_characters_max": 95,
        "plain_text": "Control characters and markup-like tags are rejected; model-created links never become source links.",
    }
    assert validator.MAX_MODEL_RESPONSE_BYTES == 16_384
    assert validator.MAX_ANSWER_CHARACTERS == 4_000
    assert validator.MAX_ANSWER_SECTIONS == 6
    assert validator.MAX_SECTION_CHARACTERS == 1_200
    assert validator.MAX_EXTRACTIVE_SPAN_CHARACTERS == 96


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
