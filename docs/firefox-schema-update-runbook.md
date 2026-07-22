# Firefox Schema Update Runbook

This runbook turns the Firefox schema bump into a repeatable release task instead of a one-off migration.

Use it when BPM needs to refresh its supported Firefox Release/ESR schema matrix. A matrix may
contain one Release channel and one or more concurrently supported ESR channels.

Current product surfaces are the profile library, Guided editor, All settings, and JSON editor. Do
not reintroduce a separate advanced editor route, template, redirect, or JavaScript bundle during a
schema bump. In code, the `advanced` section id may still exist as an internal bucket for complex
policy/preference coverage, but it must stay inside Guided review / All settings workflows.

## Inputs You Need Before Editing

Collect the Firefox source tag and one row for every target channel first:

1. Mozilla `policy-templates` tag, for example `v7.10`.
2. Firefox channel type and version, for example `Release 153`, `ESR 153.0`, or `ESR 140.13`.
3. BPM channel string and output filename for that version.
4. Explicit persisted-profile migration destination for every previously supported channel.

Keep one support-and-migration table for the whole change. For example, the Firefox 153 transition
supports a Release channel and two ESR channels:

| Field | Example |
|---|---|
| Firefox 153 source tag | `mozilla-policy-templates-v8.0` |
| Release channel | `release-153` |
| Release version/file | `153.0` / `app/schemas/policies/firefox-release-153.json` |
| Current ESR channel | `esr-153.0` |
| Current ESR version/file | `153.0` / `app/schemas/policies/firefox-esr-153.0.json` |
| Previous ESR channel | `esr-140.13` |
| Previous ESR version/file | `140.13` / `app/schemas/policies/firefox-esr-140.13.json` |
| Migration map | `release-152 → release-153`; `esr-140.12 → esr-140.13` |

If this table is not clear up front, stop and resolve it first. Do not infer an ESR migration from
the highest version: a concurrently supported ESR remains a separate target channel.

## Source Artifacts

BPM currently builds bundled schemas from two Mozilla inputs for every source tag:

1. The versioned `docs/index.md` policy-template document:
   `data/upstream/policy-templates/<mozilla-tag>/policy-templates.md`
2. The Linux example policy snapshot from the official release zip:
   `data/upstream/policy-templates/<mozilla-tag>/linux-policies.json`

Recommended workflow:

1. Download `docs/index.md` from the exact Mozilla release tag named in the support matrix.
2. Download the Mozilla release zip for the target tag.
3. Extract `docs/index.md` and `linux/policies.json` and save them as:
   `data/upstream/policy-templates/<mozilla-tag>/policy-templates.md` and
   `data/upstream/policy-templates/<mozilla-tag>/linux-policies.json`

The release zip is the authoritative source for the example policy payloads used by the converter.

Before downloading, confirm the release metadata from the official Mozilla GitHub release page or
API. The release name must explicitly cover the target Firefox support matrix. Record the zip
checksum in the execution notes so a later regeneration can identify the exact input. The `data/`
tree is a local, Git-ignored converter cache; the committed/reviewed outputs are the bundled schemas
and the code/tests that identify their upstream source.

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

Treat the following as one unit of change:

- `app/core/schema_channels.py`
- `app/services/profile_schema_normalization.py`
- `app/schemas/policies/firefox-*.json`
- `README.md`
- `tools/convert_policies_from_upstream_lib/common.py`
- `tools/convert_policies_from_upstream_lib/cli.py`
- `tools/update_schemas.py`
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
- `tests/test_schema_channels.py`
- `tests/test_schema_validation.py`
- `tests/test_firefox_wizard_shell.py`
- `tests/test_firefox_manual_policy_controls.py`
- `tests/test_firefox_settings_catalog_builders.py`
- `tests/test_web_profiles_page.py`
- `tests/test_no_legacy_schema_refs.py`
- `tests/test_migrations.py`
- `tests/test_ru_locale_quality.py` and
  `tests/fixtures/locale_contracts/visible_english_allowlists.json` when a new policy label contains
  a preserved Latin technical/product term
- `.github/workflows/ci.yml`
- `README.md`
- `alembic/versions/*.py` for the schema-version migration

If one of these still references a retired channel or omits a supported matrix channel, the bump is
not finished.

## Update Sequence

### 1. Update the central channel constants

Start in `app/core/schema_channels.py`.

Update:

- `SUPPORTED_SCHEMA_CHANNELS`
- `DEFAULT_SCHEMA_CHANNEL`
- `DEFAULT_RELEASE_SCHEMA_CHANNEL`
- `SCHEMA_LABELS`
- `SCHEMA_FILENAMES`
- `RAW_SCHEMA_DIRS`

This file is the product-level source of truth. UI, API, loaders, and validation should derive supported channels from here.

### 2. Update converter defaults

Adjust the declarative build targets in:

- `tools/firefox_schema_targets.json`
- `tools/convert_policies_from_upstream_lib/common.py`
- `tools/convert_policies_from_upstream_lib/cli.py`
- `tools/update_schemas.py`

At minimum, update:

- bundled output filenames
- every supported Release / ESR channel string and version
- each channel's Mozilla source tag and versioned input paths
- `--version` choices in `tools/update_schemas.py` if the raw-cache helper is still used

Do not use a broad version-string replacement for historical policy metadata. Existing policies
must keep their real `x-bpm-min-version` and compatibility provenance even when the active channel
moves forward.

## 3. Generate the new bundled schemas

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

Then remove only retired bundled schema files from `app/schemas/policies/`.

Do not keep retired Release / ESR files around. Retain a previous ESR file only when it is named in
the declared current support matrix.

## 4. Sanity-check the generated schemas before wiring them in

Check the metadata directly in the JSON files:

```bash
for schema in app/schemas/policies/firefox-*.json; do
  jq '.["x-bpm-channel"], .["x-bpm-version"], .["x-bpm-source"]' "$schema"
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
- `x-bpm-source` matches the Mozilla release tag you actually used
- `ExtensionSettings.allowed_types` still contains expected upstream values such as `sitepermission`
- every item in the nested-policy completeness checklist is present only on its intended channels

If these checks fail, do not continue into app changes yet.

## 5. Migrate the product to the new channels

After the bundled JSON is correct:

1. Remove old channel references from the product code.
2. Add an Alembic migration that rewrites persisted `profiles.schema_version` values from the old channel strings to the new ones. Its `down_revision` must be the current Alembic head, which may be newer than the previous schema migration.
3. Update `app/services/profile_schema_normalization.py` so explicit runtime backfill maps every
   previously supported channel to its declared destination in the support-and-migration table. This
   covers local databases that do not go through Alembic. Never collapse a supported ESR into a
   different ESR merely because it is older.
4. Run `make backfill-profile-schema-versions` against the target database and confirm the reported `scanned`, `normalized`, and `skipped_invalid` counts. The `/profiles` library route must remain read-only and must not run schema normalization during GET rendering.
5. Update documentation and UI labels to the complete new Release/ESR support matrix.
   In `README.md`, refresh the Supported Firefox Schemas table, examples that carry a `schema_version`, and any prose that names the active Release / ESR versions.
6. Update every active locale catalog when Release / ESR labels, schema-channel copy, policy names,
   or schema-related UI strings change. Edit `app/i18n_src/<locale>/*.json`, then rebuild generated
   `app/i18n/*.json` with `make build-locale-catalogs`. The generated runtime catalogs
   `app/i18n/en.json`, `app/i18n/ru.json`, `app/i18n/de.json`, `app/i18n/zh-CN.json`,
   `app/i18n/fr.json`, and `app/i18n/es-ES.json` must all stay in sync. Cover every active locale
   source segment; follow `docs/locale_update_runbook_2026-06-01.md`, the global glossary, and the
   placeholder rules. If new or changed Mozilla/Firefox terms enter the UI, verify terminology
   against Pontoon/SUMO evidence and update the glossary or locale audit notes before release.
7. Update the legacy guard so the previous release strings are banned outside the explicit migration and normalization exceptions.

### Documentation drift gate

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
7. If the bump changes one of the six approved User Guide screenshot scenarios, update the matrix
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

Important: only the migration, runtime normalizer, and their tests should keep references to the previous channels.

### Schema-generated policy labels

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

## 6. Audit BPM UI impact from the new policy docs

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
- Tests in `tests/test_firefox_wizard_shell.py`,
  `tests/test_firefox_manual_policy_controls.py`, `tests/test_firefox_settings_catalog_builders.py`,
  and the relevant `tests/web_profiles_page/*` contract.

Record the reason for any important placement choice in the PR description or changelog note. One
line is enough, for example: "Kept `PolicyName` in All settings only because it is a nested
environment-specific control."

## 7. Update the tests that lock the release

Expected test touch points:

- `tests/test_schema_channels.py`
  Checks constants and labels.
- `tests/test_schema_validation.py`
  Checks bundled metadata, source tag, and a few smoke invariants.
- `tests/test_no_legacy_schema_refs.py`
  Prevents old channel strings and source tags from leaking back in.
- `tests/test_migrations.py`
  Verifies old DB rows are upgraded to the new schema channel values.
- `tests/test_profile_schema_normalization.py`
  Verifies runtime/library normalization upgrades retired channels according to the declared support
  matrix, preserves every currently supported channel, and leaves invalid profiles untouched.
- `tests/test_web_profiles_page.py`
  Verifies the Library remains read-only and visible UI/header text reflects the current supported
  versions. Startup/backfill normalization belongs in `tests/test_profile_schema_normalization.py`.
- `tests/test_firefox_wizard_shell.py`
  Verifies important new policies land in the intended UI section, bucket, and inline editor shape.
- `tests/test_firefox_manual_policy_controls.py`
  Verifies curated Guided quick controls stay backed by the active schema.
- `tests/test_firefox_settings_catalog_builders.py`
  Verifies All settings catalog builders keep stable control metadata for schema-backed areas.
- `tests/web_profiles_page/*`
  Verifies route DOM, navigation handoff, Guided shell, assets/i18n, layout, and responsive contracts.
- `tests/test_locale_catalogs.py`
  Verifies locale key parity, placeholder parity, and catalog integrity after schema-related copy changes.
- `tests/test_ui_runtime_i18n_contract.py`
  Verifies runtime-rendered UI keys exist in every active locale catalog.
- `tests/test_locale_visible_english_allowlists.py`
  Verifies non-English locales do not accidentally expose English UI copy outside the technical allowlist.
- `tests/test_ui_locale_glossary.py`
  Verifies glossary, locale-maintenance runbooks, ownership notes, and Mozilla terminology evidence stay current when schema changes add or rename user-facing terms.

If CI has a legacy guard step, update it in `.github/workflows/ci.yml` in the same commit.

## 8. Verification commands

Run the focused checks first:

```bash
make test-firefox-schema-contract
```

If the schema bump changes Firefox/Mozilla terminology or locale-maintenance documentation, also run
`make test-locale-contract`.

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
2. focused converter, schema-manager, CIS-generation, and placement tests
3. `make test-locale-contract` when any visible version or policy term changed
4. `make lint` and `make typecheck`
5. `make test-ui` outside the sandbox
6. `make test-release` outside the sandbox

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

- new bundled schema files exist and old ones are removed
- `app/core/schema_channels.py` matches the complete new Release/ESR support matrix
- schema metadata points to the correct Mozilla tag
- Alembic migration upgrades stored `schema_version` values
- runtime profile schema normalization maps each retired channel to its declared destination and
  leaves every currently supported Release/ESR channel unchanged
- application startup or the explicit backfill normalizes legacy rows before normal Library use,
  while GET `/profiles` remains read-only
- UI audit completed for newly added/changed policies
- no separate advanced editor route, redirect, template, or bundle was reintroduced
- current Firefox Release / ESR matrix labels are visible in the main header and schema selector
- active locale catalogs are updated for current Release / ESR labels, schema-channel copy, policy names, and schema-related UI strings
- every new schema-backed policy is visible through All settings for supported channels
- important new policies are either intentionally promoted into Guided, intentionally kept in All settings only, or explicitly left JSON-only/raw with a reason
- starter presets reviewed against changed policy semantics
- tests for schema channels, metadata, legacy guards, and migrations are green
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
- Regenerating the bundled schema but forgetting the Alembic migration.
- Keeping old filenames or source tags in tests and CI guards.
- Removing a declared supported ESR schema, or leaving a retired schema JSON file in
  `app/schemas/policies/`, which makes the support matrix ambiguous.

When in doubt, verify the bundled JSON first, then the central channel constants, then the migration.
