# BPM 0.9.6 AMO Privacy And Security Contract

Date: 2026-08-20

Backlog item: `BPM096-M2-08`

Status: active planning contract; it deliberately adds no AMO client, API route, browser request,
template, locale key, CSP change, profile field, or save behavior.

## Purpose and Mozilla API recheck

M7 may offer an optional, explicit extension lookup in the **Extensions** step.  This record fixes
the only permissible AMO boundary before that work starts.  It does not change the existing
`ExtensionSettings` editor or the external Firefox AMO canary.  The canary lets Firefox download a
fixed XPI after policy activation; BPM itself must never download an XPI.

The Mozilla-maintained documentation was rechecked on 2026-08-20:

- [External API](https://mozilla.github.io/addons-server/topics/api/index.html) identifies normal
  production as `https://addons.mozilla.org/api/v5/`.
- [Add-ons API](https://mozilla.github.io/addons-server/topics/api/addons.html) defines public
  `GET /api/v5/addons/search/`, a `q` maximum of 100 characters, `app`, `type`, pagination, and
  `lang` query parameters.
- [API overview](https://mozilla.github.io/addons-server/topics/api/overview.html) defines the
  localized-object response shape for `lang` and warns that v5 request and response formats are
  not frozen.

Consequently, only a fixed production search request and a small local projection are permitted.
A changed consumed field or envelope is an unavailable result, never a best-effort interpretation.

## Request, transport, and privacy boundary

Lookup is user initiated only.  The browser sends a future same-origin BPM request; only BPM may
make the one AMO request.  The AMO request contains the typed lookup text and mapped UI locale,
plus the fixed public search filters below.  It contains no profile ID, profile name, schema,
policy, preference, extension configuration, user identity, session identifier, browser IP header,
cookie, credential, bearer token, referrer, origin, or caller-controlled header/URL.

The AMO URL is assembled from the fixed origin, exact path, and fixed allowlisted query names and
values.  A caller cannot choose a host, port, scheme, path, page, filter, locale, redirect target,
or proxy.  TLS verification is required; environment proxy inheritance and redirects are disabled.
A non-200 response, redirect, unsupported content type/encoding, timeout, TLS/network error, or
response over the bound size terminates the attempt.  There is no retry or secondary provider.

The normalized lookup value is nonempty after trimming, at most 100 Unicode characters, and has no
C0/C1 control character.  It is the only free-form value forwarded to Mozilla.  BPM supports only
its six authored locales; it maps `en` to AMO `en-US` and otherwise uses the exact supported AMO
locale shown below.  Empty queries are rejected locally so AMO's recommendation-style default
search is never requested.

## Response, rendering, cache, and availability boundary

Only `results` and the three value paths in the fixture are consumed.  A response is accepted only
when the root is an object with a list of no more than ten results, every rendered result supplies a
bounded text GUID, a valid localized `name` object for the requested/fallback locale, and a bounded
`current_version.version` string.  The local projection has exactly `guid`, `name`, and `version`.
All other fields—including URLs, icons, authors, descriptions, Markdown, ratings, promotions,
privacy/data-collection data, and every version-file/download value—are discarded before output.
Unknown added fields have no behavior; a missing, changed-type, malformed, oversized, duplicate, or
otherwise unnormalizable consumed value is upstream schema drift and discards the complete result.

The later browser surface renders the projection as text only, with auto-escaped/template text
nodes.  It never renders provider HTML, Markdown, URLs, image/icon URLs, or active content, and it
does not turn a result into an AMO navigation or download action.  Its AMO-specific CSP constraints
require `connect-src 'self'` and no AMO host source in any directive: no browser request, script,
style, font, frame, image, or XPI request may target AMO.  This contract does not alter BPM's
current CSP.

One valid result set may be kept only in an in-memory, per-browser-session cache keyed by a
session-secret hash of normalized query and AMO locale.  It expires after five minutes, contains at
most ten entries per session, is never shared between sessions, persisted, put into diagnostics, or
served stale.  Queries and response values are never logged.  Operational logs may contain only a
fixed outcome code, cache-hit boolean, and coarse elapsed-time bucket; they must not contain a
query, locale, result count/value, URL, header, client address, cookie, credential, or profile
data.

AMO is optional.  Manual extension configuration (GUID plus the M7-validated install-URL path) is
always available before, during, after, and without lookup.  A selected result may copy only its
text GUID into an unsaved manual draft; it provides no install URL, trust endorsement, saved
provenance, or authority to bypass M7 validation.  BPM never fetches an XPI, follows an AMO result
URL, or waits for AMO while opening, validating, importing, exporting, or saving a profile.  A
Firefox policy consumer may later fetch a manually validated install URL; that external behavior is
what the separate AMO canary covers, not this lookup boundary.

Every local rejection, rate limit, cache miss failure, transport/TLS/HTTP failure, malformed or
drifted upstream response, cancellation, and unexpected implementation exception is a localized,
accessible `manual-entry` state with local manual entry and an optional explicit retry.  No failure
is retried automatically, converted to a stale result, or made a profile/save blocker.

## Normative compact fixture

<!-- bpm096-amo-privacy-security-contract-v1 -->
```json
{
  "contract_id": "bpm096-amo-privacy-security",
  "contract_version": 1,
  "status": "planning-only-no-runtime-change",
  "future_owner": "BPM096-M7-extensions-and-amo",
  "upstream": {
    "origin": "https://addons.mozilla.org",
    "path": "/api/v5/addons/search/",
    "method": "GET",
    "query": {
      "fixed": {"app": "firefox", "type": "extension", "page": "1", "page_size": "10", "sort": "relevance"},
      "user_value": "q",
      "locale_value": "lang",
      "allowed_locale_map": {"en": "en-US", "ru": "ru", "de": "de", "es-ES": "es-ES", "fr": "fr", "zh-CN": "zh-CN"},
      "q_minimum_characters": 1,
      "q_maximum_characters": 100,
      "q_control_characters": "forbidden",
      "empty_query_request": "forbidden"
    }
  },
  "transport": {
    "tls_verify": true,
    "follow_redirects": false,
    "trust_env": false,
    "timeout_seconds": 5,
    "retry_attempts": 0,
    "max_response_bytes": 131072,
    "accepted_status": 200,
    "accepted_content_type": "application/json",
    "accepted_content_encoding": ["absent", "identity"],
    "forward_browser_or_profile_headers": false,
    "fixed_request_headers": {"Accept": "application/json", "Accept-Encoding": "identity"},
    "forbidden_request_headers": ["Authorization", "Cookie", "Referer", "Origin", "X-Forwarded-For", "X-Real-IP"]
  },
  "response": {
    "root_required": ["results"],
    "results_maximum": 10,
    "local_projection": ["guid", "name", "version"],
    "consumed_paths": ["results[].guid", "results[].name", "results[].current_version.version"],
    "localized_name": "requested-locale-nonempty-text-or-requested-null-plus-_default-fallback-text",
    "maximum_guid_utf8_bytes": 255,
    "maximum_name_utf8_bytes": 512,
    "maximum_version_utf8_bytes": 255,
    "discarded_upstream_fields": ["url", "icons", "icon_url", "authors", "description", "summary", "homepage", "support_url", "previews", "ratings", "promoted", "current_version.file"],
    "consumed_schema_drift": "discard-complete-result-to-manual-entry",
    "pagination_or_result_urls_followed": false
  },
  "rate_limit": {"window_seconds": 60, "per_session_requests": 5, "global_requests": 20, "max_tracked_sessions": 32},
  "cache": {
    "scope": "per-browser-session-memory-only",
    "key": "session-secret-sha256(normalized-query,amo-locale)",
    "ttl_seconds": 300,
    "max_entries_per_session": 10,
    "cross_session_sharing": false,
    "persistence": "forbidden",
    "stale_response": "forbidden"
  },
  "browser_security": {
    "amo_direct_browser_request": false,
    "csp_connect_src": "'self'",
    "amo_host_allowed_by_any_csp_directive": false,
    "remote_asset_or_xpi_request": false,
    "provider_rendering": "text-only-no-html-markdown-url-or-active-content"
  },
  "data_and_logging": {
    "amo_data": ["explicit-typed-query", "mapped-locale", "fixed-public-search-filters"],
    "profile_data_disclosure": "forbidden",
    "query_or_response_persistence": "forbidden",
    "allowed_log_fields": ["outcome-code", "cache-hit", "coarse-elapsed-time-bucket"],
    "forbidden_log_fields": ["query", "locale", "result-count", "result-values", "urls", "headers", "client-address", "cookies", "credentials", "profile-data"]
  },
  "manual_and_save_boundary": {
    "manual_entry_always_available": true,
    "manual_fields": ["extension-guid", "validated-install-url"],
    "selected_result_can_copy": ["guid"],
    "amo_result_install_url": "forbidden",
    "bpm_xpi_fetch": "forbidden",
    "save_or_validation_calls_amo": false,
    "result_provenance_persisted": false,
    "amo_availability_blocks_profile_operation": false
  },
  "failure": {
    "state": "manual-entry",
    "automatic_retry": false,
    "reasons": ["not-requested", "query-invalid", "locale-unsupported", "rate-limited", "cancelled", "timeout", "network", "tls", "redirect", "http-status", "content-type", "content-encoding", "response-too-large", "response-malformed", "response-schema-drift", "unexpected"],
    "all_failures": "closed-to-localized-manual-entry-with-optional-explicit-retry"
  }
}
```

## Delivery and proof boundary

M7 owns the HTTPX adapter, same-origin API/UI, all six locale states, CSP implementation, manual
GUID/install-URL validation, and mocked transport/browser tests.  Its tests must prove the fixed
URL/query map; proxy, redirect, cookie/credential, SSRF, response-drift, size, timeout, rate,
cache, logging, CSP, inert-rendering, no-XPI-fetch, no-profile-disclosure, and save-independence
rules above.  `make test-firefox-live-amo` remains a manually invoked external Firefox canary and
is not a lookup test or a deterministic save-time gate.
