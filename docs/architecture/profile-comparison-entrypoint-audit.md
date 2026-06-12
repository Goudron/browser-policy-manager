# Profile Comparison Entrypoint Audit

Date: 2026-06-05

Backlog item: `BPM087-M2-01`

This note maps the comparison-owned files that must be considered while BPM 0.8.7 moves
saved-profile comparison out of the Library and into a dedicated `/profiles/compare` interface.
It is intentionally scoped to comparison entrypoints, copy, styling, and tests; implementation
contracts for the new two-column comparison model belong to `BPM087-M2-02`.

## Current Product Behavior

- Library (`GET /profiles`) owns saved-profile-to-saved-profile comparison today.
- Editor/workspace routes own a separate current-draft-or-current-profile comparison against one
  saved profile.
- Both paths summarize differences by metadata, policy count, preference count, sample changes, and
  guided-area buckets.
- Neither path renders the required BPM 0.8.7 full settings table with one value column per selected
  saved profile.
- Current comparison logic includes owner metadata; this must disappear when owner removal lands.

## BPM087-M2-04 Comparison Ownership Decision

Decision date: 2026-06-05

Profile comparison must be removed from every existing product surface and reintroduced only through
the dedicated `/profiles/compare` interface. Library keeps a single general navigation control that
opens `/profiles/compare`; it must not keep embedded comparison DOM, row-level compare actions,
hidden comparison state, or local diff rendering. Editor/workspace routes must also retire their
current draft-vs-saved comparison panel, compare state, clone-handoff compare actions, and
comparison-specific copy. They should not link to comparison unless a later approved task explicitly
adds a route-level navigation pattern.

This decision applies to profile comparison UI and profile-to-profile diff workflows. Existing
internal equality checks used for wizard dirty detection, preset matching, or search-engine helper
logic are not profile comparison entrypoints and may remain under their current ownership.

## BPM087-M3-09 Compare Data Loading Decision

Decision date: 2026-06-05

The dedicated `/profiles/compare` interface does not need a separate compare-specific API endpoint
for the current BPM 0.8.7 scope. It reuses the existing profile contracts:

- Search and quick selection use `GET /api/profiles` through `BPMProfilesData.listProfiles()` with
  active lifecycle filters, `include_deleted=false`, and newest-updated sorting.
- Final left/right selection and URL preselection use `GET /api/profiles/{id}` through
  `BPMProfilesData.getProfile()` with `includeDeleted=false`, so the comparison table renders from
  the same saved-profile payload contract as the rest of the application.
- Missing, deleted, archived, or invalid preselected profile ids are ignored silently during initial
  route loading; explicit user selection failures render the side-local API error state.
- The route owns loading, empty, and error states per side. It must not add `/api/profiles/compare`
  unless a later approved task introduces server-side compare semantics that cannot be represented
  by the existing saved-profile read contracts.

## Library Comparison Boundary

Library comparison has been removed and replaced by navigation to `/profiles/compare`:

| File | BPM 0.8.7 comparison ownership | Guardrail |
| --- | --- | --- |
| `app/templates/profiles/_page_library_workspace.html` | Owns the Library entry link to `/profiles/compare`. | Do not reintroduce embedded comparison panels, summary cards, or change lists. |
| `app/static/profiles_library_bootstrap.js` | Owns Library list rendering, clone naming, lifecycle, and navigation. | Do not keep Library compare state, row compare handlers, or panel rendering. |
| `app/static/profiles_library.js` | Route entrypoint that starts the Library bootstrap. | Keep as Library-only entrypoint; it should not initialize comparison UI. |
| `app/static/profiles_css/10-library.css` | Owns Library table and clone-name controls. | Do not reintroduce Library-only compare button or compare-panel selectors. |
| `app/static/profiles.css` | Generated CSS bundle. | Rebuild after source CSS changes; do not hand-edit generated CSS. |

## Editor And Workspace Comparison Files

These files contain existing non-Library comparison logic. `BPM087-M2-04` decided to remove editor
profile comparison instead of preserving it or linking it to `/profiles/compare`.

| File | Current comparison ownership | Expected BPM 0.8.7 direction |
| --- | --- | --- |
| `app/static/profiles_workspace.js` | Maintains `compareProfileState`, builds current-vs-saved snapshots, computes diffs, renders editor compare panel state, and handles clone handoff compare actions. | Remove editor comparison state, diff rendering, panel updates, and clone handoff compare actions. |
| `app/static/profiles_workspace_state.js` | Provides compare-base normalization and payload helpers; pure normalization now delegates to `profiles_compare_state.js`. | Remove editor-only compare-base helpers once workspace comparison is retired; keep shared compare helpers for `/profiles/compare`. |
| `app/static/profiles_dom.js` | Reads compare panel elements for editor routes. | Remove editor compare panel element lookups when editor comparison DOM is retired. |
| `app/static/profiles_runtime.js` | Includes compare-related selectors for localized status/help updates and clone handoff compare actions. | Remove comparison selectors and clone handoff compare wiring from editor runtime. |
| `app/static/profiles_wizard_flow.js` | Uses `normalizeForCompare` for wizard-step change detection, not the profile comparison panel. | Treat as adjacent comparison-style logic; do not move it unless a later task intentionally centralizes pure value normalization. |
| `app/static/profiles_network.js` | Uses `normalizeForCompare` for preset matching, not profile comparison UI. | Out of scope for Library removal; useful only as a normalization pattern reference. |
| `app/static/profiles_search_engines.js` | Uses local compare counters for search-engine preset matching. | Out of scope for profile comparison. |

## Route And Asset Loading Touchpoints

The dedicated compare route must follow the existing route asset conventions:

| File | Current role | Expected BPM 0.8.7 direction |
| --- | --- | --- |
| `app/web/profiles.py` | Defines Library, new, edit, settings, and JSON routes. | Add `GET /profiles/compare`. |
| `app/web/profiles_context.py` | Builds shared route context, locale data, schema catalogs, and asset version. | Reuse only the context needed by compare; avoid editor-only catalog bloat if practical. |
| `app/templates/profiles/_page_route_assets.html` | Chooses scripts and styles by `profiles_template_kind`; Library currently loads shared scripts plus Library bootstrap. | Add compare-specific script loading without Monaco or editor-only bundles. |
| `app/templates/profiles/_page_header.html` | Shared header currently labels profile count as Library. | Check whether compare route should reuse or simplify the header counter. |
| `app/templates/profiles.html`, `profiles_library.html`, `profiles_editor.html`, `profiles_settings.html`, `profiles_json.html` | Existing top-level route templates. | Add a compare top-level template if the current shell split needs one. |

## Locale And Copy Touchpoints

Comparison source copy currently lives in the Library namespace even when some keys are also used by
editor comparison. These files must be reviewed when moving comparison into its own route and
retiring existing comparison entrypoints:

| File or pattern | Current comparison ownership | Expected BPM 0.8.7 direction |
| --- | --- | --- |
| `app/i18n_src/en/library.json` | English source keys for the `/profiles/compare` route and the Library navigation action. | Keep only route-owned compare copy such as `profiles.compare_route_title`, search labels, table labels, and value-state labels. |
| `app/i18n_src/{ru,de,zh-CN,fr,es-ES}/library.json` | Localized dedicated compare route copy. | Keep key parity with English and avoid Library-embedded comparison copy. |
| `app/i18n_src/{locale}/common.json` | Shared shell/status keys. | Do not carry editor-only comparison status copy. |
| `app/i18n_src/catalog-order.json` | Orders generated compare route keys. | Keep only active compare route keys and the Library navigation action. |
| `app/i18n/{locale}.json` | Generated runtime catalogs. | Rebuild with `make build-locale-catalogs` after source copy changes. |
| `app/i18n_src/README.md` | Documents locale namespace ownership. | Compare copy remains route-owned; Library only provides the entry link. |

Profile-owner comparison metadata has been removed with the owner cleanup milestone.

## BPM0871-M2-01 Compare Locale Bootstrapping Audit

Audit date: 2026-06-11

The compare route reuses the shared page header, so the language and theme selectors are rendered on
`/profiles/compare`. The locale runtime path is incomplete:

- Server-side initial copy is resolved in `app/web/profiles_context.py` from `Accept-Language` only.
  It does not know about the browser `localStorage` preference that Library writes.
- `app/static/profiles_page_bootstrap.js` reads the embedded `profiles-initial-locale` payload and
  exposes `window.__BPM_INITIAL_LANG__` and `window.__BPM_INITIAL_LOCALE__` for every profile route.
- Library loads `app/static/profiles_library_bootstrap.js`, which reads `bpm-lang-mode`, resolves
  `system` language through `BPMProfilesPlatform.resolveBrowserLanguage`, fetches `/i18n/{lang}.json`,
  updates `window.__BPM_INITIAL_LOCALE__`, applies `[data-i18n]` and placeholder/title/aria-label
  text, persists language changes, and reloads Library data.
- Editor/settings/JSON routes load the editor runtime chain, where `profiles_runtime.js` exposes the
  same `applyLanguageMode`/`loadLocale` behavior for non-Library profile surfaces.
- Compare loads only shared scripts, `profiles_compare_state.js`, and `profiles_compare.js`.
  It does not load Library bootstrap or editor runtime, and `profiles_compare.js` captures
  `const locale = windowRef.__BPM_INITIAL_LOCALE__ || {}` once during `start()`.

Observed consequence: changing `#lang` on `/profiles/compare` has no compare-owned listener, so the
selector value can change without applying translated text. Opening compare from Library also falls
back to the server-resolved initial locale unless a compare-specific runtime reads the already
persisted `bpm-lang-mode` value and applies it after the new tab loads.

The fix path for BPM 0.8.7.1 should give compare a route-owned locale bootstrap instead of loading
the Library or editor runtime wholesale. That bootstrap needs to read and write the same
`bpm-lang-mode` key, use the shared platform language resolver, fetch `/i18n/{lang}.json`, update
`window.__BPM_INITIAL_LANG__` and `window.__BPM_INITIAL_LOCALE__`, apply text to all shared
`data-i18n` attributes, and ask `profiles_compare.js` to re-render selected summaries, result states,
and the comparison table after locale changes.

## Test Touchpoints

These tests protect the completed comparison boundary:

| File | BPM 0.8.7 assertion area | Guardrail |
| --- | --- | --- |
| `tests/web_profiles_page/test_library_layout_contracts.py` | Library has compare navigation only, compare state lives in compare assets. | Keep Library compare state and row compare actions out. |
| `tests/web_profiles_page/test_route_dom_contracts.py` | Library/editor routes exclude comparison DOM; `/profiles/compare` owns the compare DOM contract. | Keep `#compare-page` as the only comparison UI surface. |
| `tests/web_profiles_page_helpers.py` | Locale helper assertions track ownerless Library copy and active compare route copy. | Do not re-add removed Library compare locale keys. |
| `tests/test_ui_smoke_profile_workflow.py` | Runtime locale catalogs and source contracts exclude stale Library compare keys. | Keep old compare summary/guided keys absent. |
| `tests/test_zh_cn_script_layout_contract.py` | Chinese layout/source keys stay ownerless and Library-compare-free. | Keep removed Library compare copy out. |
| `tests/tools/test_build_locale_catalogs.py` | Maps active compare route keys to the `library` namespace. | Keep classifier coverage on `profiles.compare_route_title` while no dedicated compare namespace exists. |
| `tests/fixtures/locale_contracts/visible_english_allowlists.json` | Allows comparison-related English terms. | Review after new route copy and owner removal. |

## Implementation Notes For The Next Tasks

- The compare route owns all profile comparison. Library links to it, and editor/workspace routes do
  not keep a comparison panel or profile-diff workflow.
- Reusable comparison normalization lives in compare-specific state and entrypoint assets.
- The comparison model compares the union of policy and `Preferences` settings present in either
  selected profile, with stable ordering and readable missing-value states.
- Removal remains guarded by tests that reject Library compare state, editor compare state, clone
  handoff compare actions, stale compare CSS, and old comparison locale keys.
- Owner cleanup remains guarded by tests that reject profile-owner labels or values in active
  runtime surfaces.
