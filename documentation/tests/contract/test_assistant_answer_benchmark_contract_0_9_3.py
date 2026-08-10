from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/assistant-answer-benchmark-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def test_m13_benchmark_defines_ten_local_and_ten_external_product_bounded_intents() -> None:
    contract = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert contract["backlog_item"] == "BPM093-M13-06A"
    assert contract["status"] == "approved-fixture-pending-live-execution"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert contract["local_benchmark_locales"] == ["en", "ru"]
    assert contract["external_benchmark_locales"] == ["en", "ru"]
    assert len(contract["local_questions"]) == 10
    assert len({item["id"] for item in contract["local_questions"]}) == 10
    assert all(item["expected_result"] == "answer" for item in contract["local_questions"])
    assert len(contract["external_questions"]) == 10
    assert len({item["id"] for item in contract["external_questions"]}) == 10
    assert all(item["source_domains"] for item in contract["external_questions"])
    assert all(
        set(item["localized_questions"]) == {"en", "ru"} for item in contract["external_questions"]
    )
    assert Counter(item["topic_class"] for item in contract["external_questions"]) == {
        "regulatory_requirements": 5,
        "browser_market": 2,
        "browser_news": 3,
    }
    domains = {
        domain for item in contract["external_questions"] for domain in item["source_domains"]
    }
    assert {
        "fstec.ru",
        "eur-lex.europa.eu",
        "pcisecuritystandards.org",
        "gs.statcounter.com",
    } <= domains
    assert "M13-06A runner" in contract["prompt_localization"]


def test_m13_benchmark_freezes_quality_thresholds_and_safe_remediation_order() -> None:
    contract = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    local = contract["scoring"]["local"]
    external = contract["scoring"]["external"]
    assert local["cases"] == 20
    assert local["citation_resolution_rate"] == 1.0
    assert local["explicit_context_relevance_rate"] == 1.0
    assert local["long_extractive_answer_rate"] == 0.0
    assert local["minimum_reviewer_relevance_and_completeness_score"] == 4
    assert external["cases"] == 20
    assert external["validated_allowlisted_source_rate"] == 1.0
    assert external["legal_or_compliance_conclusion_rate"] == 0.0
    assert contract["execution_boundaries"]["local_mode_network_calls"] == 0
    assert contract["execution_boundaries"]["model_weight_change"] is False
    assert contract["remediation_order"] == [
        "evidence_and_relevance",
        "approved_rag_corpus",
        "composition_prompt_or_runtime",
        "conditional_adapter_experiment",
    ]
    verification = contract["verification"]
    assert verification["runner"] == "documentation/tools/run_assistant_answer_benchmark_0_9_3.py"
    assert verification["representative_smoke_command"].endswith("--representative-smoke")
    assert "every five seconds" in verification["progress"]
    assert "always unloads the worker" in verification["progress"]
