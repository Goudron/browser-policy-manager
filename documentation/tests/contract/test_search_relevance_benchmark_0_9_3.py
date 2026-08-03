from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/search-relevance-benchmark-0.9.3.json"
TOOLS_ROOT = ROOT / "documentation/tools"
MODULE_PATH = TOOLS_ROOT / "run_search_relevance_benchmark_0_9_3.py"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
SPEC = importlib.util.spec_from_file_location("search_relevance_benchmark", MODULE_PATH)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_relevance_benchmark_contract_locks_artifacts_and_non_selection_boundary() -> None:
    config = _config()

    assert config["backlog_item"] == "BPM093-M3-03"
    assert config["status"] == "accepted-runner-contract"
    assert config["artifacts"]["pagefind"] == {
        "version": "1.5.2",
        "npm_package": "pagefind-1.5.2.tgz",
        "npm_package_sha256": "539357f51b47ea98cbef10bd774b432730d5a839ade5b5a30d13df033cbe9348",
        "linux_x64_package": "pagefind-linux-x64-1.5.2.tgz",
        "linux_x64_package_sha256": "3c8dcfdaa69946113e0257be05bdef57297c7f1a562aa168536ff7c5d4590660",
        "source": "https://www.npmjs.com/package/pagefind/v/1.5.2",
    }
    assert config["artifacts"]["meilisearch_ce"]["version"] == "1.45.1"
    assert config["artifacts"]["meilisearch_ce"]["linux_amd64_binary_sha256"] == "35986cba02cc4c9a2f79b4f85be8c2bc0013989c208410e6cfea85b1fdc3d708"
    assert "does not select a candidate" in config["output"]["selection_boundary"]


def test_query_plan_uses_the_accepted_six_locale_matrix_without_hiding_difficult_classes() -> None:
    cases = benchmark.build_query_plan()
    counts = Counter(case.locale for case in cases)

    assert counts == {"en": 40, "ru": 40, "de": 40, "zh-CN": 40, "fr": 44, "es-ES": 40}
    assert sum(case.expected_topic_id is not None for case in cases) == 196
    assert sum(case.expected_no_result for case in cases) == 42
    assert sum(not case.scored for case in cases) == 6
    assert {
        "typo", "morphology", "german_compound", "russian_inflection", "accent",
        "technical_identifier", "chinese_segmentation", "no_result",
    } <= {case.query_class for case in cases}


def test_compact_index_keeps_only_canonical_and_reviewed_alias_forms() -> None:
    documents = benchmark.build_compact_documents()
    profile_en = next(document for document in documents if document["document_id"] == "bpm093-prototype:en:profile-library")
    profile_ru = next(document for document in documents if document["document_id"] == "bpm093-prototype:ru:profile-library")

    assert profile_en["searchable"]["aliases"] == ["saved profiles"]
    assert "profile librarry" not in profile_en["searchable"]["body"]
    assert "профелий" not in profile_ru["searchable"]["body"]
    assert benchmark._current_control_topics(
        [document for document in documents if document["locale"] == "en"], "API-VAL-001"
    )[0] == "admin-task-validate-firefox-policies-json"


def test_runner_keeps_candidate_network_boundaries_explicit_in_source() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "unexpected Pagefind fetch origin" in source
    assert "non-loopback benchmark request rejected" in source
    assert '"MEILI_NO_ANALYTICS": "true"' in source
    assert '"--no-analytics"' in source
