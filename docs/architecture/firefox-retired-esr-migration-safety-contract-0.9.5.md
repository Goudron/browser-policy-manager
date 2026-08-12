# Firefox Retired-ESR Migration Safety Contract (BPM 0.9.5)

Status: active normative contract; M6-01 through the fail-closed M6-03 owner are implemented.

## Purpose, authority, and non-implementation boundary

This contract defines the fail-closed release gate for removing a Firefox ESR
line from BPM support and moving every stored profile on that exact retired
artifact to one reviewed successor. Its machine-readable companion is
[`firefox-retired-esr-migration-safety-contract-0.9.5.json`](firefox-retired-esr-migration-safety-contract-0.9.5.json),
validated by
[`schemas/firefox-retired-esr-migration-contract-v1.schema.json`](schemas/firefox-retired-esr-migration-contract-v1.schema.json).
The JSON fixture and schema are normative. Examples are contract vectors, not
an implemented retirement or a statement that any current ESR transition is
safe.

## M6-01 implemented planning boundary

`app/core/lifecycle_transition_plan.py` now implements only the first two
non-mutating gates: previous/candidate catalog diff and declared immediate
successor validation. Its input is explicit `SchemaChannel` snapshots plus the
reviewed set of bundled exact artifacts; its deterministic value-free output
contains added, retained, refreshed, and retired stable lines, same-line patch
refresh mappings, and retirement source-to-successor mappings. It rejects
missing, cyclic, ambiguous, cross-family, non-newer, skipped-intermediate,
unsupported, unselectable, and unbundled successor targets before any proof or
database path can start.

The module has no database, service, API, conversion-planner, or runtime
normalization dependency. It neither proves total convertibility nor writes a
profile; those remain M6-02 and the later Alembic-only M6-03 boundary.

## M6-02 implemented static-proof boundary

`app/core/retirement_convertibility_preflight.py` now consumes only an already
valid M6-01 `LifecycleTransitionPlan`, explicit exact bundle bindings, reviewed
semantic-containment evidence, and the immutable M4 recipe registry. It never
opens a database, reads a profile, invokes the conversion API, creates an
Alembic revision, or writes any state.

For unchanged domains it requires both local structural source-to-target
validation containment and one exact artifact/digest-bound semantic evidence
record. For a transformed domain it accepts only finite `const`/`enum` source
sets, executes every permitted value through the one exact M4 recipe, verifies
its predicate, inverse, target constraint, and target schema, and rejects any
missing, stale, non-exhaustive, ambiguous, or invalid binding. This is an
exhaustive domain check, not a sample fixture. Other JSON Schema domains remain
uncovered until reviewed containment evidence is supplied; the gate deliberately
does not infer semantic equivalence from matching policy IDs or default values.

The output is deterministic and value-free. It binds raw-bundle SHA-256 and
normalized-validator JCS SHA-256 for both ends, registry identity, source and
successor exact artifacts, proof/result digest, and every uncovered source
schema/atom RFC 6901 pointer. An incomplete outcome has stable blocker
`retirement_total_convertibility_unproven` and `mutation: none` before any
database preflight could start.

The current required ESR 140.13 to ESR 153.0 mapping has one complete,
checked-in production exact-artifact containment proof:
[`firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json`](firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json).
It binds both current raw bundles and normalized validators, the empty reviewed
M4 registry, all 112 source policy identifiers, reviewed upstream documents,
and the semantic identity conclusion. The checker mechanically confirms that
109 policy validation projections are identical and that the `Cookies`,
`ExtensionSettings`, and `Homepage` differences only widen target acceptance.
The resulting M6-02 report is promotable with zero uncovered locations. The
synthetic ESR 115 to ESR 140 vector continues to prove the generic mechanism
only; it cannot promote a production catalog or name an Alembic revision.

## M6-03 implemented owner and candidate-only materializer

`migration_support/retirement_owner_v1.py` is the versioned, offline-only
migration owner. It is deliberately outside `app`, is not imported by startup,
services, API, or UI, and never reads the mutable runtime catalog or calls the
manual conversion API. Production admission requires one digest-valid manifest
with evidence scope `production-exact-artifacts` and the exact complete M6-02
report: source/target bundle and validator identities, recipe registry, proof,
successor, supported-line set, and source/target Alembic revisions must agree.
Synthetic contract admission is separate and cannot enter the production
Alembic adapter.

The owner provides a read-only database preflight bound to a verified native
backup/restore, exact source stamp and current profile shape. It derives every
affected active or archived row plan in memory, validates source and target
through migration-owned code, and persists only aggregate counts and a
domain-separated row-set digest. The production adapter runs inside Alembic's
outer transaction: it obtains `BEGIN IMMEDIATE` before the first SQLite read or
an exclusive `profiles` lock on PostgreSQL, rechecks the full preflight under
that lock, changes only channel, flags, compliance, revision and one
database-derived transaction timestamp, then returns so Alembic owns its normal
stamp and commit. Any exception is propagated for whole-revision rollback;
downgrade raises `retirement_downgrade_unsupported`.

The disposable synthetic contour emulates Alembic's stamp in that same
transaction and proves rollback after the first affected row, preserved
unaffected fields/rows, archived-row inclusion, terminal no-op idempotency, and
privacy-safe count progress. It is mechanism evidence only.

`migration_support/retirement_revision_materializer_v1.py` now freezes the
complete exact ESR 140.13 to ESR 153.0 report and renders a deterministic
Alembic-compatible candidate artifact only after the previous/candidate
catalogs, proof, schemas, registry, manifest and revision IDs all bind. It
deliberately rejects the active catalog because ESR 140.13 is still supported.
The artifact has passed the real Alembic path on a disposable, natively backed
up and restore-checked SQLite candidate, but is not installed in the active
revision graph. PostgreSQL execution and release activation remain pending.

## Migration observability and recovery evidence

The migration-only observation projection has version `1`. Every event has a
phase, exact source/target line and artifact identity, aggregate profile,
affected-source, already-target, transformed, and unchanged counts, transaction
result, verified backup/restore identities, failure boundary/code, and recovery
direction. It emits no profile identifier/name/description, policy ID/value or
JSON pointer, compliance content, document/row-plan digest, database URL, or
exception message.

`transformed_count` and `unchanged_count` are deliberately `null` while a
transaction is open; `processed_in_open_transaction` is the only live progress
number. A committed event alone reports final transformed/unchanged totals. A
rollback reports zero transformed rows and directs recovery to restoring the
verified backup into a **new clean candidate**, never an in-place retry. The
Alembic adapter can only report `pending-alembic-stamp` until its outer stamp
and commit finish, so it likewise cannot claim a partial success.

An incomplete static total-convertibility report produces a deterministic
`static-gate` block before any database connection or backup requirement. It
lists only blocked source/target artifact mappings and safe blocker codes, with
the recovery direction `complete-schema-wide-proof-before-retirement`.

No production revision is present in `alembic/versions/`, and the BPM 0.9.5
head remains `20260804_add_profile_name_casefold`. The exact ESR 140.13 to ESR
153.0 M6-02 report and candidate-only materializer are complete. This permits a
reviewed retired candidate to render an inert revision artifact; it does
**not** retire the active catalog row or authorize a current runtime profile
write. Installing that artifact requires coordinated candidate-catalog
promotion, active graph/matrix updates, verified backup evidence and the real
PostgreSQL contour.

Stable lines, exact artifacts, support state, and prospective successor edges
come from the active
[`firefox-schema-lifecycle-catalog-contract-0.9.5.json`](firefox-schema-lifecycle-catalog-contract-0.9.5.json).
Policy atom accounting, transformation evidence, artifact identity, compliance
dispositions, profile fields, and revision semantics come from the active
[`firefox-pairwise-profile-conversion-contract-0.9.5.json`](firefox-pairwise-profile-conversion-contract-0.9.5.json).
Native backup, restored-candidate recovery, two-engine evidence, and the
unsupported-downgrade boundary extend the active
[`database-upgrade-matrix-0.9.4.json`](database-upgrade-matrix-0.9.4.json)
contract.

M2-05 creates no runtime converter, API, UI, catalog implementation, schema
bundle, recipe, backup tool, or Alembic revision. M6 owns implementation and
must promote its immutable production evidence through this contract.

## Non-negotiable retirement gate

An ESR line can leave the supported matrix only in this order:

1. Diff the reviewed previous and candidate lifecycle catalogs.
2. Validate one explicit immediate newer supported ESR successor.
3. Bind exact source and target bundles and normalized validation schemas.
4. Complete a source-schema-wide, lossless conversion proof.
5. freeze and review one immutable transition manifest;
6. create the one versioned Alembic revision that embeds or checksum-binds all
   migration-owned conversion inputs;
7. stop BPM and other writers, create a native backup, and successfully restore
   and inspect it elsewhere;
8. run the read-only, database-specific preflight;
9. recheck the signed identities and database snapshot under the migration's
   transaction lock before its first write;
10. update every affected profile and the Alembic stamp in one transaction; and
11. prove all postconditions on SQLite and PostgreSQL.

Failure at any step stops before profile or stamp mutation. A candidate catalog
must not be promoted, and its migration revision must not be created, while the
total-convertibility proof is incomplete. Seeing every profile in one current
database convert successfully does not prove that every document allowed by
the source schema can convert.

## Immediate successor selection

Retirement is an ESR-to-ESR lifecycle transition, not a manual conversion and
not a latest-ESR recommendation. The transition manifest names the source and
target stable line and exact artifact. The target must resolve to exactly one
candidate-catalog row that is:

- family `esr`;
- supported and backed by an available exact artifact;
- numerically newer than the source; and
- the smallest numeric supported ESR line above the source.

Thus ESR 115 resolves to ESR 140 while ESR 140 remains supported, and ESR 140
resolves to ESR 153 in the required example. ESR 115 to ESR 153 is rejected if
ESR 140 is supported: it skips an intermediate line. Missing, ambiguous,
same/older, Release-family, unsupported, cyclic, and skipped successors all
block the catalog before a migration is generated.

The manifest's explicit successor must match both the candidate catalog and
the lifecycle transition declaration. It is never inferred from product
default, recommendation target, declaration order, a lexical identifier,
`max(version)`, a profile sample, or `CURRENT_ESR_SCHEMA_CHANNEL`.

## Total lossless convertibility is schema-wide

The quantified input is **every JSON instance valid under the exact normalized
source validation schema**, including empty documents, nested arrays and
objects, dynamic dictionary keys, empty containers, and every value alternative.
Two proof methods are permitted.

### Exact schema containment

A machine-checkable proof binds both exact artifact identities and both
normalized validation-schema digests. It must show that leaving every source
document byte-semantically unchanged produces a target-valid document and that
every source policy/value interpretation is semantically equivalent on the
target. A policy-name subset comparison is not semantic or value-shape
containment. Defaults are not materialized to make containment appear true.

### Complete recipe partition

An immutable registry may instead partition the entire source-valid domain
into exhaustive and pairwise-disjoint predicates. Every partition has exactly
one M2-04-compatible lossless recipe or exact unchanged evidence; every source
and target atom is accounted; every output domain is target-valid; and a
machine-checkable proof binds the exact schema, recipe definition, and evidence
digests. A first-match rule, broad version range, uncovered schema location,
ambiguous predicate, lossy transform, or sample-only fixture blocks retirement.

A complete proof has exact artifacts bound, zero uncovered schema locations,
zero blockers, and one immutable proof-artifact digest. Until then the stable
error is `retirement_total_convertibility_unproven` and mutation is `none`.
Manual preview applicability and success on sampled/current profiles are
explicitly forbidden substitutes for this proof.

## Immutable transition manifest

The release-owned manifest binds:

- canonical previous and candidate lifecycle-catalog digests;
- source and target line IDs, numeric lines, artifact IDs, bundle SHA-256, and
  normalized validation-schema SHA-256;
- the complete candidate supported-ESR set and declared successor;
- the conversion-contract version and immutable recipe registry identity;
- the total-proof artifact digest;
- exact source and target Alembic revision IDs; and
- its own domain-separated RFC 8785/JCS SHA-256 identity.

The digest projection is every manifest member except `manifest_digest`, under
`bpm-retired-esr-transition-manifest:v1\n`. Any catalog, schema, registry,
proof, mapping, or revision change invalidates the manifest and requires a new
review. A migration cannot download, discover, or substitute these inputs at
execution time.

`synthetic-contract-only` evidence can exercise the gate but can never make a
production catalog promotable. Production evidence must bind independently
generated exact bundled artifacts and be `production-exact-artifacts`.

## Backup and read-only database preflight

Before the migration transaction, BPM and every other writer are stopped. A
versioned read-only preflight binds the reviewed transition manifest to one
database identity, engine/version, known Alembic source stamp, expected schema
shape, affected count, and a canonical row-set snapshot. The snapshot covers
each affected profile's revision, document, compliance, metadata, and conversion
plan identity, while persisted/logged evidence follows the privacy boundary.

The operator must create a new native backup and prove a separate restore:

- SQLite uses the native online backup/`.backup` mechanism, an absolute
  distinct path, SHA-256, `PRAGMA integrity_check`, stamp/shape inspection, and
  row-count parity on the restored copy.
- PostgreSQL uses a custom, serializable-deferrable `pg_dump`, SHA-256, and
  `pg_restore --exit-on-error --single-transaction` into a distinct isolated
  database, followed by stamp/shape/count parity.

The preflight rejects an active writer, unknown/multiple/wrong stamp, schema
shape drift, unreadable JSON, missing source or target artifact, source-invalid
profile, conversion blocker, incomplete compliance accounting, count/snapshot
drift, insufficient resources, or unverified backup/restore. It creates no ORM
assignment, flush, commit, timestamp touch, Alembic stamp, or policy-data audit
record.

Evidence may retain aggregate counts, artifact identifiers, database-identity
and row-set digests, backup/manifest digests, and locale-neutral codes. Logs
omit policy values and presence, policy IDs/pointers, profile IDs/names/
descriptions, compliance values/notes, credentials/database URLs, and full
document, plan, or row digests.

## Alembic is the only writer

One explicit offline Alembic revision is the sole writer. Application startup,
request handlers, profile list/GET, conversion preview, validation, and UI
rendering never normalize or migrate a retired channel. An unupgraded database
fails readiness before profile routes with
`schema_channel_retired_requires_migration` and no mutation.

The revision uses immutable migration-owned schemas, registry/recipes, proof,
and transition manifest. It does not call the HTTP conversion API or read a
mutable runtime registry. Immediately before its first write, under the engine's
write/row lock, it rechecks the manifest, stamp/shape, affected count and
snapshot, exact per-profile revision and plan identity, schema identities,
registry identity, and zero blockers. Any mismatch makes the preflight stale
and rolls back without a profile or version-stamp change.

## Atomic profile behavior

The transaction contains every affected row and the target Alembic stamp. It
includes active and archived profiles on the exact retired source artifact.
In other words, all stored profiles on the exact retired artifact are in scope;
archive state never exempts a row from the required successor migration.
For each affected row it applies the M2-04-derived target document and
compliance disposition and changes only:

- `schema_version` to the exact successor artifact;
- `flags` to the fully accounted target-valid document;
- `compliance` to `absent`, `preserved-verified`, `recomputed`, or
  `invalidated-preserved`; and
- `revision` from its exact preflight value to that value plus one.

`id`, `name`, `name_casefold`, `description`, `created_at`, and `deleted_at`
are exactly preserved. The migration's database statement owns `updated_at`:
all affected rows receive one transaction-scoped database value. Unaffected
rows, including profiles already on the target, preserve revision and
`updated_at`. No non-null compliance object remains a current claim without
the exact target-bound M2-04 proof; the fallback is the complete
`invalidated-preserved` envelope, never deletion or opaque copying as live CIS
state.

Every converted document is validated against the exact target schema before
the first write. There is one commit. A validation, plan, persistence, stamp,
or injected failure rolls back every affected field, every affected timestamp,
and the source Alembic stamp. Partial success is never returned or logged.

## Idempotency, interruption, and recovery

Rows already on the successor are outside the update predicate and remain
byte/value unchanged. Zero source rows is a valid migration: it performs no
profile write but may atomically advance the Alembic stamp. Once stamped, a
normal Alembic retry is a no-op and cannot increment revisions again.
That terminal idempotent outcome uses the locale-neutral code
`retirement_already_applied`; it is not a failure or a second write.

An interruption before commit must leave the source stamp and every profile at
its source state. Retain the failed candidate for diagnosis; restore the
verified backup into a new clean candidate and rerun there. Never retry an
ambiguous or failed candidate in place.

If the connection outcome at commit is ambiguous, inspect stamp and
postconditions read-only first. A target stamp with all postconditions is
terminal success and a retry is an Alembic no-op. A source stamp with the exact
preflight state uses clean-candidate recovery. A source stamp with mixed source
and target rows, partial revision/timestamp changes, or any other mismatch is
`retirement_partial_state_detected`; in-place repair is forbidden.

Alembic downgrade across the retirement revision raises
`retirement_downgrade_unsupported` before writing. A retired source may no
longer validate current product data, transformed values may not have a safe
inverse, and compliance evidence may have been invalidated/recomputed.
Therefore downgrade is not recovery. Restore the verified pre-upgrade backup
to a new clean candidate; no tool automatically replaces the configured
database.

## Required SQLite and PostgreSQL evidence

M6 must execute the same semantic matrix on real SQLite and PostgreSQL
candidates. Both engine contours are mandatory and inject failures before the
first write, after the first affected row, immediately before commit, and at a
connection-interruption boundary. Each proves:

- source database and native backup remain unchanged;
- a failed candidate retains the source stamp and all original rows;
- no profile has a partial revision or timestamp change;
- a new candidate restored from the verified backup reaches the target stamp;
- affected active and archived rows reach the declared target and validate;
- existing target/other-channel rows remain unchanged; and
- a second upgrade is a no-op.

SQLite evidence runs through `make test-db-recovery`. PostgreSQL evidence is
mandatory in `make test-postgres-integration`; absence of the disposable
PostgreSQL service fails that CI gate rather than converting the requirement to
SQLite-only evidence.

## Contract fixtures and current truth

The machine contract contains two transition fixtures:

1. `synthetic-esr115-to-esr140-gate` uses toy exact-schema identities to prove
   successor selection, a complete synthetic containment result, backup/
   preflight shape, and the no-production-promotion boundary. It does **not**
   claim that the planned ESR 115.38 bundle exists or that real ESR 115 to ESR
   140 conversion is lossless.
2. `required-current-esr140-to-esr153` binds the current exact ESR 140.13 and
   ESR 153.0 bundles, normalized-schema hashes and complete reviewed proof. Its
   target revision remains unnamed in the active contract because ESR 140.13
   is still supported. The candidate-only materializer proves that a later
   retired catalog can bind a target revision without changing today's graph.

The current production block is therefore lifecycle state, not a missing total
proof: M6 must not install or execute the candidate while the active catalog
still advertises ESR 140.13 as supported.

The required negative vectors cover a missing successor, a skipped supported
intermediate ESR, an incomplete proof, stale and identity-mismatched manifests,
transaction failure, interruption, already-applied idempotency, partial-state
recovery, and the downgrade boundary. Every failure has mutation `none`; the
already-applied case alone reports `no-op` and preserves target rows exactly.

## Handoff boundary

M6-01 owns catalog-diff and successor validation. M6-02 owns the real total
proof. M6-03 owns immutable migration inputs, the versioned Alembic writer, and
both engine transactions. M6-04 owns the real ESR 140 to ESR 153 and synthetic
future ESR 115 to ESR 140 data matrices. M6-05 preserves read-only runtime
ownership. M6-06 owns privacy-safe observability and operator recovery evidence.
This contract authorizes none of those writes before their gates are complete.
