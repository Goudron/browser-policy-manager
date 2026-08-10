"""HTTP-independent ownership adapter for the local documentation assistant.

The adapter binds opaque same-origin browser sessions to the existing bounded conversation
controller.  It deliberately does not construct a model, an encoder or an index: release
assembly supplies those verified dependencies and may leave the assistant unavailable.
"""

from __future__ import annotations

import re
import secrets
import threading
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from importlib import import_module
from typing import TYPE_CHECKING, Protocol

from app.documentation.assistant_contracts import (
    ConversationAdmission,
    ConversationRequest,
    ConversationStreamEvent,
    ConversationTimePreview,
    WebMode,
)
from app.documentation.training_notice import training_notice

if TYPE_CHECKING:
    from app.documentation.conversation_context import ConversationContextStore
    from app.documentation.conversation_diagnostics import AssistantDiagnosticsService
    from app.documentation.conversation_stream import ConversationStreamController

STREAM_POLL_SECONDS = 0.05
STREAM_GRACE_SECONDS = 5.0
WEB_TAB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{20,64}$")
TRAINING_REQUEST_RETENTION_SECONDS = 15 * 60.0
MAX_TRAINING_REQUESTS = 32
MAX_ASSISTANT_CONTEXT_SESSIONS = 32


@dataclass(frozen=True)
class AssistantStatus:
    state: str
    assistant_ready: bool
    lexical_search_ready: bool
    locale: str
    message_key: str
    action_key: str
    reason_code: str
    state_epoch: int = 0


@dataclass(frozen=True)
class AssistantSource:
    source_id: str
    title: str
    published_url: str
    locale: str
    excerpt: str
    source_kind: str = "local"
    provider_id: str = ""


@dataclass(frozen=True)
class AssistantWebModeStatus:
    enabled: bool
    available: bool
    locale: str
    reason_code: str
    state_epoch: int = 0


@dataclass(frozen=True)
class _TrainingRequest:
    session_id: str
    locale: str
    created_at: float


class WebModeStore(Protocol):
    def status(self, *, session_id: str, locale: str) -> object: ...

    def set_enabled(self, *, session_id: str, locale: str, enabled: bool) -> object: ...

    def is_enabled(self, *, session_id: str, locale: str) -> bool: ...

    def clear_all(self) -> int: ...


class DocumentationAssistantService(Protocol):
    """The bounded service surface exposed to the same-origin API router."""

    def status(self, *, locale: str, session_id: str) -> AssistantStatus: ...

    def ask(self, *, request: ConversationRequest, session_id: str) -> ConversationAdmission: ...

    def web_mode_status(
        self, *, locale: str, session_id: str, tab_id: str | None = None
    ) -> AssistantWebModeStatus: ...

    def set_web_mode(
        self, *, locale: str, session_id: str, enabled: bool, tab_id: str | None = None
    ) -> AssistantWebModeStatus: ...

    def events(
        self, *, request_id: str, session_id: str
    ) -> Iterable[ConversationStreamEvent] | None: ...

    def cancel(self, *, request_id: str, session_id: str) -> bool | None: ...

    def clear(
        self, *, session_id: str, locale: str | None = None, tab_id: str | None = None
    ) -> bool: ...

    def source(
        self, *, request_id: str, source_id: str, session_id: str
    ) -> AssistantSource | None: ...


class TrainingDocumentationAssistantService:
    """Release-safe assistant surface while local-model training remains out of scope.

    It accepts a chat turn so the documented UI remains usable, but deliberately never creates a
    model worker, query encoder, retrieval request, citation or external-source request.  The
    opaque request record exists only long enough for the browser to read its final event.
    """

    def __init__(
        self,
        *,
        request_retention_seconds: float = TRAINING_REQUEST_RETENTION_SECONDS,
        max_requests: int = MAX_TRAINING_REQUESTS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if request_retention_seconds <= 0 or max_requests <= 0:
            raise ValueError("training request retention bounds must be positive")
        self._lock = threading.RLock()
        self._request_retention_seconds = request_retention_seconds
        self._max_requests = max_requests
        self._clock = clock
        self._requests: dict[str, _TrainingRequest] = {}

    def status(self, *, locale: str, session_id: str) -> AssistantStatus:
        del session_id
        return AssistantStatus(
            state="ready",
            assistant_ready=True,
            lexical_search_ready=True,
            locale=locale,
            message_key="assistant_training_notice",
            action_key="assistant_chat_send",
            reason_code="assistant_training_notice",
            state_epoch=1,
        )

    def ask(self, *, request: ConversationRequest, session_id: str) -> ConversationAdmission:
        request_id = secrets.token_urlsafe(24)
        with self._lock:
            self._clear_expired_locked()
            while len(self._requests) >= self._max_requests:
                self._requests.pop(next(iter(self._requests)))
            self._requests[request_id] = _TrainingRequest(session_id, request.locale, self._clock())
        return ConversationAdmission(
            request_id,
            "accepted",
            "assistant_training_notice",
            1,
            time_preview=ConversationTimePreview(1, 1),
        )

    def web_mode_status(
        self, *, locale: str, session_id: str, tab_id: str | None = None
    ) -> AssistantWebModeStatus:
        del session_id, tab_id
        return AssistantWebModeStatus(False, False, locale, "assistant_web_disabled", 0)

    def set_web_mode(
        self,
        *,
        locale: str,
        session_id: str,
        enabled: bool,
        tab_id: str | None = None,
    ) -> AssistantWebModeStatus:
        del session_id, enabled, tab_id
        return AssistantWebModeStatus(False, False, locale, "assistant_web_disabled", 0)

    def events(
        self, *, request_id: str, session_id: str
    ) -> Iterable[ConversationStreamEvent] | None:
        with self._lock:
            self._clear_expired_locked()
            owner = self._requests.get(request_id)
        if owner is None or owner.session_id != session_id:
            return None
        locale = owner.locale
        return (
            ConversationStreamEvent(
                "accepted",
                request_id,
                "accepted",
                1,
                "assistant_training_notice",
                "assistant_chat_accepted",
                "assistant_chat_cancel",
            ),
            ConversationStreamEvent(
                "final",
                request_id,
                "answer",
                2,
                "assistant_training_notice",
                "assistant_training_notice",
                "",
                "answer",
                training_notice(locale),
            ),
        )

    def cancel(self, *, request_id: str, session_id: str) -> bool | None:
        with self._lock:
            self._clear_expired_locked()
            owner = self._requests.get(request_id)
        return owner is not None and owner.session_id == session_id

    def clear(
        self, *, session_id: str, locale: str | None = None, tab_id: str | None = None
    ) -> bool:
        del locale, tab_id
        with self._lock:
            self._clear_expired_locked()
            for request_id, owner in tuple(self._requests.items()):
                if owner.session_id == session_id:
                    del self._requests[request_id]
        return True

    def source(self, *, request_id: str, source_id: str, session_id: str) -> AssistantSource | None:
        del request_id, source_id, session_id
        return None

    def shutdown(self) -> int:
        """Discard only opaque, short-lived request ownership on application shutdown."""

        with self._lock:
            count = len(self._requests)
            self._requests.clear()
            return count

    def _clear_expired_locked(self) -> None:
        cutoff = self._clock() - self._request_retention_seconds
        expired = [
            request_id
            for request_id, record in self._requests.items()
            if record.created_at <= cutoff
        ]
        for request_id in expired:
            del self._requests[request_id]


CitationSourceResolver = Callable[[object], AssistantSource | None]


class ControllerDocumentationAssistantService:
    """Own controller request handles and ephemeral context under one browser session.

    The controller keeps no notion of a browser.  This adapter keeps the small ownership maps
    needed to prevent a request, source or cancellation from crossing browser sessions.  Context
    IDs are generated by ``ConversationContextStore`` and never returned to the browser.
    """

    def __init__(
        self,
        *,
        controller: ConversationStreamController,
        context_store: ConversationContextStore,
        diagnostics: AssistantDiagnosticsService,
        bpm_version: str,
        source_resolver: CitationSourceResolver,
        web_mode_store: WebModeStore | None = None,
    ) -> None:
        if not bpm_version:
            raise ValueError("bpm_version is required")
        self._controller = controller
        self._context_store = context_store
        self._diagnostics = diagnostics
        self._bpm_version = bpm_version
        self._source_resolver = source_resolver
        self._web_mode_store = web_mode_store
        self._lock = threading.RLock()
        self._request_owners: dict[str, tuple[str, str]] = {}
        self._context_sessions: dict[tuple[str, str], str] = {}

    def status(self, *, locale: str, session_id: str) -> AssistantStatus:
        del session_id
        snapshot = self._diagnostics.status()
        reason_code = (
            "assistant_ready" if snapshot.assistant_ready else f"assistant_{snapshot.state}"
        )
        return AssistantStatus(
            state=snapshot.state,
            assistant_ready=snapshot.assistant_ready,
            lexical_search_ready=snapshot.lexical_search_ready,
            locale=locale,
            message_key=reason_code,
            action_key=(
                "assistant_chat_send" if snapshot.assistant_ready else "assistant_manage_model"
            ),
            reason_code=reason_code,
        )

    def ask(self, *, request: ConversationRequest, session_id: str) -> ConversationAdmission:
        context_key = self._context_key(session_id, request.locale, request.web_tab_id)
        with self._lock:
            self._prune_owned_state_locked()
            context_session = self._context_sessions.get(context_key)
            created_context = False
            if context_session is None:
                if len(self._context_sessions) >= MAX_ASSISTANT_CONTEXT_SESSIONS:
                    return ConversationAdmission(None, "error", "assistant_busy", 0)
                try:
                    context_session = self._context_store.create(
                        locale=request.locale, bpm_version=self._bpm_version
                    )
                except _conversation_context_unavailable_type():
                    return ConversationAdmission(None, "error", "assistant_busy", 0)
                self._context_sessions[context_key] = context_session
                created_context = True
        web_identity = self._web_mode_identity(session_id, request.web_tab_id)
        effective_web_mode: WebMode = (
            "request_web"
            if self._web_mode_store is not None
            and web_identity is not None
            and self._web_mode_store.is_enabled(session_id=web_identity, locale=request.locale)
            else "local_only"
        )
        try:
            timing_context = self._context_store.snapshot(
                session_id=context_session,
                locale=request.locale,
                bpm_version=self._bpm_version,
            )
            timing_context_characters = sum(len(turn.text) for turn in timing_context.turns)
        except _conversation_context_unavailable_type():
            # Timing is advisory only.  A race with Clear must not prevent normal admission.
            timing_context_characters = 0
        admission = self._controller.submit(
            replace(
                request,
                web_mode=effective_web_mode,
                session_id=context_session,
                web_session_id=web_identity or session_id,
                timing_context_characters=timing_context_characters,
            )
        )
        if admission.request_id is None:
            if created_context:
                with self._lock:
                    if self._context_sessions.get(context_key) == context_session:
                        del self._context_sessions[context_key]
                self._context_store.clear(context_session)
            return admission
        with self._lock:
            self._prune_owned_state_locked()
            self._request_owners[admission.request_id] = (session_id, context_key[0])
        return admission

    def web_mode_status(
        self, *, locale: str, session_id: str, tab_id: str | None = None
    ) -> AssistantWebModeStatus:
        if self._web_mode_store is None:
            return AssistantWebModeStatus(False, False, locale, "assistant_web_disabled", 0)
        identity = self._web_mode_identity(session_id, tab_id)
        if identity is None:
            return AssistantWebModeStatus(False, False, locale, "assistant_web_mode_invalid", 0)
        return self._safe_web_mode_status(
            self._web_mode_store.status(session_id=identity, locale=locale), locale
        )

    def set_web_mode(
        self,
        *,
        locale: str,
        session_id: str,
        enabled: bool,
        tab_id: str | None = None,
    ) -> AssistantWebModeStatus:
        if self._web_mode_store is None:
            return AssistantWebModeStatus(False, False, locale, "assistant_web_disabled", 0)
        identity = self._web_mode_identity(session_id, tab_id)
        if identity is None:
            return AssistantWebModeStatus(False, False, locale, "assistant_web_mode_invalid", 0)
        return self._safe_web_mode_status(
            self._web_mode_store.set_enabled(session_id=identity, locale=locale, enabled=enabled),
            locale,
        )

    def events(
        self, *, request_id: str, session_id: str
    ) -> Iterable[ConversationStreamEvent] | None:
        self._prune_owned_state()
        if not self._owns(request_id, session_id):
            return None
        return self._stream(request_id)

    def cancel(self, *, request_id: str, session_id: str) -> bool | None:
        self._prune_owned_state()
        if not self._owns(request_id, session_id):
            return None
        return self._controller.cancel(request_id)

    def clear(
        self, *, session_id: str, locale: str | None = None, tab_id: str | None = None
    ) -> bool:
        """Clear one tab/locale conversation, or every legacy session context when unspecified."""

        context_owner = (
            self._context_key(session_id, locale, tab_id)[0] if locale is not None else None
        )
        with self._lock:
            self._prune_owned_state_locked()
            request_ids = [
                request_id
                for request_id, (owner, request_context_owner) in self._request_owners.items()
                if owner == session_id
                and (context_owner is None or request_context_owner == context_owner)
            ]
            for request_id in request_ids:
                del self._request_owners[request_id]
            context_ids = [
                context_id
                for (owner, _locale), context_id in self._context_sessions.items()
                if owner == (context_owner or session_id)
            ]
            self._context_sessions = {
                key: context_id
                for key, context_id in self._context_sessions.items()
                if key[0] != (context_owner or session_id)
            }
        for request_id in request_ids:
            self._controller.cancel(request_id)
        for context_id in context_ids:
            self._context_store.clear(context_id)
        return True

    def source(self, *, request_id: str, source_id: str, session_id: str) -> AssistantSource | None:
        self._prune_owned_state()
        if not self._owns(request_id, session_id):
            return None
        citation = self._controller.source(request_id, source_id)
        if citation is None:
            return None
        source = self._source_resolver(citation)
        if source is None:
            return None
        # The stream controller deliberately exposes an opaque per-request ID.  The resolver
        # works with the underlying citation and must not be allowed to substitute that ID.
        return replace(source, source_id=source_id)

    def shutdown(self) -> None:
        """Release controller-owned state without exposing request or conversation content."""

        with self._lock:
            self._request_owners.clear()
            self._context_sessions.clear()
        shutdown = getattr(self._controller, "shutdown", None)
        if callable(shutdown):
            shutdown()
        self._context_store.clear_all()
        if self._web_mode_store is not None:
            self._web_mode_store.clear_all()

    @staticmethod
    def _safe_web_mode_status(value: object, locale: str) -> AssistantWebModeStatus:
        enabled = getattr(value, "enabled", False)
        available = getattr(value, "available", False)
        reason_code = getattr(value, "reason_code", "assistant_web_mode_unavailable")
        state_epoch = getattr(value, "state_epoch", 0)
        if (
            type(enabled) is not bool
            or type(available) is not bool
            or not isinstance(reason_code, str)
            or not reason_code
            or not isinstance(state_epoch, int)
            or state_epoch < 0
        ):
            return AssistantWebModeStatus(False, False, locale, "assistant_web_mode_unavailable", 0)
        return AssistantWebModeStatus(
            enabled and available,
            available,
            locale,
            reason_code,
            state_epoch,
        )

    @staticmethod
    def _web_mode_identity(session_id: str, tab_id: str | None) -> str | None:
        if tab_id is None:
            return session_id
        if not WEB_TAB_ID_PATTERN.fullmatch(tab_id):
            return None
        return f"{session_id}.{tab_id}"

    @classmethod
    def _context_key(cls, session_id: str, locale: str, tab_id: str | None) -> tuple[str, str]:
        """Bind dialogue memory to a browser tab when the UI supplied its opaque tab handle."""

        return (cls._web_mode_identity(session_id, tab_id) or session_id, locale)

    def _owns(self, request_id: str, session_id: str) -> bool:
        with self._lock:
            owner = self._request_owners.get(request_id)
            return owner is not None and owner[0] == session_id

    def _prune_owned_state(self) -> None:
        with self._lock:
            self._prune_owned_state_locked()

    def _prune_owned_state_locked(self) -> None:
        retains = getattr(self._controller, "retains", None)
        if callable(retains):
            self._request_owners = {
                request_id: owner
                for request_id, owner in self._request_owners.items()
                if retains(request_id)
            }
        contains = getattr(self._context_store, "contains", None)
        if callable(contains):
            self._context_sessions = {
                key: context_id
                for key, context_id in self._context_sessions.items()
                if contains(context_id)
            }

    def _stream(self, request_id: str) -> Iterable[ConversationStreamEvent]:
        deadline = time.monotonic() + _request_timeout_seconds() + STREAM_GRACE_SECONDS
        terminal = False
        try:
            while not terminal and time.monotonic() < deadline:
                events = self._controller.poll(request_id)
                for event in events:
                    yield event
                    terminal = event.state in {
                        "answer",
                        "clarify",
                        "abstain",
                        "refuse",
                        "cancelled",
                        "error",
                    }
                if not terminal:
                    time.sleep(STREAM_POLL_SECONDS)
        finally:
            if not terminal:
                self._controller.disconnect(request_id)


def _conversation_context_unavailable_type() -> type[RuntimeError]:
    """Load the incubation controller's exception only when that controller is exercised."""

    module = import_module("app.documentation.conversation_context")
    return module.ConversationContextUnavailable


def _request_timeout_seconds() -> float:
    """Read the optional stream controller's timeout without importing it in release assembly."""

    module = import_module("app.documentation.conversation_stream")
    return module.REQUEST_TIMEOUT_SECONDS
