# BPM 0.8.5 Refactoring And Optimization Backlog

Date: 2026-06-01

This backlog captures the current refactoring/optimization assessment for BPM 0.8.5. The goal is to reduce fragility, repeated context loading, oversized files, stale artifacts, and test runtime while preserving the current product behavior and coverage confidence.

Shared acceptance rules for these tasks live in `docs/architecture/refactoring-acceptance-rules.md`.

## Current Assessment

- The repository is functionally healthy: the default non-live test suite passed with `583 passed, 53 deselected`.
- The default suite is too slow for routine iteration: `pytest --durations=25 --durations-min=0.05` took `803.15s` test time and `807.50s` wall time.
- The slowest default test is `tests/compliance/test_cis_firefox_mapping_targets.py::test_cis_mapping_targets_validate_against_declared_schema_channels` at `39.77s`.
- Several default route/static contract tests in `tests/test_web_profiles_page.py` each cost `20-30s`.
- The main frontend surface is split across many static files, but still behaves like a global-script monolith loaded by `app/templates/profiles/_page_document.html`.
- The largest project-maintained source hot spots are `app/static/profiles.css`, `app/static/profiles_review.js`, `app/static/profiles_runtime.js`, `app/static/profiles_workspace.js`, `app/static/profiles_wizard_flow.js`, `app/static/profiles_network.js`, `app/static/profiles_extensions.js`, and `app/static/profiles_schema_shell_sections.js`.
- Vendored Monaco assets dominate tracked line count and size. They are expected, but should be treated as generated vendor outputs with reproducibility checks.
- Runtime locale catalogs have strict key parity and currently contain `2,620` keys per locale. They are too large for comfortable review and token-efficient iteration.
- `docs/` contains many dated backlog, audit, runbook, and locale files. Some tests read exact docs paths, so docs cleanup must happen through an indexed migration rather than ad hoc deletion.
- Local ignored artifacts are under control in git, but the working tree contains large ignored state such as `.bpm-test-browsers/`, `docs/screenshots/`, `artifacts/`, `data/`, `.coverage`, and local DB files.
- The obsolete editor compatibility route has been removed; remaining atavism
  candidates include route-time legacy schema normalization and scattered
  legacy schema guards.

## Milestone 1: Baseline, Ownership, And Safety Rails

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M1-01 | Set project metadata and docs anchors for `0.8.5`. | low | Update version surfaces only after the backlog is accepted. |
| BPM085-M1-02 | Add a repo health report command for file sizes, generated/vendor files, ignored artifacts, locale key counts, and test timing. | medium | Prefer a repeatable command over one-off shell archaeology. |
| BPM085-M1-03 | Add `docs/architecture/current-system-map.md` with routes, API, frontend entrypoints, schemas, locales, compliance, and tests. | medium | Reduces repeated context loading for future agents. |
| BPM085-M1-04 | Define refactoring acceptance rules: public behavior stays stable, each split preserves route/API contracts, tests move with ownership. | low | Keeps 0.8.5 focused instead of turning into a rewrite. |

## Milestone 2: Docs And Artifact Cleanup

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M2-01 | Create a docs index with `active`, `runbook`, `audit`, `backlog`, and `archive` status for every file in `docs/`. | medium | Required before moving files because tests reference exact docs. |
| BPM085-M2-02 | Move dated completed audits/backlogs into `docs/archive/2026-q2/` and update tests to validate the index rather than old exact paths. | medium | Keeps historical value without cluttering active context. |
| BPM085-M2-03 | Convert `docs/archive/2026-q2/source_string_inventory_en_2026-05-21.json` into a generated artifact or archive it behind an index entry. | medium | It is useful data but expensive to load accidentally. |
| BPM085-M2-04 | Add `make clean-local-artifacts` for ignored screenshots, coverage, DB files, browser sandboxes, caches, and local upstream downloads. | low | Do not delete automatically; make cleanup explicit. |
| BPM085-M2-05 | Replace docs-as-tests for finished backlog items with a small machine-readable docs manifest. | high | This removes brittle text assertions while preserving documentation contracts. |

## Milestone 3: Frontend Shape And Route Loading

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M3-01 | Replace the long static script chain with route entrypoint manifests for library, guided, all-settings, and JSON routes. | high | The current split still depends on global load order. |
| BPM085-M3-02 | Lazy-load Monaco only where JSON editing is actually needed. | high | Monaco vendor output is large; route loading should make that cost explicit. |
| BPM085-M3-03 | Split `profiles_runtime.js` by responsibilities: locale/theme, library controls, wizard navigation, persistence, JSON editor, beforeunload. | high | This is the main frontend coordination file. |
| BPM085-M3-04 | Split `profiles_review.js` and `profiles_workspace.js` into pure state/serialization helpers plus DOM adapters. | high | Gives tests smaller units and lowers future context cost. |
| BPM085-M3-05 | Split `profiles.css` into route/component layers, with a generated bundle or documented import order. | medium | Avoid CSS becoming the next unstructured monolith. |
| BPM085-M3-06 | Remove the old `advanced` route and helper after an explicit compatibility decision. | medium | Keep only if external links still require it. |

## Milestone 4: Backend And Schema Boundaries

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M4-01 | Extract profile page context building from `app/web/profiles.py` into dedicated context/catalog services. | medium | Routes should fetch profile data and choose templates, not build every catalog. |
| BPM085-M4-02 | Move legacy schema normalization out of `/profiles` request handling into a migration/backfill command. | medium | Route-time mutation is surprising and keeps old schema history alive. |
| BPM085-M4-03 | Consolidate route URL builders and focus-target semantics into a shared tested module. | high | Python and JS currently need to agree by convention. |
| BPM085-M4-04 | Generate schema channel constants from the bundled schema inventory, or centralize all schema version strings behind one service. | medium | Reduces update churn for future Firefox releases. |
| BPM085-M4-05 | Audit `ProfileService` and profile API boundaries for smaller command/query helpers. | medium | Keep behavior, reduce broad service methods and repeated setup in tests. |

## Milestone 5: Locale Catalog Strategy

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M5-01 | Add a locale inventory command that reports key counts, placeholder parity, string length, unchanged source strings, and ownership status. | medium | Makes locale health visible without loading every catalog manually. |
| BPM085-M5-02 | Split locale source into namespaces such as `common`, `library`, `wizard`, `settings`, `json`, `policy-labels`, then build runtime `app/i18n/{locale}.json`. | high | Keeps runtime contract while making reviews smaller. |
| BPM085-M5-03 | Move large policy/control labels into generated locale segments tied to schema/catalog metadata. | high | Prevents policy catalog growth from bloating every UI copy review. |
| BPM085-M5-04 | Replace long visible-English allowlists and terminology checks with data files plus focused tests. | medium | Keeps QA but reduces test/source noise. |
| BPM085-M5-05 | Review non-English catalog quality after the split, especially machine-like phrases in generated long-tail keys. | high | Do not optimize structure while freezing bad copy. |

## Milestone 6: Test Platform And CI Speed

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M6-01 | Introduce test markers: `unit`, `api`, `contract`, `docs_contract`, `ui_contract`, `slow`, `browser_ui`, `firefox_live`, `firefox_live_amo`. | medium | The default marker split is too coarse. |
| BPM085-M6-02 | Create `make test-fast`, `make test-contract`, `make test-ui`, `make test-live`, and `make test-release`. | low | Makes the intended testing layers obvious. |
| BPM085-M6-03 | Split `tests/test_web_profiles_page.py` by route or concern and cache repeated rendered pages/clients where safe. | high | This file is both large and slow. |
| BPM085-M6-04 | Optimize CIS target validation by caching schemas/compiled validators across mappings. | medium | The current test validates many small documents through repeated schema loads. |
| BPM085-M6-05 | Move static source string assertions into small helper-driven contract tests or generated snapshots. | medium | Preserve intent while lowering repetition. |
| BPM085-M6-06 | Split CI into mandatory fast checks, coverage/contract checks, browser UI checks, and scheduled/manual live Firefox checks. | medium | Current CI runs one expensive coverage gate after lint/type checks. |
| BPM085-M6-07 | Evaluate `pytest-xdist` only after DB/session isolation and marker cleanup are stable. | high | Parallelism should not hide shared-state bugs. |

## Milestone 7: Vendor, Playbooks, And Reproducibility

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M7-01 | Add a frontend lockfile and checksum verification for vendored JS/CSS outputs. | medium | `package.json` pins versions, but reproducibility should be machine-checkable. |
| BPM085-M7-02 | Make Monaco/vendor rebuild fully scripted with `npm ci`, build, license verification, and size diff reporting. | medium | Avoid manual vendor drift. |
| BPM085-M7-02a | Refresh vendored `js-yaml` to patched `4.2.0` and verify YAML import compatibility. | medium | Addresses the moderate prototype-pollution advisory without using `npm audit fix --force`. |
| BPM085-M7-03 | Replace scattered runbook commands with Make targets and short docs that point to those targets. | medium | Playbooks should be executable where possible. |
| BPM085-M7-04 | Add local browser sandbox lifecycle docs and cleanup checks for `.bpm-test-browsers/`. | low | The sandbox is large but correctly ignored. |
| BPM085-M7-05 | Add a release-readiness checklist for 0.8.5 that runs only the right layers for code, docs, locales, schemas, and live Firefox. | medium | Prevents "run everything always" from becoming the only safe path. |

## Milestone 8: Xdist Isolation And Parallel Test Pilot

| ID | Task | Minimal reasoning | Notes |
|---|---|---:|---|
| BPM085-M8-01 | Audit `pytest-xdist` isolation blockers across DB/session, FastAPI app overrides, process-local caches, temporary files, ports, browser profiles, and artifacts. | high | Parallelism should start from a concrete risk map, not from `-n auto` optimism. |
| BPM085-M8-02 | Add an xdist-safe DB/session harness for pytest, including per-test or per-worker `BPM_DATABASE_URL`, cleanup contracts, and proof that workers never touch `./data/bpm.db`. | high | `app.db` creates engine/session state at import time, so DB isolation must be explicit before any pilot. |
| BPM085-M8-03 | Isolate FastAPI app/client state and process-local caches with fresh app factories, dependency-override cleanup, and a cache-reset registry for settings, schemas, validators, and locale catalogs. | high | Shared `app.dependency_overrides` and manual cache clearing are the main order-dependence risks inside each worker. |
| BPM085-M8-04 | Add `pytest-xdist` as an opt-in dev dependency plus local/CI pilot targets for pure `unit`/tool tests only, excluding `api`, `contract`, `docs_contract`, `ui_contract`, `slow`, browser, and live Firefox markers. | medium | Proves value on the safest layer before touching route, DB-heavy, docs, UI, or browser suites. |
| BPM085-M8-05 | Decide whether to keep the xdist pilot opt-in for BPM 0.8.5, promote a narrow mandatory CI layer, or defer adoption after BPM 0.8.5. | high | Decision: keep it opt-in for 0.8.5; the measured subset speedup does not yet shorten the mandatory CI critical path. |

## Suggested Execution Order

1. Test telemetry and marker taxonomy.
2. Docs index and active/archive split.
3. Locale inventory and namespace build plan.
4. Frontend route entrypoint manifests.
5. Backend context/schema cleanup.
6. Test file split and slow-test optimization.
7. Vendor/playbook reproducibility.
8. Xdist isolation audit and pure-unit parallel pilot.
