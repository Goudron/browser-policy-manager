"""Local-only, conservative response-time previews for the documentation assistant.

The preview intentionally exposes only a rounded second range.  It is calculated before a
request starts and never serializes hardware identifiers, prompts, evidence, model output or
measurements outside the current process.
"""

from __future__ import annotations

from collections.abc import Callable
from math import ceil
from typing import Protocol

from app.ai.local_inference_worker import (
    MAX_OUTPUT_TOKENS,
    MODEL_QUANTIZATION,
    WorkerTimingProfile,
)
from app.ai.model_installation import MODEL_ID
from app.ai.runtime_installation import RUNTIME_ID
from app.documentation.assistant_contracts import ConversationTimePreview


class _TimingRequest(Protocol):
    @property
    def question(self) -> str: ...

    @property
    def timing_context_characters(self) -> int: ...

    @property
    def timing_evidence_tokens(self) -> int: ...


class LocalResponseTimeEstimator:
    """Estimate conservatively from local runtime facts and in-process measurements only."""

    # A first request on a small CPU can include model mapping and private runtime extraction.
    _COLD_START_SECONDS_BY_THREADS = ((2, 120.0), (4, 75.0), (8, 45.0))
    _BASE_TOKENS_PER_SECOND_BY_THREADS = ((2, 0.60), (4, 1.00), (8, 1.80))

    def __init__(self, profile_provider: Callable[[], WorkerTimingProfile]) -> None:
        self._profile_provider = profile_provider

    def __call__(self, request: _TimingRequest, *, queued: bool) -> ConversationTimePreview:
        profile = self._profile_provider()
        question_characters = len(request.question) if isinstance(request.question, str) else 0
        context_characters = max(0, int(request.timing_context_characters))
        evidence_tokens = max(0, int(request.timing_evidence_tokens))
        prompt_tokens = self._estimated_prompt_tokens(
            question_characters, context_characters, evidence_tokens
        )
        lower_tokens = min(
            MAX_OUTPUT_TOKENS,
            max(64, 48 + (question_characters + context_characters) // 48),
        )
        # The upper value is the explicit runtime resource cap, never a desired answer length.
        upper_tokens = MAX_OUTPUT_TOKENS
        conservative_tps, optimistic_tps = self._throughput(profile)
        startup_lower, startup_upper = self._startup(profile)
        prompt_seconds = prompt_tokens / max(8.0, optimistic_tps * 12.0)
        lower_seconds = startup_lower + prompt_seconds + lower_tokens / optimistic_tps
        upper_seconds = startup_upper + prompt_seconds + upper_tokens / conservative_tps
        if queued:
            # At most one prior request is admitted.  Its full conservative budget is included.
            upper_seconds += startup_upper + prompt_seconds + upper_tokens / conservative_tps
            lower_seconds += min(30.0, prompt_seconds + lower_tokens / optimistic_tps)
        return ConversationTimePreview(max(1, ceil(lower_seconds)), max(1, ceil(upper_seconds)))

    @classmethod
    def _baseline(cls, profile: WorkerTimingProfile, table: tuple[tuple[int, float], ...]) -> float:
        for maximum_threads, value in table:
            if profile.cpu_threads <= maximum_threads:
                return value
        return table[-1][1]

    def _throughput(self, profile: WorkerTimingProfile) -> tuple[float, float]:
        baseline = self._baseline(profile, self._BASE_TOKENS_PER_SECOND_BY_THREADS)
        measured = profile.rolling_tokens_per_second if self._known_runtime(profile) else None
        if measured is None or measured <= 0:
            conservative_baseline = baseline if self._known_runtime(profile) else baseline * 0.60
            return conservative_baseline, conservative_baseline * 1.6
        # Measurements are discounted so a transient fast response cannot promise an unsafe time.
        return max(0.20, measured * 0.60), max(0.30, measured * 0.90)

    def _startup(self, profile: WorkerTimingProfile) -> tuple[float, float]:
        if not profile.cold_start_required:
            return (0.0, 8.0)
        baseline = self._baseline(profile, self._COLD_START_SECONDS_BY_THREADS)
        observed = profile.last_cold_start_seconds if self._known_runtime(profile) else None
        expected = observed if observed is not None and observed > 0 else baseline
        return (expected * 0.65, expected * 1.50)

    @staticmethod
    def _estimated_prompt_tokens(
        question_characters: int, context_characters: int, evidence_tokens: int
    ) -> int:
        # UTF-8 text is deliberately over-counted here; the exact model tokenizer stays private.
        return max(1, evidence_tokens + ceil((question_characters + context_characters) / 3))

    @staticmethod
    def _known_runtime(profile: WorkerTimingProfile) -> bool:
        """Do not reuse a measurement after a model, quantization or runtime replacement."""

        return (
            profile.model_id == MODEL_ID
            and profile.model_quantization == MODEL_QUANTIZATION
            and profile.runtime_id == RUNTIME_ID
        )


def conservative_default_preview(
    _request: _TimingRequest, *, queued: bool
) -> ConversationTimePreview:
    """Safe fallback for tests and unavailable custom assemblers; it never starts a worker."""

    return ConversationTimePreview(120 if queued else 60, 1_800 if queued else 900)
