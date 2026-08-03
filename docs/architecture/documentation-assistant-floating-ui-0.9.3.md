# BPM 0.9.3 Floating Documentation Support-Chat UI

Date: 2026-07-30
Backlog item: `BPM093-M12B-01`
Status: architecture/state contract implemented by `BPM093-M12B-01`; its transport-free portal shell
and layout are implemented by `BPM093-M12B-02`.

## Decision

The documentation assistant will replace the former planned sidebar presentation with a portal-owned
support-chat overlay. It is collapsed by default and fixed at the lower-right edge of every `/help/`
locale page. In that state, the only visible content is its localized title; Russian uses
**«ИИ-помощник BPM»**. There are no icons, badges, status labels or explanatory paragraphs.

When a reader expands it on a desktop viewport, the panel occupies half of the viewport width and
90% of the visible viewport height. This M13-10 release decision supersedes the historical M12B
geometry recorded in the original contract; the narrow-viewport fallback remains unchanged. The
document remains in place: the panel overlays it and does not reserve a sidebar column. The
transcript is the only scrollable region, so the localized title, composer and bottom status row
stay visible during long conversations. The existing portal tokens, light/dark themes,
reduced-motion and forced-colors treatment remain authoritative.

## Visible state

The expanded visual order is title, transcript, composer and bottom status row. A ready assistant
shows the short locale-owned ready status and a Clear control. A non-ready assistant exposes the
model installation or recovery action instead. An explicit installation may show only factual
server-owned phases and byte/percentage progress; a failure may show only a reviewed safe reason.
The UI never offers removal of a maintainer-installed local model.

The widget itself intentionally has no explanatory scope, privacy, performance, resource or search
fallback paragraphs. Those explanations belong in the reviewed documentation. Ordinary deterministic
search remains independent and unchanged.

## Session and transport boundary

The reader's collapsed/expanded preference and a bounded text-only view of up to eight completed
turns live only in a versioned locale-private `sessionStorage` key. `BPM093-M12B-03` implements this
ephemeral per-tab presentation cache in `bpm-docs-assistant-conversation.js`: Clear, tab close,
locale change and server-declared conversation expiry remove it. Active requests, partial output,
credentials, paths, raw errors and cross-locale material are never retained. Neither `localStorage`,
IndexedDB, cookies, server persistence nor telemetry may be used for this purpose.

`BPM093-M12B-04` binds the shell only to the reviewed same-origin assistant API and server-owned
opaque identifiers. No status, model, RAG, search or web request occurs on page load, including a
reload that restores an expanded panel; a status request begins only after an explicit reader
opening action. Admission always sends `web_mode=local_only`. The browser verifies response, event,
source ID, source URL, locale and epoch shapes before rendering. It stores completed text only after
a validated terminal event, resolves sources only through the server-owned request handle, and
issues server Clear only after the reader explicitly clicks Clear. `BPM093-M12B-05` connects the
unavailable control to the existing guarded same-origin local-model lifecycle only after an explicit
reader action. The widget displays factual server-owned download bytes/percentage and preparation
phase, reattaches after a reader reopens it following reload/navigation, and attempts local runtime
activation only after the model has been verified. A preparation failure retains the verified model,
shows only a locale-owned safe failure state, and never offers deletion. M12B-06 binds M12A-04's
optional web-evidence server path to a Ready-state, tab/locale-private switch and renders validated
external claims in a separately labelled region. All visible dynamic text remains text-only DOM
content.

The normative record is
`documentation/config/documentation-assistant-floating-ui-contract-0.9.3.json`.
