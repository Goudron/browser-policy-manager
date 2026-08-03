# BPM 0.9.3 Active-Version And AI-Boundary Audit

Date: 2026-07-28

Backlog item: `BPM093-M1-07`

Status: **Accepted audit; no AI/RAG behavior is enabled by this record.**

## Scope And Method

This audit separates current product sources from historical release evidence and from the current
deterministic-search safety boundary. It searched `app/` (excluding generated installed
`app/documentation/site/`), root metadata, `README.md`, `CHANGELOG.md`, `docs/`,
`documentation/`, and focused tests/runbooks for `0.9.2` and documentation-assistant terms.
Generated builds, installed sites, reports, caches, vendor/dependency directories, and archived
material were excluded.

No `0.9.2` reference exists in runtime source outside generated documentation, project metadata,
README, Makefile, or active-version tests. The only root-release occurrence is the historical
`CHANGELOG.md` heading. The bounded source scan found 56 `0.9.2` path hits and 37
AI/RAG-boundary path hits; the tables classify owners rather than treating repeated versioned files
or assertions as independent current-product claims.

## `0.9.2` Classification

| Source family | Current meaning | Disposition | Owner / follow-up |
| --- | --- | --- | --- |
| `app/` excluding generated installed documentation; `pyproject.toml`; `README.md`; `Makefile`; active-version and bootstrap tests | No `0.9.2` current-version claim exists. BPM `0.9.3` is supplied by product metadata and checked by active-version tests. | **Retain** the absence; no change. | M1 version surfaces are closed; later changes must retain this guard. |
| `CHANGELOG.md` | `0.9.2` is the preceding release heading and shipped history. | **Retain as history.** | M13-12 may add verified `0.9.3` outcomes but never overwrites older notes. |
| `docs/architecture/*-0.9.2.*`, including UI, editorial, search-state, Firefox-schema, dependency, release-contract, and drift records | Versioned point-in-time evidence for the 0.9.2 scope. An `active` index status means maintained reference, not current product target. | **Retain as versioned evidence.** | A separate retention task may alter index status only with a replacement-reference review. |
| `documentation/config/*-0.9.2.*`, `documentation/tools/validate_editorial_release_gate.py`, and `documentation/tests/contract/*0_9_2.py` | Exact 0.9.2 editorial, screenshot, and Linux-evidence contracts and guards. | **Retain as historical contract/test pairs.** | M12/M13 add 0.9.3 counterparts where implementation changes; old evidence remains traceable. |
| `tests/test_ui_compaction_baseline_guards_092.py`, `tests/test_documentation_audience_status_leakage_audit_092.py`, and their fixtures | Regression guards for a past UI/documentation release, not runtime release selection. | **Retain as historical regression coverage.** | Keep versioned fixture ownership; do not repurpose as assistant tests. |
| `docs/docs-index.md` | Lists maintained 0.9.2 records and now has a 0.9.3 heading/current records. | **Retain links; index new 0.9.3 records once.** | M12-07/M13-14 reconcile final index state. |
| `documentation/PROJECT_SNAPSHOT.generated.md` and installed/generated output | Derived local state; not editable current-version authority. | **Exclude and regenerate only.** | M12-07 updates a snapshot only for real implemented entry points. |

## AI/RAG Boundary Dispositions

`Retain` means a prohibition remains necessary outside the future assistant. `Replace` means the
wording must be superseded by the approved 0.9.3 safe-local-assistant contract in its named task.
`Narrow` preserves the underlying safety rule while removing only the blanket ban on an implemented
assistant. No `Replace` or `Narrow` disposition authorizes an early feature change.

| Active source family | Existing boundary | Disposition | Required 0.9.3 owner and invariant |
| --- | --- | --- | --- |
| `documentation/config/search-corpus-and-results-0.9.0.json`, `search-normalization-aliases-0.9.0.json`, `search-ranking-typo-0.9.0.json`, `search-facets-filters-0.9.0.json`, `search-quality-performance-0.9.0.json`, `search-integrity-drift-0.9.0.json`, and `search-ui-filter-contract-0.9.1.json` | `no-ai-no-rag-no-embeddings-no-generative-answers` is the current lexical-search contract. | **Replace** in M2/M4 with a versioned lexical-plus-assistant contract. | Lexical search remains deterministic, offline, complete without AI, and may not silently start a worker or network request. |
| `documentation/tools/build_docs.py` and its unit/contract search tests | Build/search output assumes the above non-AI field and emits current static-search copy. | **Replace** in M4-M5 only after selected formats and artifact ownership exist. | Never hand-edit generated output; selected search, chunk, and index artifacts derive reproducibly from reviewed source. |
| `documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/user/ug-concept-documentation-search-boundary.dita` | User-facing search says no conversational answers, embeddings, vector retrieval, or RAG. | **Replace** in M12-01 after shipped behavior and six-locale wording are approved. | Direct search and tree guidance remain usable in every assistant-disabled/degraded state. |
| `documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/user/ug-reference-schema-dependent-guided-controls.dita` and `ug-task-configure-firefox-ai-policies.dita` | Separates Firefox browser AI policy controls from documentation-portal AI. | **Narrow** in M12-01/M12-05. | Retain the Firefox-policy distinction and the ban on claims that browser policy settings enable BPM assistant behavior. |
| `documentation/AGENTS.md`, `documentation/README.md`, `documentation/runbooks/README.md`, `inventory-refresh.md`, and `links-manifest-and-publishing.md` | Blanket no-ship authoring/runbook boundary. | **Narrow** in M12-05. | Keep the ban on unreviewed AI-authored product prose, machine-translation fallback, generated-source editing, silent networking, and unrelated schema-bump AI work. |
| `docs/architecture/product-documentation-ownership-boundary-0.9.0.md`, `product-documentation-accessibility-security-contract-0.9.0.md`, and 0.9.0/0.9.1 release contracts | Historic release limits prohibit documentation AI for their releases. | **Retain as history.** | `product-documentation-release-contract-0.9.3.md` is the safe-local-assistant gate; past contracts are not rewritten. |
| `README.md` and `tests/test_current_version_surfaces.py` | Current shipped-product copy accurately says search is deterministic, local, offline-capable, and non-AI. | **Replace** in M12-06 only after final shipped behavior is proven. | README remains durable current-state copy; it may not advertise target-only AI/RAG work. |
| `documentation/PROJECT_SNAPSHOT.md` | It accurately lists AI/RAG search as not implemented today. | **Retain until implemented; then replace** in M12-07. | Snapshot describes only real entry points and never planned behavior. |
| `documentation/tests/contract/test_search_*.py`, `test_user_guide_search_boundary_topics.py`, `test_authoring_runbooks.py`, `tests/test_product_documentation_context_guide.py`, and `tests/test_product_documentation_ownership_boundary.py` | Tests make current no-AI release/authoring guarantees fail closed. | **Retain until replacement contracts are implemented, then replace/narrow with M2/M4/M5/M12 tests.** | New tests prove lexical independence, artifact provenance, no silent worker/network, citations, scope-before-inference, privacy, and six-locale equivalence. |
| Firefox AI-policy UI/source/catalog references | Firefox Enterprise policy settings, not documentation-assistant functionality. | **Retain outside the assistant.** | No search/RAG task changes Firefox policy semantics without a separate schema/product task. |
| `docs/architecture/product-documentation-release-contract-0.9.3.md` and `dependency-currency-0.9.3.md` | Future safe local-RAG gates and candidates, not blanket prohibitions. | **Retain as the replacement contract.** | M2-M13 must satisfy resource, provenance, scope, privacy, web, and evidence gates before release. |

## Required Transition Order

1. M2 records replacement architecture, corpus/artifact ownership, resource ceilings, and
   pre-implementation guards before a runtime/model/search dependency is added.
2. M3-M6 select and implement search, retrieval, artifacts, and local inference while the old
   deterministic search path remains continuously available.
3. M7-M10 prove answers, scope, privacy, optional web, and six-locale UI before user-facing copy
   changes.
4. M11-M12 replace only approved active contracts, tests, DITA, snapshots, and runbooks; old
   versioned release evidence remains historical.
5. M13 verifies no obsolete current-state or blanket prohibition contradicts shipped behavior, while
   no-silent-AI and non-assistant safety boundaries still hold.

## Result

There is no current-version `0.9.2` defect in runtime or metadata. Existing AI/RAG prohibitions
remain effective until their named, fail-closed 0.9.3 replacement task completes. This audit changes
no product behavior, documentation claim, model availability, network behavior, or history.
