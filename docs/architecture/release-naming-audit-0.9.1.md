# BPM 0.9.1 Release Naming Audit

Date: 2026-07-06
Status: active audit
Backlog item: `BPM091-M1-07`

This audit bounds BPM 0.9.1 release-name cleanup. It records current-version
surfaces, active follow-up updates, and references that must stay as historical
or provenance records.

## Current 0.9.1 Surfaces

These surfaces already name the active target as BPM 0.9.1:

- `pyproject.toml` declares project version `0.9.1`.
- `CHANGELOG.md` opens the current release entry with `## 0.9.1`.
- `docs/docs-index.md` is headed `BPM 0.9.1 Documentation Index`.
- `docs/architecture/current-system-map.md` names BPM 0.9.1 as the current
  orientation point.
- `docs/architecture/dependency-currency-0.9.1.md` records the dependency
  currency decision for this release.
- `docs/architecture/product-documentation-release-contract-0.9.1.md` records
  the 0.9.1 documentation release gates.
- `docs/bpm_0_9_1_documentation_completion_backlog_2026-07-06.md` is the active
  backlog for this release.
- `tests/integration/app/test_current_version_surfaces.py` pins the maintained version-surface
  contract to `0.9.1`.

## Bounded Update List

These active documentation-workspace surfaces still mention 0.9.0 and must be
reviewed or refreshed only in the relevant 0.9.1 documentation tasks:

- `documentation/PROJECT_SNAPSHOT.md` is still a generated snapshot for the
  completed BPM 0.9.0 documentation workspace. Refresh it after the 0.9.1
  documentation baseline and release gates are established.
- `documentation/config/artifact-policy.json` still names the 0.9.0 release
  archive/root. Update it only when the 0.9.1 documentation package policy or
  release extraction gate is implemented.
- `documentation/config/toolchain-lock.json` still records
  `target_bpm_version` and first-party plugin version as `0.9.0`. Keep the
  dependency pins from the 0.9.1 dependency-currency decision; refresh this
  metadata only through a documentation toolchain/package task.
- `documentation/config/requirements.lock` starts with a 0.9.0 environment
  comment. Refresh the label when documentation test-environment metadata is
  next regenerated or reviewed.
- `app/documentation/site/manifest.json` and
  `app/documentation/site/ui-target-map.json` are the installed generated
  documentation artifact for 0.9.0. Do not hand-edit them; regenerate/install
  the site through the documentation build pipeline when the 0.9.1 content and
  UI work is ready.

## Historical And Provenance Exclusions

The following 0.9.0 references are intentionally excluded from this cleanup:

- `CHANGELOG.md` entries below `## 0.9.1`; changelog history is versioned
  release history and must not be renamed.
- `docs/archive/`; archive files are point-in-time material and do not steer
  current implementation without a fresh review.
- Earlier backlog files such as
  `docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md`.
- Accepted 0.9.0 architecture contracts, inventories, provenance matrices,
  and audit files under `docs/architecture/`, including files whose names end
  in `-0.9.0.md` or `-0.9.0.json`.
- Documentation configuration inventories and target maps whose filenames
  encode 0.9.0 provenance, for example
  `documentation/config/firefox-policy-context-targets-0.9.0.json`.
- Tests that intentionally assert historical 0.9.0 contracts, inventories, or
  generated-artifact provenance.

## Decision

No broad repository-wide replacement of `0.9.0` is approved for BPM 0.9.1.
Only the bounded update list above may move forward, and each item must be
changed by the backlog task that owns the corresponding documentation surface.
