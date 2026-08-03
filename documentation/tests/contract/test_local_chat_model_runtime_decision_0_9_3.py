from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DECISION_PATH = ROOT / "documentation/config/local-chat-model-runtime-decision-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _decision() -> dict:
    return json.loads(DECISION_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_m6_04a_selects_the_exact_0_6b_artifact_under_the_explicit_policy() -> None:
    decision = _decision()

    assert decision["backlog_item"] == "BPM093-M6-04"
    assert decision["status"] == "maintainer-selected-under-best-effort-latency-policy"
    assert (
        decision["model_decision"]["production_selected_candidate"]
        == "qwen3-0.6b-q8_0-official-gguf"
    )

    fallback = decision["model_decision"]["comparative_fallback"]
    assert fallback["id"] == "qwen3-0.6b-q8_0-official-gguf"
    assert (
        fallback["artifact_sha256"]
        == "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
    )
    assert fallback["complete_compact_matrix"]["durable_records"] == 27
    assert fallback["complete_compact_matrix"]["benchmark_status"] == "fail"
    assert "warm:ttft" in " ".join(fallback["complete_compact_matrix"]["failures"])
    assert "explicit opt-in installation" in fallback["disposition"]


def test_m6_04_pins_decisions_and_rejects_the_larger_candidate_on_observed_hard_gates() -> None:
    decision = _decision()

    for pin in decision["pins"].values():
        assert _sha256(ROOT / pin["path"]) == pin["sha256"]

    assert decision["runtime"]["id"] == "llama.cpp-b9637-linux-x64-cpu"
    assert decision["runtime"]["required_flags"] == [
        "--offline",
        "--device",
        "none",
        "--grammar",
        "--no-show-timings",
        "--jinja",
        "--reasoning",
        "off",
        "--simple-io",
    ]
    assert decision["inference_profile"]["reasoning_mode"].startswith("non-thinking")

    rejected = decision["model_decision"]["rejected_candidates"][0]
    sample = rejected["measured_early_rejection"]
    assert rejected["id"] == "qwen3-1.7b-q8_0-official-gguf"
    assert sample["ttft_ms"] > 30000
    assert sample["completion_ms"] > 60000
    assert sample["tokens_per_second"] < 3.0
    assert "could not change a hard rejection" in sample["reason"]


def test_m6_04a_preserves_chat_only_retrieval_and_the_explicit_install_boundary() -> None:
    decision = _decision()

    retrieval = decision["retrieval_boundary"]
    assert retrieval["embedding_model"] == "multilingual-e5-base-onnx-o4"
    assert "not called, changed, reranked, or replaced" in retrieval["ordinary_search"]
    assert retrieval["cross_locale_retrieval"] == "forbidden"
    assert "disabled by default" in retrieval["optional_external_evidence"]

    blocker = decision["release_blocker"]
    assert blocker["status"] == "superseded-by-m6-04a-performance-policy"
    assert blocker["resolution_backlog_item"] == "BPM093-M6-04A"
    assert any(
        "M6-05 may implement explicit verified installation" in effect
        for effect in blocker["effect"]
    )
    assert any("M6-06 owns the bounded worker only" in effect for effect in blocker["effect"])
    assert any(
        "M7/M8 controller work owns any chat route" in effect for effect in blocker["effect"]
    )
    assert "requires an explicit new decision" in blocker["resolution_rule"]
    assert (
        "do not start, download, or retry a model"
        in decision["no_model_fallback"]["current_product_behavior"]
    )
    assert decision["verification"]["product_runtime_change"] is False

    policy = decision["performance_policy"]
    assert policy["backlog_item"] == "BPM093-M6-04A"
    assert policy["status"] == "maintainer-accepted-no-rerun"
    assert policy["no_rerun"] is True
    assert "no fixed target-laptop promise" in policy["user_visible_promise"]
    assert policy["excluded_candidate_rule"].startswith("The amendment does not select Qwen3 1.7B")
