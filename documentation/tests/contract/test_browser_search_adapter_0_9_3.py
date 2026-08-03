from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
BUILD_DOCS_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
ADAPTER_CONTRACT = DOCUMENTATION_ROOT / "config/search-browser-adapter-contract-0.9.3.json"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"
SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract

NODE_HARNESS = r"""
const fs = require("node:fs");
global.window = global;
global.window.location = { origin: "https://docs.example.test" };
global.HTMLSelectElement = class HTMLSelectElement {};
global.document = {
  documentElement: { dataset: {} },
  addEventListener() {},
  querySelector() { return null; },
  querySelectorAll() { return []; },
};
require(process.argv[1]);
const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const adapter = window.BpmDocsSearchAdapter;
const hydrated = adapter.hydrate(payload.index, payload.search, payload.recentQuery);
const result = adapter.query(payload.index, hydrated);
process.stdout.write(JSON.stringify({
  frozen: Object.isFrozen(adapter),
  contractId: adapter.contractId,
  schemaVersion: adapter.schemaVersion,
  hydrated: {
    query: hydrated.query,
    filters: Object.fromEntries([...hydrated.filters].map(([field, values]) => [field, [...values].sort()])),
  },
  serialized: adapter.serialize(payload.index, hydrated),
  result: {
    statusKind: result.statusKind,
    resultCount: result.resultCount,
    topicIds: result.documents.map((documentRecord) => documentRecord.topic_id),
    rankingEvidence: result.rankingEvidence,
    facetCounts: result.facetCounts,
  },
  readyStatus: adapter.query(payload.index, { query: "", filters: new Map() }).statusKind,
  urls: payload.urls.map((url) => adapter.safeResultUrl(payload.index.locale, url)),
}));
"""


def _index() -> dict[str, Any]:
    aliases = build_docs._search_normalization_aliases()
    ranking = build_docs._search_ranking_typo()
    searchable = {
        "title": "Profile Library",
        "shortdesc": "Save and reuse managed profiles.",
        "headings": [],
        "body": "Profile Library documentation.",
        "keywords": [],
        "identifiers": ["ug-task-use-profile-library"],
        "aliases": ["saved profiles"],
    }
    return {
        "locale": "en",
        "normalization": {
            **aliases["normalization"],
            "alias_groups": [],
        },
        "ranking": {
            "weights": ranking["weights"],
            "typo_tolerance": ranking["typo_tolerance"],
        },
        "filtering": {
            "url_state": {"parameters": {"guide_id": "guide"}},
            "facet_fields": {"guide_id": {"values": ["user-guide"]}},
        },
        "facet_counts": {"guide_id": {"user-guide": 1}},
        "documents": [
            {
                "document_id": "en:ug-task-use-profile-library",
                "topic_id": "ug-task-use-profile-library",
                "guide_id": "user-guide",
                "url": "/help/en/user/ug-task-use-profile-library.html#a-profile-library",
                "searchable": searchable,
                "normalized": {
                    "fields": {
                        field: build_docs._normalize_search_values(
                            "en", value if isinstance(value, list) else [value], aliases
                        )
                        for field, value in searchable.items()
                    },
                    "alias_ids": [],
                    "alias_match_sources": {},
                },
                "filter_facets": {"guide_id": ["user-guide"]},
            }
        ],
    }


def _run_adapter() -> dict[str, Any]:
    completed = subprocess.run(
        ["node", "--eval", NODE_HARNESS, str(SEARCH_SCRIPT)],
        input=json.dumps(
            {
                "index": _index(),
                "search": "?q=Profile%20Library&guide=user-guide&guide=unknown&ignored=value",
                "recentQuery": "must-not-override-url",
                "urls": [
                    "/help/en/user/ug-task-use-profile-library.html#a-profile-library",
                    "/help/en/../ru/index.html",
                    "https://example.invalid/help/en/index.html",
                    "javascript:alert(1)",
                ],
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_browser_search_adapter_contract_defines_a_bpm_owned_stable_boundary() -> None:
    contract = json.loads(ADAPTER_CONTRACT.read_text(encoding="utf-8"))

    assert contract["contract_id"] == "bpm-doc-search-browser-adapter-0.9.3"
    assert contract["backlog_item"] == "BPM093-M4-02"
    assert contract["adapter"]["global"] == "BpmDocsSearchAdapter"
    assert contract["adapter"]["operations"] == ["hydrate", "serialize", "query", "safeResultUrl"]
    assert contract["state"]["history"].startswith("hydrate initial and popstate")
    assert contract["result"]["link_policy"].startswith("Only same-origin normalized paths")
    assert "add a dependency or vendor-specific browser UI" in contract["non_goals"]


def test_browser_search_adapter_hydrates_query_filters_results_and_safe_links() -> None:
    result = _run_adapter()

    assert result["frozen"] is True
    assert result["contractId"] == "bpm-doc-search-browser-adapter-0.9.3"
    assert result["schemaVersion"] == 1
    assert result["hydrated"] == {
        "query": "Profile Library",
        "filters": {"guide_id": ["user-guide"]},
    }
    assert result["serialized"] == "q=Profile+Library&guide=user-guide"
    assert result["result"] == {
        "statusKind": "result-singular",
        "resultCount": 1,
        "topicIds": ["ug-task-use-profile-library"],
        "rankingEvidence": [
            {
                "topic_id": "ug-task-use-profile-library",
                "document_id": "en:ug-task-use-profile-library",
                "score": 600,
                "score_breakdown": {
                    "exact_identifier": 0,
                    "title": 540,
                    "alias": 0,
                    "heading": 0,
                    "body": 60,
                    "bounded_typo": 0,
                    "recency": 0,
                },
                "matched_fields": ["title", "body"],
                "identifiers": ["ug-task-use-profile-library"],
                "filter_facets": {"guide_id": ["user-guide"]},
            }
        ],
        "facetCounts": {"guide_id": {"user-guide": 1}},
    }
    assert result["readyStatus"] == "ready"
    assert result["urls"] == [
        "/help/en/user/ug-task-use-profile-library.html#a-profile-library",
        "",
        "",
        "",
    ]


def test_browser_search_adapter_source_keeps_keyboard_history_and_safe_title_boundary() -> None:
    source = SEARCH_SCRIPT.read_text(encoding="utf-8")

    for required in (
        "window.BpmDocsSearchAdapter = BrowserSearchAdapter",
        'event.key !== "Escape"',
        'window.addEventListener("popstate"',
        "root.contains(document.activeElement)",
        'document.createElement("span")',
        "normalizeFilters(index, filters)",
        "rankingEvidence: visible.map",
        "facetCounts: index.facet_counts || {}",
    ):
        assert required in source
