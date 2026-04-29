# CIS Firefox Update Runbook

Goal: refresh CIS Firefox benchmark data while keeping older versions available for existing profiles.

This runbook assumes English source files and official CIS PDF as the only authoritative input.

## 1. Prepare inputs

1. Download the official CIS PDF from the CIS website, CIS Portal, or CIS WorkBench.
2. Store the PDF under `app/compliance/firefox/cis/source_materials/` locally.
3. Do not commit the PDF unless legal approves redistribution.

## 2. Add new source files

1. Create a new source YAML file, for example:
   - `app/compliance/firefox/cis/firefox_esr_gpo_1_1_0.yaml`
2. Copy the previous version and update:
   - `benchmark.upstream_version`
   - `benchmark.release_date`
   - recommendation list, mapping_status values, and expected_state details
3. Create a new mapping file if the structure changes materially, or keep `mappings.yaml` if only incremental changes are needed.

Keep old versions in the repo. Do not overwrite previous benchmark files.

## 3. Register the version in sources.yaml

Add a new benchmark entry to `app/compliance/firefox/cis/sources.yaml`:

- `id`: stable benchmark id, for example `cis-firefox-esr-gpo`
- `upstream_version`: new version
- `source_file`: new source YAML
- `mapping_file`: new mapping YAML
- `official_source_status`: `imported` after review
- `is_default`: `true` for the current version, `false` for older versions

## 4. Validate sources and mappings

Run validation:

```
./.venv/bin/python tools/cis_firefox/validate_sources.py
./.venv/bin/python tools/cis_firefox/coverage_report.py
```

## 5. Diff against the previous version

```
./.venv/bin/python tools/cis_firefox/diff_benchmarks.py \
  --from cis-firefox-esr-gpo@1.0.0 \
  --to cis-firefox-esr-gpo@1.1.0
```

Include `--json` for machine-readable output or `--validate-targets` to scan for invalid policy targets.

## 6. Regenerate CIS layers

```
./.venv/bin/python tools/cis_firefox/generate_presets.py --check
./.venv/bin/python tools/cis_firefox/generate_presets.py
```

## 7. Run tests

```
./.venv/bin/pytest -q tests/compliance
```

## 8. Release checklist

- `sources.yaml` includes the new entry and keeps prior versions.
- `is_default` points at the intended current version.
- All compliance tests pass.
- Compliance metadata reflects the new version.
- Update notes mention the benchmark version and release date.
