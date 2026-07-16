# BPM Product Documentation Workspace

This directory is the isolated source, build, asset, tooling, fixture, and test boundary for the
BPM 0.9.0 product documentation portal. Maintainer architecture decisions and backlog records stay
under `docs/`; publishable product documentation belongs here.

The workspace is scaffolded by `BPM090-M3-01`; its local context guide and compact snapshot are
maintained by `BPM090-M3-02`, and its pinned local toolchain is implemented by `BPM090-M3-03`.
`BPM090-M3-04` adds the localized guide and aggregate maps; `BPM090-M3-07` adds deterministic
ignored release-candidate packaging; `BPM090-M3-08` adds the accessible static portal shell and
theme; `BPM090-M3-09` adds the generated manifest and UI target map; `BPM090-M3-10` adds maintainer
authoring runbooks; `BPM090-M4-01` defines the case-oriented User Guide map; `BPM090-M4-02` adds
localized orientation/core concepts; `BPM090-M4-03` adds Profile Library management topics;
`BPM090-M4-04` adds import/export topics; `BPM090-M4-05` adds comparison topics;
`BPM090-M4-06` adds Guided Editor topics; `BPM090-M4-07` adds All Settings topics; `BPM090-M4-08`
adds JSON Editor topics; `BPM090-M4-09` adds schema/validation topics; `BPM090-M4-10` adds
cross-cutting user topics; `BPM090-M4-11` adds troubleshooting topics; `BPM090-M4-12` closes the
User Guide coverage matrix; `BPM090-M5-01` defines the Firefox Policy topic model;
`BPM090-M5-02` adds generated Firefox policy skeletons; `BPM090-M5-03` adds Firefox policy
selection, deployment-boundary, and starter-preset concepts; `BPM090-M5-04` adds schema-valid
Firefox policy examples; `BPM090-M5-05` adds Release/ESR channel-difference metadata and guidance;
`BPM090-M5-06` adds complex policy family and managed-preference locking guidance; `BPM090-M5-07`
adds Firefox policy relationship/context targets; `BPM090-M5-08` adds Firefox schema drift gates;
`BPM090-M5-09` adds Firefox policy provenance/accuracy gates; `BPM090-M6-01` defines the CIS
Settings Guide topic model/disclaimer contract; `BPM090-M6-02` adds CIS orientation/selection
topics; `BPM090-M6-03` adds generated CIS recommendation skeletons; `BPM090-M6-04` adds CIS
mapping tables and layer-checked examples; `BPM090-M6-05` adds CIS preset/layer/source-attribution
topics; `BPM090-M6-06` adds CIS manual-review, deviation, and verification topics; `BPM090-M6-07`
adds CIS Level 1 and Level 2 end-to-end workflow topics and deterministic fixtures; `BPM090-M6-08`
adds the CIS benchmark/mapping drift gate to the inventory-refresh runbook and generated CIS index;
`BPM090-M6-09` adds the CIS accuracy/provenance review artifact and gates; `BPM090-M7-01` adds API Integration Guide audience and supported-pattern topics; `BPM090-M7-02` adds API conventions and limitation topics; `BPM090-M7-03` adds profile lifecycle integration tasks; `BPM090-M7-04` adds Firefox import/export integration tasks; `BPM090-M7-05` adds validation-gate integration tasks; `BPM090-M7-06` adds health/readiness handshake tasks; `BPM090-M7-07` adds end-to-end control-product scenario tasks; `BPM090-M7-08` adds reusable curl and Python examples; `BPM090-M7-09` adds OpenAPI-to-DITA drift checks; `BPM090-M8-01` defines the DITA localization workflow; `BPM090-M8-04` adds Firefox Policy Guide locale-parity gates; `BPM090-M8-05` adds CIS Settings Guide locale-parity gates; `BPM090-M8-06` adds API Integration Guide locale-parity gates; `BPM090-M9-01` adds the `/help/` runtime bridge; `BPM090-M9-02` adds locale-aware `/help/` routing; `BPM090-M9-03` adds the BPM header documentation link; `BPM090-M9-04` adds manifest-backed runtime URL resolution; `BPM090-M9-05` adds five surface contextual help links; `BPM090-M9-06` adds manifest-backed policy, CIS, validation, and import/export help icons; `BPM090-M9-07` adds localized missing, stale, incompatible, incomplete, and not-found portal states; `BPM090-M9-08` adds focused accessibility, responsive, CSP, theme, and OpenAPI coexistence integration contracts; `BPM090-M10-01` defines deterministic search corpus and result contracts; `BPM090-M10-02` adds reproducible per-locale static search indexes; `BPM090-M10-03` adds locale-aware normalization, reviewed aliases, and query fixtures; `BPM090-M10-04` adds deterministic ranking and bounded typo tolerance; `BPM090-M10-05` adds deterministic search facets, filters, counts, URL-state preservation, and localized empty-result recovery; `BPM090-M10-06` adds the accessible local search UI; `BPM090-M10-07` adds search quality/performance fixtures; `BPM090-M10-08` adds search-index drift/integrity gates; `BPM090-M10-09` adds non-AI search boundary copy; `BPM090-M11-01` through `BPM090-M11-10` add isolated documentation test-suite boundaries, focused Make commands, source fast checks, coverage, fixtures, diagnostics, generated snapshots, release/browser gates, and the debugging protocol; the early `BPM090-M8-02` slice adds current User Guide locale-parity contracts; `BPM090-M12-01` adds the Administrator/DevOps Guide map/key/root contract and scope boundary; and `BPM090-M12-02` audits API/User Guide integration content for future Administrator/DevOps re-home.

`BPM090-M12-03` through `BPM090-M12-13` add six-locale Administrator/DevOps source-deployment, operations, update-from-source, API integration, external control-product DevOps runbook topics, reusable DevOps example templates, troubleshooting/diagnostics topics, production-readiness boundary topics, Administrator Guide validation fixtures/contracts, and final six-locale admin localization review for Linux, Windows 10/11 through WSL, runtime configuration, storage/logs/backups, CORS/security limits, verification, WSL troubleshooting, documentation rebuild checks, rollback/stop conditions, migrated API operation/convention topics, executable pull/list/read, validate-before-apply, import-review-export, health-gated startup, failure-recovery/audit-evidence workflows, environment setup, curl/Python snippets, JSON/multipart samples, response assertions, failed startup/probes, schema/cache/API validation, import/export, database/storage, stale dependencies, documentation portal build/link failures, single-node source readiness, network exposure/proxy-readiness questions, monitoring/backup/update windows, deferred production/HA/reverse-proxy boundaries, stale-command checks, health/API example checks, locale-peer checks, WSL caveats, deferred-claim warnings, and no-fallback/no-short-summary parity.

The dev-inspection slice of `BPM090-M13-01` adds `make docs-install-dev`, which promotes the
validated local site into ignored `app/documentation/site` so maintainers can open BPM with
`make dev` and review `/help/` plus product links before final manual QA is closed.
`BPM090-M13-01` is now closed by maintainer acceptance: many documentation issues were observed,
but fixes are intentionally deferred to the next version while 0.9.0 proceeds to the final quality
milestone.

## Directory Contract

```text
documentation/
├── AGENTS.md
├── PROJECT_SNAPSHOT.md
├── README.md
├── config/
├── src/
│   ├── dita/
│   │   ├── en/
│   │   ├── ru/
│   │   ├── de/
│   │   ├── zh-CN/
│   │   ├── fr/
│   │   └── es-ES/
│   ├── generated/
│   └── shared/
├── assets/
│   ├── theme/
│   └── screenshots/
│       ├── en/
│       ├── ru/
│       ├── de/
│       ├── zh-CN/
│       ├── fr/
│       └── es-ES/
├── fixtures/
├── runbooks/
├── tools/
├── tests/
│   ├── unit/
│   ├── contract/
│   └── browser/
├── build/       # generated and ignored; created by build commands
├── dist/        # generated and ignored; created by packaging commands
├── reports/     # generated and ignored; created by validation commands
└── .cache/      # dependencies/toolchain/cache; ignored and never committed
```

## Ownership Classes

| Path | Class | Mutation rule |
| --- | --- | --- |
| `config/` | Hand-authored build and information-architecture configuration | Review changes; never generated implicitly. |
| `src/dita/en/` | Hand-authored source-locale DITA | English product source; reviewed before localization. |
| `src/dita/{ru,de,zh-CN,fr,es-ES}/` | Hand-authored localized DITA | Human-reviewed peers; no silent English fallback, compact summaries, or unreviewed machine output. |
| `src/shared/` | Hand-authored language-neutral DITA metadata | Keys, subject schemes, conditions, and identifiers only; not hidden English prose. |
| `src/generated/` | Generator-owned DITA facts/skeletons | Regenerate from approved sources; edit only explicit reviewed regions. |
| `assets/theme/` | Hand-authored first-party static portal theme | CSS-only, self-hosted, CSP-friendly, and reviewed with accessibility/security contracts. |
| `assets/screenshots/{locale}/` | Reviewed publishable source assets | Promote deterministic captures only after locale/content/privacy review. |
| `fixtures/` | Hand-authored compact test data | Synthetic, deterministic, versioned, and safe to publish in tests. |
| `runbooks/` | Hand-authored maintainer workflow instructions | Explain how to change documentation safely; not product-guide content and not served under `/help/`. |
| `tools/` | Hand-authored documentation-only tooling | May read BPM public contracts at build time; never imported by `app/`. |
| `tests/` | Hand-authored focused documentation tests | Unit, contract, and browser ownership remains local to this subsystem and follows `tests/suite-boundaries-0.9.0.json`. |
| `build/`, `dist/`, `reports/`, `.cache/` | Generated local/CI state | Never hand-edit, commit, package as source, or include in normal context scans. |

## Source And Artifact Separation

- Reviewed DITA, first-party theme assets, approved screenshot assets, fixtures, configuration,
  runbooks, tools, and tests are source.
- `config/user-guide-map-0.9.0.json` is the machine-readable User Guide coverage map: it groups the
  89 planned user topics by intent and maps all 106 user capabilities to a primary topic path.
- `config/user-guide-coverage-closure-0.9.0.json` is the User Guide release gate: it binds those
  topics to README capabilities, product routes, templates, locale catalogs, API boundaries, and
  browser-smoke evidence.
- `config/firefox-policy-topic-model-0.9.0.json` defines the Firefox Policy Guide reference topic
  model used by schema-grounded topic skeleton generation.
- `config/cis-settings-topic-model-0.9.0.json` defines the CIS Settings Guide reference topic
  model, disclaimer contract, source boundary, and automation/manual-review sections.
- `config/firefox-policy-context-targets-0.9.0.json` assigns Firefox policy families to contextual
  documentation topics, related policies, user tasks, API operations, and validation guidance.
- `config/search-corpus-and-results-0.9.0.json` defines the deterministic static search corpus,
  result schema, facets, exclusions, six-locale boundary, and no-AI/RAG/embeddings/generative-answer contract.
- `config/search-normalization-aliases-0.9.0.json` defines deterministic locale-aware search
  normalization, reviewed aliases, technical identifier preservation, and six-locale query fixtures.
- `config/search-ranking-typo-0.9.0.json` defines deterministic ranking weights, bounded typo
  tolerance, explainable score components, and exact-ID/title/alias/body fixture expectations.
- `config/search-facets-filters-0.9.0.json` defines deterministic local search facets, filter
  composition, per-corpus counts, URL-state preservation, and six-locale empty-result recovery.
- `config/search-quality-performance-0.9.0.json` defines deterministic search-quality fixtures,
  top-result expectations, no-result/adversarial cases, index-size limits, and scan-unit budgets.
- `config/search-integrity-drift-0.9.0.json` defines deterministic search-index drift checks for
  manifest topics, anchors, locale/output metadata, snippets, and source-inventory coverage.
- `tests/suite-boundaries-0.9.0.json` maps DITA, content, manifest, localization, screenshot,
  search, link, API-example, administrator-guide-scope, administrator update, portal-integration, release-gate,
  browser-smoke, debugging-protocol, and toolchain failures to focused documentation suites,
  compact fixtures, and rerun commands.
- `src/dita/{locale}/firefox/` contains authored Firefox Policy Guide concept, task, and reference topics.
- `src/dita/{locale}/cis/` contains authored CIS Settings Guide orientation, baseline-selection,
  preset/layer merge, source-attribution, manual-review, verification, and workflow topics with
  equivalent structure across all six locales.
- `src/dita/{locale}/api/` now contains only the thin API Integration Guide compatibility landing
  topic. The formerly API-owned integration corpus moved to Administrator/DevOps topics in
  `src/dita/{locale}/admin/`, while OpenAPI-to-DITA drift tests continue to protect endpoint
  coverage and examples.
- `src/dita/{locale}/admin/` contains Administrator/DevOps Guide topics for current source deployment
  on Linux and Windows 10/11 through WSL, DevOps operation, source-based updates, and current API
  integration ownership; future M12 tasks will expand reusable examples, troubleshooting,
  production-readiness boundary, and final parity review content.
- `src/generated/firefox/` contains the reproducible Firefox policy DITA skeletons, generated map,
  schema-valid examples, channel-differences metadata, provenance review, and skeleton index for every supported policy ID.
- `src/generated/cis/` contains reproducible CIS recommendation skeletons, a generated map, and an
  index with mapping tables, layer-checked examples, unresolved provenance-only records, and the
  CIS refresh runbook marker plus accuracy/provenance review artifact.
- `build/` is disposable output. A clean build must recreate it; no source may link to a file only
  because it happens to be present there.
- `manifest.json`, `ui-target-map.json`, and deterministic per-locale search indexes are generated
  artifact files. They are validated and packaged, but their generated copies remain ignored local
  output.
- `dist/` contains deterministic release-candidate archives and checksums produced from source; it
  is ignored and regenerated locally/CI, not committed.
- `reports/` contains disposable diagnostics and browser/audit output.
- `.cache/` and dependency/toolchain/vendor/virtual-environment directories are disposable local
  state and are excluded by `documentation/.gitignore`.
- The release-candidate artifact is produced atomically from reviewed source. The
  `app/documentation/` runtime bridge reads only an installed static documentation artifact.
  `make docs-install-dev` may install a local build into ignored `app/documentation/site` for
  maintainer review through `make dev`; current packages still declare `runtime_ready=false` until
  release extraction policy, localized screenshot review, and final manual QA/defect disposition are
  finished.
- BPM runtime code must not import `documentation.tools`, DITA libraries, Java, build configuration,
  source topics, fixtures, or documentation tests.

## Locale Boundary

Published locale identities are exactly `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. Equivalent
topics, DITA keys, anchors, asset IDs, and source slugs remain locale-independent. Each visible BPM
UI screenshot is stored under its locale directory; reuse across locales requires the explicit
language-neutral exception defined by the ownership and manifest contracts.

## Context Discipline

Start documentation work from `documentation/AGENTS.md`, then `documentation/PROJECT_SNAPSHOT.md`,
this README, the relevant `documentation/runbooks/` file, and the one relevant architecture
decision or backlog task. Read only the affected locale/topic, direct shared resources, fixture/tool,
and focused test. Do not scan `build/`, `dist/`, `reports/`, `.cache/`, dependencies, generated
output, all locale trees, or unrelated BPM modules.

## Deferred From This Scaffold

- `BPM090-M3-05`: keys, subject schemes, and conditions;
- `BPM090-M11-09+`: screenshots, release package extraction, and remaining release gates.

The toolchain can be installed with `make setup-docs-toolchain` and then revalidated without network
access with `make setup-docs-toolchain DOCS_TOOLCHAIN_OFFLINE=1`. Use `make test-docs`,
`make test-docs-contract`, `make test-docs-ui-contract`, `make test-docs-browser`, and
`make test-docs-ui` for focused documentation checks; browser-backed targets require immediate
sandbox escalation. Use
`make docs-snapshot` to refresh `documentation/PROJECT_SNAPSHOT.generated.md`. Use
`make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"` as the first
one-topic source loop; without `DOCS_CHANGED`, it derives changed documentation inputs from git.
Use `make docs-coverage` for isolated documentation-code coverage reports under
`documentation/reports/coverage/`. Use `make docs-release-check` for the documentation release gate;
it runs full DITA validation and the documentation contract suite before `make test-release`
continues into the general BPM release suite.
Use `documentation/fixtures/fixture-catalog-0.9.0.json` to find the smallest synthetic fixture for a
documentation failure domain.
Failed focused checks may retain compact JSON diagnostics under `documentation/reports/diagnostics/`.
Use `make dev` to refresh the ignored runtime copy through `make docs-install-dev` before starting
the app for maintainer review; generated site/package output remains build evidence and release
extraction is still a separate gate. Use `make run` only when you intentionally need to start the
app without refreshing local documentation.

Use `make docs-validate` for a disposable six-locale DITA/link validation build,
`make docs-build` for an atomic local publish to ignored `documentation/build/site`,
`make docs-install-dev` to copy the validated local site into ignored `app/documentation/site`,
`make docs-reproducibility-check` to compare two clean publish trees byte for byte,
`make docs-package` to build the ignored deterministic release-candidate archive, and
`make docs-package-verify` to verify its checksum and integrity manifest. The build wraps DITA-OT
HTML in the same deterministic shell every time and copies the first-party CSS theme into each
locale output, then generates and validates `manifest.json`, `ui-target-map.json`, and six
per-locale search indexes with normalized tokens, reviewed aliases, ranking fixtures, deterministic
facets/filters, quality/performance fixtures, integrity/drift reports, corpus counts, URL-state
fixtures, and localized empty-result recovery. The dev runtime copy is intentionally ignored and
must be regenerated rather than edited by hand.
