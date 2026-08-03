# BPM 0.9.3 Documentation-Assistant Copy Catalogue

Date: 2026-07-30
Backlog item: `BPM093-M10-03`
Status: implemented as a six-locale catalogue and static release files; no assistant capability is
enabled.

## Catalogue boundary

`documentation/config/documentation-assistant-copy-0.9.3.json` is the source catalogue for
English, Russian, German, Simplified Chinese, French and Spanish. It supplies natural copy for:

- all availability states and their title, detail, safe action, live announcement and ARIA label;
- scope, out-of-scope refusal, clarification, evidence absence, incomplete answers and local or
  external citations;
- question, send, stop, clear, recovery, search, settings, install and remove actions;
- optional local-model disclosure, CPU and response-time expectations, verified installation and
  removal confirmation; and
- disabled external evidence, exact-question consent, recipient, privacy boundary and external
  provenance label.

Every published locale receives a generated `assistant-copy.json`. State `live` and `aria` strings
are expanded from per-locale templates and the local state title/detail; the generated payload is
therefore complete without copying English fallback text. Named placeholders are identical at every
catalogue path. At the completion of M10-03 the static portal entry did not load or render that
file. M10-03A later reuses it only after the reader explicitly opens local-model management; it does
not fetch it during page load or enable the dialogue controls.

Long translated labels can wrap at safe word boundaries. Assistant action controls have no minimum
inline width and stack on narrow portal layouts, preventing a long German, Russian, French, Chinese
or Spanish label from forcing horizontal overflow.

## Meaning and safety

The catalogue never promises a completed model download, worker, answer, citation or external
request before the owning subsystem has proven it. Refusal remains limited to BPM documentation and
settings. A missing or insufficient local source results in clarification, abstention or an honest
unavailable state; it is not a licence to invent an answer. External evidence is described as
optional, per-question, explicitly consented and separately labelled. The privacy text states that
conversation history, BPM profiles, local documentation, files, session IDs and credentials are not
sent to the provider.

The model-related messages describe an optional local CPU workload, no fixed response-time promise,
verified-artifact confirmation, and an explicit removal confirmation. M10-03 supplied this text
only; the release lifecycle UI is implemented separately by `BPM093-M10-03A` and remains distinct
from chat enablement.

## No enablement in M10-03

M10-03 creates no assistant HTTP route, status poll, browser-side fetch, worker start, model check,
retrieval, provider call or change to deterministic documentation search. `AI093-T05`, `AI093-T06`
and `AI093-T07` therefore remain gating conditions for enabling the disabled M10-02 controls.

The normative record is
`documentation/config/documentation-assistant-copy-0.9.3.json`.
