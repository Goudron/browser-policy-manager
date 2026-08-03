from __future__ import annotations

import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONTRACT_PATH = DOCUMENTATION_ROOT / "config/search-domain-ranking-facets-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def test_domain_ranking_and_facets_contract_preserves_bpm_search_evidence() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert contract["contract_id"] == "bpm-doc-search-domain-ranking-facets-0.9.3"
    assert contract["backlog_item"] == "BPM093-M4-03"
    assert contract["ranking"]["weight_contract_id"] == "bpm-doc-search-ranking-typo-0.9.0"
    assert contract["ranking"]["preserved_sources"] == [
        "identifiers", "title", "aliases", "headings", "body", "bounded_typo"
    ]
    assert contract["ranking"]["evidence_fields"] == [
        "topic_id", "document_id", "score", "score_breakdown", "matched_fields",
        "identifiers", "filter_facets",
    ]
    assert contract["facets"]["preserved_fields"] == [
        "locale", "guide_id", "topic_kind", "firefox_channel", "policy_category",
        "cis_level", "cis_control_state", "api_area", "bpm_version",
    ]
    assert contract["facets"]["composition"] == (
        "AND across facet fields; OR within values of the same facet field."
    )
    assert contract["adapter_projection"]["maximum_evidence_rows"] == 50
    assert "invent a domain facet" in contract["adapter_projection"]["must_not"]
