"""Bounded in-memory event controller for validated documentation-chat outcomes.

This is deliberately transport-neutral: M10 owns the same-origin HTTP/SSE route and browser UI.
The controller serializes the old-laptop worker, supplies safe lifecycle events, and makes stop or
disconnect cancellation visible without ever exposing raw model tokens or implementation details.
"""

from __future__ import annotations

import secrets
import threading
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic
from typing import Literal, Protocol

from app.documentation.assistant_contracts import (
    ConversationAdmission,
    ConversationRequest,
    ConversationStreamEvent,
    ConversationStreamExternalClaim,
    ConversationTimePreview,
    EventType,
    RequestState,
)
from app.documentation.conversation import (
    AnswerDisposition,
    ConversationOutcome,
)
from app.documentation.response_timing import (
    conservative_default_preview,
)

API_VERSION = 1
MAX_ACTIVE_REQUESTS = 1
MAX_QUEUED_REQUESTS = 1
MAX_EVENT_BUFFER = 8
MAX_COMPLETED_REQUESTS = 4
COMPLETED_RECORD_RETENTION_SECONDS = 15 * 60.0
REQUEST_TIMEOUT_SECONDS = 1_200.0


class ConversationRunner(Protocol):
    """The orchestration boundary with optional cancellation and lifecycle notifications."""

    def ask(
        self,
        request: ConversationRequest,
        *,
        lifecycle_callback: Callable[[str], None] | None = None,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> ConversationOutcome: ...


@dataclass
class _ConversationRecord:
    request_id: str
    request: ConversationRequest | None
    events: deque[ConversationStreamEvent] = field(default_factory=deque)
    sources: dict[str, object] = field(default_factory=dict)
    cancellation_requested: threading.Event = field(default_factory=threading.Event)
    state: RequestState = "accepted"
    state_epoch: int = 0
    terminal: bool = False
    timeout_timer: threading.Timer | None = None
    completed_at: float | None = None


class ConversationStreamController:
    """Serialize local conversations and retain only a small, safe event window in memory."""

    def __init__(
        self,
        *,
        orchestrator: ConversationRunner,
        cancel_generation: Callable[[], bool],
        request_timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        max_event_buffer: int = MAX_EVENT_BUFFER,
        completed_retention_seconds: float = COMPLETED_RECORD_RETENTION_SECONDS,
        clock: Callable[[], float] = monotonic,
        time_preview_estimator: Callable[
            ..., ConversationTimePreview
        ] = conservative_default_preview,
    ) -> None:
        if request_timeout_seconds <= 0 or completed_retention_seconds <= 0:
            raise ValueError("conversation retention timeout must be positive")
        if max_event_buffer < 2:
            raise ValueError("max_event_buffer must reserve accepted and terminal events")
        self._orchestrator = orchestrator
        self._cancel_generation = cancel_generation
        self._request_timeout_seconds = request_timeout_seconds
        self._max_event_buffer = max_event_buffer
        self._completed_retention_seconds = completed_retention_seconds
        self._clock = clock
        self._time_preview_estimator = time_preview_estimator
        self._lock = threading.RLock()
        self._records: dict[str, _ConversationRecord] = {}
        self._active_request_id: str | None = None
        self._queued_request_ids: deque[str] = deque()

    def submit(self, request: ConversationRequest) -> ConversationAdmission:
        """Accept one active and one queued request; reject excess work before it allocates a worker."""

        with self._lock:
            self._expire_completed_locked()
            if (
                self._active_request_id is not None
                and len(self._queued_request_ids) >= MAX_QUEUED_REQUESTS
            ):
                return ConversationAdmission(None, "error", "assistant_busy", 0)
            request_id = self._new_request_id()
            record = _ConversationRecord(request_id=request_id, request=request)
            self._records[request_id] = record
            queued = self._active_request_id is not None
            time_preview = self._time_preview(request, queued=queued)
            self._emit_locked(
                record,
                "accepted",
                "accepted",
                "assistant_queued" if queued else "assistant_accepted",
                "assistant_chat_queued" if queued else "assistant_chat_accepted",
                "assistant_chat_cancel",
            )
            if queued:
                self._queued_request_ids.append(request_id)
            else:
                self._start_locked(record)
            return ConversationAdmission(
                request_id,
                record.state,
                "assistant_queued" if queued else "assistant_accepted",
                record.state_epoch,
                time_preview=time_preview,
            )

    def _time_preview(
        self, request: ConversationRequest, *, queued: bool
    ) -> ConversationTimePreview:
        """Keep admission fast even if a future estimator rejects malformed local input."""

        try:
            return self._time_preview_estimator(request, queued=queued)
        except TypeError:
            return conservative_default_preview(request, queued=queued)
        except ValueError:
            return conservative_default_preview(request, queued=queued)

    def poll(self, request_id: str) -> tuple[ConversationStreamEvent, ...]:
        """Return and consume the bounded pending event window for one opaque request."""

        with self._lock:
            self._expire_completed_locked()
            record = self._records.get(request_id)
            if record is None:
                return ()
            events = tuple(record.events)
            record.events.clear()
            return events

    def cancel(self, request_id: str) -> bool:
        """Idempotently cancel an active or queued request; the worker is never replaced."""

        with self._lock:
            self._expire_completed_locked()
            record = self._records.get(request_id)
            if record is None:
                return False
            if record.terminal:
                return True
            record.cancellation_requested.set()
            if request_id in self._queued_request_ids:
                self._queued_request_ids.remove(request_id)
                self._terminal_locked(record, "cancelled", "assistant_cancelled", incomplete=True)
                record.request = None
                return True
            if request_id == self._active_request_id:
                self._terminal_locked(record, "cancelled", "assistant_cancelled", incomplete=True)
            else:
                return False
        self._cancel_generation()
        return True

    def disconnect(self, request_id: str) -> bool:
        """A disconnected stream has the same stop semantics as an explicit cancellation."""

        return self.cancel(request_id)

    def source(self, request_id: str, source_id: str) -> object | None:
        """Resolve only a completed request's opaque citation handle for the future route owner."""

        with self._lock:
            self._expire_completed_locked()
            record = self._records.get(request_id)
            if record is None or not record.terminal:
                return None
            return record.sources.get(source_id)

    def retains(self, request_id: str) -> bool:
        """Report whether an opaque request handle remains valid without returning its contents."""

        with self._lock:
            self._expire_completed_locked()
            return request_id in self._records

    def shutdown(self) -> None:
        """Cancel active work and release every controller-owned record during app shutdown."""

        with self._lock:
            active = self._active_request_id is not None
            records = tuple(self._records.values())
            self._records.clear()
            self._queued_request_ids.clear()
            self._active_request_id = None
        for record in records:
            record.cancellation_requested.set()
            if record.timeout_timer is not None:
                record.timeout_timer.cancel()
            record.request = None
            record.events.clear()
            record.sources.clear()
        if active:
            self._cancel_generation()

    def queue_depth_class(self) -> Literal["idle", "active", "queued"]:
        """Return a coarse safe queue class without exposing request identities or counts."""

        with self._lock:
            self._expire_completed_locked()
            if self._active_request_id is None:
                return "idle"
            if self._queued_request_ids:
                return "queued"
            return "active"

    def _start_locked(self, record: _ConversationRecord) -> None:
        self._active_request_id = record.request_id
        record.timeout_timer = threading.Timer(
            self._request_timeout_seconds, self._timeout, args=(record.request_id,)
        )
        record.timeout_timer.daemon = True
        record.timeout_timer.start()
        thread = threading.Thread(target=self._run, args=(record.request_id,), daemon=True)
        thread.start()

    def _run(self, request_id: str) -> None:
        with self._lock:
            record = self._records.get(request_id)
            request = record.request if record is not None else None
        if record is None or request is None:
            return
        outcome: ConversationOutcome | None = None
        failed = False
        try:
            outcome = self._orchestrator.ask(
                request,
                lifecycle_callback=lambda phase: self._progress(request_id, phase),
                cancellation_check=record.cancellation_requested.is_set,
            )
        except Exception:
            failed = True
        finally:
            with self._lock:
                current = self._records.get(request_id)
                if current is not None:
                    if current.timeout_timer is not None:
                        current.timeout_timer.cancel()
                    if not current.terminal:
                        if current.cancellation_requested.is_set() or (
                            outcome is not None and outcome.reason_code == "assistant_cancelled"
                        ):
                            self._terminal_locked(
                                current, "cancelled", "assistant_cancelled", incomplete=True
                            )
                        elif failed or outcome is None:
                            self._terminal_locked(
                                current, "error", "assistant_internal_error", incomplete=True
                            )
                        else:
                            self._final_locked(current, outcome)
                    self._complete_active_locked(current)

    def _progress(self, request_id: str, phase: str) -> None:
        progress_states: dict[str, RequestState] = {
            "scope_check": "scope_check",
            "evidence_check": "evidence_check",
            "generating": "generating",
            "validating": "validating",
        }
        state = progress_states.get(phase)
        if state is None:
            return
        with self._lock:
            record = self._records.get(request_id)
            if record is None or record.terminal:
                return
            self._emit_locked(
                record,
                "progress",
                state,
                f"assistant_{phase}",
                f"assistant_chat_{phase}",
                "assistant_chat_cancel",
            )

    def _timeout(self, request_id: str) -> None:
        with self._lock:
            record = self._records.get(request_id)
            if record is None or record.terminal or request_id != self._active_request_id:
                return
            record.cancellation_requested.set()
            self._terminal_locked(record, "error", "assistant_timeout", incomplete=True)
        self._cancel_generation()

    def _final_locked(self, record: _ConversationRecord, outcome: ConversationOutcome) -> None:
        if outcome.disposition not in {"answer", "clarify", "abstain", "refuse"}:
            self._terminal_locked(record, "error", "assistant_internal_error", incomplete=True)
            return
        source_ids: tuple[str, ...] = ()
        external_claims: tuple[ConversationStreamExternalClaim, ...] = ()
        if outcome.disposition == "answer":
            source_ids = tuple(
                self._source_id_for(record, citation) for citation in outcome.citations
            )
            external_claims = tuple(
                ConversationStreamExternalClaim(
                    claim.text,
                    tuple(self._source_id_for(record, citation) for citation in claim.citations),
                )
                for claim in outcome.external_claims
            )
        self._terminal_locked(
            record,
            "final",
            outcome.reason_code,
            disposition=outcome.disposition,
            text=outcome.text if outcome.disposition == "answer" else "",
            source_ids=source_ids,
            external_claims=external_claims,
        )

    def _terminal_locked(
        self,
        record: _ConversationRecord,
        event_type: Literal["final", "cancelled", "error"],
        reason_code: str,
        *,
        disposition: AnswerDisposition | None = None,
        text: str = "",
        source_ids: tuple[str, ...] = (),
        external_claims: tuple[ConversationStreamExternalClaim, ...] = (),
        incomplete: bool = False,
    ) -> None:
        state: RequestState = "error"
        if event_type == "cancelled":
            state = "cancelled"
        elif event_type == "final" and disposition is not None:
            state = disposition
        self._emit_locked(
            record,
            event_type,
            state,
            reason_code,
            f"assistant_chat_{state}",
            "assistant_chat_search" if state in {"error", "cancelled", "abstain"} else "",
            disposition=disposition,
            text=text,
            source_ids=source_ids,
            external_claims=external_claims,
            incomplete=incomplete,
        )
        record.terminal = True
        record.completed_at = self._clock()

    def _complete_active_locked(self, record: _ConversationRecord) -> None:
        if self._active_request_id != record.request_id:
            return
        record.request = None
        self._active_request_id = None
        if self._queued_request_ids:
            next_id = self._queued_request_ids.popleft()
            next_record = self._records.get(next_id)
            if next_record is not None and not next_record.terminal:
                self._start_locked(next_record)
        self._prune_completed_locked()

    def _prune_completed_locked(self) -> None:
        self._expire_completed_locked()
        completed = sorted(
            (
                record
                for record in self._records.values()
                if record.terminal and record.completed_at is not None
            ),
            key=lambda record: record.completed_at or 0.0,
        )
        while len(completed) > MAX_COMPLETED_REQUESTS:
            oldest = completed.pop(0)
            self._records.pop(oldest.request_id, None)

    def _expire_completed_locked(self) -> None:
        now = self._clock()
        expired = [
            record.request_id
            for record in self._records.values()
            if (
                record.terminal
                and record.completed_at is not None
                and now - record.completed_at >= self._completed_retention_seconds
            )
        ]
        for request_id in expired:
            self._records.pop(request_id, None)

    def _emit_locked(
        self,
        record: _ConversationRecord,
        event_type: EventType,
        state: RequestState,
        reason_code: str,
        message_key: str,
        action_key: str,
        *,
        disposition: str | None = None,
        text: str = "",
        source_ids: tuple[str, ...] = (),
        external_claims: tuple[ConversationStreamExternalClaim, ...] = (),
        incomplete: bool = False,
    ) -> None:
        record.state = state
        record.state_epoch += 1
        event = ConversationStreamEvent(
            event_type=event_type,
            request_id=record.request_id,
            state=state,
            state_epoch=record.state_epoch,
            reason_code=reason_code,
            message_key=message_key,
            action_key=action_key,
            disposition=disposition,
            text=text,
            source_ids=source_ids,
            incomplete=incomplete,
            external_claims=external_claims,
        )
        while len(record.events) >= self._max_event_buffer:
            record.events.popleft()
        record.events.append(event)

    def _source_id_for(self, record: _ConversationRecord, citation: object) -> str:
        for source_id, retained in record.sources.items():
            if retained == citation:
                return source_id
        source_id = f"src_{secrets.token_urlsafe(18)}"
        while source_id in record.sources:
            source_id = f"src_{secrets.token_urlsafe(18)}"
        record.sources[source_id] = citation
        return source_id

    @staticmethod
    def _new_request_id() -> str:
        return f"req_{secrets.token_urlsafe(18)}"
