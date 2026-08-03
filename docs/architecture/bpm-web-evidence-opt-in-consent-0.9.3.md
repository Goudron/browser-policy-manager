# BPM 0.9.3 Optional Web-Evidence Opt-In and Consent

Date: 2026-07-30
Backlog item: `BPM093-M9-02`
Status: implemented as a transport-neutral, memory-only boundary. It adds no HTTP route, browser UI,
provider request or ordinary-search change.

## Decision

Web evidence remains disabled by default. An administrator can only make it eligible by setting
`BPM_WEB_EVIDENCE_ENABLED=true` and supplying their own
`BPM_BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN` in server configuration. BPM ships no credential. The
token is omitted from configuration representations and is never returned by the consent API; the
future M9-03 server adapter is its only intended consumer.

An absent/blank token or disabled feature is a normal `local_only` result. No question is promoted
to web mode silently, and these states do not attempt DNS, network, ordinary search or a fallback
provider.

## Per-question disclosure and authorization

Before any web request, the controller calls `disclose` with its opaque server-owned session,
active locale and unmodified question. BPM returns a UI-ready disclosure with:

- the exact question that would leave the machine;
- Brave Search API as the provider and Brave Software, Inc. in the United States as recipient;
- locale-derived search language and the fixed Mozilla filter/bounded parameters;
- the notice that standard Brave query logs can be retained for up to 90 days; and
- explicit exclusions: conversation history, local evidence/citations, BPM profiles/database/files,
  session identifiers, location and the subscription token.

Only a separate affirmative `approve` transition yields an opaque authorization. It lasts five
minutes and can be consumed once only when the same server session, locale and byte-exact question
are supplied. Session clearing, expiry, mismatch, process restart and every consume attempt revoke
it. Pending records are capped at 32 and retain a per-process HMAC digest, never the raw question;
raw text exists only in the immediate disclosure returned to the controller. The accepted question
is bounded to 400 characters and 50 whitespace-delimited words.

This is intentionally stricter than a session-wide switch. It applies independently to English,
Russian, German, Simplified Chinese, French and Spanish; cross-locale use is rejected.

## Handoff

M9-03 must first apply the existing BPM scope gate, then consume this authorization before it builds
its one fixed Brave request. It cannot reuse consent, add a route/UI here, send provider results to
the browser, or use web evidence without this record. The provider-policy ADR remains the source of
request, source-filter, sanitization and transient-retention controls.

The normative record is
`documentation/config/bpm-web-evidence-opt-in-consent-contract-0.9.3.json`.
