# BPM 0.9.0 API Documentation Inventory

Date: 2026-06-21

Backlog item: `BPM090-M2-02`

## Purpose

This inventory is the coverage source for the BPM Administrator/DevOps Guide API integration sections. It records every current
programmatic HTTP operation, its request and response contract, known errors and limitations, and a
planned locale-independent DITA topic ID. It is checked against the generated OpenAPI 3.1 schema
and focused API contracts.

The generated schema currently contains 27 operations: 21 programmatic/service operations and six
HTML product routes tagged `web`. All 21 programmatic/service operations are integration API
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
| `API-PROFILE-005` | `PATCH` | `/api/profiles/{profile_id}` | Partially update description, normalized flags, compliance metadata, or expected revision; it cannot relabel a saved schema. | Integer `profile_id`; JSON `ProfileUpdate`. | `200 ProfileRead` with incremented revision after a material update. | `400` invalid schema/profile; `404` missing or archived profile; `409` stale `expected_revision` or `profile_schema_conversion_required`; `422` request or policy validation. | `admin-task-sync-profile-lifecycle` |
| `API-PROFILE-010` | `POST` | `/api/profiles/{profile_id}/conversion-preview` | Build a value-free, read-only conversion plan for one current stored active profile and a caller-selected exact target artifact. | Integer `profile_id`; JSON `ConversionPreviewRequest` with only `target_artifact_id`. | `200 ConversionPreviewResponse`; an available but blocked plan remains `200` with `compatibility.applicable=false`. | `404` missing source; `409` inactive or retired source; `422` invalid/identical/unsupported target or source; `503` missing exact artifact. Every error has the conversion detail envelope and `mutation=none`. | `admin-task-use-reusable-api-examples` |
| `API-PROFILE-011` | `POST` | `/api/profiles/{profile_id}/conversion-apply` | Atomically rederive and apply one explicitly confirmed, current preview. | Integer `profile_id`; JSON `ConversionApplyRequest` with the reviewed revision, exact source/target identities, and digests. | `200 ConversionApplyResponse` with `status="applied"`, incremented result revision, target validation, compliance disposition, and field accounting. | `404` missing source; `409` stale, blocked, inactive, or retired source; `422` invalid request/precondition; `500` transaction failure; `503` missing exact artifact. Every error has `mutation=none`; stale-identity errors require a fresh preview. | `admin-task-use-reusable-api-examples` |
| `API-PROFILE-012` | `POST` | `/api/profiles/prepare/new` | Atomically create a server-composed profile from catalog identities. | JSON `NewProfilePreparationRequest`; it accepts only name, target schema, starter, CIS identities, and one opaque idempotency key. | `201 ProfileRead` with server-owned baseline provenance; replay of the same accepted key and fingerprint returns the original result. | `409` name conflict or incompatible replay; `422` invalid request or unavailable catalog candidate; `500` transaction failure. Every terminal error is the complete value-free `ProfilePreparationErrorEnvelope` with `mutation=none`; no row is created. | `admin-task-use-reusable-api-examples` |
| `API-PROFILE-013` | `POST` | `/api/profiles/prepare/duplicate` | Atomically rederive and create a source-preserving duplicate from one fixed revision. | JSON `DuplicateProfilePreparationRequest`; it adds source ID, expected source revision, and one opaque idempotency key but never accepts policy/compliance/provenance candidates. | `201 ProfileRead`; replay of the same accepted key and fingerprint returns the original result. | `404` missing source; `409` stale, inactive, blocked, conflict, or incompatible replay; `422` invalid request or unavailable catalog candidate; `500` transaction failure. Every terminal error is the complete value-free `ProfilePreparationErrorEnvelope` with `mutation=none`; conversion diagnostics contain codes/identities only, never policy values. | `admin-task-use-reusable-api-examples` |
| `API-PROFILE-015` | `POST` | `/api/profiles/prepare/duplicate/preview` | Read-only, value-safe duplicate planning before its atomic creation command. | Source and selected catalog identities parsed by the endpoint; it never accepts a policy/compliance/provenance candidate. | `200 DuplicateProfilePreparationPreview`; it never creates or changes a profile. | `404` missing source; `422` invalid planning input; `500` planning failure. Each terminal error is the value-free `ProfilePreparationErrorEnvelope` with `mutation=none`. | `admin-task-use-reusable-api-examples` |
| `API-PROFILE-014` | `GET` | `/api/profiles/extensions/amo-search` | Same-origin, explicit extension-name lookup through BPM's fixed AMO adapter; it is read-only and cannot select an upstream URL or write a profile. | Required bounded `q` and authored `locale`; browser `Sec-Fetch-Site: same-origin`; an opaque HttpOnly session cookie is issued only for private five-minute lookup caching/rate accounting. | `200 AmoSearchApiResponse` with normalized text-only GUID/name/version results or an unavailable/manual-entry state; `Cache-Control: no-store`. | `403` cross-site request, without an AMO attempt; invalid/duplicate/unknown query keys and adapter/upstream failures remain `200` unavailable state codes with no lookup/provider values. | `admin-task-use-reusable-api-examples` |
| `API-PROFILE-006` | `DELETE` | `/api/profiles/{profile_id}` | Soft-delete/archive a profile. | Integer `profile_id`. | `204` empty response. | `404` missing profile; `422` invalid path input. | `admin-task-manage-profile-retirement` |
| `API-PROFILE-007` | `POST` | `/api/profiles/{profile_id}/restore` | Restore an archived profile. | Integer `profile_id`. | `200 ProfileRead`. | `404` profile cannot be restored/found; `422` invalid path input. | `admin-task-manage-profile-retirement` |
| `API-PROFILE-008` | `DELETE` | `/api/profiles/{profile_id}/hard` | Permanently delete one active or archived profile. | Integer `profile_id`. | `204` empty response. | `404` missing profile; `422` invalid path input. | `admin-task-manage-profile-retirement` |
| `API-PROFILE-009` | `DELETE` | `/api/profiles/reset` | Permanently delete every profile in the Library. | None; no confirmation token. | `200 {"deleted":int}`. | No application error currently declared; database failures use framework handling. | `admin-task-manage-profile-retirement` |
| `API-FF-001` | `POST` | `/api/profiles/import/firefox/policies.json` | Validate a canonical Firefox document and create a normalized BPM profile. | JSON `FirefoxPoliciesJsonImportRequest` or multipart import fields. | `201 ProfileRead`. | `400` malformed JSON/document/schema; `409` duplicate name; `415` unsupported media type; `422` request/policy validation. | `admin-task-import-firefox-policies-json` |
| `API-FF-002` | `GET` | `/api/export/profiles/{profile_id}/firefox/policies.json` | Render a BPM profile as canonical Firefox Enterprise `policies.json`. | Integer `profile_id`; export query parameters. | `200 application/json`; optional attachment header and indentation. | `404` missing/not-visible profile; `422` invalid path/query input. | `admin-task-export-firefox-policies-json` |
| `API-VAL-001` | `POST` | `/api/validate/{profile}` | Validate a canonical Firefox document or compatibility policy mapping against a supported channel. | Channel path `profile`; JSON `ValidationRequest`. | `200 {"ok":true,"profile":...}`; a non-object document returns `200` with `ok=false`. | `400` malformed canonical document/profile validation; `422` unknown channel, request, or policy validation; `503` registered schema unavailable. | `admin-task-validate-firefox-policies-json` |

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
| `API-PROFILE-014` | `q` | Required explicit extension-name lookup. The runtime accepts exactly one NFC-normalized nonempty value of at most 100 characters with no C0/C1 control character; it never accepts an upstream URL, path, page, filter, or provider header. |
| `API-PROFILE-014` | `locale` | Required one of `en`, `ru`, `de`, `es-ES`, `fr`, or `zh-CN`; BPM maps it to the fixed AMO locale internally. |
| `API-FF-002` | `download` | Integer `0` or `1`; `1` adds `Content-Disposition` with `profile-{id}-policies.json`. |
| `API-FF-002` | `indent` | Optional integer greater than or equal to zero passed to JSON rendering. |
| `API-FF-002` | `pretty` | Integer `0` or `1`; `1` selects indent `2` only when `indent` is omitted. |

All integer path IDs are FastAPI-validated. Invalid path or constrained query values normally use
the framework `422` validation response.

## Request And Response Models

| Model | Fields and meaning | Stability note | Planned DITA topic |
| --- | --- | --- | --- |
| `ProfileCreate` | Required `name`; optional `description`, `schema_version`, normalized policy `flags`, and opaque `compliance`. | This is BPM's internal normalized profile boundary, not a full Firefox `policies.json` document. Name is limited to 255 characters. | `admin-concept-api-conventions` |
| `ProfileUpdate` | Optional `description`, deprecated `schema_version`, `flags`, `compliance`, and `expected_revision`. | Profile name is immutable through PATCH. A saved profile cannot be relabeled with `schema_version`: PATCH returns the documented `409 ProfileUpdateConflictErrorEnvelope` and callers must use conversion preview/apply. `expected_revision` is the only optimistic-concurrency guard. | `admin-concept-api-conventions` |
| `ProfileRead` | Create fields plus `id`, `revision`, server-owned `baseline_provenance`/value-free `baseline_display`, timestamps, `deleted_at`, `is_deleted`, and `validation_state`. | Datetimes are JSON-serialized by FastAPI/Pydantic; no separate response version field exists. | `admin-concept-api-conventions` |
| `NewProfilePreparationRequest` | Required `name`, `target_schema_id`, `starter_id`, `cis_baseline_id`, and opaque `preparation_idempotency_key`. | The server resolves the document, compliance, and baseline provenance. Same key plus same fingerprint replays the accepted result; a different fingerprint is a `409`. No caller policy, compliance, provenance, or destination field is accepted. | `admin-task-use-reusable-api-examples` |
| `DuplicateProfilePreparationRequest` | New-preparation identities plus required `source_id`, `expected_source_revision`, and opaque `preparation_idempotency_key`. | The server rederives the duplicate from the locked source/current catalogs. Same key plus same fingerprint replays the accepted result; a different fingerprint is a `409`. | `admin-task-use-reusable-api-examples` |
| `DuplicateProfilePreparationPreview` | Value-free duplicate source/catalog identities, conversion availability, warnings/blockers, and a plan identity used by the preparation form. | It is planning only: it cannot create, write, or expose policy/compliance candidate values. | `admin-task-use-reusable-api-examples` |
| `ProfilePreparationErrorEnvelope` | Complete `detail` envelope: kind, contract version, code, client i18n key, HTTP status, `mutation="none"`, and value-free parameters. | This is the stable terminal-error contract for both preparation commands. It deliberately excludes profile names, flags, compliance, source documents, candidates, and conversion diagnostic values. | `admin-task-use-reusable-api-examples` |
| `AmoSearchApiResponse` | `availability`, value-free `reason_code`, normalized text-only `results` of `guid`/`name`/`version`, and `cache_hit`. | This is a same-origin, read-only AMO projection, not an AMO proxy or extension installation interface. `unavailable` means the future UI must keep manual GUID/install-URL entry available; it never blocks profile work. | `admin-task-use-reusable-api-examples` |
| `ConversionPreviewRequest` | Only `target_artifact_id`, the exact selectable target artifact. | The client cannot submit a source document, candidate policy document, compliance candidate, recipe, or localized message. | `admin-task-use-reusable-api-examples` |
| `ConversionPreviewResponse` | Value-free source/target artifact identities and digests, compatibility counts, item classifications, target validation, compliance disposition, warnings/blockers, and plan digest. | Preview is read-only; available does not mean applicable. Raw policy and compliance values are excluded. | `admin-task-use-reusable-api-examples` |
| `ConversionApplyRequest` | Exact source/target line and artifact identities, expected revision, plan/source/schema/registry identities, and digests. | It is a confirmation of a preview, not a client-provided conversion candidate. | `admin-task-use-reusable-api-examples` |
| `ConversionApplyResponse` | Applied source/target identities, source/result revision, value-free result digests, target validation, compliance disposition, and field accounting. | The server rederives the plan and writes atomically; it preserves profile identity/name/description and never accepts raw candidates. | `admin-task-use-reusable-api-examples` |
| `FirefoxPoliciesJsonImportRequest` | `name`, optional description/channel/compliance, and full `document` containing top-level `policies`. | JSON and multipart have different wire representations; multipart `compliance` is a JSON-encoded string. | `admin-task-import-firefox-policies-json` |
| Multipart Firefox import | Required `file` in OpenAPI; runtime also accepts `document`; optional name, description, channel, and JSON-string compliance. | The runtime `document` alias is tested but the current multipart OpenAPI schema declares only `file`. This drift must be explained or corrected before guide publication. | `admin-task-import-firefox-policies-json` |
| `ValidationRequest` | Required free-form `document`. Canonical shape is `{"policies":{...}}`. | A plain policy mapping remains accepted for internal compatibility and is not the preferred external integration shape. | `admin-task-validate-firefox-policies-json` |
| Canonical Firefox export | Top-level JSON object with `policies`; BPM compliance/profile metadata is not exported. | Output media type is `application/json`; no YAML or bulk export endpoint exists. | `admin-task-import-firefox-policies-json` |
| Error response | FastAPI top-level `detail`, containing a string, validation list, or BPM object with `message`, `error`, and/or `issues`. | There is no single versioned error envelope across all operations. Consumers must branch by status and documented operation shape. | `admin-concept-api-conventions` |

## Error Family Inventory

| Status | Current meanings | Integration guidance requirement |
| --- | --- | --- |
| `200` | Successful read/validation; also `ok=false` for a non-object validation document. | Check the validation response body, not status alone, for `API-VAL-001`. |
| `403` | Cross-site AMO search request rejection. | Treat it as an unavailable manual-entry state; BPM starts no upstream request and exposes no request value or provider detail. |
| `201` | Profile created directly or through Firefox document import. | Store returned `id` and `revision`; do not infer identity from name alone. |
| `204` | Archive or permanent delete completed with no response body. | Do not parse JSON from the response. |
| `400` | Invalid schema channel, malformed JSON/canonical document, or profile validation failure. | Inspect whether `detail` is text or an object; do not assume one envelope. |
| `404` | Missing profile, excluded archived profile, or missing duplicate-preparation source. | Decide whether `include_deleted` or restore is appropriate before retrying; a missing duplicate source has a value-free preparation envelope and creates no row. |
| `409` | Duplicate profile name, stale `expected_revision`, forbidden PATCH schema relabel, or duplicate-preparation conflict/staleness/blocker. | Name conflict, concurrent update, conversion-required PATCH, and preparation retry have different recovery flows; use the operation's documented envelope. |
| `500` | A conversion apply or preparation transaction failed. | Conversion and preparation details report `mutation=none`; reload authoritative state and create a fresh preview or reconcile an accepted duplicate key rather than retrying blindly. |
| `415` | Firefox import used an unsupported content type. | Send `application/json` or `multipart/form-data`. |
| `422` | FastAPI request validation, an unknown validation channel, or Firefox policy/schema validation. | Distinguish framework validation lists from BPM `issues` objects; an unknown channel returns the locale-neutral `schema_channel_unknown` code. |
| `503` | Supported validation channel is registered but its schema cannot be loaded. | Treat as service/schema availability, not an invalid user document. |

## OpenAPI HTML Routes: Not Integration API

These operations are present in OpenAPI because their FastAPI routes are not excluded from the
schema. They return BPM HTML product surfaces and are documented by the User Guide, not by the
Administrator/DevOps API integration sections as machine endpoints.

| Web operation ID | Method | Path | Classification |
| --- | --- | --- | --- |
| `WEB-001` | `GET` | `/profiles` | Profile Library HTML route. |
| `WEB-002` | `GET` | `/profiles/compare` | Profile Comparison HTML route. |
| `WEB-003` | `GET` | `/profiles/new` | New profile preparation HTML route. |
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

- There is no authentication or authorization layer on the current API. The preparation commands
  inherit that assumption: BPM does not identify a caller, enforce profile ownership, or authorize
  a source duplicate. Deployments exposing this API must apply their own network and access controls.
- CORS defaults to enabled with `*` origins unless deployment settings override it.
- There is no API version prefix, compatibility policy, deprecation header, or media-type version.
- There is no rate limiting, request quota, or server-provided request/correlation ID for the
  general API. `API-PROFILE-014` is the narrow exception: its fixed AMO lookup adapter has its own
  private per-browser-session/global outbound reservations and no caller-controlled provider.
  The only
  command-specific retry boundaries are `API-PROFILE-012` and `API-PROFILE-013`'s opaque
  preparation idempotency keys; they are not a general API idempotency facility.
- Generic PATCH supports optimistic concurrency through optional `expected_revision`; create,
  import, delete, restore, reset, and export have no equivalent precondition token or ETag. The
  duplicate-preparation command separately binds its source with `expected_source_revision`.
- Schema conversion has a separate two-step concurrency boundary: preview is read-only, while apply
  accepts only the current reviewed identity/digest fields and rederives policy/compliance data on
  the server. It is not a bulk conversion API and cannot be used for retired-ESR migration.
- There is no bulk profile CRUD/export endpoint. List pagination is offset/limit and total counts
  require the separate stats operation.
- Profile CRUD exposes BPM's normalized `flags` and opaque `compliance`, while import/export uses
  canonical Firefox `policies.json`; integrations must not interchange these shapes.
- Profile names are unique at persistence level and cannot be changed through `ProfileUpdate`.
- Error bodies are not a single stable envelope. The two preparation commands are the explicit
  exception: their declared `404`/`409`/`422`/`500` terminal failures always use the documented
  value-free `ProfilePreparationErrorEnvelope`.
- The API does not promise transactional workflows across multiple operations. Consumers must not
  assume a failed multi-step integration is automatically rolled back.
- Health/readiness responses expose only fixed status fields; readiness currently does not report
  individual database, schema, or documentation subsystem checks.

The Administrator/DevOps Guide API integration sections must state these limitations plainly. Documentation does not authorize
adding security, concurrency, versioning, or bulk semantics under this epic.

## Audit Result

- 21 programmatic/service OpenAPI operations map to seven planned primary DITA operation topics.
- Six OpenAPI `web` operations are explicitly assigned to the User Guide rather than integration
  consumers.
- Generated schema UIs, schema/asset routes excluded from OpenAPI, internal Python helpers,
  compatibility validation input, and opaque compliance metadata are classified explicitly.
- The JSON-versus-multipart import shapes, all query parameters, success contracts, known status
  families, and current cross-cutting limitations have bounded documentation ownership.
- Any OpenAPI operation, parameter, request/response model, status behavior, or integration
  guarantee change must update this inventory and its drift test before release.
