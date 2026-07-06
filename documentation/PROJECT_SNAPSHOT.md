# BPM Product Documentation Workspace Snapshot

Updated: 2026-07-06
Target BPM version: `0.9.0`
Current completed backlog item: `BPM090-M14-08`
Next backlog item: `BPM090-M14-09`

## Current State

The isolated documentation workspace, pinned toolchain, localized guide-map matrix, key maps,
subject scheme, conditional metadata contract, reproducible static publishing pipeline,
deterministic release-candidate packaging policy, accessible static portal shell/theme, generated
manifest/target-map contracts, maintainer authoring runbooks, case-oriented User Guide map,
localized User Guide corpus, DITA localization workflow, Firefox/CIS topic models, Firefox/CIS generated skeletons, Firefox examples/channel differences, Firefox Policy/CIS/API six-locale parity gates, CIS mapping/source-attribution/manual-review/workflow topics, API integration audience/pattern/profile-lifecycle/import-export/validation-gate/health-handshake/scenario/reusable-example topics plus OpenAPI drift gates, six-locale Firefox Policy/CIS/API topics, an Administrator/DevOps Guide map/key/root contract for source deployment, operations, updates, integrations, production/HA/reverse-proxy boundaries, validation fixtures, and final six-locale admin localization review, an API/integration re-home audit from API/User Guide content into Administrator/DevOps ownership, a manifest-validated locale-aware `/help/` runtime bridge, a localized BPM header documentation link, five manifest-backed contextual help links, manifest-backed policy/CIS/validation/import-export deep help icons, localized unavailable/stale/incomplete documentation states, focused `/help/` accessibility/responsive/CSP/theme integration contracts, deterministic six-locale static search indexes/UI with reviewed normalization/aliases/ranking/facets/filters/quality/integrity gates and non-AI boundary copy, isolated documentation test suite boundaries, focused documentation make targets, a documentation-only source fast loop, isolated documentation coverage reporting, a compact deterministic fixture catalog, ignored failure diagnostics, a generated subsystem snapshot, a release-blocking documentation gate wired into `make test-release`, a browser-backed documentation portal smoke for BPM links, an ignored dev-site install target for maintainer review through `make dev`, maintainer-accepted manual QA with known issues deferred to the next version, a final content coverage audit with explicit release blockers, a refreshed implemented-product README, and a documentation-only debugging protocol exist.
Generated output and the dev-installed site are ignored; `make docs-install-dev` installs the current local build under `app/documentation/site`, while release package extraction remains a separate gate. Full application/documentation-owned coverage, non-browser documentation release, and browser smoke gates are green.

Implemented:

- exact DITA locale source directories for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`;
- matching localized screenshot source directories;
- hand-authored `config/`, `src/shared/`, `fixtures/`, `tools/`, focused tests, and committed
  generated Firefox/CIS skeletons under `src/generated/{firefox,cis}/`;
- documentation test group directories `tests/unit/`, `tests/contract/`, and `tests/browser/` plus
  a suite-boundary contract mapping DITA, content, manifest, localization, screenshot, search, link, API-example, API-rehome-audit, administrator-guide-scope, administrator-devops-operational-boundaries, administrator-linux-deployment, administrator-windows-wsl-deployment, administrator-update-from-source, administrator-production-readiness-boundaries, administrator-guide-validation, portal-integration, release-gate, content-coverage-audit, browser-smoke, debugging-protocol, and toolchain checks to focused fixtures and reruns;
- local ignores for build/reports/cache/toolchain/dependency/generated output;
- maintained architecture contracts and inventories under `docs/architecture/`;
- general `docs_contract` tests covering those decisions and the scaffold.
- checksum-locked DITA-OT 4.4 and Eclipse Temurin JRE 21.0.11+10 for Linux x86_64;
- exact documentation-only Python test pins, third-party notices, and an ignored wheel/venv cache;
- a fail-closed repository-local bootstrap with safe extraction, version checks, and DITA smoke;
- networked and offline `make setup-docs-toolchain` entry points plus focused bootstrap unit tests.
- five independently buildable guide maps and one stable-order portal aggregate for every locale;
- locale/map identity, aggregate-reference, DITA-only source, and parity contract tests.
- locale key maps with stable `guide.*` identities and a shared DITA 1.3 subject scheme;
- fixed audience/platform/version/locale/channel/CIS vocabularies and inventory-backed dynamic
  policy, CIS-recommendation, and API-operation validation;
- orthogonal locale and Firefox Release/ESR DITAVAL filters plus a compact no-copy fixture;
- focused metadata validator and contracts that reject unknown fixed and dynamic values.
- offline six-locale DITA validation and atomic local HTML publication;
- fail-closed source key/link/fragment and generated HTML link/fragment/path-leak validation;
- byte-equivalence verification across two clean publish trees with explicit deterministic inputs.
- ignored deterministic package output under `documentation/dist/` with normalized tar.gz metadata,
  checksum verification, artifact-integrity manifest, license notices, source-mutation detection,
  stale-output deletion on failed package builds, dev-install separation, and `runtime_ready=false` blockers.
- deterministic post-build portal shell with skip link, landmarks, breadcrumbs, guide/locale
  switchers, version/status context, exact locale `html lang`, CSP-friendly static HTML, accessible
  local search UI, and first-party responsive/dark/light/forced-colors/reduced-motion/print CSS covering code, tables, and notes.
- schema-valid generated `manifest.json`/`ui-target-map.json`, 256 current topics, stable anchors,
  policy/CIS/API/capability/topic targets, hashes, and six reproducible per-locale search indexes with normalized tokens, aliases, ranking fixtures, deterministic facets, quality/performance fixtures, integrity/drift reports, filter counts, URL-state fixtures, and localized empty-result recovery.
- maintainer runbooks for one-topic authoring, DITA localization workflow, screenshots, Firefox/CIS/API inventory refresh, Firefox schema and CIS benchmark/mapping drift gates, link/manifest changes, review, and publishing checks.
- case-oriented User Guide coverage map grouping all 89 planned user topics and all 106 inventoried
  user capabilities into eight user-intent sections, with matching localized DITA map section
  headings for all six locales.
- closed User Guide coverage gate against README capabilities, routes, templates, locale catalogs, API boundary behavior, and browser smoke-flow evidence.
- Firefox Policy Guide DITA reference topic model, shared template, and locale parity contract covering purpose, BPM location, value shape, channel support, examples, validation, caveats, interactions, CIS links, provenance, and full-content authored topic peers.
- CIS Settings Guide DITA reference topic model, shared template, six-locale orientation/selection/preset-merge/source-attribution/manual-review/verification/workflow topics, locale parity contract, deterministic workflow fixtures, CIS refresh drift gate, and generated skeletons for 53 publishable recommendations plus two provenance-only records, with mapping tables/examples checked against current CIS layer JSON, source-boundary/non-certification claims, refresh-runbook metadata, and CIS provenance-review artifact.
- six-locale Administrator/DevOps API integration topics, migrated from the former API Integration Guide corpus, cover audience, supported patterns, conventions, limitations, profile lifecycle, Firefox import/export, validation gates, health/readiness handshakes, control-product scenarios, reusable curl/Python examples, locale parity, and OpenAPI-to-DITA drift gates; the API Integration Guide now remains only as a thin compatibility landing page.
- generated Firefox Policy skeletons for all 120 policy IDs, 232 schema-valid examples, channel/provenance metadata, language-neutral schema-fact preservation, and six-locale policy/channel/complex-family topics.
- six-locale DITA core-concept topics for profile lifecycle, editor-surface choice, Firefox schema
  channels and validation, policies and managed preferences, and starter presets/CIS layers, all
  keyed from localized User Guide maps.
- six-locale DITA Profile Library management topics covering create/open/find/filter/sort/refresh,
  row status, duplicate, archive, restore, permanent delete, archived behavior, and troubleshooting.
- six-locale DITA import/export topics and fixtures distinguishing Firefox `policies.json`
  boundary documents from BPM's normalized model, with JSON/multipart import and export options.
- six-locale DITA Profile Comparison topics covering Library handoff, Profile A/B selection,
  policy/preference rows, and equal/changed/missing states.
- six-locale DITA Guided, All Settings, JSON, schema-validation, cross-cutting, troubleshooting, and
  parity contracts covering visual/raw editing, Firefox AI-policy settings, Release/ESR, locale/theme,
  tabs, unsaved changes, keyboard/focus/status, documentation search non-AI boundaries, destructive actions, malformed JSON, schema mismatch, and API failures.
- locale-root DITA output link normalization plus `app/documentation/` serving an installed static documentation artifact under `/help/` with active-locale selection, manifest/target-map version and digest validation, topic/alias redirects, manifest-resolved BPM header, five surface contextual help URLs, policy/CIS/validation/import-export deep help icons, localized missing/stale/incompatible/incomplete/not-found status pages, route-specific headers, MIME allowlists, 503/404 safe states, unsupported-locale fallback, path traversal rejection, accessibility/responsive/CSP/theme integration contracts for served docs and status pages, preserved FastAPI `/docs`/`/openapi.json`, and deterministic per-locale DITA search corpus/normalization/ranking/facet generation.
- `administrator-guide` is the fifth guide family with stable `admin/` root, six-locale map/key entries, manifest/search registration, and ownership for source deployment, DevOps operation, updates, API integration, and production-readiness boundaries; six-locale Linux/WSL deployment, DevOps operations, update-from-source evidence/migrations/docs rebuild/rollback-stop runbooks, and migrated API integration corpus cover runtime variables, health/readiness probes, UI smoke, WSL troubleshooting, DevOps configuration/storage/logs/backups/CORS/security limits, revision/dependency refresh, documentation build checks, backup/export evidence, profile lifecycle, Firefox import/export, validation gates, reusable DevOps environment templates/curl/Python/multipart examples, OpenAPI drift, DevOps integration runbooks for external control products, pull/list/read, validate-before-apply, import-review-export, compliance handoff, health-gated startup, failure-recovery/audit evidence, failed startup/probe/schema/API/import/export/storage/WSL/dependency/documentation-portal diagnostics, single-node source readiness, network exposure/proxy-readiness questions, monitoring/backup/update windows, HA/deferred production boundary records, deferred production/installer/native-service boundaries, compact validation fixtures for stale command/API/env/path/locale/deferred-claim drift, and final no-fallback/no-short-summary locale parity review.
- `api-integration-rehome-audit-0.9.0.{json,md}` records completed migration of all 13 API topics,
  7 API-adjacent User Guide topics, fixtures, tests, current `admin-*` IDs, and compatibility landing/cross-link rules.
- `product-documentation-content-coverage-audit-0.9.0.{json,md}` records the final M14-07 audit: product/admin/Firefox/CIS/API/locale/manifest/search/portal domains are covered; localized screenshot capture/review remains an explicit release blocker.
- `BPM090-M13-01` is closed by maintainer manual review acceptance: many documentation UX/content issues remain known, but their correction is deferred to the next product version rather than blocking the 0.9.0 final quality milestone.
Not implemented yet: localization screenshot capture/review and release package extraction policy.

## Compact Tree

```text
documentation/
├── {AGENTS.md,PROJECT_SNAPSHOT.md,README.md,config/,fixtures/,runbooks/,tools/,tests/}
├── src/dita/{en,ru,de,zh-CN,fr,es-ES}/maps/{five-guide-maps,portal,keys}.ditamap
├── src/dita/{en,ru,de,zh-CN,fr,es-ES}/{user/,firefox/,cis/,api/,admin/}
├── src/generated/{firefox/,cis/} and src/shared/{metadata-subject-scheme.ditamap,filters/,templates/}
└── assets/{theme/,screenshots/{en,ru,de,zh-CN,fr,es-ES}/}
```

Ignored and normally unread: `build/`, `dist/`, `reports/`, `.cache/`, `.toolchain/`, local virtual environments, dependency/vendor folders, test caches, and generated DITA below `src/generated/` except committed Firefox/CIS skeletons.

## Stable Product Scope

Guide families:

1. case-oriented BPM User Guide covering all user-visible product capabilities;
2. Firefox Policy Guide covering supported Release/ESR policy and managed-preference behavior;
3. CIS Settings Guide covering BPM mappings/workflows without copying restricted source prose or
   claiming certification/compliance;
4. API Integration Guide thin compatibility landing for the old guide entry point;
5. Administrator/DevOps Guide for source deployment, operations, updates, current-API integration
   ownership, and production-readiness boundaries.

Global constraints:

- all publishable product content originates in DITA 1.3 topics;
- all five guides ship in all six locales with locale-specific UI screenshots where illustrated;
- deterministic static search is local/offline and contains no AI/RAG/embeddings/generative answer;
- distribution-specific installer variants are deferred until distribution formats exist;
- `/help/` serves an installed documentation artifact; FastAPI `/docs` remains OpenAPI UI;
- build/source/tool dependencies never become BPM runtime imports.

## Maintained Entry Points

| Need | Entry point |
| --- | --- |
| Backlog and next approved task | `docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md` |
| Ownership/tree/debug isolation | `docs/architecture/product-documentation-ownership-boundary-0.9.0.md` |
| DITA/Java/toolchain decision | `docs/architecture/dita-publishing-toolchain-decision-0.9.0.md` |
| Topic/key/anchor/URL identity | `docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md` |
| Manifest and UI targets | `docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md` |
| Source reuse/licenses | `docs/architecture/product-documentation-provenance-review-0.9.0.md` |
| Accessibility/security/CSP | `docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md` |
| Final content coverage audit | `docs/architecture/product-documentation-content-coverage-audit-0.9.0.json`, `docs/architecture/product-documentation-content-coverage-audit-0.9.0.md` |
| User capability coverage | `docs/architecture/product-user-capability-inventory-0.9.0.md` |
| User Guide case map | `documentation/config/user-guide-map-0.9.0.json` |
| Search corpus/result contract | `documentation/config/search-corpus-and-results-0.9.0.json` |
| Search facets/filters contract | `documentation/config/search-facets-filters-0.9.0.json` |
| Search quality/integrity contracts | `documentation/config/search-quality-performance-0.9.0.json`, `documentation/config/search-integrity-drift-0.9.0.json` |
| Documentation coverage policy | `documentation/config/coverage-policy-0.9.0.json` |
| Documentation diagnostics policy | `documentation/config/diagnostics-policy-0.9.0.json` |
| Documentation fixture catalog | `documentation/fixtures/fixture-catalog-0.9.0.json` |
| Administrator Guide validation fixture | `documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json` |
| Generated subsystem snapshot | `documentation/PROJECT_SNAPSHOT.generated.md` |
| Documentation test suite boundaries | `documentation/tests/suite-boundaries-0.9.0.json` |
| Documentation release gate | `documentation/tests/contract/test_documentation_release_gate.py` |
| Documentation browser smoke | `documentation/tests/browser/test_documentation_portal_browser_smoke.py` |
| Documentation debugging protocol | `documentation/runbooks/debugging-protocol.md` |
| Administrator Guide scope contract | `documentation/tests/contract/test_administrator_guide_scope.py` |
| Administrator operations/source deployment | `documentation/tests/contract/test_administrator_devops_operational_boundaries.py`, `documentation/tests/contract/test_administrator_linux_deployment_topics.py`, `documentation/tests/contract/test_administrator_windows_wsl_deployment_topics.py`, `documentation/tests/contract/test_administrator_update_from_source_topics.py`, `documentation/tests/contract/test_administrator_troubleshooting_diagnostics_topics.py`, `documentation/tests/contract/test_administrator_production_readiness_boundaries.py`, `documentation/tests/contract/test_administrator_guide_validation_fixtures.py` |
| Administrator API integration | `documentation/tests/contract/test_api_integration_topics.py`, `documentation/tests/contract/test_api_locale_parity.py`, `documentation/tests/contract/test_api_openapi_drift.py`, `documentation/tests/contract/test_api_rehome_audit.py`, `documentation/tests/contract/test_api_devops_integration_runbooks.py` |
| Firefox policy coverage | `docs/architecture/firefox-policy-documentation-inventory-0.9.0.json` |
| CIS coverage | `docs/architecture/cis-documentation-inventory-0.9.0.json` |
| API coverage | `docs/architecture/api-documentation-inventory-0.9.0.md` |
| API re-home audit / authoring workflows | `docs/architecture/api-integration-rehome-audit-0.9.0.json`, `docs/architecture/api-integration-rehome-audit-0.9.0.md`, `documentation/runbooks/README.md` |
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
./.venv/bin/pytest -q -m docs_contract tests/<one_relevant_contract>.py
./.venv/bin/pytest -q -m docs_contract
./.venv/bin/ruff check <changed_python_files>
git diff --check -- <changed_files>
```

`make setup-docs-toolchain` is networked unless `DOCS_TOOLCHAIN_OFFLINE=1`; build/package commands
are offline. `make test-docs*` runs focused documentation tests. `make docs-fast-check` validates
changed inputs without DITA-OT or unrelated BPM code. `make docs-coverage` writes terminal/XML/HTML
reports under `documentation/reports/coverage/` and fails below 100% for included policy scope.
`make docs-release-check` runs full six-locale DITA validation and documentation contracts before
`make test-release` continues into the general release suite. `make test-docs-browser` and
`make test-docs-ui` launch Chromium/Selenium and require immediate sandbox escalation. `make docs-install-dev` promotes the current local build into ignored `app/documentation/site` for `/help/` review through `make dev`; it is not release extraction evidence. No `make docs-screenshots-check` target exists yet.
