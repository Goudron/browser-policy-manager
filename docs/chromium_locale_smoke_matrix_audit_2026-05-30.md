# Chromium Locale Smoke Matrix Audit

Backlog item: `GLOC-601`

Scope: extend the Chromium browser smoke matrix for `de`, `zh-CN`, `fr`, and `es-ES` across the primary profile UI routes:
Library, Guided editor, All settings, and JSON editor.

Implemented browser flow:

- Creates one profile through the API against the temporary browser-test server.
- Opens the Library route, switches the runtime locale through the real locale picker, and verifies localized Library copy.
- Reuses the same browser session and persisted locale choice to open Guided editor, All settings, and JSON editor.
- Verifies route-specific localized text from the matching catalog and checks `document.documentElement.lang` for each target locale.

Coverage:

| Locale | Library | Guided editor | All settings | JSON editor |
|---|---|---|---|---|
| `de` | covered | covered | covered | covered |
| `zh-CN` | covered | covered | covered | covered |
| `fr` | covered | covered | covered | covered |
| `es-ES` | covered | covered | covered | covered |

Verification:

- Browser test: `tests/test_ui_browser_tabs.py::test_locale_smoke_matrix_browser_regression_loads_new_locales_across_primary_routes`
- Contract test: `tests/test_chromium_locale_smoke_matrix_contract.py`
