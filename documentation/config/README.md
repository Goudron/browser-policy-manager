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
- `search-quality-performance-0.9.0.json` defines deterministic search quality fixtures,
  top-result expectations, no-result/adversarial coverage, index-size limits, and CI-stable
  scan-unit performance budgets;
- `search-integrity-drift-0.9.0.json` defines search-index drift gates for manifest topics,
  anchors, locale/output metadata, snippets, and Firefox policy/CIS/API inventory coverage;
- `THIRD_PARTY_NOTICES.md` records licenses and distribution boundaries.

Do not place downloaded dependencies, DITA-OT distributions, Java runtimes, caches, credentials, or
generated site files here. The accepted design schemas currently remain maintained architecture
artifacts under `docs/architecture/`; later implementation tasks promote the required runtime/build
copies deliberately and test them for drift.

`make setup-docs-toolchain` is the only networked installation entry point. It places verified
archives, extracted tools, wheels, and a test virtual environment under the ignored
`documentation/.cache/toolchain/`. Re-running with `DOCS_TOOLCHAIN_OFFLINE=1` forbids downloads and
proves the cache is sufficient. Unknown platforms and checksum/version mismatches fail closed.
