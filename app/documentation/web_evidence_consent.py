"""Server-owned, memory-only consent for the optional external documentation evidence path.

This module deliberately has no HTTP client, route, browser storage or provider payload.  It gives
the future controller enough information to display a precise disclosure, then authorizes one use
of that exact question only after an explicit approval.  The pending record retains an HMAC, never
the outgoing question itself.
"""

from __future__ import annotations

import hmac
import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic
from typing import Final, Literal

from app.core.config import Settings
from app.documentation.retrieval import SUPPORTED_LOCALES

BRAVE_PROVIDER_NAME: Final[str] = "Brave Search API"
BRAVE_RECIPIENT: Final[str] = "Brave Software, Inc. in the United States"
BRAVE_QUERY_LOG_RETENTION_WARNING: Final[str] = (
    "Standard Brave Search API query logs may be retained for up to 90 days for billing, "
    "troubleshooting and abuse prevention."
)
WEB_QUERY_CHARACTERS_MAX: Final[int] = 400
WEB_QUERY_WORDS_MAX: Final[int] = 50
CONSENT_TTL_SECONDS: Final[float] = 5 * 60.0
MAX_SESSION_ID_CHARACTERS: Final[int] = 256
MAX_PENDING_CONSENTS: Final[int] = 32
MAX_WEB_MODE_RECORDS: Final[int] = 32

WebEvidenceConsentState = Literal["local_only", "disclosure_required", "approved"]
Clock = Callable[[], float]

_SEARCH_LANGUAGE_BY_LOCALE: Final[dict[str, str]] = {
    "en": "en",
    "ru": "ru",
    "de": "de",
    "zh-CN": "zh-hans",
    "fr": "fr",
    "es-ES": "es",
}


@dataclass(frozen=True)
class WebEvidenceConfiguration:
    """BYOK configuration whose credential is intentionally excluded from all representations."""

    enabled: bool = False
    subscription_token: str | None = field(default=None, repr=False)

    @classmethod
    def from_settings(cls, settings: Settings) -> WebEvidenceConfiguration:
        return cls(settings.WEB_EVIDENCE_ENABLED, settings.BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN)

    @property
    def availability_code(self) -> str:
        if not self.enabled:
            return "assistant_web_disabled"
        if not self.subscription_token or not self.subscription_token.strip():
            return "assistant_web_credential_unavailable"
        return "assistant_web_available"


@dataclass(frozen=True)
class WebEvidenceDisclosure:
    """Display-safe facts a future UI must render before any provider call can be authorized."""

    consent_id: str
    locale: str
    search_language: str
    outgoing_query: str
    provider: str = BRAVE_PROVIDER_NAME
    recipient: str = BRAVE_RECIPIENT
    query_log_retention_warning: str = BRAVE_QUERY_LOG_RETENTION_WARNING
    sent_data: tuple[str, ...] = (
        "the exact query shown above",
        "locale-derived search language",
        "fixed Mozilla source filter and bounded retrieval parameters",
    )
    not_sent: tuple[str, ...] = (
        "conversation history",
        "local BPM documentation or citations",
        "BPM profiles, database data, or filesystem data",
        "session identifiers, device location, or the subscription token",
    )


@dataclass(frozen=True)
class WebEvidenceAuthorization:
    """Opaque server-side capability for one later M9-03 provider call; it contains no query/key."""

    consent_id: str
    locale: str


@dataclass(frozen=True)
class WebEvidenceConsentResult:
    """Safe transport-neutral result for local-only fallback, disclosure, or approved use."""

    state: WebEvidenceConsentState
    reason_code: str
    disclosure: WebEvidenceDisclosure | None = None
    authorization: WebEvidenceAuthorization | None = None


@dataclass(frozen=True)
class WebEvidenceModeStatus:
    """Safe release status for a reader-owned external-sources mode."""

    enabled: bool
    available: bool
    locale: str
    reason_code: str
    state_epoch: int = 0


class WebEvidenceModeStore:
    """Bounded server-owned mode, off by default and retained until explicitly disabled.

    This is the effective M12A release policy.  The older one-question consent store remains
    available solely for the already-reviewed M9 component contract and compatibility tests.
    """

    def __init__(
        self,
        *,
        configuration: WebEvidenceConfiguration,
        max_records: int = MAX_WEB_MODE_RECORDS,
    ) -> None:
        if max_records <= 0:
            raise ValueError("web evidence mode bound must be positive")
        self._configuration = configuration
        self._max_records = max_records
        self._enabled: dict[tuple[str, str], int] = {}
        self._epochs: dict[tuple[str, str], int] = {}
        self._lock = threading.RLock()

    def status(self, *, session_id: str, locale: str) -> WebEvidenceModeStatus:
        """Return mode/configuration state without contacting or probing the provider."""

        if not WebEvidenceConsentStore._valid_identity(session_id, locale):
            return WebEvidenceModeStatus(
                False, False, locale, "assistant_web_mode_invalid"
            )
        available = self._configuration.availability_code == "assistant_web_available"
        key = (session_id, locale)
        with self._lock:
            enabled = available and key in self._enabled
            epoch = self._epochs.get(key, 0)
        reason_code = (
            "assistant_web_enabled"
            if enabled
            else (
                "assistant_web_disabled_by_reader"
                if available
                else self._configuration.availability_code
            )
        )
        return WebEvidenceModeStatus(enabled, available, locale, reason_code, epoch)

    def set_enabled(
        self, *, session_id: str, locale: str, enabled: bool
    ) -> WebEvidenceModeStatus:
        """Apply one explicit reader choice; repeated questions do not alter it."""

        if type(enabled) is not bool or not WebEvidenceConsentStore._valid_identity(
            session_id, locale
        ):
            return WebEvidenceModeStatus(
                False, False, locale, "assistant_web_mode_invalid"
            )
        key = (session_id, locale)
        available = self._configuration.availability_code == "assistant_web_available"
        with self._lock:
            current = key in self._enabled
            target = enabled and available
            if target and not current and len(self._enabled) >= self._max_records:
                return WebEvidenceModeStatus(
                    False,
                    available,
                    locale,
                    "assistant_web_mode_unavailable",
                    self._epochs.get(key, 0),
                )
            if target != current:
                epoch = self._epochs.get(key, 0) + 1
                if target:
                    self._epochs[key] = epoch
                    self._enabled[key] = epoch
                else:
                    self._enabled.pop(key, None)
                    self._epochs.pop(key, None)
            elif not available:
                self._enabled.pop(key, None)
                self._epochs.pop(key, None)
                epoch = 0
            else:
                epoch = self._epochs.get(key, 0)
        reason_code = (
            "assistant_web_enabled"
            if target
            else (
                "assistant_web_disabled_by_reader"
                if available
                else self._configuration.availability_code
            )
        )
        return WebEvidenceModeStatus(target, available, locale, reason_code, epoch)

    def is_enabled(self, *, session_id: str, locale: str) -> bool:
        """Authorize a later request only while both reader mode and configuration allow it."""

        return self.status(session_id=session_id, locale=locale).enabled

    def clear_all(self) -> int:
        """Clear process-owned release mode state during controlled shutdown."""

        with self._lock:
            count = len(self._enabled)
            self._enabled.clear()
            self._epochs.clear()
            return count


@dataclass
class _PendingConsent:
    session_id: str
    locale: str
    query_digest: bytes
    created_at: float
    approved: bool = False


class WebEvidenceConsentStore:
    """Thread-safe one-time consent records, scoped to a server-owned session and exact question."""

    def __init__(
        self,
        *,
        configuration: WebEvidenceConfiguration,
        consent_ttl_seconds: float = CONSENT_TTL_SECONDS,
        clock: Clock = monotonic,
    ) -> None:
        if consent_ttl_seconds <= 0:
            raise ValueError("web evidence consent TTL must be positive")
        self._configuration = configuration
        self._consent_ttl_seconds = consent_ttl_seconds
        self._clock = clock
        self._hmac_key = secrets.token_bytes(32)
        self._pending: dict[str, _PendingConsent] = {}
        self._lock = threading.RLock()

    def disclose(
        self, *, session_id: str, locale: str, question: str
    ) -> WebEvidenceConsentResult:
        """Create a precise pre-call disclosure without retaining the question in server state."""

        unavailable = self._unavailable_result()
        if unavailable is not None:
            return unavailable
        if not self._valid_identity(session_id, locale) or not self._valid_question(question):
            return WebEvidenceConsentResult("local_only", "assistant_web_consent_invalid")
        consent_id = secrets.token_urlsafe(24)
        now = self._clock()
        pending = _PendingConsent(session_id, locale, self._digest(question), now)
        with self._lock:
            self._clear_expired_locked(now)
            if len(self._pending) >= MAX_PENDING_CONSENTS:
                return WebEvidenceConsentResult("local_only", "assistant_web_consent_unavailable")
            self._pending[consent_id] = pending
        return WebEvidenceConsentResult(
            "disclosure_required",
            "assistant_web_consent_required",
            disclosure=WebEvidenceDisclosure(
                consent_id=consent_id,
                locale=locale,
                search_language=_SEARCH_LANGUAGE_BY_LOCALE[locale],
                outgoing_query=question,
            ),
        )

    def approve(self, *, session_id: str, consent_id: str) -> WebEvidenceConsentResult:
        """Record an explicit approval; a later consumer still must bind the exact question."""

        if self._unavailable_result() is not None:
            return WebEvidenceConsentResult("local_only", self._configuration.availability_code)
        with self._lock:
            pending = self._require_pending_locked(consent_id)
            if pending is None or pending.session_id != session_id or pending.approved:
                return WebEvidenceConsentResult("local_only", "assistant_web_consent_unavailable")
            pending.approved = True
            return WebEvidenceConsentResult(
                "approved",
                "assistant_web_consent_approved",
                authorization=WebEvidenceAuthorization(consent_id, pending.locale),
            )

    def consume(
        self,
        *,
        authorization: WebEvidenceAuthorization,
        session_id: str,
        locale: str,
        question: str,
    ) -> bool:
        """Consume exactly one approved capability for the same session, locale and question."""

        if self._unavailable_result() is not None or not self._valid_question(question):
            return False
        with self._lock:
            pending = self._require_pending_locked(authorization.consent_id)
            if pending is None:
                return False
            try:
                return self._matches_authorization(
                    pending,
                    authorization=authorization,
                    session_id=session_id,
                    locale=locale,
                    question=question,
                )
            finally:
                # An authorization is one-shot even if an invalid caller attempts to use it.
                self._pending.pop(authorization.consent_id, None)

    def is_consumable(
        self,
        *,
        authorization: WebEvidenceAuthorization,
        session_id: str,
        locale: str,
        question: str,
    ) -> bool:
        """Check exact one-use binding before a cost reservation without retaining or consuming it."""

        if self._unavailable_result() is not None or not self._valid_question(question):
            return False
        with self._lock:
            pending = self._require_pending_locked(authorization.consent_id)
            return pending is not None and self._matches_authorization(
                pending,
                authorization=authorization,
                session_id=session_id,
                locale=locale,
                question=question,
            )

    def clear_session(self, session_id: str) -> int:
        """Drop all unconsumed state for one server-owned session without exposing content."""

        with self._lock:
            consent_ids = [
                consent_id
                for consent_id, pending in self._pending.items()
                if pending.session_id == session_id
            ]
            for consent_id in consent_ids:
                del self._pending[consent_id]
            return len(consent_ids)

    def clear_expired(self) -> int:
        """Drop expired pending/approved records without a provider call or content diagnostic."""

        with self._lock:
            return self._clear_expired_locked(self._clock())

    def clear_all(self) -> int:
        """Clear every bounded pending consent on shutdown or explicit controller reset."""

        with self._lock:
            count = len(self._pending)
            self._pending.clear()
            return count

    def _unavailable_result(self) -> WebEvidenceConsentResult | None:
        availability = self._configuration.availability_code
        if availability == "assistant_web_available":
            return None
        return WebEvidenceConsentResult("local_only", availability)

    def _require_pending_locked(self, consent_id: str) -> _PendingConsent | None:
        if not isinstance(consent_id, str) or not consent_id:
            return None
        self._clear_expired_locked(self._clock())
        return self._pending.get(consent_id)

    def _clear_expired_locked(self, now: float) -> int:
        expired = [
            consent_id
            for consent_id, pending in self._pending.items()
            if now - pending.created_at >= self._consent_ttl_seconds
        ]
        for consent_id in expired:
            del self._pending[consent_id]
        return len(expired)

    def _digest(self, question: str) -> bytes:
        return hmac.digest(self._hmac_key, question.encode("utf-8"), "sha256")

    def _matches_authorization(
        self,
        pending: _PendingConsent,
        *,
        authorization: WebEvidenceAuthorization,
        session_id: str,
        locale: str,
        question: str,
    ) -> bool:
        return (
            pending.approved
            and pending.session_id == session_id
            and pending.locale == locale == authorization.locale
            and hmac.compare_digest(pending.query_digest, self._digest(question))
        )

    @staticmethod
    def _valid_identity(session_id: str, locale: str) -> bool:
        return (
            isinstance(session_id, str)
            and bool(session_id)
            and len(session_id) <= MAX_SESSION_ID_CHARACTERS
            and not any(character.isspace() or ord(character) < 32 for character in session_id)
            and locale in _SEARCH_LANGUAGE_BY_LOCALE
            and locale in SUPPORTED_LOCALES
        )

    @staticmethod
    def _valid_question(question: str) -> bool:
        return (
            isinstance(question, str)
            and bool(question.strip())
            and len(question) <= WEB_QUERY_CHARACTERS_MAX
            and len(question.split()) <= WEB_QUERY_WORDS_MAX
        )
