# BPM 0.9.2 Compact UI User Documentation Review

Date: 2026-07-19
Status: active update record
Backlog item: `BPM092-M11-01`

## Updated user guidance

All six active DITA locales now describe the compact product interface through these topics:

| User-visible change | Updated source topic |
| --- | --- |
| One BPM header, one visible BPM version, Firefox ESR/Release support, and concise Library count | `ug-reference-product-version` |
| Library action grid before filters, with filters directly above the table | `ug-task-use-profile-library` |
| Compact shared profile context and switching between Guided, All settings, and JSON | `ug-task-switch-editor-mode` |
| Choosing Library, Guided editor, All settings, JSON editor, or Compare with shared header state | `ug-concept-choose-editor-surface` |

The existing dedicated task topics for Guided editor, All settings, JSON editor, Compare, locale,
theme, and validation retain their workflow, safety, and recovery instructions. They do not repeat
the retired persistent explanatory panels; the compact header/context facts above are shared rather
than copied into every workflow.

## Screenshot refresh boundary

The following screenshots were recaptured for the compact 0.9.2 UI by `BPM092-M11-03`:

| Screenshot key | Reason | State |
| --- | --- | --- |
| `screenshot.library-overview` | Action/filter/table order and compact profile count changed. | recaptured M11-03 |
| `screenshot.guided-editor-overview` | Shared editor context and Guided content spacing changed. | recaptured M11-03 |
| `screenshot.all-settings-review` | Shared editor context changed. | recaptured M11-03 |
| `screenshot.json-editor` | Shared editor context changed. | recaptured M11-03 |
| `screenshot.compare-profiles` | Shared header changed. | recaptured M11-03 |

This is a documentation evidence boundary, not a product limitation. The maintained task text above
is the current source of workflow guidance. The captured assets are recorded in the M11-03 evidence
record; final locale/editorial acceptance remains governed by the release gate.
