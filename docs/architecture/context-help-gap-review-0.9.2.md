# BPM 0.9.2 Context-Help Gap Review

Date: 2026-07-19
Status: no new gap confirmed
Backlog item: `BPM092-M11-02`
Input: [UI Copy Documentation Disposition Map](ui-copy-documentation-disposition-map-0.9.2.md)

## Decision

No new contextual-help topic or circled-info link is approved for BPM 0.9.2.

The M2 map requires no replacement for compact header labels, locale/theme selectors, editor-mode
labels, passive lifecycle state, generic filters, or routine Guided/All settings/JSON narration.
Where the map identifies a genuine comprehension boundary, the installed documentation already has
a stable, localized target.

| UI boundary | Existing target owner |
| --- | --- |
| Library, Compare, Guided editor, All settings, JSON editor | `DOCUMENTATION_CONTEXTUAL_HELP_TARGET_IDS` |
| Profile validation, import, export, CIS baseline selection, AI controls, visual search | `DOCUMENTATION_DEEP_HELP_TARGET_IDS` |
| All settings policy and known-preference rows | Generated manifest target map with the existing row-help disposition contract |

The five surface links and six deep links resolve their URL from target IDs and locale. The visible
link text and accessible names remain localized; the UI does not construct a URL from a translated
label.

## Reopening rule

A later change may add a circled-info link only when it records the exact source control, observed
ambiguity after compaction, six-locale target coverage, a manifest-valid stable target ID, localized
accessible name, keyboard behavior, and the reason existing inline state/error/recovery text is not
being replaced. Routine explanatory copy, passive state, and every filter or mode selector are not
such evidence.
