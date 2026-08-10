from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/chat-rag-embedding-selection-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_chat_rag_embedding_selection_is_separate_from_ordinary_search_and_cross_locale_retrieval() -> (
    None
):
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["backlog_item"] == "BPM093-M5-03B"
    assert contract["supported_locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["scope"]["entrypoint"] == "An explicitly enabled user chat only."
    assert "not called, changed, ranked against" in contract["scope"]["ordinary_search"]
    assert (
        "cross-locale prose retrieval and fallback are forbidden"
        in contract["scope"]["retrieval_mode"]
    )
    assert (
        "need not be more relevant than ordinary search"
        in contract["scope"]["not_a_quality_substitute"]
    )


def test_chat_rag_embedding_selection_requires_citable_local_evidence_or_safe_abstention() -> None:
    contract = _contract()

    assert "exact active locale" in contract["local_evidence"]["allowed"]
    assert set(contract["local_evidence"]["forbidden"]) >= {
        "ordinary search results",
        "cross-locale prose",
        "generated answers",
        "external pages",
    }
    assert "never citations" in contract["local_evidence"]["citation"]
    boundaries = contract["hard_boundaries"]
    assert boundaries["same_locale_only"] is True
    assert boundaries["citation_target_must_resolve"] is True
    assert boundaries["missing_evidence_disposition"] == "abstain_or_clarify"
    assert boundaries["unsupported_factual_answer"] == "forbidden"
    assert boundaries["ordinary_search_dependency"] == "forbidden"
    assert boundaries["cross_locale_fallback"] == "forbidden"


def test_chat_rag_embedding_selection_pins_candidates_and_keeps_web_opt_in_out_of_local_knowledge() -> (
    None
):
    contract = _contract()

    artifacts = contract["candidate_artifact"]
    assert artifacts["minimum_count"] == 2
    assert "artifact_sha256" in artifacts["must_pin"]
    assert "changed swap counter invalidates selection" in artifacts["resource_measurement"]
    assert "not a comparison to ordinary-search relevance" in artifacts["selection_order"]

    external = contract["optional_external_evidence"]
    assert external["default"] == "disabled"
    assert "explicit user opt-in" in external["activation"]
    assert (
        "never enters local chunks, embeddings, indexes, model training" in external["persistence"]
    )
    assert external["citation"] == "External claims require their own labelled external citation."
