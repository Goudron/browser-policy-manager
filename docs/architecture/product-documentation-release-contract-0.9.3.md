# BPM 0.9.3 Documentation Search And Local Assistant Release Contract

Date: 2026-07-28

Backlog item: `BPM093-M1-06`

## Purpose

This contract defines the release-blocking outcomes for BPM 0.9.3. It maps the approved
documentation-search and local-RAG epic to accountable evidence, resource and quality thresholds,
and reproducible checks. It is a release-control document, not a statement that an open search,
model, assistant, or web capability has shipped.

The project maintainer owns every gate and its functional area. An owner may delegate work, but no
gate becomes ownerless. Missing future checks, models, index artifacts, or web-provider approval
keep their gates open; a manual demonstration, backlog row, or model benchmark alone cannot close
a release gate.

README remains durable current-state product documentation. Target-version planning and non-final
release status belong to this contract, the backlog, and `CHANGELOG.md`; README cannot close a gate
by acquiring a release-history, planned-version, or completion statement.

## Blocking Gates

Every gate below is release-blocking. `Closed` means that the stated scope and recorded check have
passed; `Open` means implementation or verification remains.

| Gate | Required outcome and threshold | Accountable owner | Required evidence | Focused verification | State |
| --- | --- | --- | --- | --- | --- |
| `BPM093-G01` | Product metadata, runtime, editable package, active documentation index, and version tests agree on BPM 0.9.3; historical versions stay explicitly historical. | Project maintainer - release metadata | Version surfaces, editable-package probe, current-system map, docs index, and migration context. | `./.venv/bin/pytest -q tests/test_current_version_surfaces.py tests/test_bootstrap_config.py tests/test_docs_index.py` | Closed |
| `BPM093-G02` | Dependencies, frontend vendor, documentation toolchain, browser drivers, search candidates, inference runtime, and model candidates have an explicit currency, license, provenance, platform, advisory, and update decision. | Project maintainer - dependency and model supply chain | [Dependency currency decision](dependency-currency-0.9.3.md), manifests, locks, vendor checksums, and advisory disposition. | `make verify-frontend-vendor`, `npm audit --omit=dev`, and `./.venv/bin/pytest -q tests/tools/test_verify_frontend_vendor.py tests/test_docs_index.py` | Closed |
| `BPM093-G03` | The non-final changelog entry exists while README has no target-version, planned-release, history, or completion copy. | Project maintainer - release documentation | `CHANGELOG.md`, README guard assertions, and backlog/runbook release boundaries. | `./.venv/bin/pytest -q tests/test_current_version_surfaces.py tests/test_readme_firefox_policies_contract.py` | Closed |
| `BPM093-G04` | An approved architecture and threat contract defines source eligibility, artifact ownership, installation/removal, no-network default, conversation retention, citations, fallback, scope taxonomy, and a safe-local-AI boundary replacing only relevant historic prohibitions. | Project maintainer - assistant architecture and safety | M1-07 and M2 ADRs, threat model, corpus schema, lifecycle/state contracts, and focused fail-closed fixtures. | Future focused M1-07/M2 contract tests and `make test-docs-contract` | Open |
| `BPM093-G05` | BPM-owned static documentation search is selected after six-locale relevance, CJK, accessibility, CSP, footprint, latency, operability, and fallback benchmarks. An external candidate must be no worse than the previous-version control and strictly more relevant in every locale before it replaces that engine. | Project maintainer - documentation search | Frozen corpus/query fixtures, benchmark report, selected-engine ADR, exact version/license/source/checksum, and fallback design. | Focused M3 search tests, `make test-docs`, and `make test-docs-contract` | Closed |
| `BPM093-G06` | Selected lexical search is reproducibly built from reviewed content and preserves deterministic direct search, navigation, contextual links, six locales, and AI-disabled operation. Baseline P95 result rendering is at most 250 ms. | Project maintainer - documentation search implementation | Build/index manifest, source hashes, locale reports, accessibility/CSP/offline evidence, and regression measurements. | Future focused M4 search tests, `make test-docs`, `make test-docs-ui`, and `make test-docs-browser` | Open |
| `BPM093-G07` | Reviewed DITA is transformed into versioned, locale-bound chunks and selected multilingual embeddings; hybrid retrieval preserves exact identifiers. Warm retrieval P95 is at most 2 s, Top-1 is at least 90%, Recall@5 at least 98%, and exact identifiers are 100% correct in every locale. | Project maintainer - retrieval and corpus | Chunk schema/manifest, model/version/dimension/source hashes, per-locale retrieval corpus, index compatibility report, and atomic rebuild evidence. | Future focused M5 retrieval tests and `make test-docs-contract` | Open |
| `BPM093-G08` | A compact local CPU runtime and chat model are selected with immutable source, checksum, license, quantization, supported platform, installation/removal, rollback, and no-exposed-server evidence. No GPU, account, hosted inference, or telemetry is required. | Project maintainer - local inference runtime | M6 shortlist ADR, model/runtime manifest, signed or checksummed artifacts, lifecycle tests, and offline-install/removal record. | Future focused M6 runtime tests and `pytest -q tests/test_docs_index.py` | Open |
| `BPM093-G09` | On the i5-7200U, 7.1 GiB, CPU-only baseline, selected chat, embedding, index, and runtime artifacts occupy at most 2.5 GiB; model/embedding/retrieval worker RSS is at most 3.5 GiB; disabled mode starts no AI worker. | Project maintainer - resource engineering | Reproducible baseline-machine inventory, cold/warm measurements, artifact-size report, disabled-mode probe, and unload record. | Future focused M6/M13 resource tests and `make test-release` | Open |
| `BPM093-G10` | Grounded answers cite current local sources: every displayed citation resolves, at least 95% of scored claims are supported, and unsupported-answer abstention is at least 95% in each locale. Warm TTFT P95 is at most 10 s, cold TTFT P95 at most 30 s, median throughput at least 3 tokens/s, and cited completion P95 at most 60 s. | Project maintainer - answer quality | Frozen six-locale answer/dialogue/citation/abstention corpus, prompt and output policy, per-locale report, and cancellation evidence. | Future focused M7 answer tests and `make test-docs-contract` | Open |
| `BPM093-G11` | A pre-generation multilingual scope gate blocks 100% of reviewed off-topic, injection, tool, file, process, and network-escape fixtures before inference; in-scope false refusal is at most 2% per locale. The assistant cannot mutate BPM state, execute commands, access arbitrary files/URLs, or expose a model service. | Project maintainer - assistant security | M8 taxonomy, pre-inference invocation counters, adversarial fixtures, least-privilege configuration, and independent threat review. | Future focused M8 security tests and `make test-release` | Open |
| `BPM093-G12` | Local mode emits no query, conversation, chunk, embedding, or model telemetry and makes no network request after explicit model installation. Chats are session-local by default and have tested clear/expiry behavior. | Project maintainer - privacy and conversation lifecycle | Network/telemetry probes, retention design, diagnostics-redaction checks, clear/restart/expiry tests, and data-flow review. | Future focused M8 privacy tests and `make test-release` | Open |
| `BPM093-G13` | Optional web evidence is selected, explicitly consented, BPM-scoped, sanitized, source-labelled, and disabled by default. Rejected/off-topic queries make zero provider calls; provider absence and failure retain local-only behavior. No qualifying provider blocks release rather than silently dropping the promised capability. | Project maintainer - web evidence security | M9 provider ADR, terms/license/privacy review, allowlist and SSRF tests, consent records, local-vs-web citation evidence, and provider-down fixture. | Future focused M9 web-security tests and `make test-release` | Open |
| `BPM093-G14` | The assistant is a usable, accessible six-locale documentation companion beside deterministic search: free questions, bounded follow-ups, citations, clarify/abstain/refuse, stop, clear, unavailable/degraded states, resource warnings, and web consent are natural and equivalent in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. | Project maintainer - assistant UX and localization | M10 UI/state contracts, six locale catalogs and editorial reviews, accessibility/theme/zoom/keyboard evidence, and search-only fallback tests. | Future focused M10 UI tests, `make test-locale-contract`, `make test-docs-ui`, and `make test-docs-browser` | Open |
| `BPM093-G15` | Documentation, operations, update/rollback, artifact provenance, privacy/scope/web behavior, screenshots/targets, authoring rules, docs index, and snapshots describe only shipped behavior; models, embeddings, generated indexes, transcripts, and reports follow their artifact boundary. | Project maintainer - documentation and maintenance | M11-M12 runbooks, six-locale DITA sources, admin procedures, screenshot/target records, documentation-update verification, and `make docs-install-dev` handoff. | Future focused M11/M12 tests, `make docs-release-check`, and `./.venv/bin/pytest -q tests/test_docs_index.py` | Open |
| `BPM093-G16` | Final quality proves type/lint/test/coverage, documentation release validation, frozen six-locale search/RAG quality, old-laptop resources, security/privacy/scope/web gates, and Chromium/Selenium behavior. The final changelog contains only verified outcomes; README boundaries and maintainer handoff remain intact. | Project maintainer - quality and release | M13 command records, coverage reports, quality/resource/security evidence, browser versions/results, changelog review, docs-index check, reviewed commit, and push handoff. | `make typecheck`, `make lint`, `pytest -q`, `make coverage`, `make docs-release-check`, `make test-ui`, and `make test-release` | Open |

## Evidence Handoff

| Backlog boundary | Release evidence owned by the boundary |
| --- | --- |
| M1-M2 | Version and package evidence, changelog/README boundary, supply-chain decision, active-reference audit, architecture, threat model, corpus, artifact, resource, and lifecycle contracts. |
| M3-M4 | Six-locale search benchmark/ADR, selected indexer integration, deterministic build assets, lexical-search parity, and AI-disabled fallback. |
| M5-M7 | Reviewed chunks, embeddings, retrieval/index compatibility, local model/runtime selection, quality corpus, grounded answers, citations, abstention, dialogue, and resource measurements. |
| M8-M9 | Pre-inference scope blocking, adversarial-security review, privacy/retention controls, optional-provider decision, consent, SSRF/injection safety, and local-only fallback. |
| M10 | Accessible six-locale chat UI, model states, degraded/search-only behavior, citations, and web disclosures. |
| M11-M12 | Atomic refresh/rollback, update runbooks and drift checks, six-locale user/admin documentation, screenshots/targets, README decision, docs index/snapshot, and dev-install handoff. |
| M13 | Static/full/release/browser validation, frozen quality and resource evidence, security closure, final changelog, README boundary, commit, and maintainer-run push command. |

## Gate Closing Rules

1. A gate closes only after all named implementation and reproducible checks pass against the
   selected, checksummed artifacts and the relevant clean generated-output state.
2. No average can hide a failing locale: all six locales must pass every stated search, retrieval,
   answer, scope, privacy-copy, and UX requirement.
3. AI-disabled, absent, incompatible, busy, crashed, or resource-limited states preserve lexical
   search, navigation, direct topics, and contextual help without a network fallback.
4. Model weights, embeddings, generated indexes, web bodies, transcripts, build output, and
   benchmark reports are never committed as hand-authored source. Installation is explicit,
   license-visible, checksummed, removable, and supports verified offline input.
5. The scope gate precedes retrieval, inference, and optional web access. Prompt-only instructions
   do not satisfy the security boundary.
6. Local BPM sources outrank external evidence. Web mode is opt-in and cannot be enabled by a model,
   a page, a URL, or absent credentials.
7. Any change to source DITA, locale, search/index format, embedding, model, runtime, prompt,
   dependency, provider, browser, browser driver, UI, resource ceiling, or documentation procedure
   reopens every affected gate.
8. Browser and Selenium checks require immediate sandbox escalation. A missing future command or
   unavailable candidate does not waive its gate.

## Explicitly Deferred Outcomes

The following do not block BPM 0.9.3 unless a separately approved task admits them:

- base-model fine-tuning or a LoRA/adapter; ordinary product updates use reviewed chunking and
  reindexing instead;
- cloud inference, hosted vector databases, hosted search, accounts, API keys, telemetry, GPU/NPU,
  model-server exposure, browser automation, arbitrary tools, or profile mutation by the assistant;
- broader general-purpose chat, non-BPM web search, and training from raw DITA or conversations;
- any model, search engine, embedding, runtime, or web provider not selected by its benchmark and
  safety gates.
