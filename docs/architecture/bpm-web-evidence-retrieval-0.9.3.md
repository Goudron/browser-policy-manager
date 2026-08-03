# BPM 0.9.3 Optional Web-Evidence Retrieval and Sanitization

Date: 2026-07-30
Backlog item: `BPM093-M9-03`
Status: implemented as an isolated Brave LLM Context adapter. It adds neither an assistant route nor
a browser UI, and tests do not make live provider calls.

## Admission and transport

`ScopedWebEvidenceRetriever` accepts only a `ConversationRequest` with `web_mode=request_web`, then
runs the existing deterministic BPM scope gate and consumes the M9-02 one-use authorization bound to
that exact session, locale and question. Scope or consent failure builds no client and makes zero
provider calls. A consumed authorization cannot be retried.

The sole connection is a TLS-verified `POST` to
`https://api.search.brave.com/res/v1/llm/context`. `httpx` disables redirects and environment proxy
inheritance; the adapter accepts no caller URL, redirect, location header, country or user-agent
override. Its four fixed headers are `Accept`, `Accept-Encoding: gzip`, `Content-Type`, and the
server-owned `X-Subscription-Token`. There is one fifteen-second request attempt and no retry.
BPM never opens a returned URL, so provider data cannot cause a connection to a private, link-local
or arbitrary address.

The request uses the exact disclosed question, the six-locale search-language mapping, strict
relevance, no local/POI recall, the M9-01 inline Mozilla Goggle, five URLs, 2,048 tokens, ten total
snippets and the other frozen M9-01 bounds. Brave documents this POST form, raw RAG context,
`grounding.generic`, source metadata and the relevant token/URL controls in its
[LLM Context documentation](https://api-dashboard.search.brave.com/documentation/services/llm-context).

## Quarantine

Responses must be JSON, identity/gzip encoded and at most 256 KiB. The strict schema permits only
`grounding.generic` plus matching `sources` metadata. Any nonempty POI/map/rich result fails the
whole response. Every generic item must contain only a URL, title and bounded snippets; source
metadata must contain a title, matching hostname and optional bounded age.

The adapter independently accepts only clean HTTPS default/443 URLs for the approved Mozilla
host/path pairs. Credentials, query strings, fragments, percent-encoded bytes, backslashes, dot
segments and double-slash paths are rejected. It never treats the provider Goggle as authorization.
All returned titles, age strings and snippets pass the existing active-content, encoded-control and
prompt-override sanitizer. Any validation/sanitization issue discards the complete provider result
and yields a safe `local_only` status.

Successful sanitized records carry an external-untrusted citation: provider ID, canonical source
URL, title, source age and retrieval time. They are held by a context-manager lease and the adapter
clears its references when the request ends, fails or is cancelled. The provider body is not
persisted. M9-04 alone may merge these temporary records with higher-authority local BPM evidence;
M9-03 sends no external text to the model.

The normative record is
`documentation/config/bpm-web-evidence-retrieval-contract-0.9.3.json`.
