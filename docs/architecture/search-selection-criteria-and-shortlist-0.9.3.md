# BPM 0.9.3 Search Selection Criteria And Shortlist

Date: 2026-07-28

Backlog item: `BPM093-M3-01`

Status: **Accepted shortlist and scoring contract; no engine is selected or installed.**

## Decision Boundary

This record makes engine comparison reproducible. It preserves the current browser-visible static
search as the control and admits two open-source alternatives to isolated prototypes: Pagefind
`1.5.2` and Meilisearch Community Edition `1.45.1`. The shortlist is not a product dependency
decision. M3-02 implements no production replacement; M3-03 and M3-04 provide the evidence; only
M3-05 may select an engine.

Every candidate uses the accepted six-locale corpus (`en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`) and
the i5-7200U/7.1 GiB CPU-only protocol. The current control must be measured in the rendered
browser: its build-time scorer has bounded-typo and alias-group semantics that the current browser
scorer does not yet implement.

## Public Entry Gates

Entry gates are published prerequisites; there are no hidden selection vetoes. A candidate that fails one is
recorded with its failure and receives no weighted score.

| Gate | Prerequisite |
| --- | --- |
| `SG093-E1` | Exact edition/version has an OSI-approved license and immutable distribution/checksum evidence. |
| `SG093-E2` | BPM can self-host it without an account, mandatory cloud control plane, hosted service, or telemetry. |
| `SG093-E3` | Primary documentation shows a credible route for all six BPM locales; the benchmark still measures each locale. |
| `SG093-E4` | BPM can retain offline, same-origin CSP, safe rendering, keyboard/localized UI, and degraded lexical behavior. |
| `SG093-E5` | BPM can retain guide/topic/channel/policy/CIS/API facets, URL state, result URLs, exact IDs, aliases, and deterministic fallback. |
| `SG093-E6` | Update, rollback, process/listener ownership, and maintenance are bounded and operable by BPM. |

## Frozen Weighted Matrix

Scores range from 0 (no demonstrated fit) to 5 (demonstrated fit). The final total is
`sum(weight × score / 5)`, from 0 to 100. A missing result is **unscored**, not a zero and not an
assumed pass.

| Dimension | Weight | Required evidence |
| --- | ---: | --- |
| Relevance | 35% | M3-03 raw six-locale results: Top-1, Recall@5, exact IDs, aliases, typos, morphology, CJK, and no-result cases. |
| Locale parity | 20% | Separate result for every locale; a macro average cannot conceal a failed locale. |
| Resource/performance | 15% | M3-04 raw old-laptop artifact, startup, browser-render P95, memory, and recovery samples. |
| Offline/CSP/accessibility | 10% | Prototype proof for no-network operation, same-origin CSP, inert rendering, keyboard flow, localized states, and degradation. |
| Facet/integration compatibility | 10% | Prototype and corpus proof for existing facets, URL/filter state, result URLs, exact-ID/alias behavior, and browser-visible parity. |
| License/security/operations/maintenance | 10% | Exact edition/license, checksum, advisory check, update/rollback, isolation, and upstream-maintenance record. |

No external engine can win merely on weighted total. The primary selection rule is comparative: in
each of the six locales it must be no worse than the frozen previous-version static control for
Top-1, MRR, Recall@5, no-result handling, and exact identifiers, and it must demonstrate a strict
relevance improvement in that locale. There is no invented universal Top-1 or Recall@5 threshold
for lexical-engine selection. If no external candidate satisfies this per-locale rule, BPM retains
and improves the static control.

## Admitted Candidates

| Candidate | Why admitted | Mandatory prototype proof | Known constraint |
| --- | --- | --- | --- |
| Current BPM static search | Repository-owned self-hosted six-locale control with existing facet, URL, integrity, CSP, and fallback contracts. | Rendered-browser quality and old-laptop measurements, not build-report substitution. | Browser scoring is simpler than build scoring, especially for typos and alias groups. |
| Pagefind `1.5.2` | Pagefind documents static deployment, multilingual indexes, language-specific stemming/Chinese segmentation, and filtering; it is MIT licensed. [Multilingual](https://pagefind.app/docs/multilingual/), [filtering](https://pagefind.app/docs/filtering/), [license](https://github.com/CloudCannon/pagefind/blob/main/LICENSE), [release](https://github.com/CloudCannon/pagefind/releases/tag/v1.5.2) | BPM-owned localized accessible adapter, all BPM facets/URL/ranking invariants, browser-visible results, and same-origin-only network behavior. | Upstream capability is not BPM parity evidence. |
| Meilisearch Community Edition `1.45.1` | Meilisearch documents locale-oriented indexing, Russian/Cyrillic, German and Chinese handling, and typo controls. Only its MIT Community Edition is in scope. [Languages](https://www.meilisearch.com/docs/resources/help/language), [multilingual indexing](https://www.meilisearch.com/docs/capabilities/indexing/how_to/handle_multilingual_data), [typo tolerance](https://www.meilisearch.com/docs/resources/internals/typo_tolerance), [license](https://github.com/meilisearch/meilisearch/blob/main/LICENSE), [release](https://github.com/meilisearch/meilisearch/releases/tag/v1.45.1) | Private BPM-owned adapter; browser never reaches daemon; no LAN/public listener; clean stop, offline failure, static fallback, and all portal invariants. | A local service has startup, memory, package, listener, and recovery risk. Enterprise Edition is excluded. |

No other candidate is admitted. A future addition must supply primary evidence for every public gate
and follow the identical prototype, corpus, and old-laptop benchmark path. Popularity, a result from
another product, or build-time-only output does not meet that rule.

## Evidence Sequence

1. `BPM093-M3-02` creates isolated, disposable prototypes without changing the shipped search.
2. `BPM093-M3-03` measures relevance and locale parity on the accepted corpus.
3. `BPM093-M3-04` measures resource, browser latency, offline, CSP, accessibility, and operability.
4. `BPM093-M3-05` records the ADR: an external replacement only if comparative evidence supports
   it, otherwise the BPM-owned static control is selected for improvement.

No search source, generated index, package, runtime service, browser UI, dependency, or model is
changed by this task.
