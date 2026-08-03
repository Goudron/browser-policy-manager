# BPM 0.9.3 Six-Locale Search Relevance Benchmark

Date: 2026-07-28

Backlog item: `BPM093-M3-03`

Status: **Measured; no engine is selected.**

## Method And Evidence Boundary

The runner used the accepted corpus and 24 compact locale-separated documents: four domains for
each of `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. The documents contained only canonical terms
and reviewed aliases. Inflection, typo, compound, and accent variants appeared only in queries; this
prevents an index from passing because a test variant was copied into its source text.

Each candidate received the identical 244-query plan: 40 queries in each locale plus four
French accent queries. That gives 196 expected-topic queries, 42 expected-empty queries, and six
explicitly unscored ambiguity queries. The raw evidence has 732 records (three candidates times
244 queries) in ignored
`documentation/reports/benchmark/bpm093-m3-03.QJmGRq/bpm093-m3-03-search-relevance.raw.ndjson`.
The deterministic summary beside it carries host and artifact hashes.

The host was the required Intel Core i5-7200U CPU at 2.50 GHz, `x86_64`, 7,662,370,816 bytes RAM,
and Linux `7.0.0-28-generic`. Pagefind ran as the real `1.5.2` CLI and Search API against a
temporary same-origin loopback static site; every fetch was guarded to that origin. Meilisearch ran
as the real Community Edition `1.45.1` binary on private loopback with analytics disabled. The
current control is a deterministic mirror of the exact lexical scoring core in
`bpm-docs-search.js`; rendered-browser parity remains an explicit M3-04 obligation.

| Artifact | SHA-256 |
| --- | --- |
| Pagefind npm package `1.5.2` | `539357f51b47ea98cbef10bd774b432730d5a839ade5b5a30d13df033cbe9348` |
| Pagefind Linux x64 package `1.5.2` | `3c8dcfdaa69946113e0257be05bdef57297c7f1a562aa168536ff7c5d4590660` |
| Meilisearch CE Linux amd64 `1.45.1` | `35986cba02cc4c9a2f79b4f85be8c2bc0013989c208410e6cfea85b1fdc3d708` |

One earlier local raw run was retained but excluded from this result because its compact documents
incorrectly indexed typo/inflection/compound query stimuli. It is not selection evidence.

## Per-Locale Results

Values are fractions. `NR precision` is correct empty results divided by all empty results; `NR
recall` is correct empty results divided by expected-empty queries. The table is deliberately not
collapsed into a macro average.

| Candidate | Locale | Top-1 | MRR | Recall@5 | NR precision | NR recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Current control | en | 0.969 | 0.969 | 0.969 | 0.750 | 0.429 |
| Current control | ru | 0.969 | 0.969 | 0.969 | 0.875 | 1.000 |
| Current control | de | 0.719 | 0.734 | 0.750 | 0.429 | 0.857 |
| Current control | zh-CN | 0.719 | 0.734 | 0.750 | 0.467 | 1.000 |
| Current control | fr | 0.972 | 0.972 | 0.972 | 0.857 | 0.857 |
| Current control | es-ES | 0.969 | 0.969 | 0.969 | 1.000 | 0.857 |
| Pagefind `1.5.2` | en | 0.875 | 0.875 | 0.875 | 0.429 | 0.429 |
| Pagefind `1.5.2` | ru | 0.781 | 0.797 | 0.812 | 0.500 | 0.857 |
| Pagefind `1.5.2` | de | 0.812 | 0.812 | 0.812 | 0.500 | 0.857 |
| Pagefind `1.5.2` | zh-CN | 0.719 | 0.719 | 0.719 | 0.400 | 0.857 |
| Pagefind `1.5.2` | fr | 0.667 | 0.667 | 0.667 | 0.294 | 0.714 |
| Pagefind `1.5.2` | es-ES | 0.625 | 0.625 | 0.625 | 0.200 | 0.429 |
| Meilisearch CE `1.45.1` | en | 0.656 | 0.672 | 0.688 | 0.429 | 0.857 |
| Meilisearch CE `1.45.1` | ru | 0.531 | 0.547 | 0.562 | 0.333 | 0.857 |
| Meilisearch CE `1.45.1` | de | 0.625 | 0.641 | 0.656 | 0.400 | 0.857 |
| Meilisearch CE `1.45.1` | zh-CN | 0.656 | 0.672 | 0.688 | 0.429 | 0.857 |
| Meilisearch CE `1.45.1` | fr | 0.583 | 0.597 | 0.611 | 0.333 | 0.857 |
| Meilisearch CE `1.45.1` | es-ES | 0.531 | 0.547 | 0.562 | 0.333 | 0.857 |

## Query-Class Recall@5

Each cell is `correct / expected-topic queries`. This exposes the failures which a locale average
would otherwise mask. The evidence is not collapsed into a macro average.

| Query class | Current control | Pagefind `1.5.2` | Meilisearch CE `1.45.1` |
| --- | ---: | ---: | ---: |
| Accent | 4 / 4 | 4 / 4 | 4 / 4 |
| Alias | 24 / 24 | 15 / 24 | 24 / 24 |
| Canonical | 20 / 20 | 20 / 20 | 20 / 20 |
| Chinese segmentation | 4 / 8 | 8 / 8 | 8 / 8 |
| Compound | 16 / 16 | 12 / 16 | 4 / 16 |
| German compound | 1 / 4 | 3 / 4 | 3 / 4 |
| Morphology | 14 / 20 | 12 / 20 | 0 / 20 |
| Natural context | 24 / 24 | 6 / 24 | 12 / 24 |
| Natural language | 23 / 24 | 23 / 24 | 0 / 24 |
| Russian inflection | 3 / 4 | 3 / 4 | 0 / 4 |
| Technical identifier | 24 / 24 | 18 / 24 | 24 / 24 |
| Typo | 19 / 24 | 23 / 24 | 24 / 24 |

## Result

No external candidate is more relevant than the current control in all six locales. Pagefind improves
the German compact result (Top-1 0.812 / Recall@5 0.812 versus 0.719 / 0.750) but regresses in
English, Russian, Simplified Chinese, French, and Spanish; its Simplified Chinese Recall@5 is 0.719
versus the control's 0.750. Meilisearch CE regresses against the control in every locale. This is
evidence about the frozen compact mapping and the recorded candidate configuration, not a claim that
either upstream engine is generally unsuitable.

M3-04 must still measure resource, browser integration, CSP, offline behavior, service failure, and
operability. M3-05 may retain the current BPM-owned engine when no external candidate beats it under
the comparative rule; a later revision of that own engine must be remeasured against this frozen
control without weakening the locale, identifier, facet, or fallback contract.
