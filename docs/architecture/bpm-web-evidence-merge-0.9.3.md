# BPM 0.9.3 Conservative Local and Web Evidence Merge

Date: 2026-07-30
Backlog item: `BPM093-M9-04`
Status: implemented as a request-local merger and model-output schema. It adds no route, UI,
provider call or worker invocation; M10 will compose these verified boundaries into a transport.

## Local authority

`ConservativeEvidenceMerger` accepts web data only when the current locale already has an
answer-ready, current local BPM `EvidencePack`. Web-only data abstains: a Mozilla source cannot
create, expand or override a BPM support claim. The merged packet writes local records first and
marks every later web record `external_untrusted_lower_priority` with the explicit trust statement
that external data cannot create BPM support. Ordinary documentation search remains uninvolved.

At most two already-sanitized M9-03 sources and 8 KiB of external context fit beside the 24 KiB local
packet; the total packet is capped at 32 KiB. The M9-03 result lease is consumed by this merger only
for the current request. The merger then owns a second context-manager lease and clears its
provider-derived packet references on terminal completion, cancellation or error.

## Freshness and conflict rule

An external source needs a reported ISO date and must not be more than 365 days old. Missing, invalid,
future or old age is a `local_only` result with no external claim. The adapter abstains entirely for
an unresolved conflict: any external Browser Policy Manager/BPM support claim, or a different Firefox
or ESR major version from accepted local evidence. This deliberately favors omission over a plausible
but unsupported product answer; additional conflict classes require a separately reviewed rule.

External citation metadata remains separate: provider ID, canonical source URL, sanitized title,
source age and retrieval time. External snippets never become local citations, local source ordering
does not rank external material, and the provider body is not persisted.

## Answer contract

The fixed model response shape is:

```json
{"disposition":"answer","local_text":"...","local_citation_ids":["topic:..."],"external_claims":[{"text":"...","citation_ids":["web:..."]}]}
```

`local_text` is BPM product guidance and must cite accepted local evidence. Each optional external
claim is a separately rendered plain-text unit with one or more accepted external citations. An
unknown, duplicate, empty, markup-bearing or uncited external claim abstains the whole response;
external citation IDs cannot be used as local citations. Non-answer states carry no text or sources.
M10 renders the local and external regions with distinct labels and citation lists rather than
combining their provenance in one paragraph.

The normative record is
`documentation/config/bpm-web-evidence-merge-contract-0.9.3.json`.
