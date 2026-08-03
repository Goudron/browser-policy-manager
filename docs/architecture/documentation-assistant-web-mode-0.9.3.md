# BPM 0.9.3 Optional Web-Mode Presentation

Date: 2026-07-30
Backlog item: `BPM093-M10-06`
Status: the historical per-question consent renderer and M12B-06 persistent reader switch are
retained for post-0.9.3 investigation; neither is emitted by the 0.9.3 portal.

`bpm-docs-assistant-web-mode.js` remains in the repository as a reviewed historical component. It
is not copied or loaded by generated 0.9.3 documentation pages, and does not fetch, poll, inspect a
model, decide scope or send a provider request on its own.

M12B-06 owns the native `role=switch` control, its six-locale short label and its tab/locale-private
preference. The same-origin transport reconciles that preference with the server mode only after
the reader opens the assistant. The server, not the browser field, authorizes external retrieval.

The switch is visible only in `Ready`, is disabled when administrator configuration is unavailable,
and remains selected until the reader explicitly turns it off, changes locale or closes the tab.
External claims are rendered in a distinct labelled region and remain subordinate to local BPM
documentation. Toggling contacts only the same-origin mode API and never contacts Brave directly.

The normative record is
`documentation/config/documentation-assistant-web-mode-contract-0.9.3.json`.
