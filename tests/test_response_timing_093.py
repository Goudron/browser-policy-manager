from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.ai.local_inference_worker import WorkerTimingProfile
from app.documentation.response_timing import (
    ConversationTimePreview,
    LocalResponseTimeEstimator,
    conservative_default_preview,
)


@dataclass(frozen=True)
class _Request:
    question: str
    timing_context_characters: int = 0
    timing_evidence_tokens: int = 2_048


def _estimator(profile: WorkerTimingProfile) -> LocalResponseTimeEstimator:
    return LocalResponseTimeEstimator(lambda: profile)


def test_time_preview_covers_slow_cold_and_fast_warm_local_completion_without_network() -> None:
    slow = WorkerTimingProfile(
        cpu_threads=2,
        model_id="qwen3-0.6b-q8_0-official-gguf",
        model_quantization="Q8_0",
        runtime_id="llama.cpp-b9637-linux-x64-cpu",
        cold_start_required=True,
        last_cold_start_seconds=120.0,
        rolling_tokens_per_second=0.6,
    )
    fast = WorkerTimingProfile(
        cpu_threads=8,
        model_id="qwen3-0.6b-q8_0-official-gguf",
        model_quantization="Q8_0",
        runtime_id="llama.cpp-b9637-linux-x64-cpu",
        cold_start_required=False,
        last_cold_start_seconds=30.0,
        rolling_tokens_per_second=10.0,
    )
    request = _Request("How do I configure a supported Browser Policy Manager policy?", 1_200)

    slow_preview = _estimator(slow)(request, queued=False)
    fast_preview = _estimator(fast)(request, queued=False)

    # Representative observed completions must fit inside the deliberately conservative range.
    assert slow_preview.minimum_seconds <= 1_000 <= slow_preview.maximum_seconds
    assert fast_preview.minimum_seconds <= 90 <= fast_preview.maximum_seconds
    assert fast_preview.maximum_seconds < slow_preview.maximum_seconds


def test_queued_preview_accounts_for_one_prior_request_and_uses_all_bounded_inputs() -> None:
    profile = WorkerTimingProfile(
        cpu_threads=4,
        model_id="qwen3-0.6b-q8_0-official-gguf",
        model_quantization="Q8_0",
        runtime_id="llama.cpp-b9637-linux-x64-cpu",
        cold_start_required=True,
        last_cold_start_seconds=None,
        rolling_tokens_per_second=None,
    )
    estimator = _estimator(profile)
    short = _Request("BPM?", 0, 512)
    detailed = _Request("Explain the supported BPM configuration in detail.", 8_000, 2_048)

    direct = estimator(short, queued=False)
    queued = estimator(detailed, queued=True)

    assert direct.minimum_seconds >= 1
    assert direct.maximum_seconds >= direct.minimum_seconds
    assert queued.maximum_seconds > direct.maximum_seconds
    assert "http" not in (LocalResponseTimeEstimator.__module__ + __file__)


def test_preview_rejects_invalid_ranges_and_caps_the_thread_baseline() -> None:
    with pytest.raises(ValueError, match="invalid local response-time range"):
        ConversationTimePreview(0, 1)
    with pytest.raises(ValueError, match="invalid local response-time range"):
        ConversationTimePreview(2, 1)

    profile = WorkerTimingProfile(
        cpu_threads=64,
        model_id="unrecognized-model",
        model_quantization="unknown",
        runtime_id="unknown",
        cold_start_required=True,
        last_cold_start_seconds=1.0,
        rolling_tokens_per_second=5.0,
    )

    assert _estimator(profile)._baseline(profile, ((2, 1.0), (8, 2.0))) == 2.0


def test_default_preview_remains_bounded_for_direct_and_queued_requests() -> None:
    request = _Request("BPM?")

    assert conservative_default_preview(request, queued=False) == ConversationTimePreview(60, 900)
    assert conservative_default_preview(request, queued=True) == ConversationTimePreview(120, 1_800)
