# BPM 0.9.2 Rendered UI Copy Baseline Inventory

Date: 2026-07-17
Status: baseline inventory
Backlog item: `BPM092-M2-01`

## Scope And Method

This pre-compaction inventory covers Library, Guided editor, All settings, JSON editor, Compare,
the shared product header/editor chrome, and the documentation portal. It uses English source
because English owns the source keys; every listed `profiles.*` key has six locale peers.

`Words` is the whitespace-delimited English source value, with a placeholder such as `{name}`
counted as one word. `Footprint` records an occupied rendered region rather than a fabricated
pixel claim: `P` is persistent route chrome, `A` is initially visible work-area content, `D` is
conditional/dynamic content, and `S` is an accessible status or safety region. `1r`, `2r`, and
`3r+` are expected text rows at the desktop baseline; narrow layouts may wrap further. M2-03 will
add browser-derived pixel and first-work-area measurements from this baseline.

The complete candidate population is mechanically bounded to Jinja `data-i18n`/`tr` nodes,
JavaScript `t` nodes inserted into visible DOM, and English values matching `_body`, `_hint`,
`_copy`, `_subtitle`, `_context_`, or `_meta` in `app/i18n_src/en/*.json`. It contains **449 keys /
5,934 words**: `common.json` 58 / 676, `json.json` 1 / 16, `library.json` 3 / 54,
`settings.json` 35 / 406, and `wizard.json` 352 / 4,782. The inventory is a candidate census, not
a decision that all text is removable.

## Shared Persistent Chrome

| Surface/state | Node or source-key family | Words | Footprint | Source mapping |
| --- | --- | ---: | --- | --- |
| All product routes | Product subtitle: “Build and maintain … Release 153.” | 11 | `P`, 2r | `_page_header.html` → `profiles.subtitle` in `common.json` |
| All product routes | Locale explanatory line: “UI language”. | 2 | `P`, 1r | `_page_header.html` → `profiles.locale_hint` |
| All product routes | Theme explanatory line: “Appearance mode”. | 2 | `P`, 1r | `_page_header.html` → `profiles.theme_hint` |
| All product routes | Documentation action label. | 3 | `P`, 1r | `_page_header.html` → `profiles.documentation_link` |
| Editor routes, saved/draft | Repeated ID/schema/current-state labels and ID/schema metadata. | labels + variable | `P`, 2r | `_page_editor_chrome.html` → `editor_chrome_*`, `wizard_export_shareable_schema_label`, `current-meta` |
| Editor routes | Mode-switch heading and three descriptions. | 18 + 13 + 11 + 12 | `P`, 3r+ | `_page_editor_chrome.html` → `editor_chrome_modes_body`, `editor_chrome_guided_body`, `editor_chrome_settings_body`, `editor_chrome_json_body` |
| Editor, unsaved draft | Disabled-mode reason: “Save the profile first … separate tab.” | 14 | `S`, 2r | `_page_editor_chrome.html` → `profiles.editor_chrome_save_first` |
| Editor, lifecycle expanded | Lifecycle and compliance descriptions. | 15 + 6 | `D`, 2r | `_page_editor_chrome.html` → `lifecycle_review_body`, `compliance_summary_body` |
| Editor, name state | New-name or locked-name hint. | 9 / 7 | `S`, 1r | `_page_editor_chrome.html` → `name_hint`, `name_locked` |

## Library And Compare

| Surface/state | Node or source-key family | Words | Footprint | Source mapping |
| --- | --- | ---: | --- | --- |
| Library, populated/filtered | Workflow narration: “Open an existing profile … filters change.” | 16 | `P`, 2r | `_page_library_workspace.html` → `profiles.sidebar_hint` |
| Library, import ready | Import setup instruction. | 12 | `S`, 2r | `_page_library_workspace.html` → `profiles.import_firefox_policies_ready` in `library.json` |
| Library, populated | Ready status and filter/count labels. | 2 + labels | `S`, 1r | `_page_library_workspace.html` → `library_ready`, `library_filtered_short`, `library_total_short` |
| Library, archive/export | Archive/export recovery message. | 7 | `S`, 1r | `profiles_library.js` → `profiles.library_export_unavailable_archived` |
| Library, clone draft | Handoff title/body, active notice, and four checklist items. | 6 + 22 + 16 + 9 + 11 + 8 + 10 | `D`, 3r+ | `profiles_library.js`, wizard setup template → `profiles.clone_handoff_*` |
| Library, row | Note fallback and lifecycle/validation labels. | 2 + labels | `A`, 1r per row | library template and `profiles_library.js` → `library_description_empty`, `library_*` |
| Compare, initial | Route eyebrow and empty comparison instruction. | 2 + 10 | `A`, 2r | `_page_compare_workspace.html` → `compare_route_eyebrow`, `compare_table_empty` |
| Compare, no results | Search and no-profile state. | 2 + 4 | `S`, 1r | `profiles_compare.js` → `compare_search_empty`, `compare_profile_empty` |
| Compare, selected | Difference-state labels and no-settings message. | labels + 7 | `D`, 1r | `profiles_compare.js` → `compare_state_*`, `compare_table_no_settings` |

## Guided Editor

| Surface/state | Node or source-key family | Words | Footprint | Source mapping |
| --- | --- | ---: | --- | --- |
| Guided, initial header | Wizard title, route narration, and new/existing/cloned context sentence. | 9 + 24 + 16/15/18 | `P`, 3r+ | `_page_wizard.html` → `wizard_title`, `wizard_body`, `wizard_context_new`, `wizard_context_existing`, `wizard_context_cloned` |
| Guided, stepper | Six step descriptions. | 9 + 9 + 8 + 8 + 8 + 12 | `P`, 1r per step | `_page_wizard.html` → `wizard_step_*_copy` |
| Guided, each step | Scenario, baseline, security, privacy, general, home, search, sync, AI, extensions, site, and export-card explanations. | 352 keys / 4,782 | `A`/`D`, 1r–3r+ each | `_page_wizard_step_*.html`, `_wizard_macros.html`, `profiles_wizard_flow.js`, `profiles_extensions.js`, `profiles_search_engines.js`, `profiles_schema_shell_sections.js` → `wizard.json` |
| Guided, technical disclosure | Coverage, map/handoff, raw-fallback, and nested-input explanations. | included above | `D`/`S`, 1r–3r+ | wizard support/macros and schema-shell JS → `wizard_shell_*`, `wizard_settings_covered_*`, `wizard_preferences_*` |
| Guided, review/export | Dynamic drilldown/recovery copy and confirmation states. | included above | `D`/`S`, 1r–3r+ | `profiles_review.js`, wizard export template → `wizard_*_body` and status keys |

The 352-key Guided family is intentionally retained as one mechanically complete group, rather
than a misleading hand-curated sample: every matching key is an inventory member, its word count
is the source value count, and its rendered node is found through the named files. M2-02 assigns a
disposition to each member before removal.

## All Settings And JSON Editor

| Surface/state | Node or source-key family | Words | Footprint | Source mapping |
| --- | --- | ---: | --- | --- |
| All settings, initial | Route-purpose paragraph. | 11 | `P`, 2r | `_page_settings_workspace.html` → `settings_route_body` |
| All settings, mode bar | Review, Configured, and Catalog descriptions. | 6 + 5 + 4 | `P`, 1r each | `_page_settings_workspace.html` → `settings_mode_*_body` |
| All settings, search | Search hint. | 11 | `P`, 2r | `_page_settings_workspace.html` → `settings_search_hint` |
| All settings, review | Technical-review explanation. | 9 | `A`, 2r | `_page_settings_workspace.html` → `settings_review_body` |
| All settings, inventory | List explanation. | 12 | `A`, 2r | `_page_settings_workspace.html` → `settings_list_body` |
| All settings, dynamic details | Review queue, source/domain/category/detail, preference, raw, and recovery explanations. | remaining 30 keys / 348 | `D`/`S`, 1r–3r+ | settings templates and `profiles_all_settings_*.js`, `profiles_settings_search.js` → `settings.json` |
| JSON, initial | Editor-purpose paragraph. | 16 | `P`, 2r | `_page_json_workspace.html` → `profiles.editor_section_hint` in `json.json` |
| JSON, active | Ready, parse/validation, and download/save feedback. | state-dependent | `S`, 1r–3r+ | JSON template and `profiles_json.js`, `profiles_runtime_json_editor.js` → status keys |

## Documentation Portal

| Surface/state | Node or source-key family | Words | Footprint | Source mapping |
| --- | --- | ---: | --- | --- |
| Home/topic | Brand kicker, portal title, and visible `BPM 0.9.1 · Documentation 0.9.1`. | 3 + variable + 4 | `P`, 2r–3r | `documentation/tools/build_docs.py` → `labels["version"]`, `bpm-docs-version` header node |
| Search, collapsed | Search/toggle/result/active-filter labels. | locale/state-dependent | `P`, 1r–2r | `build_docs.py` shell and `documentation/assets/theme/bpm-docs-search.js` |
| Search, expanded | Facets, active-filter descriptions, empty-result/recovery text. | locale/state-dependent | `D`/`S`, 1r–3r+ | `build_docs.py` labels/templates and search JS |
| Navigation | Breadcrumb, home, guide/section/topic labels and tree-node titles. | source/topic-dependent | `P`/`A`, 1r per node | `build_docs.py`, DITA maps/topics, generated `navigation.json` |
| Article | Title, short description, task/concept/reference prose, warnings, prerequisites, results, and captions. | source/topic-dependent | `A`/`S`, variable | `documentation/src/dita/<locale>/**` transformed by `build_docs.py` |
| Footer/status | Build/runtime status and footer/ownership labels. | locale/state-dependent | `P`/`S`, 1r–2r | `build_docs.py` labels and generated HTML |

Article prose is in scope as user-facing content but not density debt by default: the compaction
target applies to product UI explanations and documentation shell chrome, while DITA owns removed
workflow explanation. M10 separately audits maintainer-facing and implementation-progress prose.

## Protected Text And Follow-up

Validation, parse, import/export, conflict, archive/restore, permanent-delete, permission, and
recovery feedback; accessible names/descriptions; keyboard instructions; localized placeholders;
current values; technical policy state; and DITA prerequisites, warnings, results, commands, and
support boundaries are inventoried but not automatic compaction candidates.

Representative states are Library populated/filtered/import/clone/archive; Compare
empty/selected/no-result; each editor new/saved/dirty/invalid/archived where permitted; every
Guided step and technical disclosure; All settings review/configured/catalog/search/filter/detail;
JSON valid/invalid/dirty/export; and documentation home/topic with collapsed/expanded active
filters. M2-02 classifies every entry, M2-03 turns footprints into budgets, and M2-04 determines
whether a removable explanation needs no replacement, an existing target, or a new localized topic.
