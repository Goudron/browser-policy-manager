from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONFIG_PATH = DOCUMENTATION_ROOT / "config/search-browser-tuning-benchmark-0.9.3.json"
RUNNER_PATH = DOCUMENTATION_ROOT / "tools/run_browser_search_tuning_benchmark_0_9_3.py"
TOOLS_ROOT = DOCUMENTATION_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
SPEC = importlib.util.spec_from_file_location("browser_search_tuning_benchmark", RUNNER_PATH)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)

pytestmark = pytest.mark.docs_contract


def test_browser_tuning_benchmark_contract_locks_per_locale_comparative_rule() -> None:
    contract = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert contract["contract_id"] == "bpm-doc-search-browser-tuning-benchmark-0.9.3"
    assert contract["backlog_item"] == "BPM093-M4-04"
    assert contract["metrics"] == ["top_1", "mrr", "recall_at_5", "no_result_recall"]
    assert contract["acceptance"]["strict_improvement_metrics"] == [
        "top_1", "mrr", "recall_at_5"
    ]
    assert "Every maintained locale independently" in contract["acceptance"]["scope"]
    assert "no network request" in contract["network_boundary"]


def test_browser_tuning_benchmark_improves_each_locale_without_no_result_regression() -> None:
    report = benchmark.run_benchmark()

    assert report["status"] == "pass"
    assert report["case_count"] == 244
    for locale, comparison in report["comparison"].items():
        assert comparison["no_regression"], locale
        assert set(comparison["strictly_improved_metrics"]) >= {
            "top_1", "mrr", "recall_at_5"
        }, locale
        assert report["selected_browser_metrics"][locale]["no_result_recall"] >= report[
            "frozen_control_metrics"
        ][locale]["no_result_recall"]
