# Firefox Schema Update Runbook

This runbook turns the Firefox schema bump into a repeatable release task instead of a one-off migration.

Use it when BPM needs to add, retain, refresh, or retire a supported Firefox Release/ESR schema
artifact. A matrix may contain one Release channel and one or more concurrently supported ESR
lines. This is a lifecycle procedure, not a version-string replacement procedure.

Current product surfaces are the profile library, Guided editor, All settings, and JSON editor. Do
not reintroduce a separate advanced editor route, template, redirect, or JavaScript bundle during a
schema bump. In code, the `advanced` section id may still exist as an internal bucket for complex
policy/preference coverage, but it must stay inside Guided review / All settings workflows.

## Inputs You Need Before Editing

Collect official Mozilla support evidence, the Firefox source tag, and one row for every previous
and candidate channel before editing:

1. Mozilla `policy-templates` tag, for example `v7.10`.
2. Firefox channel type and version, for example `Release 153`, `ESR 153.0`, or `ESR 140.13`.
3. BPM channel string and output filename for that version.
4. Stable line identity, exact artifact identity, support state, lifecycle role, and selector role.
5. Explicit same-line refresh mapping or retirement successor for each changed persisted artifact.

The source evidence must be official and reviewable: Mozilla product-details/support material for
the support state and end/recheck date, and the official `mozilla/policy-templates` release metadata
for each source tag. Browser binaries, generated schemas, labels, the largest version number, and a
previous BPM file are not support evidence.

Keep one previous-versus-candidate lifecycle matrix for the whole change. It must classify every
stable line as **added**, **retained**, **refreshed** (same stable line, new exact artifact), or
**retired**, and it must separately identify the latest ESR, product default, default Release, and
each retirement successor. For the BPM 0.9.5 four-channel example:

| Field | Example |
|---|---|
| Firefox 153 source tag | `mozilla-policy-templates-master-a892b621f7f98ee91c8ed84290641f2703e88490` |
| Release channel | `release-153` |
| Release version/file | `153.0` / `app/schemas/policies/firefox-release-153.json` |
| Latest ESR / product default | `esr-153.0` / `app/schemas/policies/firefox-esr-153.0.json` |
| Retained older ESR | `esr-140.13` / `app/schemas/policies/firefox-esr-140.13.json` |
| Retained legacy-OS ESR | `esr-115.39` / `app/schemas/policies/firefox-esr-115.39.json` |
| Latest-ESR recommendations | `esr-115` and `esr-140` → `esr-153` (explicit user preview only) |
| Prospective retirement chain | `esr-115` → `esr-140` → `esr-153` (Alembic only after retirement) |

If this matrix is not clear up front, stop and resolve it first. Do not infer an ESR migration from
the highest version, catalog order, product default, or recommendation target: a concurrently
supported ESR remains a separate target channel and profile conversion is an explicit user action.

### Lifecycle-role rules

- **Added** lines require independently generated source/checksum evidence and complete wiring, but
  do not authorize a write to any existing profile.
- **Retained** lines remain selectable and must retain their exact artifact/source evidence.
- **Refreshed** lines require an explicit old-artifact to new-artifact mapping on the same stable
  line; they are not a retirement and must not be confused with a newer ESR successor.
- **Retired** ESR lines require exactly one explicit, supported, immediate numerically newer ESR
  successor. Release is never an ESR successor.
- The only latest ESR is a lifecycle role. It may be the product default and recommendation target,
  but neither role authorizes automatic migration.

The active authority is the machine-readable Firefox schema lifecycle catalog contract. Its
Markdown companion explains the roles, ordering, recommendation, and successor meanings. Treat
the catalog, not a tuple position or label, as the lifecycle source of truth.

## Source Artifacts

BPM builds bundled schemas from two Mozilla inputs for every source tag. Their exact raw URLs,
byte sizes, SHA-256 digests, Mozilla release attribution, and MPL-2.0 attribution are declared in
`tools/firefox_schema_inputs_manifest_0_9_4.json`; this input manifest is independent from browser
patch evidence and the schema-target manifest.

1. The versioned `docs/index.md` policy-template document:
   `data/upstream/policy-templates/<mozilla-tag>/policy-templates.md`
2. The Linux example policy snapshot from the official release-tag raw file:
   `data/upstream/policy-templates/<mozilla-tag>/linux-policies.json`

Recommended workflow:

1. Review the Mozilla release metadata and update the declarative input manifest with the exact
   release tag, raw file URLs, byte sizes, SHA-256 digests, and license/provenance fields.
2. Run `make provision-firefox-schema-inputs`. It downloads only manifest-pinned inputs, verifies
   size and checksum before atomic cache placement, retries transient failures a bounded number of
   times, and quarantines an invalid cache entry before replacement.
3. For an offline generation/review machine, run
   `python tools/provision_firefox_schema_inputs.py --offline`; it reuses only valid cached inputs
   and fails without a network fallback when an input is absent or invalid.
4. Use the cache paths
   `data/upstream/policy-templates/<mozilla-tag>/policy-templates.md` and
   `data/upstream/policy-templates/<mozilla-tag>/linux-policies.json` only after that verification.

The manifest-pinned raw `linux/policies.json` input is the authoritative example policy payload for
the converter. Do not infer its content, tag, or provenance from a Firefox browser patch.

Before downloading, confirm the release metadata from the official Mozilla GitHub release page or
API. The release name must explicitly cover the target Firefox support matrix. Record or review the
manifest's raw-input sizes and SHA-256 digests in the execution notes so a later regeneration can
identify the exact inputs. The `data/` tree is a local, Git-ignored converter cache; the
committed/reviewed outputs are the bundled schemas and the code/tests that identify their upstream
source.

Mozilla release notes and the rendered legacy docs page can move at different speeds. Compare the
release notes with the generated diff. If Mozilla announces a new field but it is absent from both
the rendered docs input and `linux/policies.json`, do not silently claim coverage: verify the current
Firefox Admin Docs or upstream implementation, then either extend the converter with a tested rule
or record the upstream/converter gap explicitly.

### Nested-policy completeness gate

Before accepting generated schemas, make a per-channel checklist of every new top-level policy and
every new nested field announced in the Firefox release notes or Firefox Administrator Reference.
Compare that checklist with the generated JSON, including fields below dynamic dictionaries such as
`ExtensionSettings["*"].allowed_permissions`. For each checklist item, add a regression that proves
presence on every supported channel and absence on channels where Firefox does not support it. A
converter bridge for incomplete source artifacts must cite the authoritative Mozilla evidence in its
comment and test name. Do not start product-documentation updates until this gate passes.

## Files That Must Move Together

Treat the following as one unit of change when their owned surface is affected:

- `app/core/schema_channels.py`
- lifecycle catalog, transition-plan, total-proof, and retirement-safety contracts under
  `docs/architecture/`
- `alembic/env.py` and a new immutable revision in `alembic/versions/` **only for an approved
  actual retirement**
- `app/schemas/policies/firefox-*.json`
- `README.md`
- `tools/convert_policies_from_upstream_lib/common.py`
- `tools/convert_policies_from_upstream_lib/cli.py`
- `app/services/firefox_policy_ui_registry/overrides.py`
- `app/web/firefox_wizard_shell/inline_editors.py`
- `app/web/firefox_wizard_shell/catalog.py`
- `app/web/firefox_settings_catalog/*`
- `app/web/firefox_manual_policy_controls.py` when a new policy becomes a curated Guided control
- Guided editor templates and static bindings when a new policy deserves a first-class card
- All settings templates/static bindings when schema-shell behavior, search, or route handoff changes
- `app/i18n_src/*/*.json` source catalogs and generated `app/i18n/*.json` runtime catalogs when
  labels, placement copy, or policy help text changes
- `app/i18n_src/catalog-order.json`, `app/i18n_src/overrides/*/policy-labels.json`, and generated
  `app/i18n_src/generated/*/policy-labels.json` when schema generation introduces a policy label
- `tests/unit/schema/contracts/test_schema_channels.py`
- `tests/integration/schema/test_schema_validation.py`
- `tests/integration/firefox/test_firefox_wizard_shell.py`
- `tests/integration/firefox/test_firefox_manual_policy_controls.py`
- `tests/unit/firefox/test_firefox_settings_catalog_builders.py`
- `tests/contract/ui/localization/test_web_profiles_page.py`
- `tests/integration/db/test_migrations.py` and retirement-owner/materializer tests when lifecycle
  state changes
- `tests/integration/locale/test_ru_locale_quality.py` and
  `tests/fixtures/locale_contracts/visible_english_allowlists.json` when a new policy label contains
  a preserved Latin technical/product term
- `.github/workflows/ci.yml`
- `README.md`
- `alembic/versions/*.py` only for the approved retirement migration

If one of these omits a supported matrix channel, retains an actually retired runtime artifact, or
claims a migration that has not passed the retirement gate, the bump is not finished.

## Update Sequence

### 1. Plan and review the lifecycle transition without mutation

Compare explicit previous and candidate catalog snapshots. Run the maintained schema-lifecycle
dry-run in its default **read-only** mode and retain its value-free plan: phases, changed lines,
added/retained/refreshed/retired classifications, exact artifacts, successor mappings, blockers,
and terminal result. A dry-run may inspect an explicitly selected disposable or
backup-verified database for aggregate affected-profile counts, but it must not write profiles,
stamp Alembic, alter the active catalog, or create an installed revision.

Use two explicit reviewed snapshots; the command does not infer either side from the runtime
catalog. The default does not create a database engine or inspect profile rows:

```bash
make schema-lifecycle-dry-run \
  PREVIOUS_LIFECYCLE_CATALOG=docs/architecture/firefox-schema-lifecycle-catalog-contract-previous.json \
  CANDIDATE_LIFECYCLE_CATALOG=docs/architecture/firefox-schema-lifecycle-catalog-contract-candidate.json \
  RETIREMENT_TOTAL_PROOF=docs/architecture/firefox-esr-140.13-to-esr-153.0-retirement-total-proof-0.9.5.json
```

The report has flushed `phase`/`channel` completed/total progress and a deterministic terminal
JSON record. It identifies the cache as unused/not-written, prints only line/artifact mappings and
aggregate counts, and never includes policy values, profile identifiers, connection URLs, or
backup secrets. An optional count requires both an explicit database URL and an explicit
`disposable` or `verified-backup` scope; SQLite must use a URI opened with `mode=ro`, and a
`verified-backup` count also requires reviewed native-backup evidence. A count observation is not
a migration preflight and cannot authorize activation.

For every directed pair of supported artifacts, preserve the pairwise conversion contract: preview
is read-only, apply is explicit and atomic, and each source atom is unchanged, an approved exact
transformation, or a blocker. The full directed pair matrix is evidence for manual conversion; it
does not replace the retirement proof.

For a proposed retirement, validate the lifecycle plan before schema or database work. It must
reject absent, ambiguous, non-ESR, non-newer, unsupported, unbundled, cyclic, or skipped
successors. An ESR 115 retirement selects ESR 140 while ESR 140 remains supported; it cannot jump
to ESR 153. An ESR 140 retirement selects ESR 153 only when ESR 140 is actually removed from the
candidate catalog.

### 2. Update the central channel constants

Start in `app/core/schema_channels.py`.

Update:

- `SUPPORTED_SCHEMA_CHANNELS`
- `DEFAULT_SCHEMA_CHANNEL`
- `DEFAULT_RELEASE_SCHEMA_CHANNEL`
- `SCHEMA_LABELS`
- `SCHEMA_FILENAMES`

This file is the product-level source of truth. UI, API, loaders, and validation should derive supported channels from here.

### 3. Update converter defaults

Adjust the declarative build targets in:

- `tools/firefox_schema_targets.json`
- `tools/convert_policies_from_upstream_lib/common.py`
- `tools/convert_policies_from_upstream_lib/cli.py`

At minimum, update:

- bundled output filenames
- every supported Release / ESR channel string and version
- each channel's Mozilla source tag and versioned input paths

Do not use a broad version-string replacement for historical policy metadata. Existing policies
must keep their real `x-bpm-min-version` and compatibility provenance even when the active channel
moves forward.

### 4. Generate the new bundled schemas

Run the converter through the committed target manifest. The manifest is the explicit audit record
for every generated output and prevents a second ESR from being silently derived by file copy.

Example:

```bash
python tools/convert_policies_from_upstream.py \
  --targets-file tools/firefox_schema_targets.json
```

For a matrix with more than one ESR, extend the converter contract and invoke it so each output is
generated from its own explicit channel/version row. Do not create an additional ESR schema by
copying or relabeling another generated JSON file.

Do not remove a bundled artifact merely because a newer artifact exists. Remove a schema file only
in the coordinated candidate that retires its exact artifact, after the transition plan, proof, and
future Alembic activation gates below are ready. Retain every artifact named by the current support
matrix.

### 5. Sanity-check the generated schemas before wiring them in

Check the metadata directly in the JSON files:

```bash
for schema in app/schemas/policies/firefox-*.json; do
  jq '{
    channel: .["x-bpm-channel"],
    artifact_id: .["x-bpm-artifact-id"],
    line_id: .["x-bpm-line-id"],
    artifact_version: .["x-bpm-version"],
    firefox_line: .["x-bpm-firefox-line"],
    firefox_version: .["x-bpm-firefox-version"],
    source: .["x-bpm-source"],
    source_provenance: .["x-bpm-source-provenance"],
    generator: .["x-bpm-generator"]
  }' "$schema"
done

jq '.properties.ExtensionSettings.additionalProperties.properties.allowed_types.items.enum' \
  app/schemas/policies/firefox-release-153.json

jq '.properties.ExtensionSettings.additionalProperties.properties | with_entries(select(
  .key == "allowed_permissions" or .key == "blocked_permissions" or
  .key == "runtime_allowed_hosts" or .key == "runtime_blocked_hosts"
))' app/schemas/policies/firefox-release-153.json
```

Minimum expectations:

- Release channel matches the intended `release-*` value.
- ESR channel matches the intended `esr-*` value.
- versions match the intended Firefox numbers exactly
- exact artifact identity, stable line identity, Firefox line, and observed
  Firefox patch/version remain distinct; do not derive one from another
- `x-bpm-source` matches the Mozilla release tag you actually used
- `x-bpm-source-provenance` exactly records the M3-01 manifest's upstream tag,
  release attribution, license, raw URLs, byte lengths, and SHA-256 inputs;
  `x-bpm-generator` identifies the owner command that emitted the bundle
- `ExtensionSettings.allowed_types` still contains expected upstream values such as `sitepermission`
- every item in the nested-policy completeness checklist is present only on its intended channels

If these checks fail, do not continue into app changes yet.

### 6. Wire the candidate catalog, conversion, UI, and drift owners

After the bundled JSON is correct:

1. Update active owned surfaces from the lifecycle catalog; do not replace channel literals
   mechanically or infer roles from an ordered list.
2. Update or add pairwise conversion fixtures for every affected source/target artifact direction.
   A blocked conversion remains blocked and visible; it must never discard, coerce, default, or
   silently relabel policy data.
3. Update documentation and UI labels to the complete new Release/ESR support matrix.
   In `README.md`, refresh the Supported Firefox Schemas table, examples that carry a `schema_version`, and any prose that names the active Release / ESR versions.
4. Update every active locale catalog when Release / ESR labels, schema-channel copy, policy names,
   or schema-related UI strings change. Edit `app/i18n_src/<locale>/*.json`, then rebuild generated
   `app/i18n/*.json` with `make build-locale-catalogs`. The generated runtime catalogs
   `app/i18n/en.json`, `app/i18n/ru.json`, `app/i18n/de.json`, `app/i18n/zh-CN.json`,
   `app/i18n/fr.json`, and `app/i18n/es-ES.json` must all stay in sync. Cover every active locale
   source segment; follow `docs/locale_update_runbook_2026-06-01.md`, the global glossary, and the
   placeholder rules. If new or changed Mozilla/Firefox terms enter the UI, verify terminology
   against Pontoon/SUMO evidence and update the glossary or locale audit notes before release.
5. Update CIS source/mapping/generation evidence for every supported exact schema channel. A
   missing, empty, invalid, or unreviewed CIS layer blocks the candidate; do not publish an
   unavailable compliance selector for a supported product schema. Follow
   `docs/cis_firefox_update_runbook_2026-04-13.md` and its provenance and restricted-content rules.
6. Update the legacy guard so retired strings are banned outside explicit immutable migration
   material, focused fixtures, and historical evidence. A retained older ESR is not legacy merely
   because a newer ESR exists.

### 7. Retirement: prove first, materialize only for a future candidate

Retirement has a stricter path than addition or refresh. Before any database mutation, bind exact
source/target bundle hashes, normalized-validator hashes, the immutable recipe registry, the
previous/candidate catalog digests, and the exact immediate successor in one reviewable transition
manifest. Then complete **total convertibility** for every source-schema-valid document shape:
schema containment with semantic evidence, or an exhaustive, non-overlapping set of approved
lossless recipes. A sampled profile set, successful preview, a policy-name comparison, or an
upstream version label is never a substitute. Any uncovered path yields
`retirement_total_convertibility_unproven` and mutation remains `none`.

The M6 ESR 140.13 → ESR 153.0 exact-artifact containment proof is the required production example:
it is complete but it does **not** retire ESR 140 while that line remains supported. Its
candidate-only materializer may render a deterministic, reviewable future Alembic-compatible
artifact, but it must reject the active catalog, must not install a revision in the active graph,
and must not write a profile. Do not create a premature current migration.

At the actual removal of ESR 140 from the candidate catalog, the approved transition must
automatically migrate every stored exact ESR 140 artifact to ESR 153 through the single immutable
Alembic revision. That is the only automatic ESR 140 → ESR 153 migration. It is forbidden while
ESR 140 is supported, and it is forbidden in startup, readiness, request handling, GET/list,
validation, preview, UI rendering, or an ad-hoc backfill. Runtime inference, silent loss,
implicit defaults, and best-effort conversion are prohibited.

Before activation, stop BPM and all other writers, create a native backup, and prove restoration in
a distinct clean candidate. Perform the database-specific preflight read-only, then recheck the
snapshot under the migration lock before its first write. `alembic upgrade head` is the sole schema and stored-channel upgrade path. The revision changes only the reviewed channel, target-valid
flags, compliance disposition, revision, and database-owned transaction timestamp; it includes
archived rows, preserves unaffected data byte-for-byte, stamps and converts in one transaction, and
does not support downgrade. Recovery is restore into a new clean candidate, never in-place repair.

Require the full interruption/idempotency/rollback matrix on both engines. SQLite evidence runs
through `make test-db-recovery`; PostgreSQL evidence is mandatory through
`make test-postgres-integration`. A missing disposable PostgreSQL service is a failed required gate,
not permission to substitute SQLite evidence. Future activation is incomplete until native
PostgreSQL backup/restore and transaction evidence are current for the actual candidate.

### 8. Documentation drift gate

Treat Firefox schema documentation as part of the schema bump, not as a later cleanup:

1. Follow `documentation/runbooks/inventory-refresh.md`, especially the Firefox Release/ESR schema
   bump drift gate.
2. Update `docs/architecture/firefox-policy-documentation-inventory-0.9.0.{json,md}` and any
   affected DITA Firefox Policy Guide topics, User Guide schema-channel topics, Administrator/DevOps
   references, manifests, UI targets, aliases, and deterministic search fixtures in the same review.
3. Preserve six-locale content equivalence for every changed publishable topic; do not leave compact
   localized summaries or English fallback prose.
4. Run the focused Firefox documentation inventory/skeleton/manifest contracts before the release
   gate, then run `make docs-release-check` when generated documentation artifacts changed.
5. Reconcile every added, removed, or renamed policy and managed preference with
   `documentation/config/all-settings-help-target-map-0.9.1.json` and the target audit. A supported
   All Settings row must resolve to its current Firefox documentation topic or retain an explicit
   reviewed no-link disposition; a schema bump may not leave a stale circled-information link.
6. If topic ownership, labels, or routes change, rebuild and review each locale's generated
   `navigation.json`, deterministic search index, manifest, and UI target map. Direct links must
   expand the Documents/guide/section/topic tree to the active topic, and root/parent return must
   remain valid.
7. If the bump changes one of the eleven approved User Guide screenshot scenarios, update the matrix
   row first, recapture all affected locales, and review localized captions and alt text. Do not
   expand the minimal screenshot matrix as an incidental part of a schema update.
8. Run the applicable drift contracts before the broad release gate:

```bash
./.venv/bin/pytest -q -m docs_contract \
  documentation/tests/contract/test_all_settings_documentation_target_audit.py \
  documentation/tests/contract/test_all_settings_help_target_map.py \
  documentation/tests/contract/test_documentation_polish_regression_gates.py \
  documentation/tests/contract/test_user_guide_screenshot_matrix.py
```

9. If the schema bump changes compact UI copy or documentation chrome, record every affected string
   in the UI-copy classification contract: routine explanation may stay removed, while labels,
   state, validation, consequence, unavailable reason, accessible name, and recovery remain at the
   point of action. Reconcile every circled-info target with its localized manifest-backed owner or
   explicit reviewed no-link disposition. Review the audience/style contract, normalized BPM header,
   and one derived BPM product version. Search, URL/history hydration, results, and clear must not
   reopen a collapsed advanced-filter panel.
10. After every documentation-source, documentation-tooling, generated-shell, or served
    documentation-version change in this bump, run `make docs-install-dev` before handoff. Report
    that successful install so the maintainer's subsequent `make dev` serves the current
    documentation artifact; do not start `make dev` for the maintainer.

Important: only the immutable migration and its focused migration fixtures should keep references to
the previous channels.

### 9. Schema-generated policy labels

Every new schema policy can create a runtime key such as
`profiles.shell_policy_<normalized_policy_name>`. Handle these keys before running the broad locale
suite:

1. Derive the exact key through the existing schema-shell/catalog builder or its focused contract.
2. Add the key to `app/i18n_src/catalog-order.json`; overrides alone are not emitted unless the key
   is in catalog order.
3. Add translations to all six `app/i18n_src/overrides/<locale>/policy-labels.json` files.
4. Run `make build-locale-catalogs`. Never hand-edit generated policy-label segments or runtime
   `app/i18n/*.json` as the source of truth.
5. Run the focused runtime-key and accidental-English tests immediately. If the label intentionally
   preserves a technical name such as an API name, update both the global visible-English fixture
   and any locale-specific quality allowlist (currently Russian has an additional token check).
6. Add or update the global glossary and Mozilla terminology evidence when the term is new.

Run the maintained locale contract after registering the generated key:

```bash
make test-locale-contract
```

### 10. Audit BPM UI impact from the new policy docs

Do this as a deliberate product pass, not as a side effect of schema generation:

1. Compare old and new bundled schemas and list added, removed, and structurally changed policies.
2. For every added or changed policy, make an explicit placement decision:
   - All settings coverage is the default and must be present for every schema-backed policy.
   - Guided editor promotion is opt-in and needs a product reason.
   - JSON editor support must preserve exact import/export behavior for values that stay outside visual controls.
3. Confirm every new supported policy appears in All settings for its channel and is absent from unsupported channels.
4. Confirm schema-shell search, category chips, guided-coverage markers, and route handoff links still point to the right surface.
5. Confirm the product header/subtitle and schema selector show the new Firefox Release / ESR labels.
6. Review Firefox policy docs for changed semantics in policies already used by BPM starter presets, CIS overlays, and quick controls.
7. Update starter presets only when the new policy semantics clearly improve an existing BPM scenario without surprising users or breaking compatibility.
8. Add tests that lock the placement decision for important new policies.

For placement, prefer:

- first-class Guided editor control/card: common administrator workflow, high operational value,
  low ambiguity, stable upstream semantics, and safe defaults or clear empty state;
- mapped schema-shell item in All settings and the relevant Guided review bucket: useful but
  detailed, nested, environment-specific, or needs per-site/per-domain tuning;
- JSON-only / raw fallback: rare, risky, deprecated, not yet documented well enough, or too open-ended
  for a visual control.

Do not promote every new Firefox policy into Guided. Guided should remain the short scenario-first
surface. New policies that are valuable but detailed belong in All settings first.

When a policy is promoted into Guided, update all relevant pieces together:

- UI registry placement in `app/services/firefox_policy_ui_registry/overrides.py`.
- Inline editor shape in `app/web/firefox_wizard_shell/inline_editors.py` if the inferred editor is
  not good enough.
- Curated quick controls in `app/web/firefox_manual_policy_controls.py` only for simple, repeatedly
  used controls.
- Guided templates/static bindings if a first-class card or workflow-specific behavior is required.
- All settings search/context copy if users need to jump between Guided and the full catalog.
- Source locale segments under `app/i18n_src/` and generated runtime catalogs under `app/i18n/`.
- Tests in `tests/integration/firefox/test_firefox_wizard_shell.py`,
  `tests/integration/firefox/test_firefox_manual_policy_controls.py`, `tests/unit/firefox/test_firefox_settings_catalog_builders.py`,
  and the relevant `tests/contract/ui/profiles/*` contract.

Record the reason for any important placement choice in the PR description or changelog note. One
line is enough, for example: "Kept `PolicyName` in All settings only because it is a nested
environment-specific control."

### 11. Update the tests that lock the release

Expected test touch points:

- `tests/unit/schema/contracts/test_schema_channels.py`
  Checks constants and labels.
- `tests/integration/schema/test_schema_validation.py`
  Checks bundled metadata, source tag, and a few smoke invariants.
  Prevents old channel strings and source tags from leaking back in.
- `tests/unit/schema/contracts/test_lifecycle_transition_plan.py`
  Verifies added/retained/refreshed/retired rows and immediate-successor rejection cases.
- `tests/unit/schema/contracts/test_retirement_convertibility_preflight.py` and
  `tests/contract/docs/schema/test_firefox_retirement_total_proof.py`
  Verify exact-artifact total-convertibility evidence and strict no-sample proof behavior.
- `tests/integration/db/test_retirement_owner_v1.py` and
  `tests/integration/db/test_retirement_revision_materializer_v1.py`
  Verify candidate-only materialization, backup-gated atomic retirement ownership, rollback, and
  idempotency on the supported database contours. They do not authorize an active migration while
  the source ESR remains supported.
- `tests/contract/ui/localization/test_web_profiles_page.py`
  Verifies the Library remains read-only and visible UI/header text reflects the current supported
  versions.
- `tests/integration/firefox/test_firefox_wizard_shell.py`
  Verifies important new policies land in the intended UI section, bucket, and inline editor shape.
- `tests/integration/firefox/test_firefox_manual_policy_controls.py`
  Verifies curated Guided quick controls stay backed by the active schema.
- `tests/unit/firefox/test_firefox_settings_catalog_builders.py`
  Verifies All settings catalog builders keep stable control metadata for schema-backed areas.
- `tests/contract/ui/profiles/*`
  Verifies route DOM, navigation handoff, Guided shell, assets/i18n, layout, and responsive contracts.
- `tests/integration/locale/test_locale_catalogs.py`
  Verifies locale key parity, placeholder parity, and catalog integrity after schema-related copy changes.
- `tests/contract/ui/localization/test_ui_runtime_i18n_contract.py`
  Verifies runtime-rendered UI keys exist in every active locale catalog.
- `tests/integration/locale/test_locale_visible_english_allowlists.py`
  Verifies non-English locales do not accidentally expose English UI copy outside the technical allowlist.
- `tests/contract/ui/localization/test_ui_locale_glossary.py`
  Verifies glossary, locale-maintenance runbooks, ownership notes, and Mozilla terminology evidence stay current when schema changes add or rename user-facing terms.

If CI has a legacy guard step, update it in `.github/workflows/ci.yml` in the same commit.

### 12. Verification commands

Run the focused checks first:

```bash
make test-firefox-schema-contract
```

`make test-firefox-schema-contract` includes the offline reproducibility contract: it regenerates
all declared targets into a temporary directory from the pinned local source inputs and requires
byte-identical bundled JSON. It does not fetch an upstream schema or contact Mozilla while converting.

If the schema bump changes Firefox/Mozilla terminology or locale-maintenance documentation, also run
`make test-locale-contract`.

Run the lifecycle and conversion evidence that applies to the candidate before a broad gate:

```bash
make verify-firefox-schema-matrix
make verify-firefox-conversion-matrix
make test-db-recovery
```

For a retirement candidate, the reviewed dry-run must complete read-only before any backup or
Alembic activation. Then run `make test-postgres-integration`; its required PostgreSQL service and
recovery evidence are not optional. Do not present a candidate-only materializer test as a current
production migration.

Run `make test-firefox-live` only after the matrix, conversion, database, CIS, locale, and product
contracts pass. Live Firefox evidence is separately pinned per channel and must name the exact
browser/geckodriver versions, checksums, runtime observations, skips, and artifacts. For the current
four-channel matrix, execute the Release 153, ESR 153, ESR 140, and ESR 115 contours independently;
never substitute a floating/latest browser or reuse one channel's binary evidence for another.

For fast visual smoke, run the compact Chromium/Selenium layer:

```bash
make test-ui
```

Run `make test-ui` outside the Codex filesystem/network sandbox from the first attempt. The suite
creates local HTTP sockets and browser-driver processes; a sandboxed trial is expected to fail with
`PermissionError: Operation not permitted` and provides no product signal.

The browser smoke suite intentionally checks only Russian and Simplified Chinese locale rendering,
primary route loading, policies import, and route handoff across the Library, Guided editor, All
settings, and JSON editor. Do not expand it into a deep browser regression matrix; put detailed
behavior in API, static DOM, schema, and locale contract tests.

Then run the full suite:

```bash
make test-release
```

Run `make test-release` outside the sandbox as well. It includes the `browser_ui` marker, so it has
the same local socket/browser requirements as `make test-ui`.

Recommended gate order:

1. `make test-firefox-schema-contract`
2. `make verify-firefox-schema-matrix`, `make verify-firefox-conversion-matrix`, focused offline
   schema-workflow, lifecycle, total-proof, CIS-generation, and placement tests
3. `make test-db-recovery`, then `make test-postgres-integration` for retirement evidence
4. `make test-locale-contract` when any visible version or policy term changed
5. affected documentation/help/search gates and `make docs-release-check` when documentation
   artifacts changed
6. `make lint` and `make typecheck`
7. `make test-ui` outside the sandbox when the UI surface changed
8. `make test-firefox-live` for the independently pinned affected channels
9. `make test-release` outside the sandbox

Do not solve a large-list browser timeout by increasing Selenium waits first. Profile lists validate
many documents and must use the cached validator for their schema channel rather than recompiling a
full JSON Schema per row. Measure the API path before changing test timing. Also remember that locale
initialization can rerender lists: browser tests should reacquire elements after rerenders or perform
one atomic DOM lookup/action instead of retaining stale Selenium handles.

If the schema bump touched product wiring heavily, also review the profiles page manually in the browser and verify:

- schema selector shows only the new supported channels
- wizard defaults to the intended channel
- validation uses the same default channel as the UI
- existing migrated profiles still open and export correctly
- non-English locales still show the current Release / ESR labels and schema-related messages without English fallback islands

## Release Checklist

Before calling the bump finished, confirm all of the following:

- new bundled schema files exist; an old file is removed only when its exact artifact is retired
  by the approved candidate, while every retained supported artifact remains bundled
- official Mozilla support and policy-template release evidence is recorded for every candidate row
- previous/candidate lifecycle matrix names every added, retained, refreshed, and retired line,
  latest ESR, product/default Release roles, and exact immediate successor where retirement occurs
- `app/core/schema_channels.py` matches the complete new Release/ESR support matrix
- schema metadata points to the correct Mozilla tag
- every schema is independently generated from its own manifest-pinned raw sources, byte sizes, and
  SHA-256 digests; no browser patch, copied bundle, or label substitutes for that provenance
- all supported directed conversion pairs have current positive/negative evidence and retain
  explicit preview/apply semantics
- retirement has a complete exact-artifact source-schema-wide proof or is blocked with no mutation;
  profile samples never satisfy this requirement
- a candidate-only retirement artifact is neither installed nor activated while its source ESR is
  supported
- at actual ESR 140 removal, the immutable Alembic revision automatically migrates exact ESR 140
  profiles to ESR 153 in one transaction after backup/preflight gates pass
- application startup verifies the exact Alembic head without writing; legacy rows are changed only
  by the reviewed migration while GET `/profiles` remains read-only
- UI audit completed for newly added/changed policies
- no separate advanced editor route, redirect, template, or bundle was reintroduced
- current Firefox Release / ESR matrix labels are visible in the main header and schema selector
- active locale catalogs are updated for current Release / ESR labels, schema-channel copy, policy names, and schema-related UI strings
- every new schema-backed policy is visible through All settings for supported channels
- important new policies are either intentionally promoted into Guided, intentionally kept in All settings only, or explicitly left JSON-only/raw with a reason
- starter presets reviewed against changed policy semantics
- CIS source/mapping/layer generation has valid evidence for every supported exact schema channel
- tests for schema channels, metadata, lifecycle plans, pairwise conversions, legacy guards, and
  retirement materialization are green
- native backup/restore, rollback, interruption, idempotency, and atomicity evidence is green on
  SQLite and PostgreSQL for any retirement candidate
- fast Chromium/Selenium smoke is green when the bump touches route handoff, editor wiring, import flow, or visible locale copy
- locale parity, runtime i18n, and visible-English allowlist tests are green
- new schema-generated policy-label keys are present in catalog order, all six override catalogs,
  generated segments, and runtime catalogs
- glossary and Pontoon/SUMO evidence are updated when the schema bump introduces or renames Mozilla/Firefox user-facing terms
- All Settings policy/preference help targets and reviewed no-link dispositions match the new
  schema, with no stale target IDs
- changed documentation routes remain present in locale navigation/search artifacts and reveal the
  active topic in the hierarchical tree
- any affected approved User Guide screenshot rows, localized captions, and alt text have been
  regenerated and reviewed without expanding the matrix implicitly
- compact-copy dispositions, contextual-help targets, audience/style review, header parity, and
  collapsed-filter state have been revalidated where the schema bump changed those surfaces
- `README.md` mentions the current supported Release / ESR versions
- the final documentation artifact has been installed with `make docs-install-dev` after the last
  documentation change, ready for the maintainer's `make dev`
- live browser evidence is current and independently pinned/checksummed for every affected channel;
  a release gate covers all four current channels

## Common Failure Modes

- Using the new Firefox version with the old Mozilla `policy-templates` tag.
- Updating UI labels but leaving API, validation, or one concurrently supported ESR on the previous channel.
- Updating English schema labels or README text but leaving non-English catalogs on the previous Release / ESR wording.
- Adding schema-related locale keys only to `en.json`, which creates fallback islands in non-English UI.
- Adding policy-label overrides without adding the key to `app/i18n_src/catalog-order.json`, so the
  build silently omits the label from generated/runtime catalogs.
- Preserving a new Latin technical term in localized labels but updating only the global allowlist
  and forgetting a locale-specific quality allowlist.
- Running `make test-ui` or `make test-release` inside the sandbox and mistaking local-socket denial
  for a product failure.
- Raising browser timeouts when the actual regression is repeated JSON Schema compilation in a
  large profile list.
- Reusing Selenium element handles across asynchronous locale rerenders, producing stale-element
  failures unrelated to product behavior.
- Broadly replacing version numbers inside historical policy compatibility metadata.
- Treating an older but supported ESR as retired, then generating or activating an Alembic revision.
- Regenerating the bundled schema and creating a premature current Alembic migration instead of a
  candidate-only artifact for a future actual retirement.
- Choosing a retirement target from `max()`, a default, a recommendation, tuple order, or a manual
  conversion result instead of the declared immediate successor.
- Treating sample profiles, a passing preview, or a policy-name diff as total convertibility.
- Writing/normalizing a retired channel at runtime or dropping an unconvertible policy silently.
- Accepting SQLite-only recovery evidence when PostgreSQL is required.
- Keeping old filenames or source tags in tests and CI guards.
- Removing a declared supported ESR schema, or leaving a retired schema JSON file in
  `app/schemas/policies/`, which makes the support matrix ambiguous.

When in doubt, verify the bundled JSON first, then the central channel constants, then the migration.
