# BPM 0.8.7.1 Compare And Clone UI Polish Backlog

Date: 2026-06-11

This backlog defines the BPM 0.8.7.1 patch-release work for polishing the dedicated profile
comparison interface and the Library clone-name controls after the BPM 0.8.7 comparison move.

Product source, UI copy, README, changelog, and maintained documentation stay in English. Maintainer
chat may be Russian, but implementation copy must not switch to Russian unless the task is explicitly
about localization.

## Scope Summary

- Target BPM version: `0.8.7.1`.
- Compact epic id: `BPM0871`.
- Scope boundary: product UI polish, localization persistence, frontend layout fixes, browser smoke
  coverage, docs, and release metadata.
- Release risk: medium, because the work touches the shared profile shell, compare route runtime,
  localized UI, responsive layouts, and browser UI smoke coverage.
- Primary outcome: `/profiles/compare` behaves like the rest of the product for locale selection,
  profile selection, large profile lists, and setting-table readability.
- Secondary outcome: Library clone-name controls stay inside their container across supported
  locales, long labels, and narrow viewports.

## Current-State Assessment

- BPM 0.8.7 introduced `/profiles/compare` as the only profile comparison surface and Library opens
  it in a new tab.
- The compare route currently does not switch language or theme reliably and does not preserve the
  language selected in Library when the user opens the comparison interface from Library.
- Compare profile selectors use a custom visual pattern that is less consistent with the rest of the
  profile UI than Library/editor controls.
- Profile selector option metadata can visually stick to the profile name, for example name, schema
  version, and timestamp can render without enough separation.
- The selector has search, but its result list needs an explicit bounded scrolling contract so it
  remains usable with a large number of saved profiles.
- The settings comparison table is mostly readable, but the left setting column can duplicate the
  setting name/key, for example rendering a row like `POLICY AIControls AIControls`.
- The comparison table legend/header area can become visually crowded and needs spacing/wrapping
  protection for localized labels.
- In the Library clone-name flow, the right action button can overflow outside the clone panel when
  localized labels are long or the available action width is narrow.
- The current CI workflow no longer runs browser UI checks on GitHub; browser UI smoke remains a
  local/release verification layer.

## Non-Goals And Assumptions

- Do not add new comparison semantics, merge behavior, conflict resolution, or patch generation.
- Do not restore comparison to Library, editor, settings, or JSON routes. `/profiles/compare` remains
  the only profile comparison interface.
- Do not reintroduce profile owner fields, filters, copy, or metadata.
- Do not add a compare-specific backend API unless the existing profile read/list contracts cannot
  support the UI fixes safely.
- Do not move browser UI checks back into GitHub Actions as part of this patch backlog.
- Do not redesign the entire Library or editor UI. Fix only the compare route and clone-name overflow
  defects identified for BPM 0.8.7.1.

## Milestone 1: Version Transition And Release Anchors

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M1-01` | Update project metadata to `0.8.7.1`. | Move package and runtime version surfaces from `0.8.7` to the patch version. | low | `pyproject.toml`, runtime app version, and version tests agree on `0.8.7.1`. |
| `BPM0871-M1-02` | Prepare README version anchors for `0.8.7.1`. | Keep README current while reserving final behavior copy for the final milestone. | low | README version heading names `0.8.7.1` and does not describe the patch as completed before implementation lands. |
| `BPM0871-M1-03` | Add a `CHANGELOG.md` section for `0.8.7.1`. | Create the patch-release note landing zone without overwriting older history. | low | `CHANGELOG.md` has a new `0.8.7.1` section above `0.8.7` and preserves previous release notes. |
| `BPM0871-M1-04` | Update maintained docs anchors that name the current release. | Align active docs with the new patch target while preserving historical notes. | medium | Active docs that should track the current target mention `0.8.7.1`; archive files and explicit historical notes keep their original versions. |
| `BPM0871-M1-05` | Update tests that assert current version surfaces. | Make the patch version transition repeatable. | medium | Focused tests fail on stale `0.8.7` current-version metadata and pass after the transition. |

## Milestone 2: Reproduction, Contracts, And UI Boundaries

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M2-01` | Audit compare route locale bootstrapping. | Identify why compare does not switch language or preserve Library-selected language. | high | A short note or failing tests name the runtime/context path that must be fixed. |
| `BPM0871-M2-02` | Add regression tests for compare locale switching and persistence. | Lock the language bug before changing runtime code. | high | Tests cover switching language on `/profiles/compare` and opening compare from Library with the selected locale preserved. |
| `BPM0871-M2-03` | Add selector layout contracts for profile option text. | Protect against stuck-together name, schema, and timestamp labels. | medium | Static/DOM tests assert separate elements or spacing classes for profile name, schema, and updated timestamp. |
| `BPM0871-M2-04` | Add large-list selector contracts. | Ensure search results remain usable with many profiles. | medium | Tests assert a bounded scroll container, stable option height, and no page-level overflow requirement for large result sets. |
| `BPM0871-M2-05` | Add comparison table setting-identity contracts. | Prevent duplicate setting names in the left column. | medium | Tests fail if a setting row renders the same setting key/name twice in the setting identity cell. |
| `BPM0871-M2-06` | Add clone-name overflow contracts. | Capture the Library clone action overflow before layout changes. | medium | DOM/CSS tests cover long localized clone action labels and require actions to stay inside the clone panel. |

## Milestone 3: Compare Route Localization, Theme, And Preference Persistence

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M3-01` | Reuse the shared locale and theme runtime on the compare route. | Make compare route language and theme switching match Library/editor behavior. | high | Compare route loads the same locale and theme resolvers, applies selected locale to all compare copy, and applies selected theme without a page-specific dead path. |
| `BPM0871-M3-02` | Preserve Library-selected language and theme when opening compare. | Keep navigation from Library to compare consistent across tabs. | high | Opening `/profiles/compare` from Library uses the currently selected locale and theme in the new tab. |
| `BPM0871-M3-03` | Persist compare language and theme changes through reloads and navigation. | Make compare participate in product-wide locale and theme preferences. | high | Changing language or theme on compare survives reload and is reflected when navigating back to Library. |
| `BPM0871-M3-04` | Update compare locale source and generated catalogs if needed. | Keep six-locale parity after runtime fixes. | medium | `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES` catalogs build with no missing or extra compare keys. |
| `BPM0871-M3-05` | Update locale contracts for compare route copy. | Keep localization tests aligned with active compare UI. | medium | Locale matrix and visible-English contracts cover active compare labels and do not permit stale duplicate/placeholder copy. |

## Milestone 4: Compare Profile Selector Consistency And Scale

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M4-01` | Align compare selector controls with existing profile UI patterns. | Make selector search and options feel consistent with Library/editor controls. | high | Search inputs, selected summaries, empty states, and option rows reuse or closely match existing design tokens and spacing. |
| `BPM0871-M4-02` | Separate option name, schema, and timestamp rendering. | Fix visually stuck selector labels. | medium | Profile option rows render the profile name, schema version, and updated time with clear spacing at desktop and mobile widths. |
| `BPM0871-M4-03` | Add bounded scrolling for selector result lists. | Keep profile selection usable with many saved profiles. | high | Each selector list has a max height, vertical scroll, and stable behavior with at least 50 profiles. |
| `BPM0871-M4-04` | Preserve keyboard and focus behavior in the selector. | Avoid regressing accessibility while changing layout. | high | Users can search, tab through options, select a profile, and see focus states without layout jumps. |
| `BPM0871-M4-05` | Polish selector responsive behavior. | Prevent overlap and horizontal overflow in narrow viewports. | high | Mobile and narrow desktop selectors wrap metadata cleanly and do not push selected cards outside the page. |

## Milestone 5: Comparison Table Readability

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M5-01` | Define one canonical setting identity display. | Decide what the left column should show for policies and preferences. | medium | The setting identity contract names one type badge, one readable label/key, and optional secondary metadata without duplication. |
| `BPM0871-M5-02` | Remove duplicate setting names from table rows. | Fix rows like `POLICY AIControls AIControls`. | high | Each setting row renders the policy/preference identifier once in the main label and never repeats the same key as adjacent text. |
| `BPM0871-M5-03` | Improve comparison table legend and header spacing. | Fix crowded labels such as missing/same/different states. | medium | Legend items and the `Setting` header wrap or space consistently in all supported locales. |
| `BPM0871-M5-04` | Protect table columns from long setting names and values. | Keep the two-value comparison table usable with realistic enterprise policies. | high | Long keys, localized labels, JSON values, and missing/equal/different state labels do not overlap or force incoherent page overflow. |
| `BPM0871-M5-05` | Add focused table rendering tests. | Lock the table polish against regressions. | medium | Unit/DOM tests cover policy rows, preference rows, duplicate-name prevention, long labels, and missing-value states. |

## Milestone 6: Library Clone-Name Layout Polish

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M6-01` | Audit Library clone-name action layout. | Identify the exact container and breakpoint where the right action overflows. | medium | A focused note or failing test names the clone panel, action group, and viewport/locale condition. |
| `BPM0871-M6-02` | Refactor clone-name action wrapping. | Keep action buttons inside the clone panel. | medium | Long labels wrap or stack within the panel, and neither primary nor secondary action escapes the container. |
| `BPM0871-M6-03` | Align clone-name controls with Library action sizing. | Keep clone controls visually consistent with other Library actions. | medium | Input, primary action, cancel action, and helper text use stable widths, gaps, and responsive constraints. |
| `BPM0871-M6-04` | Add localized clone layout coverage. | Protect Russian and other long-label locales. | medium | Tests include at least Russian and one Latin locale with long labels and verify no overflow-prone classes or dimensions. |

## Milestone 7: Browser UI Smoke And Visual Regression Coverage

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M7-01` | Add browser smoke for compare locale switching. | Verify the language bug in a real browser. | extra high | Selenium opens Library, switches locale, opens compare in a new tab, and sees compare copy in the selected locale. |
| `BPM0871-M7-02` | Add browser smoke for large compare selector lists. | Verify selector scrolling with many profiles. | high | Selenium seeds many profiles, searches, scrolls the selector list, and selects profiles without page overflow. |
| `BPM0871-M7-03` | Add browser smoke for comparison table setting labels. | Verify duplicate labels are gone in rendered UI. | high | Selenium compares profiles and asserts setting identity cells do not duplicate policy/preference keys. |
| `BPM0871-M7-04` | Add browser smoke for clone-name action overflow. | Verify clone controls stay inside the Library card/panel. | high | Selenium opens clone naming in a long-label locale and verifies action buttons remain inside the clone panel bounds. |
| `BPM0871-M7-05` | Capture local visual QA notes for the fixed screenshots. | Keep review evidence without committing generated screenshots. | medium | The final report lists inspected viewports/routes and stores any local screenshots only in ignored artifact paths. |

## Milestone 8: Final Quality, Release Docs, And Handoff

| ID | Task | Essence | Minimal reasoning | Acceptance |
| --- | --- | --- | --- | --- |
| `BPM0871-M8-01` | Run `make typecheck`. | Verify static typing after frontend-adjacent changes. | medium | `make typecheck` passes. |
| `BPM0871-M8-02` | Run `make lint`. | Verify Ruff style and lint contracts. | low | `make lint` passes. |
| `BPM0871-M8-03` | Run `pytest -q`. | Verify the default non-browser suite. | high | `pytest -q` passes with compare and clone layout regressions covered. |
| `BPM0871-M8-04` | Run `make coverage`. | Verify coverage with code-surface reporting. | high | `make coverage` passes and reports covered code surface. |
| `BPM0871-M8-05` | Bring covered code surface to 100% if it falls below 100%. | Do not accept coverage debt for this patch epic. | high | Any coverage drop is fixed with focused tests, removed unreachable code, or documented removal of dead paths. |
| `BPM0871-M8-06` | Run `make test-ui` with immediate sandbox escalation. | Verify local Chromium/Selenium product behavior without a doomed sandbox trial. | extra high | `make test-ui` is run outside the Codex sandbox from the start and passes, including compare locale, large selector, table label, and clone overflow smoke coverage. |
| `BPM0871-M8-07` | Refresh README for the completed 0.8.7.1 product state. | Document the actual fixed behavior. | medium | README describes the current compare/clone behavior, commands, supported locales, and test workflow while preserving maintainer copyright and email-topic information. |
| `BPM0871-M8-08` | Finalize `CHANGELOG.md` for `0.8.7.1`. | Preserve historical release notes and summarize the patch. | low | Changelog entry includes compare locale persistence, selector polish, table label fix, clone overflow fix, and tests. |
| `BPM0871-M8-09` | Update docs index after final docs changes. | Keep documentation inventory complete. | low | `docs/docs-index.md` lists every maintained docs file exactly once with correct status. |
| `BPM0871-M8-10` | Create a git commit for the completed patch epic. | Produce a clean handoff point. | medium | Commit includes only intended `0.8.7.1` changes and has a clear message. |
| `BPM0871-M8-11` | Provide the maintainer-run push command. | Do not push from backlog execution. | low | Final report prints the exact `git push` command for the maintainer to run manually. |

## Suggested Execution Order

1. Version transition and failing contracts for the screenshot defects.
2. Compare route locale switching and persistence.
3. Compare selector consistency, spacing, scrolling, and responsive layout.
4. Comparison table setting identity and label deduplication.
5. Library clone-name overflow fix.
6. Browser UI smoke coverage for the fixed workflows.
7. Final quality gates, release docs, commit, and maintainer-run push command.

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

- Target BPM version is present and normalized as `0.8.7.1`.
- Epic id and task IDs use stable `BPM0871-*` identifiers.
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
