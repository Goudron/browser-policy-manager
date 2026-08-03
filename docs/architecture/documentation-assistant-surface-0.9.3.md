# BPM 0.9.3 Accessible Documentation-Assistant Surface

Date: 2026-07-30
Backlog item: `BPM093-M10-02`
Status: implemented as an inert, accessible dialogue structure; no assistant HTTP route is added.

## Surface and current state

The M10-01 assistant entry now contains the semantic shape of a conversation: a named transcript
log, a named answer-state region, a named source list, a bounded question field, and Send, Stop and
Clear controls. The source list and answer-state region are hidden until a later validated response
may populate them. The transcript declares only `user`, `assistant` and `system` message roles.
Its independent scroll area is capped at `min(40dvh, 20rem)` so a long conversation cannot expand
the portal indefinitely.

The release surface remains honestly unavailable. The textarea and all three buttons are disabled,
there is no client-side fake action, and no new tab stop is introduced. The visible localised
explanation directs a reader to the existing deterministic search and guide navigation. This is an
intentional availability state, not a claim about whether an artifact happens to be present on disk.

## Accessibility contract

Every control and future result region has a localised programmatic name. Stable availability and
future progress use a polite, atomic status region. The transcript is a polite non-atomic log so a
later safe message addition can be announced without moving keyboard focus. Later activation uses
the native Send, Stop and Clear buttons and must leave focus in the question field or on the control
explicitly operated by the user; it must never steal focus merely to announce a status change. Narrow layouts stack the action controls, while
reduced-motion and forced-colors rules are covered by the shared documentation theme.

This task adds no user or assistant content and no browser rendering sink. If a later task renders a
validated answer, it must use text-only DOM APIs and the malicious-render fixtures required by
`AI093-T06`.

## Security boundary

The frozen API and stream contracts describe the future protocol, but `AI093-T05`, `AI093-T06` and
`AI093-T07` remain release blockers. Therefore this task does not publish a status endpoint, submit
a chat request, open an SSE stream, poll, start a worker, load a model, retrieve evidence, invoke
web mode, or make a network call. The deterministic documentation search remains independent.

Before a later task enables the disabled controls, it must compose and test actual request-body
bounds, session-bound CSRF rotation/replay protection, strict schema and same-origin rejection,
text-only rendering with a strict help CSP and malicious-render fixtures, and per-session request
rate limiting.

The normative record is
`documentation/config/documentation-assistant-surface-contract-0.9.3.json`.
