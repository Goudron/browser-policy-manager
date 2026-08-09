# BPM 0.9.3 Web-Evidence Security Closure

Date: 2026-07-30
Backlog item: `BPM093-M9-05`
Status: implemented offline adversarial suite; no route, browser UI, worker invocation or live
Brave request is added.

## Closure scope

M8 recorded `AI093-T02` (fixed-provider SSRF, redirect, DNS/IP and proxy safety) and `AI093-T13`
(consent, sanitization, external labelling and local-only failure) as M9 release blockers. That
review remains a dated pre-M9 record. This review closes those two M9 findings with the M9-01--M9-04
contracts and a fixed suite of in-process transport tests; it does not alter the remaining M10, M11
or M13 release blockers.

The retriever still admits a web operation only after the caller selects `request_web`, the
deterministic BPM scope gate allows it, the disabled-by-default BYOK configuration is available,
and M9-02 validates then consumes an exact-question, session-bound, one-use approval. Invalid
authorization cannot spend a provider-rate reservation. Off-topic, invalid-consent and
rate-limited paths, as well as cancellation observed before provider work, make zero provider
calls. Ordinary documentation search is not called, imported or changed by this path.

## Cost, cancellation and privacy guardrails

One process-lifetime `WebEvidenceRateLimiter` is injected into the retriever. It atomically limits
provider attempts to five per server-owned session and twenty overall per rolling sixty seconds;
at most 32 active session counters are retained. An exhausted limit leaves the consent usable and
returns only `assistant_web_rate_limited`. Counters contain timestamps and opaque server session
identifiers, can be pruned or cleared, and never contain questions, tokens or provider text. M10
must keep one such limiter for the server lifetime when it composes the route.

The retriever checks an injected cancellation probe before scope, before network admission and after
provider parsing. A failed probe is cancellation, not permission to proceed. Cancellation known
before the request creates no network work; cancellation after the provider response drops the
sanitized evidence rather than returning a lease. M9 intentionally has no asynchronous route or
in-flight HTTP cancellation; M10 must connect the stream-disconnect signal to this boundary.

Provider exceptions, malformed bodies, redirects, timeout/TLS/DNS failures and post-filter or
sanitization failures collapse to a fixed local-only status. Neither a token, question, exception
message nor raw response body is returned. Successful data remains a request-lifetime
`external_untrusted` citation with provider ID, canonical Mozilla URL, source age and retrieval
time. M9-04 requires local answer-ready evidence and separately cited external claims before any
later model answer can use it.

## Fixed adversarial evidence

`tests/integration/ai/incubation/test_web_evidence_security.py` uses only fakes. It proves off-topic refusal before
network; private, link-local, IPv6, userinfo, non-default-port and path-bypass URLs cannot widen
the sole provider destination; six locale-specific prompt overrides are rejected while preserving
the request locale's search language; per-session and global limits preserve consent; pre/post
provider cancellation fails local-only; provider errors are redacted; and successful evidence has
explicit external provenance. Existing M9-03 tests cover fixed endpoint, TLS, disabled proxy
inheritance, redirect handling, bounded response reads and no result-url fetching. M9-04 tests
prove local-first merge and strict external citation binding.

No test uses a Brave credential, performs DNS, connects to the internet or fetches a result URL.
The normative closure record is
`documentation/config/bpm-web-evidence-security-contract-0.9.3.json`.
