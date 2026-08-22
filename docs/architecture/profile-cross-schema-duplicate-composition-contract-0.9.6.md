# BPM 0.9.6 Profile Duplicate Composition Contract

Date: 2026-08-20

Backlog item: `BPM096-M2-05`

Status: active planning contract; it adds no runtime composer, persistence field, API, route,
template, catalog entry, generated artifact, or migration.

## Purpose and authority

This contract freezes the server-owned derivation that M3-03 and M3-05 must use when duplicating a
profile. It composes one new target candidate; it never converts, patches, archives, relabels, or
otherwise writes the source. M2-03 remains authoritative for the single transaction, idempotency,
zero-row failure, and post-commit reconciliation lifecycle. M2-04 remains authoritative for the
stored baseline envelope and truthful CIS display states.

The existing pure conversion planner and immutable recipe registry are the only cross-schema
conversion authority. The production registry currently contains zero Firefox transformations, so
any non-empty difference that the planner cannot prove remains blocked. This contract does not add
a recipe or weaken the pairwise no-silent-loss contract.

The active lifecycle catalog currently exposes four exact selectable artifacts. Coverage means all
four same-schema targets and all 12 ordered non-self pairs; evidence for `A -> B` never proves
`B -> A`.

## Derivation order and precedence

The service first binds one complete source snapshot: ID, active lifecycle, revision, exact schema
artifact and validator, document, raw compliance, M2-04 baseline provenance, durable extension
value attribution, and persisted metadata digests.
An invalid, incomplete, archived/deleted, unavailable, or changed snapshot has no candidate.

The target base is derived without sharing object references with the source:

- Same schema: validate the source under the exact artifact, then deep-copy it. The conversion
  planner is not invoked because it correctly rejects identical source and target artifacts.
- Different schema: invoke the pure planner for that exact direction. Only an applicable plan with
  complete source/target atom coverage, zero blockers, current recipe-registry identity, and valid
  target validation supplies the private converted candidate. A diagnostic or blocked candidate is
  never a persistence candidate, and changing the candidate's schema label is never conversion.

Composition then runs in this fixed order:

1. **Converted source.** Every source atom is already accounted by the same-schema copy or the
   conversion plan. It is authoritative over a starter preset.
2. **Starter preset.** `keep_current` adds nothing. An explicit target-schema preset is resolved
   from its exact catalog/version/definition and may fill only absent RFC 6901 paths. Recursive
   object descent may fill a missing child, but a preset never replaces or removes an existing
   source value. Identical collisions and differing value collisions keep the source and receive
   distinct ledger decisions. An incompatible ancestor/container collision, unaccounted path, or
   invalid preset definition blocks the whole composition.
3. **CIS baseline.** `none` adds no layer. A selected Level 1 or Level 2 resolves one exact
   target-schema layer and the reviewed merge-rule set, then calls the existing deterministic CIS
   merge with the source-plus-preset document as its base. A CIS value may replace a base value only
   when the recorded reviewed rule selects it. Manual-review rules keep the base and are allowed
   only as an explicit `manual-review` CIS result with `current_claim=false`; they can never produce
   `verified`. An unavailable layer, missing rule identity, unaccounted decision, or unsafe merge
   blocks creation.

An exact same-schema carry-forward exists only when the resolved starter/CIS selection matches the
source envelope and composition makes no change. It preserves starter/CIS identities and statuses
without promotion. Any explicit different preset/CIS selection or any cross-schema target is a
recomposition: `keep_current` is never stored as a preset ID, cross-schema preset history is never
inferred from flags, and a current CIS claim requires a new target-bound proof. Source compliance
that is no longer current is accounted as preserved inert evidence or an M2-04 invalidated or
manual-review result; it is never silently discarded or represented as verified.

The recomposed M2-04 envelope is deterministic. An explicit target preset stores its exact target
definition with disposition `recomposed`; `keep_current` outside the exact carry-forward stores
starter `custom-imported` while lineage retains the source provenance digest. Selected CIS `none`
stores `none` with no current claim. A selected catalog layer stores the exact target identity and
is `verified` only with complete target proof and zero review decisions; otherwise its known
identity is `manual-review` with no current claim. None of these results promotes a source state.

## Extension value attribution

M7-07 stores extension value source attribution separately from M2-04 baseline provenance. It is
value-level review metadata only: it never establishes a selected starter identity or a verified
CIS benchmark claim. A same-schema exact carry preserves the source attribution for unchanged
extension values. In a cross-schema duplicate, only a candidate admitted by the existing pairwise
planner can survive; every surviving extension value is labelled `converted`, while unsupported
values remain a planner blocker and create no target. Explicit preset fills are labelled `preset`
and selected CIS-layer values are labelled `cis`. M7-07's migration labels pre-existing extension
values `imported`; editor changes are `manual`, AMO-assisted manual, or `raw` only when the value
changes in that request. These facts are part of the source snapshot/digest and cannot be used to
relabel unchanged source values.

## Decisions, identity, and final validation

The duplicate plan has three ordered, value-safe ledgers. Conversion entries account for every
source atom. Preset decisions account for every resolved preset atom as filled, identical,
source-preserved, or blocked. CIS decisions account for every selected-layer/base outcome using the
existing merge vocabulary, recommendation IDs, merge rule, and review flag. Public planning data
contains pointers, codes, counts, identities, and subtree digests, never policy/compliance values.
Coverage gaps, duplicate target ownership, implicit defaults, silent drops, best-effort coercion,
or an unknown decision code are blockers.

Strict JSON uses RFC 8785 JCS and lowercase SHA-256. The composition digest uses the domain
`bpm096-profile-duplicate-composition:v1\n` and binds the source snapshot; exact source/target
artifacts and validators; conversion plan/registry identity or same-schema marker; resolved preset
and CIS identities; merge-rule identity; all ordered decisions and blockers; target document,
compliance, and provenance digests; and final target-validation result. It excludes clocks,
localized text, request IDs, the future target database ID, and database engine.

After preset and CIS composition, the complete private target document is validated again against
the exact target validator. `valid`, zero blockers, complete ledger coverage, and a matching
validated-document digest are all required. A conversion plan's earlier valid candidate does not
authorize a later preset/CIS result.

## Staleness, revision, and source nonmutation

Read-only planning writes no row and changes no source field or timestamp. Inside the M2-03 write
transaction, M3-05 must lock or conditionally verify the source, resolve every catalog artifact
again, rederive conversion and composition from current bytes, rerun target validation, and compare
the entire composition digest. A changed source revision, lifecycle, schema, document, compliance,
baseline provenance, extension attribution, metadata, schema bundle/validator, recipe registry, preset definition, CIS layer,
merge-rule set, decision ledger, or result is stale. A stale, invalid, blocked, or merely diagnostic
plan inserts zero rows; it cannot be accepted because its final document happens to validate.

Success inserts one complete new profile at `revision = 1`. The source revision does not advance.
Before planning, after planning, after every rejection, and after success, the source's name,
description, schema, flags, raw compliance, baseline provenance, extension attribution, lifecycle, revision, timestamps,
and every other database-managed value are byte/value unchanged. The target owns new identity and
timestamps plus duplicate lineage; no idempotency, plan, ledger, audit, or navigation state is
written to the source.

## Normative compact fixture

<!-- bpm096-profile-duplicate-composition-contract-v1 -->
```json
{
  "contract_id": "bpm096-profile-duplicate-composition",
  "contract_version": 1,
  "status": "planning-only-no-runtime-change",
  "schema_matrix": {
    "artifacts": ["release-153", "esr-153.0", "esr-140.13", "esr-115.39"],
    "same_schema_target_count": 4,
    "same_schema_targets": [
      ["release-153", "release-153"],
      ["esr-153.0", "esr-153.0"],
      ["esr-140.13", "esr-140.13"],
      ["esr-115.39", "esr-115.39"]
    ],
    "directed_cross_schema_pair_count": 12,
    "pair_rule": "all-ordered-non-self-pairs",
    "directed_cross_schema_pairs": [
      ["release-153", "esr-153.0"],
      ["release-153", "esr-140.13"],
      ["release-153", "esr-115.39"],
      ["esr-153.0", "release-153"],
      ["esr-153.0", "esr-140.13"],
      ["esr-153.0", "esr-115.39"],
      ["esr-140.13", "release-153"],
      ["esr-140.13", "esr-153.0"],
      ["esr-140.13", "esr-115.39"],
      ["esr-115.39", "release-153"],
      ["esr-115.39", "esr-153.0"],
      ["esr-115.39", "esr-140.13"]
    ]
  },
  "base_derivation": {
    "same_schema": "validated-private-deep-copy",
    "cross_schema": "current-applicable-pairwise-plan-private-candidate",
    "relabel_without_conversion": "forbidden",
    "blocked_or_diagnostic_candidate_persistable": false,
    "production_recipe_count_at_contract_time": 0
  },
  "precedence": ["converted-source", "absent-path-preset-fill", "reviewed-cis-merge"],
  "preset": {
    "keep_current": "no-fill-and-never-stored-as-preset-id",
    "existing_value_authority": "converted-source",
    "allowed_decisions": [
      "filled-absent",
      "source-identical",
      "source-preserved",
      "blocked-structural-collision",
      "blocked-invalid-preset-path"
    ],
    "overwrite_or_remove_source_value": "forbidden",
    "every_resolved_atom_accounted": true
  },
  "cis": {
    "none": "no-layer",
    "selected_layer": "exact-target-schema-layer",
    "merge_owner": "app.compliance.firefox.cis.merge.merge_base_with_cis_layer",
    "allowed_decisions": [
      "added_from_cis",
      "kept_base_only",
      "already_satisfied",
      "cis_replaced_base",
      "kept_base_stricter",
      "manual_review_kept_base"
    ],
    "cis_replacement_requires_reviewed_rule": true,
    "manual_review_current_claim": false,
    "verified_requires_target_proof_and_zero_review": true,
    "every_layer_and_base_outcome_accounted": true
  },
  "baseline_provenance": {
    "same_schema_exact_carry": "preserve-identities-and-statuses-without-promotion",
    "explicit_preset_starter": "exact-target-catalog-identity-recomposed",
    "keep_current_recomposed_starter": "custom-imported-with-source-lineage-digest",
    "cis_none": "none-with-current-claim-false",
    "cis_catalog_verified": "target-proof-and-zero-review-only",
    "cis_catalog_review": "manual-review-with-current-claim-false",
    "source_compliance_evidence": "preserved-and-never-live-without-target-proof"
  },
  "extension_provenance": {
    "storage": "separate-value-level-review-metadata",
    "same_schema_unchanged": "preserve-source-attribution",
    "cross_schema_supported": "converted-only-after-applicable-pairwise-plan",
    "cross_schema_unsupported": "block-with-zero-target-writes",
    "preset_fill": "preset",
    "cis_selected_layer": "cis",
    "legacy_migration": "imported-without-historical-inference"
  },
  "certificate_provenance": {
    "storage": "separate-value-level-review-metadata",
    "baseline_provenance": "never-modified-by-attribution",
    "same_schema_unchanged": "preserve-source-attribution",
    "cross_schema_supported": "converted-only-after-applicable-pairwise-plan",
    "cross_schema_unsupported": "block-with-zero-target-writes",
    "preset_fill": "baseline",
    "cis_selected_layer": "cis-with-review-visible-without-benchmark-promotion",
    "legacy_migration": "imported-without-historical-inference"
  },
  "identity": {
    "canonicalization": "RFC-8785-JCS",
    "digest": "sha256-lowercase-hex",
    "composition_domain": "bpm096-profile-duplicate-composition:v1\n",
    "binds": [
      "source-snapshot",
      "source-target-artifacts-and-validators",
      "conversion-plan-and-recipe-registry-or-same-schema-marker",
      "preset-definition",
      "cis-layer-and-merge-rules",
      "ordered-decision-ledgers-and-blockers",
      "target-document-compliance-and-provenance",
      "final-target-validation"
    ]
  },
  "acceptance": {
    "source_must_validate": true,
    "cross_schema_plan_applicable": true,
    "cross_schema_plan_blockers": 0,
    "final_target_validation": "valid",
    "final_blockers": 0,
    "ledger_coverage": "complete",
    "stale_plan_creation": "forbidden",
    "invalid_plan_creation": "forbidden"
  },
  "revision": {
    "target_initial_revision": 1,
    "source_revision_increment": 0
  },
  "source_nonmutation": {
    "applies_to": ["planning", "rejection", "success"],
    "unchanged_fields": [
      "name",
      "description",
      "schema_version",
      "flags",
      "compliance",
      "baseline_provenance",
      "extension_provenance",
      "certificate_provenance",
      "lifecycle",
      "revision",
      "created_at",
      "updated_at",
      "deleted_at"
    ],
    "source_writes": 0
  },
  "future_owners": {
    "read_only_plan": "BPM096-M3-03",
    "atomic_duplicate": "BPM096-M3-05",
    "api": "BPM096-M3-06",
    "ui": "BPM096-M4-04"
  }
}
```

## Delivery boundary

M3 must add behavior tests for same-schema composition, every ordered cross-schema pair, all
preset/CIS choices, digest drift, revision races, target validation, rollback, and byte-for-byte
source snapshots on SQLite and PostgreSQL. M4 may render only the resulting value-safe state. This
planning fixture is executable architecture evidence; it is not an M3 API or M4 UI implementation.
