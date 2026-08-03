# BPM 0.9.3 Local AI Availability And Fallback Contract

Date: 2026-07-28

Backlog item: `BPM093-M2-06`

Status: **Accepted architecture contract; no assistant endpoint, worker, artifact lifecycle, or UI is implemented by this record.**

## Decision

`documentation/config/local-ai-availability-fallback-contract-0.9.3.json` defines the future assistant state machine. It applies to `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. It is separate from the existing documentation-search panel state: AI state never changes deterministic search query/filter/result state, search URL/history, documentation navigation, or lexical ranking.

`/health/ready` continues to report only core BPM readiness. It must remain true when the assistant is unavailable. The planned assistant status endpoint has an independent `assistant_ready` field; it is true only when a verified compatible local assistant can accept an immediate generation. `lexical_search_ready` remains true for every assistant state in a valid documentation installation.

## Status And Localization API

M6 implements no assistant HTTP route. M7-01 freezes the planned status/chat API and later M7/M10 tasks implement its controller and UI surfaces. A status response carries stable `state`, `assistant_ready`, `lexical_search_ready`, `locale`, `message_key`, `action_key`, `reason_code`, and `state_epoch` fields. It may carry bounded progress, queue, retry, active-generation, web-state, and safe-capability fields, but never prompts, answers, paths, exception text, secrets, hashes, or provider bodies.

Every state expands to five locale-owned keys: title, detail, action, live-region text, and accessible name. English visible fallback is forbidden in the five non-English locales. If a key is absent, the assistant surface fails closed and leaves the existing localized lexical-search recovery surface available. Human locale review is required before release.

## State Matrix

| State | `assistant_ready` | Chat API result | Visible behavior and safe fallback |
| --- | ---: | --- | --- |
| `disabled` | no | 409 | No implicit start; direct readers to lexical search. |
| `not-installed` | no | 409 | Show verified-install disclosure and explicit action only; no auto-download. |
| `downloading` | no | 503 | Show consented bounded progress/cancel; artifacts are unusable until verified and promoted. |
| `indexing` | no | 503 | Build local knowledge without serving partial artifacts; use lexical search. |
| `loading` | no | 503 | Wait for isolated worker health/resource/artifact checks; do not show a ready composer. |
| `ready` | yes | 200 | Accept one guarded local request; show citations and optional-web disclosure. |
| `busy` | no | 202 or 429 | One bounded queued request at most; show queue/cancel and offer lexical search. |
| `cancelled` | no | 409 | Emit one terminal cancellation outcome, clean up, then transition safely. |
| `degraded` | no | 503 | Do not answer with weakened grounding/security/privacy; show safe reason and lexical fallback. |
| `incompatible` | no | 409 | Quarantine candidate; never mix or silently substitute artifacts. |
| `crashed` | no | 503 | Stop process tree, require explicit verified restart, preserve `/help/` and core BPM. |
| `web-offline` | yes, local only | 200 local-only | Label web unavailable, make no silent retry, and retain local citations/lexical search. |

`busy` can return `202` only while the single approved queue slot exists; otherwise it returns `429`. `web-offline` is capability-specific: it cannot disguise a local worker, artifact, scope, privacy, or resource failure, which must instead be `degraded`, `incompatible`, or `crashed`.

## Transitions And Truthfulness

```text
disabled -> not-installed -> downloading -> indexing -> loading -> ready -> busy
                                      |             |          |          |       |
                              incompatible/crashed  |   cancelled     web-offline
                                                    v          v          |
                                             loading/incompatible     ready
```

The complete transition map is in the JSON contract. Explicit consent is required for download and web use. A successful download first verifies artifacts; indexing requires one complete compatible chunk/vector/index/integrity generation; loading requires worker isolation, no listening port, health, resources, locale, artifacts, and security checks. Any failed gate cannot transition to `ready`.

An existing verified generation may continue serving during a new index build. In that case state stays `ready` with `background_operation=indexing`; `indexing` is used only when no active verified generation exists. This prevents both false unavailability and false readiness.

## Failure, Fallback, And Recovery

- A rejected or unavailable chat never blocks documentation navigation or deterministic search.
- Partial, stale, unverified, mixed-generation, or incompatible artifacts cannot set `assistant_ready=true`; they are quarantined under the security/rebuild contracts.
- Cancellation stops streaming and transitions through `cancelled`; crashes terminate the worker tree, clear temporary/conversation state, and do not enter a restart loop.
- `degraded` blocks answering when any grounding, security, privacy, or resource protection is not safe. It exposes stable reason/action keys, not sensitive diagnostics.
- The status endpoint, background work, page load, lexical search, and rejected chat never trigger an implicit download, model start, or network access.

## Ownership And Verification

M6 owns lifecycle, state transitions, worker availability, and resource evidence. M8 owns scope, privacy, CSRF, and no-network state behavior. M10 owns six-locale accessible UI, and M11 owns update/rollback/recovery. The focused M2-06 test validates this state contract only; browser, runtime, and lifecycle evidence remain release-blocking future work.
