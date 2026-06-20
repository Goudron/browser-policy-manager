# All Settings Current Contracts

Date: 2026-06-12

Backlog item: `BPM088-M2-02`

This note captures the current All settings route contracts before the BPM
0.8.8 Review / Configured / Catalog refactor. It is a working map for
implementation tasks, not a target-state design.

## Route Boundary

All settings is rendered by `GET /profiles/{profile_id}/settings` with
`profiles_template_kind == "settings"`. The route shell is
`app/templates/profiles/_settings_shell.html`, which includes:

- shared page header and editor chrome;
- `app/templates/profiles/_page_settings_workspace.html` as the route body;
- shared command deck and footer;
- catalog JSON payloads from `app/templates/profiles/_page_catalog_scripts.html`;
- settings preference support markup from
  `app/templates/profiles/_page_settings_preference_support.html`.

The route uses the editor/static runtime chain rather than the Library or
Compare entrypoints.

## Route-Specific DOM

The current route has these main DOM anchors:

| Area | DOM contract |
| --- | --- |
| Route header | `#settings-panel` owns the All settings title and search shell. |
| Search | `#wizard-settings-search-input`, `#wizard-settings-search-clear`, `#wizard-settings-search-meta`, and `#wizard-settings-search-results`. |
| Technical review | `#all-settings-review-panel`, `#all-settings-review-summary`, and `#all-settings-review-actions`. |
| Inventory list | `#all-settings-list-panel`, `#all-settings-list-summary`, `#all-settings-list`, and `#all-settings-list-empty`. |
| Filters | `[data-settings-list-filter]` buttons with `[data-settings-list-filter-count]` counters. |
| Detail | `#all-settings-detail-panel` and `#all-settings-add-preference`. |
| Category map | `[data-settings-category-link]` links to `#settings-category-{id}` sections. |
| Category sections | `[data-settings-category-id]` sections render mapped controls, schema-shell blocks, and preference sections. |
| Mapped-control navigation | `[data-settings-nav]`, `[data-settings-filter]`, `[data-settings-area-id]`, and `[data-settings-jump-target]`. |
| Schema-shell blocks | `#settings-schema-shell-step-{step}` and the `-coverage`, `-badges`, `-recommended`, `-additional`, `-preferences`, and `-raw` child lists. |
| Preference sections | `#settings-preferences-{id}`, `#wizard-preferences-{id}-add`, `-count`, `-presets`, `-bundles`, `-known`, `-empty`, and `-list`. |

Search and detail navigation also depend on `data-settings-target` values from
schema-shell controls, guided controls reused on the settings route, and
preference sections. All settings list rows render dynamic
`data-settings-entry-*` attributes for id, kind, category, state, guided
coverage, invalid/deprecated/raw/unknown attention flags, and selected state.

## Catalog Payloads

The route embeds the following catalog payloads before frontend startup:

- `wizard-starter-catalog`;
- `wizard-settings-catalog`;
- `wizard-preferences-catalog`;
- `wizard-manual-policy-controls`;
- `wizard-schema-shell-catalog`;
- `all-settings-category-catalog`;
- `schema-channels-catalog`.

`all-settings-category-catalog` maps categories to settings sections,
preference sections, and schema-shell steps. The All settings list and category
sections both depend on this catalog today.

## Frontend Modules

| Module | Current ownership |
| --- | --- |
| `profiles_all_settings_state.js` | Route-state model for active category, active filter, search query, selected entry key, focused target, expanded groups, entries, visible entries, and counts. |
| `profiles_all_settings_list.js` | Collects current policy/preference entries, renders technical review cards, renders the full inventory table, applies list filters, and selects entries. |
| `profiles_all_settings_detail.js` | Renders the selected entry detail, policy raw editor, preference editor, reset/remove/apply actions, and add-preference flow. |
| `profiles_settings_search.js` | Builds the settings search index, merges All settings inventory entries with mapped controls and schema-shell targets, renders result buttons, resolves targets, and highlights/focuses them. |
| `profiles_schema_shell.js` plus `profiles_schema_shell_*` | Renders schema-backed editor cards and review state reused by All settings detail and category sections. |
| `profiles_preferences*.js` | Owns managed-preference rows, presets, bundles, known preferences, and manual preference sections rendered in category bodies. |
| `profiles_bootstrap_core.js` | Wires schema shell, All settings state/list/detail/search, workspace updates, validation issues, and document-change rerenders. |

The current implementation still duplicates inventory knowledge between list
collection and search indexing. `profiles_all_settings_list.js` owns entry
collection today; search consumes `allSettingsList.getSearchEntries()` and then
adds mapped controls, preference sections, search-engine presets, and
schema-shell policy blueprints.

## Render And Data Flow

Startup wiring in `profiles_bootstrap_core.js` currently follows this order:

1. Create `schemaShell`.
2. Create `allSettingsDetail`.
3. Create `allSettingsRouteState`.
4. Create `allSettingsList`, passing `allSettingsRouteState` and
   `onSelectionChange: (entry) => allSettingsDetail.render(entry)`.
5. Create `settingsSearch`, passing the same `allSettingsRouteState`,
   `getAllSettingsSearchEntries: () => allSettingsList.getSearchEntries()`,
   and `findAllSettingsEntryTarget: (target) => allSettingsList.findTarget(target)`.

All settings entry collection reads the current document through
`readWizardSchemaSource()`, schema channel through
`getActiveWizardSchemaVersion()`, and validation issues through
`getValidationIssues()`. Entry construction uses:

- `wizardSchemaShellCatalog` for policy definitions and schema-shell buckets;
- `wizardPreferencesCatalog` for known managed preferences and preference
  section matching;
- `allSettingsCategoryCatalog` for policy/preference category labels and
  ordering;
- the current profile document's `Preferences` object for configured managed
  preferences and unknown preference entries;
- top-level unknown policy keys for imported or unmapped policy entries.

When the detail panel changes the document, `handleAllSettingsDocumentChange`
rerenders schema shell, All settings list, search index/results, and workspace
action state:

```text
schemaShell.renderWizardSchemaShell()
allSettingsList.render()
settingsSearch.buildIndex()
settingsSearch.renderResults()
workspace.updateActionState()
```

## Current Filters And Review Groups

The inventory list currently supports these list filters:

- `all`;
- `configured`;
- `available`;
- `guided-covered`;
- `all-settings-only`;
- `invalid`;
- `deprecated`;
- `raw`;
- `unknown`.

Technical review currently groups entries by:

- unknown configured entries;
- deprecated configured entries;
- raw fallback configured entries;
- invalid entries.

These are not yet the target Review mode. They are the existing technical
review cards that BPM 0.8.8 will convert into a first-class review workflow.

## Refactor Watchpoints

- Preserve `focus` and search-result handoff for `all-settings-entry:{kind}:{id}`
  and `data-settings-target` values.
- Do not remove schema-shell or preference-section reachability while moving
  long category bodies behind Review / Configured / Catalog navigation.
- Keep `readWizardSchemaSource()` as the source of current profile data until a
  shared inventory module replaces list-owned collection.
- Keep validation issue mapping independent from a specific renderer.
- Keep detail apply/remove/reset flows responsible for triggering the shared
  document-change rerender path.
