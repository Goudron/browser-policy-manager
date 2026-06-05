# Runtime Count I18n Audit

Date: `2026-05-30`

Backlog item: `GLOC-402`

Scope: runtime-generated count text in Library, Guided editor, All settings, CIS summaries, and
export review.

## Decisions

- Library counter labels remain catalog-backed with `one`, `few`, and `many` keys for every active
  catalog. Russian keeps the existing `one/few/many` behavior; German, Simplified Chinese, French,
  and Spanish labels were corrected so the visible label is no longer mixed English prose.
- Guided editor search count text now uses `profiles.wizard_settings_search_match_count` instead
  of hardcoded English/Russian template literals in JavaScript.
- All settings search count strings now use neutral label-first wording in every non-Russian
  catalog. The existing `one` and `many` keys remain for compatibility, but both can safely render
  the same label-first shape.
- Export-review and guided-summary count fragments were normalized to label-first wording such as
  `DoH settings: {count}` instead of `{count} DoH settings`. This avoids English plural order
  assumptions when the runtime injects the number.
- CIS count summaries were already catalog-backed and label-first after the earlier CIS locale
  work; no runtime hardcoding was found there.

## Validation Contract

`tests/test_runtime_count_i18n.py` now locks the audited count strings to catalog-backed,
label-first shapes across all active catalogs and verifies that Guided editor search counts are no
longer hardcoded per language in `profiles_settings_search.js`.
