# BPM 0.9.3 Grounded Conversation API And State Machine

Original backlog item: `BPM093-M7-01`
Delivery: `BPM093-M12A-01` implements this transport contract; runtime assembly remains
`BPM093-M12A-02` and optional external evidence remains `BPM093-M12A-04`.

## V1 Surface

The assistant API uses schema version `1` on the same BPM origin. Every request supplies
`api_version: 1`; JSON responses and SSE events repeat it. A newer or absent version fails with
`assistant_api_version_unsupported`; a client is never silently interpreted using a guessed schema.

The frozen paths are safe status, asynchronous ask, request-local SSE stream, cancellation,
conversation clear, and an approved-source lookup scoped to a completed opaque request. The source
lookup returns only title, public URL, locale and a display-safe excerpt of at most 1,200 characters.
It cannot reveal raw chunks, scores, vectors, prompts, file paths, hashes, model/runtime internals or
unapproved evidence.

The API is same-origin only. It is not a proxy for `llama.cpp`, an external provider, a local port,
or a model server. The server owns opaque request/source identifiers and an in-memory same-origin
session; clients cannot provide session, evidence, citation, model, tool, prompt, path or worker
fields.

## Request State Machine

One request moves through `accepted`, `scope_check`, `evidence_check`, `generating`, and
`validating`, ending exactly once as `answer`, `clarify`, `abstain`, `refuse`, `cancelled`, or
`error`. Scope/evidence/citation failures, cancellation and unavailable artifacts stop before a
confident answer. Partial text is always incomplete, never an answer. Each transition increments
`state_epoch` so a browser discards stale events.

The fixed bounds are 48,152 request bytes, 4,000 question characters, sixteen chronological
dialogue entries (eight completed user-question/assistant-answer pairs), one
active and one queued request, the selected worker's 96 output-token maximum, and a 1,200-character
source excerpt. Only supported BPM locales are accepted. `request_web` means an explicit request for
future web capability; until M9 exists it makes zero network calls and terminates local-only with a
stable `assistant_web_not_available` outcome.

SSE emits only `accepted`, safe localized `progress`, exactly one terminal `final`, `cancelled`, or
`error` event. It never streams raw model tokens, prompts, evidence, exceptions or runtime details.
M7-02 through M7-06 implement retrieval, context, citation checks, streaming and observability
behind this contract. M8 implements scope/origin/privacy enforcement. M12A-01 binds those pieces to
the same-origin HTTP API through opaque cookie/session ownership; it exposes no model, index or
provider endpoint and starts no worker during status, page load, ordinary search or rejected
admission. Until M12A-02 assembles verified runtime dependencies, its default is the explicit
`assistant_unavailable` fallback. Ordinary documentation search, `/health/ready`, and local worker
startup remain independent.

The normative machine-readable contract is
`documentation/config/grounded-conversation-api-contract-0.9.3.json`.
