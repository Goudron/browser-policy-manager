from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/chat-rag-retrieval-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_retrieval_contract_pins_the_active_e5_exact_generation() -> None:
    contract = _contract()
    generation = contract["generation_contract"]

    assert contract["contract_id"] == "bpm-chat-rag-same-locale-retrieval-0.9.3"
    assert contract["backlog_item"] == "BPM093-M5-06"
    assert contract["status"] == "accepted-runtime-retrieval-contract"
    assert generation["sha256"] == hashlib.sha256((ROOT / generation["path"]).read_bytes()).hexdigest()
    assert generation["active_pointer"] == "active-generation.json"
    assert generation["storage_backend"] == "normalized-exact-f32-matrix-v1"
    assert contract["selected_embedding"] == {
        "model_id": "intfloat/multilingual-e5-base",
        "artifact_sha256": "f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703",
        "dimension": 768,
        "query_requirement": "The caller supplies one finite L2-normalized E5 query vector. Encoding, model loading, and answer generation are outside this task.",
    }


def test_retrieval_contract_is_same_locale_citable_and_independent_from_m4() -> None:
    contract = _contract()

    assert contract["entry_boundary"]["network_calls_after_install"] == 0
    assert "neither imported nor called" in contract["entry_boundary"]["ordinary_search"]
    assert contract["entry_boundary"]["external_evidence"] == "disabled and absent from this retriever"
    filtering = contract["locale_and_filtering"]
    assert filtering["supported_locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert "Cross-locale merge, fallback, and retry are forbidden" in filtering["locale_rule"]
    assert filtering["maximum_candidates"] == 5
    assert "stable chunk_id ascending" in filtering["ranking"]
    evidence = contract["evidence_and_citation"]
    assert set(evidence["required_chunk_fields"]) >= {"bpm_version", "documentation_version", "published_url", "text"}
    assert "source_kind=local" in evidence["citation"]
    assert "fragment-free /help/{locale}/ topic URL" in evidence["citation"]
    assert "never falls back to ordinary search" in evidence["no_evidence"]


def test_retrieval_contract_fails_closed_on_unverified_or_stale_artifacts() -> None:
    contract = _contract()

    integrity = contract["integrity_and_recovery"]
    assert "safe active pointer and generation identifier" in integrity["validate_before_scan"]
    assert "matrix byte count/hash/shape/finiteness/L2 normalization" in integrity["validate_before_scan"]
    assert "metadata byte hash/shape/field set/canonical chunk order" in integrity["validate_before_scan"]
    assert "retrieval unavailable" in integrity["failure"]
    assert "never local paths" in integrity["diagnostics"]
