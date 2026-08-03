"""Compare the BPM browser ranker with the frozen M3 static-search control.

The runner uses the compact reviewed six-locale corpus and the maintained browser script only. It
does not read a generated site, call a network service, launch a browser, or download software.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from . import build_docs
    from . import run_search_relevance_benchmark_0_9_3 as relevance_benchmark
    from .search_candidate_prototypes import build_compact_documents
except ImportError:  # Direct script execution keeps documentation/tools on sys.path.
    import build_docs
    import run_search_relevance_benchmark_0_9_3 as relevance_benchmark
    from search_candidate_prototypes import build_compact_documents

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = DOCUMENTATION_ROOT / "config/search-browser-tuning-benchmark-0.9.3.json"
SEARCH_SCRIPT = DOCUMENTATION_ROOT / "assets/theme/bpm-docs-search.js"

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
const output = payload.cases.map((item) =>
  window.BpmDocsSearchRanking.rankDocuments(item.index, item.query)
    .map((result) => result.documentRecord.topic_id)
);
process.stdout.write(JSON.stringify(output));
"""


class BenchmarkError(RuntimeError):
    """Raised when benchmark inputs or comparative acceptance are invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _browser_document(document: dict[str, Any], aliases: dict[str, Any]) -> dict[str, Any]:
    projected = copy.deepcopy(document)
    locale = projected["locale"]
    searchable = projected["searchable"]
    alias_groups = build_docs._search_alias_groups_for_document(
        locale,
        projected["topic_id"],
        set(searchable["identifiers"]),
        aliases,
    )
    searchable["aliases"] = sorted(
        set(searchable["aliases"])
        | {term for group in alias_groups for term in group["terms"]}
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
        "document_id": projected["document_id"],
        "topic_id": projected["topic_id"],
        "guide_id": projected["guide_id"],
        "searchable": searchable,
        "filter_facets": projected["facets"],
        "normalized": {
            "fields": normalized_fields,
            "alias_ids": [group["alias_id"] for group in alias_groups],
            "alias_match_sources": {
                group["alias_id"]: group["match_sources"] for group in alias_groups
            },
        },
    }


def _browser_index(locale: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
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


def _browser_topics(cases: list[Any], documents: list[dict[str, Any]]) -> dict[str, list[str]]:
    aliases = build_docs._search_normalization_aliases()
    documents_by_locale = {
        locale: [
            _browser_document(document, aliases)
            for document in documents
            if document["locale"] == locale
        ]
        for locale in build_docs.LOCALES
    }
    payload = {
        "cases": [
            {
                "query": case.query,
                "index": _browser_index(case.locale, documents_by_locale[case.locale]),
            }
            for case in cases
        ]
    }
    completed = subprocess.run(
        ["node", "--eval", NODE_HARNESS, str(SEARCH_SCRIPT)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise BenchmarkError(f"browser ranker execution failed: {completed.stderr.strip()}")
    topics = json.loads(completed.stdout)
    return {case.query_id: result for case, result in zip(cases, topics, strict=True)}


def _metrics(cases: list[Any], topics: dict[str, list[str]]) -> dict[str, dict[str, float]]:
    expected_ranks: dict[str, list[int | None]] = defaultdict(list)
    no_result_outcomes: dict[str, list[bool]] = defaultdict(list)
    for case in cases:
        result_topics = topics[case.query_id]
        if case.expected_topic_id:
            rank = (
                result_topics.index(case.expected_topic_id) + 1
                if case.expected_topic_id in result_topics
                else None
            )
            expected_ranks[case.locale].append(rank)
        elif case.expected_no_result:
            no_result_outcomes[case.locale].append(not result_topics)
    metrics: dict[str, dict[str, float]] = {}
    for locale in build_docs.LOCALES:
        expected = expected_ranks[locale]
        no_results = no_result_outcomes[locale]
        if not expected or not no_results:
            raise BenchmarkError(f"incomplete benchmark coverage for {locale}")
        metrics[locale] = {
            "top_1": sum(rank == 1 for rank in expected) / len(expected),
            "mrr": sum(1 / rank if rank else 0 for rank in expected) / len(expected),
            "recall_at_5": sum(bool(rank and rank <= 5) for rank in expected) / len(expected),
            "no_result_recall": sum(no_results) / len(no_results),
        }
    return metrics


def run_benchmark() -> dict[str, Any]:
    config = _read_json(CONFIG_PATH)
    documents = build_compact_documents()
    cases = relevance_benchmark.build_query_plan()
    frozen_topics = {
        case.query_id: relevance_benchmark._current_control_topics(
            [document for document in documents if document["locale"] == case.locale],
            case.query,
        )
        for case in cases
    }
    selected_topics = _browser_topics(cases, documents)
    frozen_metrics = _metrics(cases, frozen_topics)
    selected_metrics = _metrics(cases, selected_topics)
    comparison: dict[str, dict[str, Any]] = {}
    for locale in build_docs.LOCALES:
        no_regression = all(
            selected_metrics[locale][metric] >= frozen_metrics[locale][metric]
            for metric in config["acceptance"]["no_regression_metrics"]
        )
        improvements = [
            metric
            for metric in config["acceptance"]["strict_improvement_metrics"]
            if selected_metrics[locale][metric] > frozen_metrics[locale][metric]
        ]
        comparison[locale] = {
            "no_regression": no_regression,
            "strictly_improved_metrics": improvements,
        }
    status = "pass" if all(
        result["no_regression"] and result["strictly_improved_metrics"]
        for result in comparison.values()
    ) else "fail"
    return {
        "schema_version": 1,
        "backlog_item": config["backlog_item"],
        "status": status,
        "case_count": len(cases),
        "source_hashes": {
            "config": _sha256(CONFIG_PATH),
            "browser_script": _sha256(SEARCH_SCRIPT),
            "evaluation_corpus": _sha256(relevance_benchmark.EVALUATION_CORPUS),
        },
        "frozen_control_metrics": frozen_metrics,
        "selected_browser_metrics": selected_metrics,
        "comparison": comparison,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"browser tuning benchmark: {report['status']}", flush=True)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
