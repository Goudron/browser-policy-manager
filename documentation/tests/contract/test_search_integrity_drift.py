from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
INTEGRITY_CONTRACT = DOCUMENTATION_ROOT / "config/search-integrity-drift-0.9.0.json"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(INTEGRITY_CONTRACT.read_text(encoding="utf-8"))


def test_search_integrity_contract_is_static_localized_and_non_ai() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-doc-search-integrity-drift-0.9.0"
    assert contract["backlog_item"] == "BPM090-M10-08"
    assert contract["target_bpm_version"] == "0.9.0"
    assert contract["status"] == "accepted"
    assert contract["search_mode"] == "deterministic-local-static"
    assert contract["non_ai_boundary"] == "no-ai-no-rag-no-embeddings-no-generative-answers"


def test_search_integrity_contract_defines_actionable_release_gates() -> None:
    contract = _contract()

    assert set(contract["check_categories"]) == {
        "missing_topics",
        "stale_anchors",
        "duplicate_document_ids",
        "wrong_locale",
        "wrong_url_or_output",
        "broken_snippet_sources",
        "firefox_policy_inventory_gaps",
        "cis_inventory_gaps",
        "api_inventory_gaps",
    }
    assert contract["report_contract"] == {
        "status_must_be": "pass",
        "failure_count_must_be": 0,
        "report_is_recomputed_during_manifest_and_package_validation": True,
        "actionable_ids_required": True,
    }
    assert contract["snippet_integrity"]["source_fields"] == ["shortdesc", "body", "title"]
    assert contract["snippet_integrity"]["max_characters"] == 260
    assert contract["snippet_integrity"]["plain_text_only"] is True
    assert contract["snippet_integrity"]["control_characters_forbidden"] is True
    assert contract["snippet_integrity"]["html_snippets_forbidden"] is True
    assert contract["inventory_gap_integrity"]["extra_targets_forbidden"] is True


def test_search_integrity_report_exposes_actionable_drift_ids() -> None:
    contract = _contract()
    topics = {
        "topic-a": {
            "output": {"en": "en/user/topic-a.html"},
            "anchors": {"a-topic-a": {"title": {"en": "Topic A"}}},
        },
        "topic-b": {
            "output": {"en": "en/user/topic-b.html"},
            "anchors": {"a-topic-b": {"title": {"en": "Topic B"}}},
        },
    }
    documents = [
        {
            "document_id": "en:topic-a",
            "locale": "en",
            "topic_id": "topic-a",
            "url": "/help/en/user/topic-a.html",
            "source": {"output_path": "en/user/topic-a.html"},
            "searchable": {
                "title": "Topic A",
                "shortdesc": "",
                "headings": [],
                "body": "Valid body",
                "keywords": [],
                "identifiers": [],
                "aliases": [],
            },
        },
        {
            "document_id": "en:topic-a",
            "locale": "ru",
            "topic_id": "topic-a",
            "url": "/help/ru/user/topic-a.html",
            "source": {"output_path": "ru/user/topic-a.html"},
            "searchable": {
                "title": "",
                "shortdesc": "",
                "headings": [],
                "body": "Broken\u0001 body",
                "keywords": [],
                "identifiers": [],
                "aliases": [],
            },
        },
        {
            "document_id": "en:unknown-topic",
            "locale": "en",
            "topic_id": "unknown-topic",
            "url": "/help/en/user/unknown-topic.html",
            "source": {"output_path": "en/user/unknown-topic.html"},
            "searchable": {
                "title": "",
                "shortdesc": "",
                "headings": [],
                "body": "",
                "keywords": [],
                "identifiers": [],
                "aliases": [],
            },
        },
    ]
    target_map = {
        "targets": {
            "policy:MissingPolicy": {
                "kind": "policy",
                "source_id": "MissingPolicy",
                "topic_id": "topic-a",
                "anchor_id": "a-missing-anchor",
            },
            "cis:missing": {
                "kind": "cis",
                "source_id": "missing",
                "topic_id": "missing-topic",
                "anchor_id": "a-missing-topic",
            },
        },
    }

    report = build_docs._search_integrity_report("en", documents, topics, target_map, contract)

    assert report["status"] == "fail"
    assert report["failure_count"] > 0
    assert report["document_integrity"]["missing_topic_ids"] == ["topic-b"]
    assert report["document_integrity"]["extra_topic_ids"] == ["unknown-topic"]
    assert report["document_integrity"]["duplicate_document_ids"] == ["en:topic-a"]
    assert report["document_integrity"]["wrong_locale_document_ids"] == ["en:topic-a"]
    assert report["document_integrity"]["wrong_url_document_ids"] == ["en:topic-a"]
    assert report["document_integrity"]["wrong_output_document_ids"] == ["en:topic-a"]
    assert report["anchor_integrity"]["stale_target_anchors"] == [
        {
            "target_id": "policy:MissingPolicy",
            "topic_id": "topic-a",
            "anchor_id": "a-missing-anchor",
        }
    ]
    assert report["anchor_integrity"]["target_topic_mismatches"] == ["cis:missing"]
    assert report["snippet_integrity"]["broken_snippet_document_ids"] == ["en:unknown-topic"]
    assert report["snippet_integrity"]["control_character_document_ids"] == ["en:topic-a"]
    assert (
        "MissingPolicy" in report["inventory_gap_integrity"]["firefox_policy"]["extra_source_ids"]
    )
    assert "missing" in report["inventory_gap_integrity"]["cis"]["extra_source_ids"]
