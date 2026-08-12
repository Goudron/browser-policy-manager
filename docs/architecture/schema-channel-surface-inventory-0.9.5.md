# BPM 0.9.5 Current Schema-Channel Surface Inventory

Status: active architecture inventory
Scope: current BPM095 ownership after M7-04. This inventory names maintained
entrypoints and their smallest useful proof; it is not product documentation,
a generated-artifact inventory, or authorization to retire a supported ESR.

## Current lifecycle matrix

The runtime catalog has four independently generated, supported artifacts:
`release-153`, `esr-153.0`, `esr-140.13`, and `esr-115.38`. Lifecycle roles,
not tuple order, labels, defaults, or aliases, determine product default
(ESR 153.0), latest ESR (ESR 153.0), older-ESR recommendations (ESR 115.38
and ESR 140.13 to ESR 153.0), and prospective immediate retirement successors
(ESR 115 to ESR 140; ESR 140 to ESR 153). An older supported ESR is selectable
and is never moved at runtime.

The exact normative lifecycle input is
[`firefox-schema-lifecycle-catalog-contract-0.9.5.json`](firefox-schema-lifecycle-catalog-contract-0.9.5.json).
The paired human contract explains the fail-closed rules. A future candidate
can retire an ESR only through a reviewed previous/candidate lifecycle diff,
an exact total-convertibility proof, backup/preflight gates, and an immutable
Alembic revision; the current ESR 140 row remains supported.

## Current owners and focused routes

| Concern | Smallest maintained owner | Focused proof |
| --- | --- | --- |
| Lifecycle catalog and schema loading | `app/core/schema_channels.py`, `app/core/schemas_loader.py` | `tests/unit/schema/contracts/test_schema_channels.py`; `tests/contract/docs/schema/test_firefox_schema_lifecycle_catalog_contract.py` |
| Independent source/provenance and bundle reproduction | `tools/firefox_schema_targets.json`, `tools/firefox_schema_inputs_manifest_0_9_4.json`, `tools/provision_firefox_schema_inputs.py`, `tools/convert_policies_from_upstream_lib/` | `make test-firefox-schema-workflow`; `tests/unit/tooling/test_provision_firefox_schema_inputs.py` |
| Schema-matrix drift guard | `tools/verify_firefox_schema_matrix.py` | `make verify-firefox-schema-matrix`; `tests/unit/tooling/test_verify_firefox_schema_matrix.py` |
| Manual pairwise conversion | `app/core/profile_conversion_planner.py`, `app/core/profile_conversion_recipes.py`, `app/api/profiles.py` | `tests/unit/schema/general/test_profile_conversion_planner.py`; `tests/integration/api/test_profile_conversion_preview_api.py`; `tests/integration/api/test_profile_conversion_apply_api.py` |
| Conversion-matrix evidence | `tools/verify_firefox_conversion_matrix.py` | `make verify-firefox-conversion-matrix`; `tests/unit/tooling/test_verify_firefox_conversion_matrix.py` |
| Recommendation and conversion UI | `app/static/profiles_modules/conversion_recommendation.mjs`, `app/static/profiles_modules/conversion_review.mjs` | `tests/javascript/integration/profiles/profile_conversion_review.test.js`; `tests/browser/profiles/test_schema_conversion_ux.py` |
| Lifecycle transition and retirement proof | `app/core/lifecycle_transition_plan.py`, `app/core/retirement_convertibility_preflight.py` | `tests/unit/schema/contracts/test_lifecycle_transition_plan.py`; `tests/unit/schema/contracts/test_retirement_convertibility_preflight.py`; `tests/contract/docs/schema/test_firefox_retirement_total_proof.py` |
| Candidate lifecycle review | `tools/schema_lifecycle_dry_run.py` | `make schema-lifecycle-dry-run` with explicit reviewed snapshots; `tests/unit/tooling/test_schema_lifecycle_dry_run.py` |
| Retired-ESR migration | `migration_support/retirement_owner_v1.py`, `migration_support/retirement_revision_materializer_v1.py` | `tests/integration/db/test_retirement_owner_v1.py`; `tests/integration/db/test_retirement_revision_materializer_v1.py`; `make test-postgres-integration` for an actual retirement candidate |
| CIS, locale, and help-derived consumers | `app/compliance/firefox/cis/`, `app/i18n_src/`, `documentation/config/` | `tests/contract/compliance/test_cis_firefox_generation.py`; `make check-locale-catalogs`; `make docs-validate` |
| Deterministic Firefox live matrix | `tools/firefox_live_browsers_manifest_0_9_4.json`, `tools/provision_firefox_live_browsers.py`, `tools/run_firefox_live_workflow.py` | `make firefox-live-four-channel-workflow`; `tests/unit/firefox/test_live_firefox_provisioning.py`; `tests/unit/firefox/test_live_workflow_runner.py` |

## Boundaries

- Bundled schemas, generated CIS layers, runtime locale catalogs, CSS, and
  profile bundles are derived outputs. Change their source owner and run its
  rebuild/check command; do not hand-edit those outputs.
- The conversion planner is a read-only manual-preview path. It never proves
  retirement and does not write a profile. Apply rederives the digest-bound
  plan in the API-owned transaction.
- The lifecycle planner and total-proof preflight are value-free and have no
  database, API, service, or runtime-normalization dependency.
- `migration_support/` is offline-only and not imported by startup, API,
  services, or UI. Its ESR 140 to ESR 153 materializer is candidate-only while
  ESR 140 remains supported; no retirement revision is installed at the active
  Alembic head.
- Live-browser pins are separate Firefox binaries per channel. Browser version,
  policy-template tag, schema provenance, and live evidence are distinct facts.

For release sequencing and all cross-cutting gates, use
[`../firefox-schema-update-runbook.md`](../firefox-schema-update-runbook.md).
