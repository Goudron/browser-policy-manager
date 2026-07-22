# BPM 0.9.2 UI Copy Documentation Disposition Map

Date: 2026-07-17
Status: active map
Backlog item: `BPM092-M2-04`
Inputs: [UI copy inventory](ui-copy-inventory-0.9.2.md),
[classification contract](ui-copy-classification-contract-0.9.2.md), and
[density budget](ui-density-budget-contract-0.9.2.md)

## Rule

This map disposes of every `remove-explanation`, `deduplicate`, and
`documentation-candidate` family in the classification contract. The default is **no replacement**:
clear labels, selected values, named actions, and normal application affordances are sufficient.
Existing documentation is used only for a confirmed remaining comprehension gap. No new topic is
required by the current map.

An inline error, validation result, destructive consequence, unavailable reason, recovery action,
current state, accessible name, keyboard instruction, or domain distinction is not mapped here for
removal. It remains inline under the `essential` or `safety-accessibility` classification.

All listed existing targets resolve through the generated manifest and UI target map for `en`, `ru`,
`de`, `zh-CN`, `fr`, and `es-ES`. UI code resolves URLs from target IDs and locale; it must not
construct links from translated labels.

## Product UI Map

| Removed/deduplicated family | Disposition | Existing target or new topic | UI action and threshold |
| --- | --- | --- | --- |
| `profiles.subtitle`, `profiles.locale_hint`, `profiles.theme_hint` | No replacement. | None. | Remove; product identity, control labels, and selected values explain the header. Do not add a help icon for locale/theme. |
| Editor duplicate ID/schema/current-state presentation and `current-meta` | No replacement; retain one compact authority. | None. | M5 removes duplicates after choosing the compact context-bar owner. |
| `profiles.editor_chrome_modes_body`, `profiles.editor_chrome_guided_body`, `profiles.editor_chrome_settings_body`, `profiles.editor_chrome_json_body` | No replacement. | Existing route topics: `topic:ug-task-use-guided-editor`, `topic:ug-task-use-all-settings`, `topic:ug-task-use-json-editor`. | Remove bodies; concise mode labels/current state are sufficient. Add no persistent per-mode icon. Reuse existing surface help only if a tested ambiguity remains. |
| `profiles.lifecycle_review_body`, `profiles.compliance_summary_body`, repeated lifecycle summaries | No replacement; retain one state owner. | Existing lifecycle topics only when invoked by an affected action: `topic:ug-task-archive-profile`, `topic:ug-task-restore-profile`, `topic:ug-reference-archived-profile-behavior`. | M5 removes summary duplication. Do not link a passive status merely because it has background documentation. |
| `profiles.sidebar_hint` | Existing topic sufficient. | `topic:ug-task-use-profile-library`. | Remove narration; preserve the existing Library surface help link. No new target. |
| Routine `profiles.clone_handoff_*` checklist and walkthrough text | Existing topic sufficient. | `topic:ug-task-duplicate-profile`; destructive/retirement context: `topic:ug-task-manage-destructive-actions`. | M4 removes the persistent checklist. A sparse clone-state link is allowed only if tests show name/origin ambiguity after compacting; conflict and separate-profile outcome remain inline. |
| `profiles.compare_route_eyebrow` | Existing topic sufficient but no new link. | `topic:ug-task-compare-profiles`. | Remove eyebrow; preserve existing Compare surface help. Empty selection/result state remains inline. |
| `profiles.wizard_body`, `profiles.wizard_step_*_copy`, generic `profiles.wizard_*_body`, `profiles.wizard_*_hint`, and `profiles.wizard_*_copy` | No replacement by default. | Existing Guided overview: `topic:ug-task-use-guided-editor`. | M6 removes generic narration and instruction. A topic link is not a substitute for a missing label, selected state, validation, or a required choice differentiator. |
| Guided scenario/baseline prose where a genuine post-compaction choice ambiguity remains | Existing topic sufficient. | `topic:ug-task-choose-guided-scenario`. | Retain the shortest essential differentiator first; add a circled-i only if labels and selected state still cannot distinguish the choices. |
| Guided fine-tuning/map/handoff and routine “open All settings” prose | Existing topics sufficient. | `topic:ug-task-use-guided-fine-tuning`, `topic:ug-task-use-all-settings`, `topic:ug-task-edit-raw-policies-json`. | Remove walkthrough prose. A context link may appear at a sparse group boundary only when the mapped lower-level surface is genuinely ambiguous. |
| Guided schema-channel background prose | Existing topic sufficient. | `topic:ug-task-choose-firefox-schema`. | Prefer schema label/value. Use a circled-i only for non-obvious channel compatibility, not on every schema selector. |
| Guided CIS and AI explanatory bodies that survive only as a comprehension gap | Existing exact targets sufficient. | `cis:1.1.1.1`, `policy:AIControls`, `policy:VisualSearchEnabled`. | Keep the existing exact control-level icon pattern; remove generic surrounding paragraphs. No new broad topic. |
| `profiles.settings_route_body`, `profiles.settings_mode_*_body`, `profiles.settings_search_hint`, `profiles.settings_review_body`, `profiles.settings_list_body` | Existing topic sufficient. | `topic:ug-task-use-all-settings`. | M7 removes all routine route/mode/search/review narration; preserve existing All settings surface help. |
| All Settings generic queue/category/domain/preference/detail walkthroughs | Existing topics sufficient. | `topic:ug-task-use-all-settings`, policy/known-preference targets emitted by the current target map. | Use per-setting circled-i only for the existing policy/preference disposition; do not add icons to every category, filter, or state badge. |
| `profiles.editor_section_hint` | Existing topic sufficient. | `topic:ug-task-use-json-editor`. | M8 removes the route-purpose paragraph; preserve existing JSON surface help. |
| JSON raw/unknown/schema background explanation after compacting | Existing topics sufficient. | `topic:ug-task-edit-raw-policies-json`, `topic:ug-task-validate-json-document`. | Add a sparse group/action icon only for a proven ambiguity. Parse/schema error and recovery remain inline. |

## Documentation Shell And Editorial Map

| Removed family | Disposition | Existing target or new topic | UI/editorial action |
| --- | --- | --- | --- |
| Visible independent documentation version and its styling | No replacement. | None. | M9 removes it; the unified BPM header remains the product identity/version authority. |
| Runtime-package-pending/progress narration in portal chrome | No replacement. | None. | M9/M10 remove it from visible user-facing documentation rather than linking to maintainer status. |
| Maintainer address, roadmap, and implementation-progress DITA narration | No replacement. | None. | M10 removes it. Honest user/admin/DevOps/API support boundaries remain in the relevant topic. |
| Background DITA explanation that does not carry prerequisite, warning, command, result, state, or support-boundary meaning | Existing topic/section sufficient unless M10 finds a real coverage gap. | The containing localized DITA topic. | M10 rewrites or removes it using the audience/editorial contract; a new topic requires a documented gap and six locale peers. |

## Context-Link Contract

1. Retain existing surface links for `library`, `compare`, `guided`, `settings`, and `json`, and
   existing deep links for validation, import, export, CIS baseline, AI controls, and visual search.
   They already resolve through `DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS` and
   `DOCUMENTATION_DEEP_HELP_TARGET_IDS`.
2. New circled-i links require all of: a recorded exact source key, a demonstrated ambiguity after
   compacting, an existing or approved new six-locale target, a manifest-valid target ID, localized
   accessible name, keyboard reachability, and no replacement of essential inline feedback.
3. No new topic is requested in this map. If implementation exposes a gap, M11-02 owns authoring
   the topic and locale peers; M11-03 owns manifest/search regeneration.
4. The map is complete only when M4-M9 implementation evidence records one of these dispositions
   for every removed source family. A generic “see documentation” link does not close an item.

## M11-02 Gap Review

The post-compaction review in
[Context-Help Gap Review](context-help-gap-review-0.9.2.md) confirmed no new gap. Existing
surface/deep links and the All Settings row-help contract cover every M2-approved comprehension
boundary; no new topic or circled-info control is authorized.
