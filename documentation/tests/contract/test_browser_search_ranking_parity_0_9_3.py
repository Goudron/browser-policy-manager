from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
TOOLS_ROOT = DOCUMENTATION_ROOT / "tools"
BUILD_DOCS_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
PROTOTYPES_PATH = DOCUMENTATION_ROOT / "tools/search_candidate_prototypes.py"
RELEVANCE_RUNNER_PATH = DOCUMENTATION_ROOT / "tools/run_search_relevance_benchmark_0_9_3.py"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"
SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS_PATH)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)
PROTOTYPES_SPEC = importlib.util.spec_from_file_location("search_candidate_prototypes", PROTOTYPES_PATH)
assert PROTOTYPES_SPEC and PROTOTYPES_SPEC.loader
search_candidate_prototypes = importlib.util.module_from_spec(PROTOTYPES_SPEC)
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
sys.modules[PROTOTYPES_SPEC.name] = search_candidate_prototypes
PROTOTYPES_SPEC.loader.exec_module(search_candidate_prototypes)
RELEVANCE_RUNNER_SPEC = importlib.util.spec_from_file_location(
    "run_search_relevance_benchmark_0_9_3", RELEVANCE_RUNNER_PATH
)
assert RELEVANCE_RUNNER_SPEC and RELEVANCE_RUNNER_SPEC.loader
relevance_runner = importlib.util.module_from_spec(RELEVANCE_RUNNER_SPEC)
sys.modules[RELEVANCE_RUNNER_SPEC.name] = relevance_runner
RELEVANCE_RUNNER_SPEC.loader.exec_module(relevance_runner)

pytestmark = pytest.mark.docs_contract

NODE_HARNESS = r"""
const fs = require("node:fs");
global.window = global;
global.HTMLSelectElement = class HTMLSelectElement {};
global.document = {
  documentElement: { dataset: {} },
  addEventListener() {},
  querySelector() { return null; },
  querySelectorAll() { return []; },
};
require(process.argv[1]);
const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const output = payload.cases.map((item) => ({
  tokens: window.BpmDocsSearchRanking.queryTokens(item.query, item.index),
  topic_ids: window.BpmDocsSearchRanking.rankDocuments(item.index, item.query)
    .map((result) => result.documentRecord.topic_id),
}));
process.stdout.write(JSON.stringify(output));
"""


def _document(locale: str, topic_id: str, title: str, body: str) -> dict[str, Any]:
    aliases = build_docs._search_normalization_aliases()
    identifiers = [topic_id, f"topic:{topic_id}"]
    alias_groups = build_docs._search_alias_groups_for_document(
        locale,
        topic_id,
        set(identifiers),
        aliases,
    )
    searchable = {
        "title": title,
        "shortdesc": body,
        "headings": [],
        "body": body,
        "keywords": [],
        "identifiers": identifiers,
        "aliases": [term for group in alias_groups for term in group["terms"]],
    }
    normalized_fields = {
        field: build_docs._normalize_search_values(
            locale,
            value if isinstance(value, list) else [value],
            aliases,
        )
        for field, value in searchable.items()
    }
    return {
        "topic_id": topic_id,
        "guide_id": "user-guide",
        "searchable": searchable,
        "normalized": {
            "fields": normalized_fields,
            "alias_ids": [group["alias_id"] for group in alias_groups],
            "alias_match_sources": {
                group["alias_id"]: group["match_sources"] for group in alias_groups
            },
        },
    }


def _index(locale: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
    aliases = build_docs._search_normalization_aliases()
    ranking = build_docs._search_ranking_typo()
    return {
        "locale": locale,
        "normalization": {
            **aliases["normalization"],
            "alias_groups": [
                {
                    "alias_id": group["alias_id"],
                    "terms": build_docs._alias_terms_for_locale(group, locale),
                }
                for group in aliases["alias_groups"]
            ],
        },
        "ranking": {
            "weights": ranking["weights"],
            "typo_tolerance": ranking["typo_tolerance"],
            "tie_breakers": ranking["tie_breakers"],
        },
        "documents": documents,
    }


def _compact_document(document: dict[str, Any]) -> dict[str, Any]:
    locale = document["locale"]
    aliases = build_docs._search_normalization_aliases()
    searchable = document["searchable"]
    alias_groups = build_docs._search_alias_groups_for_document(
        locale,
        document["topic_id"],
        set(searchable["identifiers"]),
        aliases,
    )
    normalized_fields = {
        field: build_docs._normalize_search_values(
            locale,
            value if isinstance(value, list) else [value],
            aliases,
        )
        for field, value in searchable.items()
    }
    return {
        "topic_id": document["topic_id"],
        "guide_id": document["guide_id"],
        "searchable": searchable,
        "normalized": {
            "fields": normalized_fields,
            "alias_ids": [group["alias_id"] for group in alias_groups],
            "alias_match_sources": {
                group["alias_id"]: group["match_sources"] for group in alias_groups
            },
        },
    }


def _node_rank(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["node", "--eval", NODE_HARNESS, str(SEARCH_SCRIPT)],
        input=json.dumps({"cases": cases}, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_browser_ranker_uses_the_same_versioned_normalization_and_ranking_contract() -> None:
    source = SEARCH_SCRIPT.read_text(encoding="utf-8")

    for required in (
        "window.BpmDocsSearchRanking",
        "documentRecord.normalized?.fields",
        "index.normalization?.alias_groups",
        "boundedLevenshtein",
        "cjkExpansions",
        "weights.exact_identifier",
        "compareRankedDocuments",
    ):
        assert required in source

    # M4-05 removes the former flattened-text browser scorer.  The active scorer
    # must consume the generated normalized field projection shared with the build.
    assert "searchableText" not in source


def test_browser_ranker_matches_build_ranker_for_typo_alias_and_cjk_cases() -> None:
    cases = [
        {
            "query": "profil library",
            "index": _index(
                "en",
                [
                    _document("en", "ug-task-use-profile-library", "Profile Library", "Save profiles."),
                    _document("en", "ug-task-configure-firefox-ai-policies", "Firefox AI", "Policies."),
                ],
            ),
        },
        {
            "query": "配置档案库",
            "index": _index(
                "zh-CN",
                [
                    _document("zh-CN", "ug-task-use-profile-library", "配置档案库", "保存配置档案。"),
                    _document("zh-CN", "ug-task-configure-firefox-ai-policies", "Firefox AI 策略", "策略。"),
                ],
            ),
        },
        {
            "query": "API Validirungsendpunkt",
            "index": _index(
                "de",
                [
                    _document(
                        "de",
                        "admin-task-validate-firefox-policies-json",
                        "API-Validierungsendpunkt",
                        "Policies validieren.",
                    ),
                    _document("de", "ug-task-use-profile-library", "Profilbibliothek", "Profile."),
                ],
            ),
        },
    ]

    browser_results = _node_rank(cases)
    for case, browser in zip(cases, browser_results, strict=True):
        index = case["index"]
        expected = build_docs._rank_search_documents(
            index["locale"],
            case["query"],
            index["documents"],
            build_docs._search_normalization_aliases(),
            build_docs._search_ranking_typo(),
        )
        assert browser["topic_ids"] == [result["document"]["topic_id"] for result in expected]

    assert {"配置", "档案"} <= set(browser_results[1]["tokens"])


def test_browser_ranker_does_not_regress_frozen_control_on_six_locale_relevance_corpus() -> None:
    compact_documents = search_candidate_prototypes.build_compact_documents()
    documents_by_locale = {
        locale: [
            _compact_document(document)
            for document in compact_documents
            if document["locale"] == locale
        ]
        for locale in build_docs.LOCALES
    }
    cases = relevance_runner.build_query_plan()
    browser_results = _node_rank(
        [
            {"query": case.query, "index": _index(case.locale, documents_by_locale[case.locale])}
            for case in cases
        ]
    )

    for case, browser_result in zip(cases, browser_results, strict=True):
        frozen_control = relevance_runner._current_control_topics(
            [document for document in compact_documents if document["locale"] == case.locale],
            case.query,
        )
        if case.expected_topic_id:
            frozen_rank = (
                frozen_control.index(case.expected_topic_id) + 1
                if case.expected_topic_id in frozen_control
                else None
            )
            browser_rank = (
                browser_result["topic_ids"].index(case.expected_topic_id) + 1
                if case.expected_topic_id in browser_result["topic_ids"]
                else None
            )
            if frozen_rank is not None:
                assert browser_rank is not None, case.query_id
                assert browser_rank <= frozen_rank, case.query_id
        elif case.expected_no_result and not frozen_control:
            assert browser_result["topic_ids"] == [], case.query_id
