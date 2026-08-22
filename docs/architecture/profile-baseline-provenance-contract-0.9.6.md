# BPM 0.9.6 Profile Baseline Provenance Contract

Date: 2026-08-20

Backlog item: `BPM096-M2-04`

Status: active planning contract; it deliberately makes no current runtime, API, database,
migration, catalog, or rendered-header claim.

## Purpose and current boundary

Flags can resemble a starter preset or a CIS layer without having been created from one. They are
not provenance. This contract defines the durable server-owned record M3 will add and the only
projection M5 headers may render. The M2-03 preparation form submits catalog identities; the server
records resolved identities only after it composes and validates the saved profile.

Today `Profile` has `schema_version`, `flags`, and optional `compliance`; generic create, PATCH, and
Firefox import accept caller-composed values; and starter/CIS web catalog entries have no persisted
identity. The conversion planner can recompute or invalidate raw `compliance`, but cannot make a
saved header truthful by itself. This contract changes none of that current behavior. It does not
authorize changes to `Profile`, Pydantic models, generic CRUD/import, conversion, retirement
tooling, Alembic history, catalogs, or templates.

`baseline_provenance` is the non-null M3-01 profile-owned envelope. `compliance` remains a payload,
not header authority. A profile is never classified from flags, `compliance` shape or presence, a
matching current catalog, or an old Guided selection. An old-looking document is `Custom/imported`
unless its own persisted envelope says otherwise.

## Durable envelope

M3-01 stores one JSON/I-JSON envelope for active and archived profiles. Its version and pinned schema
artifact make catalog drift observable. SHA-256 values are lowercase 64-hex digests; IDs/versions are
nonempty opaque catalog values. Normalized columns are allowed only if this logical record is stored
and serialized atomically with the profile.

<!-- bpm096-baseline-provenance-contract-v1 -->
```json
{
  "contract_id": "bpm096-profile-baseline-provenance",
  "contract_version": 1,
  "status": "planning-only-no-runtime-change",
  "storage": {
    "profile_field": "baseline_provenance",
    "required_after_m3_01": true,
    "authoritative_for_header": true,
    "flags_or_compliance_inference": "forbidden"
  },
  "starter": {
    "identity_states": ["catalog", "custom-imported"],
    "catalog_identity_fields": ["catalog_id", "catalog_version", "preset_id", "definition_sha256", "resolved_schema_artifact_id"],
    "custom_imported_catalog_fields": "all-null",
    "request_only_directive": "keep_current"
  },
  "cis": {
    "identity_states": ["none", "catalog", "custom-imported"],
    "display_statuses": ["none", "verified", "manual-review", "invalidated", "unavailable"],
    "catalog_identity_fields": ["catalog_id", "catalog_version", "baseline_id", "benchmark_id", "benchmark_version", "layer_sha256", "merge_rules_sha256", "merge_result_sha256", "resolved_schema_artifact_id"],
    "current_claim_rule": "true-only-for-verified",
    "noncurrent_statuses": ["none", "manual-review", "invalidated", "unavailable"]
  },
  "api": {
    "profile_read_fields": ["baseline_provenance", "baseline_display"],
    "request_provenance_authority": "server-only",
    "generic_create_default": "custom-imported-manual-review",
    "firefox_import_default": "custom-imported-manual-review",
    "legacy_migration_default": "custom-imported-manual-review"
  },
  "duplicate": {
    "same_schema_exact_copy": "preserve-baseline-identities-and-statuses",
    "different_composition": "rederive-under-m2-05",
    "source_mutation": "forbidden"
  },
  "conversion": {
    "verified_target_cis": "requires-target-recomputation-and-proof",
    "unproven_target_cis": "invalidated-or-manual-review",
    "source_preset_history": "never-inferred-from-flags"
  }
}
```

The logical envelope has `lineage`, `starter`, and `cis`. `lineage.kind` is `prepared`,
`generic-create`, `firefox-import`, `legacy-migration`, `duplicate`, or `conversion`. Duplicate and
conversion lineage bind source ID/revision and, when needed, a reviewed plan digest. It records target
derivation, never a writable parent relationship; the source remains immutable under M2-03.

Starter `catalog` requires the pinned catalog ID/version, exact `preset_id`, definition digest, and
resolved schema artifact. `definition_sha256` identifies the resolved schema-specific definition,
not flags. Its disposition is `created`, `preserved`, or
`recomposed`. `custom-imported` has all null catalog fields and disposition `custom-imported`.
**Custom/imported** means unknown/non-catalog origin, not no policies. `keep_current` is request-only,
never stored as a preset ID, and invalid for source-free create. A same-schema duplicate records its
source preset ID with disposition `preserved`; it never stores `keep_current` as that ID. M2-05 decides
a duplicate's real target identity or Custom/imported result.

CIS `none` requires status `none`, no catalog identity, and `current_claim == false`; only a
server composition can choose it, never import/legacy migration. CIS `catalog` requires all nine
identity fields, including benchmark, layer, merge-rule/result, and schema artifacts; `proof_digest`
binds policy/review evidence. CIS `custom-imported` has null catalog fields and status
`manual-review` with a stable reason such as `cis_provenance_unknown`.

`verified` requires catalog identity, matching proof, no unresolved review decision, and
`current_claim == true`. It means saved policy matches pinned baseline evidence, not that a deployed
browser or organization is compliant. `manual-review` preserves known identity but sets the claim
false; it is required for unresolved merges, manual edits, import, and unknown legacy provenance.
`invalidated` preserves historical identity/proof but names target/schema reason. `unavailable`
preserves identity when exact artifacts cannot resolve. Neither may fall back to `verified`, `none`,
or a current catalog label.

## API serialization and header projection

After M3-01, `ProfileRead` gains additive non-null `baseline_provenance` and `baseline_display`.
Request DTOs (`ProfileCreate`, `ProfileUpdate`, generic import) cannot accept either as caller
authority. Dedicated M3 preparation commands accept M2-03 catalog identities and return the
server-derived envelope. Generic create and Firefox import remain generic but save/read as
Custom/imported/manual-review. A generic policy/compliance mutation downgrades former verified CIS
to manual-review in the same write; caller metadata cannot restore verified.

`baseline_display` is the locale-neutral, compact projection of stored provenance:

```text
baseline_display = {
  starter: { identity_state, catalog_id?, catalog_version?, preset_id?, disposition?, availability },
  cis: { identity_state, display_status, baseline_id?, benchmark_id?, benchmark_version?,
         current_claim, reason_code? }
}
```

Starter availability is available only if the exact saved identity resolves; it never substitutes a
newer preset. `preset_id` and disposition are stable, label-safe state; API responses contain no
localized labels or policy values. An older catalog record that predates persisted `preset_id` reports
`starter_preset_identity_unavailable` rather than inferring one from flags or a current catalog. M5
localizes exactly this projection in Guided, All settings, and JSON, rendering the truth table rather
than comparing flags:

| Stored projection | Header fact | Prohibited claim |
| --- | --- | --- |
| starter catalog / available | Starter: exact saved preset ID/version and created/recomposed/preserved disposition | Current flags still equal preset. |
| starter Custom/imported | Starter: Custom/imported | Recognizable preset was used. |
| CIS none / none | CIS baseline: None | Profile was reviewed for CIS. |
| CIS catalog / verified | CIS baseline: level/version, verified evidence | Browser/deployment/organization is compliant. |
| CIS any / manual-review | Identity or Custom/imported; manual review required | Current benchmark compliance. |
| CIS catalog / invalidated | Historical identity and reason | Target-schema/current CIS claim. |
| CIS catalog / unavailable | Saved identity unavailable and reason | Replacement/current baseline. |

Reload/direct links and all editors receive this same server projection. A missing, malformed,
unknown-version, or inconsistent envelope fails closed: API serialization reports
`baseline_provenance_unavailable`, and the header is unavailable/manual-review with recovery. It must
not inspect flags or untrusted `compliance` to repair a display.

## Import, legacy, duplicate, and conversion compatibility

| Case | Required stored result | Compatibility rule |
| --- | --- | --- |
| Generic `POST /api/profiles` with caller flags/compliance | lineage `generic-create`; starter Custom/imported; CIS Custom/imported + manual review | Existing validation/CRUD remains; caller metadata is not catalog proof. |
| Firefox `policies.json` import, with or without compliance JSON | lineage `firefox-import`; same Custom/imported/manual-review result | Imported `compliance` is raw data, not a CIS display claim. |
| Any row predating M3-01, including archived rows | lineage `legacy-migration`; same Custom/imported/manual-review result | Do not pattern-match flags/current catalog/`keep_current`/old compliance shape. |
| Same-schema duplicate with exact M2-05 source composition | lineage `duplicate`; preserve starter/CIS identities and statuses exactly | Copying never promotes Custom/imported/manual-review/invalidated/unavailable. |
| Different selection or cross-schema duplicate | lineage `duplicate` with plan digest; only M2-05 rederived result | Client flags, labels, and `keep_current` cannot choose target status. |
| Explicit schema conversion | lineage `conversion` with source revision/plan digest; starter is history | Target CIS verifies only after target recomputation/proof; otherwise manual-review or invalidated. |

Existing planner dispositions (`absent`, `preserved-verified`, `recomputed`, and
`invalidated-preserved`) remain evidence until M3 integration. `absent` cannot manufacture CIS none
for import/legacy rows; `recomputed` verifies only under this proof rule; `invalidated-preserved`
becomes invalidated; unproven raw compliance becomes manual-review. Historical retirement owners and
old Alembic revisions stay immutable; M3-01 owns the new migration and includes archived rows without
rewriting policy data.

## Delivery ownership and proof

- M3-01 adds storage, constraints, reads, all-row defaults, and generic-write safety; M3-02 pins
  identities; M3-03/M2-05 own duplicate composition; M3-04/M3-05 write atomically; M3-06 owns API.
- M5-03/M5-04 render only `baseline_display`; M5-06 proves reload/cross-editor parity. No selector,
  client catalog reconstruction, or flag inference is allowed.
- Future runtime proof covers clean/migrated/archived/imported/generic/duplicate/converted rows,
  catalog withdrawal, manual edits, invalidated CIS, and SQLite/PostgreSQL serialization. This test
  guards planning only.
