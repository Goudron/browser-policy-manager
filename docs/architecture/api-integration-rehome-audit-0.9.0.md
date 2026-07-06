# BPM 0.9.0 API Integration Re-home Audit

Status: **Re-home completed for BPM 0.9.0**  
Decision date: 2026-06-30  
Backlog item: `BPM090-M12-07`

## Purpose

This audit records the completed migration after integration guidance moved into the
Administrator/DevOps Guide. The machine-readable source of truth is
`api-integration-rehome-audit-0.9.0.json`.

The API Integration Guide is now a thin compatibility landing page after
`BPM090-M12-07`. User Guide topics remain focused on browser UI workflows and
user-visible recovery. Administrator/DevOps becomes the owner for endpoint,
request/response, health/readiness, retry, automation, and external control-product
procedures.

## Decisions

- Moved all 13 current `api-*` topics to `admin-*` topics, preserving
  examples, warnings, OpenAPI operation coverage, and six-locale parity.
- Keep User Guide import/export/validation/troubleshooting topics, but remove
  their API procedure ownership in the migration task.
- Preserve user-facing troubleshooting in the User Guide when the reader is
  responding to a visible BPM status or browser workflow failure.
- Move programmatic request shapes, endpoint/query options, health checks,
  retry/evidence decisions, reusable curl/Python examples, and external control
  product scenarios to the Administrator/DevOps Guide.
- Keep the old API guide entry point reachable through a thin compatibility landing page until a
  future alias layer or guide-map contract explicitly removes the API guide.

## Migrated API Topics And Admin Destinations

| Former API topic | Current admin topic | Current section |
| --- | --- | --- |
| `api-concept-integration-audience` | `admin-concept-integration-audience` | integration/audience-and-boundaries |
| `api-concept-supported-patterns` | `admin-concept-supported-integration-patterns` | integration/supported-patterns |
| `api-concept-api-conventions` | `admin-concept-api-conventions` | integration/api-conventions |
| `api-concept-api-limitations` | `admin-concept-api-limitations` | integration/current-limitations |
| `api-task-sync-profile-lifecycle` | `admin-task-sync-profile-lifecycle` | integration/profile-lifecycle |
| `api-task-manage-profile-retirement` | `admin-task-manage-profile-retirement` | integration/profile-lifecycle |
| `api-task-import-firefox-policies-json` | `admin-task-import-firefox-policies-json` | integration/import-export |
| `api-task-export-firefox-policies-json` | `admin-task-export-firefox-policies-json` | integration/import-export |
| `api-task-validate-firefox-policies-json` | `admin-task-validate-firefox-policies-json` | integration/validation-gates |
| `api-task-check-health-readiness` | `admin-task-check-health-readiness` | operations/health-and-readiness |
| `api-task-run-pull-compare-update-scenario` | `admin-task-run-pull-compare-update-scenario` | integration/control-product-runbooks |
| `api-task-run-import-review-export-scenario` | `admin-task-run-import-review-export-scenario` | integration/control-product-runbooks |
| `api-task-use-reusable-api-examples` | `admin-task-use-reusable-api-examples` | integration/examples |

## User Guide Topics That Stay User-owned

| User topic | Retained User Guide scope | Future admin cross-link |
| --- | --- | --- |
| `ug-task-import-policies-json` | Library/UI import steps and visible recovery. | `admin-task-import-firefox-policies-json` |
| `ug-task-export-policies-json` | Library/JSON Editor export steps and active-profile recovery. | `admin-task-export-firefox-policies-json` |
| `ug-task-validate-profile` | Visible validation action and profile readiness decision. | `admin-task-validate-firefox-policies-json` |
| `ug-troubleshoot-import-failure` | User-visible import diagnostics and retry limit. | `admin-task-import-firefox-policies-json` |
| `ug-troubleshoot-policy-validation` | Visible validation-error classification and UI recovery. | `admin-task-validate-firefox-policies-json` |
| `ug-troubleshoot-schema-mismatch` | ESR/Release mismatch decision and UI recovery. | `admin-task-validate-firefox-policies-json` |
| `ug-troubleshoot-product-connection` | Browser/UI connection recovery and maintainer handoff evidence. | `admin-task-check-health-readiness` |

## Fixtures And Tests

The re-home must preserve the import/export fixtures, schema-validation fixtures,
API-state fixture, API topic contracts, OpenAPI drift gate, API locale parity gate,
User Guide import/export contract, guide-map contract, and this audit contract.

The no-lost-procedure rule is: every current API topic has one future admin topic,
and every API-adjacent User Guide procedure fragment has either retained UI scope
or a future admin cross-link.
