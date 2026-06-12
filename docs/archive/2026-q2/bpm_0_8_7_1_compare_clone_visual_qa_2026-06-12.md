# BPM 0.8.7.1 Compare And Clone Visual QA

Date: 2026-06-12

Scope: local visual QA notes for the BPM 0.8.7.1 compare selector, comparison table, and Library
clone-name fixes. These notes correspond to `BPM0871-M7-01` through `BPM0871-M7-05`.

Generated screenshots are intentionally not committed. If screenshots or HTML dumps are captured for
local review, keep them under ignored paths such as `docs/screenshots/` or
`artifacts/local_chromium_ui_audit/`.

## Routes And Viewports

| Route | Locale | Viewport | Evidence |
| --- | --- | --- | --- |
| `/profiles` to `/profiles/compare` | `ru` | Chromium 1366 x 1200 | Library language selection carried into the new compare tab. |
| `/profiles/compare` | `en` | Chromium 1366 x 1200 | Large profile selector rendered a bounded scroll list, selected a scrolled option, and avoided page overflow. |
| `/profiles/compare?left={id}&right={id}` | `en` | Chromium 1366 x 1200 | Setting identity cells rendered without duplicated policy or preference identifiers. |
| `/profiles` | `ru` | Chromium 920 x 1100 | Clone-name panel actions stayed inside the panel with Russian button text. |

## Findings

- The compare route now participates in the product-wide locale preference path. Opening Compare from
  Library after selecting Russian renders Russian compare copy in the new tab.
- Compare profile search results are usable with at least 50 seeded profiles. The visible result set
  is bounded, scrollable, and selectable from the lower part of the result list.
- The comparison table no longer visually duplicates setting identity text. Policy rows show the
  policy identifier once; managed preferences keep the readable label and secondary key separate.
- The Library clone-name panel handles Russian action labels inside the panel bounds on a narrower
  desktop viewport. The panel, actions wrapper, and both action buttons avoid horizontal overflow.
- No generated screenshots were added to git for this pass.

## Browser Smoke Evidence

The following Selenium/Chromium checks were run locally with immediate sandbox escalation:

```bash
.venv/bin/pytest -q tests/test_ui_browser_tabs.py::test_browser_smoke_library_compare_preserves_locale_in_new_tab_and_selects_two_profiles -m browser_ui
.venv/bin/pytest -q tests/test_ui_browser_tabs.py::test_browser_smoke_compare_selector_scrolls_large_profile_lists_and_selects_profiles -m browser_ui
.venv/bin/pytest -q tests/test_ui_browser_tabs.py::test_browser_smoke_compare_table_setting_cells_do_not_duplicate_identifiers -m browser_ui
.venv/bin/pytest -q tests/test_ui_browser_tabs.py::test_browser_smoke_library_clone_name_actions_stay_inside_panel_in_russian -m browser_ui
```

All four checks passed in local Chromium.
