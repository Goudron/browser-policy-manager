# BPM 0.9.3 Local AI Security And Privacy Architecture

Date: 2026-07-28

Backlog item: `BPM093-M2-05`

Status: **Accepted architecture and threat contract; local AI remains unimplemented and disabled.**

## Scope And Current-State Finding

The machine-readable source is
`documentation/config/local-ai-security-privacy-contract-0.9.3.json`. It covers the browser, BPM
controller, pre-inference scope gate, local retrieval, inference worker, verified artifact store,
ephemeral conversations, and optional web adapter.

No AI route, worker, model, index, network permission, or conversation store exists today. The
current application can enable broad CORS and defaults `CORS_ALLOW_ORIGINS` to `*`; a future AI
endpoint must not inherit that policy. It is same-origin only, uses strict JSON methods plus
Origin/Host/Fetch-Metadata and session-bound CSRF validation, and rejects failures before scope,
retrieval, inference, web access, or resource allocation. The current strict `/help/` CSP and safe
DOM-sink contract remain mandatory.

## Trust And Data Flow

```text
untrusted browser query
  -> same-origin/schema/CSRF/size/session controller
  -> pre-inference multilingual scope gate
       -> refuse/clarify (no retrieval, model, or network call)
       -> verified locale retrieval by manifest ID
       -> optional per-query-consented provider adapter (M9 only)
  -> bounded isolated local inference worker
  -> output schema + citation + scope validation
  -> plain-text segments and server-resolved /help/{locale}/ citations
```

The controller is the security authority. A model cannot approve scope, choose a path or URL,
activate artifacts, change retention, bypass quotas, resolve citations, or grant itself tools. The
worker is treated as an untrusted parser and probabilistic process even when its weights are
checksummed.

## Non-Negotiable Isolation

- The worker is a BPM-owned child process reached through a pipe, stdio, or an owner-only Unix
  socket. A TCP/HTTP listener, wildcard/LAN bind, public model API, remote inference mode, or direct
  browser-to-worker connection blocks release.
- The worker receives fixed structured input and verified read-only artifact handles. It has no BPM
  database/API handle, arbitrary filesystem access, shell, subprocess, tool/function calling, MCP,
  plugin system, or inbound/outbound network capability.
- Opaque manifest IDs, not request/model paths, select regular non-symlink files below fixed roots.
  Version, license, size, SHA-256, compatibility, and provenance are checked before activation.
- The scope gate runs before retrieval, inference, and web access. Prompt instructions alone do not
  implement this gate, and a guard model cannot replace deterministic fail-closed controls.
- All DITA, examples, retrieved chunks, web bodies, model metadata, and model output remain data.
  Instruction-looking text in those inputs receives no authority.

## Browser, API, And Output Safety

AI requests use no state-changing `GET`, broad CORS, URL query data, or ambient cross-origin access.
Unsafe operations require strict `application/json`, exact schemas, same-origin signals, and an
unpredictable session-bound CSRF header. The session is bound to locale and rotated after clear or
expiry.

The model returns a narrow schema: disposition, locale, plain-text answer segments, and citation
IDs. Raw HTML, executable Markdown, script/style/event content, data URLs, and model-created links
are invalid. BPM resolves citations against the activated manifest; the browser uses text-node
sinks under the `/help/` CSP.

## Optional Web And SSRF Boundary

Web evidence remains disabled and has no selected provider. M9 must approve one before shipping.
Each request requires explicit consent after disclosing the query and locale that will leave the
computer. Conversation history, local chunks, profile data, and unrelated identifiers are never
sent.

The adapter builds a request only for one fixed approved HTTPS provider. It accepts no user/model
URL, link following, redirect, alternate scheme, credentials, or proxy inheritance. DNS and every
connection target are checked; loopback, private, link-local, multicast, unspecified, metadata, and
local destinations are rejected for IPv4 and IPv6. Responses are byte/time/MIME/result bounded,
reduced to inert text, labelled external and untrusted, and kept separate from higher-priority local
citations. Any failure returns to local-only behavior.

## Privacy And Resources

Local mode performs zero network requests after explicit installation and emits no content
telemetry. Queries, turns, chunks, embeddings, answers, and prompts are not persisted or placed in
logs. Conversation state is bounded, memory-only, per session, clearable, expiring, and removed on
restart/unload. Diagnostics contain reason codes, versions, durations, counts, and resource values,
without content, secrets, private paths, environment values, or stack locals. Crash/core dumps,
prompt tracing, feedback learning, personalization, and conversation training are disabled.

Only one generation and one queued request are permitted on the old-laptop baseline, with a hard
3.5 GiB worker/retrieval RSS ceiling. M6/M8 must set and test input, turn, chunk, byte, token, time,
queue, and rate ceilings. Cancellation escalates to process-tree termination; limit breaches trip a
circuit breaker and cannot take down `/help/` or lexical search.

## Artifact Supply Chain And Recovery

Dependencies, runtimes, models, embeddings, and indexes require exact source, version, license,
checksum, compatibility, and available provenance/advisory evidence. Installation is explicit into
private staging, verification precedes atomic promotion, partial/mixed sets are quarantined, and the
last known-good set remains available.

On suspected compromise or protocol violation BPM cancels work, terminates the worker process tree,
clears private temporary and conversation state, revokes the session, and requires explicit
verified restart. Rollback/removal addresses only manifest-owned exact files and verifies that no
worker or listener remains. AI readiness fails closed while `/help/` and lexical search remain
ready.

## Threat Register And Evidence Owners

| ID | Threat | Owner | Required future evidence |
| --- | --- | --- | --- |
| `AI093-T01` | Direct/indirect prompt injection, jailbreak, prompt leakage | M8 | Off-topic/injection fixtures invoke inference zero times; retrieved/web instructions cannot create authority. |
| `AI093-T02` | SSRF, rebinding, redirects, local/metadata access | M9 | IPv4/IPv6/private/encoded/rebinding/redirect/proxy fixtures make zero forbidden calls. |
| `AI093-T03` | Traversal, symlinks, unsafe files, local-file reads | M5/M6 | Absolute/dot/encoded/backslash/NUL/symlink cases fail; worker sees only allowlisted artifacts. |
| `AI093-T04` | Exposed model service and cross-user/LAN invocation | M6 | Socket inventory has no AI listener; browser and unrelated processes cannot invoke worker. |
| `AI093-T05` | CSRF, CORS inheritance, cross-site calls, replay | M8 | Cross-origin/simple/missing-token/replay cases invoke no downstream stage; no unsafe `GET`. |
| `AI093-T06` | XSS, unsafe Markdown/HTML/citations | M7/M10 | Script/style/event/URL payloads render inertly; unknown citations are rejected. |
| `AI093-T07` | CPU/RAM/disk/token/queue/retry exhaustion | M6/M8 | Limits are deterministic; cancellation/timeout/RSS breach restores lexical readiness. |
| `AI093-T08` | Poisoned, stale, partial or mixed artifacts | M5/M6 | Hash/version/compatibility failures cannot activate; rollback retains one known-good set. |
| `AI093-T09` | Conversation retention, cross-session disclosure | M8 | Clear/expiry/restart/unload erase state; locale/session isolation rejects replay. |
| `AI093-T10` | Telemetry, logs, dumps, learning, disclosure | M8 | Network probe is zero in local mode; diagnostics contain no query/chunk/answer/path/token. |
| `AI093-T11` | Dependency/model/runtime/index supply chain | M6/M13 | Unapproved license/source/hash/provenance fails; locked manifests and advisory checks pass. |
| `AI093-T12` | Tools, BPM mutation, file/process/environment escape | M6/M8 | No callable escape capability exists and assistant requests cannot mutate BPM. |
| `AI093-T13` | Unsafe web ingestion, exfiltration, provider tracking | M9 | Provider sees only consented query/locale; external instructions cannot create actions/local citations. |
| `AI093-T14` | Unsafe crash/cancel/update/unload/rollback/removal | M6/M11 | State matrix fails closed and leaves no listener, worker, mixed artifact, or conversation state. |

Every register row is release-blocking until its named implementation and tests exist. The focused
M2-05 test validates this architecture contract only; it is not attack-execution evidence.

## Guidance Reviewed

- OWASP LLM Prompt Injection Prevention Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html`
- OWASP Server Side Request Forgery Prevention Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html`
- OWASP Cross-Site Request Forgery Prevention Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html`
- OWASP Content Security Policy Cheat Sheet:
  `https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html`
- SLSA v1.2 artifact-verification guidance: `https://slsa.dev/spec/v1.2/verifying-artifacts`
