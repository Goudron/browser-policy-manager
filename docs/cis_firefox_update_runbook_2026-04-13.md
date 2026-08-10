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
./.venv/bin/pytest -q tests/contract/compliance
```

## 8. Documentation drift gate

Treat CIS documentation as part of the benchmark or mapping refresh:

1. Follow `documentation/runbooks/inventory-refresh.md`, especially the CIS benchmark and mapping
   drift gate.
2. Update `docs/architecture/cis-documentation-inventory-0.9.0.{json,md}` and every affected CIS
   DITA recommendation, workflow, mapping, preset/layer/source-attribution, manual-review,
   verification, manifest, UI target, search, and locale peer in the same review.
3. Preserve source-rights boundaries: do not copy or index restricted CIS benchmark expression, and
   do not claim CIS certification, endorsement, conformance, or compliance guarantee.
4. Run the focused CIS documentation inventory/skeleton/manifest contracts before release readiness,
   then run `make docs-release-check` if generated documentation artifacts changed.
5. Reconcile changed recommendation and policy/preference routes with the generated locale
   navigation trees, deterministic search indexes, manifest, and UI target map. A contextual link
   must open the current Administrator/CIS/Firefox owner, reveal the active topic in the hierarchy,
   and never revive the retired standalone API guide.
6. Apply `documentation/runbooks/localization-and-screenshots.md` to every visible CIS label,
   source/review state, caption, and alt text. Runtime UI catalog terms are authoritative; remaining
   technical English requires a live narrow allowlist entry and ordinary prose does not.
7. If a CIS change affects an approved User Guide screenshot scenario, update the 36-row matrix
   first and recapture the affected row for all six locales. Do not add CIS-guide or decorative
   screenshots outside the approved minimal matrix.
8. Run the affected navigation, locale, link, and screenshot contracts before the release gate:

```bash
./.venv/bin/pytest -q -m docs_contract \
  documentation/tests/contract/test_documentation_polish_regression_gates.py \
  documentation/tests/contract/test_locale_anti_anglicism_guard.py \
  documentation/tests/contract/test_user_guide_screenshot_matrix.py \
  documentation/tests/contract/test_all_settings_help_target_map.py
```

9. If the refresh changes compact UI copy or documentation chrome, cite the affected UI-copy
   classification dispositions. Preserve essential and safety/accessibility meaning at the action;
   do not restore routine explanation. Every affected circled-info link has a localized
   manifest-backed owner or explicit reviewed no-link disposition. Recheck audience/style review,
   normalized BPM header parity, one derived BPM product version, and the explicit advanced-filter
   toggle: search, URL/history hydration, results, and clear must not reopen a collapsed panel.

## 9. Release checklist

- `sources.yaml` includes the new entry and keeps prior versions.
- `is_default` points at the intended current version.
- All compliance tests pass.
- Compliance metadata reflects the new version.
- CIS documentation inventory, DITA topics, manifests, search indexes, and locale peers reflect the
  current mappings and boundaries.
- Locale navigation trees, contextual target mappings, and direct-topic reveal point to current
  recommendation and Firefox owner topics.
- Visible terminology follows runtime UI catalogs plus reviewed Pontoon/SUMO evidence, and affected
  approved screenshot rows retain six-locale caption/alt-text parity.
- Any changed compact-copy, contextual-help, header/version, or advanced-filter surface has current
  classification, localized target, audience/style, and collapsed-filter regression evidence.
- Update notes mention the benchmark version and release date.
