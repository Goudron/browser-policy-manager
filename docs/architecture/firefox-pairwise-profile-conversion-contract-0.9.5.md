# Firefox Pairwise Profile Conversion Contract (BPM 0.9.5.1)

Status: active M4-06 directed-matrix contract. The deterministic planner,
bounded registry, read-only preview API, atomic apply API, and repeatable
four-channel matrix gate are implemented.

## Purpose, authority, and non-implementation boundary

This contract defines one fail-closed conversion operation for Firefox policy
profiles. BPM095-M4-01 implements its pure planner, BPM095-M4-02 implements
its bounded recipe registry, M4-03 implements the read-only preview API, and
M4-04 implements the atomic conversion writer. M4-06 proves all current
directed pairs through the owner gate. No UI or migration consumer exists yet.
Its machine-readable companion is
[`firefox-pairwise-profile-conversion-contract-0.9.5.json`](firefox-pairwise-profile-conversion-contract-0.9.5.json).
The reusable plan, apply-request, result, and error shapes are Draft 2020-12
JSON Schema definitions in
[`schemas/firefox-profile-conversion-contract-v1.schema.json`](schemas/firefox-profile-conversion-contract-v1.schema.json).
The fixture and schema are normative; examples are contract vectors, not claims
that the routes or conversions are currently implemented.

The lifecycle identities and supported-state meaning come only from the
[`firefox-schema-lifecycle-catalog-contract-0.9.5.json`](firefox-schema-lifecycle-catalog-contract-0.9.5.json)
fixture. Source provenance comes from the reviewed four-channel matrix. A
converter must not infer a line, patch, schema, source tag, support state,
recommendation, or successor from a label, tuple position, filename, or version
maximum.

This M2-04 contract changes no profile row, generated policy schema,
CIS layer, OpenAPI document, locale, or migration. M2-05 separately owns the
retirement gate. M3 promotes independently generated artifacts. M4 implements
the domain/API boundary, and M5 owns UI and localization.

## The no-silent-loss invariant

For a structurally valid source `{"policies": Profile.flags}`, conversion
builds a complete set of **source atoms**. An atom is each scalar JSON leaf and
each empty object or array. Non-empty containers are accounted by their child
atoms. Object member names, including dynamic dictionary keys, are preserved
in RFC 6901 pointers; array indexes are explicit pointer segments. Thus a
non-empty nested policy, an empty allowlist, an empty dynamic dictionary, and
every array element are all visible to coverage checking.

Every source atom is covered exactly once by one non-overlapping plan entry,
and every candidate-target atom is produced and covered exactly once. An entry
has exactly one classification:

| Classification | Permitted meaning |
| --- | --- |
| `unchanged` / `byte-identical` | Path and canonical JSON subtree bytes are identical. |
| `unchanged` / `semantic-equivalent` | Path and canonical value are identical, and reviewed evidence proves the exact source and target schema artifacts interpret it equivalently. |
| `transformed` | One exact, versioned registry recipe deterministically maps the declared source atoms to target atoms and supplies reversibility or reviewed semantic-equivalence evidence. |
| `blocked` | BPM cannot prove one of the preceding outcomes. The source atoms remain present in the diagnostic candidate but the plan is not applicable. |

There is deliberately no `drop`, `best-effort`, `implicit-default`,
`implicit-coercion`, truthy/falsey normalization, numeric/string conversion,
case normalization, unknown-key removal, or first-matching-recipe class. A
target schema default is never materialized merely because it exists. A policy
accepted by both schemas is not automatically semantically unchanged: exact
cross-artifact evidence is still required. An empty document has zero source
atoms, zero entries, and still receives target validation.

Plan entries sort by the UTF-8 bytes of their first source pointer, then all
source pointers, target pointers, classification, and recipe identity.
Pointers use RFC 6901 escaping. Source object declaration order, registry
declaration order, lifecycle-catalog declaration order, locale, process, clock,
and database engine cannot affect coverage, entry identity, output bytes, or
plan identity. Object traversal follows canonical member ordering; arrays
retain their semantic order.

`entry_id` is SHA-256 over the UTF-8 domain
`bpm-profile-conversion-entry:v1\n` followed by JCS of `source_paths`,
`target_paths`, `classification`, and the recipe identity or `null`. Entries
contain subtree digests, types through schema evidence, paths, and reason codes,
but never raw source or target policy values.

## Stable identities and canonical serialization

All domain objects are strict JSON/I-JSON: duplicate object keys, non-finite
numbers, or values that cannot be represented by RFC 8785 are invalid-source
preconditions, not coercion opportunities. Canonical JSON is RFC 8785 JCS and
digests are lowercase SHA-256 hex.

The following identities have distinct meanings:

| Identity | Canonical input |
| --- | --- |
| Source document | `SHA-256("bpm-policy-document:v1\n" || JCS({"policies": flags}))`. |
| Compliance | `SHA-256("bpm-profile-compliance:v1\n" || JCS(compliance))`; JSON `null` has a real digest. |
| Profile metadata | The metadata-domain digest binds exact `name`, `description`, `created_at`, `updated_at`, and `deleted_at`. Profile `id`, `revision`, lifecycle, channel, flags, and compliance are separately explicit. |
| Schema bundle | SHA-256 of exact checked-in bundle bytes. |
| Validation schema | SHA-256 of JCS after the loader's documented deterministic normalization. This prevents a loader change from masquerading as the same validator. |
| Artifact | Stable `line_id` plus exact `artifact_id`/`channel_id`, artifact version, source tag, bundle digest, and validation-schema digest. |
| Recipe registry | Immutable positive registry version plus content digest; each used recipe also supplies immutable version, definition digest, and evidence digest. |
| Plan | The plan-domain digest over the fixture's complete listed projection, excluding only the digest itself, clocks, localization, and raw values. |

Plan arrays have contract-defined stable order: entries as above; recipes by
`recipe_id` then version; diagnostics by code, policy ID, and pointers. The
canonical plan contains source and candidate document digests, compliance and
metadata digests, exact artifact/schema identities, registry identity,
compatibility counts, entries, target validation, compliance disposition,
warnings, and blockers. Any meaningful replan changes the digest. Preview time,
localized copy, request ID, database engine, and UI display order cannot change
it.

The apply request repeats the source/target line and artifact IDs, an explicit
duplicate `target_artifact_id`, expected revision, plan digest,
document/compliance/metadata digests, both normalized validation schema
digests, and registry version/digest. It never submits a caller-authored target
document. This prevents an apply caller from replacing the reviewed plan with
different policy bytes.

## Plan and target validation

Preview first verifies that the profile is active, the exact stored source and
requested target are distinct supported/selectable catalog artifacts, both
bundles exist with the expected identities, and the source document validates
against the exact source artifact. A failed precondition returns the stable
error envelope and no plan.

For a valid source, the planner always constructs a deterministic diagnostic
candidate. A blocked atom is copied unchanged at its original path in that
candidate solely so target validation can expose exact incompatibility; this
does not authorize persistence. Every valid-source preview runs the target
validator, including blocked previews. `not-run-precondition-failed` exists
only for internal result composition before a public plan is returned. An
invalid candidate adds locale-neutral blockers and makes `applicable=false`.
A valid target alone cannot override a missing equivalence or recipe proof.

Compatibility summaries are derived, never separately authored:

- `compatible-unchanged`: no transformed/blocked entries and valid target;
- `compatible-transformed`: at least one approved transformation, no blockers,
  and valid target; or
- `blocked`: at least one blocker or an invalid target.

Counts equal the actual atom coverage, classifications, warnings, and blockers.
The stable schema intentionally carries no human message. Representative
entry/diagnostic codes include `policy_byte_identical`,
`policy_semantic_equivalence_verified`, `lossless_transformation_applied`,
`target_policy_unsupported`, `target_value_invalid`,
`semantic_equivalence_unproven`, `transform_recipe_missing`,
`transform_predicate_mismatch`, `transform_output_invalid`,
`transform_lossless_evidence_missing`, and `dynamic_key_unaccounted`.
Unknown codes require a contract-version change when they alter handling.

## Deterministic transformation registry

A recipe is immutable once its `(recipe_id, recipe_version,
definition_digest)` is published. A behavioral change creates a new version
and registry digest. A recipe declares exact predicates for source and target
stable lines, exact artifact IDs, both normalized schema digests, RFC 6901
source path pattern, and accepted JSON shape. Broad version ranges, a family-
only match, or an omitted schema digest are not sufficient.

Selection is set-based and declaration-order independent. Exactly one recipe
must match every transformed group. Zero matches blocks with
`transform_recipe_missing`; more than one blocks with
`transform_recipe_ambiguous`. There is no priority or first-match behavior.

Recipes are pure and total on their reviewed input domain. They cannot read the
network, clock, locale, database, environment, catalog order, or mutable global
state. They deep-copy source input and cannot mutate a previewed profile. They
declare all consumed source atoms and all produced target atoms, including
nested/dynamic dictionary keys and empty containers. New target atoms are legal
only when explicitly produced by the recipe, never as an implicit schema
default.

Every recipe has either an executable inverse with round-trip fixtures or a
reviewed semantic-equivalence proof explaining why byte reversal is not the
right criterion. Evidence binds exact source/target schema and recipe digests.
The output is canonicalizable strict JSON and must validate under the exact
target schema. Any predicate, evidence, coverage, or validation failure is a
blocker. M2-04 approves no production transformation recipe. M4-02 therefore
ships an active, explicitly empty production registry with a machine-reviewed
`no-production-recipe-after-four-channel-diff-audit` disposition. It is not an
implicit identity registry: exact channel/schema/path recipe lookup, predicate
miss, transform exception, output/round-trip failure, and candidate coverage
failure each fail closed with a stable blocker while target validation still
runs. Synthetic exact-schema vectors prove the bounded mechanism; they are not
Mozilla production evidence. A future production recipe must satisfy this
contract before M4 can classify an entry as `transformed`.

## Compliance disposition without false CIS claims

Today `Profile.compliance` is `dict | None`, not a versioned or channel-bound
schema. Stored examples include legacy arbitrary objects, while the current
wizard can emit `layer`, benchmark identity/version/name, summary, decisions,
and user exception notes. Generated CIS layers are explicitly channel-bound.
Therefore copying a non-null object across artifacts and continuing to display
it as current would be a false claim.

Every plan chooses exactly one disposition:

| Disposition | Rule |
| --- | --- |
| `absent` | Source is JSON `null`; target remains `null`. |
| `preserved-verified` | A recognized versioned envelope and exact target CIS artifact prove every claim/decision remains true for the final target document; every JSON leaf is accounted. |
| `recomputed` | A recognized envelope, exact target CIS artifact, and deterministic auditor recompute metadata from the final target document without changing policies. User notes/exceptions are mapped and accounted; an unmappable leaf prevents this disposition. |
| `invalidated-preserved` | Mandatory fallback for any other non-null object. It removes current-claim status while preserving the complete original JSON as evidence. |

The deterministic invalidation value is exactly a versioned object containing
`schema_version: 1`, `status: "invalidated"`, a locale-neutral `reason_code`,
source and target exact artifact IDs, the source compliance digest,
`current_claims: false`, and a deep-copy `preserved_source`. The original object
must never remain at the top level where existing consumers could interpret it
as live CIS status. Repeated conversion may wrap the preceding envelope; it may
not discard its preserved evidence.

Recomputation is an audit of the converted document, not permission to add CIS
policies. Its target CIS artifact digest is in the plan/result. Until a target
CIS artifact and auditor exist, the truthful outcome is invalidation, not
retaining source claims. `compliance_invalidated`, `compliance_recomputed`, and
`compliance_preservation_verified` are warnings because the policy plan can
remain applicable, but their full source leaf coverage is mandatory. Failure
to preserve user-authored notes or opaque metadata is a blocker, never cleanup.

## Read-only preview and atomic apply

Preview is read-only at every layer: no ORM assignment, flush, commit,
timestamp touch, compliance rewrite, validator cache mutation with externally
observable state, or audit record that contains profile data. Multiple previews
of the same canonical state and owned artifacts return the same plan digest.

Apply accepts only the versioned apply-request shape. In one transaction it:

1. reads/locks the active profile and compares the exact expected revision;
2. rechecks stored source, target support, stable/exact identities, bundle and
   normalized schema identities, document/compliance/metadata identities, and
   registry identity;
3. rederives the complete plan from current bytes and compares its digest;
4. reruns exact source and target validation and rejects any blocker;
5. assigns only `schema_version`, the fully accounted `flags`, the disposition-
   owned `compliance`, and `revision = source_revision + 1`; and
6. flushes/commits once and returns the versioned result.

The normal ORM/database update mechanism owns `updated_at`; it is never client
input. The result truthfully reports whether its stored value changed (database
timestamp precision can make equal values observable). `id`, `name`,
`name_casefold`, `description`, `created_at`, and `deleted_at` are byte/value
preserved. `is_deleted` and `validation_state` remain derived read fields. A
successful manual apply is active before and after and increments revision
exactly once, even if all policy values are unchanged. No separate profile is
created.

Unknown/unsupported/identical target, unknown/retired/deleted/invalid source,
missing schema, blocked replan, stale revision, stale document/compliance/
metadata or plan digest, stale schema identity, stale registry/recipe identity,
validation error, transaction error, cancellation before commit, and retry of
an already consumed request all leave every profile field and timestamp
unchanged. The fixture gives stable HTTP status/code mappings. Failure returns
`mutation: "none"`; a stale identity requires a new preview. A blocked preview
is a successful read (`200`) with `applicable=false`, but applying it returns
`409 conversion_plan_blocked`.

## All ordered pairs and the ESR 115 promotion boundary

For the four lifecycle rows, the permanent requirement is all
`4 × (4 - 1) = 12` ordered pairs. The machine fixture lists each pair exactly
once and excludes self-pairs. Direction matters: evidence for A to B proves
nothing about B to A, even when schemas currently share a Mozilla source.

M3 independently provisioned all four artifacts, so all 12 directions are
current planner inputs. M4-01/M4-02 supply structural no-silent-loss planning,
exact validation, and an active empty immutable recipe registry in production;
any difference that needs a recipe remains blocked. M4-03 owns the read-only
API and M4-04 owns atomic apply. M4-06 is complete: run
`make verify-firefox-conversion-matrix` to prove every canonical pair has
empty and shared nested/dynamic/array positive previews, an invalid-source
negative, and either a real source-only/enum blocker or an exact pair-bound
precondition. The gate also proves API `available=true`, target validation for
every valid-source preview (including blockers), source-profile immutability,
repeatability, server rederivation, one-step apply revision, replay staleness,
and plan/source/registry identity rejection.

The command is offline and prints `phase=... pair=source->target [n/12]` plus
a terminal status. It uses one disposable in-memory SQLite fixture for API
proofs and disposes it after verification; it never writes a product profile.
Its optional deterministic JSON report contains only pair/channel identities,
counts, stable codes, and digests—never raw policy, metadata, compliance, or
localized values. Immutable parsed schemas and validators are bounded to one
load/cache entry per exact current channel. Production transformation count is
explicitly zero; a separate synthetic reversible recipe scenario tests only
the registry mechanism and is not a Firefox production conversion.

## Manual conversion is not retirement migration

Manual conversion is an explicit, previewed user operation between any two
distinct supported/selectable exact artifacts. It never follows a
recommendation automatically and cannot target a retired or merely planned
artifact.

A retirement migration is a separate Alembic-owned consumer. It is restricted
to the lifecycle catalog's immediate newer ESR successor, uses immutable
migration-owned schema/recipe data, and requires the total-convertibility,
backup, interruption, and two-database gate that M2-05 will define. It cannot
call an HTTP apply route or rely on a mutable runtime registry. Sharing the
classification vocabulary and canonical proof format does not authorize a
migration. Nothing in M2-04 declares a line retired or proves a retirement
transition safe.

## API, OpenAPI, UI, localization, and privacy

M4 is to add versioned preview/apply operations and component schemas without
removing current profile fields or changing `ProfileRead`. Existing create and
Firefox import operations continue to select a schema for new data and are not
conversions. Once the conversion API ships, direct `PATCH` changes of
`schema_version` for an existing profile with policy/compliance data must be
deprecated in OpenAPI and rejected with
`profile_schema_conversion_required`; allowing PATCH to bypass preview would
defeat this contract. The response `schema_version` field is not deprecated.
Adding an optional response field is additive; changing required fields, digest
projection, enum handling, or apply semantics requires contract version 2 and a
documented overlap/deprecation window.

Import remains the only boundary that unwraps a new external
`{"policies": {...}}` document into `Profile.flags`; conversion never reparses
or weakens import validation. Export continues to wrap only the currently
persisted flags, so preview cannot change exported bytes and successful apply
exports only the target-validated result. Compare remains read-only and may
link to preview but cannot apply. An editor with unsaved work must require an
explicit save/discard/cancel decision before preview/apply; a conversion cannot
overwrite browser-local edits, and any intervening save makes the preview
revision/digest stale.

Codes, pointer paths, counts, identities, and parameters are locale-neutral.
Lifecycle failures retain M2-03's shared `schema_channel_unknown`,
`schema_channel_retired`, and `schema_channel_retired_requires_migration`
codes; conversion-specific failures use the `conversion_...` namespace.
M5 owns presentation in the existing Library/editor surfaces and must block
confirmation when `applicable=false`. M2-06/M5-04 own English source copy and
the complete `ru`, `de`, `zh-CN`, `fr`, and `es-ES` UI localization. API/server
code never receives localized reason text back from a client and never hashes
localized text.

Policy values, dynamic keys, paths, profile names/descriptions, compliance
objects, exception notes, and even policy presence can be sensitive enterprise
configuration. Plan/result/error payloads omit raw values; paths and policy IDs
are returned only to a caller already authorized to read that profile. They
must not enter URLs, analytics, metrics labels, client storage, or DOM data
attributes. Logs contain only operation outcome code, pair IDs, aggregate
counts, and a request correlation ID: no raw values, names, descriptions,
pointers, policy IDs, compliance data/notes, full document/plan digests, or
serialized request/response bodies. Debug logging cannot weaken this boundary.

## Sol-level cross-system decisions

This contract intentionally resolves the high-risk cross-system questions at
the architecture boundary:

1. **Atomic unit is the complete profile, not only `flags`.** Profile metadata,
   lifecycle, compliance, timestamps, channel, and revision are all accounted,
   preventing a policy-safe conversion from corrupting concurrency or claims.
2. **Exact schema bytes and normalized validator identity are both bound.**
   This closes the gap where generated input is unchanged but loader behavior
   silently changes validation semantics.
3. **Semantic sameness requires evidence.** Shared v8.0 provenance for Release
   153 and ESR 153 does not, by itself, prove browser-channel semantics.
4. **Opaque compliance is invalidated while preserved.** This is the only
   current-model option that avoids both data loss and a false live CIS claim.
5. **Apply rederives instead of trusting preview output.** This joins API/UI
   confirmation, optimistic revision, schema updates, recipes, and database
   atomicity under one stale-state rule.
6. **All 12 directions are structurally planned after M3 promotion.** This
   proves the current artifact matrix without pretending that an empty registry
   supplies reviewed transformations or that a domain plan can write a profile.
7. **Manual and retirement consumers share proof language, not authority.**
   This prevents a user-facing converter from becoming an unreviewed migration
   mechanism.

These decisions are stricter than the current free-form DTO/storage surface on
purpose. A later implementation may add evidence and supported transformations;
it may not introduce a silent-loss escape hatch.

## Executable acceptance contract

The focused test validates strict JSON and Draft 2020-12 shapes, current
artifact/schema hashes in the example, canonical plan identity, complete
directed-pair coverage, declaration-order independence, ESR 115's planned-only
state, classifications, nested/dynamic atom coverage, target atom coverage,
registry evidence, metadata/compliance accounting, result/revision rules, and
nonmutation failure semantics. Mutation cases remove or duplicate atoms, add a
forbidden `drop` class, omit recipe/evidence, alter target validation, stale the
plan digest, weaken profile/compliance field coverage, and change failure
mutation to prove the contract fails closed.

M4/M5/M6 must add behavior tests; satisfying this documentation fixture alone
does not prove a runtime converter, API, UI, or migration safe.
