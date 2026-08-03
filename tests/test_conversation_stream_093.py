from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from app.documentation.conversation import (
    ConversationExternalClaim,
    ConversationOutcome,
    ConversationRequest,
)
from app.documentation.conversation_stream import ConversationStreamController
from app.documentation.response_timing import ConversationTimePreview
from app.documentation.retrieval import LocalCitation
from app.documentation.web_evidence import ExternalWebCitation


@dataclass
class ControlledOrchestrator:
    """A deterministic stand-in that exposes lifecycle and cancellation ordering."""

    release: threading.Event = field(default_factory=threading.Event)
    started: list[str] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)

    def ask(
        self,
        request: ConversationRequest,
        *,
        lifecycle_callback: Callable[[str], None] | None = None,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> ConversationOutcome:
        self.started.append(request.question)
        for phase in ("scope_check", "evidence_check", "generating", "validating"):
            if lifecycle_callback is not None:
                lifecycle_callback(phase)
        while not self.release.wait(0.002):
            if cancellation_check is not None and cancellation_check():
                self.completed.append(request.question)
                return ConversationOutcome("abstain", "assistant_cancelled", request.locale)
        self.completed.append(request.question)
        citation = LocalCitation("topic:alpha", "/help/en/user/alpha.html", "alpha", "root")
        return ConversationOutcome(
            "answer", "assistant_grounded_answer", request.locale, "Safe answer.", (citation,)
        )


def _wait_until(predicate: Callable[[], bool], timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.002)
    raise AssertionError("timed out waiting for conversation controller")


def test_controller_streams_safe_lifecycle_then_opaque_final_source_handle() -> None:
    third_orchestrator = ControlledOrchestrator()
    third_orchestrator.release.set()
    retained = ConversationStreamController(
        orchestrator=third_orchestrator, cancel_generation=lambda: False
    )
    third = retained.submit(ConversationRequest("en", "Which policies are supported?"))
    assert third.request_id is not None
    _wait_until(lambda: third_orchestrator.completed == ["Which policies are supported?"])
    events = retained.poll(third.request_id)

    assert [event.event_type for event in events] == [
        "accepted",
        "progress",
        "progress",
        "progress",
        "progress",
        "final",
    ]
    assert [event.state for event in events] == [
        "accepted",
        "scope_check",
        "evidence_check",
        "generating",
        "validating",
        "answer",
    ]
    final = events[-1]
    assert final.text == "Safe answer."
    assert final.source_ids and final.source_ids[0].startswith("src_")
    assert "topic:alpha" not in str(final)
    assert retained.source(third.request_id, final.source_ids[0]) is not None


def test_controller_returns_an_immediate_local_time_preview_without_waiting_for_generation() -> None:
    orchestrator = ControlledOrchestrator()
    observed: list[tuple[int, int, bool]] = []

    def preview(request: ConversationRequest, *, queued: bool) -> ConversationTimePreview:
        observed.append(
            (request.timing_context_characters, request.timing_evidence_tokens, queued)
        )
        return ConversationTimePreview(95, 245)

    controller = ConversationStreamController(
        orchestrator=orchestrator,
        cancel_generation=lambda: False,
        time_preview_estimator=preview,
    )

    admission = controller.submit(
        ConversationRequest("ru", "Как настроить BPM?", timing_context_characters=900)
    )

    assert admission.time_preview == ConversationTimePreview(95, 245)
    assert observed == [(900, 2_048, False)]
    controller.cancel(admission.request_id or "")


def test_controller_serializes_one_active_one_queued_and_rejects_excess_work() -> None:
    orchestrator = ControlledOrchestrator()
    controller = ConversationStreamController(
        orchestrator=orchestrator, cancel_generation=lambda: False
    )

    first = controller.submit(ConversationRequest("en", "first"))
    assert first.request_id is not None
    _wait_until(lambda: orchestrator.started == ["first"])
    second = controller.submit(ConversationRequest("en", "second"))
    third = controller.submit(ConversationRequest("en", "third"))

    assert second.request_id is not None
    assert second.reason_code == "assistant_queued"
    assert third.request_id is None
    assert third.reason_code == "assistant_busy"
    assert orchestrator.started == ["first"]

    orchestrator.release.set()
    _wait_until(lambda: orchestrator.started == ["first", "second"])


def test_cancel_and_disconnect_emit_one_incomplete_terminal_and_release_the_worker() -> None:
    orchestrator = ControlledOrchestrator()
    cancellation_calls: list[str] = []
    controller = ConversationStreamController(
        orchestrator=orchestrator,
        cancel_generation=lambda: cancellation_calls.append("cancel") or True,
    )
    active = controller.submit(ConversationRequest("en", "active"))
    assert active.request_id is not None
    _wait_until(lambda: orchestrator.started == ["active"])

    assert controller.disconnect(active.request_id)
    assert controller.cancel(active.request_id)
    _wait_until(lambda: orchestrator.completed == ["active"])
    events = controller.poll(active.request_id)

    terminal = [event for event in events if event.event_type == "cancelled"]
    assert len(terminal) == 1
    assert terminal[0].state == "cancelled"
    assert terminal[0].incomplete is True
    assert terminal[0].text == ""
    assert cancellation_calls == ["cancel"]

    successor = controller.submit(ConversationRequest("en", "next question"))
    assert successor.request_id is not None
    _wait_until(lambda: orchestrator.started == ["active", "next question"])
    orchestrator.release.set()
    _wait_until(lambda: orchestrator.completed == ["active", "next question"])


def test_timeout_cancels_the_worker_and_does_not_turn_late_output_into_an_answer() -> None:
    orchestrator = ControlledOrchestrator()
    cancellation_calls: list[str] = []
    controller = ConversationStreamController(
        orchestrator=orchestrator,
        cancel_generation=lambda: cancellation_calls.append("timeout") or True,
        request_timeout_seconds=0.01,
    )
    admission = controller.submit(ConversationRequest("en", "slow"))
    assert admission.request_id is not None
    _wait_until(lambda: orchestrator.started == ["slow"])
    _wait_until(lambda: cancellation_calls == ["timeout"])
    _wait_until(lambda: orchestrator.completed == ["slow"])

    events = controller.poll(admission.request_id)
    terminal = [event for event in events if event.event_type in {"final", "cancelled", "error"}]
    assert len(terminal) == 1
    assert terminal[0].event_type == "error"
    assert terminal[0].reason_code == "assistant_timeout"
    assert terminal[0].incomplete is True


def test_completed_stream_record_drops_request_content_and_expires_source_handles() -> None:
    now = 0.0
    orchestrator = ControlledOrchestrator()
    orchestrator.release.set()
    controller = ConversationStreamController(
        orchestrator=orchestrator,
        cancel_generation=lambda: False,
        completed_retention_seconds=5.0,
        clock=lambda: now,
    )
    admission = controller.submit(ConversationRequest("en", "private question"))
    assert admission.request_id is not None
    _wait_until(lambda: orchestrator.completed == ["private question"])

    events = controller.poll(admission.request_id)
    source_id = events[-1].source_ids[0]

    assert controller._records[admission.request_id].request is None
    assert not controller._records[admission.request_id].events
    assert controller.source(admission.request_id, source_id) is not None
    now = 5.0
    assert controller.source(admission.request_id, source_id) is None


def test_external_claims_receive_separate_opaque_source_handles() -> None:
    class ExternalOrchestrator:
        def ask(
            self,
            request: ConversationRequest,
            *,
            lifecycle_callback: Callable[[str], None] | None = None,
            cancellation_check: Callable[[], bool] | None = None,
        ) -> ConversationOutcome:
            del lifecycle_callback, cancellation_check
            local = LocalCitation(
                "topic:alpha", "/help/en/user/alpha.html", "alpha", "root"
            )
            external = ExternalWebCitation(
                "web:mozilla",
                "brave-search-llm-context",
                "https://mozilla.github.io/policy-templates/README.md",
                "Mozilla policy templates",
                ("2026-07-29",),
                "2026-07-30T00:00:00+00:00",
                locale="en",
            )
            return ConversationOutcome(
                "answer",
                "assistant_merged_answer_validated",
                request.locale,
                "Local BPM answer.",
                (local,),
                (ConversationExternalClaim("External Firefox note.", (external,)),),
            )

    controller = ConversationStreamController(
        orchestrator=ExternalOrchestrator(),  # type: ignore[arg-type]
        cancel_generation=lambda: False,
    )
    admission = controller.submit(ConversationRequest("en", "BPM question"))
    assert admission.request_id is not None
    _wait_until(lambda: controller._records[admission.request_id].terminal)
    final = controller.poll(admission.request_id)[-1]

    assert final.text == "Local BPM answer."
    assert len(final.source_ids) == 1
    assert len(final.external_claims) == 1
    external_source_id = final.external_claims[0].source_ids[0]
    assert external_source_id not in final.source_ids
    assert isinstance(
        controller.source(admission.request_id, external_source_id),
        ExternalWebCitation,
    )
