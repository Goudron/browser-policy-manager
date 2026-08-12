# Changelog

## 0.9.5

Status: **Release candidate; implementation, documentation delivery, and final quality review are complete. Reviewed commit and CI handoff remain.**

### Changed
- Moved the active BPM product and package version surfaces to `0.9.5`.
- Applied the approved M1 refreshes: `build==1.5.0`, optional-AI `numpy>=2.5.2`,
  `esbuild` 0.28.2, and the documentation-toolchain `packaging==26.3` lock.
- Refreshed the checksum-pinned Firefox Release live-test archive to 153.0.3.
- Added Firefox ESR 115.38 to the supported Release 153, ESR 153.0, and ESR 140.13
  schema matrix. CIS availability is now evaluated by exact schema channel and does not invent a
  compliance result where the benchmark is unavailable.
- Added explicit, no-silent-loss profile conversion: BPM can recommend ESR 153.0 for supported
  older ESR profiles, create a read-only preview, and apply only an explicitly confirmed,
  current eligible plan. A blocked, stale, invalid, or failed conversion leaves the profile
  unchanged.
- Added the reviewed ESR 140.13-to-ESR 153.0 total-convertibility proof and candidate-only
  retirement materializer. ESR 140.13 remains supported, so no retirement migration is installed
  in the active Alembic graph.

### Documentation
- Updated all four guide families in English, Russian, German, Simplified Chinese, French, and
  Spanish for the four-channel lifecycle, conversion, CIS availability, API, and recovery
  boundaries.
- Completed the verified documentation release handoff: six-locale site validation, the two-guide
  PDF set, reproducibility and delivery checks, package verification, and installation of the
  BPM 0.9.5 documentation artifact.

## 0.9.4

Status: **Release-readiness evidence accepted; reviewed commit and CI handoff remain.**

### Changed
- Completed the behavior-preserving optimization, refactoring, and release-hardening scope for
  0.9.4, with current ownership and release boundaries recorded in the maintained technical
  contracts.
- Reviewed and applied the approved dependency and toolchain updates, including FastAPI, Uvicorn,
  Selenium, Ruff, Mypy, Monaco Editor, js-yaml, and the Temurin documentation JRE.
- Pinned the Firefox live-test environment to checksum-verified Firefox Release 153.0.1, Firefox
  ESR 140.13.0esr, and geckodriver 0.37.1 archives.

### Quality
- Accepted the M11 six-locale documentation and PDF release review: DITA/site validation, binary
  PDF verification, delivery/package verification, cache-bypass reproducibility, and the final
  documentation release check passed. See the
  [0.9.4 release-readiness evidence](docs/architecture/release-readiness-evidence-0.9.4.md).

## 0.9.3

Status: **Release candidate; implementation complete.**

### Changed
- Retained the BPM-owned deterministic documentation search as the released search experience;
  its ranking and six-locale behavior remain independent from the assistant surface.
- Added the six-locale documentation assistant UI and API boundary with a localized training notice.
  In 0.9.3 it does not start a model worker, RAG index, generated-answer flow, citation flow, or
  external-source request.
- Preserved the local-only privacy and product-scope boundary: external sources are not exposed in
  the release UI, and deferred model training, RAG answer quality, citations, and external search
  remain outside 0.9.3.

### Documentation
- Completed the User and Administrator Guides in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`,
  including the product overview, minimum system requirements, search/assistant boundary, current
  Firefox schema header, editorial and terminology review, and localized navigation.
- Generated and verified both guide PDFs for all six locales, the versioned documentation delivery
  directory, checksums, package metadata, and the installed documentation artifact used by `make dev`.

### Quality
- Completed deterministic-search, locale, security/privacy, documentation, PDF, package,
  reproducibility, and browser smoke release gates. Deferred model/RAG quality is not represented as
  a 0.9.3 quality result.

### Known boundaries
- Local model training and RAG-generated answers are planned for a later release. The 0.9.3
  assistant truthfully reports that training is in progress; it does not claim model readiness.

## 0.9.2

Status: **Release candidate; implementation complete.**

### Changed
- Уплотнены Library, Guided editor, All settings, JSON editor, Compare и общая оболочка редакторов:
  удалены дублирующие пояснения при сохранении подписей, состояний, валидации, восстановления,
  предупреждений об опасных действиях и доступности.
- Документация получила ту же компактную оболочку, заголовок, стили, локаль и версию BPM, что и
  основной интерфейс; состояние свёрнутых фильтров поиска сохраняется после поиска.
- Из пользовательской документации удалены обращения к разработчику и служебные сведения о ходе
  реализации; заголовки и видимый текст выровнены по локальным редакционным правилам.
- Добавлена одновременная поддержка трёх схем Firefox: релиз 153, ESR 153.0 и ESR 140.13;
  различия каналов и отсутствие автоматической миграции между ESR документированы. Supported
  channels are Release 153, ESR 153.0, and ESR 140.13.

## 0.9.1

### Added
- Added the approved minimal User Guide screenshot set: six workflow screenshots in each of the
  `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` locales, with deterministic capture states,
  localized captions and alt text, normalized PNG assets, and visual/freshness/orphan checks.
- Added manifest-backed circled-information documentation links for all 120 supported Firefox
  policy rows and all 62 known managed-preference rows in All Settings, including localized
  labels, new-tab deep links, keyboard behavior, and explicit unavailable/stale/incomplete states.

### Changed
- Aligned the documentation portal with the BPM interface and added light, dark, and system theme
  modes; changed the primary light surfaces in both BPM and documentation from harsh white to
  accessible light gray.
- Collapsed documentation search to one line by default with deliberate expansion, retained query
  and filter state, deterministic offline results, and localized filter labels in all six locales.
- Replaced duplicated document headings and long flat topic lists with one generated
  Documents/guide/section/topic tree that supports direct-topic reveal, reliable parent/root
  return, keyboard navigation, and independent sidebar scrolling.
- Removed the obsolete standalone API Integration Guide from the six-locale portal, navigation,
  search, and manifests; API workflows and contextual targets now resolve through the
  Administrator Guide.
- Made the six runtime locale catalogs the documented authority for BPM interface names, with
  explicit historical aliases, non-UI technical-term boundaries, and catalog defects that must be
  corrected before localized documentation replacement.
- Replaced historical English BPM interface names across all six documentation locales and
  generated navigation/search surfaces, while correcting malformed French, Spanish, German, and
  Chinese runtime labels and retaining former terminology only as non-visible search queries.
- Completed the full five-locale visible-prose review across all 805 non-English DITA/map sources,
  replacing English and mixed-language sentences while retaining only reviewed technical literals,
  identifiers, brands, and established abbreviations.
- Replaced per-page embedded documentation trees with one deterministic, manifest-backed
  `navigation.json` per locale and a shared same-origin runtime that preserves accessible tree
  navigation, direct-topic reveal, independent scrolling, and localized failure recovery.
- Added fail-closed documentation regression gates for retired API-guide structure, Administrator
  API ownership, navigation artifact/manifest semantics, compact tree hosts, locale-owned UI terms,
  visible-English review coverage, and bounded live technical exceptions.
- Completed six-locale Chromium QA for successful and failed asynchronous navigation loading,
  desktop/narrow long-tree wheel and keyboard scrolling, direct-topic/root return, retired API-guide
  absence, exact BPM interface terms, and representative localized prose.
- Accepted the maintainer-approved contract for bounded five-distribution Docker validation,
  including a Docker-absent host baseline, immutable image/ISO provenance, strict CPU/RAM/storage
  limits, no user-data or production access, retained transcripts, failed-install rollback,
  M11-resource inventory/handoff, and persistent Docker Engine retention for future project work.
- Installed the five approved Docker Engine components from Docker's signed Ubuntu 26.04
  repository, verified the daemon/socket/group boundary with an isolated resource-limited smoke
  container, removed all smoke resources, and retained the empty Docker runtime for live Linux
  source-install validation and future project work.
- Added the retained clean-container source-install harness with attempt-isolated evidence,
  DITA-owned command extraction, bounded CPU/RAM/storage, deterministic probes, and no deletion
  path; accepted Ubuntu lifecycle checks and a signed-official-ISO-derived Linux Mint 22.3 image
  while retaining all stopped validation containers, target images, and the dedicated network.
- Completed the live Ubuntu 26.04 LTS source-install procedure from the retained clean golden image
  against an immutable BPM 0.9.1 ref, including prerequisites, migrations, six-locale documentation
  publication, BPM health/readiness/UI probes, and clean shutdown; hardened completion detection
  after two retained diagnostic attempts and accepted only the fresh third-container transcript.
- Completed the live Debian 13.5 source-install procedure against the same immutable BPM 0.9.1 ref,
  including checksum-verified CPython 3.14.6, migrations, six-locale documentation publication,
  BPM probes, and shutdown; retained the first diagnostic container, corrected the shared runtime
  adapter to preserve the activated environment and fail early, and accepted a fresh second run.
- Completed the live Fedora Linux 44 source-install procedure on the first clean container against
  the immutable BPM 0.9.1 ref, using Fedora's Python 3.14.6 packages and the inherited Ubuntu/Debian
  harness protections; migrations, six-locale documentation publication, BPM probes, completion
  guards, and clean shutdown passed while the Fedora image and stopped container were retained.
- Completed the live Linux Mint 22.3 Zena source-install procedure on the first clean container
  derived from the verified signed official ISO, including the real Mint Zena package repository,
  checksum-verified CPython 3.14.6, migrations, six-locale documentation publication, BPM probes,
  completion guards, and clean shutdown; the clean image and stopped container remain retained.
- Completed the live Manjaro stable source-install procedure from the pinned March seed after a
  full stable-branch update to the July 2026 package state; corrected the documented pacman command
  to confirm non-interactively after the retained first diagnostic attempt, then passed BPM 0.9.1
  installation, migrations, six-locale documentation, probes, guards, and shutdown in a fresh retry.
- Reconciled all five Linux source-install procedures and six locale peers with their retained live
  transcripts, including exact Russian command parity and reviewed CPython optional-module results;
  closed the Linux userspace evidence blocker while explicitly retaining OCI, native-host,
  production, Windows, and WSL boundaries.
- Added a fail-closed PowerShell validation runner and feasibility contract for genuine Windows
  10/11 WSL 2 hosts, covering host/build identity, Ubuntu 26.04 source assertions, systemd and
  filesystem state, Windows/WSL localhost and Edge access, clean stop, WSL restart, and hashed
  evidence while retaining both actual-host outcomes as unverified until those hosts are supplied.
- Closed the conditional Windows 10 WSL validation task as unverified because no actual Windows 10
  host was supplied, retaining an explicit machine-readable no-run record and making no Windows,
  WSL, localhost, Edge, shutdown, restart, native-support, or production-readiness claim.
- Closed the equivalent conditional Windows 11 WSL task as unverified without creating a VM because
  neither an actual Windows 11 host nor installation media was supplied; retained the no-run record
  and left a future supported-host rerun explicitly available.
- Completed the retained Docker-environment handoff with all 13 validation containers stopped, all
  five clean target images and the dedicated network preserved, zero volumes/build cache, unchanged
  package/repository/key/socket/group and firewall boundaries, and no cleanup deletion or unrelated
  host mutation.
- Closed the live-install evidence record with five mandatory Linux userspace procedures accepted
  against exact retained command/result transcripts, no unresolved mandatory failure, Windows
  10/11 WSL outcomes explicitly unverified without actual hosts or validation claims, and the
  retained Docker environment handed off intact; later milestones still own overall 0.9.1 release
  readiness.
- Refreshed README current-state documentation for the four-guide portal, application-aligned
  themes, compact search, generated independently scrolling hierarchy, localized screenshots and
  terminology, five Linux source-install procedures, conditional WSL boundary, and per-policy and
  per-preference All Settings help links without adding version-specific release history.
- Updated all six localized User Guide peers to explain the independently scrolling documentation
  tree, direct-topic reveal, compact expandable search and filters, documentation theme behavior,
  and All Settings policy/preference help links; removed visible 0.9.0 portal wording and standalone
  API-guide naming, and moved maintained Administrator topics to current product metadata.
- Updated the maintained localization and screenshot runbook with explicit 36-row User Guide
  matrix drift gates, localized caption/alt-text checks, runtime UI-catalog authority,
  Pontoon/SUMO terminology review, and narrowly evidenced visible-English allowlists.
- Extended Firefox schema, CIS, locale, Administrator/DevOps, update, integration, publishing, and
  release procedures with navigation/search/theme/help-link drift checks, retained-image Linux
  live-evidence invalidation, honest actual-host WSL boundaries, and implemented release commands.
- Closed the documentation sufficiency record across all four maintained guides, localized
  screenshots and terminology, themes/search/navigation, API-guide consolidation, All Settings
  targets, and five retained Linux runs while preserving explicit unverified Windows/WSL and
  overall release-readiness boundaries.
- Reconciled the maintained documentation index to all 119 active, runbook, audit, backlog, and
  archive files with no missing, stale, duplicate, generated, local, or container-state entries.

### Quality
- Passed static typing and Ruff lint, the complete default pytest suite, and branch-aware coverage
  of all 3,268 maintained application statements and 1,072 branches at `TOTAL 100%`.
- Passed clean six-locale DITA publication and all 752 non-browser documentation release
  contracts, plus 256 UI contracts/browser scenarios, six dedicated documentation Selenium
  scenarios, and 17 focused screenshot/visual-QA contracts.
- Verified the maintained M10-M12 handoff across navigation/localization, guide consolidation,
  five-distribution live evidence, conditional WSL boundaries, retained environment inventory,
  README, product documentation, runbooks, docs index, sufficiency, and drift gates.

### Known boundaries
- Windows 10 and Windows 11 WSL behavior remains unverified because no actual Windows hosts were
  supplied; Linux containers and static checks do not substitute for actual-host validation.
- Screenshot coverage remains intentionally limited to the approved minimal User Guide matrix;
  screenshots for every guide family and topic remain outside this release.
- Documentation search remains deterministic and non-AI. Packaged installers, production
  hardening, HA, managed secrets, and automated restore guarantees remain deferred.

## 0.9.0

### Added
- Added the packaged BPM product documentation portal under `/help/` with DITA-authored source,
  deterministic static publication, manifest/target-map validation, locale-aware routing, and
  offline operation.
- Added five documentation guide families for User Guide, Firefox Policy Guide, CIS Settings Guide,
  API/DevOps integration guidance, and Administrator/DevOps source-deployment guidance.
- Added complete six-locale documentation coverage for `en`, `ru`, `de`, `zh-CN`, `fr`, and
  `es-ES`, with parity checks that prevent reduced localized topic content.
- Added a deterministic non-AI documentation search experience with per-locale indexes,
  normalization, aliases, facets, typo-tolerant ranking, quality fixtures, and integrity gates.
- Added a visible documentation link in the BPM product header plus contextual help icons that open
  relevant documentation pages in a new browser tab while preserving FastAPI/OpenAPI `/docs`.
- Added Administrator/DevOps runbooks for Linux source deployment, Windows 10/11 source deployment
  through WSL, source-update procedures, operational boundaries, health/readiness checks, API
  integration workflows, reusable examples, and troubleshooting.
- Added documentation-specific test boundaries, focused Make targets, compact fixtures, browser
  smoke coverage, isolated documentation coverage reporting, failure diagnostics, and a compact
  documentation subsystem snapshot.

### Changed
- Updated active package, runtime, README, changelog, documentation-index, architecture-map, and
  version-contract test surfaces to the 0.9.0 product documentation portal release line.
- Refreshed README as current-state product documentation rather than release history; versioned
  change summaries remain in this changelog.
- Updated the backlog-creation runbook so the first milestone includes editable-environment
  metadata refresh, external component currency checks, and dependency/toolchain review.
- Updated Python dependency minimums and the local editable environment metadata for BPM 0.9.0;
  refreshed frontend vendor pins and rebuilt vendored Monaco assets with clean npm audit results.

### Quality
- Kept static typing and lint gates green with `make typecheck` and `make lint`.
- Completed full default pytest, full app coverage, documentation release validation, and
  browser-backed BPM/documentation smoke gates during the final 0.9.0 quality milestone.
- Confirmed the documentation release gate covers DITA publication, six-locale parity, content,
  manifests, target maps, deterministic search, provenance, API examples, accessibility/security,
  and non-browser portal contracts.
- Confirmed npm audit reports zero vulnerabilities after frontend vendor refresh.

### Known non-goals and deferred work
- Documentation search is deterministic and non-AI; conversational search, embeddings, RAG, or
  learning behavior remain outside 0.9.0.
- Packaged installers, official service units, supported HA clustering, production hardening,
  managed secrets, official reverse-proxy recipes, rolling upgrades, and automatic restore
  automation remain deferred until distribution/runtime decisions exist.
- System Python remains on the available 3.14 patch line in the local environment because the
  package manager did not provide Python 3.14.6; the project requirement remains `>=3.14`.
- Maintainer manual documentation QA found issues accepted for deferral to a later version rather
  than blocking the 0.9.0 final quality milestone.

## 0.8.8

### Added
- Added a shared All settings inventory model for schema-backed policies, known and unknown managed
  preferences, validation issues, source attribution, CIS decisions, search, and detail editing.
- Added explicit Review, Configured, and Catalog modes inside the existing All settings route.
  Review prioritizes invalid, CIS review, raw, unknown, deprecated, and imported items; Configured
  summarizes applied settings by domain/source; Catalog exposes the complete supported inventory.
- Added grouped, scope-aware settings search with deduplicated destinations and a primary detail
  editor for apply, remove, reset, source, validation, and location context.
- Added domain summaries, source filters, category drilldown, bounded visible lists, Catalog
  pagination, keyboard/focus contracts, screen-reader labels, and responsive heavy-profile layouts.
- Added a distinct permanent-delete action for active and archived Library profiles with explicit
  irreversible confirmation and failure-safe API handling.
- Added bundled Firefox Release 153 and ESR 140.13 schemas from Mozilla policy templates v7.12,
  including migration/runtime normalization, generated CIS layers, and All settings coverage for
  new schema policies.

### Changed
- Made Review the default All settings workflow for saved enterprise profiles instead of opening
  the complete schema catalog and every long section at once.
- Re-homed full schema-shell and managed-preference controls behind Catalog/detail while retaining
  complete coverage and guided/raw/deprecated metadata.
- Unified baseline, CIS, manual, imported, raw, unknown, and catalog-only source state across list,
  summary, search, and detail views.
- Updated supported Firefox channels, UI labels, README examples, converter defaults, legacy guards,
  migrations, locale catalogs, CIS mappings, and generated layers to Release 153 / ESR 140.13.
- Updated all six active locale catalogs and the global terminology/allowlist contracts for new All
  settings copy, permanent deletion, Compare cleanup, and the Web Serial policy label.

### Fixed
- Removed duplicate All settings category/catalog surfaces and conflicting configured counters,
  filters, automatic category drilldown, and row-selection category mutation.
- Corrected heavy-profile inventory hydration so corporate preset + CIS Level 2 profiles expose
  configured, baseline, CIS, guided, raw, and known-preference counts instead of zeros or unknowns.
- Fixed JSON editor loading for CIS-managed known preferences and localized Guided disclosure labels
  across runtime language changes.
- Removed the redundant return-to-Library action, dead header container, and stale value-state legend
  from the dedicated Compare route while retaining new-tab Library handoff.
- Reduced large-profile list latency by reusing cached schema validators and stabilized browser smoke
  interactions across asynchronous locale rerenders.

### Quality
- Added inventory, route-state, source attribution, search grouping, detail editing, performance,
  responsive layout, accessibility, Library deletion, Compare cleanup, schema migration, locale,
  and Chromium/Selenium regression coverage.
- Kept `make typecheck`, `make lint`, `make test-ui`, and `make test-release` green after the completed
  epic and Firefox schema bump.
- Confirmed non-live `app/` coverage remains at `100%`: 2,739 statements and 828 branches with no
  missing statements, branches, or partial branches.

## 0.8.7.1

### Changed
- Completed the BPM 0.8.7.1 polish pass for the dedicated `/profiles/compare` route.
- Made Compare participate in the shared language and theme preference flow, including Library
  new-tab handoff.
- Documented the completed compare and clone behavior in README and local visual QA notes.

### Fixed
- Fixed Compare language/theme persistence so the route no longer falls out of sync with the
  Library-selected preferences.
- Improved large profile selection in Compare with bounded, scrollable search results and clearer
  name, schema, and updated-time spacing.
- Removed duplicated policy/preference identifiers from comparison table setting cells.
- Kept Library clone-name actions inside their panel across supported locales and narrower
  viewports.

### Quality
- Added Chromium/Selenium smoke coverage for compare locale handoff, large selector lists,
  comparison table labels, and Russian clone-name action bounds.
- Kept `make typecheck`, `make lint`, `pytest -q`, `make coverage`, and `make test-ui` green.
- Confirmed non-live `app/` coverage remains at `100%`.

## 0.8.7

### Added
- Added a dedicated `/profiles/compare` interface for selecting two saved profiles and comparing
  policy and managed-preference settings side by side.
- Added compare-specific frontend assets, route templates, localization keys, responsive layout
  contracts, and browser UI smoke coverage.
- Added explicit clone naming from the Library so duplicate-profile flows open a named guided-editor
  draft in a new tab.

### Changed
- Kept the Profile Library focused on profile management by replacing embedded comparison UI with
  a navigation control to the dedicated comparison route.
- Simplified profile data flow by removing the unused owner field from runtime models, schemas, API
  filters/responses, import handling, frontend payloads, locale catalogs, and active docs.
- Updated README and active architecture notes for the completed 0.8.7 product state.

### Fixed
- Removed stale Library/editor comparison DOM, state, CSS, locale keys, and clone-handoff compare
  guidance so comparison happens only in `/profiles/compare`.
- Tightened clone-name conflict handling and browser-smoke coverage for named clone drafts.
- Suppressed noisy third-party `websockets` deprecation warnings in pytest while keeping project
  warnings visible.

### Quality
- Kept `make typecheck`, `make lint`, `pytest -q`, `make coverage`, and `make test-ui` green.
- Confirmed non-live `app/` coverage remains at `100%`.

## 0.8.5

### Added
- Added repository health reporting, refactoring acceptance rules, and a maintained architecture map to reduce repeated project discovery work.
- Added a documentation index and machine-readable manifest, with completed audits and backlogs moved into a dated archive.
- Added source locale catalogs, deterministic locale build/check commands, locale inventory, and locale quality tooling while preserving runtime catalog parity.
- Added reproducible frontend vendor locking, checksum verification, scripted rebuilds, license checks, and size-diff reporting.
- Added marker-based test layers, executable Make targets, release-readiness guidance, and a manual pure-unit `pytest-xdist` pilot.
- Added xdist-safe database, FastAPI app, dependency override, and cache isolation harnesses for pytest.

### Changed
- Moved the project from `0.8.0` to `0.8.5`.
- Split large profile frontend assets, route context/navigation helpers, schema normalization logic, policy validation logic, and test modules into smaller ownership-focused files.
- Replaced scattered playbook commands with Make targets for routine development, locale maintenance, vendor rebuilds, schema work, browser checks, and release verification.
- Split CI into mandatory fast checks, coverage/contract checks, manual browser UI checks, and scheduled/manual live Firefox checks.
- Kept `pytest-xdist` opt-in for BPM 0.8.5 after the pure-unit pilot improved its 221-test subset by approximately 27% to 37% but did not shorten the existing mandatory CI critical path.

### Fixed
- Removed the obsolete editor compatibility route, redirect, compatibility artifacts, and stale JSON-editor naming so the product exposes only Library, Guided editor, All settings, and JSON editor surfaces.
- Refreshed vendored `js-yaml` to the patched `4.2.0` release and retained YAML import compatibility.
- Reduced brittle documentation, static-source, locale, and workflow assertions by moving repeated contracts into shared helpers and generated checks.

### Quality
- Kept mandatory fast tests, focused contract tests, Ruff, mypy, and release-oriented test layers green throughout the refactoring backlog.
- Preserved the existing product behavior, supported Firefox schema channels, six-locale runtime matrix, and non-browser coverage gate.

## 0.8.0

### Added
- Added first-class runtime locale catalogs for German, Simplified Chinese, French, and Spanish (Spain), bringing the UI matrix to `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.
- Added locale matrix, fallback, picker, runtime-loading, and catalog parity coverage for all six supported locales.
- Added Mozilla/Pontoon/SUMO terminology audits, a six-locale UI glossary, locale placeholder/identifier rules, and a locale-update runbook for future copy changes.
- Added browser and workflow QA contracts for locale smoke coverage, viewport overflow, screenshot review, locale switching, and localized import/edit/export flows.

### Changed
- Moved the project from `0.7.7` to `0.8.0`.
- Updated README localization guidance to describe the six supported locales, English source-language policy, Mozilla terminology expectations, and current `0.8.0` product state.
- Promoted the global six-locale glossary as the current maintainer terminology reference and kept the old EN/RU glossary as a historical archive only.
- Expanded locale quality checks so valid technical English remains allowed while untranslated prose, placeholder drift, key mismatches, and machine-translation artifacts are caught earlier.

### Fixed
- Fixed untranslated and partially translated UI islands across Guided editor, All settings, JSON editor, Library, CIS flows, runtime counts, validation/error text, search/filter labels, and generated workflow copy.
- Fixed locale-specific terminology issues found during review, including Chinese profile wording, footer copyright identity, Mozilla terms, and accidental English fragments in non-English catalogs.
- Removed the redundant `Back to previous mode` return button from settings/JSON editor routes so JSON mode opens consistently from Library, Guided editor, and All settings.
- Fixed locale-related layout and script risks exposed by German, French, Spanish, and Simplified Chinese QA passes.

### Quality
- Kept `mypy app`, `ruff check .`, and fast pytest green after the locale expansion.
- Confirmed non-live `app/` coverage remains at `100%`.

## 0.7.7

### Added
- Added bundled Firefox policy schemas for Firefox Release 151 and Firefox ESR 140.11.
- Added profile schema migration and runtime library normalization so profiles stored on Firefox Release 149/150 or ESR 140.9/140.10 are upgraded to the current supported schema channels when the library opens.
- Added UI coverage for new Firefox 151 policies, including `LocalNetworkAccess` in the guided privacy/site-data flow and `XSLTEnabled` in the Privacy/Security settings catalog.
- Added schema-bump runbook steps for profile normalization, UI impact review, README version checks, and starter-preset review.

### Changed
- Moved the project from `0.7.6` to `0.7.7`.
- Updated the supported schema documentation, product header copy, schema labels, examples, CI guards, and generated CIS Firefox layers to Firefox Release 151 / ESR 140.11.
- Refreshed Mozilla policy conversion logic for the 7.11 policy template release, including handling for new Linux-example-only policy entries and `ExtensionSettings.update_url` metadata.
- Reviewed starter presets against the new policy docs and kept their defaults unchanged where new policies could surprise intranet, local-device, or compatibility workflows.

### Quality
- Kept `mypy app`, `ruff check .`, and fast pytest with branch coverage green.
- Confirmed non-live `app/` coverage remains at `100%`.

## 0.7.6

### Added
- Added a more complete profile-library manager with clearer search, schema, validation, lifecycle, duplicate, export, and editor-entry actions.
- Added a schema-aware All settings catalog for full visual policy inspection and editing beyond the guided path.

### Changed
- Moved the project from `0.7.5` to `0.7.6`.
- Reworked the guided editor into a shorter task-first workflow while keeping AI and smart browser features as a standalone step.
- Decoupled All settings from the guided editor and made Release/ESR behavior explicit, including unsupported AI settings on ESR 140.10.
- Refined English and Russian UI localization, removed future-documentation placeholders, and updated the README for the current product shape.

### Fixed
- Fixed Russian layout issues where profile-library action buttons could overflow.
- Fixed outdated AI-step wording, stale provider-handoff messaging, and terminology drift around All settings and JSON editing.
- Fixed browser UI regressions around mode separation, search, schema-aware rendering, and editor navigation.

### Quality
- Refreshed regression coverage and completed full non-browser plus browser UI passes for the UI/UX release candidate.

## 0.7.5

### Added
- Added Firefox `policies.json` import as a first-class product workflow, including API support, validation, and profile-library import controls.
- Added dedicated profile workspace routes for library, visual editor, and JSON editor flows instead of treating `/profiles` as one combined surface.
- Added CIS Firefox compliance data, mappings, generated hardening layers, merge logic, tooling, and regression coverage.
- Added schema support for Firefox `release-150` and `esr-140.10`, plus migration coverage for stored profile schema versions.
- Added a local Chromium UI audit script and artifact/report flow for guided, advanced, layout, theme, and localization QA.
- Added explicit live Firefox setup guidance and version reporting for the isolated Selenium harness.
- Added dedicated `settings` and `json` profile editor routes, templates, and frontend entrypoints.
- Added a shared editor chrome across guided, settings, and JSON modes with unified save/validate/status controls.
- Added mode-specific regression coverage for DOM structure, route behavior, and multi-tab editor flows.

### Changed
- Moved the project from `0.7.0` to `0.7.5`.
- Promoted Firefox Enterprise `policies.json` to the main user-facing import/export contract and removed internal JSON/YAML handoff routes from the primary product surface.
- Reworked `/profiles` into a library-first workspace and moved editing into dedicated visual and advanced routes.
- Expanded guided coverage across shared-device, trust/auth, extensions governance, privacy hardening, upkeep, site access, home/search, language, AI, and compliance-aware surfaces.
- Aligned guided mode, advanced editing, validation, export, compare, lifecycle, and clone flows around one canonical profile model.
- Updated English and Russian product copy, route titles, and advanced-workflow terminology to match the current split workspace.
- Refreshed schema-update, live-testing, migration, and workspace backlog documentation to match the current repository shape.
- Raised non-live coverage for `app/` to `100%`.
- Refreshed the dependency/tooling stack and aligned the project baseline with Python `3.14`, including CI workflows and local tooling metadata.
- Split the profiles UI into four clear modes: library, guided editor, advanced settings, and JSON editor.
- Switched cross-mode navigation to a new-tab-first model and removed editor-only surfaces from the library route.
- Reduced frontend asset loading per mode so each route boots only the runtime it actually needs.
- Separated guided editing from settings/JSON concerns, moved advanced settings into a searchable settings-only surface, and turned the Monaco workflow into a dedicated JSON mode.

### Fixed
- Fixed route-context and frontend bootstrap regressions that affected locale switching, theme switching, step navigation, profile loading, and split-workspace rendering.
- Fixed multiple guided wizard bugs found during Chromium QA, including AI-step behavior, preset application, language switching, advanced handoff, export-step readiness, and `SearchEngines` document generation.
- Fixed dark-theme surface leaks, desktop/mobile overflow issues, and narrow-viewport regressions across library, guided, review, and advanced surfaces.
- Fixed profile-library state, labels, and rendering glitches that could surface stale fixtures, untranslated action copy, or inconsistent badges on first load.
- Fixed remaining advanced-workflow terminology drift where older `JSON editor` / `JSON editor` copy still appeared.
- Fixed remaining SQLite URL normalization edge cases with explicit regression tests.

### Notes
- This release exposed architectural coupling across the library, guided editor, JSON editor, export/review surfaces, and shared frontend runtime. Those follow-up architecture issues are planned for `0.7.5-dev`.

## 0.7.0

### Added
- Added Firefox `policies.json` import as a first-class product workflow, including API support, validation, and profile-library import controls.
- Added dedicated profile workspace routes for library, visual editor, and JSON editor flows instead of treating `/profiles` as one combined surface.
- Added CIS Firefox compliance data, mappings, generated hardening layers, merge logic, tooling, and regression coverage.
- Added schema support for Firefox `release-150` and `esr-140.10`, plus migration coverage for stored profile schema versions.
- Added a local Chromium UI audit script and artifact/report flow for guided, advanced, layout, theme, and localization QA.
- Added explicit live Firefox setup guidance and version reporting for the isolated Selenium harness.

### Changed
- Moved the project from `0.6.0-dev` to `0.7.0`.
- Promoted Firefox Enterprise `policies.json` to the main user-facing import/export contract and removed internal JSON/YAML handoff routes from the primary product surface.
- Reworked `/profiles` into a library-first workspace and moved editing into dedicated visual and advanced routes.
- Expanded guided coverage across shared-device, trust/auth, extensions governance, privacy hardening, upkeep, site access, home/search, language, AI, and compliance-aware surfaces.
- Aligned guided mode, advanced editing, validation, export, compare, lifecycle, and clone flows around one canonical profile model.
- Updated English and Russian product copy, route titles, and advanced-workflow terminology to match the current split workspace.
- Refreshed schema-update, live-testing, migration, and workspace backlog documentation to match the current repository shape.
- Raised non-live coverage for `app/` to `100%`.

### Fixed
- Fixed route-context and frontend bootstrap regressions that affected locale switching, theme switching, step navigation, profile loading, and split-workspace rendering.
- Fixed multiple guided wizard bugs found during Chromium QA, including AI-step behavior, preset application, language switching, advanced handoff, export-step readiness, and `SearchEngines` document generation.
- Fixed dark-theme surface leaks, desktop/mobile overflow issues, and narrow-viewport regressions across library, guided, review, and advanced surfaces.
- Fixed profile-library state, labels, and rendering glitches that could surface stale fixtures, untranslated action copy, or inconsistent badges on first load.
- Fixed remaining advanced-workflow terminology drift where older `JSON editor` / `JSON editor` copy still appeared.
- Fixed remaining SQLite URL normalization edge cases with explicit regression tests.

### Notes
- This release exposed architectural coupling across the library, guided editor, JSON editor, export/review surfaces, and shared frontend runtime. Those follow-up architecture issues are planned for `0.7.5-dev`.

## Earlier (2025-10-26)

### Added
- ESR-140 / Release-144 schemas, validators, and `/api/validate/{profile}`.
- CRUD for policies with soft delete and restore.
- Export API with JSON/YAML routes:
  - `/api/export/{id}/policies.json|yaml`
- Web UI `/profiles`:
  - Monaco editor (JSON/YAML), create/update/delete/restore, validation.
  - i18n (EN base, RU added), download JSON/YAML buttons.
- CI (GitHub Actions) for `dev` branch:
  - ruff, black, mypy, pytest with coverage ≥85%.
- Alembic migration for `deleted_at` (idempotent, creates table if missing).
- Security headers middleware (CSP, X-Frame-Options, etc.).
- Pre-commit hooks (ruff/black/mypy/pytest).

### Fixed
- JSON serialization for datetimes in export responses (`model_dump(mode="json")`).
- Pydantic v2 deprecations (ConfigDict).
- Package discovery / editable install via `pyproject.toml`.

### Notes
- No Beta; legacy ESR 115/128 dropped (enterprise focus).
- Default language: English; Russian available via `/i18n/ru.json`.
