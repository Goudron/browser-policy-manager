from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/search-candidate-prototypes-0.9.3.json"
MODULE_PATH = ROOT / "documentation/tools/search_candidate_prototypes.py"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
SPEC = importlib.util.spec_from_file_location("search_candidate_prototypes", MODULE_PATH)
assert SPEC and SPEC.loader
prototypes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototypes)

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_candidate_prototype_contract_has_the_same_shortlist_and_a_non_execution_boundary() -> None:
    config = _config()

    assert config["backlog_item"] == "BPM093-M3-02"
    assert config["status"] == "accepted-adapter-contracts-not-benchmarked"
    assert tuple(config["locales"]) == LOCALES
    assert set(config["candidate_adapters"]) == {
        "current-static-control",
        "pagefind-1.5.2",
        "meilisearch-ce-1.45.1",
    }
    assert config["prototype_boundary"]["production_portal"] == "not modified"
    assert (
        "not installed, downloaded, started, or benchmarked"
        in config["prototype_boundary"]["vendor_execution"]
    )
    assert (
        "not Pagefind or Meilisearch relevance results"
        in config["prototype_boundary"]["result_meaning"]
    )


def test_compact_documents_are_locale_separated_and_keep_required_bpm_metadata() -> None:
    documents = prototypes.build_compact_documents()

    assert len(documents) == 24
    for locale in LOCALES:
        locale_documents = [document for document in documents if document["locale"] == locale]
        assert len(locale_documents) == 4
        for document in locale_documents:
            assert document["url"].startswith(f"/help/{locale}/")
            assert document["source"]["output_path"].startswith(f"{locale}/")
            assert document["facets"]["locale"] == [locale]
            assert document["searchable"]["identifiers"]
            assert document["searchable"]["aliases"]
            assert document["source_weights"] == {
                "exact_identifier": 1000,
                "title": 180,
                "alias": 140,
                "heading": 80,
                "body": 20,
                "bounded_typo": 12,
                "recency": 0,
            }


def test_candidate_inputs_are_real_adapter_shapes_without_vendor_execution() -> None:
    current = prototypes.candidate_index_input("current-static-control", "ru")
    pagefind = prototypes.candidate_index_input("pagefind-1.5.2", "ru")
    meilisearch = prototypes.candidate_index_input("meilisearch-ce-1.45.1", "ru")

    assert len(current["documents"]) == 4
    assert pagefind["execution"] == "not-invoked"
    assert len(pagefind["static_documents"]) == 4
    assert "data-pagefind-body" in pagefind["static_documents"][0]["html"]
    assert "data-pagefind-filter" in pagefind["static_documents"][0]["html"]
    assert meilisearch["execution"] == "not-started-private-adapter-only"
    assert meilisearch["index_settings"]["filterableAttributes"]
    assert len(meilisearch["documents"]) == 4
    envelope = prototypes.candidate_query_envelope("meilisearch-ce-1.45.1", "ru", "AIControls", {})
    assert envelope["browser_to_daemon"] == "forbidden"
    assert envelope["request"]["path"] == "/private/search"


@pytest.mark.parametrize(
    "candidate_id", ("current-static-control", "pagefind-1.5.2", "meilisearch-ce-1.45.1")
)
def test_every_adapter_has_stable_normalized_results_for_identifiers_aliases_and_facets(
    candidate_id: str,
) -> None:
    exact = prototypes.query_candidate(candidate_id, "en", "API-VAL-001")
    alias = prototypes.query_candidate(candidate_id, "ru", "умные функции")
    filtered = prototypes.query_candidate(
        candidate_id, "en", "validation", {"api_area": ["validation"]}
    )

    assert exact["execution"] == "adapter-contract-reference-only"
    assert exact["results"][0]["topic_id"] == "admin-task-validate-firefox-policies-json"
    assert exact["results"][0]["score_breakdown"]["exact_identifier"] == 1000
    assert alias["results"][0]["topic_id"] == "ug-task-configure-firefox-ai-policies"
    assert "alias" in alias["results"][0]["matched_fields"]
    assert [result["topic_id"] for result in filtered["results"]] == [
        "admin-task-validate-firefox-policies-json"
    ]
    assert all(result["url"].startswith("/help/") for result in exact["results"])
