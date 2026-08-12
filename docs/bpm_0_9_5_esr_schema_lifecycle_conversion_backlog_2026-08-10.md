# BPM 0.9.5 ESR Schema Lifecycle And Conversion Backlog

Date: 2026-08-10

Target BPM version: `0.9.5`

Epic ID: `BPM095`

Release risk: high. This epic adds a fourth independently generated Firefox policy schema, changes
the default and recommendation semantics for ESR channels, introduces explicit cross-channel
conversion, and changes the database-upgrade rule for retired ESR channels. A defect could silently
drop policy data, validate a profile against the wrong Firefox line, leave an upgraded database on
an unsupported channel, or recommend a migration that the profile cannot complete safely.

This backlog takes BPM from the current `0.9.4` implementation to a release-ready `0.9.5`. It adds
the Firefox ESR 115 line for organizations that still operate legacy systems, provides deterministic
conversion between every supported Release/ESR channel, recommends the latest supported ESR for
profiles on older ESR lines, and makes retirement-to-successor migration a required part of future
schema bumps.

Model assignments use the current
[GPT-5.6 model guidance](https://developers.openai.com/api/docs/models), rechecked on 2026-08-10:
Luna for deterministic maintenance, Terra as the normal engineering default, and Sol only for the
cross-system data-safety decisions where a wrong design could corrupt stored policy documents.
Reasoning effort is selected independently.

## Scope Summary

- Move active BPM version, package, editable-install, UI/generated version, test, and changelog
  surfaces from `0.9.4` to `0.9.5`; keep README version-neutral.
- Add Firefox ESR 115 as an independent, provenance-pinned BPM schema line. The exact maintained
  ESR 115 patch, channel string, policy-template source, inputs, and checksums are selected from
  official Mozilla evidence during execution rather than guessed in this planning document.
- Extend the schema catalog with explicit ESR-line identity, ordering, support state, latest-ESR
  role, and retirement successor metadata. These meanings must not be inferred from tuple order,
  display labels, the default channel, or a singular `CURRENT_ESR_SCHEMA_CHANNEL` alias.
- Implement previewable, deterministic conversion between every ordered pair of supported ESR and
  Release channels, including Release-to-ESR, ESR-to-Release, older-to-newer, and newer-to-older.
- Never silently delete, coerce, or hide an unsupported policy/value. A manual conversion with a
  blocking incompatibility stays unapplied until the user resolves it.
- Show an actionable UI recommendation for every profile on a supported ESR line older than the
  latest supported ESR. Profiles on Release or already on the latest ESR do not receive that ESR
  recommendation.
- When a future schema bump removes an ESR line from support, migrate every profile on that retired
  line through Alembic to the explicitly declared immediate newer supported ESR successor. For
  example, retirement of ESR 140 migrates its profiles to ESR 153.
- Update the Firefox schema update runbook and tooling so an added/retained/retired channel matrix,
  lossless-conversion proof, successor map, profile migration, documentation drift, locale drift,
  CIS impact, and live-browser coverage move together.
- Update product documentation, all six locales, API guidance, schema inventories, contextual help,
  screenshots when affected, README durable product facts, and release evidence.

## Official ESR 115 Planning Evidence

Mozilla's maintained
[Firefox support article for Windows 7, 8, and 8.1](https://support.mozilla.org/en-US/kb/firefox-users-windows-7-8-and-81-moving-extended-support)
states on 2026-08-10 that Firefox 115 is the last supported Firefox line for those systems and that
ESR updates are planned through March 2027, after which Mozilla will re-evaluate support. Mozilla's
[Firefox version feed](https://product-details.mozilla.org/1.0/firefox_versions.json) exposes ESR
115 as a separate maintained line.

This is external release evidence, not a BPM guarantee. The task that pins the ESR 115 artifact
must recheck Mozilla's current support statement, exact ESR patch, policy-template provenance, and
checksums. If Mozilla changes the date or patch before implementation, BPM documentation must state
the newly verified fact and must not preserve this planning observation as a permanent promise.

## Current-State Assessment

- `app/core/schema_channels.py` declares three supported first-class channels:
  `release-153`, `esr-153.0`, and `esr-140.13`. It records `family`, but not stable ESR-line
  identity, support state/end, latest-ESR role, or retirement successor.
- `DEFAULT_SCHEMA_CHANNEL` and `CURRENT_ESR_SCHEMA_CHANNEL` currently resolve to `esr-140.13`, while
  `esr-153.0` is the newest supported ESR. The product has no explicit `latest ESR` concept from
  which a recommendation can safely derive.
- `tools/firefox_schema_targets.json` and the pinned input manifest generate the three bundled
  schemas independently. No ESR 115 target or bundled schema exists.
- Schema loaders, validation, selectors, header data, import/export, All settings, Guided review,
  locales, documentation inventories, and live Firefox automation are coupled to the current
  three-channel matrix.
- A generic profile PATCH can submit `schema_version` and `flags` together and validates only the
  resulting document. BPM has no conversion planner, compatibility preview, conversion recipe
  registry, dedicated API result, or UI that explains retained, changed, and blocked values.
- The active Firefox 153 dual-ESR contract deliberately forbids automatic cross-ESR migration.
  BPM 0.9.5 must supersede that rule narrowly: a still-supported older ESR remains an explicit user
  choice, while a removed ESR receives an automatic, declared successor during the schema bump.
- Alembic owns stored-channel upgrades and currently applies immutable, explicit same-line channel
  maps. Startup and profile GET paths are read-only with respect to legacy normalization. This
  ownership must be preserved.
- The Firefox schema update runbook already requires an explicit support/migration table and warns
  against guessing from the highest version. It does not yet require lifecycle roles, the latest-ESR
  recommendation, pairwise conversion evidence, or automatic successor migration for a retired ESR.
- Product documentation and Firefox live-test matrices describe the current three channels and will
  drift if ESR 115 is added only to the backend catalog.

## Approved Product And Lifecycle Decisions

1. A schema channel is a first-class artifact with its own upstream provenance and exact Mozilla
   version. ESR 115 is never created by copying or relabelling ESR 140, ESR 153, or Release JSON.
2. `latest ESR` means the newest supported ESR line in the reviewed lifecycle catalog. It is a
   distinct role from Release, display order, historical channel aliases, and migration successor.
3. New profiles default to the latest supported ESR after this epic. An older supported ESR is
   selected explicitly for an organization's compatibility requirement.
4. A profile on an older but still-supported ESR is never moved automatically. BPM shows a
   recommendation and requires preview plus explicit confirmation.
5. Manual conversion supports every ordered pair of currently supported channels. An unchanged
   value may pass through, an approved recipe may transform a value deterministically, and a value
   without a lossless target representation is a blocker. Silent deletion and best-effort coercion
   are forbidden.
6. A removed ESR is different from an older supported ESR. Removal requires an explicit successor
   map to the immediate newer supported ESR line. The planning examples are ESR 115 to ESR 140 and
   ESR 140 to ESR 153 when those are the adjacent supported lines at retirement time.
7. A schema bump may retire an ESR only after proving that every source-schema-valid policy shape
   has a lossless successor representation or an approved total conversion recipe. If that proof
   fails, the bump fails before database mutation; it does not strand, invalidate, or truncate
   customer profiles.
8. The successor map is reviewed in source and materialized into an immutable Alembic revision.
   Runtime code does not infer a migration destination from a maximum version, tuple position, UI
   default, or network response.
9. Alembic remains the only owner of automatic stored-profile channel migration. Startup, list,
   GET, validation, and UI rendering remain unable to rewrite persisted profiles.
10. Profile conversion uses optimistic revision checks and one transaction. A stale preview, stale
    profile revision, unsupported target, or blocked conversion leaves the profile unchanged.

## Non-Goals And Assumptions

- BPM schema support does not extend operating-system vendor support and does not claim that legacy
  Windows is safe. Product documentation must preserve Mozilla's security/support caveats.
- Do not promise ESR 115 support beyond Mozilla's currently verified window. Recheck the source at
  the implementation and documentation tasks that consume it.
- Do not download schemas or Firefox binaries during product startup, page load, validation,
  conversion, or profile migration. Sources remain pinned, checksum-verified release inputs.
- Do not treat Release and ESR schemas as aliases even when their current policy fingerprints match.
- Do not automatically move a profile between two still-supported ESR lines, including at ordinary
  startup or when the latest-ESR role changes.
- Do not add an option that discards incompatible policies to force a conversion. Resolution is a
  separate explicit profile edit followed by a fresh preview.
- Do not rewrite immutable historical Alembic revisions, archived evidence, old changelog entries,
  or historical policy compatibility metadata.
- Do not change CIS benchmark provenance. Revalidate how existing CIS layers and compliance state
  behave on ESR 115 and after conversion, and state unsupported combinations truthfully.
- Do not reintroduce a separate Advanced editor. Conversion belongs to the existing Library,
  Guided, All settings, and JSON/profile API boundaries.
- README may change only for durable current product facts such as supported schema lines and
  conversion behavior. It must not contain a `0.9.5` anchor, active-target statement, planned work,
  or release-history summary.
- Product source, visible UI copy, changelog, and maintained documentation remain English-first;
  the maintainer-facing execution conversation may remain Russian.

## Milestone 1: Version Transition And Release Anchors

Goal: establish `0.9.5` as the single active BPM product version and refresh release metadata before
feature work, without turning README into a version surface.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M1-01` | Update active product version surfaces to `0.9.5`. | Move package metadata, runtime/OpenAPI/UI/generated version data, active architecture/release surfaces, and current-version assertions from `0.9.4` to `0.9.5`. | GPT-5.6 Luna | Light | All nonhistorical version surfaces agree on `0.9.5`; historical evidence and migrations remain unchanged; README receives no target-version marker. |
| `BPM095-M1-02` | Refresh editable-package metadata. | Reinstall the local editable package and remove stale environment metadata after the version transition. | GPT-5.6 Luna | Light | `pip show browser-policy-manager`, `importlib.metadata.version`, and a clean editable reinstall report `0.9.5`; local `*.egg-info` is not committed. |
| `BPM095-M1-03` | Recheck external dependency and toolchain currency. | Review Python/base and optional dependencies, frontend vendor packages, documentation tooling, test/dev tools, Firefox binaries, and geckodriver against official sources. | GPT-5.6 Terra | High | A reviewed matrix records declared/installed/current versions, licenses, advisories, platform constraints, dispositions, and focused compatibility checks; no floating update is accepted; any materially uncertain audit prints flushed phase/component progress. |
| `BPM095-M1-04` | Apply approved dependency and lock refreshes. | Update only M1-03-approved constraints, locks, vendor outputs, pre-commit pins, licenses, and checksums. | GPT-5.6 Terra | High | Lock/vendor integrity, `npm ci`, `pip check`, license/advisory checks, and focused compatibility tests pass; deferrals remain explicit; long install/build steps print real completed/total unit progress. |
| `BPM095-M1-05` | Open the `0.9.5` changelog entry. | Add an English release landing section for ESR 115, conversion, recommendations, and lifecycle migration while preserving older history. | GPT-5.6 Luna | Light | The entry contains only approved or completed claims and all older release history remains intact. |
| `BPM095-M1-06` | Guard version and package consistency. | Add focused contracts for project, wheel/sdist, installed/runtime, served documentation, and README version-neutrality. | GPT-5.6 Terra | Medium | Tests fail on active `0.9.4` leakage, package/runtime disagreement, stale served documentation version, or README release prose while allowing historical `0.9.4` context. |

## Milestone 2: Schema Lifecycle, Conversion, And Safety Contracts

Goal: define one reviewed source of truth for supported channels, manual conversion, recommendation,
and retirement migration before changing generated schemas or stored data.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M2-01` | Inventory the current schema-channel surface. | Map catalog constants, generated inputs/outputs, loaders, validators, profile storage, API, editors, locales, CIS, documentation, runbooks, tests, and live-browser ownership. | GPT-5.6 Luna | Medium | Every current three-channel assumption has an owner, planned disposition, and focused verification route; generated, historical, and active references are distinguished. |
| `BPM095-M2-02` | Establish the verified four-channel support matrix. | Recheck official Mozilla support/version evidence and pin the exact ESR 115 patch, channel ID, UI label, policy-template source, input URLs, and checksums beside Release 153, ESR 153, and ESR 140. | GPT-5.6 Terra | High | The reviewed matrix proves independent provenance for all four rows, records Mozilla's current ESR 115 support caveat/date, and does not infer an artifact from a product label. |
| `BPM095-M2-03` | Define the schema lifecycle catalog contract. | Specify stable ESR-line identity, exact artifact version, family, ordering, support state, latest-ESR role, default role, successor, labels, and serialization/API fields. | GPT-5.6 Terra | Extra High | One fail-closed contract distinguishes supported older, latest, and retired ESR lines; default/recommendation/migration meanings cannot drift or depend on tuple order; the Firefox 153 dual-ESR contract is explicitly superseded only where 0.9.5 changes it. |
| `BPM095-M2-04` | Define the pairwise conversion contract. | Specify the plan/result model, compatibility classes, deterministic transformations, blocker semantics, preview identity, compliance handling, and all ordered source/target pairs. | GPT-5.6 Sol | Extra High | The contract proves no-silent-loss behavior for policy documents and profile metadata across API, UI, and migration consumers; Sol is required because one mistaken cross-system rule could silently corrupt stored enterprise policy data. |
| `BPM095-M2-05` | Define retired-ESR migration safety. | Specify successor selection, total-convertibility proof, backup/preflight, transactionality, idempotency, interruption behavior, downgrade boundary, and SQLite/PostgreSQL evidence. | GPT-5.6 Terra | Extra High | A retired ESR cannot leave the supported matrix without an explicit immediate-newer successor and lossless proof; failure occurs before mutation; ESR 140 to ESR 153 is a required fixture. |
| `BPM095-M2-06` | Classify new UI copy and interaction states. | Apply the active UI-copy classification contract to recommendation, preview, blockers, confirmation, success, stale-revision, unavailable, and recovery states. | GPT-5.6 Terra | High | Labels, state, consequences, validation, accessible names, and recovery remain at the action; no explanatory copy is removed or replaced by an unowned help link; all six locales have planned owners. |

## Milestone 3: Firefox ESR 115 Schema And Product Wiring

Goal: generate ESR 115 from verified Mozilla inputs and make it a first-class channel everywhere
that loads, validates, displays, imports, exports, or documents schema-backed policy data.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M3-01` | Provision and pin ESR 115 source inputs. | Extend the offline input manifest/provisioner with the approved Mozilla tag/files and checksum-verifying local-cache lifecycle. | GPT-5.6 Terra | High | Exact URLs, tags, hashes, license/provenance, cache verification, retry/quarantine, and real stdout progress are tested; no runtime download path is added. |
| `BPM095-M3-02` | Generate the independent ESR 115 bundled schema. | Add the approved declarative target and extend the converter only where Firefox 115 source shape requires a version-gated, authoritative rule. | GPT-5.6 Terra | Extra High | The ESR 115 JSON has exact channel/version/source metadata, is byte-reproducible from pinned inputs, passes nested-policy completeness, and is neither copied nor relabelled from another channel; generation prints real target/policy progress. |
| `BPM095-M3-03` | Wire the four-channel lifecycle catalog. | Implement the M2 catalog roles and derive loaders, validators, API catalogs, selector/header order, latest ESR, default channel, and filenames from it. | GPT-5.6 Terra | High | All four channels load and validate independently; new profiles default to the latest ESR; no consumer relies on a singular current-ESR alias or hard-coded three-channel list. |
| `BPM095-M3-04` | Add ESR 115 to product editors and locales. | Expose the verified label and channel-specific policy availability in Library filters, Guided review, All settings, JSON editor, header data, and six source/runtime locale catalogs. | GPT-5.6 Terra | High | ESR 115 is selectable and visible without English fallback islands; supported policies appear only on correct channels; schema-generated labels and locale allowlists/glossary stay synchronized. |
| `BPM095-M3-05` | Audit policy placement, presets, and CIS behavior. | Diff ESR 115 against every other channel and review All settings, Guided promotion, raw fallback, starter presets, CIS overlays, and compliance claims. | GPT-5.6 Terra | High | Every added/missing/changed policy has a recorded product disposition; All settings covers every supported policy; CIS/preset behavior is validated or explicitly unavailable without changing benchmark provenance. |
| `BPM095-M3-06` | Prove four-channel schema reproducibility. | Run focused converter, metadata, loader, validation, policy-placement, locale, CIS, legacy-guard, and offline byte-identity contracts. | GPT-5.6 Terra | Extra High | The complete four-channel matrix is generated and verified independently, retired/unknown artifacts are rejected, diffs are reviewable, and no schema-refresh exception remains; the command reports phase/channel and completed/total targets. |

## Milestone 4: Cross-Channel Conversion Engine And API

Goal: make conversion a deterministic domain operation with a preview/apply boundary shared by
manual UI flows and future retirement migrations.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M4-01` | Implement the schema-diff conversion planner. | Compare a profile document with source and target schemas and classify each policy/value as unchanged, transformed, or blocked with stable paths and reason codes. | GPT-5.6 Terra | Extra High | Planner output is deterministic, locale-neutral, serializable, complete for nested/dynamic values, and validated against the target schema; it never mutates the input. |
| `BPM095-M4-02` | Implement explicit conversion recipes. | Add a bounded registry for approved structural/value transformations whose source/target constraints and reversibility are testable. | GPT-5.6 Terra | High | Every non-identity transformation names exact channel/schema predicates, produces a target-valid value, preserves source input, and fails closed outside its reviewed domain. |
| `BPM095-M4-03` | Add the conversion preview API. | Expose source/target, profile revision, plan identity, summary counts, detailed blockers/changes, target validity, and availability without writing the profile. | GPT-5.6 Terra | High | Preview is read-only, rejects unknown/identical/unsupported targets consistently, preserves API security/error conventions, and has OpenAPI plus focused API tests. |
| `BPM095-M4-04` | Add atomic conversion apply semantics. | Apply an unblocked current preview through the profile service with expected revision and one transaction, updating channel, converted flags, compliance disposition, and revision together. | GPT-5.6 Terra | Extra High | Success is target-valid and increments revision once; stale/blocked/invalid/failed requests leave every field unchanged; retry behavior is explicit and SQLite/PostgreSQL tests pass. |
| `BPM095-M4-05` | Preserve import, edit, compare, and export consistency. | Ensure a converted profile opens in every editor, compares using the new channel, and exports the exact target-valid `policies.json` envelope. | GPT-5.6 Terra | High | Round trips preserve all nontransformed values and metadata owned by the contract; no editor silently reverts the target channel or exposes source-only controls. |
| `BPM095-M4-06` | Prove the complete directed conversion matrix. | Build fixtures for every `N × (N - 1)` supported-channel pair, representative nested policies, blockers, transformations, empty documents, stale revisions, and repeatability. | GPT-5.6 Terra | Extra High | Every pair has positive and negative evidence; target validation always runs; input/source profiles are immutable during preview; runtime remains bounded with validator reuse; the matrix run prints current pair and completed/total pairs. |

## Milestone 5: Profile Recommendations And Conversion UI

Goal: guide profiles on older ESR lines toward the latest ESR while keeping all channel changes
explicit, previewable, localized, accessible, and recoverable.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M5-01` | Derive recommendation eligibility from the catalog. | Return recommendation metadata only when a profile's supported ESR line is older than the catalog's latest ESR. | GPT-5.6 Terra | Medium | ESR 115 and ESR 140 profiles point to ESR 153 in the planning matrix; Release/latest/unknown/retired states do not receive a misleading manual recommendation; no version label is hard-coded. |
| `BPM095-M5-02` | Add the Library latest-ESR recommendation. | Show a compact status/action on eligible profile rows/cards and route the action into conversion preview. | GPT-5.6 Terra | High | The recommendation identifies source and target, is keyboard/screen-reader operable, survives filtering/pagination/locale changes, and performs no write before confirmation. |
| `BPM095-M5-03` | Add the full conversion review and confirmation flow. | Present summary, changed policies, blockers, consequence, target selector for all supported channels, resolution path, and explicit apply action in existing profile surfaces. | GPT-5.6 Terra | Extra High | Blocked plans cannot be applied; successful conversion handles stale revisions and reloads exact saved state; unsaved editor work cannot be overwritten; cancel is side-effect free. |
| `BPM095-M5-04` | Localize and visually harden conversion states. | Add English-first copy and complete Russian, German, Simplified Chinese, French, and Spanish translations with native headings and Mozilla terminology evidence. | GPT-5.6 Terra | High | Locale parity, placeholders, visible-English allowlists, long-label layouts, narrow viewports, dark/light themes, focus, contrast, and accessible status announcements pass. |
| `BPM095-M5-05` | Prove recommendation and conversion UX. | Add semantic DOM/module tests and focused Chromium/Selenium smoke for eligible, latest, Release, blocked, successful, stale, cancellation, and responsive states. | GPT-5.6 Terra | Extra High | Real-browser behavior matches API state, no duplicate action or hidden write occurs, localized source/target labels are correct, and failure artifacts are retained; browser output identifies the current scenario and completed/total scenarios. |

## Milestone 6: Retired ESR Successor Migration

Goal: make removal of a supported ESR a deterministic release migration that automatically moves
its profiles to the immediate newer supported ESR without hidden runtime writes or data loss.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M6-01` | Implement lifecycle-transition plan validation. | Compare previous and candidate catalogs and emit added, retained, refreshed, and retired lines plus exact same-line and retirement-successor mappings. | GPT-5.6 Terra | High | A retired ESR without one supported immediate-newer ESR successor fails; cycles, jumps over a supported intermediate ESR, family mismatches, ambiguity, and unsupported targets are rejected. |
| `BPM095-M6-02` | Add total-convertibility retirement preflight. | Prove schema containment or complete approved recipes for every source-valid policy/value shape before a retired ESR plan is promotable. | GPT-5.6 Terra | Extra High | The gate reports exact uncovered paths and rejects promotion before DB changes; sampled profile success cannot substitute for the source-schema-wide proof. |
| `BPM095-M6-03` | Materialize safe retirement in Alembic. | Create immutable migration-owned conversion data/code that applies the approved successor plan to stored channel, flags, compliance disposition, and revision in one database transaction. | GPT-5.6 Sol | Extra High | SQLite and PostgreSQL upgrades are atomic, idempotent, backup-gated, interruption-safe, and byte-preserving outside approved transformations; large migrations print real preflight/profile-count and terminal transaction progress without policy values; Sol is required because this irreversible cross-database migration must combine generated-schema proof with customer-data integrity. |
| `BPM095-M6-04` | Test current and future retirement examples. | Cover synthetic ESR 115 to ESR 140 and required ESR 140 to ESR 153 retirement, same-line patch refresh, retained supported ESRs, latest ESR, Release, empty/complex profiles, and failure rollback. | GPT-5.6 Terra | Extra High | Every affected profile reaches the declared successor and validates; retained channels remain unchanged; counts/revisions/flags/compliance/lifecycle/name timestamps follow the approved contract; unsupported downgrade remains backup restore only. |
| `BPM095-M6-05` | Preserve read-only runtime ownership. | Remove or guard any fallback that could normalize retired channels during startup, request handling, list/GET, validation, or UI rendering. | GPT-5.6 Terra | High | Alembic is the sole writer; startup verifies head without mutation; GET/list/preview are read-only; an unupgraded database fails with actionable operator guidance. |
| `BPM095-M6-06` | Add migration observability and recovery evidence. | Report preflight counts, source/target channels, transformed/unchanged totals, transaction result, backup identity, and failure boundary without exposing policy values or secrets. | GPT-5.6 Terra | High | Operators can verify what will move and what moved; logs are safe, deterministic, and testable; partial success is never reported; recovery points to verified backup restore. |

## Milestone 7: Schema-Bump Runbook, Tooling, And Live Matrix

Goal: make ESR lifecycle behavior repeatable for maintainers so a future channel addition, refresh,
or retirement cannot omit profile conversion, documentation, localization, or runtime evidence.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M7-01` | Update the Firefox schema update runbook. | Require official support evidence; lifecycle roles; added/retained/refreshed/retired rows; latest ESR; immediate successor; pairwise conversion; total-convertibility; Alembic; backup; docs/locale/CIS/live gates. | GPT-5.6 Terra | High | The runbook explicitly requires automatic ESR 140 to ESR 153 migration when 140 is removed, forbids runtime inference and silent loss, and preserves independent source/checksum generation. |
| `BPM095-M7-02` | Add a schema-lifecycle dry-run command. | Produce a reviewable candidate plan from previous/current manifests and optionally report affected profile counts from an explicitly selected disposable/backup-verified database without mutation. | GPT-5.6 Terra | High | Output names phases/channels, completed/total units, cache state, exact mappings, blockers, and terminal status with flushed real progress; default execution is read-only. |
| `BPM095-M7-03` | Strengthen schema and drift guards. | Generate or update tests that find undeclared channel literals, stale labels/files/source tags, incomplete conversion pairs, missing successor data, and omitted docs/locale/CIS/help targets. | GPT-5.6 Terra | High | Active owned surfaces derive from the catalog/manifests; historical/migration exceptions are explicit; a partial future bump fails in the earliest responsible layer. |
| `BPM095-M7-04` | Add ESR 115 to deterministic Firefox live automation. | Pin/checksum the current ESR 115 browser artifact and run the persisted-profile/export/install/runtime contour independently from Release 153, ESR 153, and ESR 140. | GPT-5.6 Terra | Extra High | All four channels report exact browser/geckodriver versions, hashes, policy/runtime evidence, skips, and artifacts; setup is idempotent, prints phase/channel plus completed/total channels, and uses no floating `latest` download. |
| `BPM095-M7-05` | Refresh schema ownership and agent context. | Update current architecture maps, release procedures, bounded Codex/documentation snapshots, and focused verification routes for lifecycle, conversion, UI, migration, and tooling owners. | GPT-5.6 Luna | Medium | Maintained maps point to the smallest current owners/tests, generated snapshots use their commands, docs index is unique, and no active technical surface retains the superseded three-channel rule. |

## Milestone 8: Product Documentation, README, And Maintainer Handoff

Goal: document the delivered four-channel, conversion, recommendation, and retirement behavior for
users and operators in all six locales before final release quality.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M8-01` | Inventory affected documentation and help ownership. | Map User, Firefox Policy, CIS, Administrator/DevOps, API, support/troubleshooting, schema inventory, search, contextual-help, and screenshot impacts. | GPT-5.6 Terra | High | Every delivered behavior and support boundary has one audience owner; untouched guides have a recorded unaffected reason; stale three-channel claims and links have dispositions. |
| `BPM095-M8-02` | Update English product and API documentation. | Explain ESR 115 purpose/caveat, channel choice, latest-ESR recommendation, preview/apply results, blockers/recovery, all conversion directions, and automatic retired-ESR successor migration. | GPT-5.6 Terra | High | Procedures match shipped UI/API and exact `policies.json` envelopes; administrator backup/upgrade/recovery is complete; no internal, future, or unsafe workflow is exposed. |
| `BPM095-M8-03` | Localize the delivered documentation scope. | Propagate complete equivalent content to `ru`, `de`, `zh-CN`, `fr`, and `es-ES`, using the BPM catalog, Pontoon for Firefox UI terms, SUMO for support prose, and native heading rules. | GPT-5.6 Terra | Extra High | All six locales cover the same supported matrix, conversion outcomes, caveats, and recovery without fallback islands, English-calqued headings, stale versions, or mistranslated identifiers. |
| `BPM095-M8-04` | Refresh schema inventories, help targets, search, and screenshots. | Regenerate Firefox policy support data, navigation/manifests/search, aliases, All settings targets, and only the approved screenshot scenarios affected by the feature. | GPT-5.6 Terra | High | Every policy/channel badge and contextual-help link is current; changed topics reveal correctly in navigation; screenshots fit site/PDF layouts and include localized captions/alt text; generation reports phase/locale and completed/total artifacts. |
| `BPM095-M8-05` | Run the required editorial and PDF review. | Follow `documentation-update-for-future-epics.md` across affected guide maps, headings, completeness/exclusions, Microsoft style, locale rules, BPM UI labels, Pontoon/SUMO evidence, DITA/site, and both PDFs in six locales. | GPT-5.6 Terra | Extra High | User and Administrator PDFs are rebuilt with flushed guide/locale progress and visually checked for title/contents, CJK glyphs, inline literals, code blocks, links, screenshots, page fit/numbering, and reproducibility; untouched guides are justified. |
| `BPM095-M8-06` | Refresh README durable product facts. | Update supported Firefox schema lines, legacy-OS caveat, and user-facing conversion behavior after implementation; inventory every README-reading test. | GPT-5.6 Terra | Medium | README describes current facts only, retains legal/author/contact material, contains no `0.9.5` release anchor/history/planning or maintainer/test prose, and all README-reading contracts plus `pytest -q` pass. |
| `BPM095-M8-07` | Install the verified documentation artifact. | Run focused/release documentation, package, PDF, and reproducibility gates, then `make docs-install-dev` after the final documentation change. | GPT-5.6 Terra | Extra High | Commands emit real progress and pass; installed artifacts derive their visible version from BPM `0.9.5`; the maintainer's next `make dev` consumes them without the task starting the server. |

## Milestone 9: Final Quality, Release Commit, And CI Handoff

Goal: prove BPM 0.9.5 release readiness across code, schemas, conversion, databases, locales,
documentation, and real browsers, then publish only the reviewed epic commit.

| ID | Task | Essence | Model | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- | --- |
| `BPM095-M9-01` | Run focused epic verification. | Execute schema generation/reproducibility, lifecycle, conversion matrix, API, migration, locale, CIS, UI-contract, runbook, and documentation checks before broad gates. | GPT-5.6 Terra | Extra High | Every owning focused suite passes with no unexplained skip/warning; M8 documentation completion and `make docs-install-dev` are reconfirmed; the gate prints current suite/channel/locale and completed/total suites. |
| `BPM095-M9-02` | Run the final Mypy gate. | Execute maintained type checking over application, migration-support, tooling, and documentation-owned Python surfaces. | GPT-5.6 Luna | Medium | `make typecheck` passes without broad ignores, untyped conversion payloads, or excluded new modules. |
| `BPM095-M9-03` | Run the final Ruff and architecture gates. | Execute lint, format, complexity, import-boundary, generated-source, and ownership checks. | GPT-5.6 Luna | Medium | `make lint` and architecture contracts pass with no temporary suppression, cycle, hand-edited generated artifact, or stale compatibility alias. |
| `BPM095-M9-04` | Run the complete test suite. | Execute `pytest -q` and the complete maintained documentation contours after focused checks pass. | GPT-5.6 Terra | Extra High | All tests pass with no unexpected skip/deselection or warning; schema/conversion/migration behavior is not replaced by source-text assertions; the test command exposes real layer/completed-test progress and a terminal result. |
| `BPM095-M9-05` | Prove 100% covered code surface. | Run `make coverage` plus owned JS/documentation coverage and close every line/branch gap. | GPT-5.6 Terra | Extra High | Every declared maintained surface is at exactly 100%; no gap is accepted as known debt; reports remain uncommitted; coverage reports current surface and completed/total surfaces while running. |
| `BPM095-M9-06` | Run final Chromium product/documentation smoke. | Execute responsive, keyboard, locale, theme, CSP, recommendation, preview, blocker, apply, import/edit/export, and documentation portal scenarios. | GPT-5.6 Terra | Extra High | `make test-ui` passes with clean logs, real scenario/completed-total progress, and retained failure artifacts; browser execution uses immediate sandbox escalation where applicable. |
| `BPM095-M9-07` | Run final four-channel Firefox evidence. | Execute pinned Release 153, ESR 153, ESR 140, and ESR 115 persisted-profile/export/install/runtime tests. | GPT-5.6 Terra | Extra High | Every deterministic channel passes and reports versions, hashes, runtime observations, skips, artifacts, and current/completed-total channel progress independently. |
| `BPM095-M9-08` | Run release migration and reproducibility gates. | Prove clean package installs, SQLite/PostgreSQL upgrades, backup/restore, schema/vendor/docs byte reproducibility, dependency audits, and release procedures. | GPT-5.6 Terra | Extra High | All gates pass from clean state with real progress, no stale cache dependency, no partial migration, and no unexpired unreviewed advisory exception. |
| `BPM095-M9-09` | Finalize release documentation and indexes. | Replace provisional changelog text with verified claims; validate README boundaries, technical/product documentation drift gates, docs index, manifests, snapshots, and release-readiness evidence. | GPT-5.6 Luna | Medium | Older changelog history is preserved; README remains version-neutral; maintained docs are indexed once; no active surface describes the new work as `0.9.4` or retains the superseded lifecycle rule. |
| `BPM095-M9-10` | Create the reviewed BPM 0.9.5 epic commit. | Review status/diff/evidence, exclude unrelated/local/generated-report changes, and commit the completed approved epic without tagging or releasing. | GPT-5.6 Terra | High | Only reviewed BPM095 changes are committed; checks are current; the SHA is reported; no unrelated user work, tag, release, or PR is included. |
| `BPM095-M9-11` | Push normally and monitor required CI. | Push the reviewed commit to the configured branch without force/history rewrite and observe every triggered required workflow to terminal state. | GPT-5.6 Terra | High | Commit SHA, remote branch, workflow URLs, and every job result are reported; rejection, advanced remote, credential/protection failure, or failed workflow stops handoff for explicit maintainer direction. |

## Suggested Execution Order

1. Complete M1 version, package, dependency, and changelog anchors.
2. Freeze the lifecycle, conversion, migration, and UI-copy contracts in M2.
3. Generate and wire the independent ESR 115 schema in M3.
4. Implement and prove the backend conversion planner/API in M4 before adding UI actions.
5. Add recommendations and explicit conversion UX in M5.
6. Implement reusable retired-ESR planning and immutable Alembic ownership in M6.
7. Update the bump runbook, drift tooling, live-browser matrix, and context maps in M7.
8. Complete six-locale product documentation, README current-state copy, PDF/reproducibility review,
   and `make docs-install-dev` in M8.
9. Execute M9 final gates, reviewed commit, regular push, and terminal CI monitoring.

Within a milestone, follow task ID order unless an acceptance condition explicitly depends on a
later fixture. Do not add write-capable UI before the M4 API contract, do not generate an Alembic
retirement revision before the total-convertibility proof, and do not document a behavior as shipped
before its focused implementation checks pass.

## Execution Protocol

- Do not execute a task merely because this backlog exists.
- Before each task, show exactly one next task with its ID, essence, acceptance, minimum model, and
  minimal reasoning; wait for explicit maintainer approval.
- Execute only that approved task through exactly one focused subagent using the task-row model and
  at least the task-row reasoning level. If that exact model is unavailable, report it and obtain
  approval for the nearest replacement before starting.
- Keep the primary agent as maintainer-facing coordinator. Report task start, meaningful phase
  transitions, material finding/blocker, and terminal verification; raw subagent command streams
  remain opt-in.
- Start from `docs/codex/PROJECT_SNAPSHOT.md`, then read only named owners, adjacent tests, relevant
  runbooks/contracts, and nearby modules. Preserve unrelated user changes and keep diffs reviewable.
- Run the narrowest relevant validation first. Expand to schema, conversion, migration, locale,
  documentation, browser, or release contours only when their owning task calls for them.
- Any command that may exceed one minute or has uncertain duration must print flushed real-work
  progress on stdout: phase/channel/locale, completed and total units, cache/retry state, and a
  terminal success/failure boundary. Measured elapsed time/ETA is allowed; fabricated percentages,
  decorative spinners, timers, and chat-only progress are not.
- While a long command runs, keep maintainer chat silent. If a third-party command cannot expose
  units, use a task-owned read-only observer. Preserve safe interruption, partial-artifact
  quarantine, and atomic promotion.
- Run Selenium/Chromium/Firefox commands with immediate sandbox escalation where the environment
  requires it; do not first perform a known-failing sandbox trial.
- Recheck Mozilla support/version/tag/checksum evidence, dependencies, licenses, advisories,
  browser binaries, geckodriver, and GPT-5.6 guidance at the task that consumes them. Backlog-time
  observations are not permanent pins.
- A conversion preview is read-only. A manual conversion applies only after explicit confirmation
  and current-revision validation. A retired-ESR migration applies only through the approved
  Alembic revision after backup and preflight.
- Coverage below 100% is never accepted as known debt. Add focused tests, remove proven dead code,
  or stop for an approved scope decision.
- The final push is regular and non-force. Do not rewrite history, tag, create a release/PR, or
  include unrelated changes. Monitor every required workflow to a terminal result and stop on
  failure.

## Backlog Creation Acceptance Checklist

- Target version is normalized as `0.9.5`, epic ID `BPM095`, and filename prefix `bpm_0_9_5`.
- Scope, current state, external ESR 115 evidence, approved decisions, assumptions, non-goals, and
  high release/data-migration risk are explicit.
- Milestones are grouped by meaning and end in type, lint, full test, 100% coverage, Chromium,
  four-channel Firefox, documentation, changelog, commit, push, and terminal CI gates.
- Every task has one stable ID, one minimum GPT-5.6 model, one allowed reasoning level, and a focused
  acceptance condition; each Sol assignment explains why Terra is unsafe.
- M1 covers version surfaces, editable metadata, external dependency/toolchain checks, changelog,
  package/version tests, and README version-neutrality.
- ESR 115 source/version remains an official-evidence pin selected at execution, not a copied or
  guessed schema artifact.
- Latest ESR, default channel, older supported ESR, retired ESR, and immediate newer successor are
  independent catalog roles with executable drift guards.
- Pairwise Release/ESR conversion has preview/apply, no-silent-loss, optimistic revision, compliance,
  target-validation, round-trip, and all-directed-pairs tasks.
- Older supported ESR profiles receive an explicit UI recommendation; they are not auto-migrated.
- Retired ESR profiles move automatically through Alembic to the declared immediate newer ESR, with
  ESR 140 to ESR 153 as required evidence and ESR 115 to ESR 140 as a future-transition fixture.
- The schema-bump runbook and tooling include official provenance, lifecycle diff, successor map,
  total-convertibility, backup, migration, locale, CIS, docs, and live-browser gates.
- M8 follows `documentation-update-for-future-epics.md`, including guide-map and exclusion review,
  Microsoft/Pontoon/SUMO/native-heading authority, six-locale DITA/site/PDF verification, CJK and
  code-block checks, page-fitting screenshots, reproducibility/package checks, and successful
  `make docs-install-dev` handoff.
- README work is limited to durable installer/user/administrator facts, preserves legal and
  author/contact material, inventories all README-reading contracts, and reruns `pytest -q`.
- Long-running commands have real flushed stdout progress and browser commands require immediate
  escalation where applicable.
- Every backlog task requires separate explicit maintainer approval, one focused subagent, exact
  task-row model/minimum reasoning or an approved replacement, major coordinator updates, and
  opt-in raw command output.
- Docs index includes this backlog with status `backlog`; no creation-time manifest entry or archive
  move is required.
