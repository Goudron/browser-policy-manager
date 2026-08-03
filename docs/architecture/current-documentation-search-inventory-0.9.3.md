# BPM 0.9.3 Current Documentation Search Inventory

Date: 2026-07-28

Backlog item: `BPM093-M2-01`

Status: **Accepted baseline inventory; no search replacement selected.**

## Boundary And Current Artifact Flow

The current search is a self-hosted, deterministic, per-locale static implementation. Its source is
reviewed DITA, maintained metadata/alias/facet contracts, and generated policy/CIS inventories. It
does not query BPM data, a search service, or the network beyond same-origin retrieval of its local
index. Full generated indexes were not read for this inventory. One structural manifest sample
shows six `search/{locale}/index.json` records, each with a SHA-256 and 159 documents; generated
installed-site values are evidence only and are not source-of-truth inputs.

```text
reviewed DITA + target/inventory metadata + search JSON contracts
  -> documentation/tools/build_docs.py (DITA transform, shell, document extraction, index build)
  -> per-locale search/{locale}/index.json + manifest.json search SHA-256 records
  -> self-hosted bpm-docs-search.js fetches same-origin index and renders local results
  -> manifest/package validation + archive SHA-256
  -> ignored app/documentation/site development install for /help/
```

The six supported locales are `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. `manifest.json`,
`navigation.json`, `ui-target-map.json`, search indexes, package archives, and installed site are
generated artifacts: they are never hand-edited or committed as a replacement for source.

At the accepted M2 baseline, **build-time ranking** was the detailed authoritative implementation
and the browser scorer is simpler. The historical baseline states: source fingerprint does not include the search JSON contracts. M4-01 deliberately replaces that gap by fingerprinting every
active lexical-search configuration and by aligning the browser with the build ranker. This
historical observation is retained to make the M4 migration boundary auditable, not to describe
the completed implementation.

## Current Contract Inventory

| Current contract and owner | Behavior now | BPM093 disposition | Focused verification owner |
| --- | --- | --- | --- |
| `documentation/config/search-corpus-and-results-0.9.0.json` | Defines DITA/inventory authority; document/result schemas; locale, guide, identifier, provenance, version, facet, plain-text snippet, and result-URL fields. Excludes unpublished, restricted, cross-locale, and runtime-private data. | **Preserve and extend.** M2-M5 retain source/provenance/locale/facet requirements while replacing only the blanket non-AI field with a safe lexical-plus-assistant contract. | M2 architecture/corpus contracts; `documentation/tests/contract/test_search_corpus_contract.py`. |
| `search-normalization-aliases-0.9.0.json`, `search-ranking-typo-0.9.0.json`, and `search-browser-tuning-benchmark-0.9.3.json` | Unicode NFKC/casefold/diacritic normalization, CJK one/two-character expansion, reviewed aliases, exact identifiers, bounded Levenshtein, deterministic tie breaks. Build-time weights are identifier 1000, title 180, alias 140, heading 80, body 20, typo 12. | **Preserve as the shared browser/build contract.** M4-01 serializes reviewed locale alias terms into the per-locale index and applies the same normalization, technical-identifier rejection, bounded typo, weights, and tie breaks in the browser. M4-04 compares the actual browser ranker with frozen M3 scoring over all six locales and requires no regression plus a strict per-locale gain. | `test_search_ranking_typo.py`, `test_search_normalization_aliases.py`, `test_browser_search_ranking_parity_0_9_3.py`, and `test_browser_search_tuning_benchmark_0_9_3.py`. |
| `documentation/assets/theme/bpm-docs-search.js` and `search-browser-adapter-contract-0.9.3.json` | Browser loads one same-origin JSON index through an immutable BPM-owned adapter, applies the versioned deterministic ranker, filters, renders safe text nodes, preserves URL/filter/recent-query state, and stores only a locale-scoped recent query in browser localStorage. | **Aligned in M4-01 and adapted in M4-02.** The adapter exposes BPM-owned hydrate, serialize, query, and safe-result-URL operations; it rejects unknown URL filters and unsafe result paths, restores popstate without creating history, and keeps DOM labels/rendering separate from search behavior. | `test_browser_search_ranking_parity_0_9_3.py`, `test_browser_search_adapter_0_9_3.py`, `test_search_ui_filter_contract.py`, and `make test-docs-browser`. |
| `search-facets-filters-0.9.0.json`, `search-domain-ranking-facets-contract-0.9.3.json`, and `search-ui-filter-contract-0.9.1.json` | AND across fields/OR within field, guide/topic/channel/policy/CIS/API facets, `q` plus repeat-parameter URL state, compact one-line UI, explicit filter expansion, localized labels and empty recovery. | **Preserved and projected in M4-03.** The generated index records the domain/facet contract, browser adapter returns bounded per-result score breakdown and generated per-locale facet counts, and no undeclared filter value can affect a query. Assistant entry must sit beside search; it may not change filter visibility, result URLs, keyboard behavior, or search-only use. | `test_search_facets_filters.py`, `test_search_domain_ranking_facets_0_9_3.py`, `test_browser_search_adapter_0_9_3.py`, and docs UI contracts. |
| `search-quality-performance-0.9.0.json` | Six-locale exact/natural/typo/synonym/channel/CIS/API/CJK/no-result/adversarial fixtures; static size/document/scan-unit budgets, max 50 visible results. Current budget is a deterministic CI proxy, not a wall-clock laptop measurement. | **Preserve fixtures and replace the performance measurement method.** M2-02 freezes wall-clock/resource methodology; M2-03 expands the corpus; M3 compares all candidates against the unchanged control set. | M2-02/M2-03/M3; `test_search_quality_performance.py`. |
| `search-integrity-drift-0.9.0.json`, manifest schema, and `build_docs._validate_search_index_semantics` | Recomputes topic/anchor/inventory/snippet/locale/URL/output integrity; validates contract IDs, artifact SHA-256, byte/document counts, and search payload semantics during manifest and package checks. | **Preserve and extend.** Selected search/RAG artifacts require source hashes, model/index compatibility, and atomic promotion without weakening existing lexical checks. | M4/M5/M11; `test_search_integrity_drift.py`, manifest-generation tests, `make docs-reproducibility-check`. |
| Portal shell, `bpm-docs-search.js`, and static CSP/asset policy | Shell emits a relative `data-search-index-href`; client fetch uses `credentials: same-origin`, renders with DOM text nodes, and rejects result URLs outside `/help/{locale}/`. A failed index leaves a localized unavailable state. | **Preserve CSP, same-origin, inert rendering, locale URL, and degraded fallback.** M4/M8/M10 may add local assistant UI only behind explicit state and no unexpected network. | M4/M8/M10; docs UI contracts and `make test-docs-browser`. |
| `build_tree`, `validate_manifest_files`, `package`, `verify_package`, `install_dev_site` | Clean DITA build produces indexes, validates manifest SHA/semantics, packages artifact integrity and archive SHA-256, and promotes ignored development output atomically. | **Preserve package/rollback discipline; adapt artifact ownership.** M4-01 includes every active lexical-search contract in the development-site source fingerprint and validates the emitted browser alias groups, so changed search rules cannot leave a stale installed index. | M4 packaging/integration; `test_build_docs.py`, `make docs-reproducibility-check`, `make docs-package`, and `make docs-package-verify`. |
| `documentation/runbooks/links-manifest-and-publishing.md` and search-focused unit/contract tests | Defines source/artifact ownership, targeted reruns, locale search validation, no generated-output patching, and package/install flow. | **Adapt only after implementation.** M11-M12 must replace no-AI wording with the safe-local assistant boundary while retaining source ownership and release checks. | M11/M12; `test_authoring_runbooks.py`, `test_build_docs.py`, and `make test-docs-contract`. |

## Preservation, Replacement, And Retirement Map

| Category | BPM093 decision |
| --- | --- |
| **Preserve** | Six locales; DITA/manifest/target provenance; exact identifiers; reviewed aliases; CJK treatment; facets/URL state; compact accessible UI; same-origin/CSP/inert rendering; SHA-256 and package validation; deterministic lexical search when AI is absent. |
| **Replace** | The prior divergent browser scoring path is replaced by the shared BPM-owned ranker; blanket non-AI search mode; static-only quality budget; generated user copy that says answers/semantic retrieval never exist. |
| **Adapt** | Tokenizer and ranking integration, search build inputs and dev-site fingerprint, manifest/index schema, artifact ownership, integrity/reproducibility checks, locale fixtures, portal shell states, runbooks, and tests. |
| **Retire** | M4-05 retires the unreachable flattened-text `searchableText()` browser helper and the redundant derived `normalized.tokens` index field. The latter was not read by the shared ranker and could inflate a locale index; semantic validation now rejects it. M3's frozen control, candidate adapters, and comparative reports remain benchmark/rollback evidence only; they are never imported into the generated site or package. |

## Constraints For The Next Tasks

- M3 evaluated the previous browser-visible behavior as the frozen control. M4-01 closes the
  browser/build scorer divergence, M4-04 records a strict relevance gain per locale, and M4-06
  records final package, CSP/offline, accessibility, real-browser, performance-contract, and
  production-quality evidence in `production-browser-search-verification-0.9.3.md`.
- M4 must preserve the lexical path as an independent, same-origin, offline-capable fallback and
  must include every search configuration input in dev-install freshness detection.
- M5-M6 may add chunks, embeddings, models, or indexes only as generated, checksummed artifacts
  outside hand-authored DITA/source ownership.
- M8-M10 must retain local-only search when scope blocks a query, a model is unavailable, or web
  evidence is disabled or fails.

## Result

Current static search remains a mature deterministic baseline with strong provenance, localization,
integrity, package, and UI-state guarantees. M4-01 retains it as the selected engine and removes
the browser/build scoring divergence without adding a dependency; M4-02 gives the browser a stable
BPM-owned adapter boundary without a vendor UI. M4-05 removes the unreachable legacy browser helper,
so the generated index and shared field-aware ranker are the only active BPM-owned lexical path.
The shared ranker has passed final M4 production verification: its six-locale frozen-control
comparison is strictly better in every locale, while package, reproducibility, CSP/offline,
accessibility, and real-browser checks preserve the AI-independent lexical fallback.
