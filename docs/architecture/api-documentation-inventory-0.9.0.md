# BPM 0.9.0 API Documentation Inventory

Date: 2026-06-21

Backlog item: `BPM090-M2-02`

## Purpose

This inventory is the coverage source for the BPM Administrator/DevOps Guide API integration sections. It records every current
programmatic HTTP operation, its request and response contract, known errors and limitations, and a
planned locale-independent DITA topic ID. It is checked against the generated OpenAPI 3.1 schema
and focused API contracts.

The generated schema currently contains 21 operations: 15 programmatic/service operations and six
HTML product routes tagged `web`. Only the 15 programmatic/service operations are integration API
coverage. The six HTML routes remain product UI navigation and must not be presented as a stable
machine-integration API.

## Programmatic And Service Operations

| Operation ID | Method | Path | Purpose | Primary input | Success contract | Primary error families | Planned DITA topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `API-SVC-001` | `GET` | `/` | Read BPM identity, status, and runtime version. | None. | `200` JSON with `status`, `app`, `name`, `version`, and `message`. | No application error currently declared. | `admin-task-check-health-readiness` |
| `API-HEALTH-001` | `GET` | `/health` | Liveness probe. | None. | `200 {"status":"ok"}`. | No application error currently declared. | `admin-task-check-health-readiness` |
| `API-HEALTH-002` | `GET` | `/health/ready` | Readiness probe. | None. | `200` JSON with `status="ready"` and `ready=true`. | No dependency detail or degraded state is currently exposed. | `admin-task-check-health-readiness` |
| `API-PROFILE-001` | `GET` | `/api/profiles` | List profiles with search, lifecycle, validation, schema, sorting, and offset pagination. | Query parameters from the list-query table. | `200 ProfileRead[]`. | `422` for invalid typed/ranged query input. | `admin-task-sync-profile-lifecycle` |
| `API-PROFILE-002` | `GET` | `/api/profiles/stats` | Return Library filtered and total counts for the current filter context. | Query filter parameters from the stats-query table. | `200 {"filtered":int,"total":int}`. | `422` for invalid typed query input. | `admin-task-sync-profile-lifecycle` |
| `API-PROFILE-003` | `GET` | `/api/profiles/{profile_id}` | Read one active or explicitly included archived profile. | Integer `profile_id`; optional `include_deleted`. | `200 ProfileRead`. | `404` missing/not-visible profile; `422` invalid path/query input. | `admin-task-sync-profile-lifecycle` |
| `API-PROFILE-004` | `POST` | `/api/profiles` | Create a profile from BPM's normalized profile model. | JSON `ProfileCreate`. | `201 ProfileRead`. | `400` invalid/unknown schema; `409` duplicate name; `422` request or policy validation. | `admin-task-sync-profile-lifecycle` |
| `API-PROFILE-005` | `PATCH` | `/api/profiles/{profile_id}` | Partially update description, schema, normalized flags, compliance metadata, or expected revision. | Integer `profile_id`; JSON `ProfileUpdate`. | `200 ProfileRead` with incremented revision after a material update. | `400` invalid schema/profile; `404` missing or archived profile; `409` stale `expected_revision`; `422` request or policy validation. | `admin-task-sync-profile-lifecycle` |
| `API-PROFILE-006` | `DELETE` | `/api/profiles/{profile_id}` | Soft-delete/archive a profile. | Integer `profile_id`. | `204` empty response. | `404` missing profile; `422` invalid path input. | `admin-task-manage-profile-retirement` |
| `API-PROFILE-007` | `POST` | `/api/profiles/{profile_id}/restore` | Restore an archived profile. | Integer `profile_id`. | `200 ProfileRead`. | `404` profile cannot be restored/found; `422` invalid path input. | `admin-task-manage-profile-retirement` |
| `API-PROFILE-008` | `DELETE` | `/api/profiles/{profile_id}/hard` | Permanently delete one active or archived profile. | Integer `profile_id`. | `204` empty response. | `404` missing profile; `422` invalid path input. | `admin-task-manage-profile-retirement` |
| `API-PROFILE-009` | `DELETE` | `/api/profiles/reset` | Permanently delete every profile in the Library. | None; no confirmation token. | `200 {"deleted":int}`. | No application error currently declared; database failures use framework handling. | `admin-task-manage-profile-retirement` |
| `API-FF-001` | `POST` | `/api/profiles/import/firefox/policies.json` | Validate a canonical Firefox document and create a normalized BPM profile. | JSON `FirefoxPoliciesJsonImportRequest` or multipart import fields. | `201 ProfileRead`. | `400` malformed JSON/document/schema; `409` duplicate name; `415` unsupported media type; `422` request/policy validation. | `admin-task-import-firefox-policies-json` |
| `API-FF-002` | `GET` | `/api/export/profiles/{profile_id}/firefox/policies.json` | Render a BPM profile as canonical Firefox Enterprise `policies.json`. | Integer `profile_id`; export query parameters. | `200 application/json`; optional attachment header and indentation. | `404` missing/not-visible profile; `422` invalid path/query input. | `admin-task-export-firefox-policies-json` |
| `API-VAL-001` | `POST` | `/api/validate/{profile}` | Validate a canonical Firefox document or compatibility policy mapping against a supported channel. | Channel path `profile`; JSON `ValidationRequest`. | `200 {"ok":true,"profile":...}`; a non-object document returns `200` with `ok=false`. | `400` malformed canonical document/profile validation; `404` unknown channel; `422` request/policy validation; `503` registered schema unavailable. | `admin-task-validate-firefox-policies-json` |

## Query Parameter Inventory

| Operation | Parameter | Contract |
| --- | --- | --- |
| `API-PROFILE-001`, `API-PROFILE-002` | `q` | Optional substring filter over profile name/description. |
| `API-PROFILE-001`, `API-PROFILE-002` | `schema_version` | Optional exact schema-channel filter. The API type is string; supported-value validation is operation-specific. |
| `API-PROFILE-001`, `API-PROFILE-002` | `validation_state` | Optional `valid`, `invalid`, or `not_validated` filter; currently described rather than OpenAPI-enumerated. |
| `API-PROFILE-001`, `API-PROFILE-002` | `lifecycle` | Defaults to `active`; described values are `active`, `archived`, and `all`, but the OpenAPI type is currently plain string. |
| `API-PROFILE-001`, `API-PROFILE-002` | `include_deleted` | Boolean compatibility flag for including soft-deleted rows; lifecycle semantics must be documented together with it. |
| `API-PROFILE-001` | `limit` | Integer, default `50`, minimum `1`, maximum `200`. |
| `API-PROFILE-001` | `offset` | Integer, default `0`, minimum `0`; there is no cursor or next-page link. |
| `API-PROFILE-001` | `sort` | Defaults to `updated_at`; described fields are `created_at`, `updated_at`, `name`, `schema_version`, and `id`; currently not an OpenAPI enum. |
| `API-PROFILE-001` | `order` | Defaults to `desc`; described values are `asc` and `desc`; currently not an OpenAPI enum. |
| `API-PROFILE-003` | `include_deleted` | Boolean, default `false`; allows an archived profile to be returned. |
| `API-FF-002` | `include_deleted` | Boolean, default `false`; permits API export of an archived profile even though the current Library UI disables its direct export action. |
| `API-FF-002` | `download` | Integer `0` or `1`; `1` adds `Content-Disposition` with `profile-{id}-policies.json`. |
| `API-FF-002` | `indent` | Optional integer greater than or equal to zero passed to JSON rendering. |
| `API-FF-002` | `pretty` | Integer `0` or `1`; `1` selects indent `2` only when `indent` is omitted. |

All integer path IDs are FastAPI-validated. Invalid path or constrained query values normally use
the framework `422` validation response.

## Request And Response Models

| Model | Fields and meaning | Stability note | Planned DITA topic |
| --- | --- | --- | --- |
| `ProfileCreate` | Required `name`; optional `description`, `schema_version`, normalized policy `flags`, and opaque `compliance`. | This is BPM's internal normalized profile boundary, not a full Firefox `policies.json` document. Name is limited to 255 characters. | `admin-concept-api-conventions` |
| `ProfileUpdate` | Optional `description`, `schema_version`, `flags`, `compliance`, and `expected_revision`. | Profile name is immutable through PATCH. `expected_revision` is the only optimistic-concurrency guard. | `admin-concept-api-conventions` |
| `ProfileRead` | Create fields plus `id`, `revision`, timestamps, `deleted_at`, `is_deleted`, and `validation_state`. | Datetimes are JSON-serialized by FastAPI/Pydantic; no separate response version field exists. | `admin-concept-api-conventions` |
| `FirefoxPoliciesJsonImportRequest` | `name`, optional description/channel/compliance, and full `document` containing top-level `policies`. | JSON and multipart have different wire representations; multipart `compliance` is a JSON-encoded string. | `admin-task-import-firefox-policies-json` |
| Multipart Firefox import | Required `file` in OpenAPI; runtime also accepts `document`; optional name, description, channel, and JSON-string compliance. | The runtime `document` alias is tested but the current multipart OpenAPI schema declares only `file`. This drift must be explained or corrected before guide publication. | `admin-task-import-firefox-policies-json` |
| `ValidationRequest` | Required free-form `document`. Canonical shape is `{"policies":{...}}`. | A plain policy mapping remains accepted for internal compatibility and is not the preferred external integration shape. | `admin-task-validate-firefox-policies-json` |
| Canonical Firefox export | Top-level JSON object with `policies`; BPM compliance/profile metadata is not exported. | Output media type is `application/json`; no YAML or bulk export endpoint exists. | `admin-task-import-firefox-policies-json` |
| Error response | FastAPI top-level `detail`, containing a string, validation list, or BPM object with `message`, `error`, and/or `issues`. | There is no single versioned error envelope across all operations. Consumers must branch by status and documented operation shape. | `admin-concept-api-conventions` |

## Error Family Inventory

| Status | Current meanings | Integration guidance requirement |
| --- | --- | --- |
| `200` | Successful read/validation; also `ok=false` for a non-object validation document. | Check the validation response body, not status alone, for `API-VAL-001`. |
| `201` | Profile created directly or through Firefox document import. | Store returned `id` and `revision`; do not infer identity from name alone. |
| `204` | Archive or permanent delete completed with no response body. | Do not parse JSON from the response. |
| `400` | Invalid schema channel, malformed JSON/canonical document, or profile validation failure. | Inspect whether `detail` is text or an object; do not assume one envelope. |
| `404` | Missing profile, excluded archived profile, or unknown validation channel. | Decide whether `include_deleted` or restore is appropriate before retrying. |
| `409` | Duplicate profile name or stale `expected_revision`. | Name conflict and concurrent update require different recovery flows. |
| `415` | Firefox import used an unsupported content type. | Send `application/json` or `multipart/form-data`. |
| `422` | FastAPI request validation or Firefox policy/schema validation. | Distinguish framework validation lists from BPM `issues` objects. |
| `503` | Supported validation channel is registered but its schema cannot be loaded. | Treat as service/schema availability, not an invalid user document. |

## OpenAPI HTML Routes: Not Integration API

These operations are present in OpenAPI because their FastAPI routes are not excluded from the
schema. They return BPM HTML product surfaces and are documented by the User Guide, not by the
Administrator/DevOps API integration sections as machine endpoints.

| Web operation ID | Method | Path | Classification |
| --- | --- | --- | --- |
| `WEB-001` | `GET` | `/profiles` | Profile Library HTML route. |
| `WEB-002` | `GET` | `/profiles/compare` | Profile Comparison HTML route. |
| `WEB-003` | `GET` | `/profiles/new` | New Guided draft HTML route. |
| `WEB-004` | `GET` | `/profiles/{profile_id}/edit` | Saved Guided Editor HTML route. |
| `WEB-005` | `GET` | `/profiles/{profile_id}/settings` | All Settings HTML route. |
| `WEB-006` | `GET` | `/profiles/{profile_id}/json` | JSON Editor HTML route. |

## Excluded, Generated, And Internal Surfaces

| Surface | Classification | Documentation treatment |
| --- | --- | --- |
| `/openapi.json` | FastAPI-generated schema endpoint, not listed inside its own path map. | Document as the discovery source for the current contract. |
| `/docs` and `/redoc` | FastAPI-generated interactive schema UIs. | Preserve them when product documentation is added under `/help/`; do not confuse `/docs` with the DITA portal. |
| `/i18n/{locale}.json` | Public runtime asset route with `include_in_schema=False`. | User Guide localization implementation detail, not integration API. |
| `/favicon.ico` and `/static/*` | Product asset routes excluded from OpenAPI. | No Administrator/DevOps API integration operation topic. |
| `_list_profiles_core` and other underscore-prefixed handlers | Internal Python reuse/test helpers, not HTTP routes. | Never document as callable API operations. |
| Plain mapping accepted by `/api/validate/{profile}` | Exposed compatibility behavior described in code as internal compatibility. | Mention as compatibility only; all new examples use full `policies.json`. |
| `compliance` objects | Exposed opaque metadata with no public versioned schema. | Document pass-through behavior and instability; do not invent fields or guarantees. |

## Current Cross-Cutting Limitations

- There is no authentication or authorization layer on the current API.
- CORS defaults to enabled with `*` origins unless deployment settings override it.
- There is no API version prefix, compatibility policy, deprecation header, or media-type version.
- There is no rate limiting, request quota, retry contract, idempotency key, or server-provided
  request/correlation ID.
- Only PATCH supports optimistic concurrency through optional `expected_revision`; create, import,
  delete, restore, reset, and export have no equivalent precondition token or ETag.
- There is no bulk profile CRUD/export endpoint. List pagination is offset/limit and total counts
  require the separate stats operation.
- Profile CRUD exposes BPM's normalized `flags` and opaque `compliance`, while import/export uses
  canonical Firefox `policies.json`; integrations must not interchange these shapes.
- Profile names are unique at persistence level and cannot be changed through `ProfileUpdate`.
- Error bodies are not a single stable envelope, and generated OpenAPI does not enumerate every
  application error response raised by handlers.
- The API does not promise transactional workflows across multiple operations. Consumers must not
  assume a failed multi-step integration is automatically rolled back.
- Health/readiness responses expose only fixed status fields; readiness currently does not report
  individual database, schema, or documentation subsystem checks.

The Administrator/DevOps Guide API integration sections must state these limitations plainly. Documentation does not authorize
adding security, concurrency, versioning, or bulk semantics under this epic.

## Audit Result

- 15 programmatic/service OpenAPI operations map to 13 planned primary DITA operation topics.
- Six OpenAPI `web` operations are explicitly assigned to the User Guide rather than integration
  consumers.
- Generated schema UIs, schema/asset routes excluded from OpenAPI, internal Python helpers,
  compatibility validation input, and opaque compliance metadata are classified explicitly.
- The JSON-versus-multipart import shapes, all query parameters, success contracts, known status
  families, and current cross-cutting limitations have bounded documentation ownership.
- Any OpenAPI operation, parameter, request/response model, status behavior, or integration
  guarantee change must update this inventory and its drift test before release.
