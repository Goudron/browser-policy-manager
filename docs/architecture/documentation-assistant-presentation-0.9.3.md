# BPM 0.9.3 Grounded Answer Presentation

Date: 2026-07-30
Backlog item: `BPM093-M10-04`
Status: implemented as a validated final-answer renderer; chat remains disabled.

## Rendering boundary

`bpm-docs-assistant-renderer.js` registers a future-callable renderer but performs no action when a
documentation page loads. It does not fetch a model, inspect status, retrieve, start a worker, poll
or enable the disabled dialogue controls. A later, security-cleared same-origin chat transport may
call it only after the server has completed the M7 answer and source validation.

The renderer accepts exactly one API-v1 terminal payload. `answer` requires bounded plain text and
one or more sources, including a current local source. `clarify`, `abstain` and `refuse` deliberately
carry neither answer text nor citations. The UI shows a locale-owned mode explanation rather than a
made-up confidence percentage.

## Sources

Every accepted source is a small server-owned view: opaque source handle, localized title, guide,
section anchor, locale, BPM version, provenance, published URL and a display-safe excerpt. An
excerpt is presented in a native expandable element only when the server supplies it. Local links must be same-origin
`/help/{locale}/` paths and receive only a validated anchor. External links are HTTPS-only, visibly
labelled external and receive `noopener noreferrer`. An answer must contain at least one local source;
an external source cannot impersonate product documentation.

All content is created with DOM nodes and `textContent`; the renderer has no HTML parsing sink. It
rejects unknown fields, stale locale/version combinations, raw model/partial output, unbounded text,
unapproved URLs, internal retrieval data and numeric confidence claims. Deterministic documentation
search remains separate and usable.

The normative record is
`documentation/config/documentation-assistant-presentation-contract-0.9.3.json`.
