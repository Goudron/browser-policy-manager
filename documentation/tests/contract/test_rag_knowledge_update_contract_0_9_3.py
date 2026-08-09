from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/rag-knowledge-and-update-contract-0.9.3.json"
LOCALES = ["en", "ru", "de", "zh-CN", "fr", "es-ES"]

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_rag_knowledge_contract_is_architecture_only_and_preserves_current_runtime_boundary() -> (
    None
):
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-rag-knowledge-update-0.9.3"
    assert contract["backlog_item"] == "BPM093-M2-04"
    assert contract["target_bpm_version"] == "0.9.3"
    assert contract["status"] == "accepted-architecture-only"
    assert contract["locales"] == LOCALES
    assert contract["implementation_boundary"]["implemented_now"] is False
    assert (
        "remains the active runtime contract"
        in contract["implementation_boundary"]["current_lexical_contract"]
    )
    chat_boundary = contract["chat_retrieval_boundary"]
    assert "explicitly enabled user chat" in chat_boundary["entrypoint"]
    assert "independent" in chat_boundary["ordinary_search"]
    assert "cross-locale prose retrieval and fallback are rejected" in chat_boundary["locale_rule"]
    assert "need not outrank ordinary search" in chat_boundary["quality_rule"]

    external = contract["optional_external_evidence"]
    assert external["default"] == "disabled"
    assert "explicit user opt-in" in external["activation"]
    assert (
        "never enter local chunks, embeddings, indexes, model training"
        in external["local_corpus_boundary"]
    )
    assert "labelled external citation" in external["citation_rule"]


def test_rag_knowledge_contract_allows_only_published_reviewed_locale_bound_sources() -> None:
    contract = _contract()
    source_eligibility = contract["source_eligibility"]

    assert {entry["kind"] for entry in source_eligibility["eligible"]} == {
        "published_reviewed_dita",
        "published_approved_generated_dita",
        "language_neutral_technical_identifier",
    }
    excluded = " ".join(source_eligibility["excluded"])
    for forbidden in (
        "unpublished",
        "restricted",
        "cross-locale",
        "generated answers",
        "chat transcripts",
        "runtime state",
        "web content",
    ):
        assert forbidden in excluded
    assert "published locale URL" in source_eligibility["citation_rule"]
    assert "never a citation source" in source_eligibility["citation_rule"]


def test_rag_chunk_schema_has_stable_ids_and_complete_provenance_metadata() -> None:
    chunking = _contract()["chunking"]

    assert chunking["chunk_schema_version"] == "rag-chunk-v1"
    assert (
        chunking["stable_id"]["format"]
        == "ragc-v1:{locale}:{topic_id}:{anchor_id_or_root}:{ordinal}"
    )
    assert "neither content hashes nor model identifiers" in chunking["stable_id"]["rule"]
    assert set(chunking["required_metadata"]) >= {
        "chunk_id",
        "locale",
        "topic_id",
        "anchor_id_or_root",
        "published_url",
        "source_revision",
        "source_sha256",
        "manifest_sha256",
        "documentation_version",
        "bpm_version",
        "provenance_class",
        "text_normalization_revision",
    }
    boundaries = " ".join(chunking["boundaries"])
    assert "exactly one locale" in boundaries
    assert "do not mix text" in boundaries
    assert "deterministic" in boundaries


def test_rag_embedding_compatibility_and_rebuilds_fail_closed_and_are_complete() -> None:
    contract = _contract()
    compatibility = contract["embedding_compatibility"]

    assert compatibility["selection_status"] == "No embedding model is selected by this task."
    assert set(compatibility["required_compatibility_key"]) >= {
        "chunk_schema_version",
        "text_normalization_revision",
        "embedding_model_id",
        "embedding_model_revision_or_checksum",
        "embedding_dimension",
        "vector_normalization",
        "distance_metric",
        "locale",
        "source_manifest_sha256",
    }
    rules = " ".join(compatibility["rules"])
    assert "mixed keys are rejected" in rules
    assert "retain lexical search" in rules
    assert "independent of ordinary lexical search" in rules
    assert "resolvable citation" in rules

    rebuild = contract["rebuild_contract"]
    assert "atomically promoting" in rebuild["promotion"]
    trigger_changes = {trigger["change"] for trigger in rebuild["triggers"]}
    assert any("published source text" in change for change in trigger_changes)
    assert any("source provenance" in change for change in trigger_changes)
    assert any("chunk schema" in change for change in trigger_changes)
    assert any("embedding compatibility-key" in change for change in trigger_changes)
    assert any("chat model" in change for change in trigger_changes)


def test_rag_contract_separates_ordinary_reindexing_from_weight_training_and_artifacts() -> None:
    contract = _contract()
    training = contract["reindexing_and_training"]
    artifacts = contract["artifact_boundary"]

    assert "does not change base-model weights" in training["ordinary_product_update"]
    assert "out of scope for BPM 0.9.3" in training["training_boundary"]
    assert len(training["separate_approval_required_for_future_training"]) == 4
    assert "embedding vectors" in " ".join(artifacts["generated_ignored_artifacts"])
    assert "never hand-edited or committed" in " ".join(artifacts["rules"])
    assert artifacts["committed_source"][0].startswith("reviewed eligible DITA")
