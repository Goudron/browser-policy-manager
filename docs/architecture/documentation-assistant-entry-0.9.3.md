# BPM 0.9.3 Documentation-Assistant Entry

Date: 2026-07-30
Backlog item: `BPM093-M10-01`
Status: implemented as a static, localized portal entry; no assistant HTTP route or conversation
surface is added.

## User-facing boundary

Every generated `/help` locale page now places a concise Documentation Assistant card beside the
existing deterministic documentation search. Search is serialized first, receives the larger wide
viewport column, and remains fully usable regardless of the assistant card. The card states its BPM
documentation scope and tells the reader that search and guide navigation remain independent.

The card has a localized heading, scope statement and polite unavailable status in English, Russian,
German, Simplified Chinese, French and Spanish. It contains no button, composer, install/retry link,
web-mode control or focusable placeholder. It therefore cannot become a dead control when a model is
disabled, absent, incompatible or otherwise unavailable. On narrow screens the search and card stack;
the card is excluded from print output.

## Why availability is static here

`AI093-T05` remains a release blocker for assistant HTTP routes. The M7 status API and diagnostics
contracts are intentionally not published by this task: the portal makes no status poll, model or
runtime verification, worker start, retrieval, external-web request, or any other network call.
The visible unavailable state is truthful for this release surface because a conversation cannot yet
be started from it; it does not infer model readiness from an artifact on disk.

M10-02 may establish the inert accessible markup for future conversation controls, but may enable
none of them until it composes the frozen request-security requirements. M10-03 then owns the wider
dialogue/model-management catalogue. Until then, the deterministic local search remains the direct
discovery and fallback path.

The normative record is
`documentation/config/documentation-assistant-entry-contract-0.9.3.json`.
