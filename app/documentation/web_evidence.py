"""Fail-closed retrieval of optional Brave web evidence for a later conservative merge stage.

The adapter has exactly one possible network destination.  It never follows provider result URLs,
never retries, and does not expose raw provider data.  M9-04 owns evidence merging and model input;
M10 owns the route and UI.  Callers must use the returned lease as a context manager so sanitized
external content is released at the end of the current request.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import deque
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Final, Literal, Protocol
from urllib.parse import urlsplit, urlunsplit

import httpx

from app.documentation.content_boundary import sanitize_evidence_text
from app.documentation.conversation import ConversationRequest, ScopeDecision
from app.documentation.web_evidence_consent import (
    WEB_QUERY_CHARACTERS_MAX,
    WEB_QUERY_WORDS_MAX,
    WebEvidenceAuthorization,
    WebEvidenceConfiguration,
    WebEvidenceConsentStore,
    WebEvidenceModeStore,
)

BRAVE_LLM_CONTEXT_ENDPOINT: Final[str] = "https://api.search.brave.com/res/v1/llm/context"
BRAVE_LLM_CONTEXT_HOST: Final[str] = "api.search.brave.com"
BRAVE_PROVIDER_ID: Final[str] = "brave-search-llm-context"
PROVIDER_TIMEOUT_SECONDS: Final[float] = 15.0
MAX_PROVIDER_RESPONSE_BYTES: Final[int] = 256 * 1024
MAX_EXTERNAL_URLS: Final[int] = 5
MAX_EXTERNAL_SNIPPETS: Final[int] = 10
MAX_EXTERNAL_SNIPPETS_PER_URL: Final[int] = 4
MAX_EXTERNAL_TITLE_BYTES: Final[int] = 512
MAX_EXTERNAL_AGE_BYTES: Final[int] = 256
MAX_EXTERNAL_URL_CHARACTERS: Final[int] = 2048
WEB_EVIDENCE_RATE_LIMIT_WINDOW_SECONDS: Final[float] = 60.0
WEB_EVIDENCE_MAX_REQUESTS_PER_SESSION: Final[int] = 5
WEB_EVIDENCE_MAX_REQUESTS_GLOBAL: Final[int] = 20
WEB_EVIDENCE_MAX_TRACKED_SESSIONS: Final[int] = 32

INLINE_MOZILLA_GOGGLE: Final[str] = (
    "$discard\n"
    "$site=mozilla.github.io\n"
    "$site=support.mozilla.org\n"
    "$site=firefox-source-docs.mozilla.org\n"
    "$site=www.mozilla.org"
)
_SOURCE_PATH_PREFIXES: Final[dict[str, tuple[str, ...]]] = {
    "mozilla.github.io": ("/policy-templates/",),
    "support.mozilla.org": ("/",),
    "firefox-source-docs.mozilla.org": (
        "/browser/components/enterprisepolicies/",
        "/toolkit/components/enterprisepolicies/",
    ),
    "www.mozilla.org": (
        "/en-US/firefox/",
        "/ru/firefox/",
        "/de/firefox/",
        "/zh-CN/firefox/",
        "/fr/firefox/",
        "/es-ES/firefox/",
    ),
}
_SEARCH_LANGUAGE_BY_LOCALE: Final[dict[str, str]] = {
    "en": "en",
    "ru": "ru",
    "de": "de",
    "zh-CN": "zh-hans",
    "fr": "fr",
    "es-ES": "es",
}

ScopeGate = Callable[[ConversationRequest], ScopeDecision]
ClientFactory = Callable[[], httpx.Client]
Clock = Callable[[], float]
CancellationCheck = Callable[[], bool]
WebEvidenceState = Literal["ready", "local_only"]


class WebEvidenceTransportError(RuntimeError):
    """A provider transport failed without exposing a network detail to the caller."""


class WebEvidenceRateLimiter:
    """Thread-safe, process-lifetime reservation limit for outbound optional-web requests."""

    def __init__(
        self,
        *,
        window_seconds: float = WEB_EVIDENCE_RATE_LIMIT_WINDOW_SECONDS,
        max_requests_per_session: int = WEB_EVIDENCE_MAX_REQUESTS_PER_SESSION,
        max_requests_global: int = WEB_EVIDENCE_MAX_REQUESTS_GLOBAL,
        max_tracked_sessions: int = WEB_EVIDENCE_MAX_TRACKED_SESSIONS,
        clock: Clock = monotonic,
    ) -> None:
        if (
            window_seconds <= 0
            or max_requests_per_session <= 0
            or max_requests_global <= 0
            or max_tracked_sessions <= 0
        ):
            raise ValueError("web evidence rate-limit bounds must be positive")
        self._window_seconds = window_seconds
        self._max_requests_per_session = max_requests_per_session
        self._max_requests_global = max_requests_global
        self._max_tracked_sessions = max_tracked_sessions
        self._clock = clock
        self._global_requests: deque[float] = deque()
        self._session_requests: dict[str, deque[float]] = {}
        self._lock = threading.RLock()

    def reserve(self, session_id: str) -> bool:
        """Atomically reserve one provider attempt, or fail closed before consent is consumed."""

        now = self._clock()
        with self._lock:
            self._clear_expired_locked(now)
            session_requests = self._session_requests.get(session_id)
            if len(self._global_requests) >= self._max_requests_global:
                return False
            if (
                session_requests is not None
                and len(session_requests) >= self._max_requests_per_session
            ):
                return False
            if session_requests is None:
                if len(self._session_requests) >= self._max_tracked_sessions:
                    return False
                session_requests = deque()
                self._session_requests[session_id] = session_requests
            self._global_requests.append(now)
            session_requests.append(now)
            return True

    def clear_session(self, session_id: str) -> int:
        """Forget one session's bounded counters on lifecycle reset without exposing request data."""

        with self._lock:
            requests = self._session_requests.pop(session_id, None)
            return len(requests) if requests is not None else 0

    def clear_expired(self) -> int:
        """Prune expired counter entries and empty sessions."""

        with self._lock:
            before = len(self._global_requests)
            self._clear_expired_locked(self._clock())
            return before - len(self._global_requests)

    def clear_all(self) -> int:
        """Clear all bounded process-memory counters on controlled shutdown."""

        with self._lock:
            count = len(self._global_requests)
            self._global_requests.clear()
            self._session_requests.clear()
            return count

    def _clear_expired_locked(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._global_requests and self._global_requests[0] <= cutoff:
            self._global_requests.popleft()
        empty_sessions: list[str] = []
        for session_id, requests in self._session_requests.items():
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if not requests:
                empty_sessions.append(session_id)
        for session_id in empty_sessions:
            del self._session_requests[session_id]


@dataclass(frozen=True)
class ProviderHttpResponse:
    """Small decoded response envelope without a live client or redirect-following capability."""

    status_code: int
    content_type: str | None
    content_encoding: str | None
    body: bytes


class BraveContextTransport(Protocol):
    """Fixed-destination POST boundary; the adapter never accepts a caller-supplied URL."""

    def post(
        self, *, url: str, headers: Mapping[str, str], payload: Mapping[str, object]
    ) -> ProviderHttpResponse: ...


class HttpxBraveContextTransport:
    """TLS-verifying, proxy-free, redirect-free bounded HTTP implementation for the fixed endpoint."""

    def __init__(
        self,
        *,
        timeout_seconds: float = PROVIDER_TIMEOUT_SECONDS,
        client_factory: ClientFactory | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("web evidence timeout must be positive")
        self._timeout_seconds = timeout_seconds
        self._client_factory = client_factory

    def post(
        self, *, url: str, headers: Mapping[str, str], payload: Mapping[str, object]
    ) -> ProviderHttpResponse:
        if url != BRAVE_LLM_CONTEXT_ENDPOINT:
            raise WebEvidenceTransportError("fixed provider endpoint required")
        client = self._new_client()
        try:
            with client.stream("POST", url, headers=dict(headers), json=dict(payload)) as response:
                if 300 <= response.status_code < 400:
                    raise WebEvidenceTransportError("provider redirect rejected")
                content_type = response.headers.get("content-type")
                content_encoding = response.headers.get("content-encoding")
                if not _json_content_type(content_type) or not _accepted_content_encoding(
                    content_encoding
                ):
                    raise WebEvidenceTransportError("provider response type rejected")
                body = _bounded_response_body(response)
                return ProviderHttpResponse(
                    response.status_code,
                    content_type,
                    content_encoding,
                    body,
                )
        except httpx.HTTPError as error:
            raise WebEvidenceTransportError("provider transport failed") from error
        finally:
            client.close()

    def _new_client(self) -> httpx.Client:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.Client(
            timeout=httpx.Timeout(self._timeout_seconds),
            verify=True,
            follow_redirects=False,
            trust_env=False,
        )


@dataclass(frozen=True)
class ExternalWebCitation:
    """External citation metadata only; its URL is never requested by BPM."""

    citation_id: str
    provider_id: str
    source_url: str
    source_title: str
    source_age: tuple[str, ...]
    retrieved_at: str
    source_kind: str = "external_untrusted"
    locale: str = ""


@dataclass(frozen=True)
class ExternalWebEvidence:
    """Inert sanitized content, still separate from local RAG evidence until M9-04 merges it."""

    citation: ExternalWebCitation
    snippets: tuple[str, ...]


class ExternalWebEvidenceLease(AbstractContextManager[tuple[ExternalWebEvidence, ...]]):
    """Own sanitized provider text for one request and clear the adapter's references on exit."""

    def __init__(self, evidence: tuple[ExternalWebEvidence, ...]) -> None:
        self._evidence = list(evidence)
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> tuple[ExternalWebEvidence, ...]:
        if self._closed:
            raise RuntimeError("external evidence lease is closed")
        return tuple(self._evidence)

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Discard the adapter-owned external response references at terminal completion/error."""

        self._evidence.clear()
        self._closed = True


@dataclass(frozen=True)
class WebEvidenceResult:
    """A safe local-only failure class or a short-lived lease for M9-04's conservative merge."""

    state: WebEvidenceState
    reason_code: str
    lease: ExternalWebEvidenceLease | None = None


class ScopedWebEvidenceRetriever:
    """Apply scope, cancellation and rate bounds before one fixed provider POST."""

    def __init__(
        self,
        *,
        configuration: WebEvidenceConfiguration,
        scope_gate: ScopeGate,
        rate_limiter: WebEvidenceRateLimiter,
        consent_store: WebEvidenceConsentStore | None = None,
        mode_store: WebEvidenceModeStore | None = None,
        transport: BraveContextTransport | None = None,
        retrieved_at: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if (consent_store is None) == (mode_store is None):
            raise ValueError("exactly one web evidence authorization store is required")
        self._configuration = configuration
        self._consent_store = consent_store
        self._mode_store = mode_store
        self._scope_gate = scope_gate
        self._rate_limiter = rate_limiter
        self._transport = transport or HttpxBraveContextTransport()
        self._retrieved_at = retrieved_at

    def retrieve(
        self,
        request: ConversationRequest,
        *,
        authorization: WebEvidenceAuthorization | None,
        cancellation_check: CancellationCheck = lambda: False,
    ) -> WebEvidenceResult:
        """Return sanitized temporary web evidence, or fail to local-only without a fallback call."""

        if request.web_mode != "request_web":
            return WebEvidenceResult("local_only", "assistant_web_not_requested")
        if self._cancelled(cancellation_check):
            return WebEvidenceResult("local_only", "assistant_cancelled")
        try:
            scope = self._scope_gate(request)
        except Exception:
            return WebEvidenceResult("local_only", "assistant_web_scope_unavailable")
        if scope.disposition != "allow" or not scope.reason_code:
            return WebEvidenceResult(
                "local_only", scope.reason_code or "assistant_web_scope_unavailable"
            )
        authorization_session_id = request.web_session_id or request.session_id
        if authorization_session_id is None:
            return WebEvidenceResult("local_only", "assistant_web_mode_unavailable")
        if self._configuration.availability_code != "assistant_web_available":
            return WebEvidenceResult("local_only", self._configuration.availability_code)
        if (
            len(request.question) > WEB_QUERY_CHARACTERS_MAX
            or len(request.question.split()) > WEB_QUERY_WORDS_MAX
        ):
            return WebEvidenceResult("local_only", "assistant_web_query_too_large")
        if self._cancelled(cancellation_check):
            return WebEvidenceResult("local_only", "assistant_cancelled")
        if self._mode_store is not None:
            if not self._mode_store.is_enabled(
                session_id=authorization_session_id, locale=request.locale
            ):
                return WebEvidenceResult("local_only", "assistant_web_disabled_by_reader")
        elif (
            self._consent_store is None
            or authorization is None
            or not self._consent_store.is_consumable(
                authorization=authorization,
                session_id=authorization_session_id,
                locale=request.locale,
                question=request.question,
            )
        ):
            return WebEvidenceResult("local_only", "assistant_web_consent_unavailable")
        if not self._rate_limiter.reserve(authorization_session_id):
            return WebEvidenceResult("local_only", "assistant_web_rate_limited")
        if self._cancelled(cancellation_check):
            return WebEvidenceResult("local_only", "assistant_cancelled")
        if self._consent_store is not None:
            if authorization is None or not self._consent_store.consume(
                authorization=authorization,
                session_id=authorization_session_id,
                locale=request.locale,
                question=request.question,
            ):
                return WebEvidenceResult("local_only", "assistant_web_consent_unavailable")
        try:
            response = self._transport.post(
                url=BRAVE_LLM_CONTEXT_ENDPOINT,
                headers=self._headers(),
                payload=self._payload(request.question, request.locale),
            )
            evidence = self._sanitize_response(response, request.locale)
        except Exception:
            return WebEvidenceResult("local_only", "assistant_web_provider_unavailable")
        if self._cancelled(cancellation_check):
            return WebEvidenceResult("local_only", "assistant_cancelled")
        if not evidence:
            return WebEvidenceResult("local_only", "assistant_web_no_evidence")
        return WebEvidenceResult(
            "ready",
            "assistant_web_evidence_ready",
            ExternalWebEvidenceLease(evidence),
        )

    def shutdown(self) -> None:
        """Clear bounded authorization counters owned by this process-local retriever."""

        self._rate_limiter.clear_all()
        if self._consent_store is not None:
            self._consent_store.clear_all()

    @staticmethod
    def _cancelled(cancellation_check: CancellationCheck) -> bool:
        """Treat a faulty cancellation probe as cancellation so it cannot permit network work."""

        try:
            return bool(cancellation_check())
        except Exception:
            return True

    def _headers(self) -> dict[str, str]:
        token = self._configuration.subscription_token
        if not token or not token.strip():
            raise WebEvidenceTransportError("provider token unavailable")
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "X-Subscription-Token": token,
        }

    @staticmethod
    def _payload(question: str, locale: str) -> dict[str, object]:
        language = _SEARCH_LANGUAGE_BY_LOCALE.get(locale)
        if language is None:
            raise ValueError("unsupported web evidence locale")
        return {
            "q": question,
            "search_lang": language,
            "count": 10,
            "spellcheck": False,
            "maximum_number_of_urls": MAX_EXTERNAL_URLS,
            "maximum_number_of_tokens": 2048,
            "maximum_number_of_snippets": MAX_EXTERNAL_SNIPPETS,
            "maximum_number_of_tokens_per_url": 1024,
            "maximum_number_of_snippets_per_url": MAX_EXTERNAL_SNIPPETS_PER_URL,
            "context_threshold_mode": "strict",
            "enable_local": False,
            "goggles": INLINE_MOZILLA_GOGGLE,
        }

    def _sanitize_response(
        self, response: ProviderHttpResponse, locale: str
    ) -> tuple[ExternalWebEvidence, ...]:
        if (
            not isinstance(response.status_code, int)
            or response.status_code != 200
            or not _json_content_type(response.content_type)
            or not _accepted_content_encoding(response.content_encoding)
            or not isinstance(response.body, bytes)
            or len(response.body) > MAX_PROVIDER_RESPONSE_BYTES
        ):
            raise ValueError("provider response rejected")
        payload = json.loads(response.body.decode("utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"grounding", "sources"}:
            raise ValueError("provider response schema rejected")
        grounding = payload["grounding"]
        sources = payload["sources"]
        if not isinstance(grounding, dict) or not isinstance(sources, dict):
            raise ValueError("provider response schema rejected")
        if set(grounding) - {"generic", "poi", "map"}:
            raise ValueError("provider response schema rejected")
        if grounding.get("poi") not in (None,):
            raise ValueError("provider rich response rejected")
        if grounding.get("map", []) != []:
            raise ValueError("provider rich response rejected")
        generic = grounding.get("generic")
        if not isinstance(generic, list) or len(generic) > MAX_EXTERNAL_URLS:
            raise ValueError("provider generic response rejected")
        if not all(isinstance(item, dict) for item in generic):
            raise ValueError("provider generic response rejected")
        raw_urls = [item.get("url") for item in generic]
        if (
            not all(isinstance(url, str) for url in raw_urls)
            or len(set(raw_urls)) != len(raw_urls)
            or set(sources) != set(raw_urls)
        ):
            raise ValueError("provider source metadata rejected")
        sanitized: list[ExternalWebEvidence] = []
        snippet_count = 0
        for item in generic:
            record = self._sanitize_item(item, sources, locale)
            sanitized.append(record)
            snippet_count += len(record.snippets)
        if snippet_count > MAX_EXTERNAL_SNIPPETS:
            raise ValueError("provider snippet limit rejected")
        return tuple(sanitized)

    def _sanitize_item(
        self, item: dict[str, Any], sources: dict[str, Any], locale: str
    ) -> ExternalWebEvidence:
        if set(item) != {"url", "title", "snippets"}:
            raise ValueError("provider generic item rejected")
        raw_url = item["url"]
        source_url = _approved_source_url(raw_url)
        title = _sanitize_bounded_text(item["title"], MAX_EXTERNAL_TITLE_BYTES)
        snippets = item["snippets"]
        if source_url is None or title is None or not isinstance(snippets, list):
            raise ValueError("provider generic item rejected")
        if not 1 <= len(snippets) <= MAX_EXTERNAL_SNIPPETS_PER_URL:
            raise ValueError("provider generic item rejected")
        clean_snippets = tuple(sanitize_evidence_text(snippet) for snippet in snippets)
        if any(snippet is None for snippet in clean_snippets):
            raise ValueError("provider generic item rejected")
        metadata = sources[raw_url]
        source_age = _source_age(metadata, source_url)
        citation_id = f"web:{hashlib.sha256(source_url.encode('utf-8')).hexdigest()[:32]}"
        return ExternalWebEvidence(
            ExternalWebCitation(
                citation_id=citation_id,
                provider_id=BRAVE_PROVIDER_ID,
                source_url=source_url,
                source_title=title,
                source_age=source_age,
                retrieved_at=self._retrieved_at()
                .astimezone(UTC)
                .replace(microsecond=0)
                .isoformat(),
                locale=locale,
            ),
            tuple(snippet for snippet in clean_snippets if snippet is not None),
        )


def _bounded_response_body(response: httpx.Response) -> bytes:
    body = bytearray()
    for block in response.iter_bytes(chunk_size=64 * 1024):
        body.extend(block)
        if len(body) > MAX_PROVIDER_RESPONSE_BYTES:
            raise WebEvidenceTransportError("provider response too large")
    return bytes(body)


def _json_content_type(content_type: str | None) -> bool:
    return (
        isinstance(content_type, str)
        and content_type.split(";", 1)[0].strip().casefold() == "application/json"
    )


def _accepted_content_encoding(content_encoding: str | None) -> bool:
    return content_encoding is None or content_encoding.strip().casefold() in {"identity", "gzip"}


def _approved_source_url(value: object) -> str | None:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_EXTERNAL_URL_CHARACTERS
        or any(
            character.isspace() or ord(character) < 32 or character in {"\\", "%"}
            for character in value
        )
    ):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    host = parsed.hostname.casefold() if parsed.hostname else ""
    if (
        parsed.scheme.casefold() != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or parsed.query
        or parsed.fragment
        or host not in _SOURCE_PATH_PREFIXES
        or not _approved_path(parsed.path, _SOURCE_PATH_PREFIXES[host])
    ):
        return None
    return urlunsplit(("https", host, parsed.path, "", ""))


def _approved_path(path: str, prefixes: tuple[str, ...]) -> bool:
    if not path.startswith("/") or "//" in path:
        return False
    segments = path.split("/")[1:]
    if any(segment in {".", ".."} for segment in segments):
        return False
    return any(path.startswith(prefix) for prefix in prefixes)


def _sanitize_bounded_text(value: object, maximum_bytes: int) -> str | None:
    if not isinstance(value, str) or len(value.encode("utf-8")) > maximum_bytes:
        return None
    return sanitize_evidence_text(value)


def _source_age(metadata: object, source_url: str) -> tuple[str, ...]:
    if not isinstance(metadata, dict) or set(metadata) != {"title", "hostname", "age"}:
        raise ValueError("provider source metadata rejected")
    host = urlsplit(source_url).hostname
    if (
        not isinstance(metadata["hostname"], str)
        or metadata["hostname"] != host
        or _sanitize_bounded_text(metadata["title"], MAX_EXTERNAL_TITLE_BYTES) is None
    ):
        raise ValueError("provider source metadata rejected")
    age = metadata["age"]
    if age is None:
        return ()
    if not isinstance(age, list) or not 1 <= len(age) <= 3:
        raise ValueError("provider source metadata rejected")
    sanitized = tuple(_sanitize_bounded_text(value, MAX_EXTERNAL_AGE_BYTES) for value in age)
    if any(value is None for value in sanitized):
        raise ValueError("provider source metadata rejected")
    return tuple(value for value in sanitized if value is not None)
