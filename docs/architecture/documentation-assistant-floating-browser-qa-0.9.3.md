# BPM 0.9.3 Floating Assistant Browser QA

Backlog item: `BPM093-M12B-07`.

This release check proves the user-visible floating assistant in a real Chromium portal, rather than
relying only on markup or JavaScript contracts. It uses six generated locale pages and replaces
browser `fetch`/`EventSource` only after a page has loaded. The substitution is restricted to
same-origin reviewed API shapes; it neither starts the local model nor contacts Brave, Mozilla or
the deterministic-search index.

Every locale is opened in an alternating desktop or narrow viewport, and in both light and dark
themes. The evidence checks title, Ready status, native external-sources switch, keyboard return to
the collapsed trigger, panel bounds, below-header placement and unchanged portal-control width.
The locale matrix starts with external sources off. Russian then proves that an explicit selection
survives documentation navigation and is reconciled using only the same-origin mode endpoint;
another locale still starts off.

English proves a Busy-to-validated-answer sequence and eight bounded, text-only long turns. A
reload restores the expanded panel and those turns without an assistant request; no image or script
node can be restored. Spanish exercises a safe chat admission failure. German exercises the guarded
model-install path through a terminal failure and shows only locale-owned failure copy, never the
server reason code. The preceding M12B-06 smoke remains the factual progress-path proof.

The browser console must contain no CSP violation and interaction calls may target only the
same-origin assistant/model API. Ordinary deterministic search remains untouched throughout.

The normative record is
`documentation/config/documentation-assistant-floating-browser-qa-contract-0.9.3.json`.
