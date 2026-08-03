# BPM 0.9.3 Search Candidate Adapter Prototypes

Date: 2026-07-28

Backlog item: `BPM093-M3-02`

Status: **Accepted deterministic adapter prototypes; no vendor engine is installed, started, or benchmarked.**

## Purpose And Boundary

The prototypes make the next benchmark compare equivalent BPM inputs and outputs rather than each
vendor's default UI or implicit schema. They expand the four accepted evaluation-corpus domains once
for each of the six locales, producing 24 compact plain-text documents with stable `/help/{locale}/`
URLs, identifiers, aliases, source weights, and guide/topic/channel/policy/CIS/API facets. The
documents index only a canonical term and reviewed alias. Inflections, deliberate typos, compound
variants, and accentless forms remain query-only stimuli, so a relevance result does not receive an
accidental exact match from its own test input.

They do **not** modify the portal, build a production index, download a dependency, spawn a process,
open a listener, or issue a network request. Their normalized result is a deterministic mapping
smoke result; it must not be reported as Pagefind or Meilisearch relevance, latency, memory, or
operability evidence.

## Candidate-Specific Adapter Inputs

| Candidate | Isolated input | Query boundary |
| --- | --- | --- |
| Current static control | Canonical BPM document records and in-process deterministic envelope. | Same normalized result schema used by the other adapters. |
| Pagefind `1.5.2` | Minimal static HTML records with `data-pagefind-body` and one `data-pagefind-filter` value per BPM facet. | BPM-owned static adapter envelope; Pagefind executable is not invoked. |
| Meilisearch Community Edition `1.45.1` | Document batch plus `filterableAttributes` and ordered searchable attributes. | A not-started private `/private/search` envelope; browser-to-daemon transport is forbidden. |

The Pagefind and Meilisearch shapes preserve an explicit integration seam, but do not imply that the
vendors accept BPM's ranking values or have passed any locale requirement. M3-03 connects these
shapes to exact candidate versions and records raw results; M3-04 tests lifecycle, network, CSP,
accessibility, failure isolation, and laptop resources.

## Preserved BPM Contract Fields

Every canonical document carries the existing result-contract fields: locale, guide/topic identity,
source topic/anchor/key/output path, title, plain-text snippet inputs, technical identifiers,
reviewed aliases, facets, product/documentation/source versions, and the current source weights.
The normalized result has stable result/document IDs, URL, score breakdown, matched fields,
identifiers, and facets. Filters remain AND across fields and OR within one field.

The shared reference adapter is deliberately conservative: it has no vendor tokenizer, stemming,
typo implementation, service response, or browser timing. Its job is only to fail early if a
candidate mapping loses a BPM identifier, alias, facet, locale boundary, URL, snippet, or result
field before a costly benchmark exists.

## Verification And Handoff

`documentation/tests/contract/test_search_candidate_prototypes_0_9_3.py` verifies the exact
shortlist, no-execution boundary, six locale-separated compact documents, Pagefind static-input
shape, Meilisearch private-boundary shape, stable identifier/alias/facet result mapping, and source
weights. It does not use a browser, a Pagefind binary, or a Meilisearch process.

No source, generated index, package, runtime route, UI, vendor dependency, or model has changed.
