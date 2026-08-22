"""Bounded, server-only AMO extension search for the Guided Extensions step.

This is deliberately an adapter rather than an HTTP/API surface.  Callers can
provide only a lookup term, one supported UI locale and an opaque browser
session secret.  The adapter owns the fixed Mozilla URL, minimal headers,
response projection, private in-memory cache and outbound rate reservation.
It never accepts a provider URL, profile data, credentials or a result URL.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import threading
import unicodedata
from collections import OrderedDict, deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import monotonic
from typing import Final, Literal, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx

AMO_ORIGIN: Final[str] = "https://addons.mozilla.org"
AMO_SEARCH_PATH: Final[str] = "/api/v5/addons/search/"
AMO_SEARCH_ENDPOINT: Final[str] = f"{AMO_ORIGIN}{AMO_SEARCH_PATH}"
AMO_QUERY_MAXIMUM_CHARACTERS: Final[int] = 100
AMO_TIMEOUT_SECONDS: Final[float] = 5.0
AMO_MAX_RESPONSE_BYTES: Final[int] = 131_072
AMO_RESULTS_MAXIMUM: Final[int] = 10
AMO_GUID_MAXIMUM_BYTES: Final[int] = 255
AMO_NAME_MAXIMUM_BYTES: Final[int] = 512
AMO_VERSION_MAXIMUM_BYTES: Final[int] = 255
AMO_RATE_LIMIT_WINDOW_SECONDS: Final[float] = 60.0
AMO_MAX_REQUESTS_PER_SESSION: Final[int] = 5
AMO_MAX_REQUESTS_GLOBAL: Final[int] = 20
AMO_MAX_TRACKED_SESSIONS: Final[int] = 32
AMO_CACHE_TTL_SECONDS: Final[float] = 300.0
AMO_CACHE_MAX_ENTRIES_PER_SESSION: Final[int] = 10

AMO_LOCALE_MAP: Final[dict[str, str]] = {
    "en": "en-US",
    "ru": "ru",
    "de": "de",
    "es-ES": "es-ES",
    "fr": "fr",
    "zh-CN": "zh-CN",
}
AMO_FIXED_QUERY: Final[dict[str, str]] = {
    "app": "firefox",
    "type": "extension",
    "page": "1",
    "page_size": "10",
    "sort": "relevance",
}
AMO_FIXED_HEADERS: Final[dict[str, str]] = {
    "Accept": "application/json",
    "Accept-Encoding": "identity",
}

Clock = Callable[[], float]
CancellationCheck = Callable[[], bool]
AmoAvailability = Literal["available", "unavailable"]
AmoFailureReason = Literal[
    "available",
    "query-invalid",
    "locale-unsupported",
    "rate-limited",
    "cancelled",
    "timeout",
    "network",
    "tls",
    "redirect",
    "http-status",
    "content-type",
    "content-encoding",
    "response-too-large",
    "response-malformed",
    "response-schema-drift",
    "unexpected",
]

# Firefox extension IDs are either email-style application IDs or braced UUIDs.
# This deliberately rejects wildcard IDs and any display/URL-like provider value.
_EMAIL_STYLE_EXTENSION_ID = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,126}@[A-Za-z0-9][A-Za-z0-9.-]{0,126}$"
)
_BRACED_UUID_EXTENSION_ID = re.compile(
    r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$"
)


class AmoTransportError(RuntimeError):
    """A classified fixed-origin transport failure without provider detail."""

    def __init__(
        self,
        reason_code: Literal["timeout", "network", "tls", "redirect", "response-too-large"],
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True)
class AmoHttpResponse:
    """Decoded transport envelope; it never exposes a live client or response URL."""

    status_code: int
    content_type: str | None
    content_encoding: str | None
    body: bytes


class AmoSearchTransport(Protocol):
    """Fixed-destination transport interface suitable for deterministic tests."""

    def get(self, *, url: str, headers: Mapping[str, str]) -> AmoHttpResponse: ...


@dataclass(frozen=True)
class AmoExtensionResult:
    """The complete, inert local projection of one AMO result."""

    guid: str
    name: str
    version: str


@dataclass(frozen=True)
class AmoSearchResult:
    """One available projection or a stable local-unavailable disposition."""

    availability: AmoAvailability
    reason_code: AmoFailureReason
    results: tuple[AmoExtensionResult, ...] = ()
    cache_hit: bool = False


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    results: tuple[AmoExtensionResult, ...]


class AmoSearchRateLimiter:
    """Bounded process-memory reservation counter for outbound AMO attempts."""

    def __init__(
        self,
        *,
        window_seconds: float = AMO_RATE_LIMIT_WINDOW_SECONDS,
        max_requests_per_session: int = AMO_MAX_REQUESTS_PER_SESSION,
        max_requests_global: int = AMO_MAX_REQUESTS_GLOBAL,
        max_tracked_sessions: int = AMO_MAX_TRACKED_SESSIONS,
        clock: Clock = monotonic,
    ) -> None:
        if (
            window_seconds <= 0
            or max_requests_per_session <= 0
            or max_requests_global <= 0
            or max_tracked_sessions <= 0
        ):
            raise ValueError("AMO rate-limit bounds must be positive")
        self._window_seconds = window_seconds
        self._max_requests_per_session = max_requests_per_session
        self._max_requests_global = max_requests_global
        self._max_tracked_sessions = max_tracked_sessions
        self._clock = clock
        self._global_requests: deque[float] = deque()
        self._session_requests: dict[str, deque[float]] = {}
        self._lock = threading.RLock()

    def reserve(self, session_hash: str) -> bool:
        """Reserve exactly one AMO attempt, or reject it before transport starts."""

        now = self._clock()
        with self._lock:
            self._clear_expired_locked(now)
            session_requests = self._session_requests.get(session_hash)
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
                self._session_requests[session_hash] = session_requests
            self._global_requests.append(now)
            session_requests.append(now)
            return True

    def clear_session(self, session_hash: str) -> int:
        """Forget counters for one ended browser session without retaining its secret."""

        with self._lock:
            requests = self._session_requests.pop(session_hash, None)
            return len(requests) if requests is not None else 0

    def clear_all(self) -> int:
        """Clear process-memory state at controlled application shutdown."""

        with self._lock:
            count = len(self._global_requests)
            self._global_requests.clear()
            self._session_requests.clear()
            return count

    def _clear_expired_locked(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._global_requests and self._global_requests[0] <= cutoff:
            self._global_requests.popleft()
        expired_sessions: list[str] = []
        for session_hash, requests in self._session_requests.items():
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if not requests:
                expired_sessions.append(session_hash)
        for session_hash in expired_sessions:
            del self._session_requests[session_hash]


class HttpxAmoSearchTransport:
    """TLS-verifying, proxy-free and redirect-free HTTPX transport for AMO search."""

    def __init__(
        self,
        *,
        timeout_seconds: float = AMO_TIMEOUT_SECONDS,
        client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("AMO timeout must be positive")
        self._timeout_seconds = timeout_seconds
        self._client_factory = client_factory

    def get(self, *, url: str, headers: Mapping[str, str]) -> AmoHttpResponse:
        """Issue the one allowlisted request after independently checking its shape."""

        if not _is_fixed_search_url(url) or dict(headers) != AMO_FIXED_HEADERS:
            raise AmoTransportError("network")
        client = self._new_client()
        try:
            with client.stream("GET", url, headers=dict(AMO_FIXED_HEADERS)) as response:
                if 300 <= response.status_code < 400:
                    raise AmoTransportError("redirect")
                if response.status_code != 200:
                    return AmoHttpResponse(
                        status_code=response.status_code,
                        content_type=None,
                        content_encoding=None,
                        body=b"",
                    )
                content_type = response.headers.get("content-type")
                content_encoding = response.headers.get("content-encoding")
                # The adapter below maps these two fixed-envelope facts to its
                # public stable codes.  Do not stream a body the contract says
                # must be rejected before interpretation.
                if not _is_json_content_type(content_type) or not _is_accepted_content_encoding(
                    content_encoding
                ):
                    return AmoHttpResponse(
                        status_code=response.status_code,
                        content_type=content_type,
                        content_encoding=content_encoding,
                        body=b"",
                    )
                return AmoHttpResponse(
                    status_code=response.status_code,
                    content_type=content_type,
                    content_encoding=content_encoding,
                    body=_bounded_response_body(response),
                )
        except AmoTransportError:
            raise
        except httpx.TimeoutException as error:
            raise AmoTransportError("timeout") from error
        except httpx.HTTPError as error:
            raise AmoTransportError("network") from error
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


class AmoSearchAdapter:
    """Normalize explicit AMO search into a safe, session-private local result."""

    def __init__(
        self,
        *,
        transport: AmoSearchTransport | None = None,
        rate_limiter: AmoSearchRateLimiter | None = None,
        clock: Clock = monotonic,
    ) -> None:
        self._transport = transport or HttpxAmoSearchTransport()
        self._rate_limiter = rate_limiter or AmoSearchRateLimiter(clock=clock)
        self._clock = clock
        self._cache: OrderedDict[str, OrderedDict[str, _CacheEntry]] = OrderedDict()
        self._cache_lock = threading.RLock()

    def search(
        self,
        *,
        query: object,
        locale: object,
        session_secret: object,
        cancellation_check: CancellationCheck = lambda: False,
    ) -> AmoSearchResult:
        """Run at most one bounded AMO request; all failures remain local and value-safe."""

        if _cancelled(cancellation_check):
            return _unavailable("cancelled")
        normalized_query = normalize_amo_lookup_query(query)
        if normalized_query is None:
            return _unavailable("query-invalid")
        amo_locale = amo_locale_for(locale)
        if amo_locale is None:
            return _unavailable("locale-unsupported")
        session_hash = _session_hash(session_secret)
        if session_hash is None:
            return _unavailable("unexpected")
        lookup_hash = _lookup_hash(session_secret, normalized_query, amo_locale)
        if lookup_hash is None:
            return _unavailable("unexpected")

        cached = self._cached(session_hash, lookup_hash)
        if cached is not None:
            return AmoSearchResult("available", "available", cached, cache_hit=True)
        if _cancelled(cancellation_check):
            return _unavailable("cancelled")
        if not self._rate_limiter.reserve(session_hash):
            return _unavailable("rate-limited")
        if _cancelled(cancellation_check):
            return _unavailable("cancelled")

        try:
            response = self._transport.get(
                url=build_amo_search_url(normalized_query, amo_locale),
                headers=AMO_FIXED_HEADERS,
            )
        except AmoTransportError as error:
            return _unavailable(error.reason_code)
        except httpx.TimeoutException:
            return _unavailable("timeout")
        except httpx.HTTPError:
            return _unavailable("network")
        except Exception:
            return _unavailable("unexpected")
        if _cancelled(cancellation_check):
            return _unavailable("cancelled")
        if response.status_code != 200:
            return _unavailable("redirect" if 300 <= response.status_code < 400 else "http-status")
        if not _is_json_content_type(response.content_type):
            return _unavailable("content-type")
        if not _is_accepted_content_encoding(response.content_encoding):
            return _unavailable("content-encoding")
        if not isinstance(response.body, bytes) or len(response.body) > AMO_MAX_RESPONSE_BYTES:
            return _unavailable("response-too-large")
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except UnicodeDecodeError, json.JSONDecodeError:
            return _unavailable("response-malformed")
        try:
            results = _normalize_response(payload, amo_locale)
        except ValueError:
            return _unavailable("response-schema-drift")
        self._store_cached(session_hash, lookup_hash, results)
        return AmoSearchResult("available", "available", results)

    def clear_session(self, session_secret: object) -> int:
        """Clear cache/rate state when the host ends one browser session."""

        session_hash = _session_hash(session_secret)
        if session_hash is None:
            return 0
        with self._cache_lock:
            cache_entries = self._cache.pop(session_hash, None)
        rate_entries = self._rate_limiter.clear_session(session_hash)
        return (len(cache_entries) if cache_entries is not None else 0) + rate_entries

    def clear_all(self) -> int:
        """Clear all process-lifetime cache and rate state during controlled shutdown."""

        with self._cache_lock:
            cache_entries = sum(len(entries) for entries in self._cache.values())
            self._cache.clear()
        return cache_entries + self._rate_limiter.clear_all()

    def _cached(self, session_hash: str, lookup_hash: str) -> tuple[AmoExtensionResult, ...] | None:
        now = self._clock()
        with self._cache_lock:
            entries = self._cache.get(session_hash)
            if entries is None:
                return None
            entry = entries.get(lookup_hash)
            if entry is None:
                return None
            if entry.expires_at <= now:
                del entries[lookup_hash]
                if not entries:
                    del self._cache[session_hash]
                return None
            self._cache.move_to_end(session_hash)
            entries.move_to_end(lookup_hash)
            return entry.results

    def _store_cached(
        self,
        session_hash: str,
        lookup_hash: str,
        results: tuple[AmoExtensionResult, ...],
    ) -> None:
        entry = _CacheEntry(self._clock() + AMO_CACHE_TTL_SECONDS, results)
        with self._cache_lock:
            entries = self._cache.get(session_hash)
            if entries is None:
                if len(self._cache) >= AMO_MAX_TRACKED_SESSIONS:
                    self._cache.popitem(last=False)
                entries = OrderedDict()
                self._cache[session_hash] = entries
            entries[lookup_hash] = entry
            entries.move_to_end(lookup_hash)
            while len(entries) > AMO_CACHE_MAX_ENTRIES_PER_SESSION:
                entries.popitem(last=False)
            self._cache.move_to_end(session_hash)


def normalize_amo_lookup_query(value: object) -> str | None:
    """Return the only user-controlled AMO value, or reject it without a request."""

    if not isinstance(value, str):
        return None
    normalized = unicodedata.normalize("NFC", value).strip()
    if not normalized or len(normalized) > AMO_QUERY_MAXIMUM_CHARACTERS:
        return None
    if _has_c0_or_c1_control(normalized):
        return None
    try:
        normalized.encode("utf-8")
    except UnicodeEncodeError:
        return None
    return normalized


def amo_locale_for(locale: object) -> str | None:
    """Map one authored BPM locale to its exact allowlisted AMO locale."""

    return AMO_LOCALE_MAP.get(locale) if isinstance(locale, str) else None


def build_amo_search_url(query: str, amo_locale: str) -> str:
    """Build the canonical one-and-only AMO request URL from already validated values."""

    return f"{AMO_SEARCH_ENDPOINT}?{urlencode(AMO_FIXED_QUERY | {'q': query, 'lang': amo_locale})}"


def is_verified_extension_guid(value: object) -> bool:
    """Check the strictly bounded Firefox extension identifier accepted from AMO."""

    if (
        not isinstance(value, str)
        or not value
        or _has_c0_or_c1_control(value)
        or value != value.strip()
    ):
        return False
    if not _has_maximum_utf8_bytes(value, AMO_GUID_MAXIMUM_BYTES):
        return False
    return bool(
        _EMAIL_STYLE_EXTENSION_ID.fullmatch(value) or _BRACED_UUID_EXTENSION_ID.fullmatch(value)
    )


def _normalize_response(payload: object, amo_locale: str) -> tuple[AmoExtensionResult, ...]:
    if not isinstance(payload, dict):
        raise ValueError("AMO payload must be an object")
    upstream_results = payload.get("results")
    if not isinstance(upstream_results, list) or len(upstream_results) > AMO_RESULTS_MAXIMUM:
        raise ValueError("AMO results are invalid")
    normalized: list[AmoExtensionResult] = []
    seen_guids: set[str] = set()
    for upstream in upstream_results:
        if not isinstance(upstream, dict):
            raise ValueError("AMO result must be an object")
        guid = upstream.get("guid")
        name = _localized_name(upstream.get("name"), amo_locale)
        version = _version(upstream.get("current_version"))
        if (
            not isinstance(guid, str)
            or not is_verified_extension_guid(guid)
            or name is None
            or version is None
        ):
            raise ValueError("AMO result fields are invalid")
        canonical_guid = guid.casefold()
        if canonical_guid in seen_guids:
            raise ValueError("AMO result GUID is duplicated")
        seen_guids.add(canonical_guid)
        normalized.append(AmoExtensionResult(guid=guid, name=name, version=version))
    return tuple(normalized)


def _localized_name(value: object, amo_locale: str) -> str | None:
    if not isinstance(value, dict) or amo_locale not in value:
        return None
    requested = value[amo_locale]
    if requested is None:
        return _bounded_nonempty_text(value.get("_default"), AMO_NAME_MAXIMUM_BYTES)
    return _bounded_nonempty_text(requested, AMO_NAME_MAXIMUM_BYTES)


def _version(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    return _bounded_nonempty_text(value.get("version"), AMO_VERSION_MAXIMUM_BYTES)


def _bounded_nonempty_text(value: object, maximum_bytes: int) -> str | None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or not _has_maximum_utf8_bytes(value, maximum_bytes)
        or _has_c0_or_c1_control(value)
    ):
        return None
    return value


def _is_fixed_search_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "addons.mozilla.org"
            or parsed.port not in {None, 443}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path != AMO_SEARCH_PATH
            or parsed.fragment
        ):
            return False
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return False
    query = dict(pairs)
    if len(query) != len(pairs) or set(query) != {*AMO_FIXED_QUERY, "q", "lang"}:
        return False
    if any(query[key] != value for key, value in AMO_FIXED_QUERY.items()):
        return False
    normalized_query = normalize_amo_lookup_query(query["q"])
    if normalized_query is None or query["lang"] not in AMO_LOCALE_MAP.values():
        return False
    return url == build_amo_search_url(normalized_query, query["lang"])


def _bounded_response_body(response: httpx.Response) -> bytes:
    body = bytearray()
    for block in response.iter_bytes(chunk_size=64 * 1024):
        body.extend(block)
        if len(body) > AMO_MAX_RESPONSE_BYTES:
            raise AmoTransportError("response-too-large")
    return bytes(body)


def _is_json_content_type(value: str | None) -> bool:
    return (
        isinstance(value, str) and value.split(";", 1)[0].strip().casefold() == "application/json"
    )


def _is_accepted_content_encoding(value: str | None) -> bool:
    return value is None or value.strip().casefold() == "identity"


def _has_c0_or_c1_control(value: str) -> bool:
    return any(0 <= ord(character) <= 31 or 127 <= ord(character) <= 159 for character in value)


def _has_maximum_utf8_bytes(value: str, maximum_bytes: int) -> bool:
    try:
        return len(value.encode("utf-8")) <= maximum_bytes
    except UnicodeEncodeError:
        return False


def _session_hash(session_secret: object) -> str | None:
    if not isinstance(session_secret, str) or not session_secret:
        return None
    try:
        return hashlib.sha256(session_secret.encode("utf-8")).hexdigest()
    except UnicodeEncodeError:
        return None


def _lookup_hash(session_secret: object, query: str, amo_locale: str) -> str | None:
    if not isinstance(session_secret, str) or not session_secret:
        return None
    try:
        return hmac.new(
            session_secret.encode("utf-8"),
            f"{query}\x00{amo_locale}".encode(),
            hashlib.sha256,
        ).hexdigest()
    except UnicodeEncodeError:
        return None


def _cancelled(cancellation_check: CancellationCheck) -> bool:
    try:
        return bool(cancellation_check())
    except Exception:
        return True


def _unavailable(reason_code: AmoFailureReason) -> AmoSearchResult:
    return AmoSearchResult("unavailable", reason_code)
