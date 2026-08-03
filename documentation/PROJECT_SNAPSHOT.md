# BPM Product Documentation Workspace Snapshot

Updated: 2026-07-16
Target BPM version: `0.9.1`
Current completed backlog item: `BPM091-M13-10`
Next backlog item: `BPM091-M13-11`

## Current State

The maintained subsystem has a browser-verified accessible return-safe hierarchical duplicate-free
static portal shell/theme, an Administrator/DevOps Guide map/key/root contract, an API/integration
re-home audit, five manifest-backed contextual help links, localized unavailable/stale/incomplete
documentation states, and focused `/help/` accessibility/responsive/CSP/theme integration
contracts. It also has isolated documentation test suite boundaries, focused documentation make
targets, a documentation-only source fast loop, isolated documentation coverage reporting, a
compact deterministic fixture catalog, ignored failure diagnostics, a generated subsystem
snapshot, a release-blocking documentation gate, a browser-backed documentation portal smoke, a
final content coverage audit, a refreshed implemented-product README, and a documentation-only
debugging protocol.

The localized User Guide screenshot workflow has a frozen capture-state contract, 36 normalized
PNG source assets, and `capture_user_guide_screenshots.py`. The `administrator-guide` includes
DevOps configuration/storage/logs/backups/CORS/security limits, update-from-source
evidence/migrations/docs rebuild/rollback-stop runbooks, a migrated API integration corpus, DevOps
integration runbooks for external control products, reusable DevOps environment
templates/curl/Python/multipart examples, and failed
startup/probe/schema/API/import/export/storage/WSL/dependency/documentation-portal diagnostics.
Its boundaries cover single-node source readiness, network exposure/proxy-readiness questions,
HA/deferred production boundary records, compact validation fixtures for stale
command/API/env/path/locale/deferred-claim drift, and final no-fallback/no-short-summary locale
parity review.

Milestones M10, M11, and M12 are complete and linked from the active release contract. M13-01
through M13-10 are accepted: static quality, full suites and coverage, clean documentation
validation/build, Chromium/Selenium smoke, milestone handoff, changelog finalization, and release
procedure verification all pass, and the reviewed epic commit is ready. The repeated documentation
gate reports 754 passed and 4 deselected after two stale Administrator deployment contract paths
were corrected and guarded. `DOC091-G14` and overall BPM 0.9.1 release readiness remain open only
until the M13-11 maintainer handoff completes.

`make dev` refreshes the current local documentation build through `make docs-install-dev` before
starting BPM. The maintainer manual review acceptance and final `runtime_ready=false` blockers stay
release evidence rather than generated source edits.

Not implemented yet:

- Windows 10/11 WSL validation on actual hosts; current outcomes remain explicitly unverified.
- Product screenshot coverage beyond the approved minimal User Guide matrix.
- Packaged installers, production hardening, HA, managed secrets, and AI/RAG documentation search.
- No `make docs-screenshots-check` target exists yet.

## Maintained Entry Points

| Area | Paths |
| --- | --- |
| Backlog | `docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md` |
| Ownership | `docs/architecture/product-documentation-ownership-boundary-0.9.0.md` |
| Toolchain | `docs/architecture/dita-publishing-toolchain-decision-0.9.0.md` |
| Identity | `docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md` |
| Manifest | `docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md` |
| Provenance | `docs/architecture/product-documentation-provenance-review-0.9.0.md` |
| Accessibility | `docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md` |
| Theme | `docs/architecture/product-documentation-visual-theme-contract-0.9.1.md`, `docs/architecture/bpm-documentation-theme-token-audit-0.9.1.md` |
| Sufficiency | `documentation/config/documentation-sufficiency-review-protocol-0.9.1.json` |
| Capability inventory | `docs/architecture/product-user-capability-inventory-0.9.0.md` |
| User Guide | `documentation/config/user-guide-map-0.9.0.json`, `documentation/config/user-guide-screenshot-matrix-0.9.1.json` |
| Search | `documentation/config/search-corpus-and-results-0.9.0.json`, `documentation/config/search-facets-filters-0.9.0.json`, `documentation/config/search-ui-filter-contract-0.9.1.json`, `documentation/config/search-quality-performance-0.9.0.json`, `documentation/config/search-integrity-drift-0.9.0.json` |
| Search candidate prototypes | `documentation/config/search-candidate-prototypes-0.9.3.json`, `documentation/tools/search_candidate_prototypes.py`, `documentation/tests/contract/test_search_candidate_prototypes_0_9_3.py` |
| Search relevance benchmark | `documentation/config/search-relevance-benchmark-0.9.3.json`, `documentation/tools/run_search_relevance_benchmark_0_9_3.py`, `documentation/tests/contract/test_search_relevance_benchmark_0_9_3.py` |
| Search resource benchmark | `documentation/tools/run_search_resource_benchmark_0_9_3.py`, `docs/architecture/search-resource-operability-integration-benchmark-0.9.3.md` |
| Search-engine ADR | `docs/architecture/search-engine-adr-0.9.3.md` |
| Browser/build ranking parity | `documentation/tests/contract/test_browser_search_ranking_parity_0_9_3.py`, `documentation/assets/theme/bpm-docs-search.js` |
| Browser search adapter | `documentation/config/search-browser-adapter-contract-0.9.3.json`, `documentation/tests/contract/test_browser_search_adapter_0_9_3.py`, `documentation/assets/theme/bpm-docs-search.js` |
| Domain ranking and facets | `documentation/config/search-domain-ranking-facets-contract-0.9.3.json`, `documentation/tests/contract/test_search_domain_ranking_facets_0_9_3.py`, `documentation/tools/build_docs.py` |
| Browser search tuning benchmark | `documentation/config/search-browser-tuning-benchmark-0.9.3.json`, `documentation/tools/run_browser_search_tuning_benchmark_0_9_3.py`, `documentation/tests/contract/test_browser_search_tuning_benchmark_0_9_3.py` |
| Active lexical implementation retirement | `documentation/assets/theme/bpm-docs-search.js`, `documentation/tools/build_docs.py`, `documentation/tests/contract/test_browser_search_ranking_parity_0_9_3.py`, `docs/architecture/current-documentation-search-inventory-0.9.3.md` |
| M4 production search verification | `docs/architecture/production-browser-search-verification-0.9.3.md`, `make test-docs`, `make docs-release-check`, `make docs-reproducibility-check`, `make docs-package`, `make docs-package-verify`, `make test-docs-ui` |
| Deterministic RAG chunks | `documentation/config/rag-chunk-extraction-0.9.3.json`, `documentation/tools/extract_rag_chunks_0_9_3.py`, `documentation/tests/contract/test_rag_chunk_extraction_0_9_3.py`, `docs/architecture/deterministic-dita-rag-chunk-extraction-0.9.3.md` |
| RAG corpus exclusions | `documentation/config/rag-corpus-exclusions-0.9.3.json`, `documentation/tests/contract/test_rag_corpus_exclusions_0_9_3.py`, `documentation/tools/extract_rag_chunks_0_9_3.py` |
| Embedding-model benchmark | `documentation/config/embedding-model-benchmark-0.9.3.json`, `documentation/config/embedding-model-benchmark-m5-03a-0.9.3.json`, `documentation/tools/run_embedding_model_benchmark_0_9_3.py`, `documentation/tests/contract/test_embedding_model_benchmark_0_9_3.py`, `docs/architecture/compact-multilingual-embedding-benchmark-0.9.3.md`, `docs/architecture/embedding-model-remediation-benchmark-0.9.3.md` |
| Chat RAG embedding selection | `documentation/config/chat-rag-embedding-selection-contract-0.9.3.json`, `documentation/config/chat-rag-embedding-benchmark-0.9.3.json`, `documentation/config/chat-rag-embedding-decision-0.9.3.json`, `documentation/config/chat-rag-clean-host-validation-0.9.3.json`, `documentation/config/chat-rag-resource-policy-amendment-0.9.3.json`, `documentation/tools/run_chat_rag_embedding_benchmark_0_9_3.py`, `documentation/tests/contract/test_chat_rag_embedding_selection_contract_0_9_3.py`, `documentation/tests/contract/test_chat_rag_embedding_benchmark_0_9_3.py`, `documentation/tests/contract/test_chat_rag_embedding_decision_0_9_3.py`, `documentation/tests/contract/test_chat_rag_clean_host_validation_0_9_3.py`, `documentation/tests/contract/test_chat_rag_resource_policy_amendment_0_9_3.py`, `docs/architecture/chat-rag-embedding-selection-contract-0.9.3.md`, `docs/architecture/chat-rag-embedding-benchmark-0.9.3.md` |
| Chat RAG vector storage | `documentation/config/chat-rag-vector-storage-decision-0.9.3.json`, `documentation/tools/run_chat_rag_vector_storage_benchmark_0_9_3.py`, `documentation/tests/contract/test_chat_rag_vector_storage_decision_0_9_3.py`, `docs/architecture/chat-rag-vector-storage-adr-0.9.3.md` |
| Chat RAG exact generations | `documentation/config/chat-rag-exact-generation-contract-0.9.3.json`, `documentation/tools/generate_chat_rag_exact_generations_0_9_3.py`, `documentation/tools/report_chat_rag_exact_generation_progress_0_9_3.py`, `documentation/tests/contract/test_chat_rag_exact_generation_0_9_3.py`, `docs/architecture/chat-rag-exact-generation-0.9.3.md` |
| Chat RAG same-locale retrieval | `app/documentation/retrieval.py`, `documentation/config/chat-rag-retrieval-contract-0.9.3.json`, `documentation/tests/contract/test_chat_rag_retrieval_0_9_3.py`, `tests/test_documentation_chat_retrieval_093.py`, `docs/architecture/chat-rag-same-locale-retrieval-0.9.3.md` |
| Chat RAG evidence packing | `app/documentation/evidence.py`, `documentation/config/chat-rag-evidence-packing-contract-0.9.3.json`, `documentation/tests/contract/test_chat_rag_evidence_packing_0_9_3.py`, `tests/test_documentation_evidence_packing_093.py`, `docs/architecture/chat-rag-evidence-packing-0.9.3.md` |
| Chat RAG retrieval validation | `documentation/config/chat-rag-retrieval-validation-0.9.3.json`, `documentation/tools/run_chat_rag_retrieval_validation_0_9_3.py`, `documentation/tests/contract/test_chat_rag_retrieval_validation_0_9_3.py`, `docs/architecture/chat-rag-retrieval-validation-0.9.3.md` |
| Floating assistant UI shell | `documentation/config/documentation-assistant-floating-ui-contract-0.9.3.json`, `documentation/assets/theme/bpm-docs-assistant-shell.js`, `documentation/assets/theme/bpm-docs-assistant-conversation.js`, `documentation/assets/theme/bpm-docs-assistant-transport.js`, `documentation/tests/contract/test_documentation_assistant_floating_ui_contract_0_9_3.py`, `documentation/tests/contract/test_documentation_assistant_floating_shell_contract_0_9_3.py`, `documentation/tests/contract/test_documentation_assistant_floating_conversation_contract_0_9_3.py`, `documentation/tests/contract/test_documentation_assistant_floating_transport_contract_0_9_3.py`, `docs/architecture/documentation-assistant-floating-ui-0.9.3.md` |
| Floating assistant reader documentation | `documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/user/ug-concept-browser-policy-manager-overview.dita`, `documentation/src/dita/{en,ru,de,zh-CN,fr,es-ES}/user/ug-concept-documentation-search-boundary.dita`, `documentation/tests/contract/test_documentation_assistant_release_documentation_0_9_3.py` |
| Local chat model/runtime shortlist | `documentation/config/local-chat-model-runtime-shortlist-0.9.3.json`, `documentation/tests/contract/test_local_chat_model_runtime_shortlist_0_9_3.py`, `docs/architecture/local-chat-model-runtime-shortlist-0.9.3.md` |
| Grounded answer benchmark harness | `documentation/config/grounded-answer-benchmark-harness-0.9.3.json`, `documentation/tools/run_grounded_answer_benchmark_0_9_3.py`, `documentation/tests/contract/test_grounded_answer_benchmark_harness_0_9_3.py`, `docs/architecture/grounded-answer-benchmark-harness-0.9.3.md` |
| Local chat target-laptop benchmark | `documentation/config/local-chat-target-laptop-benchmark-0.9.3.json`, `documentation/tools/run_local_chat_target_laptop_benchmark_0_9_3.py`, `documentation/tests/contract/test_local_chat_target_laptop_benchmark_0_9_3.py`, `docs/architecture/local-chat-target-laptop-benchmark-0.9.3.md` |
| Navigation/help | `documentation/config/navigation-tree-contract-0.9.1.json`, `documentation/config/all-settings-row-help-link-contract-0.9.1.json`, `documentation/config/documentation-polish-guardrails-0.9.1.json` |
| Coverage/diagnostics | `documentation/config/coverage-policy-0.9.0.json`, `documentation/config/diagnostics-policy-0.9.0.json` |
| Fixtures | `documentation/fixtures/fixture-catalog-0.9.0.json`, `documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json` |
| Linux selection | `docs/architecture/linux-distribution-selection-0.9.1.md` |
| Generated snapshot | `documentation/PROJECT_SNAPSHOT.generated.md` |
| Suite boundaries | `documentation/tests/suite-boundaries-0.9.0.json` |
| Release/browser gates | `documentation/tests/contract/test_documentation_release_gate.py`, `documentation/tests/browser/test_documentation_portal_browser_smoke.py` |
| Debugging | `documentation/runbooks/debugging-protocol.md` |
| Administrator scope | `documentation/tests/contract/test_administrator_guide_scope.py` |
| Administrator operations | `documentation/tests/contract/test_administrator_devops_operational_boundaries.py`, `documentation/tests/contract/test_administrator_linux_deployment_topics.py`, `documentation/tests/contract/test_administrator_windows_wsl_deployment_topics.py`, `documentation/tests/contract/test_administrator_update_from_source_topics.py`, `documentation/tests/contract/test_administrator_troubleshooting_diagnostics_topics.py`, `documentation/tests/contract/test_administrator_production_readiness_boundaries.py`, `documentation/tests/contract/test_administrator_guide_validation_fixtures.py` |
| API contracts | `documentation/tests/contract/test_api_integration_topics.py`, `documentation/tests/contract/test_api_locale_parity.py`, `documentation/tests/contract/test_api_openapi_drift.py`, `documentation/tests/contract/test_api_rehome_audit.py`, `documentation/tests/contract/test_api_devops_integration_runbooks.py` |
| API re-home | `docs/architecture/api-integration-rehome-audit-0.9.0.json`, `docs/architecture/api-integration-rehome-audit-0.9.0.md`, `documentation/runbooks/README.md` |
| Firefox/CIS/API inventories | `docs/architecture/firefox-policy-documentation-inventory-0.9.0.json`, `docs/architecture/cis-documentation-inventory-0.9.0.json`, `docs/architecture/api-documentation-inventory-0.9.0.md` |

## Commands Available Now

```bash
make setup-docs-toolchain
make test-docs
make test-docs-contract
make test-docs-ui
make test-docs-ui-contract
make test-docs-browser
make docs-snapshot
make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"
make docs-coverage
make docs-release-check
make docs-validate
make docs-build
make docs-install-dev
make docs-reproducibility-check
make docs-package
make docs-package-verify
./.venv/bin/python documentation/tools/validate_metadata.py
./.venv/bin/pytest -q tests/test_product_documentation_scaffold.py
./.venv/bin/pytest -q -m docs_contract
./.venv/bin/ruff check <changed_python_files>
git diff --check -- <changed_files>
```

Build/package commands are offline after toolchain setup. Browser commands use one bounded
Chromium/Selenium process. Generated build, installed-site, package, report, cache, and container
evidence remain outside hand-edited DITA source.
