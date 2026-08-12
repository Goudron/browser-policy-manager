# BPM 0.9.5 Database Upgrade Matrix And Recovery Contract

Status: active release contract; interruption and recovery evidence closed by `BPM094-M4-06`

Machine contract: `database-upgrade-matrix-0.9.5.json`

Golden data: `tests/fixtures/database_upgrade/golden_profiles_0_9_5.json`

## Decision

BPM 0.9.5 retains the complete released Alembic window, from the original
October 2025 schema through the Firefox 153/dual-ESR revision, plus the three
revision aliases that `alembic/env.py` already recognizes. Every retained source
is upgradeable on SQLite and PostgreSQL through the released migration head.

The final repair revision is
`20260804_alembic_owns_profile_schema_and_data`: it owns the missing
`compliance` column, the retained `5cb73fdb68ed` root-alias data path, and the
last same-family channel convergence. Runtime startup and profile listing no
longer mutate schema or stored channels. Real two-engine proof is provided
through `tests/integration/db/test_database_integration.py` and the mandatory
`postgres-integration` CI service job. Interruption and recovery proof is closed
on both engines. Application lifespan now performs a read-only head/schema
check and refuses empty, old, unknown, or partially shaped databases. It never
migrates or repairs them.

An empty database is a supported fresh-install source. A non-empty database
without an unambiguous retained Alembic stamp is not. Maintainers must not guess
a revision, stamp an unknown database, merge `policies` and `profiles`, or run a
repair statement merely to make the upgrade continue.

## Candidate-only ESR 140 retirement artifact

The released graph still ends at `20260804_add_profile_name_casefold`, and ESR
140.13 remains supported in the active lifecycle catalog. Therefore no
retirement revision is installed under `alembic/versions/` and ordinary
`upgrade head` does not migrate ESR 140 profiles.

`migration_support/retirement_revision_materializer_v1.py` owns the exact
future ESR 140.13 to ESR 153.0 candidate. It freezes proof digest
`3d04890c00a89534526fea7456e89250c36ba3617fa0d10949c8e51d98bcc2bb`,
both exact schema identities, the empty recipe registry and the complete
report. The current supported catalog is a hard materialization error. A
reviewed candidate that explicitly retires ESR 140 can render an inert,
Alembic-compatible revision artifact whose manifest binds both catalogs and
both revision IDs.

The candidate artifact has passed a real disposable SQLite Alembic upgrade:
verified native backup/restore evidence gates the run; active and archived
source rows move in the locked outer transaction; compliance without exact
target proof is invalidated while preserving its source envelope; unrelated
rows and fields remain unchanged; and Alembic owns the stamp. This is not
release activation. The real PostgreSQL candidate execution, active-graph
installation, source-shape admission, runtime catalog retirement and final
matrix promotion remain one coordinated R3/release action.

## Supported source matrix

`Required` means that the final M4 migration/integration suite must exercise the
row on that engine. It does not claim that today's tests already supply that
evidence.

| Source ID | Alembic stamp | Required source shape | SQLite | PostgreSQL | Golden scenario |
| --- | --- | --- | --- | --- | --- |
| `fresh-empty` | no stamp, no application tables | empty | Required | Required | `fresh-empty` |
| `legacy-5cb73fdb68ed` | `5cb73fdb68ed` | legacy `policies`, owner, no soft delete | Required | Required | `from-initial` |
| `canonical-20251022` | `20251022_init_profiles` | `profiles`, owner, no soft delete | Required | Required | `from-initial` |
| `legacy-20251026` | `20251026_add_deleted_at` | legacy `policies`, owner, soft delete | Required | Required | `from-deleted-at` |
| `canonical-20251026` | `20251026_add_deleted_at_profiles` | `profiles`, owner, soft delete | Required | Required | `from-deleted-at` |
| `legacy-20260323` | `20260323_rename_profiles` | normalized `profiles`, owner and revision | Required | Required | `from-normalized` |
| `canonical-20260323` | `20260323_normalize_profiles` | normalized `profiles`, owner and revision | Required | Required | `from-normalized` |
| `canonical-20260330` | `20260330_upgrade_profiles_to_firefox149` | normalized `profiles`, owner and revision | Required | Required | `from-firefox-149` |
| `canonical-20260423` | `20260423_upgrade_profiles_to_firefox150` | normalized `profiles`, owner and revision | Required | Required | `from-firefox-150` |
| `canonical-20260521` | `20260521_upgrade_profiles_to_firefox151` | normalized `profiles`, owner and revision | Required | Required | `from-firefox-151` |
| `canonical-20260606` | `20260606_drop_profile_owner` | ownerless `profiles` with revision | Required | Required | `from-owner-drop` |
| `canonical-20260620` | `20260620_upgrade_profiles_to_firefox152` | ownerless `profiles` with revision | Required | Required | `from-firefox-152` |
| `canonical-20260721` | `20260721_upgrade_profiles_to_firefox153_dual_esr` | ownerless `profiles` with revision | Required | Required | `head-idempotent` |
| `canonical-20260804` | `20260804_alembic_owns_profile_schema_and_data` | ownerless `profiles` with compliance and revision | Required | Required | `head-idempotent` |
| `canonical-20260804-name-casefold` | `20260804_add_profile_name_casefold` | ownerless `profiles` with compliance, revision and Unicode search key | Required | Required | `head-idempotent` |

The machine contract is authoritative for exact required/optional columns. A
`compliance` column may already exist in historical databases.
Its presence and JSON value must be preserved. Its absence is a supported input
defect and must be repaired by Alembic; it is not permission for startup code to
alter the schema.

## Pre-upgrade invariants

Before a migration command is allowed to write, the maintainer or future
preflight tool must establish all of the following:

1. The application and all other writers are stopped, and the target database
   identity and SQLAlchemy dialect match the intended environment.
2. `alembic_version` contains exactly one known stamp, unless the database is
   completely empty and is being installed from scratch.
3. Tables and required columns match the shape assigned to that stamp. There is
   never both a `policies` and a `profiles` table.
4. Required stored fields are readable, names are non-null and unique, and JSON
   storage can be decoded. Firefox-policy semantic invalidity is recorded but
   does not authorize mutation or row deletion.
5. A new backup has been checksummed and restored into a different disposable
   database/path. Integrity and row-count checks pass on that restored copy.
6. There is sufficient free space and the migration identity has only the
   privileges required for the documented operation.

The preflight records database identity, engine/version, source stamp, source
shape, table/row counts, backup checksum and restore-check result. It must not
record policy JSON, compliance content, credentials, or other user data.

## Post-upgrade invariants

The released head must satisfy the same contract on SQLite and PostgreSQL:

- exactly one `profiles` table and no `policies` table;
- one Alembic version row at the released head;
- the exact profile columns listed by the JSON contract, including
  `compliance`, `revision`, and `deleted_at`, with no `owner` column;
- unique name and the schema-version/created/updated/deleted indexes, plus the portable Unicode `name_casefold` search index;
- the same row count and the same IDs, names, descriptions, nested `flags`,
  existing compliance values, timestamps, archive state, and revisions;
- `revision = 1`, `compliance = null`, and `deleted_at = null` only where that
  source schema did not have the corresponding field;
- only explicit same-family channel changes. Release rows become Release 153,
  ESR 140 rows become ESR 140.13, and ESR 153.0 is never converted to Release;
- invalid policy payloads and unknown channel strings remain byte-semantically
  equivalent JSON/data and are surfaced for later quarantine/manual review.

Dropping historical `owner` storage is the one intentional data-discarding
transformation already approved by the earlier owner-removal work. Downgrade
cannot reconstruct those values and is not a backup strategy.

## Stop conditions

Stop before any write, retain the database and backup evidence, and report the
condition when any of these is true:

- a non-empty database is unstamped;
- the stamp is unknown, missing, duplicated, or there are multiple heads;
- `policies` and `profiles` coexist;
- the table/column shape disagrees with the stamp;
- required values are null, profile names collide, or stored JSON is unreadable;
- a prior upgrade appears partial or failed;
- the application or another writer is active;
- there is insufficient disk space, connectivity, or privilege;
- the backup cannot be checksummed, restored elsewhere, or verified;
- the migration command fails or the post-upgrade invariants differ.

Do not retry against the partly changed database. Recovery proof requires that recovery
starts from a separately verified backup and a clean target.

## SQLite backup and recovery procedure

Use explicit absolute paths outside the repository and never target
`data/bpm.db` in tests.

1. Stop BPM and record the source stamp and row counts read-only.
2. Run `sqlite3 <source.db> "PRAGMA integrity_check;"`; require exactly `ok`.
3. Create a new backup with
   `sqlite3 <source.db> ".backup '<timestamped-backup.db>'"`.
4. Write a checksum with `sha256sum <timestamped-backup.db>` and make the
   backup read-only.
5. Copy that backup to a distinct restore-check path. Run `PRAGMA
   integrity_check`, inspect its Alembic stamp, and compare table/row counts.
6. Run the upgrade only against a separate candidate copy. Verify every target
   invariant and golden-data digest before configuring BPM to use it.

On failure, leave the source and failed candidate untouched. Create another
candidate from the verified backup; never copy a backup over the only source
database and never treat an Alembic downgrade as recovery.

The executable candidate workflow is intentionally split from backup creation:
the maintainer first creates the native backup, makes it read-only, then the BPM
tool verifies and binds it to a checksum manifest. All paths must be absolute,
new outputs must not exist, and neither backup nor candidate may be the
repository `data/bpm.db` path.

```bash
sqlite3 /absolute/source.db ".backup '/absolute/bpm-pre-0.9.5.backup.db'"
chmod a-w /absolute/bpm-pre-0.9.5.backup.db
.venv/bin/python tools/database_upgrade_recovery.py verify-sqlite-backup \
  --backup /absolute/bpm-pre-0.9.5.backup.db \
  --manifest /absolute/bpm-pre-0.9.5.backup.json
.venv/bin/python tools/database_upgrade_recovery.py retry-sqlite-upgrade \
  --backup /absolute/bpm-pre-0.9.5.backup.db \
  --manifest /absolute/bpm-pre-0.9.5.backup.json \
  --candidate /absolute/bpm-0.9.5-candidate.db
```

The last command restores a new candidate, runs Alembic head, and applies the
same read-only release readiness check used by application startup. It never
replaces the configured database. Inspecting the candidate and changing BPM's
database configuration remain explicit maintainer actions.

## PostgreSQL backup and recovery procedure

1. Stop BPM and other writers. Record database/server identity, stamp and counts
   with a read-only connection.
2. Create a new custom-format backup with
   `pg_dump --format=custom --serializable-deferrable --file=<backup.dump> <database-url>`.
3. Checksum the dump and restore it into a newly created, isolated verification
   database using
   `pg_restore --exit-on-error --single-transaction --dbname=<restore-check-db> <backup.dump>`.
4. Compare stamp, tables, columns and row counts in the verification database.
5. Create a second clean candidate from the same verified dump and run the
   migration there. Switch BPM configuration only after all post-invariants pass.

Never use `--clean`, `DROP DATABASE`, or an in-place restore as an automated
recovery step. Destructive replacement requires explicit maintainer action after
the verified original and backup have both been retained.

The tested retry sequence is:

```bash
pg_dump --format=custom --serializable-deferrable \
  --file=/absolute/bpm-pre-0.9.5.dump <source-database-url>
sha256sum /absolute/bpm-pre-0.9.5.dump
chmod a-w /absolute/bpm-pre-0.9.5.dump
createdb <isolated-restore-check-db>
pg_restore --exit-on-error --single-transaction --no-owner --no-privileges \
  --dbname=<isolated-restore-check-db> /absolute/bpm-pre-0.9.5.dump
createdb <new-retry-candidate-db>
pg_restore --exit-on-error --single-transaction --no-owner --no-privileges \
  --dbname=<new-retry-candidate-db> /absolute/bpm-pre-0.9.5.dump
.venv/bin/alembic -c <candidate-specific-alembic.ini> upgrade head
```

The candidate-specific Alembic configuration points only to the new retry
database. A failed candidate is retained for diagnosis; it is never cleaned and
reused. Creating or dropping these named databases and switching BPM to a
verified candidate require explicit maintainer action.

## Golden fixture semantics

The fixture is declarative and contains no production data. Each matrix source
points to one scenario. Cases cover active and archived rows, nested valid and
invalid Firefox policy JSON, compliance metadata, optimistic revisions, Release
and both ESR families, and an unsupported channel that must be quarantined
without guessing.

The database contract validates the Alembic graph, alias set, matrix coverage,
source-shape representability in an in-memory SQLite database, exact preserved
fields/defaults, and actual current-schema valid/invalid classifications.
`tests/integration/db/test_database_integration.py` materializes the same cases in temporary
SQLite and PostgreSQL databases, performs the real migration chain, and runs
the same CRUD, conflict, query, soft-delete, rollback, concurrent-worker, and
Firefox `policies.json` export contract against both async runtimes. Local
`make test-db-integration` always runs SQLite and skips PostgreSQL only when
`BPM_POSTGRES_TEST_URL` is absent. CI invokes `make test-postgres-integration`,
which fails rather than skips without the temporary PostgreSQL service URL.

## Interruption and recovery evidence

The SQLite repair and ownership proof establishes that a fresh head contains
`profiles.compliance`; the retained root alias transfers its rows exactly and
rejects other mixed-table states; application startup and listing paths perform
no schema or channel mutation. The same released proof covers the real PostgreSQL
shared golden-matrix and runtime contract.

The recovery suite injects a controlled exception into the real final migration on disposable
SQLite and PostgreSQL candidates. The failed candidate never passes application
readiness. The source and native backup remain retained; the backup checksum and
restored stamp/table/row evidence remain unchanged. A separately restored retry
candidate reaches head and preserves the golden row. `make test-db-recovery`
runs the SQLite proof locally; `make test-postgres-integration` requires and runs
the PostgreSQL native dump/restore proof in CI. There are no remaining M4
interruption/restore evidence gaps.
