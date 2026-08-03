# Documentation Configuration

This hand-authored directory contains the reviewed documentation toolchain authority:

- `toolchain-lock.json` pins DITA-OT, Temurin, platform archives, upstream SHA-256 values, and the
  repository-owned plug-in identity;
- `artifact-policy.json` defines committed/ignored/generated/shipped documentation output rules,
  normalized archive metadata, release paths, and the current `runtime_ready=false` blockers after
  manifest generation;
- `requirements.lock` pins the isolated Python documentation test environment;
- `metadata-vocabulary.json` fixes the allowed DITA 1.3 conditional attributes and binds dynamic
  policy, CIS, and API-operation groups to their maintained inventories;
- `user-guide-map-0.9.0.json` maps every inventoried user capability to a primary case-oriented
  User Guide topic path before product topics are authored;
- `user-guide-coverage-closure-0.9.0.json` records the closed User Guide release-readiness mapping
  across README capabilities, routes, templates, locale catalogs, API boundaries, and browser-smoke
  evidence;
- `user-guide-screenshot-matrix-0.9.1.json` defines the minimal BPM 0.9.1 User Guide screenshot
  matrix across all six locales without expanding into Firefox Policy, CIS, API, or
  Administrator/DevOps screenshots;
- `firefox-policy-topic-model-0.9.0.json` defines the Firefox Policy Guide DITA reference topic
  model used by schema-grounded policy topic generation;
- `cis-settings-topic-model-0.9.0.json` defines the CIS Settings Guide DITA reference topic model,
  disclaimer contract, source boundary, and automation/manual-review fields;
- `firefox-policy-context-targets-0.9.0.json` maps Firefox policy families to contextual
  documentation targets, related policies, user tasks, API operations, and validation guidance;
- `search-corpus-and-results-0.9.0.json` defines the deterministic local documentation search
  corpus, result shape, facets, exclusions, integrity checks, and explicit no-AI/no-RAG boundary;
- `search-normalization-aliases-0.9.0.json` defines locale-aware search normalization, reviewed
  aliases, technical identifier preservation, and the six-locale query fixture suite;
- `search-ranking-typo-0.9.0.json` defines deterministic ranking weights, bounded typo tolerance,
  explainable score components, and ranking fixture expectations;
- `search-facets-filters-0.9.0.json` defines deterministic search facet fields, filter
  composition, URL-state preservation, corpus count expectations, and localized empty-result
  recovery without AI/RAG/embeddings/generative answers;
- `search-ui-filter-contract-0.9.1.json` defines the compact default search UI, deliberate
  expansion behavior, locale-owned visible filter labels, selected-filter persistence, keyboard
  access, and empty-result recovery rules for the BPM 0.9.1 documentation polish work;
- `navigation-tree-contract-0.9.1.json` defines the BPM 0.9.1 hierarchical documentation tree,
  root/guide/section/topic node model, one manifest-backed navigation source per locale, compact
  page hosts, safe shared-runtime rendering and failure behavior, active state, return behavior,
  URL invariants, keyboard semantics, collapse state, and locale-owned navigation labels;
- `documentation-polish-regression-gates-0.9.1.json` binds the retired API guide, Administrator
  API ownership, navigation artifact integrity, compact tree hosts, locale-owned UI terminology,
  visible-English review coverage, and live bounded allowlists to fail-closed release checks;
- `documentation-navigation-language-browser-qa-0.9.1.json` freezes the six-locale desktop/narrow
  navigation, failure fallback, long-tree wheel/keyboard scrolling, retired API-node absence, and
  exact All settings interface-name/visible-prose assertions for the final M10 browser QA;
- `interface-name-authority-0.9.1.json` maps documentation names for BPM surfaces, modes,
  workflows, settings categories, appearance, and locale controls to the same maintained runtime
  catalog key in all six locales, while classifying historical aliases, non-UI technical terms,
  and catalog defects that must be corrected before documentation replacement;
- `interface-name-replacement-0.9.1.json` records the five-locale DITA replacement baseline,
  forbidden source UI aliases, resolved runtime-catalog defects, ambiguous ordinary-prose
  boundary, and zero-residual closure evidence for BPM091-M10-05;
- `visible-english-prose-review-0.9.1.json` records the full 805-source M10-06 review, the
  10,410-block structural pass, separate review of 36 nonparallel sources, zero release-blocking
  exact English carryover, reviewed locale homographs, and the bounded technical-literal residual set;
- `all-settings-row-help-link-contract-0.9.1.json` defines the BPM 0.9.1 All Settings row-level
  documentation-help target resolution, no-link dispositions, circled-info layout, localized
  accessible labels, keyboard behavior, and manifest target validation;
- `documentation-polish-guardrails-0.9.1.json` registers the BPM 0.9.1 guardrails that fail closed
  for missing screenshot matrix rows, localized search-filter English fallback, duplicate
  navigation titles, pure-white primary light-theme surfaces, and All Settings rows without valid
  help-link dispositions;
- `documentation-sufficiency-review-protocol-0.9.1.json` defines the BPM 0.9.1 review checklist
  and evidence types proving that documented tasks can be completed and reach their stated result;
- `search-quality-performance-0.9.0.json` defines deterministic search quality fixtures,
  top-result expectations, no-result/adversarial coverage, index-size limits, and CI-stable
  scan-unit performance budgets;
- `search-selection-shortlist-0.9.3.json` freezes public search-engine entry gates, the weighted
  M3 selection matrix, and the unbenchmarked current/Pagefind/Meilisearch Community Edition shortlist;
- `search-candidate-prototypes-0.9.3.json` defines the compact six-locale adapter inputs and
  normalized-result boundary used before M3 candidate execution and benchmarks;
- `search-relevance-benchmark-0.9.3.json` locks M3 candidate artifact hashes, identical
  six-locale query evidence, metric definitions, raw/summary output, and no-selection boundary;
- `search-integrity-drift-0.9.0.json` defines search-index drift gates for manifest topics,
  anchors, locale/output metadata, snippets, and Firefox policy/CIS/API inventory coverage;
- `rag-chunk-extraction-0.9.3.json` defines the M5 deterministic published-DITA unit, typed-block,
  bound, provenance, stable-ID, and canonical chunk-manifest contract; it does not select a model
  or enable retrieval;
- `embedding-model-benchmark-0.9.3.json` pins the M5 candidate revisions, model/tokenizer and
  runtime checksums, prefixes, normalization, six-locale retrieval/cross-language gates, resource
  ceilings, and fail-closed selection rule; it does not introduce a selected model or runtime;
- `embedding-model-benchmark-m5-03a-0.9.3.json` records the rejected M5 remediation shortlist,
  including the explicit 0.75-GiB embedding-component allocation, model-specific post-pooling, and
  the same six-locale, cross-language, offline, checksum, and no-swap selection gates;
- `chat-rag-embedding-selection-contract-0.9.3.json` freezes the chat-only, same-locale embedding
  selection boundary: RAG is independent of ordinary search, evidence is citable or abstained,
  and optional external sources are opt-in and excluded from local knowledge;
- `chat-rag-embedding-benchmark-0.9.3.json` pins the C same-locale chat evidence benchmark,
  reusing exact candidate source contracts while excluding cross-language retrieval, ordinary search,
  answer generation, and optional external evidence;
- `chat-rag-embedding-decision-0.9.3.json` records the maintainer's checksum-pinned E5-base
  implementation acceptance without rewriting the failed no-swap selector result; M5-03D remains a
  historical clean-host diagnostic after the accepted resource-policy amendment;
- `chat-rag-vector-storage-decision-0.9.3.json` selects the active-locale exact float32 matrix for
  E5-base and records the benchmarked rejection of pre-v1 sqlite-vec, artifact recovery, and the
  remaining integrity, grounding, security, interactive-resource, and release validation;
- `chat-rag-exact-generation-contract-0.9.3.json` pins six locale-private E5-base matrix
  generations, verified incremental cache reuse, immutable manifests, private staging, and atomic
  activation of the exact-vector backend;
- `chat-rag-retrieval-contract-0.9.3.json` pins the runtime-only same-locale exact scan over an
  activated E5-base generation: current-version/guide filters, local citations, no-evidence
  outcome, integrity checks, and independence from M4 ordinary search;
- `chat-rag-evidence-packing-contract-0.9.3.json` freezes pre-generation same-locale evidence
  packing: exact-token budget, canonical source-data serialization, deterministic confidence and
  deduplication, citations, and answer/clarify/abstain gates;
- `chat-rag-retrieval-validation-0.9.3.json` pins the M5 active-generation validation: selected
  E5-base and generation/retrieval/evidence contracts, reviewed six-locale corpus, exact published
  chunk/topic coverage, citable same-locale retrieval, reproducibility, interactive resources,
  no-network/M4 isolation, corruption/stale runtime-test evidence, and real stdout progress;
- `chat-rag-clean-host-validation-0.9.3.json` records the failed M5-03D reboot attempt without
  disguising it as a selection pass: swap changed before valid quality metrics; it is retained as a
  historical diagnostic after the accepted resource-policy amendment;
- `chat-rag-resource-policy-amendment-0.9.3.json` permits CPU/RAM/swap for offline embedding
  generation, retires no-swap as a release blocker, retains interactive P95/RSS limits, and forbids
  model-weight training;
- `local-chat-model-runtime-shortlist-0.9.3.json` freezes the M6 benchmark-only local-chat
  shortlist: immutable llama.cpp runtime and official compact Qwen GGUF artifacts, their exact
  licenses/checksums/templates/context/CPU/security/six-locale gates, and the explicit exclusion
  of gated or unofficial-conversion candidates pending separate provenance review;
- `grounded-answer-benchmark-harness-0.9.3.json` freezes the M6 candidate-neutral workload,
  fixed non-thinking generation settings, evidence/oracle separation, strict cited-answer and
  claim-level human-review gates, six-locale coverage, metrics, isolation, and stdout-progress
  requirements; it does not download, start, or select a model;
- `local-chat-target-laptop-benchmark-0.9.3.json` freezes M6-03's accepted compact i5-7200U
  CPU-only comparative-selection matrix: one cold, two warm first-answer, and one warm-dialogue
  sample per locale; hard per-sample disk/RSS/latency/throughput gates; one cancellation/unload
  check; and factual stdout progress. Swap remains an operational diagnostic rather than a rejection
  condition;
- `local-chat-model-runtime-decision-0.9.3.json` records the M6-04/M6-04A selected Qwen3 0.6B
  best-effort local-CPU policy, Qwen3 1.7B rejection, exact runtime/inference/retrieval boundaries,
  and the no-rerun decision; it installs no model and adds no product runtime;
- `local-chat-model-installation-contract-0.9.3.json` records the M6-05 explicit-only lifecycle for
  the selected Qwen3 0.6B artifact: six-locale disclosure, pinned provenance and checksum,
  resumable verified download, offline local-artifact verification, fixed private storage, atomic
  promotion, compatibility checks, bounded command progress, and manifest-owned removal; it adds no
  worker, chat endpoint, or automatic model action;
- `local-chat-worker-contract-0.9.3.json` records the M6-06 disabled-by-default, one-generation
  local `llama-cli` worker: verified retained runtime archive, minimal private extraction, direct
  stdin/stdout transport, fixed CPU/context/output limits, cancellation/timeout/unload, safe health,
  persistent development bootstrap, and the absence of an assistant HTTP route or browser control;
- `local-chat-runtime-validation-0.9.3.json` records the M6-07 six-locale real worker probe,
  deterministic/UTF-8/hidden-reasoning/input/context/lifecycle checks, digest-only ignored evidence,
  factual command progress, and the lexical-search fallback boundary; it adds no chat route;
- `grounded-conversation-api-contract-0.9.3.json` records the M7-01 versioned same-origin assistant
  API, opaque request/source handles, bounded request state machine, safe SSE/error shapes, optional
  web-request boundary, and the fact that it adds no route or controller;
- `documentation-assistant-api-delivery-contract-0.9.3.json` records the M12A-01 same-origin
  transport delivery, opaque session ownership and fail-closed unavailable default; it defers local
  runtime/index assembly, browser activation and external evidence to their separate M12A tasks;
- `documentation-assistant-external-evidence-release-contract-0.9.3.json` records M12A-04's
  released server path for optional external evidence: administrator configuration plus a
  persistent reader-controlled same-locale mode, repeated scope/configuration checks, fixed Brave
  and Mozilla boundaries, local-first merge, separate external claims/sources and local fallback;
- `grounded-conversation-orchestration-contract-0.9.3.json` records the M7-02 fail-closed pipeline
  from scope through same-locale E5 retrieval, evidence, worker and server citation binding; it keeps
  ordinary search independent and has no route, session persistence, scope classifier or web provider;
- `grounded-conversation-context-contract-0.9.3.json` records the M7-03 memory-only locale/version
  session identity, four-turn deterministic eviction, resolved-entity bound, topic/version reset and
  clear semantics; it adds no HTTP, browser storage, database, disk or telemetry;
- `grounded-conversation-answer-validation-contract-0.9.3.json` records the M7-04 strict JSON
  response shape, server-side local-citation binding, locale-safe URL validation and extractive or
  abstaining downgrade; it does not add a route, browser renderer, network path or search call;
- `grounded-conversation-streaming-contract-0.9.3.json` records the M7-05 bounded in-memory event
  lifecycle, one-active/one-queued worker serialization, cancellation, timeout, opaque sources and
  backpressure; it adds no HTTP route or browser UI;
- `grounded-conversation-diagnostics-contract-0.9.3.json` records the M7-06 content-free local
  assistant compatibility, worker, queue, safe error-class and web-capability diagnostics;
- `grounded-conversation-evaluation-0.9.3.json` records the M7-07 six-locale deterministic
  conformance matrix and quality floors for the implemented M7 boundaries, while explicitly
  excluding any repeat chat-model benchmark or language-quality claim;
- `bpm-topic-scope-taxonomy-0.9.3.json` records the M8-01 deterministic six-locale BPM scope
  taxonomy, stable allow/clarify/refuse precedence, code-switching rule and evidence-only
  abstention boundary; it adds no scope classifier or inference path;
- `bpm-topic-scope-gate-contract-0.9.3.json` records the M8-02 six-locale deterministic alias,
  bounded-context and local cosine-similarity scope gate, including fail-closed thresholds and the
  zero-retrieval/LLM/network boundary for refused or clarified requests;
- `bpm-scope-adversarial-fixtures-0.9.3.json` records the M8-03 fixed per-locale and code-switched
  jailbreak/control-override fixtures, bounded encoded-control detection, and the zero
  similarity/retrieval/worker/network acceptance boundary;
- `bpm-prompt-content-boundary-contract-0.9.3.json` records the M8-04 inert-data treatment for
  local evidence, fixed prompt delimiters, active-content stripping, bounded encoded-control
  rejection, no-web-before-M9 boundary and server-owned model-output authority;
- `bpm-ai-least-privilege-contract-0.9.3.json` records the M8-05 BPM-owned execution-root,
  subprocess/proxy, redirect, same-origin-JSON and bounded-resource controls without adding a chat
  route or browser surface;
- `bpm-conversation-retention-contract-0.9.3.json` records the M8-06 private memory-only
  conversation defaults: clear/restart behavior, idle/absolute expiry, completed-stream scrubbing,
  content-free diagnostics and the separately reviewed future-persistence boundary;
- `bpm-assistant-threat-review-0.9.3.json` records the M8-07 independent disposition of all 14 M2
  threats, two closed deterministic bypasses, zero security exceptions and the explicit M9/M10/M11/
  M13 product-release blockers;
- `bpm-web-evidence-provider-trust-policy-0.9.3.json` records the M9-01 Brave Search API LLM Context
  BYOK decision, reviewed terms/privacy/alternatives, six-locale request bounds, fixed Mozilla source
  policy and no-result-URL-fetch data flow without enabling network access;
- `bpm-web-evidence-opt-in-consent-contract-0.9.3.json` records the M9-02 disabled-by-default BYOK
  configuration, exact-question Brave disclosure, five-minute memory-only one-use consent, six-locale
  language binding and the no-route/no-network boundary;
- `bpm-web-evidence-retrieval-contract-0.9.3.json` records the M9-03 fixed Brave POST adapter,
  scope/consent order, proxy/redirect/SSRF barriers, exact Mozilla URL post-filter, inert bounded
  `grounding.generic` quarantine and request-lifetime clearing;
- `bpm-web-evidence-merge-contract-0.9.3.json` records the M9-04 local-first web merge, freshness
  and conflict abstention, separately labelled/cited external claims, bounded context lease and the
  no-route/no-worker-composition boundary;
- `bpm-web-evidence-security-contract-0.9.3.json` records the M9-05 adversarial closure of the two
  M9 web release blockers: fixed-provider/network isolation, six-locale injection rejection,
  bounded process-memory rate limiting, cancellation, redaction, local-only failure and explicit
  external citations, without a route, UI, worker invocation or live network test;
- `documentation-assistant-entry-contract-0.9.3.json` records the M10-01 localized static assistant
  entry beside deterministic search: honest unavailable state, no dead control, no assistant HTTP
  route or status poll, and no model/worker/retrieval/network work before the M10 security gate;
- `documentation-assistant-surface-contract-0.9.3.json` records the M10-02 localized, named and
  bounded dialogue markup: disabled question/send/stop/clear controls, transcript/status/source
  semantics, no fake client action, and the still-open M10 HTTP/rendering/rate-limit gates;
- `documentation-assistant-copy-0.9.3.json` records the M10-03 six-locale assistant catalogue and
  per-locale static `assistant-copy.json` output: states, dialogue outcomes, citations, model
  disclosure/removal text and one-question web-consent text, without enabling assistant UI or I/O;
- `local-model-management-ui-contract-0.9.3.json` records the M10-03A explicit release UI for the
  single M6 model artifact: lazy inspection, localized disclosure, confirmation, verification,
  progress, cancellation and removal, plus the bounded same-origin/rotating-CSRF lifecycle API;
- `documentation-assistant-presentation-contract-0.9.3.json` records M10-04's transport-free,
  text-only rendering of an already validated final answer and current source views, without chat
  route enablement, model activity, web activity or any ordinary-search change;
- `documentation-assistant-resource-state-contract-0.9.3.json` records M10-05's transport-free,
  locale-owned rendering of bounded local-assistant resource states and direct deterministic-search
  recovery, without enabling chat controls, polling, model work or ordinary-search changes;
- `documentation-assistant-floating-ui-contract-0.9.3.json` records M12B's floating lower-right
  support-chat UI: collapsed title-only entry, viewport-bound expanded panel, short state/install
  controls and tab-scoped safe dialogue display persistence; its external-sources selector remains
  assigned to M12B-06 after M12A-04 delivered the server capability;
- `documentation-assistant-floating-web-mode-contract-0.9.3.json` records M12B-06's released
  six-locale Ready-state switch, tab/locale-private preference and opaque tab identity, server-mode
  synchronization, unavailable-disabled state, separate external-claim rendering and browser-side
  Mozilla URL defence;
- `documentation-assistant-floating-browser-qa-contract-0.9.3.json` records M12B-07's Chromium
  release matrix for the six-locale floating assistant: responsive light/dark portal states,
  persistence, long transcript, safe chat/model failures, external-switch default/persistence, CSP,
  and deterministic-search independence;
- `documentation-assistant-web-mode-contract-0.9.3.json` records that M10-06's historical
  per-question consent presentation is superseded by M12B-06's persistent reader switch; its
  current helper remains transport-free and only validates/renders server mode state;
- `THIRD_PARTY_NOTICES.md` records licenses and distribution boundaries.

Do not place downloaded dependencies, DITA-OT distributions, Java runtimes, caches, credentials, or
generated site files here. The accepted design schemas currently remain maintained architecture
artifacts under `docs/architecture/`; later implementation tasks promote the required runtime/build
copies deliberately and test them for drift.

`make setup-docs-toolchain` is the only networked installation entry point. It places verified
archives, extracted tools, wheels, and a test virtual environment under the ignored
`documentation/.cache/toolchain/`. Re-running with `DOCS_TOOLCHAIN_OFFLINE=1` forbids downloads and
proves the cache is sufficient. Unknown platforms and checksum/version mismatches fail closed.
