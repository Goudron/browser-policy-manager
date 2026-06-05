# Validation And Error I18n Audit

Date: `2026-05-30`

Backlog item: `GLOC-403`

Scope: API/browser validation messages, import errors, JSON errors, save conflicts, and common
request failures.

## Decisions

- `profiles_data.js` now maps common API error details to locale-backed strings before surfacing
  them in status banners. This covers profile not found, duplicate profile names, revision
  conflicts, invalid JSON request bodies, unsupported import content types, locale endpoint
  failures, and policy/profile validation wrapper messages.
- Client-side policies.json shape errors are locale-backed through
  `profiles.error_expected_policies_document_root` and `profiles.error_expected_policies_object`.
- Dynamic schema identifiers remain interpolated, for example unknown schema profile names and
  unavailable schema profile names.
- Deep schema validation issue details can still include technical English from the policy schema
  validator. Those are treated as diagnostic details inside localized error wrappers rather than
  primary UI copy.
- Unknown or malformed error payloads now fall back to `profiles.error_api_unknown` instead of
  showing a raw response body as user-facing text.

## Validation Contract

`tests/test_validation_error_i18n.py` verifies that all new error keys exist in every active
catalog, executes `profiles_data.js` with a non-English catalog, and checks that common API errors
resolve through localized strings.
