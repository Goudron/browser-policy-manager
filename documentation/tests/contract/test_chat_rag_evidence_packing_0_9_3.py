from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/chat-rag-evidence-packing-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_evidence_packing_contract_pins_retrieval_and_stops_before_generation() -> None:
    contract = _contract()
    retrieval = contract["retrieval_contract"]

    assert contract["contract_id"] == "bpm-chat-rag-evidence-packing-0.9.3"
    assert contract["backlog_item"] == "BPM093-M5-07"
    assert retrieval["sha256"] == hashlib.sha256((ROOT / retrieval["path"]).read_bytes()).hexdigest()
    assert retrieval["accepted_disposition"] == "answer-ready local evidence only"
    assert contract["entry_boundary"] == {
        "before_generation": True,
        "model_or_worker_calls": 0,
        "ordinary_search_calls": 0,
        "network_calls": 0,
        "external_evidence": "forbidden",
        "scope": "Caller must pass the deterministic scope-gate admission result; a non-admitted request abstains without packing or generation.",
    }


def test_evidence_packing_contract_freezes_exact_budget_order_and_confidence() -> None:
    contract = _contract()

    budget = contract["budget"]
    assert budget["maximum_context_tokens"] == 2048
    assert budget["maximum_evidence_chunks"] == 4
    assert "immutable exact tokenizer counter" in budget["counter"]
    assert "forbidden for a production request" in budget["counter"]
    assert budget["serialization"] == "Canonical JSON Lines with sorted keys and source text as data, not executable instructions."
    selection = contract["selection"]
    assert "topic_id, anchor_id_or_root, ordinal, then chunk_id" in selection["source_order"]
    assert selection["deduplication"] == "Retain at most one highest-ranked record per exact citation identity."
    assert selection["minimum_top_score"] == 0.45
    assert "No fixed score margin produces a terminal disposition" in selection["score_margin_policy"]
    assert "scope gate before retrieval" in selection["score_margin_policy"]
    assert "never render them as fake user probability" in selection["confidence"]


def test_evidence_packing_contract_requires_citations_and_terminal_safety() -> None:
    contract = _contract()

    terminal = contract["terminal_dispositions"]
    assert "nonempty, current, locale-private, citable" in terminal["answer"]
    assert set(terminal["abstain"]) == {
        "no_evidence",
        "scope_not_admitted",
        "stale_evidence",
        "contradictory_evidence",
        "low_confidence",
        "context_budget_exceeded",
        "duplicate_chunk_identity",
    }
    citation = contract["citation"]
    assert citation["required"] == ["citation_id", "published_url", "topic_id", "anchor_id_or_root", "source_kind"]
    assert citation["source_kind"] == "local"
    assert "no model-proposed or ordinary-search URL" in citation["rule"]
