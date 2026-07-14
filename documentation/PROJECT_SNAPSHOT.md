# BPM Product Documentation Workspace Snapshot

Updated: 2026-07-14
Target BPM version: `0.9.1`
Current completed backlog item: `BPM091-M11-03`
Next backlog item: `BPM091-M11-04`

## Current State

The isolated documentation workspace, pinned toolchain, localized guide-map matrix, key maps,
subject scheme, conditional metadata contract, reproducible static publishing pipeline,
deterministic release-candidate packaging policy, browser-verified accessible return-safe hierarchical duplicate-free static portal shell/theme, generated
manifest/target-map contracts, maintainer authoring runbooks, case-oriented User Guide map,
localized User Guide corpus, DITA localization workflow, Firefox/CIS topic models, Firefox/CIS generated skeletons, Firefox examples/channel differences, Firefox Policy/CIS/API six-locale parity gates, CIS mapping/source-attribution/manual-review/workflow topics, API integration audience/pattern/profile-lifecycle/import-export/validation-gate/health-handshake/scenario/reusable-example topics plus OpenAPI drift gates, six-locale Firefox Policy/CIS/API topics, an Administrator/DevOps Guide map/key/root contract for source deployment, operations, updates, integrations, production/HA/reverse-proxy boundaries, validation fixtures, and final six-locale admin localization review, an API/integration re-home audit from API/User Guide content into Administrator/DevOps ownership, a manifest-validated locale-aware `/help/` runtime bridge, a localized BPM header documentation link, five manifest-backed contextual help links, manifest-backed policy/CIS/validation/import-export deep help icons, localized unavailable/stale/incomplete documentation states, focused `/help/` accessibility/responsive/CSP/theme integration contracts, deterministic six-locale static search indexes/UI with reviewed normalization/aliases/ranking/facets/filters/quality/integrity gates and non-AI boundary copy, isolated documentation test suite boundaries, focused documentation make targets, a documentation-only source fast loop, isolated documentation coverage reporting, a compact deterministic fixture catalog, ignored failure diagnostics, a generated subsystem snapshot, a release-blocking documentation gate wired into `make test-release`, a browser-backed documentation portal smoke for BPM links, an ignored dev-site install target for maintainer review through `make dev`, maintainer-accepted manual QA with known issues deferred to the next version, a final content coverage audit with explicit release blockers, a refreshed implemented-product README, and a documentation-only debugging protocol exist.
`BPM091-M5-05` visual QA is accepted after the M7-05 full 36-row localized User Guide screenshot
regeneration, contact-sheet review, and focused full-size DE/FR/ES guided-search review.
`BPM091-M7-01` visible-English inventory is accepted and classifies non-English localized UI,
documentation, search/navigation, screenshot, caption, and alt-text findings as replace,
allowlisted technical English, brand, identifier, command/path/API, abbreviation, or false positive.
`BPM091-M7-02` terminology authority is accepted and links every replacement finding to Pontoon,
SUMO, or maintainer-fallback terminology before source locale strings are changed.
`BPM091-M7-03` source replacement is accepted and removes the M7-01 forbidden fragments from
localized source and runtime catalogs while preserving allowlisted technical English.
`BPM091-M7-04` anti-anglicism guard is accepted and prevents regressions for the closed product
catalog replacement findings, the localized documentation topics corrected in this pass, and the
technical-English allowlist fixture behavior.
`BPM091-M7-05` human-oriented locale QA is accepted for the reviewed non-English User Guide
screenshot surfaces, closes the localized screenshot release blockers, records remaining reviewed
English as brands, abbreviations, identifiers, commands/paths/APIs, or false positives, and keeps
broader non-screenshot locale phrasing debt outside this task under the M7-04 known-debt policy.
`BPM091-M8-01` topic-section hierarchy audit is accepted and records that `user-guide` and
`administrator-guide` need section grouping, while `cis-settings-guide`, `firefox-policy-guide`,
and `api-integration-guide` remain short enough for the current flat document-topic list.
`BPM091-M8-02` topic-section taxonomy is accepted and assigns every affected `user-guide` and
`administrator-guide` topic to exactly one stable localizable section without changing topic IDs,
DITA keys, canonical URLs, manifest topic IDs, UI target IDs, search document IDs, or contextual
help target IDs.
`BPM091-M8-03` section-node implementation is accepted: taxonomy-owned documents now render
`root -> document -> section -> topic`, direct topic URLs expand both owning ancestors, short
documents retain `root -> document -> topic`, and topic URLs and manifest identities remain stable.
`BPM091-M8-04` section-label localization is accepted and gives all 21 taxonomy keys locale-owned
labels in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`, with exact key/locale parity and no
non-English runtime fallback to the canonical English value.
`BPM091-M8-05` section-level navigation verification is accepted after the six-locale Selenium
smoke covered root focus, document/section expansion, active-topic ancestors, mouse and keyboard
controls, parent/root return, narrow layout, Administrator Guide sections, and flat short guides.
`BPM091-M6-01` User Guide sufficiency review is accepted for all 62 task and 10 troubleshooting
topics across the source locale plus five-locale structural parity, with eight representative
Selenium workflows, four save/export/conflict simulations, and no remaining User Guide blockers.
`BPM091-M6-02` Firefox Policy and CIS guide sufficiency review is accepted for representative
simple, complex, Release-only, managed-preference, CIS L1/L2, manual-review, provenance-only,
mapping-example, and cross-guide-link decisions, with no remaining release blockers and explicit
live-Firefox, certification, and exception-record boundaries.
`BPM091-M6-03` Administrator/DevOps sufficiency review is accepted across all 44 topics and ten
navigation sections after current API and repository behavior checks, while intentionally keeping
release blockers for exact Linux/WSL source-install evidence (`M6-05/M6-06`) and stale 0.9.0
Administrator topic metadata/wording (`M12-02`).
`BPM091-M6-04` Linux distribution selection is confirmed by the maintainer and freezes command
validation targets for Ubuntu 26.04 LTS, Debian 13.5, Fedora Linux 44, Linux Mint 22.3, and the
Manjaro stable branch after the 2026-06-26 stable update, with the author/validate handoff corrected
to `M6-05/M6-06`.
`BPM091-M6-05` exact Linux source-install procedures are authored for all five frozen targets in
all six locales, with invariant command blocks, target-owned package/Python strategies, guarded Git
ref input, migration, documentation build, foreground start, probes/UI/log checks, and explicit
stop boundaries; execution evidence is assessed by `M6-06`.
`BPM091-M6-06` validation is accepted with an explicit release blocker: Ubuntu 26.04 runtime,
migration, documentation, probes, UI, shutdown, and shared CPython checksum evidence pass, while
Debian 13.5, Fedora 44, Linux Mint 22.3, and Manjaro stable remain simulation-only and all five
targets still require complete clean-host transcripts before release.
`BPM091-M6-07` sufficiency drift protection is accepted: one fail-closed contract normalizes the
User Guide, Firefox/CIS, and Administrator reviews, checks required procedure fields, localized
commands, observable results, recovery and guide links, Linux command blocks, drift/evidence paths,
and focused pytest nodes. The first run corrected stale All Settings, Firefox schema, and recovery
references, and the focused M6 bundle passes 66 tests.
`BPM091-M9-01` All Settings documentation-target audit is accepted: all 120 current Release/ESR
policies resolve to generated `policy:*` targets, all 62 known managed preferences are explicitly
recorded with their M9-01 missing-target baseline, and unknown imported policies/preferences have
explicit `unsupported_unknown` no-link dispositions. Editor-navigation targets are recorded as a
separate namespace that row-help code must never treat as documentation links; the focused audit
bundle passes 18 tests.
`BPM091-M9-02` manifest target generation is accepted: the generated map contains all 120 policy
targets and all 62 exact, case-sensitive known-preference targets backed by the localized managed-
preference safe-review reference. Missing, extra, removed, or case-changed identities fail closed;
editor aliases are not emitted as documentation identities. Focused contracts pass 28 tests,
manifest generation plus target contracts pass 7 tests, and full validation/build produce 519
targets. The known-preference audit finding is closed; the editor/documentation target separation
guard remains open for row rendering and unavailable-target handling.
`BPM091-M9-03` All Settings row rendering is accepted: settings routes embed only validated
manifest-resolved policy/preference locale maps, and list plus search results render the familiar
circled `i` as a sibling of the primary selection button. Stable fixed-width columns protect long
labels and row height across desktop/mobile, help clicks do not select rows, and collapsed,
expanded, paginated, Review, Configured, Catalog, and search paths retain links. The focused
resolver/route/Node-runtime/keyboard/screen-reader/CSS/responsive bundle passes 42 tests and lint
passes; explicit unsupported and unavailable no-link states remain assigned to M9-05.
`BPM091-M9-04` All Settings row-help localization is accepted: all six product locales own
matching `{setting}` templates for open, missing, unavailable, raw-not-applicable, and unsupported-
unknown states, and list/search links use the dedicated open template for title and accessible
name. Focused localization/rendering/anti-anglicism checks pass 41 tests, locale catalogs are
reproducible, locale-quality reports no findings, and lint passes.
`BPM091-M9-05` safe no-link handling is accepted: unknown and unrecognized raw entries, missing
manifest targets, and unavailable, stale, incomplete, or incompatible documentation artifacts
render localized noninteractive circled-`i` indicators without broken `href` values in both list
and search results. Valid policy and known-preference links remain manifest-backed. The broader All
Settings bundle passes 58 tests, the documentation runtime-route suite passes 21 tests, lint
passes, and both M9 audit findings are closed.
`BPM091-M9-06` All Settings row-help verification is accepted: expanded DOM coverage protects all
artifact dispositions, and the dedicated Chromium smoke covers policies, known preferences,
unknown/raw rows, all three modes, list/search controls, Russian and long-label German copy,
layout, keyboard focus, Enter activation, and localized `noopener` new-tab navigation. Focused
contracts, the browser test, and lint pass; Milestone 9 is complete.
The remaining backlog is reprioritized: M10 now owns independent sidebar scrolling, removal of the
obsolete standalone API guide, UI-catalog-authoritative topic names, and a full five-locale visible-
English review; M11 owns privileged disposable Docker validation for the five frozen Linux targets,
conditional genuine-host Windows 10/11 WSL evidence, and retained-environment handoff. Maintained documentation and
final quality move to M12 and M13. The next task is the bounded M10-01 audit; Docker is not installed
until M11-02 receives separate maintainer approval after the M11-01 safety contract.
`BPM091-M10-01` remaining-defect audit was accepted with four initially open release blockers. Browser
measurements confirm that the 183-node expanded tree creates 12,329 px and 10,117 px sidebars at
desktop/narrow viewports with visible overflow, no height bound, and no writable scroll position.
All 13 former API topics have existing six-locale Administrator Guide owners, while a redundant
one-topic API compatibility guide remains actively published. Across 815 non-English DITA/map
sources, deterministic XML-peer comparison records 2,893 unchanged English prose fragments in 208
files and source-language UI names in 225 files. Five focused contracts validate every recorded
fragment, UI-name source, API owner, count, and baseline measurement.
`BPM091-M10-02` independent sidebar scrolling is accepted. The sticky desktop tree is bounded to
the dynamic viewport, the non-sticky narrow tree to 70dvh/32rem, and both use their own contained
vertical scrolling with a stable visible scrollbar and wrapped labels. Tree focus now uses
`preventScroll` plus sidebar-only auto-reveal, keeping direct deep topics and Arrow/Home/End focus
visible without moving the article viewport. The dedicated 1366x1000/390x900 Chromium smoke and
the existing six-locale navigation smoke pass; 23 focused non-browser tests, lint, JS syntax, JSON,
and diff checks pass. The sidebar finding is closed; M10-03 is next with three blockers remaining.
`BPM091-M10-03` standalone API-guide removal is accepted. The active six-locale portal now contains
four guides; the obsolete guide maps, compatibility landing topics, portal references, keydefs,
search filters, and localized labels are removed. All 15 API operation targets resolve directly to
existing Administrator Guide topics and fail closed if an owner is missing. Full build and dev
installation succeed, and the six-locale Chromium navigation smoke passes. The API-guide finding is
closed; M10-04 is next with two blockers remaining.
`BPM091-M10-04` interface-name authority is accepted. Five interface families map 39 maintained
runtime catalog keys across all six locales, eleven historical documentation aliases have canonical
UI keys, and five technical/structural term classes are explicitly non-UI. Three malformed or
English-carryover runtime values are recorded as fail-closed M10-05 prerequisites. The authority
subtask is closed; M10-05 is next while the UI-name replacement blocker remains open.
`BPM091-M10-05` interface-name replacement is accepted. The authority now covers 39 runtime keys
and 11 documentation aliases; 2,080 source UI-name occurrences are replaced across all six locales.
Three original catalog findings and seven additional malformed values are corrected before DITA,
navigation, breadcrumb, and search generation. Installed document fields contain no forbidden UI
aliases; `profile library` remains only as a query-compatible search alias. All 625 documentation
contracts, full dev installation, and the six-locale Chromium navigation smoke pass. The UI-name
blocker is closed; M10-06 is next with only the visible-English prose blocker remaining.
`BPM091-M10-06` visible-English prose review is accepted. All 805 non-English DITA/map sources are
covered; the full structural pass replaces 10,410 visible blocks in 764 aligned files, and 36
structurally different source files receive a separate review. Exact-peer comparison reports no
release-blocking long English carryover. The remaining 28 high-signal scan
candidates are reviewed commands, paths, API/model/JSON/CIS identifiers, or locale-language false
positives, and no temporary translation marker remains. All 630 documentation contracts and six
browser smoke scenarios pass. The browser gate now reuses one generated portal from a disk-backed
pytest base directory and limits Chromium renderer/V8 memory instead of accumulating large copies
in RAM-backed `/tmp`. The final M10 audit blocker is closed.
`BPM091-M10-07` shared navigation publication is accepted. Every locale now owns one deterministic,
manifest-backed `navigation.json`; generated HTML contains only an accessible bounded host and
localized root fallback. The shared runtime validates and renders the same-origin source, restores
the current root/document/section/topic path, preserves existing tree interaction and independent
scrolling, and fails into a localized usable state when the source is absent. Schema, unit,
contract, JavaScript syntax, and focused six-locale Chromium navigation checks pass; M10-08 is next.
`BPM091-M10-08` fail-closed regression coverage is accepted. Ten release gates protect retired
standalone API-guide structure, Administrator API ownership, per-locale navigation source and
manifest integrity, compact HTML hosts, localized labels and UI terms, complete visible-English
review scope, and live bounded exceptions. File and archive validators now compare every
navigation hierarchy, label, URL, order, and node count with manifest/source authority even when a
tampered artifact carries a recomputed hash. Mutation probes reject stale, missing, fallback,
unsafe, and embedded-tree states while approved technical tokens remain valid; M10-09 is next.
`BPM091-M10-09` six-locale browser QA is accepted. A maintained matrix ties the rendered All
settings sample to exact DITA prose and runtime UI terms. Chromium verifies successful and failed
navigation loading, only the four current guide nodes, direct-topic activation, root/parent/history
return, desktop/narrow layout, localized failure recovery, and no frozen English sentence in each
non-English sample. Native wheel and keyboard input scroll every locale's representative long tree
in both viewports without moving the article. The complete six-scenario browser gate passes in one
disk-backed Chromium process. Milestone 10 is complete; M11-01 is next.
`BPM091-M11-01` is accepted by the maintainer. Its repeated read-only baseline records Docker,
containerd, sockets, group membership, repository/key, data roots, and daemon configuration as
absent on Ubuntu 26.04 x86_64 and confirms 224,906,842,112 free bytes. The contract freezes immutable registry identities for
Ubuntu, Debian, Fedora, and Manjaro; a signed official ISO-derived Mint rootfs; one-container
CPU/RAM/storage limits; no user-data, production, host-network, port, bind-mount, Docker-socket, or
secret access; reviewed evidence paths; failed-install rollback; M11-resource inventory/handoff; and
persistent Docker retention without Docker-group membership. At M11-01 acceptance no privileged
command or image pull had run; M11-02 subsequently performed the approved installation.
`BPM091-M11-02` is accepted. Exactly five Docker packages were installed from the signed official
Ubuntu `resolute/amd64` repository without recommendations or removals. Docker 29.6.1 and
containerd are active/enabled; the root-owned `0660` socket belongs to a memberless `docker` group,
and the maintainer retains no unprivileged Docker access. A labeled amd64 `hello-world` container
passed with the approved CPU/RAM/swap/PID/security/network boundary, after which its container,
image, and network were removed. Firewall configuration hashes and unrelated persistent service
settings are unchanged, no M11-labeled resource remains, more than 200 GiB is free, and Docker
Engine remains installed for M11-03 and future project work.
`BPM091-M11-03` is accepted. The retained five-target harness extracts exact DITA command plans,
isolates every attempt's evidence, records container adapters separately, enforces one-container
CPU/RAM/storage/network boundaries, stops every attempt, and has no resource-deletion path. The
first Ubuntu attempt remains as evidence of the corrected PID 1 lifecycle defect; a fresh second
Ubuntu 26.04 attempt passed and exited `0`. The official Linux Mint 22.3 Cinnamon ISO signature,
fingerprint, and pinned SHA-256 were verified before its Zena rootfs was imported; a fresh Mint
identity container passed and exited `0`. Four stopped containers, the Ubuntu and Mint images, and
the dedicated network remain available for later experiments at about 3.23 GB retained usage.
Generated output and the dev-installed site are ignored; `make dev` refreshes the current local documentation build under `app/documentation/site` through `make docs-install-dev`, while release package extraction remains a separate gate. Full application/documentation-owned coverage, non-browser documentation release, browser smoke gates, localized User Guide screenshot capture, and localized User Guide screenshot integration are green.

Implemented:

- exact DITA locale source directories for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`;
- matching localized screenshot source directories, the minimal BPM 0.9.1 User Guide screenshot matrix, frozen capture-state contract, dedicated capture command, 36 normalized PNG source assets with enforced dimensions, filename pattern, metadata-free chunks, size budgets, orphan detection, cross-locale uniqueness, stable DITA screenshot keydefs, localized captions/alt text, published locale-local screenshot asset links, accepted visual QA evidence, a reviewable visible-English inventory for all non-English locales, terminology authority notes, accepted source/runtime replacement evidence, anti-anglicism regression checks, and human-oriented locale QA evidence for the M7 cleanup pass;
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
- four independently buildable guide maps and one stable-order portal aggregate for every locale;
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
- deterministic post-build portal shell with skip link, landmarks, tree-derived breadcrumbs, sidebar-only
  hierarchical navigation tree with browser-smoked root/guide/topic return behavior, locale switchers, version/status context, exact locale `html lang`, CSP-friendly static HTML, accessible
  local search UI, and first-party responsive/dark/light/forced-colors/reduced-motion/print CSS covering code, tables, notes, figures, and screenshots.
- a topic-section hierarchy audit for the next navigation tree layer, with map-derived counts,
  a twelve-topic flat-list threshold, locale parity checks, and explicit no-URL-change invariants.
- a topic-section taxonomy for `user-guide` and `administrator-guide`, with stable section IDs,
  label-key shapes, one-owner topic assignment, source-order preservation, and a maximum of twelve
  topics per section.
- generated section tree nodes for `user-guide` and `administrator-guide`, with taxonomy-owned
  branches, current-topic ancestor expansion, mouse/keyboard collapse behavior, unchanged direct
  topic links, and flat navigation retained for the three short documents.
- locale-owned section labels for every taxonomy branch in all six locales, with fail-closed
  key/locale parity, canonical-English consistency, product terminology checks, and no English
  fallback for non-English trees.
- section-level contract, unit, and Chromium/Selenium coverage across all six locales, including
  roving focus, `ArrowRight`, `ArrowLeft`, `Enter`, `Space`, click, direct topic expansion,
  selected-ancestor protection, parent/root return, narrow layout, both grouped documents, and a
  short flat document.
- schema-valid generated `manifest.json`/`ui-target-map.json`, 256 current topics, stable anchors,
  policy/CIS/API/capability/topic targets, hashes, and six reproducible per-locale search indexes with normalized tokens, aliases, ranking fixtures, deterministic facets, quality/performance fixtures, integrity/drift reports, filter counts, URL-state fixtures, and localized empty-result recovery.
- maintainer runbooks for one-topic authoring, DITA localization workflow, screenshots, Firefox/CIS/API inventory refresh, Firefox schema and CIS benchmark/mapping drift gates, link/manifest changes, review, and publishing checks.
- case-oriented User Guide coverage map grouping all 89 planned user topics and all 106 inventoried
  user capabilities into eight user-intent sections, with matching localized DITA map section
  headings for all six locales.
- closed User Guide coverage gate against README capabilities, routes, templates, locale catalogs, API boundary behavior, and browser smoke-flow evidence.
- accepted User Guide sufficiency evidence resolving all 72 action/recovery topics to explicit
  prerequisites, ordered steps, observable results, recovery paths, drift sources, focused checks,
  and successful browser or deterministic simulation execution records.
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
- `product-documentation-content-coverage-audit-0.9.0.{json,md}` records the final M14-07 audit:
  product/admin/Firefox/CIS/API/locale/manifest/search/portal domains are covered; its former
  screenshot visual QA blocker is closed by the accepted 0.9.1 M7-05 locale QA evidence.
- `BPM090-M13-01` is closed by maintainer manual review acceptance: many documentation UX/content issues remain known, but their correction is deferred to the next product version rather than blocking the 0.9.0 final quality milestone.
Not implemented yet: Firefox Policy/CIS and Administrator/DevOps sufficiency reviews, five-distribution Linux source-install coverage, sufficiency drift checks, and release package extraction policy.

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
| Accessibility/security/CSP/theme | `docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md`, `docs/architecture/product-documentation-visual-theme-contract-0.9.1.md`, `docs/architecture/bpm-documentation-theme-token-audit-0.9.1.md` |
| Final content coverage audit and sufficiency protocol | `docs/architecture/product-documentation-content-coverage-audit-0.9.0.json`, `docs/architecture/product-documentation-content-coverage-audit-0.9.0.md`, `documentation/config/documentation-sufficiency-review-protocol-0.9.1.json`, `docs/architecture/user-guide-sufficiency-review-0.9.1.json`, `documentation/tests/contract/test_user_guide_sufficiency_review.py` |
| User capability coverage | `docs/architecture/product-user-capability-inventory-0.9.0.md` |
| User Guide case map and screenshot matrix | `documentation/config/user-guide-map-0.9.0.json`, `documentation/config/user-guide-screenshot-matrix-0.9.1.json`, `documentation/config/user-guide-screenshot-visual-qa-0.9.1.json` |
| Search corpus/result contract | `documentation/config/search-corpus-and-results-0.9.0.json` |
| Search/navigation/help UI contracts and guardrails | `documentation/config/search-facets-filters-0.9.0.json`, `documentation/config/search-ui-filter-contract-0.9.1.json`, `documentation/config/navigation-tree-contract-0.9.1.json`, `documentation/config/topic-section-hierarchy-audit-0.9.1.json`, `documentation/config/topic-section-taxonomy-0.9.1.json`, `documentation/config/topic-section-labels-0.9.1.json`, `documentation/config/all-settings-row-help-link-contract-0.9.1.json`, `documentation/config/documentation-polish-guardrails-0.9.1.json`, `documentation/tests/contract/test_topic_section_hierarchy_audit.py`, `documentation/tests/contract/test_topic_section_taxonomy.py`, `documentation/tests/contract/test_topic_section_labels.py` |
| Localization terminology and visible-English cleanup | `documentation/config/locale-visible-english-inventory-0.9.1.json`, `documentation/config/locale-terminology-authority-0.9.1.json`, `documentation/config/locale-anglicism-replacement-0.9.1.json`, `documentation/config/locale-anti-anglicism-guard-0.9.1.json`, `documentation/config/locale-human-qa-0.9.1.json`, `documentation/tests/contract/test_locale_visible_english_inventory.py`, `documentation/tests/contract/test_locale_terminology_authority.py`, `documentation/tests/contract/test_locale_anglicism_replacement.py`, `documentation/tests/contract/test_locale_anti_anglicism_guard.py`, `documentation/tests/contract/test_locale_human_qa.py` |
| Search quality/integrity contracts | `documentation/config/search-quality-performance-0.9.0.json`, `documentation/config/search-integrity-drift-0.9.0.json` |
| Documentation coverage policy | `documentation/config/coverage-policy-0.9.0.json` |
| Documentation diagnostics policy | `documentation/config/diagnostics-policy-0.9.0.json` |
| Documentation fixture catalog | `documentation/fixtures/fixture-catalog-0.9.0.json` |
| Administrator validation and Linux source-install selection | `documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json`, `docs/architecture/linux-distribution-selection-0.9.1.md` |
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
`make test-docs-ui` launch Chromium/Selenium and require immediate sandbox escalation. `make dev` promotes the current local build into ignored `app/documentation/site` through `make docs-install-dev` before starting the app for `/help/` review; it is not release extraction evidence. Use `./.venv/bin/python documentation/tools/capture_user_guide_screenshots.py` for the dedicated screenshot capture command. No `make docs-screenshots-check` target exists yet.
