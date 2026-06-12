# Profile Clone Naming UX Decision

Date: 2026-06-06

This note defines the BPM 0.8.7 clone naming workflow before implementation.
The goal is to let users choose a clone name before working with the cloned
draft while preserving the existing route separation: Library actions open
editor flows in a new browser tab.

## Accepted UX

- Library duplicate starts from the profile row action. The action opens a
  focused clone-name dialog or inline control in the Library.
- The dialog shows the source profile name, the suggested clone name, and a
  single editable clone-name field.
- The default suggestion is based on the existing clone-name pattern:
  `{source name} copy`.
- The primary confirmation action opens the clone draft in a new tab through a
  real link with `target="_blank"` and `rel="noopener"`.
- The clone draft route is `/profiles/new?clone_from={id}&clone_name={encodedName}`.
  `include_deleted=true` is preserved when cloning an archived profile from a
  surface that intentionally exposes archived profiles.
- Cancel closes the dialog without changing the current Library filters,
  selection, scroll position, or profile data.
- Empty or whitespace-only clone names disable confirmation and show a localized
  validation message near the field.
- Duplicate-name conflicts are checked optimistically against the loaded Library
  data when possible. The save API remains authoritative and must still surface
  a localized duplicate-name error if another tab or user creates the same name.

## Editor Flow

- A clone draft opens in the Guided editor as a draft, not as a saved profile.
- The draft keeps the source flags, schema, description, and compliance data.
- The draft name is initialized from `clone_name` when the query parameter is
  present; otherwise it falls back to the default suggestion.
- The name remains editable before save.
- Saving the draft follows the normal create-profile path and duplicate-name
  validation.

## New-Tab Boundary

Library duplicate must not replace the Library tab. The confirmation control is
implemented as a user-activated link so browser popup blockers do not interfere.
The target editor/draft tab is isolated with `rel="noopener"`, matching existing
Library edit, settings, JSON, and compare navigation.

## Implementation Notes

- `BPM087-M5-02` adds the Library clone-name control.
- `BPM087-M5-03` passes the chosen clone name into the new-profile draft.
- `BPM087-M5-05` tightens duplicate-name conflict handling and copy.
- Owner metadata is intentionally excluded from this decision because BPM 0.8.7
  removes profile owners from the product.

## BPM0871-M6-01 Layout Audit

The BPM 0.8.7.1 clone-name overflow defect is in the Library row clone panel:

- container: `.library-clone-name-panel` rendered by `profiles_library_bootstrap.js`;
- control group: `.library-clone-name-controls`;
- actions: `.library-clone-name-confirm` and `.library-clone-name-cancel`;
- current grid: `minmax(160px, 1fr) minmax(120px, auto) minmax(96px, auto)` with `8px` gaps;
- current breakpoint: only at `max-width: 820px`, where the controls collapse to one column.

The overflow condition is any Library card/action column whose available inline size is smaller than
the three-column minimum plus gaps and panel padding, or any locale whose confirm/cancel labels need
more than the current action minimums. Russian labels make this visible: the right cancel action can
escape the panel before the page reaches the `820px` breakpoint.

The fix should keep the panel at `max-inline-size: 100%`, clip accidental horizontal overflow at the
panel boundary, and let the action group wrap or stack inside the panel. Confirmation and cancel
controls need `min-width: 0`, `max-width: 100%`, normal whitespace, and `overflow-wrap: anywhere` so
localized labels stay inside their buttons.
