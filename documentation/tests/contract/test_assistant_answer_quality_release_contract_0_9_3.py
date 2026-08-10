from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "documentation/config/assistant-answer-quality-release-contract-0.9.3.json"

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_m13_01_freezes_complete_grounded_relevant_answers() -> None:
    contract = _contract()

    assert contract["answer_contract"]["order"] == [
        "complete_grounded_generated_answer",
        "zero_or_more_deduplicated_relevant_local_sources",
    ]
    assert "must not silently shorten it" in contract["answer_contract"]["completeness"]
    assert (
        "raw evidence excerpts and raw model output are never substituted"
        in contract["answer_contract"]["validation"]
    )
    assert "exactly one isolated local rewrite" in contract["answer_contract"]["validation"]
    benchmark = contract["benchmark"]
    assert "ten approved support intents" in benchmark["local"]
    assert "EN/RU prompts (20 cases)" in benchmark["local"]
    assert "never permits cross-locale retrieval" in benchmark["local"]
    assert "Deferred beyond 0.9.3" in benchmark["external"]
    assert "no external-source benchmark" in benchmark["external"]
    assert "Correct evidence/relevance first" in benchmark["remediation"]

    relevance = contract["universal_relevance"]
    assert relevance["dimensions"] == [
        "topic",
        "named_entities",
        "operating_system_or_distribution",
        "release",
        "reader_role",
        "bpm_version",
        "locale",
    ]
    assert "never silently substituted" in relevance["rule"]
    assert "Ubuntu 26.04" in relevance["regression_fixture"]
    assert "Debian 13.5 evidence is incompatible" in relevance["regression_fixture"]


def test_m13_01_freezes_eight_turns_timing_sources_and_geometry() -> None:
    contract = _contract()

    conversation = contract["conversation"]
    assert conversation["scope"] == "One browser tab, one exact locale and one BPM version."
    assert (
        "newest eight completed user-question/assistant-answer pairs" in conversation["retention"]
    )
    assert "ninth completed pair deterministically evicts the oldest" in conversation["retention"]
    assert "never block a later request" in conversation["follow_up"]
    assert "never sent to an external provider" in conversation["external_boundary"]

    timing = contract["time_preview"]
    assert "Expected time: from N minutes S seconds to M minutes T seconds" in timing["display"]
    assert timing["inputs"] == [
        "safe_local_hardware_and_runtime_profile",
        "installed_model_identity_and_quantization",
        "cold_or_warm_start",
        "prompt_and_retained_context_size",
        "selected_evidence_size",
        "predicted_answer_token_range",
        "rolling_local_generation_throughput",
    ]
    assert "whole seconds" in timing["calibration"]
    assert "no network, telemetry or stable hardware identifier" in timing["calibration"]
    assert "must not be used to truncate" in timing["honesty"]

    surface = contract["sources_and_viewport"]
    assert "same-window links" in surface["local_links"]
    assert "deferred beyond 0.9.3" in surface["external_links"]
    assert surface["desktop_panel"].startswith(
        "The expanded lower-right assistant overlay is 50vw wide and 90dvh high"
    )


def test_m13_01_maps_each_remaining_quality_task_to_one_implementation_step() -> None:
    contract = _contract()

    assert list(contract["implementation_sequence"]) == [
        "BPM093-M13-02",
        "BPM093-M13-03",
        "BPM093-M13-04",
        "BPM093-M13-05",
        "BPM093-M13-06",
        "BPM093-M13-06A",
        "BPM093-M13-06B",
        "BPM093-M13-06C",
        "BPM093-M13-07",
        "BPM093-M13-07A",
        "BPM093-M13-08",
        "BPM093-M13-09",
        "BPM093-M13-10",
        "BPM093-M13-11",
    ]
    assert (
        "no route, model invocation, generated answer, provider call or browser mutation"
        in contract["verification"]["implementation"]
    )
