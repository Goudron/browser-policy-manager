"""Memory-only, bounded local dialogue context for the documentation assistant.

The store is deliberately independent from HTTP, persistence, browser storage and model inference.
Only the controller can create an opaque session handle and provide a current BPM version.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Final, Literal

from app.documentation.retrieval import SUPPORTED_LOCALES, LocalCitation

MAX_CONTEXT_PAIRS: Final[int] = 8
# A dialogue pair contains one user entry and one assistant entry.  The worker receives
# chronological entries, hence the storage bound is twice the reader-visible pair limit.
MAX_CONTEXT_TURNS: Final[int] = MAX_CONTEXT_PAIRS * 2
MAX_RESOLVED_ENTITIES: Final[int] = 8
MAX_ENTITY_CHARACTERS: Final[int] = 120
IDLE_SESSION_TTL_SECONDS: Final[float] = 15 * 60.0
ABSOLUTE_SESSION_TTL_SECONDS: Final[float] = 8 * 60 * 60.0
SessionRole = Literal["user", "assistant"]
Clock = Callable[[], float]


class ConversationContextUnavailable(RuntimeError):
    """Stable safe code when a session cannot contribute context."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ContextTurn:
    """Minimal display-safe prior text; citations remain bound to each new final response."""

    role: SessionRole
    text: str


@dataclass(frozen=True)
class ConversationContext:
    """One immutable snapshot supplied to a later retrieval/generation call."""

    session_id: str
    locale: str
    bpm_version: str
    turns: tuple[ContextTurn, ...]
    resolved_entities: tuple[str, ...]
    topic_ids: tuple[str, ...]


@dataclass
class _Session:
    created_at: float
    last_accessed_at: float
    locale: str
    bpm_version: str
    turns: list[ContextTurn]
    resolved_entities: list[str]
    topic_ids: list[str]


class ConversationContextStore:
    """Thread-safe ephemeral store with deterministic eviction and topic/version invalidation."""

    def __init__(
        self,
        *,
        idle_ttl_seconds: float = IDLE_SESSION_TTL_SECONDS,
        absolute_ttl_seconds: float = ABSOLUTE_SESSION_TTL_SECONDS,
        clock: Clock = monotonic,
    ) -> None:
        if idle_ttl_seconds <= 0 or absolute_ttl_seconds <= 0:
            raise ValueError("conversation context TTL must be positive")
        self._sessions: dict[str, _Session] = {}
        self._lock = threading.RLock()
        self._idle_ttl_seconds = idle_ttl_seconds
        self._absolute_ttl_seconds = absolute_ttl_seconds
        self._clock = clock

    def create(self, *, locale: str, bpm_version: str) -> str:
        """Create a controller-owned opaque memory-only session for one exact locale and version."""

        self._validate_identity(locale, bpm_version)
        session_id = secrets.token_urlsafe(24)
        now = self._clock()
        with self._lock:
            self._sessions[session_id] = _Session(now, now, locale, bpm_version, [], [], [])
        return session_id

    def snapshot(self, *, session_id: str, locale: str, bpm_version: str) -> ConversationContext:
        """Return context only when identity still matches; a version change permanently invalidates it."""

        with self._lock:
            session = self._require(session_id)
            if session.locale != locale:
                raise ConversationContextUnavailable("assistant_session_locale_mismatch")
            if session.bpm_version != bpm_version:
                del self._sessions[session_id]
                raise ConversationContextUnavailable("assistant_session_version_changed")
            return ConversationContext(
                session_id,
                session.locale,
                session.bpm_version,
                tuple(session.turns),
                tuple(session.resolved_entities),
                tuple(session.topic_ids),
            )

    def prune_for_evidence(
        self,
        *,
        session_id: str,
        locale: str,
        bpm_version: str,
        citations: tuple[LocalCitation, ...],
    ) -> ConversationContext:
        """Refresh entities for new evidence without discarding the bounded conversation."""

        current = self.snapshot(session_id=session_id, locale=locale, bpm_version=bpm_version)
        topic_ids = self._topic_ids(citations)
        if current.topic_ids and topic_ids and not set(current.topic_ids).intersection(topic_ids):
            with self._lock:
                session = self._require(session_id)
                # Every response still receives a fresh EvidencePack.  Preserve the dialogue so a
                # reader can move between related BPM topics without a silent context reset, but
                # remove stale retrieval-expansion entities from the previous topic.
                session.resolved_entities.clear()
                session.topic_ids = list(topic_ids)
            return self.snapshot(session_id=session_id, locale=locale, bpm_version=bpm_version)
        return current

    def record(
        self,
        *,
        session_id: str,
        locale: str,
        bpm_version: str,
        question: str,
        answer: str,
        citations: tuple[LocalCitation, ...],
        resolved_entities: tuple[str, ...] = (),
    ) -> ConversationContext:
        """Append one validated exchange, retaining the newest eight pairs and trusted entities."""

        if not question or not answer:
            raise ConversationContextUnavailable("assistant_invalid_context_update")
        self._validate_entities(resolved_entities)
        with self._lock:
            session = self._require_identity(session_id, locale, bpm_version)
            topic_ids = self._topic_ids(citations)
            if (
                session.topic_ids
                and topic_ids
                and not set(session.topic_ids).intersection(topic_ids)
            ):
                session.resolved_entities.clear()
            session.topic_ids = list(topic_ids)
            session.turns.extend((ContextTurn("user", question), ContextTurn("assistant", answer)))
            session.turns[:] = session.turns[-MAX_CONTEXT_TURNS:]
            entities = [*resolved_entities, *topic_ids]
            session.resolved_entities = self._deduplicate(entities)[-MAX_RESOLVED_ENTITIES:]
        return self.snapshot(session_id=session_id, locale=locale, bpm_version=bpm_version)

    def clear(self, session_id: str) -> bool:
        """Remove the exact memory-only session; no historical context or citation identity remains."""

        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def clear_expired(self) -> int:
        """Drop idle/aged sessions without exposing or logging their content."""

        with self._lock:
            expired = [
                session_id
                for session_id, session in self._sessions.items()
                if self._expired(session, self._clock())
            ]
            for session_id in expired:
                del self._sessions[session_id]
            return len(expired)

    def clear_all(self) -> int:
        """Clear every in-memory session for process shutdown or an explicit controller reset."""

        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            return count

    def _require(self, session_id: str) -> _Session:
        if not isinstance(session_id, str) or not session_id:
            raise ConversationContextUnavailable("assistant_session_unavailable")
        session = self._sessions.get(session_id)
        if session is None:
            raise ConversationContextUnavailable("assistant_session_unavailable")
        now = self._clock()
        if self._expired(session, now):
            del self._sessions[session_id]
            raise ConversationContextUnavailable("assistant_session_expired")
        session.last_accessed_at = now
        return session

    def _require_identity(self, session_id: str, locale: str, bpm_version: str) -> _Session:
        session = self._require(session_id)
        if session.locale != locale:
            raise ConversationContextUnavailable("assistant_session_locale_mismatch")
        if session.bpm_version != bpm_version:
            del self._sessions[session_id]
            raise ConversationContextUnavailable("assistant_session_version_changed")
        return session

    @staticmethod
    def _validate_identity(locale: str, bpm_version: str) -> None:
        if locale not in SUPPORTED_LOCALES or not isinstance(bpm_version, str) or not bpm_version:
            raise ConversationContextUnavailable("assistant_invalid_session_identity")

    @staticmethod
    def _validate_entities(entities: tuple[str, ...]) -> None:
        if len(entities) > MAX_RESOLVED_ENTITIES or any(
            not isinstance(entity, str) or not entity or len(entity) > MAX_ENTITY_CHARACTERS
            for entity in entities
        ):
            raise ConversationContextUnavailable("assistant_invalid_context_update")

    @staticmethod
    def _topic_ids(citations: tuple[LocalCitation, ...]) -> tuple[str, ...]:
        return tuple(sorted({citation.topic_id for citation in citations}))

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    def _expired(self, session: _Session, now: float) -> bool:
        return (
            now - session.last_accessed_at >= self._idle_ttl_seconds
            or now - session.created_at >= self._absolute_ttl_seconds
        )
