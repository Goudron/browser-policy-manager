# BPM 0.9.2 UI Density Budget Contract

Date: 2026-07-17
Status: active contract
Backlog item: `BPM092-M2-03`
Baseline: [Rendered UI copy inventory](ui-copy-inventory-0.9.2.md)
Classification: [UI copy classification contract](ui-copy-classification-contract-0.9.2.md)

## Decision

The earlier approximate fivefold/20% figure is a diagnostic reference only, not an acceptable
residual quota. The release target is stricter: remove every node classified `remove-explanation`,
and reduce every `deduplicate` fact to one authoritative presentation. Documentation already
exists; a routine explanation does not remain in the UI merely because a new documentation topic
has not been written.

Word count, prose-node count, persistent-chrome height, and first-work-area position are recorded
as evidence of the result. They do not set a threshold below which leftover explanatory text is
permitted.

## Common Budget Rules

| Metric | Budget at release |
| --- | --- |
| `remove-explanation` nodes and words | `0` on every rendered surface and representative state. |
| Redundant presentation of a `deduplicate` fact | `0`; exactly one authoritative rendering remains. |
| Unresolved `documentation-candidate` disposition | `0`; M2-04 records no replacement, an existing localized target, or a new approved localized target. |
| Persistent helper paragraphs/secondary lines whose adjacent label/value/action is sufficient | `0`. |
| Essential or safety-accessibility text | Excluded from density arithmetic; it remains present wherever its meaning is required. |

An exception is not a preference for longer copy. It is permitted only for a named essential or
safety-accessibility item below, with the protected meaning and reason recorded. If concise labels,
state, or documentation make an item clear, it is removed.

## Per-Surface Budgets

| Surface | Release budget | Protected exception and reason | Required compact work area |
| --- | --- | --- | --- |
| Shared product header | No subtitle, locale/theme helper line, or duplicated product-context prose. Header contains product identity/version, documentation action, named locale/theme controls, and necessary workspace count/state only. | Locale/theme control names, selected values, focus order, touch targets, and accessible names remain; they describe the operable control rather than explain it. | The first route-specific control/heading begins immediately after one compact header row; no explanatory sub-row consumes height. |
| Library | No Library workflow narration, routine clone checklist, or duplicate filter/action heading. | Import profile-creation consequence, errors, archive/export recovery, active filters, and lifecycle/validation state remain because they change an available action or result. | Profile rows and primary actions are the first substantive area after compact filters/search. |
| Compare | No comparison eyebrow or selection tutorial. | Empty, missing-profile, no-result, and no-setting states remain concise and actionable; difference/state/kind labels remain. | Both selectors and the comparison table begin without an introductory prose block. |
| Shared editor chrome | No mode-description paragraphs, repeated ID/schema/state summaries, or lifecycle/compliance summary duplication. | The unavailable-mode reason remains associated with disabled links; profile name, schema, dirty/saved/archived/validation state, and required identifier remain once. | A single compact context/action bar precedes the editor; it contains no persistent explanatory card. |
| Guided editor | No wizard route narration, step descriptions, generic card explanations, fine-tuning instructions, map/handoff walkthroughs, or generic hints. | A short differentiator remains only where options would otherwise be ambiguous; input format/error, raw/unknown/schema coverage, validation, consequence, and recovery text remain. | Current step controls and choices dominate the viewport; no generic prose card precedes them. |
| All settings | No route-purpose, mode, search, review, inventory, category, or technical-workflow explanation. | Source, current value, schema support, raw/unknown/deprecated/invalid state, review reason, filter/count state, row help disposition, and accessible labels remain. | Search, modes/filters, and actual inventory/details begin without explanatory panels. |
| JSON editor | No route-purpose or document-view explanation. | Format/validate/save/download actions, dirty status, exact parse/schema errors, and recovery instructions remain live and accessible. | The document editor begins directly below the compact editor context/actions. |
| Documentation shell | No independently visible documentation version, progress/runtime-pending narration, or header helper prose that the BPM header does not have. | Product identity/version, locale/theme/search/navigation labels, active-filter summary, search recovery, keyboard/accessibility text, and article semantics remain. | Documentation content/search/tree begins after the same compact header structure as the product. |
| Documentation articles | No maintainer address, roadmap, or implementation-progress narration. | User/admin/DevOps/API prerequisites, warnings, commands, results, current support boundaries, and technical semantics remain. | Article content may use explanatory prose because it is the documentation destination, not persistent product UI chrome. |

## Measurement And Evidence

For every representative state from the baseline inventory, M3-M9 records:

1. source keys/nodes removed and source keys/nodes retained;
2. before/after English explanatory words and prose-node counts, excluding protected text;
3. persistent header/editor-chrome height and the vertical start of the first substantive work area
   at desktop and narrow viewports;
4. the sole authoritative owner for each former duplicate;
5. each protected exception, its classification, and why an adjacent label/value/action cannot
   carry the meaning; and
6. the documentation disposition for every `documentation-candidate`.

The measurement passes only when all Common Budget Rules are met. A favorable percentage cannot
compensate for one remaining removable helper line, duplicate fact, or unresolved candidate.

## Explicit Non-Exceptions

The following are not reasons to retain a classified explanatory block: a previous fivefold target,
available vertical space, concern that a user might want a tutorial, a historical UI convention,
translation effort, or the absence of a newly authored documentation page. Existing documentation,
clear labels, current values, contextual help where genuinely needed, and normal application
affordances are the default support path.
