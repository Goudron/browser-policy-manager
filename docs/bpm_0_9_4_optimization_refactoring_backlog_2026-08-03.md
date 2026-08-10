# BPM 0.9.4 Optimization, Refactoring, And Release Hardening Backlog

Date: 2026-08-03

Target BPM version: `0.9.4`

Epic ID: `BPM094`

Release risk: high. The intended product behavior is unchanged, but the work crosses database
lifecycle and migrations, backend query semantics, server-rendered profile routes, frontend module
loading, documentation build tooling, test ownership, browser automation, packaging, and mandatory
CI gates. A missed compatibility boundary could corrupt an upgraded database, remove an externally
reachable surface, or let a refactor pass brittle source-text tests while changing runtime behavior.

This backlog takes BPM from the current `0.9.3` implementation to a release-ready `0.9.4` through
measured optimization and maintainability work. It preserves the current feature set, public API,
rendered UI, user-visible copy, locale behavior, and Firefox policy output, except for the approved
removal of the user-facing YAML policy-editor mode in M3-04. Product documentation
is an active `0.9.4` release surface: it must be completed for the delivered behavior and receive
the approved PDF presentation, navigation, accessibility, and localization corrections before the
final quality milestone. Maintained technical documentation may change where architecture, test
ownership, runbooks, or release gates must accurately describe the refactored repository.

Model assignments use the current
[GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model.md), rechecked on
2026-08-03: Luna for deterministic high-volume work, Terra as the normal engineering default, and
Sol only where cross-system ambiguity or data/release risk makes Terra unsafe. Reasoning effort is
selected independently.

## Scope Summary

- Move all active BPM version surfaces, package metadata, editable-install metadata, tests, and
  changelog state from `0.9.3` to `0.9.4`. README remains version-neutral.
- Freeze black-box product behavior before refactoring: OpenAPI, API payloads/status codes, profile
  CRUD and export, rendered DOM semantics, locale output, security headers, and Firefox
  `policies.json`. Documentation contracts are characterized first, then updated only through M11
  from verified delivered behavior and the documentation-update runbook.
- Replace the synchronous SQLite session hidden behind an async interface with an application-owned
  native async database runtime initialized once in lifespan.
- Make Alembic the only database schema/data-upgrade owner and prove supported upgrades from prior
  released BPM databases without request-time or startup-time silent migration.
- Remove duplicate, unreachable, historical, and confirmed legacy code and tests; preserve negative
  security boundaries and supported upgrade contracts.
- Optimize profile queries, validation, catalog construction, route rendering, response size, and
  immutable asset delivery without changing API or UI behavior.
- Replace the global ordered profile-script graph with explicit ES-module ownership and route
  bundles built by the existing esbuild toolchain.
- Split oversized documentation tooling into bounded modules while keeping command names, generated
  content, reproducibility, installation, and served documentation behavior exact.
- Give every test one primary execution layer, remove implementation-history assertions, consolidate
  repeated route and Node harnesses, and use measured parallelism only where isolation is proven.
- Automate Chromium and Firefox validation, including a persisted complex BPM profile whose exact
  nested policy document is exported, installed, and observed in a real Firefox runtime.
- Add real PostgreSQL integration coverage, dependency/security auditing, base/optional package
  install smoke, checksum-pinned browser provisioning, 100% declared-surface coverage, and layered
  mandatory CI.
- Reduce future context and token cost through executable architecture contracts, smaller owned
  modules, generated inventories, reusable test harnesses, and current bounded system snapshots.

## Current-State Assessment

### Repository and architecture

- The maintained application contains about 18,700 Python lines. Product tests contain about 46,700
  lines, documentation tests about 31,500 lines, product-owned profile JavaScript about 25,900 lines,
  and documentation tooling about 16,400 Python lines.
- `app/db.py` turns `sqlite+aiosqlite` into a synchronous SQLite engine and exposes it through an
  `AsyncSessionAdapter`. Synchronous SQLAlchemy calls therefore run inside async request handlers.
- `get_session()` calls `init_db()` for each DB-backed request. On SQLite that performs legacy table
  inspection/DDL and `create_all`, even though application startup already initializes the database.
- Module-import settings, engine, session factory, and default app globals force tests to configure a
  worker database before application imports and to dispose shared state repeatedly.
- Startup profile schema normalization duplicates the latest Alembic channel migration. The release
  path therefore has competing owners for legacy data mutation.
- `ProfileService.list()` loads all candidate rows when name or validation-state filtering is used,
  filters and slices them in Python, and can validate a matching profile twice. API list, count, and
  stats calls repeat overlapping work.
- The visible documentation assistant intentionally ships a training notice, while a much larger
  model/RAG/retrieval implementation and tests are not wired into the default release assistant.
  Heavy `numpy`, `onnxruntime`, and `tokenizers` dependencies remain in the base install and occupy
  about 112 MiB in the current environment.
- Confirmed consolidation/removal candidates include the duplicate `app/core/validation.py`, the
  unused YAML serialization helper, the `app/schemas/init.py` compatibility re-export, and the
  best-effort raw-schema `SchemaManager`/`tools/update_schemas.py` path whose guessed upstream raw
  schema no longer exists for current Mozilla releases.
- `documentation/tools/build_docs.py` is 5,961 lines. Ruff reports 43 application/documentation
  functions above McCabe complexity 10; `_validate_search_index_semantics` is complexity 90.

### Profile routes and frontend

- `build_profiles_page_context()` rebuilds wizard settings, preferences, schema shell, starter,
  all-settings, locale, and documentation-link catalogs for every route, including routes that do
  not consume most of them.
- A same-machine, in-memory-DB audit measured the following single-request baseline:

| Route | Wall time | Response bytes |
| --- | ---: | ---: |
| `/profiles` | 5.639 s | 228,569 |
| `/profiles/compare` | 5.350 s | 302,780 |
| `/profiles/new` | 6.153 s | 1,311,354 |
| `/profiles/{id}/edit` | 5.638 s | 1,311,875 |
| `/profiles/{id}/settings` | 5.792 s | 1,360,232 |
| `/profiles/{id}/json` | 5.003 s | 1,125,399 |

- The profile frontend exposes roughly 43 `window.BPMProfiles*` globals. Editor routes load a long
  ordered core script list even when a route does not use every module. Pure state, serialization,
  DOM access, and coordination are often coupled by large callback/configuration objects.
- The repository already uses esbuild for the Monaco vendor bundle, so an additional bundler is not
  required. Current JS behavioral tests frequently start `node -e` from Python and recreate similar
  fake-window/fake-DOM harnesses.
- Generated `profiles.css` is 7,590 lines; its largest maintained source layer is itself a 4,838-line
  editor/wizard stylesheet.

### Test and CI baseline

- The product contour collects 1,399 tests. The default non-browser/non-live run completed with
  `1359 passed, 40 deselected, 1 warning` in `1071.13s` (`17:51`).
- The 40 default exclusions are 18 Chromium tests and 22 Firefox-live tests. Neither contour is a
  mandatory job in the main CI workflow.
- The isolated documentation contour collects 1,107 tests: 59 unit, 1,036 contract, and 12 browser.
  The unit/contract command passed in about 27 seconds, but the main CI workflow does not invoke it.
- Product marker counts overlap by design and 577 tests have none of the current layer-like markers.
  `tests/marker_policy.py` assigns markers through manually maintained filename lists. `slow`, `api`,
  `docs_contract`, and `ui_contract` mix execution layer, domain, and duration.
- The slowest product tests repeatedly render several large profile routes and scan their HTML.
  Individual contract cases take 15-25 seconds. Several obsolete schema-manager failure tests spend
  six seconds in real retry backoff.
- Many tests assert completed backlog IDs, historical status prose, exact implementation strings, or
  old ownership decisions instead of present behavior. At least 169 product/documentation test files
  mention backlog/milestone/completion artifacts and require classification, not blanket retention.
- The current local coverage artifact reports 100% application line and branch coverage, but CI
  allows regression to 85%. Documentation coverage claims 100% only for
  `documentation/tools/validate_metadata.py`, not the broader maintained documentation tooling.
- The pure-unit xdist workflow is manual and uses two workers. Its earlier decision was based on a
  much smaller suite and must be remeasured after classification and isolation cleanup.
- `.pre-commit-config.yaml` pins substantially older Ruff, Black, and Mypy releases than the project
  dev toolchain and runs the broad default pytest contour for Python changes.

### Firefox live, dependencies, and release engineering

- Firefox activation and behavior tests start separate browsers for the same ten policies. The AMO
  canary similarly starts one browser to inspect policy activation and another to inspect install.
- The live fixture writes a document rendered directly from a flags dictionary. It does not persist
  a BPM profile through the application and export that saved profile before Firefox installation.
- Existing complex policies include Proxy, Preferences, Certificates, and ExtensionSettings, but no
  one test proves the full BPM profile -> persistence -> exact export -> installed file -> runtime
  behavior chain.
- Browser setup downloads floating `firefox-latest` or `firefox-esr-latest` binaries without a
  checksum, shares one install root, and tests only `release` plus one rolling `esr`, not the three
  BPM schema channels `release-153`, `esr-153.0`, and `esr-140.13`.
- The setup script pins geckodriver `0.36.0`; the official compatibility table currently lists
  `0.37.1`. Currency and compatibility must be rechecked during execution rather than updated
  blindly.
- `npm audit` reported zero known vulnerabilities on 2026-08-03. A Python dependency audit is not
  installed or enforced. `pip list --outdated` and `npm outdated` both reported available direct or
  transitive updates, including core, toolchain, Selenium, js-yaml, and Monaco packages.
- PostgreSQL dependencies are published as an optional extra, but the test suite only mocks the
  non-SQLite engine constructor; no real PostgreSQL service exercises migrations or CRUD.
- CI has lint/typecheck and one coverage job. It omits documentation release checks, JS tests,
  Chromium, PostgreSQL, package-build/install smoke, dependency auditing, and scheduled deterministic
  Firefox live validation.

## Approved Decisions

The maintainer approved these boundaries on 2026-08-03:

1. Technical repository documentation may change: runbooks, architecture maps, Codex/subsystem
   snapshots, backlog/index, and changelog. Published product documentation is also an approved
   `0.9.4` release surface: M11 updates it only for verified delivered behavior, documentation
   completeness, six-locale editorial quality, and the explicitly approved PDF usability defects.
   README remains version-neutral and may change only for durable current-state product facts.
2. Alembic becomes the only database schema/data-upgrade owner. Supported prior releases retain a
   tested upgrade path; request-time and startup-time silent migration are removed.
3. Unshipped AI/RAG work is retained but isolated as incubation/optional installation. Heavy AI
   dependencies leave the base runtime, and the visible release training-notice behavior remains.
4. The existing PostgreSQL optional extra is retained and receives a real integration CI job.
5. Performance budgets, Python/npm audits, checksum-pinned Firefox provisioning, package install
   smoke, migration/backup fixtures, and a zero-warning policy are mandatory `0.9.4` release gates.
6. The documentation freeze is lifted for this non-final pre-release iteration. M11 must add
   localized figure captions and numbering, semantic UI-element formatting, emphasized note/warning
   labels, PDF title-page page counts, linked/page-numbered contents, and real explanations for
   discovered placeholders such as locale-language selection.

## Success Budgets And Quality Floors

M2 records a reproducible machine/environment manifest and freezes the exact benchmark procedure.
The initial budgets below may be tightened by a task but may not be loosened without a separately
approved backlog change.

| Area | Required floor or ceiling |
| --- | --- |
| Product behavior | Existing public routes, methods, status codes, OpenAPI, JSON shapes, profile semantics, Firefox exports, rendered UI meaning, keyboard/accessibility behavior, locales, and CSP/security headers remain equivalent. Documentation output may change only through the approved M11 completeness and PDF-quality work, and must describe verified delivered behavior. |
| Database lifecycle | Native async sessions for SQLite and PostgreSQL; no synchronous session adapter in request handlers; no schema inspection, `create_all`, migration, or legacy normalization per request; initialization occurs once per app lifespan. |
| Upgrade safety | Every supported released database fixture upgrades to Alembic head with row counts, profile flags, revisions, lifecycle state, and names preserved; an interrupted/failed upgrade never presents partial success. |
| Profile route latency | After one warm-up, the median of three same-fixture local requests is at most 1.0 second per audited profile route and no route is slower than its recorded `0.9.3` baseline. |
| Profile route size | Library and compare do not grow; every route currently above 1 MiB is reduced by at least 30%, with route-irrelevant catalogs and assets absent. |
| Profile query work | Name filtering and pagination execute in SQL; each returned/counted profile is schema-validated at most once per logical list/stats operation; list/count/stats cannot issue redundant full-table scans for one response. |
| Default product tests | The same-machine serial non-browser/non-live contour completes in at most 8 minutes with no lost behavioral assertions and zero warnings. |
| Fast feedback | The mandatory local/CI fast layer completes in at most 90 seconds on the recorded reference runner; documentation unit/contract time does not regress above 60 seconds. |
| CI critical path | Excluding runner queue time and separately scheduled live Firefox, mandatory PR jobs reach a result within 12 minutes on the selected reference runners. |
| Coverage | 100% line and branch coverage for every declared maintained Python surface; no reduction to 85%, no unowned documentation-tooling gap, and explicit JS coverage for extracted pure modules. |
| Frontend ownership | Every profile route has an explicit entry module and dependency graph; owned runtime code does not depend on `window.BPMProfiles*` load order; Monaco and route-specific code load only where used. |
| Documentation tooling | Existing commands and generated DITA/site/PDF/package content remain reproducible; build-tool modules have explicit ownership and the compatibility CLI remains thin. |
| Base package | A clean base wheel installs and starts health/profile/export smoke without `numpy`, `onnxruntime`, or `tokenizers`; the explicit AI extra installs its own tested dependency set. |
| Browser/live matrix | Chromium product/docs smoke is mandatory; deterministic Firefox live runs automatically on all three supported BPM schema channels; network-dependent AMO remains a separately identified canary. |
| Supply chain | Direct dependency currency/license decisions are recorded; Python and npm audits pass or have an explicitly approved, time-bounded exception; downloaded Firefox/geckodriver artifacts are version-pinned and checksum-verified. |
| Maintainability | Confirmed dead/legacy paths and history-only tests are removed; new architecture/test inventories are generated or executable; no new monolithic coordination module replaces a split one. |

## Non-Goals And Assumptions

- Do not add product functionality, public API capability, UI controls, routes, settings, policies,
  schemas, locales, CIS behavior, or documentation features.
- Do not change visible layout, styling, copy, interaction order, focus behavior, accessibility names,
  validation messages, error recovery, locale fallback, or supported Firefox schema channels, except
  for the explicitly approved removal of the YAML policy-editor capability in M3-04 and its owned
  controls/assets/localization/tests.
- Do not rewrite BPM in another framework, replace SQLAlchemy/FastAPI/Jinja, introduce a frontend UI
  framework, adopt a new database, or replace Selenium solely for this epic.
- Do not activate, complete, delete, or expose the incubating local AI/RAG assistant. Keep the
  current release training notice and existing externally reachable behavior exact.
- Do not remove a negative security/API contract merely because it concerns a removed feature.
  Retain a minimal black-box boundary where the absence of a dangerous route/method is part of the
  supported security posture.
- Do not remove a database migration or upgrade fixture until the approved support matrix proves it
  is outside the supported release path. Historical migration files remain immutable except for a
  separately approved correctness emergency.
- Do not update a dependency only because a newer version exists. Require compatibility, license,
  advisory, package, and focused regression evidence.
- Do not edit README for release-history, target-version, planned/completion, developer, or
  maintainer prose. Published DITA source may change only in M11 through the documentation-update
  runbook, for verified delivered behavior, completeness, localization, and the approved PDF
  presentation/navigation work; it must not document an unshipped feature as available.
- Do not commit generated build output, local browser installations, coverage output, SBOM reports,
  temporary databases, caches, or editable-package metadata.
- Do not use xdist, sharding, caching, or shared fixtures to hide order dependence or reduce semantic
  coverage. Serial execution remains authoritative until equivalence and isolation are proven.
- Product source, UI copy, changelog, and maintained technical documentation use English as the
  primary product language. Maintainer chat may remain Russian.

## Milestone 1: Version Transition And Release Anchors

Goal: establish `0.9.4` as the single active product version and refresh version/dependency metadata
without adding README release markers or changing historical records.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M1-01` | Update active product version surfaces to `0.9.4`. | Move `pyproject.toml`, runtime version resolution, active tests, and other nonhistorical product surfaces to the target version. | GPT-5.6 Luna | Light | Runtime `/`, OpenAPI, package metadata, UI-visible/generated version surfaces, and current-version assertions agree on `0.9.4`; historical migration/release fixtures remain unchanged; README receives no version anchor. |
| `BPM094-M1-02` | Refresh editable-package metadata and verify clean metadata resolution. | Reinstall the local editable package after the version change and prove the environment does not retain stale `0.9.3` metadata. | GPT-5.6 Luna | Light | `pip show browser-policy-manager`, `importlib.metadata.version`, and a clean editable reinstall report `0.9.4`; untracked `*.egg-info` is regenerated locally but not committed. |
| `BPM094-M1-03` | Recheck direct dependency currency, licenses, advisories, and compatibility. | Produce one reviewed decision matrix for base Python, PostgreSQL, AI extra, dev/test, frontend vendor, documentation toolchain, browser, and geckodriver components. | GPT-5.6 Terra | High | Every direct component has installed/declared/latest versions, source, license, advisory result, platform constraints, disposition, and focused verification; no floating or unreviewed update is accepted. |
| `BPM094-M1-04` | Apply approved dependency and toolchain refreshes. | Update only the M1-03-approved constraints, locks, pre-commit revisions, vendored outputs, licenses, and checksums. | GPT-5.6 Terra | High | Lockfiles and generated vendor checks agree; `npm ci`, `pip check`, vendor verification, focused compatibility tests, and license checks pass; rejected/deferred updates remain recorded rather than silently ignored. |
| `BPM094-M1-05` | Open and maintain the `0.9.4` changelog entry. | Add the behavior-preserving optimization/refactoring release section without overwriting prior release history. | GPT-5.6 Luna | Light | `CHANGELOG.md` contains an English `0.9.4` entry whose claims match completed work; all older entries remain byte-for-byte intact outside required link/reference maintenance. |
| `BPM094-M1-06` | Add version/package release characterization. | Guard project metadata, sdist/wheel metadata, installed runtime version, and the absence of README target-version prose. | GPT-5.6 Terra | Medium | Focused version tests fail on any active `0.9.3` leak, package/runtime disagreement, committed editable metadata, or README release anchor, while allowing historical `0.9.3` context. |

## Milestone 2: Characterization, Performance Baselines, And Architecture Contracts

Goal: make behavior preservation and optimization measurable before broad internal changes.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M2-01` | Freeze public API and profile lifecycle characterization. | Capture semantic OpenAPI, route/method/status, CRUD/conflict/soft-delete, validation, import, and export contracts without snapshotting unstable formatting. | GPT-5.6 Terra | High | Characterization fails on a changed public operation, status, payload field/meaning, revision rule, lifecycle behavior, or exact Firefox export, and passes under harmless implementation reordering. |
| `BPM094-M2-02` | Freeze rendered UI and locale behavior characterization. | Replace selected implementation-string assertions with semantic DOM, accessibility, route-asset, locale, and interaction-state contracts for every profile surface. | GPT-5.6 Terra | High | Library, compare, guided, settings, JSON, archived, clone, locale, CSP, keyboard/focus, and responsive contracts cover current behavior without requiring internal function names or global-script order. |
| `BPM094-M2-03` | Add a reproducible performance and repository-health harness. | Measure route latency/bytes, profile query/validation counts, test-layer duration, bundle sizes, owned file sizes, complexity, and package footprints with a recorded environment manifest. | GPT-5.6 Terra | High | The command emits flushed real phase/unit progress, machine-readable and human summaries, warm-up/repetition rules, cache state, failure boundaries, and comparable `0.9.3` baselines without committing local reports. |
| `BPM094-M2-04` | Freeze optimization budgets and regression gates. | Convert this backlog's latency, size, test-time, package, and coverage floors into focused executable contracts with documented variance handling. | GPT-5.6 Terra | High | Gates compare like-for-like environments, report actual measurements, reject material regressions, and cannot be satisfied by deleting tests, shrinking fixtures, skipping work, or fabricating progress. |
| `BPM094-M2-05` | Add executable Python architecture boundaries. | Use Import Linter to declare allowed API/web/service/core/model/tooling/incubation dependencies, acyclic siblings, and protected internal modules. | GPT-5.6 Terra | High | Direct and indirect illegal imports fail a fast contract; exceptions are minimal and owned; the default release graph cannot import AI/RAG runtime implementation or documentation build CLI internals. |
| `BPM094-M2-06` | Refresh the bounded current-system and ownership map. | Record entrypoints, lifecycles, data owners, generated/vendor boundaries, test contours, and targeted context routes for future maintainers and agents. | GPT-5.6 Luna | Medium | The technical map is generated or mechanically drift-checked, names the smallest files/tests to read per subsystem, excludes dependencies/generated corpora/secrets, and is indexed without changing product documentation. |

## Milestone 3: Release Runtime, Incubation, And Legacy Cleanup

Goal: make the shipped runtime boundary explicit and delete only code whose absence is proven.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M3-01` | Isolate the unshipped AI/RAG implementation behind an optional extra. | Sol is required because packaging, hidden runtime surfaces, security boundaries, development commands, and an unfinished assistant must be separated without activating or deleting externally reachable behavior. | GPT-5.6 Sol | Extra High | Base install/startup imports no NumPy/ONNX/tokenizer/model/RAG runtime and preserves the training notice plus current routes; an explicit AI extra installs and runs its isolated tests/dev commands; no assistant capability is promoted. |
| `BPM094-M3-02` | Add release-versus-incubation import and package contracts. | Prove which modules, dependencies, commands, fixtures, and tests belong to default release, optional incubation, or development tooling. | GPT-5.6 Terra | High | Clean base-wheel smoke succeeds with AI packages absent; forbidden release imports fail; optional-extra metadata is complete; hidden or disabled surfaces remain behaviorally identical. |
| `BPM094-M3-03` | Remove duplicate validation and unused YAML compatibility code. | Consolidate the test-only `PolicySchemaValidator` and unused YAML serializer into current owned validation/serialization paths, then remove their history-only tests. | GPT-5.6 Terra | Medium | All current schema/API/import/export behavior remains covered through canonical modules; no production/tool import references removed modules; obsolete tests disappear rather than being renamed. |
| `BPM094-M3-04` | Retire the user-facing YAML policy editor. | Make JSON the only profile-editor policy format: remove YAML mode selection, conversion/parsing branches, `js-yaml` route asset/vendor dependency, Monaco YAML registration, YAML-specific UI copy, and only the tests/contracts owned by that capability. Retain PyYAML and YAML files for CIS mappings, starter presets, and documentation toolchain configuration. | GPT-5.6 Terra | High | Every profile edit/import/export surface uses canonical JSON and preserves the exact full `{"policies": {...}}` document shape; JSON editor accessibility, formatting, validation, locale, CSP, browser, and route-asset contracts pass; no user-visible YAML editor control, asset, localization string, or parser remains; CIS/preset/docs YAML loading remains covered and functional. |
| `BPM094-M3-05` | Remove the obsolete raw-schema manager path. | Delete `SchemaManager`, `app/schemas/init.py`, `tools/update_schemas.py`, retry/backoff tests, and guessed raw-schema references; point technical runbooks to the authoritative pinned conversion workflow. | GPT-5.6 Terra | High | Current three-channel schema build/update/validation remains reproducible and offline-capable; no maintained runbook invokes a nonexistent raw schema; six-second retry tests and compatibility-only re-exports are gone. |
| `BPM094-M3-06` | Bound release service state and resource cleanup. | Audit request registries, caches, threads, subprocesses, files, HTTP clients, and shutdown paths; add TTL/cap/removal only where state can otherwise grow or leak. | GPT-5.6 Terra | High | Repeated completed/cancelled/expired operations do not grow process state; app shutdown closes owned resources; content-free diagnostics and current user-visible behavior remain unchanged; the existing ResourceWarning/runpy warning is eliminated. |

## Milestone 4: Native Async Database Runtime And Migration Ownership

Goal: remove blocking request-time database work and prove safe upgrades on both supported engines.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M4-01` | Define the supported database upgrade matrix and golden fixtures. | Sol is required because deciding the retained release window and exact legacy-row invariants controls irreversible data migration and removal of fallback code. | GPT-5.6 Sol | Extra High | The matrix names every supported source revision/schema, SQLite and PostgreSQL applicability, pre/post invariants, backup/restore procedure, failure stop conditions, and fixtures with representative valid, invalid, archived, compliance, revision, and channel data. |
| `BPM094-M4-02` | Introduce an application-owned native async database runtime. | Sol is required because replacing import-time global engines and a sync adapter across SQLite/PostgreSQL, FastAPI dependencies, tests, and shutdown has high concurrency and data-integrity risk. | GPT-5.6 Sol | Extra High | `DatabaseRuntime` owns async engine/sessionmaker/init/dispose; `sqlite+aiosqlite` stays async; no `AsyncSessionAdapter` remains in application code; settings/runtime can be injected; transaction and rollback semantics match characterization. |
| `BPM094-M4-03` | Initialize and dispose database state once per app lifespan. | Wire the runtime through the app factory and remove per-request `init_db`, module-import engine construction, and the unused library-route DB dependency. | GPT-5.6 Terra | High | One app lifespan performs exactly one readiness/init boundary and one dispose boundary; ordinary requests perform neither schema inspection nor `create_all`; independent app instances/tests cannot share overrides, sessions, or engines. |
| `BPM094-M4-04` | Make Alembic the only schema and data-upgrade owner. | Move every retained legacy table/column/index/channel transformation into the supported migration chain and remove startup normalization/backfill duplication. | GPT-5.6 Terra | Extra High | Runtime startup and profile listing never mutate legacy schema/channel data; `alembic upgrade head` is the sole upgrade path; historical migrations remain immutable; supported fixture data matches M4-01 invariants. |
| `BPM094-M4-05` | Add real SQLite and PostgreSQL integration coverage. | Run the same migration, CRUD, conflict, query, soft-delete, transaction, and export contracts against temporary SQLite and a CI PostgreSQL service. | GPT-5.6 Terra | High | Both engines reach head, pass common behavior, isolate transactions/workers, and close connections; PostgreSQL is no longer represented by a mocked constructor test. |
| `BPM094-M4-06` | Prove upgrade interruption, backup, and recovery boundaries. | Exercise failed migration, retained backup, retry-from-clean-state, downgrade only where supported, and application refusal against an incompatible/partial database. | GPT-5.6 Terra | Extra High | No failed/partial database is reported ready; recovery uses an explicit verified backup and documented command; tests never touch `data/bpm.db`; destructive recovery requires explicit maintainer action. |

## Milestone 5: Profile Query, Validation, And Route Performance

Goal: eliminate repeated database/schema/catalog work while preserving exact profile behavior.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M5-01` | Introduce one profile query/page result contract. | Give list items, filtered/total counts, lifecycle stats, pagination, and measured query metadata one service-owned operation without changing API response shapes. | GPT-5.6 Terra | High | API adapters return exact characterized payloads while one logical request avoids separate overlapping list/count/stats scans; unit/integration tests cover filters, sorting, archives, empty pages, and boundaries. |
| `BPM094-M5-02` | Push name filtering, sorting, and pagination into SQL. | Replace full-table Python name filtering/slicing with portable SQLAlchemy expressions for SQLite and PostgreSQL. | GPT-5.6 Terra | High | Case-insensitive search semantics match current Unicode fixtures on both engines; stable tie-breaking prevents page drift; query plans and row counts prove bounded retrieval. |
| `BPM094-M5-03` | Validate each profile at most once per logical operation. | Compile/cache validators by schema channel and carry computed validation state through filtering, counts, stats, and read-model creation. | GPT-5.6 Terra | High | Instrumented tests prove the validation-call budget; invalid/empty/unsupported profiles retain exact states and errors; cache invalidation follows schema artifact identity rather than time. |
| `BPM094-M5-04` | Split immutable catalogs from per-request profile page context. | Cache/freeze schema, wizard, preference, starter, documentation-link, locale, and category data at the narrowest safe owner while retaining test reset hooks. | GPT-5.6 Terra | High | Repeated requests do not rebuild immutable catalogs; cached values cannot be mutated by a caller; locale/schema/documentation artifact changes invalidate the correct key; parallel apps/tests remain isolated. |
| `BPM094-M5-05` | Build route-specific profile context projections. | Supply library, compare, guided, settings, and JSON templates only the catalogs and state each route consumes. | GPT-5.6 Terra | High | Every semantic DOM/UI characterization passes; route-irrelevant payloads are absent; latency and byte budgets pass; archived/clone/focus/locale/help-link paths remain exact. |
| `BPM094-M5-06` | Optimize immutable locale and static response serving. | Cache validated locale/favicon bytes and response metadata without changing routes, MIME types, status codes, or content. | GPT-5.6 Terra | Medium | Repeated requests perform no avoidable synchronous file read; missing/unsupported locale behavior and security headers remain exact; changed local assets invalidate safely in development. |

## Milestone 6: Frontend Module Ownership And Route Bundles

Goal: replace global load-order coupling with explicit modules while keeping the rendered and
interactive UI unchanged.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M6-01` | Freeze the frontend dependency graph and route ownership plan. | Map every owned profile JS/CSS module to library, compare, guided, settings, JSON, shared state, DOM adapter, or vendor ownership before conversion. | GPT-5.6 Terra | High | The plan identifies cycles, globals, dynamic boundaries, route entries, public DOM contracts, test owners, and staged conversion order; no catch-all replacement coordinator is approved. |
| `BPM094-M6-02` | Extract pure state and serialization ES modules. | Convert route state, data adapters, URL/state normalization, comparison, dirty guards, and value I/O into side-effect-free imports first. | GPT-5.6 Terra | High | Pure modules access no implicit `window`/`document`, have native Node tests, preserve serialized values/order/errors, and can be imported independently without bootstrapping a page. |
| `BPM094-M6-03` | Convert DOM/features to explicit dependency injection and imports. | Migrate preferences, extensions, network, search, schema shell, all-settings, review, workspace, and runtime coordination in bounded ownership groups. | GPT-5.6 Terra | Extra High | No converted group reads another component through `window.BPMProfiles*`; characterization and focused browser tests pass after each group; DOM/accessibility/copy remain exact. |
| `BPM094-M6-04` | Build route-specific esbuild entry bundles. | Add reproducible entries for library, compare, guided/edit, settings, and JSON with shared chunks and Monaco only on JSON routes. | GPT-5.6 Terra | High | Templates load a short manifest-owned asset set; source maps/metafiles/checksums/licenses are deterministic; route-irrelevant modules are absent; offline/CSP operation and size budgets pass. |
| `BPM094-M6-05` | Split maintained profile CSS by component ownership. | Move the large editor/wizard layer into route/component sources and generate one deterministic compatible stylesheet or explicit route bundles. | GPT-5.6 Terra | High | Generated CSS is reproducible; selector/order/specificity and all visual/accessibility browser baselines pass; generated output is never hand-edited. |
| `BPM094-M6-06` | Remove obsolete global frontend compatibility surfaces. | Delete transitional globals, shims, duplicate entry files, and source-text tests only after all route bundles and consumers are migrated. | GPT-5.6 Terra | High | A repository contract proves no owned runtime dependency on `window.BPMProfiles*`; unsupported global access fails tests; all semantic and browser regressions remain green. |

## Milestone 7: Documentation Tooling Modularity And Exact Handoff

Goal: reduce the documentation build context cost while preserving all published content and
maintainer commands.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M7-01` | Split `build_docs.py` into owned library modules. | Retain a thin compatible CLI while extracting source/DITA validation, navigation/search, manifests/targets, build/install/package, and PDF responsibilities. | GPT-5.6 Terra | Extra High | Commands, exit codes, diagnostics, generated content, ordering, hashes, and reproducibility remain characterized; no extracted module becomes another multi-thousand-line coordinator. |
| `BPM094-M7-02` | Decompose search/manifest semantic validation. | Replace the complexity-90 search validator and adjacent branch-heavy functions with typed staged validators and shared issue reporting. | GPT-5.6 Terra | Extra High | All valid current artifacts pass; each failure class has a focused fixture and stable actionable diagnostic; malformed input cannot be accepted because a branch was dropped. |
| `BPM094-M7-03` | Consolidate documentation tool progress and artifact utilities. | Give long builds/benchmarks shared flushed phase/unit progress, staging, checksum, atomic promotion, interruption, and cleanup helpers. | GPT-5.6 Terra | High | Long commands expose real completed/total work and terminal state; no fabricated percentage/spinner; interrupted candidates remain quarantined and the last verified artifact stays active. |
| `BPM094-M7-04` | Expand documentation-tooling coverage ownership. | Cover maintained library modules rather than claiming 100% for only `validate_metadata.py`; keep CLI/subprocess and browser checks in their appropriate layers. | GPT-5.6 Terra | High | Declared documentation Python surfaces reach 100% line/branch coverage or dead code is removed; coverage reports are isolated, reproducible, and invoked by mandatory CI. |
| `BPM094-M7-05` | Prove documentation-build baseline and maintainer handoff. | Run focused unit/contract, DITA/site/PDF/package reproducibility, install the current dev artifact, and record the baseline that M11 will deliberately improve. | GPT-5.6 Terra | High | `make docs-install-dev` succeeds; served/generated artifacts identify BPM `0.9.4`; baseline artifacts, commands, locale coverage, and known PDF/documentation defects are recorded so M11 changes are attributable and reproducible. |

## Milestone 8: Test Taxonomy, Consolidation, And Speed

Goal: turn the 2,506-test estate into explicit, nonoverlapping execution layers with less historical
and harness duplication.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M8-01` | Define one primary test layer plus orthogonal domains. | Adopt `unit`, `integration`, `contract`, `browser`, and `live` as exclusive primary layers; use domain/duration/environment markers separately. | GPT-5.6 Terra | High | Every collected test has exactly one primary layer; `api`, `db`, `schema`, `ui`, `docs`, `compliance`, `ai`, and `tooling` do not control primary execution; marker meanings and Make targets are unambiguous. |
| `BPM094-M8-02` | Replace filename-list marker policy with ownership configuration. | Move classification to directory/config/nearby metadata and add strict collection validation for product and documentation contours. | GPT-5.6 Terra | High | The 577 unclassified tests reach zero; unknown/duplicate primary markers fail collection; adding a new test under an owned tree needs no edit to a central filename list. |
| `BPM094-M8-03` | Reorganize test paths by layer and subsystem in reviewable batches. | Move tests and shared fixtures without mixing semantic rewrites; preserve focused commands and update imports/indexes mechanically. | GPT-5.6 Terra | Medium | Each batch collects the same intended cases, has no duplicate node IDs, preserves blame-friendly scope, and leaves generated/artifact fixtures under explicit ownership. |
| `BPM094-M8-04` | Consolidate profile route and DOM contracts. | Render each controlled route/fixture once per safe scope, parse semantic DOM once, and drive expectations from route/component tables instead of repeated megabyte string scans. | GPT-5.6 Terra | High | All current route states remain covered; isolation tests prove shared fixtures cannot leak mutations; slow route cases meet their budget and no test asserts private function/global names merely to claim architecture. |
| `BPM094-M8-05` | Move JavaScript behavior to native `node:test`. | Add a reusable ESM test harness and migrate Python `node -e` scripts/fake DOM duplication while leaving Python only for cross-language/build contracts. | GPT-5.6 Terra | High | JS tests run directly with deterministic isolation, timeouts, coverage, and useful failure locations; Python subprocess wrappers and duplicated harnesses are removed; no Vitest/Jest dependency is added without separate evidence. |
| `BPM094-M8-06` | Replace history/status tests with current generic contracts. | Classify all backlog/version/completion assertions; delete task-completion proof and generate reusable schema/manifest/index contracts for facts still required at runtime/release. | GPT-5.6 Terra | Extra High | Historical documents remain indexed but do not drive present implementation; current artifacts are validated by generic semantics; security, provenance, licensing, migration, and release facts are not lost. |
| `BPM094-M8-07` | Remove tests for confirmed legacy functionality. | Delete tests owned only by removed validation/YAML/raw-schema/re-export code and rename surviving version-coded tests by current behavior where practical. | GPT-5.6 Terra | High | No test executes nonexistent functionality or real retry sleeps; every removed test maps to deleted code/history or replacement behavioral coverage; supported legacy upgrades and negative security contracts remain. |
| `BPM094-M8-08` | Remeasure parallelism, sharding, order, and flake behavior. | Benchmark serial versus xdist/shards after isolation cleanup; run seeded order/repeat checks and choose the smallest stable mandatory parallel layer. | GPT-5.6 Terra | Extra High | The decision records median wall/CPU/RSS, worker count, failures, and critical-path effect; no order marker without an enforcing plugin remains; selected parallel runs match serial results across repeated seeds. |

## Milestone 9: Chromium And Firefox Runtime Automation

Goal: make real-browser behavior a repeatable release signal without conflating deterministic local
tests with network canaries.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M9-01` | Refactor Chromium product and docs browser harnesses. | Introduce scoped server/driver fixtures, page objects, semantic helpers, deterministic downloads, and per-test cleanup for the two large Selenium contours. | GPT-5.6 Terra | High | Product and documentation browser tests preserve current coverage, avoid repeated startup where safe, capture logs/screenshots on failure, and leave no process/profile/download state. |
| `BPM094-M9-02` | Combine Firefox activation and behavior scenarios. | For each deterministic policy scenario, assert exact input document, `about:policies` activation/errors, and runtime behavior in the same browser where isolation permits. | GPT-5.6 Terra | High | Duplicate launches are removed without dropping any activation or behavior assertion; conflicting/certificate baseline scenarios remain isolated; total launch count and runtime are reported. |
| `BPM094-M9-03` | Add a persisted complex-profile Firefox end-to-end test. | Save a nested `Proxy` + locked typed `Preferences` + `RequestedLocales` profile through BPM, read it back, export it, install the exact document, and observe Firefox. | GPT-5.6 Terra | Extra High | The test proves persistence and exact semantic/file equality, no Firefox policy errors, exact locale/proxy/lock preferences, and a real request through the local proxy; direct fixture-to-render shortcuts cannot satisfy it. |
| `BPM094-M9-04` | Make Firefox/geckodriver provisioning manifest-driven. | Pin channel/version/platform URLs and checksums for Release 153, ESR 153.0, ESR 140.13, and a compatible geckodriver; cache and isolate each installation. | GPT-5.6 Terra | High | Downloads verify checksums before extraction, reuse only verified artifacts, expose real flushed progress, never share writable policy roots across jobs, and report exact installed versions. |
| `BPM094-M9-05` | Automate deterministic Firefox live workflows. | Run all three supported channels on a reviewed schedule and manual dispatch, with cache, timeout, artifacts, and terminal job summaries. | GPT-5.6 Terra | High | Deterministic local policy tests require no external site after provisioning; each channel is independently visible; failure artifacts include versions, policy file, safe logs, and scenario identity. |
| `BPM094-M9-06` | Keep AMO as a separate external canary and remove unused XPI fixtures. | Combine AMO activation/install in one scenario, classify network failure separately, and delete the unsigned local XPI path unless a supported signed use is proven. | GPT-5.6 Terra | Medium | AMO cannot mask deterministic live results; one launch checks exact ExtensionSettings and installed add-on state; unused fixture/build/copy code is gone; provider/network failure is clearly reported. |

## Milestone 10: CI, Supply Chain, Packaging, And Release Gates

Goal: make every declared release surface prove itself in clean, nonoverlapping automation.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M10-01` | Build a nonoverlapping mandatory CI layer graph. | Separate lint/type/architecture, fast unit, integration DB, contracts/docs, JS, coverage, package, and Chromium jobs with explicit artifact/dependency flow. | GPT-5.6 Terra | Extra High | Every test belongs to exactly one normal CI owner; no required contour is omitted or redundantly rerun; critical-path and failure ownership are visible; live Firefox remains separately scheduled. |
| `BPM094-M10-02` | Add PostgreSQL service CI and migration evidence. | Install the retained `postgres` extra, run head migrations and common integration contracts against an ephemeral supported PostgreSQL service. | GPT-5.6 Terra | High | CI reports server/client versions and migration head, passes the M4 common suite, uses no production credentials, and always tears down temporary state. |
| `BPM094-M10-03` | Add Python/npm dependency audit and SBOM generation. | Run `pip-audit` and `npm audit` from resolved locks/environments and produce ignored CycloneDX evidence for release review. | GPT-5.6 Terra | High | Known actionable vulnerabilities fail CI; ignores require advisory ID, rationale, owner, and expiry; audits make no source changes; SBOM covers base and optional extras without being committed. |
| `BPM094-M10-04` | Add clean sdist/wheel and extras install smoke. | Build artifacts, inspect metadata/content, install base/PostgreSQL/AI variants into separate clean environments, and run the smallest relevant startup/health/profile/tool checks. | GPT-5.6 Terra | High | Base package has no AI dependency; extras are complete and mutually compatible; no tests/tools/secrets/caches leak into artifacts; `pip check`, version, license, entrypoint, and smoke commands pass. |
| `BPM094-M10-05` | Align pre-commit with the layered toolchain. | Update hook revisions and replace the broad per-change pytest hook with bounded fast/architecture checks while leaving full gates to explicit release/CI commands. | GPT-5.6 Terra | Medium | Local hooks use the approved Ruff/Black/Mypy/Python versions, finish within the fast budget, and cannot give a false full-suite success signal; full release commands remain documented. |
| `BPM094-M10-06` | Make coverage ownership complete and fail-closed. | Enforce 100% line/branch coverage for app and maintained documentation libraries plus declared JS pure modules, with separate readable artifacts. | GPT-5.6 Terra | Extra High | CI thresholds are 100%; falling below is not accepted as debt; uncovered dead/unreachable code is removed or tested; exclusions are narrow language/tool boilerplate and reviewed explicitly. |

## Milestone 11: Product Documentation Completion, PDF Quality, And Maintainer Handoff

Goal: bring published documentation up to the verified delivered product, correct the approved
PDF usability defects in every locale, then hand off both product and technical documentation in a
reproducible state. This milestone is intentionally before final quality because `0.9.4` is not the
last pre-release iteration and product functionality may still be refined before the documentation
tasks execute.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M11-01` | Inventory documentation gaps and placeholder prose. | Search maintained DITA maps/topics, PDF source, and generated-content contracts for TODO-like placeholders, incomplete explanations, and stale claims; map each finding to the verified product owner and locale impact. | GPT-5.6 Terra | High | A reviewed, executable inventory classifies every finding as completed, deliberately deferred with a safe boundary, or out of scope; placeholder text such as the missing explanation of locale-language selection has an identified authoritative behavior source before editing. |
| `BPM094-M11-02` | Complete verified product explanations in all affected locales. | Replace approved placeholders and incomplete reader guidance with factual purpose, prerequisites, selection rules, expected result, limitations, recovery, and related links based on current BPM behavior. Import and export guidance must both show a complete `policies.json` example with the top-level `{"policies": {...}}` envelope, never an ambiguous internal flags/settings fragment. | GPT-5.6 Terra | Extra High | English source is updated first and corresponding `ru`, `de`, `zh-CN`, `fr`, and `es-ES` content is complete; locale-language selection and every inventoried in-scope gap have real behavior descriptions, not future-tense or maintainer prose; README and every affected product-documentation import/export example show a semantically valid full `policies.json` envelope that matches the public API/export contract. |
| `BPM094-M11-03` | Normalize semantic UI and note/warning markup. | Mark BPM and Firefox UI element names with the project’s semantic inline UI markup; format localized Note, Warning, Tip, and equivalent labels boldly without changing their meaning. | GPT-5.6 Terra | High | Every affected locale renders UI controls distinctly and localized admonition labels in bold; code/API literals keep their existing semantic markup; accessibility, localization, and PDF/site contracts prove that visual formatting did not collapse meaning. |
| `BPM094-M11-04` | Add localized figure captions, numbering, and references. | Give every maintained figure a semantic caption, stable identifier, locale-appropriate numbered label, and valid cross-reference where the text relies on the figure. | GPT-5.6 Terra | High | All six locale PDFs/sites show a consecutive figure sequence per guide, visible captions, correct references, and no orphaned, duplicated, or unlabeled image; screenshots remain within printable bounds. |
| `BPM094-M11-05` | Make PDF title pages and contents navigable. | **Implemented 2026-08-05.** Added a deterministic two-pass Chromium layout, qpdf named destinations/link annotations, localized contents page labels, a page-number overlay, actual title-page totals, and bottom copyright sourced from the exact UI-footer template/catalog values. The release-scoped footer year is pinned in the PDF generation contract; UI template/catalog and PDF implementation changes invalidate the source fingerprint. | GPT-5.6 Sol | Extra High | All twelve PDFs passed fail-closed binary verification. User Guide pages are EN 106, RU 108, DE 107, ZH 103, FR 107, ES 106; Administrator Guide pages are EN 79, RU 99, DE 95, ZH 69, FR 95, ES 96. Every User Guide has 100 named and linked contents destinations; every Administrator Guide has 60. Positioned text proves the exact localized bottom copyright and one centered correct number on every non-title page. `qpdf --check` passed 12/12, focused unit/contracts passed 12/12, and an independent build matched SHA-256 for all twelve PDFs plus the manifest (13/13). Sol was required because the change crossed DITA transforms, HTML/print CSS, Chromium PDF post-processing, locale maps, UI-footer localization parity, print pagination, and binary-PDF verification. |
| `BPM094-M11-06` | Run the product-documentation editorial and PDF release review. | Follow `documentation-update-for-future-epics.md`: guide-map, terminology-authority, heading/completeness, six-locale DITA/site/PDF, visual, navigation, CJK, and reproducibility reviews. | GPT-5.6 Sol | Extra High | Every changed User, Administrator, Firefox Policy, and CIS topic has recorded product/locale authority; all six locale PDFs are visually inspected for title page, contents, linked navigation, captions, UI/admonition formatting, code/CJK layout, and correct page count; `make docs-release-check`, PDF verification, delivery/package verification, and reproducibility pass. Sol is required because this is a release-critical multi-locale publishing and binary-verification gate. |
| `BPM094-M11-07` | Update architecture, test, database, browser, and release runbooks. | Replace stale commands/owners with the implemented async DB, Alembic, module bundle, test layer, PostgreSQL, audit, browser, and revised documentation workflows. | GPT-5.6 Terra | High | Every changed technical procedure is executable, indexed, and uses current target names; no runbook references removed raw-schema, marker-list, sync-adapter, floating-browser, or the superseded documentation-freeze policy. |
| `BPM094-M11-08` | Refresh bounded Codex and documentation subsystem snapshots. | Regenerate maintained entrypoint/ownership summaries after code and documentation-pipeline moves while excluding dependencies, generated output, corpora, caches, secrets, and local artifacts. | GPT-5.6 Terra | Medium | Snapshots are current, compact, reproducible, and route future work to the smallest relevant files/tests; stale dirty-tree/version and documentation-freeze claims are gone. |
| `BPM094-M11-09` | Review README and product-documentation release boundaries. | Verify README remains version-neutral and audience-appropriate while published documentation reflects only verified delivered behavior and M11 corrections, including complete Firefox `policies.json` import/export examples. | GPT-5.6 Terra | High | README has no `0.9.4` anchor/history/planned/completion prose; its import/export examples and every changed DITA example use the complete top-level `{"policies": {...}}` document shape; changed DITA content is complete, localized, and factual; no guide exposes future capabilities, CI/source-tree details, or unapproved operator procedure. |
| `BPM094-M11-10` | Optimize the stabilized PDF build pipeline. | **Implemented 2026-08-09.** Added content-addressed locale-guide HTML and verified-PDF cache layers with transitive source/asset, locale footer, print, renderer, toolchain, contract, and generator identities. Cache reads and writes use exact manifests, SHA-256, private staging, copied-payload revalidation, quarantine, and atomic promotion; independent reproducibility bypasses the cache. Chromium remains the renderer and bounded parallelism stays at one worker after the measured two-core/RSS assessment. | GPT-5.6 Sol | Extra High | `pdf-pipeline-optimization-benchmark-0.9.4.json` records baseline median 773.89 s wall / 1075.12 s CPU / 376292 KiB RSS and optimized unchanged-build median 100.70 s / 98.82 s / 109476 KiB for the same 12 PDFs and 13 total files. The final cold build rebuilt 12/12 pairs, a warm build reused 12/12 verified PDFs, all PDFs matched baseline SHA-256, binary verification passed, and cache-bypass reproducibility rebuilt 24/24 phases and matched all 13 files. The broader documentation gate passed DITA/site/editorial validation and 1029 contracts; its three remaining failures are later-handoff README/source-install assertions, not PDF pipeline failures. |
| `BPM094-M11-11` | Run documentation and install handoff checks. | Execute focused runbook/index/snapshot tests, documentation unit/contracts, reproducibility/package/PDF verification, and `make docs-install-dev`. | GPT-5.6 Terra | High | All checks pass with real stdout progress; installed artifacts derive their visible version from BPM `0.9.4`; the maintainer's later `make dev` consumes the reviewed artifact without starting it now. |

M11 must follow the complete product-documentation editorial/localization runbook. It may update
published DITA, guide maps, screenshots, search targets, and generated artifacts only from verified
source, never to document planned functionality. If a remaining product behavior is still changing,
the owning M11 task records the dependency and runs after that behavior is finalized rather than
freezing premature prose.

## Milestone 11A: Documentation Test-Layer Rationalization

Goal: preserve fail-closed protection of published documentation and release artifacts while making
ordinary, verified editorial updates fast and proportionate. Tests must assert reader-visible
meaning, structural invariants, and delivery integrity rather than incidental wording, stale
evidence, whole-tree digests, or superseded maintainer commands.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M11A-01` | Inventory and classify the documentation test estate. | Catalogue maintained documentation tests by owner, asserted risk, execution cost, and coupling type; classify each as fast edit-time, release gate, scheduled audit, or remove/replace. Identify literal-text, snapshot, fixture, and obsolete-evidence coupling that has caused a false block during M11. | GPT-5.6 Terra | High | A machine-readable inventory assigns every maintained documentation test exactly one layer and owner; every previous M11 false blocker has a root-cause class and disposition; no critical structural, localization, PDF, security, or delivery check is merely downgraded without equivalent coverage. |
| `BPM094-M11A-02` | Define fast authoring and release-gate commands. | Establish bounded edit-time commands for a changed README/DITA/topic/locale and a separate authoritative release command for all six locales, package, PDF, reproducibility, and installation handoff. Make command output state selected scope, skipped release-only checks, and exact escalation path. | GPT-5.6 Terra | High | A documented, executable fast command completes within an agreed budget and catches schema, links, localization shape, complete `policies.json`, semantic UI/admonition, affected figure, and affected fixture regressions; the release command retains binary PDF, package, reproducibility, snapshot, and install proof and cannot be mistaken for the fast check. |
| `BPM094-M11A-03` | Replace brittle prose and stale-evidence assertions with semantic contracts. | Rewrite exact-phrase, whole-tree digest, retired-command, and stale fixture tests to use explicit authority records and positive/negative semantic assertions. Retain exact matching only for APIs, commands, identifiers, safety text, localized labels, hashes, and binary artifact invariants where exactness is the product requirement. | GPT-5.6 Terra | Extra High | A correct editorial rephrase, localized navigation change, or snapshot regeneration does not fail unrelated tests; removal of a required policy envelope, link target, protected literal, safety boundary, UI semantic, caption sequence, or release artifact still fails closed. Every rewritten assertion has a stated authority and focused positive/negative regression test. |
| `BPM094-M11A-03A` | Replace pseudo-descriptions with verified user explanations. | Review every maintained reader-facing section whose heading or lead promises an explanation, overview, description, rule, selection, fallback, behavior, or recovery. Detect empty restatements such as “description of locale selection” that do not state the actual rule. For each finding, trace the behavior to a current product owner, then write a factual explanation in English and all affected locales. | GPT-5.6 Terra | Extra High | No maintained guide contains a pseudo-description that merely repeats its heading or promises an explanation without giving it. Each in-scope explanation states the user-visible trigger or input, ordered rule/decision, supported values or boundary, observable result, fallback or recovery where applicable, and link to a related action; claims match verified current behavior. The locale-language section explicitly documents source precedence, supported locale matching, fallback locale, and the effect of an unsupported browser language. New semantic tests reject an empty lead while allowing localized editorial phrasing. |
| `BPM094-M11A-04` | Make snapshots and evidence deterministic, scoped, and reviewable. | Restrict snapshots to declared entrypoints and owners; generate them only through maintained commands; separate source-derived evidence from environment/report output; invalidate only the snapshot that owns a changed declared input. | GPT-5.6 Terra | High | Snapshot updates are reproducible without Git/local-machine state, never require manual digest editing, and do not invalidate unrelated documentation tests; generators, exclusions, owners, and narrow validation commands are indexed and tested. |
| `BPM094-M11A-05` | Rebalance CI and handoff ownership for documentation checks. | Map fast checks, release checks, scheduled audits, and browser/PDF-heavy checks to one nonoverlapping CI or manual-release owner, with clear failure classification and truthful timing/progress evidence. | GPT-5.6 Terra | High | CI does not rerun equivalent documentation work unnecessarily; each failure names its layer and owner; live/PDF/reproducibility work remains release-critical but is not imposed on ordinary prose edits; budgets, artifacts, and escalation instructions are documented and tested. |
| `BPM094-M11A-06` | Prove the rationalized documentation test model. | Execute representative benign editorial, localization, snapshot, semantic-regression, PDF, package, and reproducibility scenarios through the new layers; compare runtime and false-blocker rate with the M11 baseline. | GPT-5.6 Sol | Extra High | The evidence record demonstrates that benign scoped edits pass the fast layer without bypassing release guarantees, meaningful regressions fail in the earliest responsible layer, and the complete release chain remains clean. It reports command duration, test count, skipped-by-design contours, and remaining approved audit work. |

M11A must not delete or downgrade a documentation test merely to reduce duration or test count. Any
change in layer requires a recorded risk owner, a replacement assertion where applicable, and a
demonstration that the authoritative release chain still fails closed.

## Milestone 12: Final Quality, Release Commit, And CI Handoff

Goal: demonstrate a release-ready behavior-preserving `0.9.4`, then publish only the reviewed epic
commit and monitor every required workflow.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM094-M12-01` | Run the final Mypy gate. | Execute the maintained typecheck over all declared application/tooling surfaces after dependency and module moves. | GPT-5.6 Luna | Medium | `make typecheck` passes with no new broad ignores, untyped escape hatches, or excluded refactored package; failures are fixed and the gate is rerun. |
| `BPM094-M12-02` | Run the final Ruff and architecture gates. | Execute formatting/lint/complexity/import contracts and remove temporary suppressions introduced during staged refactors. | GPT-5.6 Luna | Medium | `make lint` and architecture contracts pass; no stale compatibility module, cyclic ownership, accidental generated edit, or unexplained new complexity exception remains. |
| `BPM094-M12-03` | Run the complete serial product and documentation test contours. | Execute authoritative non-live serial suites with duration and warning reporting before relying on parallel CI. | GPT-5.6 Terra | Extra High | `pytest -q` plus the complete documentation unit/contract commands pass with zero warnings, no unclassified tests, no unexpected skips/deselections, and the default/runtime budgets satisfied. |
| `BPM094-M12-04` | Prove 100% declared-surface coverage. | Run app, documentation tooling, and JS coverage reports and close every gap through focused tests or removal of dead code. | GPT-5.6 Terra | Extra High | All declared line/branch thresholds are exactly 100%; no gap is accepted as known debt; machine-readable and HTML artifacts identify ownership and remain uncommitted. |
| `BPM094-M12-05` | Run final Chromium product and documentation smoke. | Execute real-browser semantic, responsive, keyboard, locale, theme, CSP, import/edit/export, and documentation portal checks. | GPT-5.6 Terra | Extra High | All selected desktop/narrow and locale states pass; browser/server logs are clean; failure artifacts are retained; UI visuals/copy/behavior match characterization. Browser execution uses the required immediate sandbox escalation when applicable. |
| `BPM094-M12-06` | Run final deterministic Firefox and AMO evidence. | Execute the three pinned local Firefox channels and the separately reported external AMO canary after provisioning verification. | GPT-5.6 Terra | Extra High | Every deterministic channel passes exact policy/runtime tests including the complex profile; AMO result is reported separately; versions, checksums, runtime, skips, and artifacts are recorded. |
| `BPM094-M12-07` | Run final package, dependency, migration, and reproducibility gates. | Rebuild clean artifacts and rerun audits, SBOM, base/extras installs, SQLite/PostgreSQL migrations, vendor/docs reproducibility, and performance budgets. | GPT-5.6 Terra | Extra High | Every M1/M2/M4/M7/M10 release gate passes from clean state with real progress and no stale cache dependency; any approved advisory exception is still valid and unexpired. |
| `BPM094-M12-08` | Finalize changelog, technical indexes, and release-readiness evidence. | **Completed 2026-08-10.** Replaced provisional `0.9.4` notes with the verified release-readiness closeout; maintained indexes distinguish current ownership from retained 0.9.3 evidence. | GPT-5.6 Luna | Medium | Changelog claims are proven, older history is preserved, docs index is valid/unique, M11 documentation/PDF acceptance is reconfirmed, README remains version-neutral, and no active surface describes new work as `0.9.3`. |
| `BPM094-M12-09` | Create the reviewed BPM 0.9.4 epic commit. | Review scope/status/diff, exclude local/generated/unrelated changes, and commit the completed approved epic without tagging or releasing. | GPT-5.6 Terra | High | Working tree contains only reviewed BPM094 changes; tests/evidence are current; commit message names `0.9.4`; commit SHA is reported; no unrelated user work is included. |
| `BPM094-M12-10` | Push normally and monitor required CI to terminal state. | Push the reviewed commit to the configured branch with no force/history rewrite and observe every triggered required workflow. | GPT-5.6 Terra | High | Commit SHA, remote branch, workflow URLs, and every job result are reported; no tag/release/PR is created; rejected push, advanced remote, credential failure, protection failure, or failed workflow stops handoff for explicit maintainer direction. |

## Suggested Execution Order

1. Complete M1 version/dependency anchors.
2. Freeze M2 behavior, measurements, budgets, and architecture contracts.
3. Isolate release/incubation and remove proven legacy code in M3.
4. Complete M4 database runtime/migration ownership before broad test parallelism.
5. Optimize backend profile queries/contexts in M5.
6. Convert frontend ownership and route bundles in M6.
7. Split documentation tooling in M7.
8. Reclassify/consolidate tests and remeasure parallelism in M8.
9. Refactor and automate real-browser contours in M9.
10. Build mandatory CI, supply-chain, packaging, and coverage gates in M10.
11. Complete product documentation, PDF usability, localization review, technical documentation, and maintainer handoff in M11 after the remaining delivered behavior is stable.
12. Execute M12 final gates, commit, normal push, and terminal CI monitoring.

Within a milestone, follow task ID order unless an acceptance condition explicitly requires a later
task's fixture. Do not begin frontend bulk conversion before M2 characterization, database-dependent
parallelism before M4 isolation, or deletion of a compatibility path before its replacement and
reachability proof pass.

## Execution Protocol

- Do not execute a task merely because this backlog exists.
- Before each task, show exactly one next task with its ID, essence, acceptance, minimum model, and
  minimal reasoning; wait for explicit maintainer approval.
- Execute only the approved task. Report changed files, behavior impact, focused checks, measurements,
  remaining uncertainty, and working-tree state before offering the next task.
- Start from `docs/codex/PROJECT_SNAPSHOT.md`, then read only the task's named owners, adjacent tests,
  relevant rules/runbooks, and nearby modules. Do not recursively reload the repository.
- Keep changes small and reviewable. Separate characterization, architecture decision, mechanical
  movement, behavior-preserving implementation, and cleanup when their evidence differs.
- Preserve unrelated user changes in a dirty worktree. Never use destructive reset/checkout or force
  push to manufacture a clean state.
- Run the narrowest relevant validation first. Expand to the owning layer only after focused checks
  pass; reserve all-contour gates for their planned tasks.
- Any command that may run longer than one minute or has materially uncertain duration must emit
  flushed, real-work progress on its own stdout: current phase/channel/locale, completed and total
  units, cache/retry state, and a terminal success/failure boundary. Measured elapsed time/ETA is
  allowed; fabricated percentages, timers, and decorative spinners are not.
- While such a command runs, keep maintainer chat silent. If a third-party command cannot expose
  units, use a task-owned read-only observer that reports independently verifiable state without
  modifying the work. Safe interruption, partial-artifact quarantine, and atomic promotion remain
  mandatory.
- For Selenium/Chromium/Firefox commands that need execution outside a filesystem sandbox, request
  the required escalation immediately rather than performing a known-failing sandbox trial.
- Recheck current dependency versions, licenses, advisories, browser downloads, checksums, and model
  guidance at the task that consumes them; backlog-time observations are not permanent pins.
- A behavior, public API, UI/copy, locale, schema-channel, CIS, README, or published-product-doc change
  is out of scope unless it is explicitly owned by M11. M11 may change published documentation only
  through the documentation-update runbook and only to describe verified delivered behavior or fix
  the approved PDF/documentation-quality defects; do not rationalize an unshipped feature as prose.
- Coverage below 100% is never accepted as known debt. Add focused tests, reduce the declared surface
  by deleting proven dead code, or stop for a reviewed scope decision.
- The final push is regular and non-force. Do not rewrite history, tag, create a release/PR, or include
  unrelated changes. Monitor every required workflow to a terminal result and stop on failure.

## Backlog Creation Acceptance

- Target version is normalized as `0.9.4`, epic id `BPM094`, and filename prefix `bpm_0_9_4`.
- Scope, approved decisions, non-goals, risks, measured current state, and hard quality floors are
  explicit.
- Milestones are grouped by ownership/meaning and end in final type, lint, test, coverage, browser,
  documentation, changelog, commit, push, and CI gates.
- Every task has one stable ID, one minimum GPT-5.6 model, one allowed reasoning level, and a focused
  acceptance condition. Every Sol task explains why Terra is unsafe.
- M1 covers package/runtime/editable metadata, dependency currency, locks/vendor outputs, changelog,
  version tests, and the README version-neutral rule.
- M11 records the approved product-documentation completion, PDF usability, six-locale editorial,
  technical-documentation, and `make docs-install-dev` handoff boundaries; README remains
  version-neutral.
- Long-running commands and browser execution have explicit progress/escalation rules.
- Every backlog task requires separate explicit maintainer approval before execution.
