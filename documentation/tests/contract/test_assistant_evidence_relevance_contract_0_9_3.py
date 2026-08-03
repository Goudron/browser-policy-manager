from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/assistant-evidence-relevance-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m13_03_pins_six_locale_pre_generation_relevance_to_approved_boundaries() -> None:
    contract = _contract()

    assert contract["contract_id"] == "bpm-assistant-evidence-relevance-0.9.3"
    assert contract["backlog_item"] == "BPM093-M13-03"
    assert contract["status"] == "implemented-deterministic-pre-generation-gate"
    assert contract["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    for pin in contract["pins"].values():
        assert hashlib.sha256((ROOT / pin["path"]).read_bytes()).hexdigest() == pin["sha256"]


def test_m13_03_requires_every_explicit_context_dimension_and_fails_before_generation() -> None:
    contract = _contract()

    assert contract["placement"]["pipeline"] == [
        "exact_same_locale_retrieval",
        "deterministic_relevance_gate",
        "evidence_pack",
        "generation_or_terminal_abstention",
    ]
    assert "maximum remains five" in contract["placement"]["candidate_window"]
    assert "assistant_relevance_no_matching_evidence" in contract["placement"]["terminal"]
    assert contract["dimensions"]["required"] == [
        "topic",
        "named_entities",
        "operating_system_or_distribution",
        "release",
        "reader_role",
        "bpm_version",
        "locale",
    ]
    assert "cannot override a conflicting platform" in contract["dimensions"]["rule"]
    assert "Ubuntu 26.04" in contract["regressions"]["ubuntu"]
    assert "Debian 13.5 is incompatible" in contract["regressions"]["ubuntu"]
    assert "rather than silently substituting" in contract["regressions"]["general"]
    assert contract["boundaries"] == {
        "network_calls": 0,
        "ordinary_search_calls": 0,
        "cross_locale_retrieval_calls": 0,
        "model_invocations_for_rejected_evidence": 0,
        "external_provider_calls_for_rejected_evidence": 0,
        "telemetry": False,
        "generated_answer_or_source_for_rejected_evidence": False,
    }
