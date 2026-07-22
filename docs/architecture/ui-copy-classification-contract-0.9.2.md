# BPM 0.9.2 UI Copy Classification Contract

Date: 2026-07-17
Status: active contract
Backlog item: `BPM092-M2-02`
Baseline: [Rendered UI copy inventory](ui-copy-inventory-0.9.2.md)

## Rule

Every rendered node in the baseline inventory has exactly one primary disposition below. A node is
not removable because it is lengthy, duplicated in a locale catalog, or inconvenient to measure.
When a node has both a user-safety and explanatory aspect, its safety/recovery meaning wins; future
work may shorten it only if the required meaning, accessible name, and recovery path remain
available at the point of action.

| Disposition | Meaning |
| --- | --- |
| `essential` | Keep a label, value, action, current state, domain distinction, or navigation target. It may be restyled but remains visible or programmatically available. |
| `safety-accessibility` | Keep validation, error, consequence, recovery, unavailable reason, live update, accessible name/description, keyboard instruction, or filter/selection state. |
| `remove-explanation` | Remove routine workflow narration, repeated purpose prose, or a helper line whose meaning is already clear from adjacent labels, values, and actions. |
| `deduplicate` | Retain one authoritative presentation of the fact; remove the other visible repetition after the owner is defined. |
| `documentation-candidate` | Remove the routine inline explanation and map a genuine remaining comprehension gap to existing or new localized documentation in M2-04. It is not permission to move essential inline feedback into documentation. |

## Exhaustive Product UI Dispositions

| Inventory family or exact key group | Primary disposition | Required retained or replacement meaning |
| --- | --- | --- |
| `profiles.subtitle` | `remove-explanation` | Product identity remains in the product header; Firefox schema support remains where a current schema value or a relevant task needs it. |
| `profiles.locale_hint`, `profiles.theme_hint` | `remove-explanation` | Locale and theme labels, values, select names, focus order, and touch targets remain `essential`/`safety-accessibility`. |
| `profiles.documentation_link`, all visible route/editor labels, buttons, table headings, filter names, option names, count labels, current values, profile/schema names, and mode names | `essential` | Each action and state remains named; an icon alone is not accepted unless it has a localized accessible name. |
| Repeated profile ID/schema/current-state labels and `current-meta` in editor chrome | `deduplicate` | M5 keeps one authoritative compact profile-context presentation of name, schema, state, and required identifier. |
| `profiles.editor_chrome_modes_body`, `profiles.editor_chrome_guided_body`, `profiles.editor_chrome_settings_body`, `profiles.editor_chrome_json_body` | `remove-explanation` | Concise localized mode links/tabs and current-mode semantics remain `essential`; M2-04 evaluates only actual mode ambiguity. |
| `profiles.editor_chrome_save_first` and equivalent disabled mode reasons | `safety-accessibility` | Disabled state, the blocking condition, and the action that enables the mode remain visible or programmatically associated with the unavailable control. |
| `profiles.lifecycle_review_body`, `profiles.compliance_summary_body`, repeated lifecycle summaries | `deduplicate` | Current lifecycle/compliance facts remain once, live when changed, and available when relevant. |
| `profiles.name_hint`, `profiles.name_locked`, unique-name, conflict, and clone-name feedback | `safety-accessibility` | Users can distinguish editable, locked, invalid, and duplicate name states and recover without consulting documentation. |
| `profiles.sidebar_hint` | `remove-explanation` | Library heading, search/filter controls, profile rows, and new-draft action remain `essential`. |
| `profiles.import_firefox_policies_ready`, import progress/failure/success, and archive-export recovery messages | `safety-accessibility` | Import's profile-creation consequence, status, errors, and export precondition remain actionable. |
| `profiles.clone_handoff_title`, `profiles.clone_handoff_body`, `profiles.clone_handoff_item_*`, and other routine clone checklist narration | `documentation-candidate` | Clone origin, separate-profile result, name conflict, archive state, and destructive consequences remain inline where they affect the current action. |
| `profiles.library_description_empty`, row lifecycle/validation values, filter result counts, archive/restore state | `essential` | Row scanning must still expose note absence, current state, validation meaning, and filter effect. |
| `profiles.compare_route_eyebrow` | `remove-explanation` | Compare title, selectors, result values, and difference semantics remain `essential`. |
| `profiles.compare_table_empty`, `profiles.compare_search_empty`, `profiles.compare_profile_empty`, `profiles.compare_table_no_settings` | `safety-accessibility` | The missing selection/result condition and the next available action remain clear. |
| `profiles.compare_state_*`, profile/value/setting headers, kind labels | `essential` | Same/different/missing and policy/preference distinctions remain explicit. |
| `profiles.wizard_title`, step labels, control labels, selected values, preset names, current step, progress, and selected state | `essential` | Guided task order and choice differentiation remain clear without a paragraph. |
| `profiles.wizard_body`, `profiles.wizard_step_*_copy`, generic `profiles.wizard_*_body`, generic `profiles.wizard_*_hint`, and generic `profiles.wizard_*_copy` | `remove-explanation` | This exhaustive rule applies to the baseline's 352-key Guided family unless a more-specific row below protects it. |
| Scenario/preset/choice-card bodies that express a distinction unavailable from the label or selected value | `essential` | M6 retains the shortest differentiator necessary to avoid ambiguous choices; it must be recorded against its exact key. |
| `profiles.wizard_*_handoff_body`, `profiles.wizard_*_map_body`, `profiles.wizard_shell_*_body`, and routine “open All settings” explanations | `documentation-candidate` | Direct editor navigation, state, and action remain inline; M2-04 determines whether a circled-info link is actually needed. |
| `profiles.wizard_shell_*_coverage_*`, raw/unknown/deprecated/schema-support notices, and technical review reason text | `safety-accessibility` | Technical scope, missing coverage, raw fallback, and validation-sensitive state remain trustworthy and actionable. |
| `profiles.wizard_shell_true_map_hint`, `profiles.wizard_shell_json_hint`, JSON/number errors, field constraints, and dynamically rendered input errors | `safety-accessibility` | Valid input format, exact error, and recovery remain adjacent to the input and available to assistive technology. |
| Guided review/export confirmation, validation, destructive, import/export, conflict, save, and recovery messages | `safety-accessibility` | Do not replace with documentation, even where generic surrounding narration is removed. |
| `profiles.settings_route_body`, `profiles.settings_mode_*_body`, `profiles.settings_search_hint`, `profiles.settings_review_body`, `profiles.settings_list_body` | `remove-explanation` | Mode/filter names, count/state badges, search input, review reasons, and detail actions remain named and accessible. |
| Generic All Settings queue/category/domain/preference/detail walkthrough bodies | `documentation-candidate` | M7 keeps setting source, current value, schema support, validation, raw/unknown/deprecated state, and available actions inline. |
| All Settings `aria-label`, `aria-live`, a11y-count, source/state/kind/category, review, pagination, and help label keys | `safety-accessibility` | They remain localized in every catalog and programmatically connected to their controls/results. |
| `profiles.editor_section_hint` | `remove-explanation` | JSON label, editor, format/validate/save/download actions, and exact feedback remain `essential`/`safety-accessibility`. |
| JSON parse/schema error, dirty state, save/download/export result, and recovery text | `safety-accessibility` | The actual error and available recovery action remain inline and announced. |

The generic Guided and All Settings rules are exhaustive over the inventory's mechanically bounded
key families. A key protected by any later, more-specific rule is classified by that rule; all
other keys in the family take the generic disposition. This makes the 449-key census complete
without hiding individual decisions in an unreviewed hand-picked sample.

## Documentation Portal Dispositions

| Inventory family | Primary disposition | Required retained or replacement meaning |
| --- | --- | --- |
| Visible `BPM 0.9.1 · Documentation 0.9.1` and `.bpm-docs-version` presentation | `remove-explanation` | M9 shows one BPM product identity/version through the unified header; documentation never has a separately owned visible version. |
| Product brand, portal title, locale/theme controls, search/navigation labels, breadcrumb/tree node titles, buttons, filter names, selected values, result counts, and current filter summary | `essential` | Header parity and discoverability remain intact in all locales and themes. |
| Search empty/result/error/recovery messages, keyboard instructions, `aria-*` text, active hidden-filter state, and direct-link/history state | `safety-accessibility` | A collapsed panel must not conceal the existence or effect of active filters. |
| Runtime-package-pending/progress narration and maintainers-only implementation status in visible portal chrome or DITA | `remove-explanation` | M10 retains honest support boundaries but removes roadmap/progress narration from user/admin/DevOps documentation. |
| DITA title, short description, prerequisite, warning, task step, result, command, API semantic, and supported/unsupported boundary | `essential` or `safety-accessibility` as semantic type requires | Product documentation owns the explanation removed from UI; it must remain audience-appropriate and accurate. |
| DITA background explanation that is neither a prerequisite, warning, state, command, result, or support boundary | `documentation-candidate` | M10 reviews it for audience, editorial quality, and a natural locale-specific heading rather than deleting it automatically. |

## Enforcement Rules

1. M2-03 requires zero remaining `remove-explanation` nodes and one authoritative rendering for
   each `deduplicate` fact. Essential and safety-accessibility text is excluded from the density
   arithmetic.
2. M2-04 maps every `documentation-candidate` to no replacement, an existing localized topic, or
   a newly approved topic/help target. It may not convert an inline error, consequence, or recovery
   path into a link.
3. M3-M9 may remove a source key only after its exact inventory family and this disposition are
   cited in the implementation evidence. Retired keys and their six locale peers must be removed
   together after consumers move.
4. A mode, choice, icon, filter, or control that becomes ambiguous after copy removal requires a
   concise essential differentiator or an accessible contextual help target; it may not regain a
   generic paragraph by default.
5. Tests must fail for a removed localized accessible name, validation/recovery message, destructive
   consequence, unavailable reason, or meaningful state distinction. M2-08 owns the initial
   automated guard suite.
