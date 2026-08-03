# BPM 0.9.3 Grounded Conversation Diagnostics And Degraded Operation

Backlog item: `BPM093-M7-06`
Status: implemented in memory only; no HTTP route or browser UI is added by this task.

`AssistantDiagnosticsService` composes safe, injected compatibility, worker-health, queue and web
capability probes into one admin-facing snapshot. It does not load a model, validate an artifact,
read a query, retrieve evidence, start a worker, or make a network call. M10 owns publication of
this snapshot through the frozen status API and UI.

## Safe Diagnostic Shape

The snapshot reports only configuration/model/index compatibility booleans, a coarse load state,
the coarse queue class (`idle`, `active`, or `queued`), web availability and one retained
five-valued local-error category: `none`, `setup`, `index`, `model`, or `runtime`. It also states
assistant and lexical-search readiness. The last category is memory-only and contains no exception
text or implementation detail.

Setup and index compatibility failures become `degraded`; an incompatible model becomes
`incompatible`; a failed worker becomes `crashed` with the `runtime` category. If probes fail or
return an unknown value, the service fails closed to `degraded/setup`. `lexical_search_ready` always
remains true. `web-offline` is a capability-specific ready state: local answering remains possible
while external web use is unavailable.

The diagnostic object has no fields for a user identity, query, turn, prompt, answer, evidence
excerpt, citation identity, path, artifact hash, secret, exception, stack trace, or provider body.
No telemetry or persistence is added.

The normative machine-readable contract is
`documentation/config/grounded-conversation-diagnostics-contract-0.9.3.json`.
