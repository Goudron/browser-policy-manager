# BPM 0.9.3 M4 Production Browser-Search Verification

Date: 2026-07-29

Backlog item: `BPM093-M4-06`

Status: **Accepted production verification for the BPM-owned lexical search path.**

## Scope And Decision

This record closes M4 for the selected deterministic, per-locale static search. It verifies the
production browser/build path after parity, adapter, domain/facet, tuning, and retirement work. It
does not select or enable a RAG model, a network search provider, Pagefind, or Meilisearch.

The installed search remains complete when no AI component is present: the browser loads one
same-origin static index, runs `BpmDocsSearchRanking` through the BPM-owned adapter, and renders
local results. The static corpus and UI contracts explicitly prohibit AI, RAG, embeddings,
generative answers, and runtime network search; an unavailable future assistant therefore cannot
affect this path.

## Verification Evidence

| Protected area | Evidence and result |
| --- | --- |
| Unit and search contracts | `make test-docs` passed. It covers documentation unit and contract suites, including index semantics, deterministic quality/performance budgets, locale aliases, facets, integrity, browser/build rank parity, browser adapter, and M4 tuning contract. |
| Full six-locale release contract | `make docs-release-check` passed: full DITA validation and the maintained release-contract suite. |
| Reproducible production artifact | `make docs-reproducibility-check` passed; `make docs-package && make docs-package-verify` passed. The generated package has validated manifest and archive checksums. |
| Browser and accessibility behavior | `make test-docs-ui` passed: six non-browser portal contracts and Chromium/Selenium smoke. The smoke covers every maintained locale, compact/responsive search layout, localized filters, keyboard Escape, URL/history hydration, focus, asset/index loading, and contextual portal flow. |
| CSP, offline, and request boundary | The source/contract and browser checks preserve a single same-origin index request, safe `/help/{locale}/` result URLs, DOM text rendering, CSP-compatible static assets, and a no-network empty-result recovery. No browser-to-daemon or external-search path exists. |
| Performance and operability | The generated-search performance contract passed: deterministic scan-unit, document-count, result-count, and index-byte limits are preserved. Existing target-host resource/rollback evidence remains in `search-resource-operability-integration-benchmark-0.9.3.md`; no rejected vendor runtime is packaged. |

## Comparative Relevance Result

The final run of
`documentation/tools/run_browser_search_tuning_benchmark_0_9_3.py` passed all 244 reviewed
six-locale cases. It executes the actual browser ranker through Node with no generated site or
network request. For every locale, no protected metric regressed and Top-1, MRR, and Recall@5
strictly improved over the frozen previous-version control.

| Locale | Frozen Top-1 / MRR / R@5 / no-result | Selected Top-1 / MRR / R@5 / no-result |
| --- | --- | --- |
| `en` | .96875 / .96875 / .96875 / .42857 | 1 / 1 / 1 / 1 |
| `ru` | .96875 / .96875 / .96875 / 1 | 1 / 1 / 1 / 1 |
| `de` | .71875 / .73438 / .75 / .85714 | .9375 / .9375 / .9375 / 1 |
| `zh-CN` | .71875 / .73438 / .75 / 1 | 1 / 1 / 1 / 1 |
| `fr` | .97222 / .97222 / .97222 / .85714 | 1 / 1 / 1 / 1 |
| `es-ES` | .96875 / .96875 / .96875 / .85714 | 1 / 1 / 1 / 1 |

The run used browser-script SHA-256
`ca9c8bebdae90a776f000c2b6ab660388841c56dcba3de844818e3aa121190f9` and corpus SHA-256
`0993aec89fe2991d6ef15de251bfedfa87ea99ae6498e5ef73a84f2d6b1aff52`.

## Outcome

`BPM093-M4-06` is complete. The BPM-owned lexical implementation is the sole production search
path, remains functional independently of AI/RAG work, satisfies protected portal behavior, and is
strictly more relevant than the frozen prior-version control in each supported locale. M5 may now
add retrieval artifacts only behind this preserved lexical fallback and its existing provenance,
integrity, CSP, offline, and accessibility boundaries.
