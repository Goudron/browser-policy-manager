# Backlog 0.7.5: True Separation Of Modes Across Browser Tabs

Date: `2026-04-29`

## Context

This backlog targets version `0.7.5`.

Important: the current repository is still marked as `0.7.0` in [pyproject.toml](../pyproject.toml), while [CHANGELOG.md](../CHANGELOG.md) already states that the architectural follow-up work for the split workspace is planned for `0.7.5-dev`.

## What Is Already Done

The base route split already exists:

- `GET /profiles`
- `GET /profiles/new`
- `GET /profiles/{id}/edit`
- `GET /profiles/{id}/advanced`

This is visible in [app/web/profiles.py](../app/web/profiles.py).

We also already have:

- optimistic locking via `revision`
- shared `save` and `validate`
- `focus` and `return` support for the advanced route
- tests for the route contract and DOM contract

This is a good base, but it is still not "true separation of functions between windows/tabs".

## Findings About The Current State

### 1. The split is mostly route-level, not architectural

The `library`, `editor`, and `advanced` templates exist, but they all still pull the same shell:

- [app/templates/profiles_library.html](../app/templates/profiles_library.html)
- [app/templates/profiles_advanced.html](../app/templates/profiles_advanced.html)
- [app/templates/profiles/_page_shell.html](../app/templates/profiles/_page_shell.html)

Right now `_page_shell.html` always includes:

- header
- wizard
- command deck
- workspace

So the modes are separated mostly by hiding blocks through CSS and runtime logic, not by real layout composition.

### 2. All modes still load one heavy shared frontend runtime

[app/templates/profiles/_page_document.html](../app/templates/profiles/_page_document.html) loads the same large JS bundle set for library, guided editor, and advanced route.

As a result:

- library knows about wizard and Monaco
- advanced route knows about the guided wizard
- the modes are coupled through shared DOM ids, data attributes, and conditional runtime branches

### 3. The library still contains editor-oriented surfaces

In [app/templates/profiles/_page_workspace.html](../app/templates/profiles/_page_workspace.html), the library still lives next to:

- overview panel
- compare panel
- workspace scope switch
- advanced handoff panel
- editor panel

Even when some parts are hidden, the page is still modeled as one combined workspace.

### 4. The guided editor is not truly "guided-only" yet

The guided route hides the advanced content grid, but:

- advanced panels still remain in the DOM
- the runtime still keeps `workspaceScope` logic
- the guided path still knows about advanced scope and can switch or route into it

That increases maintenance cost and raises the risk of UI leakage between modes.

### 5. The advanced route does not yet separate "advanced settings" from "JSON"

Right now `/profiles/{id}/advanced` combines:

- metadata/details
- advanced context
- download strip
- Monaco editor

But the target model requires two separate modes:

1. an advanced settings editor with search
2. a clean JSON editor

Those do not exist as separate product surfaces yet.

### 6. New modes still open in the same tab

This directly conflicts with the target model.

Right now:

- library links do not consistently use `target="_blank"` and `rel="noopener"`
- guided -> advanced transitions are done via `window.location.assign(...)`

So the current UX is still single-tab-first.

### 7. The invariant "each editor only shows functions relevant to that mode" is not satisfied yet

The shared command deck and shared runtime still include:

- lifecycle actions
- library reset
- format
- conflict actions
- shared states that are not needed in every mode

As a result, each mode still carries extra UI and extra logic.

## Target Model For 0.7.5

### Main Modes

1. `/profiles`
   Profile library only.

2. `/profiles/new` and `/profiles/{id}/edit`
   Simplified visual editor only.

3. `/profiles/{id}/settings`
   Advanced settings editor only, with search and detailed policy cards.

4. `/profiles/{id}/json`
   JSON editor only, based on Monaco.

### Shared Rules

1. Every transition into another editor mode opens in a new browser tab.
2. Library contains no wizard, no settings editor, and no JSON editor.
3. Guided editor contains no full advanced settings UI and no Monaco.
4. Advanced settings contains no guided wizard and no Monaco as the primary surface.
5. JSON route contains no wizard and no advanced settings cards, only profile chrome plus Monaco.

### Invariants For All Editor Modes

All three editor modes must always expose:

- information about the profile being edited
- the schema/channel of the profile
- save
- validate
- dirty/saved state
- validation state
- explicit links to the other modes in new tabs

## Architectural Decisions I Recommend We Lock In

### AR-01. Separate not only routes, but also shell composition

We should introduce dedicated shell partials:

- `profiles/_library_shell.html`
- `profiles/_guided_shell.html`
- `profiles/_settings_shell.html`
- `profiles/_json_shell.html`

The current shared shell is useful only as a temporary compatibility bridge. For `0.7.5`, it is already getting in the way.

### AR-02. Extract a shared editor chrome into a reusable partial

We need one common `profile editor chrome` used by:

- guided
- settings
- json

It should contain:

- profile identity
- save
- validate
- validation summary
- dirty/saved state
- links `Open guided`, `Open settings`, `Open JSON`

This keeps behavior consistent without mixing the modes themselves.

### AR-03. Split frontend entrypoints by mode

We should move away from the model where every page knows about everything.

Recommendation:

- `profiles_library_entry.js`
- `profiles_guided_entry.js`
- `profiles_settings_entry.js`
- `profiles_json_entry.js`
- a separate shared core for API/state/utilities

This reduces coupling much more effectively than continuing to patch the shared runtime with more conditional branches.

### AR-04. For 0.7.5, choose a save-first strategy before cross-mode transitions

For unsaved drafts, we should not introduce temporary draft-id routes in this iteration.

Recommendation:

- while the profile is not saved yet, `settings` and `json` stay unavailable as separate tabs
- the UI states this clearly: "Save the profile first"

This is simpler, safer, and aligns with the existing route contract built around `profile_id`.

### AR-05. Treat `focus` deep-linking as a required shared capability

Even after splitting into tabs, we should preserve the ability to open:

- the right policy card in `settings`
- the right area in `json`

So `focus=...` should evolve into a shared navigation contract, not remain a narrow advanced-route hack.

## Backlog

The tasks below are listed in the recommended order. The `Minimum reasoning` field means the minimum sufficient GPT 5.4 reasoning level that should still let the task be done well without unnecessary extra cost.

### P0. Surface Contract And Structural Separation

#### `WS-075-01` Lock The Final Route Contract

Status: Done

Outcome:

- approve the 4 modes: `library`, `guided`, `settings`, `json`
- lock the canonical URLs
- define which actions open new tabs

Why it matters:

- without a stable route contract, the frontend split will keep drifting

Minimum reasoning: `medium`

Decision:

- The target product model for `0.7.5` uses four canonical modes:
  - `GET /profiles`
    Profile library only.
  - `GET /profiles/new`
    Guided editor for a new unsaved draft.
  - `GET /profiles/{id}/edit`
    Guided editor for an existing saved profile.
  - `GET /profiles/{id}/settings`
    Advanced settings editor for an existing saved profile.
  - `GET /profiles/{id}/json`
    Full JSON editor for an existing saved profile.

- `/profiles/{id}/advanced` is not part of the final product vocabulary.
  - During transition, it may remain temporarily as a compatibility route.
  - Its compatibility behavior should be a redirect to `/profiles/{id}/settings`.
  - New UI, new links, tests, and documentation should stop treating `/advanced` as canonical.

- New-tab contract:
  - From the library, opening `Create profile` opens `/profiles/new` in a new tab.
  - From the library, opening an existing profile opens `/profiles/{id}/edit` in a new tab.
  - From any editor mode, opening another editor mode opens a new tab.
  - This includes guided -> settings, guided -> json, settings -> guided, settings -> json, json -> guided, and json -> settings.

- Same-tab contract:
  - `/profiles` remains the library hub and may be reused in the current tab.
  - Save, validate, compare, clone, import, archive, restore, and download do not imply opening a new route.
  - In-editor navigation inside one mode stays in the same tab because it is not a mode switch.

- Unsaved draft contract:
  - `/profiles/new` is the only canonical route for an unsaved draft.
  - `/profiles/new` does not have canonical sibling routes for settings or JSON.
  - `settings` and `json` are available only after the first successful save creates a real `profile_id`.
  - Before that first save, the UI must clearly communicate `Save the profile first`.

- Canonical naming contract for visible UI and docs:
  - `Library`
  - `Guided editor`
  - `Advanced settings`
  - `JSON editor`
  - `Advanced` may still appear only in transitional technical notes, not as the final user-facing route name.

- Query contract:
  - `focus=...` remains part of the shared deep-link strategy for `settings` and `json`.
  - `return=...` is transitional compatibility only.
  - In the final new-tab-first model, `return` is no longer a primary product concept because users keep their source tab.

Implementation note:

- This task intentionally locks the contract first, before code movement.
- All later tasks in this backlog should treat `/settings` and `/json` as the destination model, even if `/advanced` still exists temporarily in code during migration.

#### `WS-075-02` Split Top-Level Shell Templates By Mode

Status: Done

Outcome:

- library template renders only the library shell
- guided template renders only the guided shell
- settings template renders only the settings shell
- json template renders only the json shell

Why it matters:

- right now modes are separated mostly by hiding, not by structure

Minimum reasoning: `high`

Implementation note:

- Added dedicated shell partials for:
  - `library`
  - `guided`
  - `advanced`
  - future `settings`
  - future `json`
- Rewired top-level template entrypoints so `/profiles` no longer points at the old shared shell.
- Added a dedicated library workspace partial so the library route no longer renders the guided wizard, command deck, or editor panel.
- Hardened shared/runtime helpers so the library route can bootstrap safely without editor-only DOM.
- Kept the current `/profiles/{id}/advanced` shell transitional for now, because deeper advanced/settings/json separation belongs to later workstreams in this backlog.

#### `WS-075-03` Split Asset Loading And Bootstrap Entrypoints By Mode

Status: Done

Outcome:

- library does not load Monaco or wizard runtime
- guided does not load settings/json runtime
- settings does not load guided-only runtime
- json does not load guided/settings card runtime

Why it matters:

- this is the core technical debt in the current architecture

Minimum reasoning: `extra high`

Implementation note:

- Locked mode-aware asset loading in [app/templates/profiles/_page_document.html](../app/templates/profiles/_page_document.html), so the library route now boots from a dedicated lightweight chain while guided and advanced continue through explicit editor-mode entrypoints.
- Kept `/profiles` on the shared low-level utilities only:
  - `profiles_utils.js`
  - `profiles_shared.js`
  - `profiles_platform.js`
  - `profiles_data.js`
  - `profiles_library_bootstrap.js`
  - `profiles_library.js`
- Removed editor-only assets from `/profiles`, including:
  - `js-yaml`
  - Monaco CSS/JS
  - wizard catalogs/runtime bootstrap
- Introduced explicit mode entrypoints for the remaining editor routes:
  - [app/static/profiles_guided.js](../app/static/profiles_guided.js)
  - [app/static/profiles_advanced.js](../app/static/profiles_advanced.js)
- Kept guided and advanced on the same transitional editor runtime internals for now, because real runtime-level separation of guided vs advanced/settings/json depends on later workstreams:
  - `WS-075-07`
  - `WS-075-08`
  - `WS-075-09`

#### `WS-075-04` Remove Editor-Only Surfaces From `/profiles`

Status: Done

Outcome:

- the library keeps only:
  - list
  - search
  - create/import
  - compare
  - lifecycle/library actions only if they are truly library-level
- wizard, workspace-scope switch, advanced handoff, editor panel, and shared command deck are removed from the library route

Why it matters:

- the library should be a clean command center, not a hidden editor

Minimum reasoning: `medium`

Implementation note:

- Simplified [app/templates/profiles/_page_library_workspace.html](../app/templates/profiles/_page_library_workspace.html) so `/profiles` now keeps only the library surface plus compare.
- Removed editor-style overview/state surfaces from the library route, including:
  - profile identity summary
  - dirty/saved signal
  - clone handoff panel
  - lifecycle panel
  - compliance panel
  - hidden editor-context helpers tied to the old combined workspace model
- Trimmed [app/static/profiles_library_bootstrap.js](../app/static/profiles_library_bootstrap.js) to match the new library-only DOM contract instead of maintaining editor-state placeholders that no longer belong on `/profiles`.

### P0. New Cross-Mode Navigation Model

#### `WS-075-05` Introduce A Single Navigation Contract: Editor Modes Always Open In New Tabs

Status: Done

Outcome:

- `create/open/settings/json` open with `_blank`
- add `rel="noopener"`
- JS handoffs stop using `location.assign(...)` and open new tabs instead

Why it matters:

- this is a direct product requirement

Minimum reasoning: `medium`

Implementation note:

- Updated library-to-editor links to explicit new-tab behavior in:
  - [app/templates/profiles/_page_library_workspace.html](../app/templates/profiles/_page_library_workspace.html)
  - [app/static/profiles_library_bootstrap.js](../app/static/profiles_library_bootstrap.js)
  - [app/static/profiles_workspace.js](../app/static/profiles_workspace.js)
- Updated guided-to-advanced handoff links to use `target="_blank"` plus `rel="noopener"` in:
  - [app/templates/profiles/_page_workspace.html](../app/templates/profiles/_page_workspace.html)
  - [app/templates/profiles/_page_wizard_step_ai.html](../app/templates/profiles/_page_wizard_step_ai.html)
  - [app/templates/profiles/_page_wizard_step_export.html](../app/templates/profiles/_page_wizard_step_export.html)
- Replaced the JS handoff fallback in [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) so advanced navigation now opens a new tab instead of reusing the current one via `location.assign(...)`.

#### `WS-075-06` Rewrite Dirty-Navigation Rules For The Multi-Tab Model

Status: Done

Outcome:

- opening a new tab does not ask for discard confirmation
- same-tab internal navigation remains guarded only where still relevant
- behavior becomes predictable across guided/settings/json

Why it matters:

- the current navigation guard logic was designed for a single-tab-first model

Minimum reasoning: `high`

Implementation note:

- Reworked the route guard in [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) so dirty-state confirmation is now applied only to same-tab profile route navigation.
- Added explicit cross-tab intent detection for `target="_blank"`, modifier-assisted open-in-new-tab gestures, and non-primary button clicks.
- Removed discard confirmation from the JS advanced handoff path opened via `window.open(...)`, while keeping the `beforeunload` safeguard for true leave/refresh/close flows.

### P0. Shared Editor Chrome

#### `WS-075-07` Extract A Shared Profile Editor Chrome

Status: Done

Outcome:

- one common top block for guided/settings/json
- it always shows:
  - profile name
  - id
  - schema channel
  - dirty/saved state
  - validation state
  - save
  - validate
  - open other modes

Why it matters:

- in every editor, the user must understand exactly what profile is being edited

Minimum reasoning: `high`

Implementation note:

- Extracted a shared editor chrome partial in [app/templates/profiles/_page_editor_chrome.html](../app/templates/profiles/_page_editor_chrome.html) and mounted it from the shared guided/advanced shell.
- Moved the canonical `save` / `validate` controls and the canonical `profile-name` / `profile-type` controls into that shared top block, so guided and advanced now read and edit the same profile identity surface.
- Kept the always-visible editor contract in one place:
  - profile title
  - profile id
  - schema channel
  - dirty/saved state
  - validation state
  - cross-mode links
- Rewired editor mode links through a shared client-side contract in [app/static/profiles_workspace.js](../app/static/profiles_workspace.js), including save-first availability for advanced-settings / JSON tabs.
- Reduced the command deck to secondary actions and conflict handling, which prepares the next action-split workstream without breaking the current runtime contract.

#### `WS-075-08` Rebuild The Action Set Per Mode

Status: Done

Outcome:

- guided/settings/json each get only actions relevant to that mode
- library reset and heavy lifecycle actions leave editor modes
- `format` remains only in the JSON route

Why it matters:

- the current command deck is overloaded and breaks mode boundaries

Minimum reasoning: `medium`

Implementation note:

- Re-scoped the shared command deck in [app/templates/profiles/_page_command_deck.html](../app/templates/profiles/_page_command_deck.html) so editor routes no longer expose one mixed action stack.
- Kept `format` only for the transitional advanced route by gating it on `profiles_template_kind == "advanced"`.
- Removed lifecycle / risk actions from editor mode shells:
  - `restore`
  - `soft-delete`
  - `hard-delete`
  - `reset-library`
- Preserved save-conflict handling and status summary in the deck, because they still belong to active editing work and are shared by the current guided/advanced runtime.
- Hardened [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) so absent mode-specific controls are treated as optional instead of assumed.

### P0. Guided-Only Mode

#### `WS-075-09` Remove `workspaceScope` As A User-Facing Model From The Guided Route

Status: Done

Outcome:

- the guided route no longer knows about an internal guided/advanced switch
- "advanced" buttons become handoff links that open new tabs
- guided runtime no longer carries UI scope-switching logic

Why it matters:

- current `workspaceScope` is a leftover from the old combined page

Minimum reasoning: `high`

Implementation note:

- Removed the guided route `workspaceScope` switch surface from [app/templates/profiles/_page_workspace.html](../app/templates/profiles/_page_workspace.html), leaving guided-to-advanced interaction only through explicit handoff actions.
- Deleted the `workspaceScope` runtime/state branch from [app/static/profiles_runtime.js](../app/static/profiles_runtime.js), including the old `localStorage` restoration path for `bpm-workspace-scope`.
- Replaced visibility gating in [app/static/profiles.css](../app/static/profiles.css) so guided vs advanced-only surfaces now follow `data-profiles-template-kind` instead of a mutable in-page scope model.
- Updated bookmark-focused advanced handoff behavior in [app/static/profiles_extensions.js](../app/static/profiles_extensions.js) to open the advanced route directly in a new tab with the right focus target.

#### `WS-075-10` Reduce The Guided Route To A Simplified-Only Surface

Status: Done

Outcome:

- the guided route keeps only:
  - simplified wizard
  - shared editor chrome
  - targeted handoff buttons
- hidden advanced panels and Monaco containers are removed from the DOM

Why it matters:

- hidden advanced DOM continues to couple the modes and complicates testing

Minimum reasoning: `high`

Implementation note:

- Removed the guided route library/compare and advanced-only surface rendering from [app/templates/profiles/_page_workspace.html](../app/templates/profiles/_page_workspace.html), leaving guided mode with the wizard, shared editor chrome, command deck, and explicit advanced handoff only.
- Introduced a headless Monaco-backed editor adapter in [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) so the guided route can keep its editor-backed state model without rendering a visible Monaco container in the DOM.
- Hardened [app/static/profiles_workspace.js](../app/static/profiles_workspace.js) so library/compare DOM becomes optional for editor routes, which allows the simplified-only guided surface to render without hidden library leftovers.
- Kept the visible Monaco surface only on the transitional advanced route, while guided mode now carries no inline advanced panels and no inline editor frame.

### P0. New Advanced Settings Editor

#### `WS-075-11` Create A New `/profiles/{id}/settings` Route

Status: Done

Outcome:

- a separate settings-only mode
- no wizard
- no Monaco
- focused on searchable advanced controls

Why it matters:

- the requested product model is a dedicated advanced settings mode, not the current hybrid advanced route

Minimum reasoning: `high`

Implementation notes:

- Added a canonical `/profiles/{id}/settings` route and a dedicated `profiles_settings.html` entry template.
- Split `settings` into its own shell with shared editor chrome, command deck, and a settings-specific workspace instead of reusing the old advanced shell.
- Removed Monaco asset loading from the `settings` mode and switched the route to a headless editor-backed runtime path.
- Added a first searchable settings surface driven by schema-shell sections as the base for `WS-075-12`.
- Updated mode links so the explicit "Advanced settings" entry now opens `/settings`, while the transitional JSON link still targets `/advanced`.

#### `WS-075-12` Build The Settings Surface On Top Of The Schema Shell Catalog And Settings Search

Status: Done

Outcome:

- searchable catalog of advanced controls
- cards grouped by policy clusters
- separate sections for:
  - recommended mapped controls
  - additional mapped controls
  - preferences
  - raw fallback

Why it matters:

- the codebase already has strong foundations for this layer, but they are still embedded in the old wizard-centric model

Minimum reasoning: `extra high`

Implementation notes:

- Removed the temporary hidden wizard backing layer from the settings shell and replaced it with a compact preference-support include that only keeps the reusable row/datalist templates needed by the preference runtime.
- Rebuilt [app/templates/profiles/_page_settings_workspace.html](../app/templates/profiles/_page_settings_workspace.html) around visible section cards, settings navigation clusters, schema-shell buckets, and managed-preference surfaces per section.
- Added stable step `id` values to the shared wizard step metadata so settings mode can bind server-rendered step cards to the same canonical section identifiers already used by the catalogs and schema shell.
- Taught settings search to resolve legacy `field:*`, `policy:*`, `preference-*`, and search preset targets to the visible settings cards via `settingsTargetAliases` and schema-shell target resolution instead of relying on hidden wizard DOM.
- Relaxed wizard-only runtime assumptions in [app/static/profiles_wizard_flow.js](../app/static/profiles_wizard_flow.js) and [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) so the settings route can reuse shared state sync without rendering the old stepper UI.
- Expanded schema-shell inline editor coverage for key settings-mode policies including `Proxy`, `Homepage`, `FirefoxHome`, `FirefoxSuggest`, `SearchEngines`, `NewTabPage`, and the main boolean browser-behavior policies, which makes the settings surface directly editable instead of mostly jump-oriented.

#### `WS-075-13` Preserve Deep-Linking In Settings Mode

Status: Done

Outcome:

- handoff from guided/review/search opens the settings tab directly on the right card
- `focus` works at least as well as it does today in the advanced route

Why it matters:

- otherwise the new split will slow users down

Minimum reasoning: `high`

Implementation notes:

- Repointed guided advanced handoff surfaces to the canonical settings route while preserving explicit `focus` targets for contextual jumps such as AI controls and the step-8 export/review shell.
- Added settings-route href builders and focus normalization in [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) so visual handoffs now route `editor` intents to JSON mode and all other advanced intents to settings mode.
- Preserved deep-link resolution on the receiving side by teaching the shared focus bootstrap to recognize settings-only anchors such as `settings-panel` and `settings-schema-shell-step-8`.
- Made editor-mode links route-aware in [app/static/profiles_workspace.js](../app/static/profiles_workspace.js), so `settings` and `json` tabs now carry the correct `return` path for the current mode instead of always assuming the guided route.
- Updated the advanced JSON route to preserve non-editor focus targets when linking back into settings, which keeps `json -> settings` handoffs aligned with the same policy card or section.

### P0. New JSON Mode

#### `WS-075-14` Rename The Current Advanced Monaco Route Into A Dedicated JSON Route

Status: Done

Outcome:

- new canonical route: `/profiles/{id}/json`
- current `/profiles/{id}/advanced` is kept only as a compatibility redirect to `/profiles/{id}/json`

Why it matters:

- JSON must become its own clear mode, both conceptually and in the product

Minimum reasoning: `medium`

Implementation notes:

- Added a canonical `/profiles/{id}/json` route in [app/web/profiles.py](../app/web/profiles.py) and moved the Monaco editor page context onto `route_mode="json"` with the title `JSON editor`.
- Added [app/templates/profiles_json.html](../app/templates/profiles_json.html) and [app/static/profiles_json.js](../app/static/profiles_json.js) so JSON mode now has its own top-level template and entrypoint instead of masquerading as the old advanced route.
- Kept `/profiles/{id}/advanced` as a temporary compatibility route, but changed it to a `307` redirect that preserves safe `return` and `focus` query params when forwarding to `/profiles/{id}/json`.
- Switched shared runtime and workspace routing logic from `advanced` to `json` for the Monaco mode, including editor-mode links, route bootstrap guards, and same-tab/cross-tab route semantics.
- Updated template gating so Monaco-only surfaces such as `format`, `details-panel`, `editor-panel`, and the content grid now belong to `profiles_template_kind == "json"` instead of `advanced`.

#### `WS-075-15` Make `/profiles/{id}/json` A Clean Monaco-Only Mode

Status: Done

Outcome:

- shared editor chrome
- Monaco
- format
- save
- validate
- download
- no wizard and no settings cards

Why it matters:

- this is the direct requirement: "in JSON, only the JSON editor"

Minimum reasoning: `high`

Implementation notes:

- Replaced the transitional JSON shell include with a dedicated [profiles/_json_shell.html](../app/templates/profiles/_json_shell.html) composition, so `/profiles/{id}/json` no longer rides through the old guided/advanced shell stack.
- Moved the JSON route body into [profiles/_page_json_workspace.html](../app/templates/profiles/_page_json_workspace.html) and reduced it to:
  - shared editor chrome
  - Monaco host
  - download link
  - status banner
- Removed hidden advanced/settings carryover from the JSON DOM by stopping JSON mode from rendering:
  - guided wizard panels
  - advanced context panel
  - advanced utility/details panel
  - advanced review strip
- Preserved compatibility for older JSON deep links in [app/static/profiles_runtime.js](../app/static/profiles_runtime.js) by mapping legacy `focus=details|download|context` targets onto the new Monaco-only surface until the explicit deep-link cleanup workstream lands.

#### `WS-075-16` Preserve A JSON Deep-Link Contract

Outcome:

- we can open the JSON tab directly at the right semantic target:
  - editor top
  - raw policy cluster
  - unknown/deprecated area

Why it matters:

- otherwise handoff flows from review and advanced settings will regress

Minimum reasoning: `medium`

### P1. Behavior For Unsaved Drafts

#### `WS-075-17` Explicitly Implement The Save-First Policy For `settings` And `json`

Outcome:

- for a new unsaved draft, `Open settings` and `Open JSON` are disabled
- nearby visible copy says: "Save the profile first"
- after the first save, those transitions become available

Why it matters:

- this is the most reliable and cheapest-to-maintain model for the `0.7.5` iteration

Minimum reasoning: `medium`

### P1. Regression Protection And Quality

#### `WS-075-18` Update DOM Contract Tests Around The Absence Of Unrelated Functions In Each Mode

Outcome:

- library tests fail if wizard/settings/json appears there
- guided tests fail if Monaco/settings shell appears there
- settings tests fail if wizard/Monaco appears there
- json tests fail if guided/settings cards appear there

Why it matters:

- for this effort, it is just as important to prove the absence of irrelevant UI as the presence of the correct UI

Minimum reasoning: `medium`

#### `WS-075-19` Add Browser Regressions For Opening Modes In New Tabs

Outcome:

- tests cover open profile
- open settings
- open JSON
- verify that the source tab keeps its context

Why it matters:

- new-tab behavior is a core product contract of this version

Minimum reasoning: `high`

#### `WS-075-20` Add Browser Regressions For The Shared Editor Chrome

Outcome:

- across all editor modes, tests verify:
  - profile identity
  - save
  - validate
  - status

Why it matters:

- this is the main user-facing invariant after the split

Minimum reasoning: `medium`

#### `WS-075-21` Finish The i18n And Naming Pass Across The 4 Modes

Outcome:

- one consistent terminology set:
  - `Library`
  - `Guided editor`
  - `Advanced settings`
  - `JSON editor`
- aligned RU/EN labels, titles, empty states, and handoff copy

Why it matters:

- after the route split, terminology becomes part of product architecture

Minimum reasoning: `low`

## Recommended Implementation Sequence

### Phase 1. Skeleton

1. `WS-075-01`
2. `WS-075-02`
3. `WS-075-03`
4. `WS-075-07`
5. `WS-075-08`

### Phase 2. True Mode Separation

6. `WS-075-04`
7. `WS-075-05`
8. `WS-075-06`
9. `WS-075-09`
10. `WS-075-10`
11. `WS-075-11`
12. `WS-075-12`
13. `WS-075-13`
14. `WS-075-14`
15. `WS-075-15`
16. `WS-075-16`
17. `WS-075-17`

### Phase 3. Quality Protection

18. `WS-075-18`
19. `WS-075-19`
20. `WS-075-20`
21. `WS-075-21`

## The Most Important Strategic Point

The key turn for `0.7.5` is not simply adding one more route. It is abandoning the model of "one shared frontend workspace where everything is hidden or shown conditionally".

If we keep the current shared-shell/shared-runtime model, the product may become a bit cleaner visually, but it will remain fragile architecturally:

- the modes will keep leaking into each other
- tests will remain dependent on hidden DOM
- every new improvement in guided/settings/json will keep affecting neighboring modes

So I recommend treating these three moves as mandatory for `0.7.5`:

1. mode-specific shells
2. mode-specific JS entrypoints
3. one shared editor chrome on top of truly separated modes

Without that, the version will be "split by URL", but not "split by product".
