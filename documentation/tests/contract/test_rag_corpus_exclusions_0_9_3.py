from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "documentation/tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("rag_chunks", TOOLS / "extract_rag_chunks_0_9_3.py")
assert SPEC and SPEC.loader
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)
POLICY = ROOT / "documentation/config/rag-corpus-exclusions-0.9.3.json"
pytestmark = pytest.mark.docs_contract


def _chunk() -> dict:
    return {
        "chunk_id": "ragc-v1:en:topic:root:0",
        "topic_id": "topic",
        "locale": "en",
        "source_dita_path": "documentation/src/dita/en/user/topic.dita",
        "source_sha256": "a" * 64,
        "manifest_sha256": "b" * 64,
        "provenance_class": "published_reviewed_dita",
        "publication_state": "published",
        "published_url": "/help/en/user/topic.html",
        "text": "excluded source text",
    }


def test_corpus_exclusions_fail_closed_and_diagnostics_do_not_leak_text() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["backlog_item"] == "BPM093-M5-02"
    extractor.validate_retrieval_chunk(_chunk())
    for path, category in (
        ("documentation/runbooks/private.md", "excluded-path"),
        ("documentation/reports/run.json", "excluded-path"),
        ("/tmp/chat.log", "unapproved-source"),
    ):
        rejected = deepcopy(_chunk())
        rejected["source_dita_path"] = path
        with pytest.raises(extractor.ChunkExtractionError) as error:
            extractor.validate_retrieval_chunk(rejected)
        diagnostic = json.loads(str(error.value))
        assert diagnostic["rejection_category"] == category
        assert set(diagnostic) <= set(policy["diagnostics"]["allowed_fields"])
        assert "excluded source text" not in str(error.value)
    blocked = deepcopy(_chunk())
    blocked["provenance_class"] = "blocked"
    with pytest.raises(extractor.ChunkExtractionError, match="blocked-provenance"):
        extractor.validate_retrieval_chunk(blocked)
