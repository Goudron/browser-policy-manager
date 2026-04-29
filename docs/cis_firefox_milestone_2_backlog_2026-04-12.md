# CIS Firefox Milestone 2 Backlog

Date: 2026-04-12

Milestone 2 goal: convert curated CIS Firefox source data into deterministic, schema-valid Firefox policy layer artifacts.

## Current Status

- CIS-M2-001: completed.
- CIS-M2-002: completed.
- CIS-M2-003: completed.
- CIS-M2-004: completed.
- CIS-M2-005: completed.
- CIS-M2-006: pending for the next milestone handoff.

## Generated Layers

Generated artifacts live under:

```text
app/compliance/firefox/cis/generated/
```

Current files:

- `cis_l1.esr-140.9.json`
- `cis_l2.esr-140.9.json`
- `cis_l1.release-149.json`
- `cis_l2.release-149.json`

Level semantics:

- CIS Level 1 includes only `level: 1` recommendations.
- CIS Level 2 includes both `level: 1` and `level: 2` recommendations.

Current generated coverage:

- L1 source recommendations: 51
- L1 generated recommendations: 49
- L2 source recommendations: 55
- L2 generated recommendations: 53

Two CIS recommendations are intentionally not generated yet:

- `1.1.5.3`: CIS GPO uses `SanitizeOnShutdown:Downloads`, but supported Mozilla policy schemas do not expose a `Downloads` member under `SanitizeOnShutdown`.
- `1.1.12.1`: CIS Flash recommendation targets `FlashPlugin`, which is absent from supported Firefox ESR 140.9 and Release 149 schemas.

## Commands

Validate without writing:

```bash
.venv/bin/python tools/cis_firefox/generate_presets.py --check
```

Regenerate artifacts:

```bash
.venv/bin/python tools/cis_firefox/generate_presets.py
```

Coverage report:

```bash
.venv/bin/python tools/cis_firefox/coverage_report.py
```

## Backlog Items

### CIS-M2-001: Add Layer Generator

Create a backend generator that converts CIS mappings into Firefox policy-layer documents.

Done when:

- generator reads curated source YAML and mappings;
- generator supports Level 1 and Level 2;
- Level 2 includes Level 1;
- generator supports nested policy paths and preference targets.

### CIS-M2-002: Add Schema Validation

Validate generated policy layers against supported Firefox schemas.

Done when:

- generated ESR layer validates against `esr-140.9`;
- generated Release layer validates against `release-149`;
- invalid schema targets are not silently emitted.

### CIS-M2-003: Add Deterministic Artifacts

Write generated JSON layer files into the repository.

Done when:

- generated file names include CIS level and schema channel;
- output is deterministic;
- tests fail when committed generated files drift from generator output.

### CIS-M2-004: Add CLI

Add a command-line wrapper for validation and regeneration.

Done when:

- `generate_presets.py --check` validates all layers without writing;
- `generate_presets.py` writes all generated files;
- command output is compact and scriptable.

### CIS-M2-005: Add Tests

Add unit tests for Level semantics, schema validation, generated policy values, and committed artifact freshness.

Done when:

- tests prove Level 2 includes Level 1;
- tests validate all generated layers;
- tests check representative policy and preference values;
- tests check committed generated JSON matches current generator output.

### CIS-M2-006: Prepare Merge Handoff

Document inputs needed by the merge engine.

Done when:

- generated layers include enough metadata for merge decisions;
- non-generated recommendations remain visible through source/mapping coverage;
- operational conflict candidates are documented for Milestone 3.

## Merge Handoff Notes

Milestone 3 should treat these policy areas carefully:

- update governance: `AppAutoUpdate`, `BackgroundAppUpdate`, `DisableAppUpdate`, `DisableSystemAddonUpdate`;
- proxy governance: `Proxy.Mode`, `Proxy.Locked`;
- authentication: `Authentication.NTLM`;
- deprecated preference mappings under `Preferences`;
- unsupported traceability gaps: Flash and download history cleanup.

