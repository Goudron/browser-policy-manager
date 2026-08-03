# BPM 0.9.3 External Evidence: Deferred Product Surface

Backlog item: `BPM093-M12A-04`.

The released assistant remains a local, documentation-grounded chat. The external-evidence
implementation and BYOK diagnostics are retained in the repository for a separately approved
post-0.9.3 investigation, but 0.9.3 ships no reader switch, web-mode script or browser path that can
request external evidence. This does not replace the local RAG retrieval or deterministic
documentation search.

## Retained implementation boundary

The same-origin assistant API and the guarded BYOK configuration remain retained implementation
work, not a 0.9.3 user-facing capability. The release transport always admits chat with
`web_mode=local_only` and does not read or mutate the server mode. The historical M12B-06 switch
and tab-local preference are not emitted into generated documentation pages.

Reading or changing mode never contacts the provider. Mutations use the existing same-origin JSON
guard and the opaque HttpOnly, SameSite=Strict assistant session.

## Future investigation boundary

Any future reactivation must begin with a distinct product decision on provider independence,
operating cost, privacy and support ownership. It must then re-approve the retained scope gate,
server configuration, rate bounds, Mozilla allowlist, redirect rejection, proxy isolation,
result filtering and content sanitization. BPM never follows a provider result URL.

The conservative merger serializes current local documentation first. External records are marked
untrusted and lower priority. Stale, empty or over-budget data falls back to the local answer;
unresolved conflict causes abstention. Provider, network, schema and sanitization failures also
preserve the working local-only assistant and do not fall back to ordinary search or another
network destination.

## Historical output and retention safeguards

The local model must return locally grounded product text with local citations and optional,
separately structured external claims with their own external citations. Server validation resolves
both citation namespaces before output. Streaming uses opaque handles; an external source resolver
exposes only its reviewed allowlisted URL, title, locale, source kind and provider identifier. When
no external claim exists, the pre-existing local final-event and local-source shapes are unchanged.

External snippets and merged model context are request-local leases and are cleared at terminal
completion, cancellation or error. Only the validated local answer and local citations may enter
multi-turn conversation context.

The browser renders external sources only after its independent HTTPS host/path check. It opens
each accepted URL in a new isolated browsing context with `noopener noreferrer` and de-duplicates
opaque source IDs before resolving their server-owned metadata. Invalid, malformed or unapproved
URLs never become links.

The normative machine-readable record is
`documentation/config/documentation-assistant-external-evidence-release-contract-0.9.3.json`.

## Retained development configuration

The project-root `.env` is ignored and is the only documented development handoff for the BYOK
credential. A maintainer who wants the optional path sets `BPM_WEB_EVIDENCE_ENABLED=true` and
`BPM_BRAVE_SEARCH_API_SUBSCRIPTION_TOKEN` there before running `make dev`. The new
`ai-web-sources-check-dev` prerequisite reports one of three content-free states: disabled, missing
credential, or available. It exits successfully for every state so missing optional configuration
does not prevent the local assistant, documentation or deterministic search from starting.

The readiness check does not contact Brave and cannot claim that a configured credential is
accepted by the provider. It remains a content-free developer diagnostic only; no 0.9.3 UI can
enable the provider. Neither the command output nor the browser status contains the credential.
