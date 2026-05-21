# UI/UX Product Backlog

Date: `2026-05-14`

This backlog turns the UI/UX roadmap into one-off implementation tasks.
The product language remains English. The currently supported UI locales remain `en` and `ru`.
No new locales and no documentation surfaces are part of this backlog.

## Operating Principles

1. Keep the UI focused on current product behavior.
   Remove all references to future documentation, disabled documentation links, and documentation placeholders.

2. Keep both existing locales healthy.
   Every visible UI copy change must update both `app/i18n/en.json` and `app/i18n/ru.json`.

3. Russian localization must follow Mozilla-style Russian.
   Use Mozilla Pontoon and SUMO terminology as the reference style. Avoid unnecessary Anglicisms.
   Examples to verify include terms such as `аккаунт Mozilla`, `куки`, `дополнения`,
   `домашняя страница`, `адресная строка`, `приватность`, and `разрешения сайтов`.

4. The Russian UI must not contain accidental English.
   Allowed exceptions: brands, product names, policy keys, JSON keys, API paths, URLs,
   schema identifiers, extension IDs, and technical identifiers that should remain untranslated.

5. Target product modes:
   - `Library`
   - `Guided editor`
   - `All settings`
   - `JSON editor`

6. `AI & smart features` remains a full standalone step in the Guided editor.
   It is expected to grow as future Firefox versions expose more related controls.

## Reasoning Level Guide For ChatGPT 5.5

- `low`: deterministic cleanup, small copy updates, simple CSS fixes, narrow tests.
- `medium`: localized UI edits across several files, small behavior changes, routine regression work.
- `high`: multi-surface UI changes, stateful behavior, route/template/runtime coordination.
- `extra high`: architecture-level UI restructuring, broad state migration, complex schema-driven behavior.

## Milestone 0: Product Shell And Documentation-Tail Cleanup

Goal: remove stale future-documentation UI, clarify product modes, and fix the most visible layout issues.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| UI-001 | Remove documentation placeholders from UI | Remove disabled doc links, documentation placeholder cards, and "coming later" copy from templates, macros, JS, and locale catalogs. | No visible UI mentions unavailable/future documentation. Tests cover the absence of placeholder tokens. | high |
| UI-002 | Remove obsolete documentation macros | Delete or neutralize helper macros such as documentation placeholder renderers when they no longer have a live use. | Template code no longer renders dead documentation surfaces. No broken includes. | medium |
| UI-003 | Rename `Advanced settings` to `All settings` in UI | Update visible labels, page titles, locale strings, mode switch labels, and copy. Keep route compatibility unless a separate routing change is planned. | Users see `All settings` consistently. No old `Advanced settings` label remains except compatibility comments or historical docs. | medium |
| UI-004 | Clarify mode hierarchy | Make mode switching read as `Guided editor`, `All settings`, `JSON editor`; avoid implying JSON is the same as advanced visual editing. | Mode switch clearly separates task-first, full visual, and raw JSON work. | medium |
| UI-005 | Compact editor overview | Replace the large shared editor overview with a compact profile bar for saved/draft state, schema, dirty/saved state, save, validate, and mode switching. | Main working surface appears in the first viewport on desktop and mobile. | high |
| UI-006 | Fix mobile header overflow | Fix the product header and toolbar layout on narrow screens. | At 390px width, no title or toolbar content is clipped horizontally. | medium |
| UI-007 | Reduce decorative density | Reduce large radii, nested cards, and oversized panels where they make admin workflows slower to scan. | UI reads more like a practical operations tool while retaining the current visual identity. | medium |
| UI-008 | Clean CSS token aliases | Normalize undefined/ambiguous CSS variables such as soft/muted/line aliases. | CSS variables are defined consistently and do not rely on accidental fallbacks. | low |

## Milestone 1: Russian Localization Quality Pass

Goal: keep `ru` as a high-quality Mozilla-style localization, not a literal or mixed-language UI.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| LOC-001 | Create current en/ru UI glossary | Record the terms used by the current UI modes, profile lifecycle, Firefox surfaces, and policy editing concepts. | A small glossary exists for maintainers and is limited to existing `en`/`ru` support. | medium |
| LOC-002 | Audit `ru.json` for accidental English | Scan every visible Russian locale string and classify English fragments as valid technical identifiers or translation defects. | No accidental English remains in Russian UI copy. | medium |
| LOC-003 | Align Russian terms with Pontoon and SUMO | Verify key Firefox/Mozilla terms against Mozilla Pontoon and SUMO style. | Russian strings use Mozilla-style terminology and avoid unnecessary Anglicisms. | high |
| LOC-004 | Audit runtime-generated Russian strings | Review strings produced in JS from templates, data, counts, validation states, and dynamic status messages. | Runtime UI in Russian does not fall back to English unexpectedly. | medium |
| LOC-005 | Add Russian locale allowlist check | Add or update a test/helper that flags English text in `ru.json`, with an allowlist for brands, keys, URLs, IDs, and schema terms. | The test catches obvious English leftovers without blocking valid technical text. | medium |
| LOC-006 | Browser QA pass in Russian | Capture key Library, Guided editor, All settings, and JSON editor screens in Russian. | No unexpected English appears in common UI paths. Layout remains usable with Russian string lengths. | medium |

## Milestone 2: Library As Profile Manager

Goal: make `/profiles` a real profile manager and command center, not only a launcher.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| LIB-001 | Expose library filters | Make schema, active/archived, validation state, and search filters visible. | Users can filter profiles without hidden controls. | medium |
| LIB-002 | Expose sorting controls | Make sorting by updated, created, name, and schema visible. | Sort state is clear and persistent during list reloads. | medium |
| LIB-003 | Redesign desktop profile table | Add denser columns for profile identity, schema, owner/description, status, updated time, and actions. | Table scans well with many profiles. | high |
| LIB-004 | Redesign mobile profile cards | Replace table compression with dedicated mobile cards. | Mobile cards show key metadata and actions without horizontal overflow. | medium |
| LIB-005 | Add row action set | Add actions for `Open`, `All settings`, `JSON`, `Duplicate`, `Export`, and archive/restore. | Common profile work can start directly from the Library. | high |
| LIB-006 | Add direct duplicate from Library | Let users duplicate a profile from the Library without first opening the editor. | Duplicate creates a draft or saved copy with clear handoff. | high |
| LIB-007 | Add archive and restore from Library | Support lifecycle actions directly in the profile list. | Users can archive and restore without opening a profile editor. | high |
| LIB-008 | Add row export for `policies.json` | Let users export a saved active profile from the Library row. | Export is disabled or explained for drafts/archived profiles. | medium |
| LIB-009 | Rework compare selection | Let users pick two profiles directly from the Library for comparison. | Compare no longer depends on a hidden current-profile baseline. | high |
| LIB-010 | Improve import `policies.json` flow | Show import result, created profile, schema channel, and validation state. | Import has a clear completion state and next actions. | high |
| LIB-011 | Add validation summary to Library | Surface last known validation status or an explicit "not validated" state. | Security/admin users can prioritize profiles that need review. | high |
| LIB-012 | Library regression tests | Update unit/browser tests for filters, sorting, row actions, import, compare, and mobile layout. | Library behavior is covered without depending only on screenshots. | medium |

## Milestone 3: Guided Editor Simplification

Goal: reduce the Guided editor from eight steps to six, while keeping the AI step standalone.

Target steps:

1. `Profile & baseline`
2. `Browser access & defaults`
3. `Security & privacy`
4. `Users, add-ons & sites`
5. `AI & smart features`
6. `Review & export`

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| GID-001 | Map current controls to six-step model | Produce the exact mapping from existing controls, data bindings, and summaries to the new step model. | No current guided capability is lost in the target model. | high |
| GID-002 | Update wizard step catalog | Change the step registry, labels, progress text, and locale strings to the six-step model. | Navigation shows exactly six steps in both locales. | medium |
| GID-003 | Rebuild `Profile & baseline` | Keep profile identity, schema channel, scenario, starter preset, and CIS layer in the first step. | First step remains the clear starting point for new and existing profiles. | high |
| GID-004 | Merge browser access/defaults controls | Move network/proxy, updates, downloads, homepage/startup, search, and navigation into one coherent step. | The step has local anchors/sections and remains scannable. | extra high |
| GID-005 | Rebuild `Security & privacy` | Consolidate telemetry, permissions, cookies, tracking protection, cleanup, and hardening. | Security posture is easier to review without losing controls. | high |
| GID-006 | Rebuild users/add-ons/sites step | Consolidate accounts, language, translation, extensions, bookmarks, and website handling. | The mixed operational areas are grouped and navigable. | high |
| GID-007 | Preserve standalone AI step | Keep `AI & smart features` as its own full step and remove documentation-tail placeholders from it. | AI remains first-class and ready for future Firefox growth without future-doc UI. | medium |
| GID-008 | Rebuild review/export step for six steps | Update summaries, counts, jump targets, guided-area grouping, and final review copy. | Review reflects the new six-step model. | high |
| GID-009 | Update JS step mappings | Update compare grouping, preference/policy area mapping, search jumps, and step memory references. | No stale step numbers or obsolete area names remain in runtime behavior. | extra high |
| GID-010 | Guided editor regression tests | Update static tests, UI smoke tests, and browser audit scripts for the six-step wizard. | Tests prove the new step model loads, edits, saves, validates, and exports. | high |

## Milestone 4: All Settings

Goal: replace the current step-shaped advanced surface with a visual manager for the whole schema.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| ALL-001 | Rename visual surface to `All settings` | Update the `/settings` page copy and mode labels without breaking route compatibility. | Users understand this is the complete visual settings manager. | medium |
| ALL-002 | Design schema category model | Build a category/navigation model that is independent of Guided editor steps. | All settings can be browsed by policy domain, not wizard step. | extra high |
| ALL-003 | Build settings list shell | Create the list/table of policy keys and managed preferences with current value state. | Users can scan all available and configured settings. | extra high |
| ALL-004 | Add All settings filters | Add filters for configured, available, guided-covered, all-settings only, invalid, deprecated, and unknown. | Users can quickly isolate review areas. | high |
| ALL-005 | Build setting detail panel | Add typed editors, current value, reset/remove actions, validation state, and schema metadata for one selected setting. | A user can edit a single setting visually without JSON. | extra high |
| ALL-006 | Include Guided-covered settings | Ensure every Guided editor setting is editable in All settings too. | All settings is a superset of Guided editor. | high |
| ALL-007 | Add managed preferences manager | Integrate managed preferences as first-class entries, not only step-specific subpanels. | Preferences can be searched, added, edited, and removed in All settings. | high |
| ALL-008 | Add unknown/deprecated/raw review | Provide a dedicated review surface for imported or unsupported keys. | Imported profile data is preserved and visible for review. | extra high |
| ALL-009 | Add All settings search | Search by label, policy key, preference key, Firefox area, and current value state. | Search results are actionable and can open the detail panel. | high |
| ALL-010 | Wire save/validate state | Keep dirty state, save, validate, and conflict handling consistent with other editors. | All settings edits use the same persistence model as Guided and JSON. | high |
| ALL-011 | All settings regression tests | Add route, rendering, filtering, editing, validation, and import-data preservation tests. | The schema manager surface has reliable coverage. | high |

## Milestone 5: JSON Editor Polish

Goal: keep JSON as a precise expert/raw editor that complements All settings.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| JSON-001 | Compact JSON header | Reduce the shared overview footprint on the JSON route. | Monaco editor appears high in the first viewport. | medium |
| JSON-002 | Add validation panel | Show validation issues in a panel with path/line-oriented navigation where possible. | Users can move from validation error to relevant JSON location. | high |
| JSON-003 | Add known-key handoff to All settings | For known keys, provide a way to open the matching All settings detail. | JSON users can switch to visual editing for supported keys. | high |
| JSON-004 | Clarify action hierarchy | Keep `Format`, `Validate`, `Save`, and `Download policies.json` prominent and predictable. | JSON route feels like an expert editing tool, not another wizard. | medium |
| JSON-005 | JSON route regression tests | Cover formatting, validation, saving, export link state, and All settings handoff. | Existing JSON editing remains stable. | medium |

## Milestone 6: Regression And Workflow Quality

Goal: protect the redesigned workflows across desktop, mobile, and both supported locales.

| ID | Task | Scope | Acceptance | Reasoning |
|---|---|---|---|---|
| QA-001 | Update local Chromium UI audit | Update browser audit flows for Library, six-step Guided editor, All settings, JSON editor, and Russian UI. | Audit covers the new product model and catches layout overflow. | high |
| QA-002 | Add viewport screenshot pack | Capture desktop and mobile screenshots for all primary modes. | Visual regressions are easier to inspect after each milestone. | medium |
| QA-003 | Keyboard navigation pass | Verify filters, tables/cards, wizard steps, setting list/detail panel, Monaco, and dialogs. | Common workflows are keyboard-usable. | high |
| QA-004 | Save/dirty/conflict regression | Verify dirty state, explicit save, validation blocking, conflict reload, copy, and overwrite flows. | Multiple-tab work does not silently lose changes. | high |
| QA-005 | End-to-end workflow regression | Cover import -> edit -> validate -> export, duplicate -> adjust -> compare, archive -> restore. | Core admin workflows work end to end. | high |
| QA-006 | Locale regression pass | Verify both `en` and `ru` across all primary routes. | No missing locale keys or accidental English in Russian UI. | medium |
| QA-007 | No-doc-tail regression | Add a focused check for documentation placeholders and unavailable doc-link copy. | Future documentation placeholders cannot reappear accidentally. | low |

## Recommended Implementation Order

1. `UI-001` through `UI-008`
2. `LOC-001` through `LOC-006`
3. `LIB-001` through `LIB-012`
4. `GID-001` through `GID-010`
5. `ALL-001` through `ALL-011`
6. `JSON-001` through `JSON-005`
7. `QA-001` through `QA-007`

The order intentionally removes stale UI and fixes terminology before deeper workflow changes.
