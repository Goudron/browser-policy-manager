from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import pytest

from app.documentation.conversation import ConversationOutcome, ConversationRequest
from app.documentation.conversation_stream import (
    ConversationStreamController,
    _ConversationRecord,
)
from app.documentation.response_timing import ConversationTimePreview
from app.documentation.retrieval import LocalCitation


@dataclass
class _Runner:
    outcome: ConversationOutcome | None = None
    error: bool = False

    def ask(self, request: ConversationRequest, **_: object) -> ConversationOutcome:
        if self.error:
            raise RuntimeError("worker failed")
        return self.outcome or ConversationOutcome(
            "abstain", "assistant_no_evidence", request.locale
        )


@dataclass
class _Timer:
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True


def _controller(runner: _Runner | None = None, **kwargs: object) -> ConversationStreamController:
    return ConversationStreamController(
        orchestrator=runner or _Runner(),
        cancel_generation=lambda: True,
        **kwargs,  # type: ignore[arg-type]
    )


def _record(request_id: str = "req_direct") -> _ConversationRecord:
    return _ConversationRecord(request_id, ConversationRequest("en", "BPM question"))


def test_stream_controller_validates_configuration_and_falls_back_for_bad_preview() -> None:
    with pytest.raises(ValueError, match="retention timeout"):
        _controller(request_timeout_seconds=0)
    with pytest.raises(ValueError, match="max_event_buffer"):
        _controller(max_event_buffer=1)

    controller = _controller(
        time_preview_estimator=lambda *_args, **_kwargs: (_ for _ in ()).throw(TypeError())
    )
    assert controller._time_preview(
        ConversationRequest("en", "BPM"), queued=False
    ) == ConversationTimePreview(60, 900)
    value_error_controller = _controller(
        time_preview_estimator=lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError())
    )
    assert value_error_controller._time_preview(
        ConversationRequest("en", "BPM"), queued=True
    ) == ConversationTimePreview(120, 1800)


def test_stream_controller_handles_missing_queued_and_detached_cancellation_safely() -> None:
    controller = _controller()
    active = _record("req_active")
    queued = _record("req_queued")
    detached = _record("req_detached")
    controller._records = {
        active.request_id: active,
        queued.request_id: queued,
        detached.request_id: detached,
    }
    controller._active_request_id = active.request_id
    controller._queued_request_ids = deque([queued.request_id])

    assert controller.poll("missing") == ()
    assert controller.cancel("missing") is False
    assert controller.cancel(queued.request_id) is True
    assert queued.terminal is True and queued.request is None
    assert controller.cancel(detached.request_id) is False


def test_stream_queue_depth_progress_and_timeout_fail_closed_without_a_live_thread() -> None:
    cancellation_calls: list[str] = []
    controller = ConversationStreamController(
        orchestrator=_Runner(),
        cancel_generation=lambda: cancellation_calls.append("cancel") or True,
    )
    active = _record("req_active")
    controller._records[active.request_id] = active

    assert controller.queue_depth_class() == "idle"
    controller._active_request_id = active.request_id
    assert controller.queue_depth_class() == "active"
    controller._queued_request_ids.append("req_queued")
    assert controller.queue_depth_class() == "queued"
    controller._queued_request_ids.clear()

    controller._progress(active.request_id, "unknown")
    controller._progress("missing", "generating")
    controller._timeout("missing")
    controller._timeout(active.request_id)

    assert active.terminal is True
    assert active.state == "error"
    assert cancellation_calls == ["cancel"]


def test_stream_run_translates_worker_failure_cancellation_and_invalid_output_to_terminals() -> (
    None
):
    failing = _controller(_Runner(error=True))
    failed = _record("req_failed")
    failed.timeout_timer = _Timer()  # type: ignore[assignment]
    failing._records[failed.request_id] = failed
    failing._active_request_id = failed.request_id
    failing._run(failed.request_id)

    cancelled = _controller(_Runner(ConversationOutcome("abstain", "assistant_cancelled", "en")))
    cancelled_record = _record("req_cancelled")
    cancelled._records[cancelled_record.request_id] = cancelled_record
    cancelled._active_request_id = cancelled_record.request_id
    cancelled._run(cancelled_record.request_id)
    cancelled._run("missing")

    invalid = _controller()
    invalid_record = _record("req_invalid")
    invalid._final_locked(
        invalid_record,
        ConversationOutcome("invalid", "unexpected", "en"),  # type: ignore[arg-type]
    )

    assert failed.terminal is True and failed.state == "error"
    assert isinstance(failed.timeout_timer, _Timer) and failed.timeout_timer.cancelled is True
    assert cancelled_record.terminal is True and cancelled_record.state == "cancelled"
    assert invalid_record.terminal is True and invalid_record.state == "error"


def test_stream_run_tolerates_a_record_expiring_during_orchestration() -> None:
    controller = _controller()
    record = _record("req_expired")

    class _ExpiringRunner:
        def ask(self, request: ConversationRequest, **_: object) -> ConversationOutcome:
            del request
            controller._records.pop(record.request_id)
            return ConversationOutcome("abstain", "assistant_no_evidence", "en")

    controller._orchestrator = _ExpiringRunner()  # type: ignore[assignment]
    controller._records[record.request_id] = record
    controller._active_request_id = record.request_id
    controller._run(record.request_id)

    assert record.request_id not in controller._records


def test_stream_retention_buffer_and_source_identifiers_are_bounded_and_deduplicated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = _controller(max_event_buffer=2, clock=lambda: 0.0)
    record = _record("req_sources")
    citation = LocalCitation("topic:alpha", "/help/en/user/alpha.html", "alpha", "root")
    different = LocalCitation("topic:beta", "/help/en/user/beta.html", "beta", "root")

    first = controller._source_id_for(record, citation)
    assert controller._source_id_for(record, citation) == first
    tokens = iter((first.removeprefix("src_"), "different"))
    monkeypatch.setattr(
        "app.documentation.conversation_stream.secrets.token_urlsafe",
        lambda _: next(tokens),
    )
    second = controller._source_id_for(record, different)
    assert second != first

    for index in range(3):
        controller._emit_locked(record, "progress", "generating", f"reason-{index}", "message", "")
    assert len(record.events) == 2

    controller._records = {
        f"req_completed_{index}": _ConversationRecord(
            f"req_completed_{index}", None, terminal=True, completed_at=float(index)
        )
        for index in range(5)
    }
    controller._prune_completed_locked()

    assert len(controller._records) == 4


def test_stream_completes_non_answer_without_sources_and_skips_missing_queued_successor() -> None:
    controller = _controller()
    record = _record("req_complete")
    controller._final_locked(
        record, ConversationOutcome("clarify", "assistant_clarify", "en", "ignored")
    )
    controller._records[record.request_id] = record
    controller._active_request_id = record.request_id
    controller._queued_request_ids.append("req_missing")
    controller._complete_active_locked(record)
    controller._complete_active_locked(_record("req_not_active"))

    assert record.events[-1].source_ids == ()
    assert controller._active_request_id is None


def test_stream_shutdown_cancels_owned_work_and_clears_all_content_bearing_records() -> None:
    cancellation_calls: list[str] = []
    controller = ConversationStreamController(
        orchestrator=_Runner(),
        cancel_generation=lambda: cancellation_calls.append("cancel") or True,
    )
    active = _record("req_active")
    active.timeout_timer = _Timer()  # type: ignore[assignment]
    queued = _record("req_queued")
    queued.timeout_timer = _Timer()  # type: ignore[assignment]
    without_timer = _record("req_without_timer")
    controller._records = {
        active.request_id: active,
        queued.request_id: queued,
        without_timer.request_id: without_timer,
    }
    controller._active_request_id = active.request_id
    controller._queued_request_ids.append(queued.request_id)

    controller.shutdown()

    assert cancellation_calls == ["cancel"]
    assert not controller._records
    assert not controller._queued_request_ids
    assert controller._active_request_id is None
    assert active.cancellation_requested.is_set() and queued.cancellation_requested.is_set()
    assert isinstance(active.timeout_timer, _Timer) and active.timeout_timer.cancelled is True
    assert isinstance(queued.timeout_timer, _Timer) and queued.timeout_timer.cancelled is True
    assert without_timer.cancellation_requested.is_set()
    assert controller.retains(active.request_id) is False
    controller.shutdown()
    assert cancellation_calls == ["cancel"]
