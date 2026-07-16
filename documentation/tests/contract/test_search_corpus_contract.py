from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
SEARCH_CONTRACT = DOCUMENTATION_ROOT / "config/search-corpus-and-results-0.9.0.json"
MODULE_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(SEARCH_CONTRACT.read_text(encoding="utf-8"))


def test_search_contract_defines_deterministic_non_ai_boundary_and_locale_matrix() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["contract_id"] == "bpm-doc-search-corpus-results-0.9.0"
    assert contract["backlog_item"] == "BPM090-M10-01"
    assert contract["target_bpm_version"] == "0.9.0"
    assert contract["status"] == "accepted"
    assert contract["search_mode"] == "deterministic-local-static"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["locales"] == list(build_docs.LOCALES)

    boundary = contract["non_ai_boundary"]
    assert boundary["mode"] == "no-ai-no-rag-no-embeddings-no-generative-answers"
    assert set(boundary["forbidden"]) >= {
        "RAG",
        "embeddings",
        "semantic vector search",
        "generative answers",
        "runtime network search services",
    }
    assert all("AI" not in allowed for allowed in boundary["allowed"])


def test_search_contract_identifies_corpus_fields_sources_and_exclusions() -> None:
    contract = _contract()
    corpus = contract["corpus"]

    source_authority = set(corpus["source_authority"])
    assert "documentation/src/dita/{locale}/{user,firefox,cis,api,admin}/*.dita" in source_authority
    assert "documentation/src/generated/firefox/firefox-policy-skeletons-0.9.0.json" in source_authority
    assert "documentation/src/generated/cis/cis-recommendation-skeletons-0.9.0.json" in source_authority
    assert "docs/architecture/api-documentation-inventory-0.9.0.md" in source_authority

    searchable_fields = {field["field"] for field in corpus["searchable_fields"]}
    assert searchable_fields == {
        "title",
        "shortdesc",
        "headings",
        "body",
        "keywords",
        "identifiers",
        "aliases",
    }
    assert set(corpus["identifier_fields"]) >= {
        "topic_id",
        "anchor_id",
        "guide_id",
        "policy_id",
        "known_preference_id",
        "cis_recommendation_id",
        "api_operation_id",
        "capability_id",
        "firefox_channel",
        "bpm_version",
    }

    exclusions = {entry["kind"]: entry["rule"] for entry in corpus["exclusions"]}
    assert "hidden_or_unpublished" in exclusions
    assert "wrong_locale_content" in exclusions
    assert "restricted_source_expression" in exclusions
    assert "provenance_only_cis" in exclusions
    assert "runtime_private_state" in exclusions
    assert "manifest.topics" in exclusions["hidden_or_unpublished"]


def test_search_document_and_result_schemas_cover_required_metadata_and_safety() -> None:
    contract = _contract()
    document_schema = contract["document_schema"]
    result_schema = contract["result_schema"]

    assert set(document_schema["required_fields"]) >= {
        "document_id",
        "locale",
        "guide_id",
        "topic_id",
        "topic_kind",
        "url",
        "source",
        "searchable",
        "facets",
        "versions",
    }
    assert set(document_schema["source"]["required_fields"]) == {
        "topic_id",
        "anchor_id",
        "dita_key",
        "source_slug",
        "output_path",
    }
    assert set(document_schema["searchable"]["required_fields"]) == {
        "title",
        "shortdesc",
        "headings",
        "body",
        "keywords",
        "identifiers",
        "aliases",
    }
    assert document_schema["searchable"]["plain_text_only"] is True
    assert document_schema["searchable"]["html_allowed"] is False
    assert set(document_schema["facets"]["required_fields"]) >= {
        "locale",
        "guide_id",
        "topic_kind",
        "firefox_channel",
        "policy_category",
        "cis_level",
        "cis_control_state",
        "api_area",
        "bpm_version",
    }

    assert set(result_schema["required_fields"]) >= {
        "result_id",
        "document_id",
        "locale",
        "guide_id",
        "topic_id",
        "anchor_id",
        "title",
        "url",
        "snippet",
        "score",
        "score_breakdown",
        "matched_fields",
        "identifiers",
        "facets",
    }
    assert result_schema["snippet"] == {
        "plain_text_only": True,
        "max_characters": 260,
        "must_escape_before_dom_insertion": True,
    }
    assert result_schema["result_url"]["source"] == "manifest topic output plus optional anchor"
    assert result_schema["result_url"]["must_start_with"] == "/help/{locale}/"
    assert "bounded_typo" in result_schema["score_breakdown"]["required_fields"]
    assert result_schema["empty_result"]["must_not_call_network"] is True
    assert result_schema["empty_result"]["must_not_offer_ai_answer"] is True


def test_search_facet_and_integrity_contracts_are_release_gate_ready() -> None:
    contract = _contract()

    facets = contract["facet_contract"]
    assert facets["locale"] == list(build_docs.LOCALES)
    assert facets["guide_id"] == [
        "user-guide",
        "firefox-policy-guide",
        "cis-settings-guide",
        "administrator-guide",
    ]
    assert facets["firefox_channel"] == ["esr-140.12", "release-152", None]
    assert facets["policy_category"] == [
        "advanced",
        "ai_smart",
        "browser_behavior",
        "extensions_integrations",
        "home_startup",
        "network_access",
        "privacy_security",
        "search",
        None,
    ]
    assert facets["cis_level"] == ["level-1", "level-2", None]
    assert facets["cis_control_state"] == [
        "mapped",
        "preference_mapped",
        "needs_research",
        "deprecated_or_removed",
        "manual-review",
        "provenance-only",
        None,
    ]
    assert facets["api_area"] == ["service", "health", "profiles", "validation", "import-export", "ui", None]

    integrity = contract["integrity"]
    assert integrity == {
        "index_per_locale": True,
        "manifest_records_sha256": True,
        "clean_build_reproducible": True,
        "duplicate_document_id_rejected": True,
        "broken_topic_or_anchor_rejected": True,
        "wrong_locale_text_rejected": True,
    }
