from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DECISION_PATH = ROOT / "documentation/config/chat-rag-embedding-decision-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _decision() -> dict:
    return json.loads(DECISION_PATH.read_text(encoding="utf-8"))


def test_e5_base_acceptance_is_explicit_and_does_not_rewrite_the_failed_selector() -> None:
    decision = _decision()

    assert decision["backlog_item"] == "BPM093-M5-03C"
    assert decision["status"] == "maintainer-accepted"
    assert decision["selected_candidate"]["id"] == "multilingual-e5-base-onnx-o4"
    assert decision["selected_candidate"]["artifact_sha256"] == (
        "f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703"
    )
    assert decision["benchmark_evidence"]["selector_result"] == "fail"
    assert decision["benchmark_evidence"]["selector_selected"] is None
    assert decision["benchmark_evidence"]["not_a_benchmark_pass"] is True
    assert "no longer a selection or release blocker" in decision["resource_policy_amendment"]["effect"]


def test_e5_base_implementation_is_chat_only_and_clean_host_validation_remains_release_blocking() -> None:
    decision = _decision()

    boundary = decision["implementation_boundary"]
    assert boundary["chat_only"] is True
    assert "not called, changed, ranked against, or replaced" in boundary["ordinary_search"]
    assert boundary["cross_locale_retrieval"] == "forbidden"
    assert "disabled by default" in boundary["optional_external_evidence"]

    release = decision["release_blocker"]
    assert release["backlog_item"] == "BPM093-M5-03D"
    assert release["status"] == "retired-no-swap-gate"
    assert "no longer a release blocker" in release["requirement"]
    assert "Do not change M4 ordinary search" in release["failure_disposition"]
