# Firefox Schema Update Runbook

This runbook turns the Firefox schema bump into a repeatable release task instead of a one-off migration.

Use it when BPM needs to move from one supported Firefox Release / ESR pair to the next one.

## Inputs You Need Before Editing

Collect these four values first:

1. Mozilla `policy-templates` tag, for example `v7.10`.
2. Firefox Release version, for example `150.0`.
3. Firefox ESR version, for example `140.10`.
4. BPM channel strings, for example `release-150` and `esr-140.10`.

Keep one mapping table for the whole change:

| Field | Example |
|---|---|
| Mozilla source tag | `mozilla-policy-templates-v7.10` |
| Release channel | `release-150` |
| Release version | `150.0` |
| Release file | `app/schemas/policies/firefox-release-150.json` |
| ESR channel | `esr-140.10` |
| ESR version | `140.10` |
| ESR file | `app/schemas/policies/firefox-esr-140.10.json` |

If this table is not clear up front, stop and resolve it first. Most migration mistakes come from mixing versions from two different upstream snapshots.

## Source Artifacts

BPM currently builds bundled schemas from two Mozilla inputs:

1. The rendered docs page:
   `data/upstream/policy-templates/policy-templates.html`
2. The Linux example policy snapshot from the official release zip:
   `data/upstream/policy-templates/<mozilla-tag>/linux-policies.json`

Recommended workflow:

1. Download the latest docs page from `https://mozilla.github.io/policy-templates/`.
2. Download the Mozilla release zip for the target tag.
3. Extract `linux/policies.json` from the zip and save it as:
   `data/upstream/policy-templates/<mozilla-tag>/linux-policies.json`

The release zip is the authoritative source for the example policy payloads used by the converter.

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
- Guided editor templates and static bindings when a new policy deserves a first-class card
- `tests/test_schema_channels.py`
- `tests/test_schema_validation.py`
- `tests/test_firefox_wizard_shell.py`
- `tests/test_web_profiles_page.py`
- `tests/test_no_legacy_schema_refs.py`
- `tests/test_migrations.py`
- `.github/workflows/ci.yml`
- `README.md`
- `alembic/versions/*.py` for the schema-version migration

If one of these still references the previous Release / ESR pair, the bump is not finished.

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

Adjust the hardcoded defaults in:

- `tools/convert_policies_from_upstream_lib/common.py`
- `tools/convert_policies_from_upstream_lib/cli.py`
- `tools/update_schemas.py`

At minimum, update:

- bundled output filenames
- default Release / ESR channel strings
- default Release / ESR version strings
- default Mozilla source tag
- `--version` choices in `tools/update_schemas.py` if the raw-cache helper is still used

## 3. Generate the new bundled schemas

Run the converter explicitly with all version flags. Even if defaults are already updated, explicit arguments make the release step easier to audit.

Example:

```bash
python tools/convert_policies_from_upstream.py \
  --input data/upstream/policy-templates/policy-templates.html \
  --linux-policies-input data/upstream/policy-templates/v7.10/linux-policies.json \
  --release-channel release-150 \
  --release-version 150.0 \
  --release-output app/schemas/policies/firefox-release-150.json \
  --esr-channel esr-140.10 \
  --esr-version 140.10 \
  --esr-output app/schemas/policies/firefox-esr-140.10.json \
  --source-tag mozilla-policy-templates-v7.10
```

Then remove the previous bundled schema files from `app/schemas/policies/`.

Do not keep the old Release / ESR files around unless the product explicitly supports multiple historical channels.

## 4. Sanity-check the generated schemas before wiring them in

Check the metadata directly in the JSON files:

```bash
  jq '.["x-bpm-channel"], .["x-bpm-version"], .["x-bpm-source"]' \
  app/schemas/policies/firefox-release-150.json

jq '.["x-bpm-channel"], .["x-bpm-version"], .["x-bpm-source"]' \
  app/schemas/policies/firefox-esr-140.10.json

jq '.properties.ExtensionSettings.additionalProperties.properties.allowed_types.items.enum' \
  app/schemas/policies/firefox-release-150.json
```

Minimum expectations:

- Release channel matches the intended `release-*` value.
- ESR channel matches the intended `esr-*` value.
- versions match the intended Firefox numbers exactly
- `x-bpm-source` matches the Mozilla release tag you actually used
- `ExtensionSettings.allowed_types` still contains expected upstream values such as `sitepermission`

If these checks fail, do not continue into app changes yet.

## 5. Migrate the product to the new channels

After the bundled JSON is correct:

1. Remove old channel references from the product code.
2. Add an Alembic migration that rewrites persisted `profiles.schema_version` values from the old channel strings to the new ones.
3. Update `app/services/profile_schema_normalization.py` so library/runtime normalization also maps the previous Release / ESR channels to the new supported channels. This covers already-open local databases when the user opens the profile library, not only databases that go through Alembic.
4. Confirm the `/profiles` library route runs the profile schema normalizer before returning the library shell, so the first profile-list refresh sees current schema channels.
5. Update documentation and UI labels to the new Release / ESR pair.
   In `README.md`, refresh the Supported Firefox Schemas table, examples that carry a `schema_version`, and any prose that names the active Release / ESR versions.
6. Update the legacy guard so the previous release strings are banned outside the explicit migration and normalization exceptions.

Important: only the migration, runtime normalizer, and their tests should keep references to the previous channels.

## 6. Audit BPM UI impact from the new policy docs

Do this as a deliberate product pass, not as a side effect of schema generation:

1. Compare old and new bundled schemas and list added, removed, and structurally changed policies.
2. Check whether each new policy should stay in All settings only, become a mapped schema-shell item, or get a first-class Guided editor control/card.
3. Confirm every new supported policy appears in All settings for its channel and is absent from unsupported channels.
4. Confirm the product header/subtitle and schema selector show the new Firefox Release / ESR labels.
5. Review Firefox policy docs for changed semantics in policies already used by BPM starter presets, CIS overlays, and quick controls.
6. Update starter presets only when the new policy semantics clearly improve an existing BPM scenario without surprising users or breaking compatibility.
7. Add tests that lock the placement decision for important new policies.

For placement, prefer:

- first-class Guided editor card: common administrator workflow, high operational value, and safe enough to expose without raw JSON;
- mapped schema-shell item in All settings / relevant guided area: useful but detailed, or needs per-site/per-domain tuning;
- raw/unmapped: rare, risky, deprecated, or not yet documented well enough for a visual control.

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
  Verifies runtime/library normalization upgrades previous channels to the current pair and leaves invalid profiles untouched.
- `tests/test_web_profiles_page.py`
  Verifies opening `/profiles` invokes runtime normalization before the library loads profile data, and visible UI/header text reflects the current supported versions.
- `tests/test_firefox_wizard_shell.py`
  Verifies important new policies land in the intended UI section, bucket, and inline editor shape.

If CI has a legacy guard step, update it in `.github/workflows/ci.yml` in the same commit.

## 8. Verification commands

Run the focused checks first:

```bash
.venv/bin/pytest -q \
  tests/test_schema_channels.py \
  tests/test_schema_validation.py \
  tests/test_no_legacy_schema_refs.py \
  tests/test_migrations.py \
  tests/test_profile_schema_normalization.py \
  tests/test_firefox_wizard_shell.py \
  tests/test_web_profiles_page.py
```

Then run the full suite:

```bash
.venv/bin/pytest -q
```

If the schema bump touched product wiring heavily, also review the profiles page manually in the browser and verify:

- schema selector shows only the new supported channels
- wizard defaults to the intended channel
- validation uses the same default channel as the UI
- existing migrated profiles still open and export correctly

## Release Checklist

Before calling the bump finished, confirm all of the following:

- new bundled schema files exist and old ones are removed
- `app/core/schema_channels.py` matches the new release pair
- schema metadata points to the correct Mozilla tag
- Alembic migration upgrades stored `schema_version` values
- runtime profile schema normalization maps the previous Release / ESR pair to the new channels
- opening `/profiles` runs the normalizer before library data is loaded
- UI audit completed for newly added/changed policies
- current Firefox Release / ESR labels are visible in the main header and schema selector
- important new policies are either intentionally mapped into Guided/All settings or explicitly left raw with a reason
- starter presets reviewed against changed policy semantics
- tests for schema channels, metadata, legacy guards, and migrations are green
- `README.md` mentions the current supported Release / ESR versions

## Common Failure Modes

- Using the new Firefox version with the old Mozilla `policy-templates` tag.
- Updating UI labels but leaving API or validation defaults on the previous channel.
- Regenerating the bundled schema but forgetting the Alembic migration.
- Keeping old filenames or source tags in tests and CI guards.
- Leaving the previous schema JSON files in `app/schemas/policies/`, which makes it look like both are supported.

When in doubt, verify the bundled JSON first, then the central channel constants, then the migration.
