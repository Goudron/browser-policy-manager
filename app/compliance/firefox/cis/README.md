# CIS Firefox Compliance Data

This directory stores versioned CIS Firefox benchmark source data and mapping metadata.

English is the canonical language for these files. CIS recommendation data must be curated from an official CIS PDF downloaded from the CIS website, CIS Portal, or CIS WorkBench. Third-party mirrors may be used for discovery only and must not be treated as authoritative source material.

The initial baseline target is:

- `CIS Mozilla Firefox ESR GPO Benchmark`
- version `1.0.0`
- release window `2024-07`

The exact release date is confirmed from the official CIS PDF as `2024-07-19`.

## Files

- `sources.yaml`: upstream benchmark identity and import metadata.
- `firefox_esr_gpo_1_0_0.yaml`: curated source recommendation records.
- `mappings.yaml`: recommendation-to-policy/preference mapping metadata.
- `schema.yaml`: documentation for the expected YAML contracts.
- `NOTICE.md`: CIS source licensing boundary for benchmark-derived data.

The source recommendation file contains the curated recommendation skeleton from the official CIS PDF. The PDF itself is treated as local source material and should not be committed unless the licensing boundary is explicitly revisited.

## Update Workflow

Follow the update runbook in `docs/cis_firefox_update_runbook_2026-04-13.md`. Keep older benchmark files in the repo and register new versions in `sources.yaml` with `is_default` set on the current version.

## Licensing Boundary

Do not copy long CIS prose into this repository unless legal/product approval explicitly allows it. Store recommendation ids, titles when allowed, short internal summaries, expected states, mapping metadata, and source attribution.

CIS PDF Benchmarks are not MPL-2.0 project code. They are handled under the CIS Non-Member Product terms and the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license. Keep official PDFs out of Git by default; see `NOTICE.md`.
