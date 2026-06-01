# Localized Import/Edit/Export Workflow Audit - 2026-05-31

Backlog item: `GLOC-605`

Scope: run a representative profile workflow in every active UI locale: import a Firefox
`policies.json`, open the Guided editor surface, edit All settings, validate, and export Firefox
`policies.json`.

## Browser Regression

Added browser test:

- `tests/test_ui_browser_tabs.py::test_localized_import_edit_validate_export_workflow_browser_regression`

Locales covered:

- `en`
- `ru`
- `de`
- `zh-CN`
- `fr`
- `es-ES`

Workflow covered in each locale:

1. Open Library and switch the real locale picker to the target locale.
2. Import a valid Firefox `policies.json` through the Library file input, creating a new profile.
3. Open Guided editor and verify the localized guided profile controls are active.
4. Open All settings and add a locale-specific boolean preference.
5. Validate the edited profile and save it.
6. Open JSON editor, verify the Firefox export link, and fetch the exported `policies.json` through
   the public export API.

For every locale, the test asserts route-specific catalog text is visible on Library, Guided editor,
All settings, and JSON editor. The exported document must include the imported policy plus the
All settings edit:

- `DisableTelemetry: true`
- `Preferences.browser.gloc605.<locale>: true`

## Reasoning

Earlier locale checks prove that pages load, fit the viewport, and switch catalogs. `GLOC-605`
covers the core operational path: importing real Firefox policy JSON, entering the guided workflow,
editing through catalog-style controls, validating, saving, and exporting the final Firefox document while the UI is
running in each locale.

## Result

The localized workflow is now covered end to end across all six active UI locales.
