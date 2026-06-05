# Locale Viewport Overflow Assertions Audit

Backlog item: `GLOC-602`

Scope: add viewport overflow assertions for every target UI locale and the primary profile routes.

Implemented browser flow:

- Locales covered: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`.
- Routes covered: Library, Guided editor, All settings, JSON editor.
- The test creates one profile against the temporary browser-test server, switches each locale through the real picker, then opens each primary route in that locale.
- Each route waits for route-specific localized text and verifies `document.documentElement.lang`.
- Each route asserts that the maximum document/body/scrolling-element width does not exceed `window.innerWidth` by more than one pixel.

Verification:

- Browser test: `tests/test_ui_browser_tabs.py::test_locale_viewport_overflow_browser_regression_fits_all_locales_and_primary_routes`
- Contract test: `tests/test_locale_viewport_overflow_contract.py`
