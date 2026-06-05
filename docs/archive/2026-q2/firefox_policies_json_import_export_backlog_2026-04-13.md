# Firefox policies.json Import and Export Backlog

## Goal

Make Firefox `policies.json` the user-facing import and export format for Browser Policy Manager.

The product should accept real Firefox Enterprise `policies.json` files, validate them before adding them to the profile library, and export real Firefox `policies.json` files back out. Internal profile JSON/YAML may remain as implementation or compatibility surfaces, but the main product workflow should no longer ask users to download or upload internal BPM profile documents.

## Current state

- Profiles store `flags`, which are the contents of the Firefox `policies` object, not the full external document.
- Profile create/update validation already validates `flags` against bundled Firefox schemas in [app/api/profiles.py](/home/valery/Projects/browser-policy-manager/app/api/profiles.py) and [app/core/policy_validation.py](/home/valery/Projects/browser-policy-manager/app/core/policy_validation.py).
- Firefox `policies.json` export already wraps `flags` as `{ "policies": ... }` in [app/api/export.py](/home/valery/Projects/browser-policy-manager/app/api/export.py) and [app/services/firefox_policy_export.py](/home/valery/Projects/browser-policy-manager/app/services/firefox_policy_export.py).
- There is no dedicated import path for a full Firefox `policies.json` document.
- The wizard export step still exposes internal JSON/YAML download buttons in [app/templates/profiles/_page_wizard_step_export.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_export.html).
- The advanced workspace download strip also exposes internal JSON/YAML routes in [app/templates/profiles/_page_workspace.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_workspace.html). Whether to keep these as advanced compatibility links is a separate product decision, but they should not be presented as the primary handoff format.

## Product contract

The user-facing input and output format is the Firefox Enterprise document:

```json
{
  "policies": {
    "DisableTelemetry": true,
    "BlockAboutConfig": true
  }
}
```

Internally, the application may continue storing only the contents of `policies` in `Profile.flags`. The import/export boundary is responsible for converting between the external Firefox document and the internal profile model.

## Priorities

### P0: Backend import contract

1. Add a Firefox `policies.json` parser and normalizer.

   Problem:
   The current validation helpers expect a `policy_id -> value` object, while the user-facing Firefox file has a root `policies` object.

   Fix:
   Add a service such as `app/services/firefox_policy_import.py` with helpers that:
   - accept a parsed JSON object;
   - require the root value to be an object;
   - require a `policies` property;
   - require `policies` to be an object;
   - return the normalized internal `flags` object;
   - reject unsupported root-level properties unless a deliberate compatibility mode is introduced later.

   Acceptance:
   - `{ "policies": { "DisableTelemetry": true } }` normalizes to `{ "DisableTelemetry": true }`.
   - `{}` is rejected with a clear missing `policies` error.
   - `{ "policies": [] }` is rejected with a clear type error.
   - `{ "flags": { "DisableTelemetry": true } }` is rejected as an internal BPM shape, not silently imported.

2. Validate imported Firefox documents before library insertion.

   Problem:
   Invalid imported files must not create library profiles.

   Fix:
   Reuse the existing schema validation after normalizing `document["policies"]` to `flags`. Map issue paths back to the external document shape by prefixing them with `policies`.

   Acceptance:
   - Invalid policy names are rejected.
   - Invalid nested values, for example `Proxy.Mode = "bogus"`, are rejected.
   - Validation issues identify external paths such as `["policies", "Proxy", "Mode"]`.
   - The error payload remains compatible with the existing `detail.message` and `detail.issues` pattern.

3. Add an import endpoint.

   Problem:
   The UI has no API route for creating a profile from a Firefox `policies.json` file.

   Fix:
   Add an endpoint such as `POST /api/profiles/import/firefox/policies.json`.
   The endpoint should accept either multipart file upload or a JSON body. Prefer multipart for the browser workflow, with fields for:
   - `name`;
   - `schema_version`;
   - optional `description`;
   - optional `owner`.

   Acceptance:
   - Valid import creates a new `ProfileRead` record.
   - Invalid JSON returns a client error without creating a profile.
   - Schema validation failure returns 422 without creating a profile.
   - Duplicate profile name returns 409 using the same conflict semantics as normal profile creation.
   - The created profile stores normalized `flags`, not the full `{ "policies": ... }` wrapper.

### P0: Library import UI

4. Add import controls to the profile library.

   Problem:
   Users need to add existing Firefox `policies.json` files directly to the library.

   Fix:
   Add a library toolbar action near refresh in [app/templates/profiles/_page_workspace.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_workspace.html):
   - visible button: `Import policies.json`;
   - hidden file input accepting `.json` and `application/json`;
   - schema selection should use the existing profile schema selector or an import-specific default if no profile is open.

   Acceptance:
   - A user can select a local `policies.json` file from the library panel.
   - Import status is announced through the existing status banner or a dedicated library import status element.
   - On success, the library refreshes and opens the imported profile.
   - On failure, the selected file does not create or modify a profile.

5. Add client-side import plumbing.

   Problem:
   [app/static/profiles_data.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_data.js) and [app/static/profiles_workspace.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_workspace.js) currently only support CRUD around internal `flags`.

   Fix:
   Add a data-layer function such as `importFirefoxPoliciesJson(formData)` and a workspace handler that:
   - reads the selected file;
   - sends it to the import endpoint;
   - shows parse, validation, and duplicate-name failures clearly;
   - resets the file input after each attempt.

   Acceptance:
   - Valid file imports without requiring manual copy/paste into the editor.
   - Malformed JSON shows a meaningful error.
   - Schema validation errors show the first few issues using the existing `readError` formatting pattern.
   - Import remains keyboard accessible.

### P0: Wizard export cleanup

6. Remove internal JSON/YAML download buttons from step 8.

   Problem:
   The final wizard step currently offers internal BPM JSON, internal YAML, and Firefox `policies.json`. This conflicts with the product contract that handoff should be Firefox `policies.json`.

   Fix:
   In [app/templates/profiles/_page_wizard_step_export.html](/home/valery/Projects/browser-policy-manager/app/templates/profiles/_page_wizard_step_export.html), remove:
   - `wizard-export-json`;
   - `wizard-export-yaml`.

   Keep:
   - `wizard-export-firefox-policies`.

   Acceptance:
   - Step 8 shows only the Firefox `policies.json` download action.
   - The final step no longer references JSON/YAML as separate downloadable formats.
   - The remaining download link still points to `/api/export/profiles/{profile_id}/firefox/policies.json`.

7. Update wizard download-link JavaScript.

   Problem:
   [app/static/profiles_workspace.js](/home/valery/Projects/browser-policy-manager/app/static/profiles_workspace.js) currently assumes the step 8 JSON/YAML elements exist.

   Fix:
   Update `updateActionState()` and `updateDownloadLinks()` so they:
   - only manage `wizardExportFirefoxPoliciesEl` for the wizard final step;
   - guard any legacy internal download links that may remain in JSON editor;
   - do not throw when wizard JSON/YAML elements are absent.

   Acceptance:
   - No console errors on `/profiles`.
   - Export availability still disables/enables the Firefox `policies.json` action correctly.
   - Advanced internal links, if retained, continue to work independently.

8. Update final-step copy and localization.

   Problem:
   i18n strings still say users can download JSON, YAML, or Firefox `policies.json`.

   Fix:
   Update [app/i18n/en.json](/home/valery/Projects/browser-policy-manager/app/i18n/en.json) and [app/i18n/ru.json](/home/valery/Projects/browser-policy-manager/app/i18n/ru.json), especially:
   - `profiles.wizard_export_ready_body`;
   - `profiles.wizard_export_ready_saved`;
   - `profiles.wizard_export_included_body`;
   - download hint strings that mention multiple buttons;
   - any guide text that directs users to JSON/YAML downloads from the wizard.

   Acceptance:
   - Guided export copy speaks about Firefox `policies.json`, not internal formats.
   - RU and EN stay aligned.
   - User-facing text does not expose implementation terms such as internal JSON/YAML.

### P1: User-facing output contract beyond the wizard

9. Decide the advanced download policy.

   Problem:
   JSON editor currently exposes internal JSON/YAML downloads. These may be useful for debugging or compatibility, but they conflict with a strict "input and output are Firefox `policies.json`" reading.

   Decision:
   Remove internal JSON/YAML export routes and user-facing download controls entirely. Firefox `policies.json` is the only product handoff export format.

   Acceptance:
   - The main product workflow only presents Firefox `policies.json` as the handoff file.
   - There are no remaining internal JSON/YAML export controls.
   - Tests and OpenAPI expectations reflect the Firefox-only export surface.

10. Align OpenAPI and docs with the external format.

    Problem:
    The API surface used to have both internal export routes and the Firefox export route, which could confuse users and integrators.

    Fix:
    Update descriptions and docs so:
    - `/api/export/profiles/{profile_id}/firefox/policies.json` is the primary user-facing export endpoint;
    - removed internal JSON/YAML routes are not presented in OpenAPI;
    - import endpoint examples use the Firefox document shape.

    Acceptance:
    - API documentation makes the canonical handoff route obvious.
    - README or product docs include a valid `policies.json` example.
    - There is no guidance telling users to use BPM internal JSON/YAML for Firefox deployment.

### P1: JSON editor full-document mode

11. Decide whether the JSON editor should show full `policies.json`.

    Problem:
    The JSON editor currently edits internal `flags` directly. Moving it to full `policies.json` would align the whole product model, but it touches many wizard sync functions that expect policy keys at the editor root.

    Decision:
    Proceed with full-document mode. The JSON editor should display Firefox `policies.json`, while save and guided synchronization continue to use normalized internal flags through shared adapters.

    Acceptance for a later full-document implementation:
    - The editor displays `{ "policies": ... }`.
    - Save unwraps `policies` before sending `flags` to profile CRUD.
    - Validation accepts the full document and reports external paths.
    - Wizard synchronization reads/writes through a shared adapter instead of assuming policy keys at the editor root.
    - Export never produces a double wrapper such as `{ "policies": { "policies": ... } }`.

12. Add shared document adapters if full-document mode proceeds.

    Problem:
    Many frontend modules call `fromEditorValue()` and then read policy keys directly from the parsed object.

    Fix:
    Add adapter helpers such as:
    - `parseEditorPolicyDocument()`;
    - `toInternalFlags()`;
    - `toFirefoxPoliciesDocument()`;
    - `setPolicyValue()`;
    - `getPolicyValue()`.

    Acceptance:
    - Wizard modules no longer need to know whether the editor stores internal flags or full Firefox documents.
    - JSON/YAML mode switching, validation, save, compare, and guided controls all use the same adapter.
    - Validation from the editor sends the full Firefox document so issue paths stay in the external `policies.*` shape.

### P1: Tests

13. Add backend unit tests for import parsing.

    Acceptance:
    - Valid document normalizes correctly.
    - Missing `policies` is rejected.
    - Non-object root is rejected.
    - Non-object `policies` is rejected.
    - Internal BPM shapes are rejected unless explicitly supported in a compatibility mode.
    - Covered in `tests/test_firefox_policy_import.py`.

14. Add API tests for import endpoint.

    Acceptance:
    - Valid multipart import creates a profile.
    - Invalid JSON returns an error and does not create a profile.
    - Invalid schema value returns 422 with issues.
    - Duplicate name returns 409.
    - Imported profile exports back to the same canonical Firefox `policies.json` shape.
    - Covered in `tests/api/test_firefox_policies_import_api.py`.

15. Add UI regression tests.

    Acceptance:
    - The profile page includes an import `policies.json` control.
    - Step 8 no longer includes `wizard-export-json` or `wizard-export-yaml`.
    - Step 8 still includes `wizard-export-firefox-policies`.
    - User-facing export copy no longer mentions downloading JSON/YAML from the final wizard step.
    - Covered in `tests/test_web_profiles_page.py`.

16. Extend export regression coverage.

    Acceptance:
    - Existing Firefox export tests continue to pass.
    - A round-trip test covers import `policies.json` -> library profile -> export `policies.json`.
    - A regression test catches double wrapping.
    - Covered in `tests/test_firefox_policy_export.py`, `tests/test_export_firefox_policies_json.py`, and `tests/api/test_firefox_policies_import_api.py`.

### P2: Documentation and cleanup

17. Update README and user-facing help.

    Acceptance:
    - Docs say the product imports and exports Firefox Enterprise `policies.json`.
    - Docs include a minimal valid example.
    - Docs explain that users choose the Firefox schema channel before import.
    - Covered in `README.md` and `tests/test_readme_firefox_policies_contract.py`.

18. Add migration notes for internal JSON/YAML.

    Acceptance:
    - If internal JSON/YAML routes remain, their status is documented.
    - If they are hidden from UI, release notes say the final wizard step now exports only Firefox `policies.json`.
    - If routes are removed later, a breaking-change note exists.
    - Covered in `docs/firefox_policies_json_migration_notes_2026-04-14.md`.

## Recommended implementation order

1. Add backend parser/normalizer for Firefox `policies.json`.
2. Add backend validation wrapper with external issue paths.
3. Add import endpoint.
4. Add backend tests for parser and endpoint.
5. Add library import UI and frontend data helper.
6. Remove wizard JSON/YAML buttons.
7. Update wizard download-link JavaScript.
8. Update EN/RU final-step copy.
9. Add UI tests for import control and step 8 cleanup.
10. Decide and implement advanced download policy.
11. Update docs and API descriptions.
12. Revisit full-document JSON editor mode as a separate follow-up.

## Definition of done

- A user can import a valid Firefox `policies.json` file into the profile library.
- Invalid Firefox `policies.json` files are rejected before profile creation.
- Imported profiles validate against the selected Firefox schema channel.
- The final wizard step offers only Firefox `policies.json` as the download format.
- Exported handoff files use the canonical Firefox shape `{ "policies": ... }`.
- The UI no longer presents internal BPM JSON/YAML as the normal user handoff format.
- Tests cover import validation, round-trip export, and the wizard button cleanup.

## Risks and notes

- Existing profile update semantics merge `flags` on PATCH. Import should create a new profile in the first increment to avoid ambiguity between "replace file" and "merge into current profile".
- The JSON editor full-document move is handled through shared frontend adapters so wizard modules keep using normalized flags while users see Firefox `policies.json`.
- Strictly rejecting root-level keys other than `policies` is the safest Firefox-compatible behavior. If compatibility with future metadata is needed, introduce it deliberately rather than accepting unknown keys silently.
