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
