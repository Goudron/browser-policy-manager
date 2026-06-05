# Locale Switching Regression Audit - 2026-05-31

Backlog item: `GLOC-604`

Scope: verify that runtime locale switching updates visible UI text for all six active locales
without stale text from the previous locale.

## Browser Regression

Added browser test:

- `tests/test_ui_browser_tabs.py::test_locale_switching_browser_regression_updates_visible_ui_without_stale_text`

Fixed runtime-localized status surfaces:

- Library `#status` now carries `data-i18n="profiles.library_ready"`.
- Guided editor, All settings, and JSON editor `#status` elements now carry
  `data-i18n="profiles.workspace_ready"`.

The flow creates a representative profile through the API, opens each primary route, and switches
the real locale picker through this sequence in a single Chromium session:

- `en`
- `ru`
- `de`
- `zh-CN`
- `fr`
- `es-ES`
- `en`

Routes covered:

- Library: `/profiles`
- Guided editor: `/profiles/{profile_id}/edit`
- All settings: `/profiles/{profile_id}/settings`
- JSON editor: `/profiles/{profile_id}/json`

For each route and locale switch, the test asserts:

- `document.documentElement.lang` matches the selected locale.
- The locale picker value matches the selected locale.
- Visible body text contains the current locale sentinel strings from the matching catalog.
- Visible body text no longer contains the previous locale sentinel strings for that route.

## Reasoning

`GLOC-601` and `GLOC-602` verify that localized routes load and fit the viewport. `GLOC-604` covers a
different failure mode: the app may fetch the right catalog but leave stale text in already-rendered
DOM after a picker change. The regression uses visible text (`innerText`) because this task is about
what the user sees, while technical or hidden catalog state is covered by lower-level i18n tests.

## Result

Locale switching is now covered across all active UI locales and primary routes without assuming a
full page reload.
