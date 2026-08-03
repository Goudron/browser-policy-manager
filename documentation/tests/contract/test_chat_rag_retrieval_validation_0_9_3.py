from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/chat-rag-retrieval-validation-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_retrieval_validation_contract_pins_active_runtime_inputs() -> None:
    config = _config()

    assert config["contract_id"] == "bpm-chat-rag-retrieval-validation-0.9.3"
    assert config["backlog_item"] == "BPM093-M5-08"
    assert config["status"] == "accepted-active-generation-validation-contract"
    for entry in config["contracts"].values():
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    corpus = config["inputs"]["evaluation_corpus"]
    assert hashlib.sha256((ROOT / corpus["path"]).read_bytes()).hexdigest() == corpus["sha256"]


def test_retrieval_validation_is_six_locale_citable_and_non_hybrid() -> None:
    config = _config()

    assert config["inputs"]["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert config["inputs"]["top_k"] == 5
    assert config["inputs"]["answer_and_dialogue_cases_per_locale"] == 20
    assert "before embedding" in config["inputs"]["no_evidence_rule"]
    assert config["boundaries"] == {
        "network_calls_after_install": 0,
        "ordinary_search_calls": 0,
        "cross_locale_retrieval_calls": 0,
        "answer_generation_invocations": 0,
        "external_evidence": "disabled and absent",
        "swap": "Observed as an operational diagnostic only; it is not a validity or release condition.",
        "output": "Write reports only under ignored documentation/.cache/bpm093-m5-08/.",
    }
    assert config["acceptance"]["citation_resolution_rate_min"] == 1.0
    assert config["acceptance"]["published_chunk_coverage_rate_min"] == 1.0
    assert config["acceptance"]["published_topic_coverage_rate_min"] == 1.0
    assert config["acceptance"]["reproducible_ranking_rate_min"] == 1.0


def test_retrieval_validation_has_real_stdout_progress_and_negative_runtime_evidence() -> None:
    config = _config()

    assert config["progress"] == {
        "stream": "stdout",
        "flush": True,
        "locale_case_update": 5,
        "latency_sample_update": 5,
        "content": "real runtime preparation, source/generation verification, locale-local evaluated-case completion, and measured latency samples; no synthetic progress or ETA",
    }
    assert config["integrity_and_recovery"]["negative_runtime_tests"] == [
        "tests/test_documentation_chat_retrieval_093.py",
        "tests/test_documentation_evidence_packing_093.py",
    ]
    assert "never import, call, modify" in config["integrity_and_recovery"]["failure_isolation"]
