# Browser Date/Time I18n Audit

Backlog item: `GLOC-405`
Date: 2026-05-30

## Scope

- Library profile timestamps.
- Editor chrome metadata.
- Lifecycle review timestamps.
- Revision-conflict local draft names that include a timestamp.

## Findings

- Library rows, editor metadata after runtime load, and lifecycle review already used
  `Intl.DateTimeFormat` with the active document locale and `dateStyle: "medium"` plus
  `timeStyle: "short"`.
- The server-rendered editor chrome still printed the raw `updated_at` value before runtime
  hydration.
- Revision-conflict copy names used a hand-built UTC timestamp slice.

## Changes

- Removed the server-rendered raw `updated_at` value from initial editor chrome metadata. Runtime
  `setMeta()` fills the localized timestamp through the existing browser formatter.
- Changed conflict-copy timestamp generation to use the same `formatTimestamp(new Date())` browser
  locale formatter.
- Added `tests/test_browser_datetime_i18n.py` to lock the date/time contract.

## Result

Date/time text shown in Library and editor metadata is localized through browser APIs. The remaining
technical timestamps stored in data payloads stay ISO strings and are not presented as localized UI
copy.
