from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "documentation/config/chat-rag-embedding-benchmark-0.9.3.json"
RUNNER_PATH = ROOT / "documentation/tools/run_chat_rag_embedding_benchmark_0_9_3.py"
TOOLS_ROOT = ROOT / "documentation/tools"

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

SPEC = importlib.util.spec_from_file_location("chat_rag_embedding_benchmark", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

pytestmark = pytest.mark.docs_contract


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_chat_benchmark_contract_reuses_only_pinned_candidates_and_excludes_cross_locale_retrieval() -> (
    None
):
    config = _config()

    assert config["backlog_item"] == "BPM093-M5-03C"
    assert config["selection_contract"]["path"].endswith(
        "chat-rag-embedding-selection-contract-0.9.3.json"
    )
    assert "no cross-language probe" in config["inputs"]["retrieval_mode"]
    assert config["inputs"]["top_k"] == 5
    assert config["protocol"]["validity"]["swap_must_not_change"] is True
    assert {candidate["id"] for candidate in config["candidates"]} == {
        "multilingual-e5-small-onnx-o4",
        "multilingual-e5-base-onnx-o4",
    }
    assert all(len(candidate["source_contract_sha256"]) == 64 for candidate in config["candidates"])


def test_chat_cases_are_same_locale_and_include_answer_dialogue_but_not_cross_language() -> None:
    cases = runner._answer_cases()

    assert len(cases) == 120
    assert {case.locale for case in cases} == set(runner.LOCALES)
    assert all(case.query_class in {"answer_question", "dialogue_answer"} for case in cases)
    assert sum(case.query_class == "dialogue_answer" for case in cases) == 24
    no_evidence = runner._no_evidence_cases()
    assert {locale: len(queries) for locale, queries in no_evidence.items()} == {
        locale: 4 for locale in runner.LOCALES
    }


def test_metadata_no_evidence_and_status_fail_closed() -> None:
    chunks = [{"identifiers": ["API-VAL-001", "topic:example"]}]
    assert runner._metadata_no_evidence("What does API-UNKNOWN-999 do?", chunks) is True
    assert runner._metadata_no_evidence("API-VAL-001", chunks) is False
    config = _config()
    report = {
        "validity": {"valid": False, "reasons": ["swap-changed-during-measurement"]},
        "per_locale": {
            locale: {
                "evidence_coverage_at_5": 1.0,
                "citation_resolution_rate": 1.0,
                "no_evidence_disposition_rate": 1.0,
            }
            for locale in runner.LOCALES
        },
        "resources": {"direct_disk_gib": 0.1, "peak_rss_gib": 0.1},
        "latency": {"p95_ms_max": 1.0},
    }
    assert runner._candidate_status(report, config) == ("fail", ["swap-changed-during-measurement"])
