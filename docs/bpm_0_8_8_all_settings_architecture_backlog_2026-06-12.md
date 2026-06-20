# BPM 0.8.8 All Settings Architecture Backlog

Date: 2026-06-12

This backlog defines the BPM 0.8.8 work for turning the existing All settings route into a
triage-first, enterprise-scale settings workspace. The work stays inside the current
`/profiles/{profile_id}/settings` section instead of creating another product surface.

Product source, UI copy, README, changelog, and maintained documentation stay in English.
Maintainer chat may be Russian, but implementation copy must not switch to Russian unless the task
is explicitly about localization.

## Scope Summary

- Target BPM version: `0.8.8`.
- Compact epic id: `BPM088`.
- Scope boundary: product UI architecture, frontend inventory/model refactor, All settings route
  layout, source attribution, search/result architecture, performance, localization, tests, docs,
  and release metadata.
- Release risk: high, because the work touches the All settings route, shared schema-shell editor
  runtime, search, profile starter/CIS metadata, route DOM contracts, CSS, localization, and browser
  UI smoke coverage.
- Primary outcome: All settings remains the single full-control settings surface, but defaults to a
  review/configured workflow rather than a long full-catalog listing.
- Secondary outcome: enterprise profiles such as `basic_corporate + CIS Level 2` are reviewable by
  source, category, and attention state without scrolling through the full policy/preference matrix.

## Current-State Assessment

- The current All settings route renders search, technical review, full inventory table, detail
  panel, category map, category sections, schema-shell coverage, and managed-preference sections in
  one vertical workspace.
- The route already has useful building blocks: `profiles_all_settings_list.js`,
  `profiles_all_settings_detail.js`, `profiles_settings_search.js`, and the shared
  `profiles_schema_shell*.js` editor/runtime.
- The default inventory state is `all`, so users first see every schema-backed policy and every
  known preference, not the changed or risky subset.
- The list renderer builds the complete entry DOM and filters rows with `hidden`; it does not
  budget, paginate, or virtualize large inventories.
- Search indexes multiple representations of similar controls: All settings entries, mapped
  controls, preference presets/bundles, known preferences, search engine presets, and schema
  blueprints. This is powerful but can produce duplicated or ambiguous navigation choices.
- The detail panel is useful but competes with lower full-page schema-shell editors. The same
  setting can feel editable from several places.
- Domain categories exist in `app/web/firefox_all_settings_categories.py`, but the screen still
  exposes long category bodies rather than a compact state summary first.
- CIS merge metadata already records decisions, recommendation IDs, and manual-review state, but
  All settings does not yet use that metadata as a first-class navigation/source model.
- A rough release-151 inventory contains about 119 policy entries and 52 known preferences before
  imported/unknown settings.
- A `basic_corporate + CIS Level 2` merged profile currently produces about 42 configured policies,
  10 configured preferences, and 4 manual-review decisions; privacy/security alone can contain more
  than 20 configured items.
- Existing cognitive-load principles already established for the guided wizard apply here too:
  summary before detail, changed items first, details on demand, full-width treatment for long
  content, and advanced detail as a destination rather than inline clutter.

## Non-Goals And Assumptions

- Do not create a new route or separate product interface for full settings control.
- Do not remove `/profiles/{profile_id}/settings`; it remains the All settings destination.
- Do not remove the JSON editor or make it the default way to review enterprise profiles.
- Do not change Firefox policy semantics, CIS generation, CIS merge rules, profile persistence, or
  export format unless a UI task explicitly requires extra metadata to be surfaced.
- Do not remove schema-shell coverage. Re-home or collapse it so it supports the task flow instead
  of competing with it.
- Do not add a backend API for settings inventory unless the frontend inventory model proves too
  expensive or too duplicated to maintain safely in static JS.
- Assume all active locales must continue to pass key/placeholder parity.
- Assume browser UI smoke is required before the epic is considered release-ready.

## Milestone 1: Version Transition And Release Anchors

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M1-01` | Update project metadata to `0.8.8`. | Move package and runtime version surfaces to the target version. | low | `pyproject.toml`, package metadata, runtime app version, and version tests agree on `0.8.8`. |
| `BPM088-M1-02` | Prepare README version anchors for `0.8.8`. | Keep README current while reserving final behavior copy for the final milestone. | low | README names `0.8.8` as the active target without describing unimplemented All settings behavior as complete. |
| `BPM088-M1-03` | Add a `CHANGELOG.md` section for `0.8.8`. | Create the release-note landing zone without overwriting older history. | low | `CHANGELOG.md` has a new `0.8.8` section above older releases and preserves previous notes. |
| `BPM088-M1-04` | Update maintained docs anchors that name the current release. | Align active docs with the new target while preserving historical notes. | medium | Active docs that should track the current target mention `0.8.8`; archive files and explicit historical notes keep original versions. |
| `BPM088-M1-05` | Update tests that assert current version surfaces. | Make the version transition repeatable. | medium | Focused tests fail on stale current-version metadata and pass after the transition. |

## Milestone 2: Baseline Audit, Contracts, And Product Decision Record

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M2-01` | Write the All settings single-surface decision record. | Document that 0.8.8 improves the current route instead of creating another interface. | low | An architecture note states the route boundary, why a new surface is a non-goal, and how Review/Configured/Catalog fit inside All settings. |
| `BPM088-M2-02` | Capture current All settings DOM and data-flow contracts. | Map template, list, detail, search, schema-shell, preference, and runtime ownership before edits. | medium | A short maintained note or test helper names the current modules, render dependencies, and route-specific DOM nodes. |
| `BPM088-M2-03` | Add failing/guarding route contracts for triage-first layout. | Lock the target structure before implementation. | high | Tests assert that All settings exposes mode controls for Review, Configured, and Catalog while still rendering the existing route shell. |
| `BPM088-M2-04` | Add enterprise-profile fixture coverage. | Make heavy-profile UX testable without manual setup. | high | Tests or fixtures can build at least `basic_corporate + CIS Level 2` for release and ESR channels. |
| `BPM088-M2-05` | Add current inventory count telemetry for tests. | Keep expected scale visible while refactoring. | medium | A focused test or helper reports policy/preference entry counts by channel and fails only on meaningful contract drift. |
| `BPM088-M2-06` | Add source-state regression fixtures. | Prepare for baseline/CIS/manual/imported attribution. | high | Fixtures cover baseline-only, CIS-added, CIS-replaced, manual-review, imported unknown, raw fallback, and manually edited settings. |

## Milestone 3: Unified Settings Inventory Model

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M3-01` | Introduce a `SettingsInventory` frontend module. | Build one entry model shared by review, configured, catalog, search, and detail. | high | A dedicated module returns stable entries with id, kind, category, state, source, attention flags, target, value summary, and editor metadata. |
| `BPM088-M3-02` | Move policy entry collection into the inventory module. | Stop list/search from owning policy collection separately. | high | Schema-shell policy entries are collected once and consumed by All settings list/search/detail. |
| `BPM088-M3-03` | Move preference entry collection into the inventory module. | Treat known and unknown managed preferences as first-class inventory entries. | high | Known preferences, configured unknown preferences, preference sections, and value summaries are produced by the shared inventory. |
| `BPM088-M3-04` | Add validation issue mapping to inventory entries. | Keep invalid state independent of a specific renderer. | medium | Inventory entries include validation issues and attention flags for policy and preference paths. |
| `BPM088-M3-05` | Add source attribution to inventory entries. | Distinguish baseline, CIS, manual, imported, raw, unknown, and available settings. | high | Entry `sources` can represent at least baseline, CIS, manual edit, imported unknown, raw fallback, and catalog-only availability. |
| `BPM088-M3-06` | Add CIS merge decision lookup helpers. | Surface CIS review metadata without duplicating merge logic. | high | Inventory can link configured entries to CIS decision, recommendation IDs, selected source, and review-required state when available. |
| `BPM088-M3-07` | Add unit tests for inventory construction. | Make the model safe before changing UI. | high | Tests cover blank, basic corporate, CIS L2, imported unknown, raw fallback, and invalid preference/policy entries. |

## Milestone 4: Review Mode As The Default Workflow

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M4-01` | Add All settings mode state. | Replace implicit `all` default with explicit Review, Configured, and Catalog modes. | high | Mode state survives list rerenders, updates URL/focus only where appropriate, and defaults to Review for saved heavy profiles. |
| `BPM088-M4-02` | Make Review the default first screen. | Show attention-worthy work before full catalog inventory. | high | Opening All settings shows invalid, CIS manual-review, raw, unknown, deprecated, and imported review cards/list before available settings. |
| `BPM088-M4-03` | Convert technical review cards into a review queue. | Turn the current counters into actionable grouped queues. | high | Review groups show counts, first affected entries, source/reason labels, and clear empty states. |
| `BPM088-M4-04` | Add CIS manual-review group. | Make CIS exceptions visible as product work, not hidden metadata. | high | `basic_corporate + CIS Level 2` exposes its manual-review decisions in Review mode with policy path and reason. |
| `BPM088-M4-05` | Add review empty and success states. | Avoid a blank technical panel when no issues exist. | medium | Clean profiles show a compact "nothing needs review" state with next actions for Configured and Catalog. |
| `BPM088-M4-06` | Add Review mode tests. | Protect the new default workflow. | high | DOM/unit tests cover default mode, review group counts, CIS review entries, invalid entries, and no-review empty state. |

## Milestone 5: Configured Mode, Category Summaries, And Source Navigation

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M5-01` | Build domain summary cards for configured settings. | Show category counts before long category detail. | high | Configured mode starts with domain summaries such as Browser access, Privacy, Users/add-ons/sites, Raw/unmapped, each with configured and attention counts. |
| `BPM088-M5-02` | Add source filter chips. | Let admins inspect baseline, CIS, manual, imported, and raw items directly. | high | Configured mode can filter by source without losing category context or selected entry state. |
| `BPM088-M5-03` | Add category drilldown lists. | Replace long always-visible category bodies with deliberate drilldown. | high | Selecting a category reveals only that category's configured entries by default, with clear counts for hidden available entries. |
| `BPM088-M5-04` | Add source and category badges to entry rows. | Make each row explain why it exists. | medium | Rows show state, category, source, and attention badges without repeating noisy table columns. |
| `BPM088-M5-05` | Redesign configured row value summaries. | Keep object/array values scannable without dumping JSON into the list. | medium | Complex values render compact summaries and defer full JSON to detail. |
| `BPM088-M5-06` | Add Configured mode tests. | Lock enterprise profile scan behavior. | high | Tests cover `basic_corporate + CIS L2` counts by category/source and verify long configured lists are not all expanded by default. |

## Milestone 6: Catalog Mode, Search, And Detail As The Main Editing Surface

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M6-01` | Move full available inventory into Catalog mode. | Keep full coverage available without making it the default. | high | Available/catalog-only settings appear in Catalog mode, not in Review or Configured defaults. |
| `BPM088-M6-02` | Redesign search results into grouped command-palette results. | Reduce duplicated target choices and clarify result intent. | high | Search groups results into configured settings, available policies, preferences, and actions, with deduped targets. |
| `BPM088-M6-03` | Add search scope controls. | Let users search within Review, Configured, Catalog, or all scopes. | medium | Search scope is visible, keyboard-accessible, and does not surprise-switch the selected mode unless the user chooses a result. |
| `BPM088-M6-04` | Make the detail panel the primary editor. | Use one edit surface for the selected setting. | high | Selecting a row/result opens detail with current value, source, validation, editor, reset/remove/apply actions, and location metadata. |
| `BPM088-M6-05` | Align detail editors with schema-shell controls. | Reuse existing editor cards without exposing duplicate full-page editors. | high | Inline policy editors and preference editors work from detail and update inventory/search after apply/remove. |
| `BPM088-M6-06` | Add detail deep-link and focus behavior. | Preserve targeted handoff into a specific setting. | high | Existing `focus` and search-result navigation can select an entry, open detail, and scroll/focus predictably. |
| `BPM088-M6-07` | Add Catalog/search/detail tests. | Protect the primary edit workflow. | high | Tests cover grouped search, target dedupe, detail apply/remove/reset, preference add, and focus handoff. |

## Milestone 7: Schema-Shell And Preference Section Re-Homing

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M7-01` | Collapse full schema-shell sections behind Catalog/Advanced detail. | Keep coverage without competing with the list/detail workflow. | high | Full schema-shell category blocks are hidden by default and reachable from Catalog or explicit advanced controls. |
| `BPM088-M7-02` | Replace category map with state summary navigation. | Make top navigation reflect work state instead of static anchors. | medium | Category navigation shows counts and state, and no longer sends users into a long page by default. |
| `BPM088-M7-03` | Re-home managed preference presets and bundles. | Keep preference creation available from Catalog/detail. | high | Preference presets, bundles, known preferences, and manual add remain accessible but no longer render as long always-visible sections. |
| `BPM088-M7-04` | Preserve schema-shell coverage badges. | Keep schema coverage useful as supporting metadata. | medium | Coverage and raw/deprecated counts remain available in advanced detail or Catalog summaries. |
| `BPM088-M7-05` | Remove duplicate action paths. | Avoid multiple visible controls that edit the same setting in the same mode. | high | In default Review/Configured modes, each setting has one obvious edit path through detail. |
| `BPM088-M7-06` | Add schema-shell re-homing tests. | Ensure coverage is not lost while default clutter is reduced. | high | Tests assert schema-shell nodes remain reachable, route focus still works, and default page height/listing is reduced. |

## Milestone 8: Performance, Long-List Budget, And Responsive Layout

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M8-01` | Add long-list budget to All settings lists. | Prevent unbounded visible rows in Review, Configured, and Catalog. | high | Any dynamic list that can exceed 7 rows defaults to a budgeted view with count and show-more control. |
| `BPM088-M8-02` | Add pagination or virtualization for Catalog mode. | Keep the full inventory responsive. | high | Catalog can handle the full release/ESR inventory plus unknown entries without rendering every row as a visible DOM block. |
| `BPM088-M8-03` | Avoid rebuilding inventory unnecessarily. | Reduce repeated collect/index/render work on document changes. | high | Inventory is recomputed only when source data, schema channel, validation issues, locale, or CIS metadata changes. |
| `BPM088-M8-04` | Add performance-oriented tests or probes. | Catch accidental full-list regressions. | medium | Focused tests or diagnostics assert bounded rendered row counts for heavy fixtures. |
| `BPM088-M8-05` | Redesign desktop layout for heavy content. | Avoid narrow-column long lists and competing sidebars. | high | Review/configured lists use full-width or drawer layouts when content is long; detail remains usable on desktop. |
| `BPM088-M8-06` | Redesign mobile layout for modes and detail. | Make heavy settings review usable on narrow screens. | high | Mode controls, search, list, and detail stack without overlap, trapped tiny columns, or inaccessible actions. |
| `BPM088-M8-07` | Add responsive CSS contracts. | Protect long labels and narrow viewport behavior. | medium | Static/DOM tests cover mode controls, source badges, category summaries, rows, detail actions, and show-more controls in long-label locales. |

## Milestone 9: Localization, Copy, Accessibility, And Browser Smoke

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M9-01` | Add concise All settings mode copy. | Explain Review, Configured, and Catalog without internal jargon. | medium | English source copy is short, task-oriented, and avoids schema-first wording in default modes. |
| `BPM088-M9-02` | Update all active locale catalogs. | Keep six-locale parity after UI changes. | high | `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` catalogs build with key and placeholder parity. |
| `BPM088-M9-03` | Update locale glossary/allowlists if naming changes. | Keep terminology consistent for All settings, configured settings, and catalog. | medium | Maintained glossary/allowlist docs reflect new terms and tests pass. |
| `BPM088-M9-04` | Add keyboard and focus contracts. | Preserve accessibility across mode switching, grouped search, and detail editing. | high | Users can tab through modes, search results, rows, detail actions, and show-more controls with visible focus and stable selection. |
| `BPM088-M9-05` | Add screen-reader labels for counts and modes. | Make summary badges understandable outside visual layout. | high | Mode controls, category cards, source badges, review groups, and row counts have useful accessible names or live announcements. |
| `BPM088-M9-06` | Add browser smoke for heavy All settings review. | Verify the target workflow in Chromium/Selenium. | extra high | Browser smoke opens a heavy `basic_corporate + CIS L2` profile, lands in Review mode, verifies review counts, switches modes, searches, edits detail, and sees no incoherent overflow. |
| `BPM088-M9-07` | Capture visual QA notes for All settings. | Record actual viewport review without committing generated screenshots. | medium | QA notes list inspected routes, locales, viewports, and any screenshots kept only in ignored artifact paths. |

## Milestone 10: Adjacent Library And Compare UI Fixes

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M10-01` | Add a permanent delete action to archived-profile controls. | Let users delete a profile without first archiving or preserving it in the archive. | high | Library rows/cards expose a destructive delete action next to archive/restore actions where appropriate, and the action is visually distinct from archive/restore. |
| `BPM088-M10-02` | Add irreversible-delete confirmation copy and behavior. | Make permanent deletion deliberate and unmistakable. | high | Permanent delete requires confirmation text that clearly says the profile will be deleted permanently and cannot be restored from the archive. |
| `BPM088-M10-03` | Wire permanent delete to the existing hard-delete API safely. | Reuse the backend lifecycle boundary instead of adding a duplicate endpoint. | high | Confirmed permanent delete calls the hard-delete path, refreshes the Library list/stats, updates status messaging, and handles failure without removing the row optimistically. |
| `BPM088-M10-04` | Add Library delete tests and localized copy coverage. | Protect the new destructive action across locales and lifecycle states. | high | Tests cover active and archived rows, confirmation copy, API call path, status/error handling, and active locale catalog parity. |
| `BPM088-M10-05` | Remove the Compare route return-to-Library action. | Drop redundant navigation because Compare opens in a new tab from Library. | medium | `/profiles/compare` no longer renders the return-to-Library button or link, and no active copy suggests it is the primary way back. |
| `BPM088-M10-06` | Normalize Compare header/layout after removing the return action. | Remove the surrounding object/container if it only existed for the redundant button. | high | Compare header and command area keep balanced spacing, no empty container remains, and desktop/mobile layouts do not show a visual gap where the button was. |
| `BPM088-M10-07` | Add Compare cleanup tests and browser smoke coverage. | Lock the simplified Compare header behavior. | high | DOM/static tests assert the return action and dead wrapper are absent; browser smoke verifies Compare still opens from Library and the header remains coherent. |

### Milestone 10 Execution Record

Status: **Completed on 2026-06-19.**

- `BPM088-M10-01..04`: Library rows expose a visually destructive permanent-delete action for
  active and archived profiles. Confirmation states that the profile is not kept in the archive
  and cannot be restored. The action waits for the existing hard-delete API before refreshing the
  list, reports failures, and leaves the row in place when the request fails.
- `BPM088-M10-05..07`: Compare no longer renders the return-to-Library link or its dead command
  column. Static/responsive contracts and Chromium smoke cover the normalized header and opening
  Compare from Library in a new tab.
- Verification: focused M10/API/locale/layout tests, Ruff, generated locale/CSS checks, Library
  permanent-delete Chromium smoke, and Compare Chromium smoke pass.

## Post-Milestone 10 Defect Corrections (Completed)

Maintainer visual QA during the attempted Milestone 10 handoff found the following defects. They
were corrected before starting the final quality milestone and are part of the `0.8.8` release
scope rather than new product tasks.

| ID | Defect | Resolution | Verification | Status |
| --- | --- | --- | --- | --- |
| `BPM088-FIX-01` | A hydrated `basic_corporate + CIS Level 2` profile showed zero configured and source counts in All settings. | Normalize wrapped `{ policies: ... }` documents, initialize the editor from hydrated profile data, and rerender inventory/search after route hydration. | Inventory contracts and Chromium heavy-profile smoke cover non-zero configured, baseline, and CIS counts. | Completed |
| `BPM088-FIX-02` | The bottom of All settings repeated category/navigation information already presented by the catalog workflow. | Remove the duplicate category summary surface, dead DOM wiring, CSS, and obsolete locale keys while retaining the single catalog/detail workflow. | Route DOM, locale, and responsive contracts assert that the duplicate surface is absent. | Completed |
| `BPM088-FIX-03` | Ten CIS-managed Firefox preferences were classified as imported unknown keys. | Add the CIS preferences to the maintained known-preference catalog with boolean/locked metadata and preserve CIS source attribution. | Inventory tests assert zero imported unknown preferences and known CIS metadata for the enterprise fixture. | Completed |
| `BPM088-FIX-04` | Global configured totals conflicted with category-local filter counts, and Configured mode exposed redundant `Configured`/`Available` filters. | Make narrowed summaries state their visible scope and hide state filters outside Catalog mode. | Configured-mode contracts and Chromium smoke verify scoped summaries and meaningful visible filters. | Completed |
| `BPM088-FIX-05` | Opening Configured mode automatically drilled into the first category, showing only part of the configured profile. | Keep `activeCategory=all` until the user explicitly selects a domain card. | Route-state and browser tests assert that initial visible entries equal the full configured count. | Completed |
| `BPM088-FIX-06` | Selecting a row after expanding/paginating the configured list changed the active domain and collapsed the list to that setting's category. | Decouple row selection from category mutation; category changes now require an explicit category action. | Route-state regression coverage preserves `activeCategory=all` when selecting a row, including the `VisualSearchEnabled` scenario. | Completed |
| `BPM088-FIX-07` | Compare displayed a stale top-right legend (`Missing`, `Same value`, `Different value`) in addition to row status badges. | Remove the redundant legend markup and its desktop/mobile CSS while retaining per-row status badges. | Compare static, responsive, and rendering contracts pass without the legend. | Completed |
| `BPM088-FIX-08` | JSON editor bootstrap failed for `basic_corporate + CIS Level 2` with `knownPreference is not defined`. | Restore preference-section search targets to `pref-section:${preferenceSection.id}` instead of referencing a loop variable before declaration. | Runtime search regression and Chromium JSON-editor smoke load a CIS known preference without an error status. | Completed |
| `BPM088-FIX-09` | Guided editor disclosure buttons remained `Show details`/`Hide details` after switching to a non-English locale. | Keep the active disclosure translation key in `data-i18n` and update it in both click and programmatic expansion paths. | Locale parity tests cover all six catalogs; Chromium smoke verifies RU and zh-CN show/hide states. | Completed |

## Milestone 11: Final Quality, Release Docs, And Handoff

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM088-M11-01` | Run `make typecheck`. | Verify static typing after the All settings architecture work. | medium | `make typecheck` passes. |
| `BPM088-M11-02` | Run `make lint`. | Verify Ruff style and lint contracts. | low | `make lint` passes. |
| `BPM088-M11-03` | Run `pytest -q`. | Verify the default non-browser suite. | high | `pytest -q` passes with All settings inventory, route, locale, layout, Library delete, and Compare cleanup regressions covered. |
| `BPM088-M11-04` | Run `make coverage`. | Verify coverage with code-surface reporting. | high | `make coverage` passes and reports covered code surface. |
| `BPM088-M11-05` | Bring covered code surface to 100% if it falls below 100%. | Do not accept coverage debt for this epic. | high | Any coverage drop is fixed with focused tests, removed unreachable code, or documented removal of dead paths. |
| `BPM088-M11-06` | Run `make test-ui` with immediate sandbox escalation. | Verify local Chromium/Selenium product behavior without a doomed sandbox trial. | extra high | `make test-ui` is run outside the Codex sandbox from the start and passes, including heavy All settings, Library permanent delete, and Compare header smoke coverage. |
| `BPM088-M11-07` | Refresh README for the completed 0.8.8 product state. | Document the actual All settings behavior after implementation. | medium | README describes Review/Configured/Catalog modes, Library permanent deletion, Compare navigation cleanup, supported workflows, commands, locales, and test workflow while preserving maintainer copyright and email-topic information. |
| `BPM088-M11-08` | Finalize `CHANGELOG.md` for `0.8.8`. | Preserve historical release notes and summarize the epic. | low | Changelog entry includes All settings triage-first workflow, source attribution, grouped search, detail editing, performance/layout, Library permanent delete, Compare return-action cleanup, localization, and tests. |
| `BPM088-M11-09` | Update docs index after final docs changes. | Keep documentation inventory complete. | low | `docs/docs-index.md` lists every maintained docs file exactly once with correct status. |
| `BPM088-M11-10` | Create a git commit for the completed epic. | Produce a clean handoff point. | medium | Commit includes only intended `0.8.8` changes and has a clear message. |
| `BPM088-M11-11` | Provide the maintainer-run push command. | Do not push from backlog execution. | low | Final report prints the exact `git push` command for the maintainer to run manually. |

### Milestone 11 Execution Progress

- [x] `BPM088-M11-01` — `make typecheck` passed on 2026-06-19; mypy reported no issues in
  62 source files.
- [x] `BPM088-M11-02` — `make lint` passed on 2026-06-19; Ruff reported no issues.
- [x] `BPM088-M11-03` — `./.venv/bin/pytest -q` passed on 2026-06-19. The repository virtualenv
  command was used because bare `pytest` is not installed in the shell PATH.
- [x] `BPM088-M11-04` — `make coverage` passed on 2026-06-19: 825 tests passed,
  34 were deselected, and the report covered 2,738 statements and 828 branches at 100%.
- [x] `BPM088-M11-05` — no coverage remediation was required because covered code surface is
  already at 100% with no missing statements, branches, or partial branches.
- [x] `BPM088-M11-06` — satisfied during the mandatory Firefox 152 / ESR 140.12 schema bump on
  2026-06-20: `make test-ui` passed with 248 tests and 619 deselected.
- [x] `BPM088-M11-07` — README refreshed on 2026-06-20 for the completed 0.8.8 product state:
  Review/Configured/Catalog modes, source-aware detail workflow, bounded lists, permanent deletion,
  Compare navigation cleanup, Firefox 152 / ESR 140.12, locales, and maintained test commands.
- [x] `BPM088-M11-08` — `CHANGELOG.md` finalized on 2026-06-20 with the completed All settings
  architecture, source-aware workflows, grouped search/detail editing, performance/layout work,
  adjacent Library/Compare fixes, Firefox 152 / ESR 140.12, localization, and quality results;
  previous release history remains unchanged.
- [x] `BPM088-M11-09` — documentation index refreshed on 2026-06-20; every maintained docs file is
  listed exactly once, new 0.8.8 architecture/backlog files are indexed, and local generated
  `docs/codex/` snapshots are explicitly excluded alongside screenshot artifacts.
- [x] `BPM088-M11-10` — completed 0.8.8 epic changes prepared and committed together on
  2026-06-20 after schema, locale, browser, release, coverage, typing, lint, and documentation
  gates; local Codex/Obsidian context and generated verification artifacts remain excluded.
- [ ] `BPM088-M11-11` — pending.

### Pre-M11-06 Firefox Schema Bump (Completed)

Status: **Completed on 2026-06-20.** This mandatory release-maintenance insertion was approved and
executed before continuing with the next backlog task.

- Updated the supported pair from Firefox Release 151 / ESR 140.11 to Release 152 / ESR 140.12
  using the official Mozilla `policy-templates` `v7.12` release and refreshed docs/example source
  artifacts.
- Generated `firefox-release-152.json` and `firefox-esr-140.12.json`, removed the previous bundled
  schemas, updated central channels, converter/cache defaults, README/version copy, six locale
  catalogs, CIS channel mappings, and all four generated CIS layers.
- Added Alembic migration `20260620_upgrade_profiles_to_firefox152` and runtime normalization for
  persisted `release-151` / `esr-140.11` profiles. Legacy guards allow old channel strings only in
  migrations, normalization, and their tests.
- Audited upstream changes: `DefaultSerialGuardSetting` is available in both supported channels and
  intentionally remains in the All settings/Guided-review raw fallback instead of becoming a
  first-class Guided control; `FirefoxHome.Weather` remains schema-shell managed. Starter presets
  did not require semantic changes.
- Added localized `Web Serial` policy labels and glossary/allowlist evidence for all active locales.
- Reused the cached channel validator for profile-list validation after the larger schema exposed
  repeated schema compilation in large Compare lists; stabilized affected Selenium checks against
  asynchronous locale rerenders.
- Verification passed: `make test-firefox-schema-contract` (`87 passed`), focused converter/schema
  manager/CIS/catalog tests, locale contracts, `make test-ui` (`248 passed, 619 deselected`), and
  `make test-release` (`845 passed, 22 deselected`).

## Suggested Execution Order

1. Version transition, decision record, and route contracts.
2. Shared inventory model and source attribution.
3. Review mode as the default workflow.
4. Configured mode with category/source summaries.
5. Catalog/search/detail editing workflow.
6. Schema-shell and preference section re-homing.
7. Performance, long-list budget, and responsive layout.
8. Localization, accessibility, and browser smoke.
9. Adjacent Library permanent-delete and Compare header cleanup.
10. Final quality gates, release docs, commit, and maintainer-run push command.

## Execution Protocol

When executing this backlog interactively:

1. Show exactly one next task with its ID, essence, acceptance, and minimal reasoning.
2. Wait for explicit maintainer approval.
3. Execute only that approved task.
4. Report what changed and which checks passed.
5. Show the next task for approval.

Browser/Selenium tests in this backlog must be run with immediate sandbox escalation. Do not first
try `make test-ui` or any Selenium/browser UI command inside the sandbox.

Do not start executing a backlog task just because this backlog exists.

## Backlog Creation Acceptance Checklist

- Target BPM version is present and normalized as `0.8.8`.
- Epic id and task IDs use stable `BPM088-*` identifiers.
- Milestones are grouped by meaning.
- Every task has `low`, `medium`, `high`, or `extra high` minimal reasoning.
- First milestone includes version transition across product surfaces.
- Final milestone includes mypy via `make typecheck`, Ruff via `make lint`, `pytest -q`,
  `make coverage`, coverage-to-100%, Selenium smoke via `make test-ui`, README refresh,
  changelog entry, commit, and maintainer-run push command.
- Selenium/browser UI verification requires immediate sandbox escalation, without a sandboxed trial
  run.
- README instructions preserve maintainer copyright and email-topic information.
- Changelog instructions preserve previous version history.
- Product language is English while maintainer chat may be Russian.
- Docs index includes this backlog.
- Assumptions and non-goals are explicit.
- Execution protocol requires separate user approval for each task.
