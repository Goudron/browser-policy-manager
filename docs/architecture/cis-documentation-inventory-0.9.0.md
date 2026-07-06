# BPM 0.9.0 CIS Documentation Inventory

Date: 2026-06-21

Backlog item: `BPM090-M2-04`

Machine-readable inventory: `docs/architecture/cis-documentation-inventory-0.9.0.json`

Regeneration command:

```bash
./.venv/bin/python tools/build_cis_documentation_inventory.py
```

Drift-check command:

```bash
./.venv/bin/python tools/build_cis_documentation_inventory.py --check
```

## Benchmark And Provenance Boundary

The shipped registry contains one imported benchmark source:

- benchmark: `CIS Mozilla Firefox ESR GPO Benchmark`;
- benchmark ID: `cis-firefox-esr-gpo`;
- upstream version: `1.0.0`;
- exact release date: `2024-07-19`, confirmed from the official PDF;
- tested-by-CIS baseline: Mozilla Firefox 115.10 ESR on Windows 11 23H2;
- source license recorded by BPM: `CC-BY-NC-SA-4.0` plus CIS non-member product terms;
- source file: `firefox_esr_gpo_1_0_0.yaml`;
- mapping file: `mappings.yaml`.

The registered PDF is present as local source material, but this inventory does not read, hash,
copy, or republish its contents. `source_content_redistribution_reviewed=false` remains a release
guard until the provenance review in `BPM090-M2-09`. The guide must not claim CIS certification,
endorsement, or independently verified compliance.

## Recommendation Coverage

The curated source contains 55 scored, automated recommendation records:

| Dimension | Counts |
| --- | --- |
| Levels | 51 Level 1; 4 Level 2 |
| Mapping status | 43 `mapped`; 10 `preference_mapped`; 1 `needs_research`; 1 `deprecated_or_removed` |
| Mapping confidence | 48 high; 7 medium |
| Targets | 53 total: 43 policy targets and 10 preference targets |
| Schema compatibility | 53 valid targets on `esr-140.12`; 53 valid targets on `release-152` |
| Publication disposition | 53 planned DITA topics; 2 provenance-only non-publishable records |

Every recommendation has a stable `provenance_id`, source section, level, category, assessment,
mapping status, confidence, source-title fingerprint, note-presence flags, generated-layer
membership, and target metadata. The inventory deliberately stores only a SHA-256 fingerprint of
the source title rather than duplicating benchmark prose.

Recommendations with `mapped` or `preference_mapped` status receive stable logical DITA IDs in the
form `cis-rec-{dotted-id-with-hyphens}`. The two other records are explicit provenance-only entries:

- `1.1.5.3` — `needs_research`; no approved current Firefox target;
- `1.1.12.1` — `deprecated_or_removed`; no modern supported Firefox target.

They have no publishable DITA topic ID until a later provenance/mapping decision changes their
status. This prevents an unsupported setting or unreviewed source statement from silently becoming
product guidance.

## Target And Cross-Link Contract

Each mapping target records:

- `policy` or `preference` kind;
- complete nested target path and effective top-level target ID;
- expected value and merge rule;
- per-channel compatibility;
- live BPM `policy:*` or `known-preference:*` UI target;
- stable `fx-policy-*` or `fx-pref-*` documentation target from the Firefox documentation
  inventory.

This makes policy/preference links testable without copying Firefox or CIS prose. Any mapping target
that loses its Firefox documentation target makes the CIS inventory build fail.

## Generated Layer Coverage

| Layer | Channel | Applied recommendations | Top-level policy keys |
| --- | --- | ---: | ---: |
| `cis-l1.esr-140.12` | `esr-140.12` | 49 | 30 |
| `cis-l1.release-152` | `release-152` | 49 | 30 |
| `cis-l2.esr-140.12` | `esr-140.12` | 53 | 33 |
| `cis-l2.release-152` | `release-152` | 53 | 33 |

Level 2 includes all applicable Level 1 recommendations plus four Level 2 recommendations. The two
provenance-only recommendations have no generated target and therefore appear in no generated
layer. Each maintained layer record includes its committed file path and a deterministic document
fingerprint.

## Presets, Merge Decisions, And Manual Review

The Guided starter catalog exposes five starting states:

- `blank`;
- `keep_current`;
- `basic_corporate`;
- `classroom_kiosk`;
- `soc_hard`.

For each starter the inventory records `none`, `cis_l1`, and `cis_l2` variants on both supported
schema channels, including top-level policy count, decision count, summary, and review-required
count without duplicating the full generated policy documents.

The merge model exposes six decision types: `added_from_cis`, `already_satisfied`,
`cis_replaced_base`, `kept_base_only`, `kept_base_stricter`, and `manual_review_kept_base`. Target
metadata currently uses eight merge-rule families. Nine explicit paths require manual review,
covering enterprise update governance, proxy routing/locking, and conflicts between forensic
retention and clearing sessions, history, or form data.

BPM records merge decisions and manual-review requirements but currently has no separate persisted
CIS exception or waiver model. The guide must not imply that acknowledging a review item creates an
auditable exception record.

## Audit Result

- All 55 shipped recommendations have a unique provenance record.
- All 53 mapped recommendations have unique planned DITA topic IDs and tested Firefox
  policy/preference cross-links.
- The two recommendations without supported targets are explicitly non-publishable provenance-only
  records rather than silent coverage gaps.
- Both levels, both schema channels, four committed generated layers, five starter states, merge
  decisions, merge rules, manual-review paths, and the missing exception model have bounded
  documentation ownership.
- The deterministic builder fails on dirty CIS source validation, unknown target cross-links,
  duplicate IDs, changed sources/mappings/layers/presets, or provenance drift.
- Recommendation prose, localized rationale, screenshots, and final publication rights remain
  later approved tasks; this inventory does not authorize copying the source PDF.
