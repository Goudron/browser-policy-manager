# BPM 0.9.2: Documentation Navigation, Search, And Theme Stability

Date: 2026-07-19
Status: implemented
Backlog item: `BPM092-M10-10`

## Stability rules

- Editorial changes alter only localized visible text. DITA topic IDs, map
  keyrefs, output paths, anchors, manifest topic identities, and contextual-help
  target IDs remain the canonical navigation identity.
- Publication regenerates each locale navigation source, search index, manifest,
  and UI target map. Search indexes derive their title field from the localized
  DITA title, so revised labels remain searchable without a title-specific
  redirect or URL change.
- The documentation shell mirrors the main product palette. Its current-tree
  item uses the same translucent selected surface and border as the primary UI:
  teal in light mode and deep green in dark mode. The dark item keeps the
  product’s normal light text color; it never uses white text on a solid or
  light-green fill.

## Regression evidence

- `test_portal_current_navigation_uses_primary_ui_selected_surfaces` compares
  the selected-state values in the documentation theme with the primary UI
  foundation and editor styles.
- Documentation metadata, locale, navigation, search, target-map, and package
  validation run during `make docs-install-dev`.
- The installed-site fingerprint is checked after publication before handoff for
  `make dev`.
