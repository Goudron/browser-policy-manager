# All Settings Search And Filter I18n Audit

Backlog item: `GLOC-404`
Date: 2026-05-30

## Scope

- All settings search result labels and kind/state badges.
- Filter chips and technical review cards.
- Setting detail action labels, metadata labels, schema badges, and inline schema editor labels.

## Findings

- Search, filter chips, review cards, and setting detail actions were already routed through
  locale keys.
- Schema shell policy cards still depended on English fallback labels for policy names,
  subsections, tags, and several schema shell metadata paths.
- Those schema shell labels are visible inside All settings detail/editor panels, so they now have
  explicit catalog entries in all six active catalogs.

## Changes

- Added missing `profiles.shell_policy_*`, `profiles.wizard_shell_subsection_*`, and
  `profiles.wizard_shell_tag_*` keys to `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.
- Removed English fallback arguments from the schema shell label paths used by All settings cards.
- Added `tests/test_all_settings_search_filter_i18n.py` to derive required labels from the runtime
  schema shell catalog and fail when new visible shell labels are not catalog-backed.

## Result

All settings search, filter chips, review cards, schema badges, and setting detail panels are now
covered by locale-backed strings for all active catalogs.
