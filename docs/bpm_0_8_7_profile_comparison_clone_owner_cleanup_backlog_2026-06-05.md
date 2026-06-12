# BPM 0.8.7 Profile Comparison, Clone Naming, And Owner Cleanup Backlog

Date: 2026-06-05

This backlog defines the BPM 0.8.7 product work for moving saved-profile comparison out of the
Library into a dedicated comparison interface, improving clone naming, and removing profile owner
metadata from the product until the maintainer explicitly asks to bring it back.

Product source, UI copy, README, changelog, and maintained documentation stay in English. Maintainer
chat may be Russian, but implementation copy must not switch to Russian unless the task is explicitly
about localization.

## Scope Summary

- Target BPM version: `0.8.7`.
- Compact epic id: `BPM087`.
- Scope boundary: product behavior change with backend schema cleanup, frontend route work,
  localization, tests, docs, and release metadata.
- Release risk: high, because profile owner removal crosses database schema, API contracts, frontend
  state, locale catalogs, imports, and tests.
- Primary outcome: `/profiles/compare` becomes the only profile comparison workflow. Library only
  navigates to it through a general button.
- Secondary outcome: profile cloning lets the user choose the clone name before working with the new
  draft or saved clone.
- Cleanup outcome: profile owner is removed from runtime models, API responses, UI, tests, and current
  docs. Do not reintroduce owner until the maintainer explicitly asks for it.

## Current-State Assessment

- The repository is currently anchored on BPM `0.8.5` in `pyproject.toml`, `README.md`,
  `CHANGELOG.md`, and maintained architecture docs.
- The active product surfaces are Library (`/profiles`), Guided editor (`/profiles/new` and
  `/profiles/{id}/edit`), All settings (`/profiles/{id}/settings`), and JSON editor
  (`/profiles/{id}/json`).
- The Library template `app/templates/profiles/_page_library_workspace.html` contains the
  `#compare-panel` DOM and the Library route loads `app/static/profiles_library_bootstrap.js`.
- Library comparison state is maintained with `compareFirstProfileState` and
  `compareSecondProfileState`; row actions include `data-compare-profile-id`, and tests currently
  assert that the Library exposes comparison controls.
- Existing comparison output summarizes metadata, changed policy counts, changed preference counts,
  sample changes, and guided-area buckets. It does not render the requested full two-column settings
  table with values for each selected saved profile.
- Similar diff logic also exists in editor/workspace code. BPM 0.8.7 removes that profile
  comparison workflow too; pure normalization helpers may remain only where they support the new
  compare route or unrelated internal equality checks.
- Current clone flow is route-based: Library duplicate links open `/profiles/new?clone_from={id}`.
  `profiles_workspace.js` then creates a draft name with `profiles.clone_name_pattern`, selects the
  generated name, and copies source description, schema, flags, compliance, and owner.
- Profile owner is a runtime field today: SQLAlchemy model, Pydantic schemas, service filters, API
  list/stats query params, Firefox policies import payload, frontend hidden inputs, profile snapshots,
  clone handoff copy, locale keys, tests, and Alembic history all reference it.
- Existing docs index and docs manifest are healthy. This backlog only needs a docs-index row at
  creation time; manifest changes are reserved for finished backlog item contracts.

## Non-Goals And Assumptions

- Do not add profile merge, conflict resolution, or patch generation in BPM 0.8.7.
- Do not expand live Firefox behavior. This epic is about BPM profile management surfaces.
- Do not keep profile owner as a hidden field, deprecated API field, filter, metadata row, or locale
  concept. Runtime API responses must not return it.
- Historical migration files may mention prior owner columns only if Alembic history requires that for
  existing database upgrades. Current runtime code, current docs, generated OpenAPI, and tests should
  treat owner as removed.
- The dedicated comparison interface compares two saved profiles selected in that interface.
  Unsaved draft comparison and editor/workspace profile-diff panels are not part of BPM 0.8.7.
- The Library button opens the comparison interface. It should not embed, lazy-render, or keep hidden
  comparison DOM inside the Library page.
- New UI must follow existing route asset patterns and must not load Monaco or editor-only bundles.

## Milestone 1: Version Transition And Release Anchors

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M1-01` | Update project metadata to `0.8.7`. | Move package and runtime version surfaces from `0.8.5` to `0.8.7`. | low | `pyproject.toml`, runtime app version, and version tests agree on `0.8.7`. |
| `BPM087-M1-02` | Prepare README version anchors for the 0.8.7 work. | Keep README current while reserving final copy refresh for the final milestone. | low | README version heading names `0.8.7` and does not describe 0.8.7 as completed before implementation tasks land. |
| `BPM087-M1-03` | Add a `CHANGELOG.md` section for `0.8.7`. | Create the release note landing zone without overwriting prior history. | low | `CHANGELOG.md` has a new `0.8.7` section above older entries and preserves all previous release notes. |
| `BPM087-M1-04` | Update maintained docs anchors that name the current release. | Align active docs with the new target version while preserving historical references. | medium | Active docs that should track the current target mention `0.8.7`; archive files and explicit historical notes keep their original versions. |
| `BPM087-M1-05` | Add or update tests that assert current version surfaces. | Make the version transition repeatable. | medium | Focused tests fail on stale `0.8.5` runtime/version metadata and pass after the transition. |

## Milestone 2: Comparison Architecture And Safety Contracts

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M2-01` | Audit all current comparison entrypoints. | Map Library comparison, workspace comparison, locale keys, CSS, and tests before moving behavior. | medium | A short implementation note or test fixture identifies every comparison-owned file that must change. |
| `BPM087-M2-02` | Define the saved-profile comparison contract. | Specify selected profile inputs, setting identity, value formatting, missing-value semantics, and sort order. | high | Contract tests describe a two-profile comparison model for policies and `Preferences` values. |
| `BPM087-M2-03` | Extract reusable comparison normalization helpers. | Avoid duplicated diff logic between the new route and legacy editor code. | high | Unit tests cover nested objects, arrays, missing branches, policy values, preference values, and stable ordering. |
| `BPM087-M2-04` | Decide editor comparison fate for 0.8.7. | Keep the epic precise by documenting that editor-only draft comparison is removed instead of preserved or linked. | high | The decision is captured in an active note and regression test, and later removal tasks have one comparison ownership rule. |
| `BPM087-M2-05` | Add failing route contract tests for `/profiles/compare`. | Lock in the new page boundary before implementation. | medium | Tests expect a compare route, compare template kind, compare DOM anchors, and no editor/Library-only surfaces. |

## Milestone 3: Dedicated Profile Comparison Interface

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M3-01` | Add the `/profiles/compare` web route and template shell. | Create the standalone comparison surface. | high | `/profiles/compare` renders with `data-profiles-route-mode="compare"` and does not load editor or Library workspace DOM. |
| `BPM087-M3-02` | Add compare-specific asset loading. | Keep comparison code in its own frontend entrypoint. | high | Route assets include shared profile utilities and a compare bundle, but do not load Monaco or editor-only bundles. |
| `BPM087-M3-03` | Build quick profile search and selection for both sides. | Let users quickly find and choose the left and right saved profiles. | high | Each side has searchable profile selection, keyboard-accessible controls, loading and empty states, and clear selected-profile summaries. |
| `BPM087-M3-04` | Support optional URL preselection. | Let navigation links open comparison with one or both profiles already selected. | medium | Query params such as `left` and `right` preselect valid saved profiles and ignore invalid or archived-inaccessible ids safely. |
| `BPM087-M3-05` | Render the two-column settings comparison table. | Compare settings by setting key and value. | high | The table shows the union of settings present in either profile, with one value column per profile. |
| `BPM087-M3-06` | Include managed preferences as first-class settings. | Compare `Preferences` entries alongside top-level policies. | high | `Preferences.<name>` rows appear with readable labels where available and raw keys where labels are unavailable. |
| `BPM087-M3-07` | Show missing, equal, and different values clearly. | Make value comparison scannable without summaries standing in for data. | high | Missing values, equal values, and changed values have distinct accessible text and visual states. |
| `BPM087-M3-08` | Add responsive and accessible compare layout. | Keep two-column comparison usable on desktop and mobile. | high | Desktop renders two stable value columns; mobile keeps setting labels and both values readable without overlap or horizontal page overflow. |
| `BPM087-M3-09` | Add compare route API or data-loading helpers if needed. | Keep frontend data fetches simple and tested. | medium | Compare page loads only the profile data it needs, handles API errors, and reuses existing `/api/profiles` contracts where sufficient. |

## Milestone 4: Remove Comparison From Library And Add Compare Navigation

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M4-01` | Remove Library comparison DOM. | Delete the embedded comparison panel from the Library page. | medium | `/profiles` no longer contains `#compare-panel`, `#compare-empty`, `#compare-active`, or comparison result lists. |
| `BPM087-M4-02` | Remove Library comparison state and actions. | Delete Library-specific compare state, diff rendering, and row compare buttons. | high | `profiles_library_bootstrap.js` no longer has two-profile compare state or `data-compare-profile-id` handlers. |
| `BPM087-M4-03` | Add a Library button that opens the comparison interface. | Preserve discoverability from Library without embedding comparison. | medium | Library toolbar exposes a clear "Compare profiles" navigation control pointing to `/profiles/compare`. |
| `BPM087-M4-04` | Update Library row action layout after compare removal. | Keep action density and wrapping polished after removing one row action. | medium | Library rows do not leave empty gaps, overflow, or stale selected-compare styling. |
| `BPM087-M4-05` | Remove stale Library comparison CSS and locale keys. | Avoid dead UI assets after the feature move. | medium | Library-only compare selectors and Library-only compare copy are removed unless reused by the new compare route. |
| `BPM087-M4-06` | Rewrite Library DOM and static contract tests. | Make tests enforce the new boundary. | medium | Tests assert that Library has the compare navigation button and does not expose embedded comparison UI. |

## Milestone 4A: Remove Comparison From Editor And Workspace

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M4A-01` | Remove editor comparison DOM. | Delete editor/workspace comparison panels and clone handoff compare controls. | high | Editor, settings, and JSON routes no longer expose comparison panels or compare-specific clone handoff actions. |
| `BPM087-M4A-02` | Remove editor comparison state and rendering. | Delete current-vs-saved compare state, snapshot diff rendering, and editor comparison status wiring. | high | `profiles_workspace.js`, `profiles_workspace_state.js`, `profiles_dom.js`, and `profiles_runtime.js` no longer carry profile-comparison UI code. |
| `BPM087-M4A-03` | Rewrite editor comparison tests. | Make static and DOM tests enforce the dedicated-route boundary. | medium | Tests fail if editor/workspace routes reintroduce profile comparison UI or state. |

## Milestone 5: Clone Naming Workflow

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M5-01` | Define clone naming UX and validation. | Choose where and when the user names the clone. | high | The accepted design covers Library duplicate, editor duplicate, default suggestion, cancel, empty name, and duplicate-name handling. |
| `BPM087-M5-02` | Add Library clone-name control. | Let users choose the clone name when starting from Library. | high | Clicking duplicate opens a focused name prompt/modal/control before opening or creating the clone draft. |
| `BPM087-M5-03` | Pass the chosen clone name into the new-profile draft. | Replace automatic-only clone naming with explicit user choice. | high | `/profiles/new?clone_from=...` or its replacement initializes the draft name from the user's chosen clone name. |
| `BPM087-M5-04` | Preserve useful source data while excluding owner. | Copy flags, schema, description, and compliance without copying removed owner metadata. | medium | Clone drafts retain source configuration and description but have no owner field or owner payload. |
| `BPM087-M5-05` | Validate clone save conflicts cleanly. | Surface duplicate-name failures at the clone naming step or save step. | medium | Duplicate clone names produce localized, actionable errors and do not silently overwrite profiles. |
| `BPM087-M5-06` | Update clone handoff copy and tests. | Keep clone guidance accurate after explicit naming and owner removal. | medium | Locale keys and tests no longer tell users to update owner, and clone tests cover custom clone names. |

## Milestone 6: Remove Profile Owner From Runtime Product

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M6-01` | Add an Alembic migration that drops profile owner storage. | Remove the owner column and owner index from current databases. | high | Migration handles SQLite batch mode and removes `profiles.owner` and `ix_profiles_owner` from upgraded schemas. |
| `BPM087-M6-02` | Remove owner from ORM and Pydantic profile schemas. | Stop representing owner in runtime profile models. | high | `Profile`, `ProfileCreate`, `ProfileUpdate`, and `ProfileRead` do not expose owner. |
| `BPM087-M6-03` | Remove owner filters from profile service and API routes. | Stop accepting owner as a list/stats filter. | high | `/api/profiles` and `/api/profiles/stats` no longer document or apply owner filters. |
| `BPM087-M6-04` | Remove owner from Firefox policies import contracts. | Stop importing owner metadata into profiles. | high | JSON and multipart import schemas omit owner, and import responses never include owner. |
| `BPM087-M6-05` | Remove owner from frontend forms and state snapshots. | Delete hidden owner inputs and payload wiring. | high | Frontend create/update payloads, form state, compare snapshots, clone drafts, and conflict-copy flows have no owner field. |
| `BPM087-M6-06` | Remove owner from Library rows and current copy. | Replace the old owner context with description or another useful non-owner context. | medium | Library table no longer renders owner values or "No owner" fallback text. |
| `BPM087-M6-07` | Remove owner locale keys and generated catalogs. | Keep localization contracts in parity after deleting owner copy. | medium | Source catalogs, built catalogs, catalog order, and locale tests have no profile-owner UI keys. |
| `BPM087-M6-08` | Update tests and fixtures for ownerless profiles. | Make the test suite enforce the removal. | high | API, service, migration, UI, support, and browser-smoke tests stop sending or asserting profile owner. |
| `BPM087-M6-09` | Add a no-owner regression contract. | Prevent accidental reintroduction. | medium | A focused test fails if current runtime schemas, OpenAPI profile responses, or active UI templates expose profile owner again. |

## Milestone 7: Localization, Documentation, And UI QA

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M7-01` | Add compare interface source copy in English. | Provide product-quality copy for the new route. | medium | English locale source includes compare route labels, selection states, table labels, missing/equal/different states, and errors. |
| `BPM087-M7-02` | Update all supported locale catalogs. | Maintain six-locale key parity. | high | `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` catalogs build successfully with no missing or extra keys. |
| `BPM087-M7-03` | Update visible-English and terminology contracts. | Keep localization QA aligned with new copy and deleted owner copy. | medium | Locale contract fixtures allow intended technical terms and reject stale owner UI strings. |
| `BPM087-M7-04` | Add compare route DOM and layout contract tests. | Cover the new UI at the HTML/static level. | medium | Tests assert compare route controls, two-column table anchors, and absence of Library/editor-only controls. |
| `BPM087-M7-05` | Add browser UI smoke for comparison and clone naming. | Verify the primary user workflows in Chromium/Selenium. | high | Browser smoke selects two profiles, sees two value columns, opens compare from Library, and creates a named clone draft. |
| `BPM087-M7-06` | Update active docs for route ownership. | Keep system maps and route docs aligned with the new surface. | medium | Active architecture docs list `/profiles/compare` and no longer describe Library as owning comparison. |

## Milestone 8: Final Quality, Release Docs, And Handoff

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM087-M8-01` | Run `make typecheck`. | Verify static typing after schema and frontend-adjacent backend changes. | medium | `make typecheck` passes. |
| `BPM087-M8-02` | Run `make lint`. | Verify style and lint contracts. | low | `make lint` passes. |
| `BPM087-M8-03` | Run `pytest -q`. | Verify the default test suite. | high | `pytest -q` passes without owner or Library-compare regressions. |
| `BPM087-M8-04` | Run `make coverage`. | Verify coverage with code-surface reporting. | high | `make coverage` passes and reports covered code surface. |
| `BPM087-M8-05` | Bring covered code surface to 100% if it falls below 100%. | Do not accept coverage debt for this epic. | high | Any coverage drop is fixed with focused tests, removed unreachable code, or documented removal of dead paths. |
| `BPM087-M8-06` | Run `make test-ui`. | Verify Chromium/Selenium product logic. | extra high | `make test-ui` passes, including comparison and clone naming smoke coverage. |
| `BPM087-M8-07` | Refresh README for the completed 0.8.7 product state. | Document the actual finished behavior. | medium | README describes `/profiles/compare`, ownerless profiles, clone naming, commands, supported schemas, and current workflows while preserving maintainer copyright and email-topic information. |
| `BPM087-M8-08` | Finalize `CHANGELOG.md` for `0.8.7`. | Preserve historical release notes and summarize the completed epic. | low | Changelog entry includes comparison route, Library cleanup, clone naming, owner removal, tests, and docs updates. |
| `BPM087-M8-09` | Update docs index after final docs changes. | Keep documentation inventory complete. | low | `docs/docs-index.md` lists every maintained docs file exactly once with correct status. |
| `BPM087-M8-10` | Create a git commit for the completed epic. | Produce a clean handoff point. | medium | Commit includes only intended 0.8.7 changes and has a clear message. |
| `BPM087-M8-11` | Provide the maintainer-run push command. | Do not push from backlog execution. | low | Final report prints the exact `git push` command for the maintainer to run manually. |

## Suggested Execution Order

1. Version transition and route/owner safety contracts.
2. Shared comparison normalization.
3. Dedicated `/profiles/compare` route and bundle.
4. Library comparison removal and compare navigation.
5. Editor/workspace comparison removal.
6. Clone naming workflow.
7. Owner removal across schema, API, frontend, locales, and tests.
8. Browser UI smoke and final release docs.

## Execution Protocol

When executing this backlog interactively:

1. Show exactly one next task with its ID, essence, acceptance, and minimal reasoning.
2. Wait for explicit maintainer approval.
3. Execute only that approved task.
4. Report what changed and which checks passed.
5. Show the next task for approval.

Do not start executing a backlog task just because this backlog exists.

## Backlog Creation Acceptance Checklist

- Target BPM version is present and normalized as `0.8.7`.
- Epic id and task IDs use stable `BPM087-*` identifiers.
- Milestones are grouped by meaning.
- Every task has `low`, `medium`, `high`, or `extra high` minimal reasoning.
- First milestone includes version transition across product surfaces.
- Final milestone includes mypy via `make typecheck`, Ruff via `make lint`, `pytest -q`,
  `make coverage`, coverage-to-100%, Selenium smoke via `make test-ui`, README refresh,
  changelog entry, commit, and maintainer-run push command.
- README instructions preserve maintainer copyright and email-topic information.
- Changelog instructions preserve previous version history.
- Product language is English while maintainer chat may be Russian.
- Docs index includes this backlog.
- Assumptions and non-goals are explicit.
- Execution protocol requires separate user approval for each task.
