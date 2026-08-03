"""Deterministic, non-production input/output adapters for BPM093 M3 search candidates.

The module intentionally creates no vendor index, subprocess, service, or network request. Its
normalized query result is an adapter-contract smoke result, not a Pagefind or Meilisearch score.
"""

from __future__ import annotations

import html
import json
import unicodedata
from pathlib import Path
from typing import Any

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = DOCUMENTATION_ROOT / "config"
PROTOTYPE_CONFIG = CONFIG_ROOT / "search-candidate-prototypes-0.9.3.json"
EVALUATION_CORPUS = CONFIG_ROOT / "search-rag-evaluation-corpus-0.9.3.json"
RANKING_CONFIG = CONFIG_ROOT / "search-ranking-typo-0.9.0.json"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).casefold()
    return "".join(character for character in folded if not unicodedata.combining(character))


def _tokens(text: str) -> list[str]:
    normalized = _normalized(text)
    return "".join(character if character.isalnum() else " " for character in normalized).split()


def _text_matches(query: str, value: str) -> bool:
    query_tokens = set(_tokens(query))
    value_tokens = set(_tokens(value))
    return bool(query_tokens and value_tokens and query_tokens & value_tokens)


def _load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _read_json(PROTOTYPE_CONFIG), _read_json(EVALUATION_CORPUS), _read_json(RANKING_CONFIG)


def build_compact_documents() -> list[dict[str, Any]]:
    """Return the same 24 plain-text canonical documents for every candidate adapter."""
    config, corpus, ranking = _load_inputs()
    weights = ranking["weights"]
    metadata = config["compact_documents"]["domain_metadata"]
    documents: list[dict[str, Any]] = []
    for locale in config["locales"]:
        for domain in corpus["domains"]:
            domain_id = domain["id"]
            details = metadata[domain_id]
            terms = domain["terms"][locale]
            topic_id = domain["topic_id"]
            identifier = domain["identifier"]
            facets = {
                "locale": [locale],
                "guide_id": [details["guide_id"]],
                "topic_kind": [details["topic_kind"]],
                "firefox_channel": details["facets"]["firefox_channel"],
                "policy_category": details["facets"]["policy_category"],
                "cis_level": details["facets"]["cis_level"],
                "cis_control_state": details["facets"]["cis_control_state"],
                "api_area": details["facets"]["api_area"],
                "bpm_version": [config["target_bpm_version"]],
            }
            output_path = f"{locale}/{details['output_slug']}.html"
            documents.append(
                {
                    "document_id": f"bpm093-prototype:{locale}:{domain_id}",
                    "locale": locale,
                    "guide_id": details["guide_id"],
                    "topic_id": topic_id,
                    "topic_kind": details["topic_kind"],
                    "url": f"/help/{output_path}",
                    "source": {
                        "topic_id": topic_id,
                        "anchor_id": None,
                        "dita_key": f"bpm093-{domain_id}",
                        "source_slug": details["output_slug"],
                        "output_path": output_path,
                    },
                    "searchable": {
                        "title": terms[0],
                        "shortdesc": f"{terms[0]} — BPM documentation prototype.",
                        "headings": [terms[0]],
                        "body": terms[0],
                        "keywords": [terms[0]],
                        "identifiers": [topic_id, identifier, domain["citation_id"]],
                        "aliases": [terms[1]],
                    },
                    "facets": facets,
                    "versions": {
                        "bpm_version": config["target_bpm_version"],
                        "documentation_version": config["target_bpm_version"],
                        "source_revision": "BPM093-M2-03",
                    },
                    "source_weights": weights,
                }
            )
    return documents


def _pagefind_static_document(document: dict[str, Any]) -> str:
    searchable = document["searchable"]
    filter_spans = "".join(
        f'<span data-pagefind-filter="{html.escape(field)}">{html.escape(value)}</span>'
        for field, values in document["facets"].items()
        for value in values
    )
    return (
        f'<main data-pagefind-body data-bpm-document-id="{html.escape(document["document_id"])}">'
        f'<h1 data-pagefind-meta="title">{html.escape(searchable["title"])}</h1>'
        f'<p>{html.escape(searchable["shortdesc"])}</p>{filter_spans}</main>'
    )


def candidate_index_input(candidate_id: str, locale: str) -> dict[str, Any]:
    """Return a candidate-specific index input without executing external software."""
    config, _, _ = _load_inputs()
    adapters = config["candidate_adapters"]
    if candidate_id not in adapters:
        raise ValueError(f"unknown search candidate: {candidate_id}")
    if locale not in config["locales"]:
        raise ValueError(f"unsupported locale: {locale}")
    documents = [document for document in build_compact_documents() if document["locale"] == locale]
    if candidate_id == "current-static-control":
        return {"candidate_id": candidate_id, "locale": locale, "documents": documents}
    if candidate_id == "pagefind-1.5.2":
        return {
            "candidate_id": candidate_id,
            "locale": locale,
            "execution": "not-invoked",
            "static_documents": [
                {"url": document["url"], "html": _pagefind_static_document(document)}
                for document in documents
            ],
        }
    return {
        "candidate_id": candidate_id,
        "locale": locale,
        "execution": "not-started-private-adapter-only",
        "index_settings": {
            "filterableAttributes": [
                "guide_id", "topic_kind", "firefox_channel", "policy_category",
                "cis_level", "cis_control_state", "api_area", "bpm_version",
            ],
            "searchableAttributes": ["identifiers", "title", "aliases", "headings", "body"],
        },
        "documents": [
            {
                "id": document["document_id"],
                "locale": locale,
                "guide_id": document["guide_id"],
                "topic_id": document["topic_id"],
                "url": document["url"],
                "title": document["searchable"]["title"],
                "identifiers": document["searchable"]["identifiers"],
                "aliases": document["searchable"]["aliases"],
                "headings": document["searchable"]["headings"],
                "body": document["searchable"]["body"],
                **document["facets"],
            }
            for document in documents
        ],
    }


def candidate_query_envelope(candidate_id: str, locale: str, query: str, filters: dict[str, list[str]]) -> dict[str, Any]:
    """Describe the adapter input that M3-03 will connect to a real candidate."""
    if candidate_id == "current-static-control":
        return {"candidate_id": candidate_id, "locale": locale, "query": query, "filters": filters, "transport": "in-process"}
    if candidate_id == "pagefind-1.5.2":
        return {"candidate_id": candidate_id, "locale": locale, "query": query, "filters": filters, "transport": "BPM-owned-static-adapter"}
    if candidate_id == "meilisearch-ce-1.45.1":
        return {
            "candidate_id": candidate_id,
            "locale": locale,
            "transport": "not-started-private-adapter-only",
            "browser_to_daemon": "forbidden",
            "request": {"method": "POST", "path": "/private/search", "body": {"q": query, "filters": filters}},
        }
    raise ValueError(f"unknown search candidate: {candidate_id}")


def _facet_match(document: dict[str, Any], filters: dict[str, list[str]]) -> bool:
    return all(
        not values or bool(set(values) & set(document["facets"].get(field, [])))
        for field, values in filters.items()
    )


def _normalized_result(document: dict[str, Any], query: str) -> dict[str, Any] | None:
    searchable = document["searchable"]
    weights = document["source_weights"]
    exact = int(any(_normalized(query) == _normalized(value) for value in searchable["identifiers"]))
    title = int(_text_matches(query, searchable["title"]))
    alias = sum(int(_text_matches(query, value)) for value in searchable["aliases"])
    heading = sum(int(_text_matches(query, value)) for value in searchable["headings"])
    body = int(_text_matches(query, searchable["body"]))
    breakdown = {
        "exact_identifier": exact * weights["exact_identifier"],
        "title": title * weights["title"],
        "alias": alias * weights["alias"],
        "heading": heading * weights["heading"],
        "body": body * weights["body"],
        "bounded_typo": 0,
        "recency": weights["recency"],
    }
    score = sum(breakdown.values())
    if not score:
        return None
    return {
        "result_id": f"result:{document['document_id']}",
        "document_id": document["document_id"],
        "locale": document["locale"],
        "guide_id": document["guide_id"],
        "topic_id": document["topic_id"],
        "anchor_id": document["source"]["anchor_id"],
        "title": searchable["title"],
        "url": document["url"],
        "snippet": searchable["shortdesc"][:260],
        "score": score,
        "score_breakdown": breakdown,
        "matched_fields": [field for field, value in breakdown.items() if field != "recency" and value],
        "identifiers": searchable["identifiers"],
        "facets": document["facets"],
    }


def query_candidate(candidate_id: str, locale: str, query: str, filters: dict[str, list[str]] | None = None) -> dict[str, Any]:
    """Run the shared reference mapping and return its candidate envelope plus normalized results.

    This is deliberately not a substitute for vendor execution or a relevance measurement.
    """
    applied_filters = filters or {}
    envelope = candidate_query_envelope(candidate_id, locale, query, applied_filters)
    results = [
        result
        for document in build_compact_documents()
        if document["locale"] == locale and _facet_match(document, applied_filters)
        if (result := _normalized_result(document, query)) is not None
    ]
    return {
        "candidate_id": candidate_id,
        "execution": "adapter-contract-reference-only",
        "query_envelope": envelope,
        "results": sorted(results, key=lambda result: (-result["score"], result["guide_id"], result["topic_id"])),
    }
