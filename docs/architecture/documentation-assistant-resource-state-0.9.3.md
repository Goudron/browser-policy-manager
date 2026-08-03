# BPM 0.9.3 Assistant Resource-State Presentation

Date: 2026-07-30
Backlog item: `BPM093-M10-05`
Status: implemented as a transport-free resource-state renderer; chat remains disabled.

`bpm-docs-assistant-state-machine.js` registers a future-callable renderer and does nothing while a
documentation page loads. A later security-cleared same-origin transport may supply only an exact
API-v1 snapshot (`locale`, state and monotonically increasing epoch) together with the reviewed
locale-owned `assistant-copy.json` messages. The renderer rejects unknown fields and stale epochs;
it never displays server-provided prose, paths, exception text, queue identifiers, resource counters
or partial model output.

It presents loading, indexing, a bounded queue/duplicate submission, cancellation, timeout,
resource-limit degradation, unloading, unloaded and search-only states. Each accepted state gives a
keyboard-reachable link to the existing deterministic documentation search. Recovery wording can
say that retry is available after recovery, but it is not an action: this task adds no request,
retry, timer, polling, worker management or chat endpoint.

The established composer remains disabled, including its stop control. Consequently the UI cannot
pretend to cancel, retry or start local work before the future guarded chat transport exists.
Ordinary documentation search remains independent and usable throughout.

The normative record is
`documentation/config/documentation-assistant-resource-state-contract-0.9.3.json`.
