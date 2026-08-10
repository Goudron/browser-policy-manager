# BPM 0.9.2 Release Naming And Documentation-Version Audit

Date: 2026-07-17
Status: active audit
Backlog item: `BPM092-M1-07`

## Purpose And Boundary

This audit separates current BPM 0.9.2 sources from the accepted 0.9.0 and 0.9.1 release record.
It also classifies every active documentation-version field as `remove`, `derive`, or
`retain-for-compatibility`. It does not approve a broad text replacement, generated-site edit, or
premature update of user-facing installation guidance.

`pyproject.toml` is the single BPM product-version authority. Documentation may retain a version
field only where a schema or installed-artifact compatibility contract requires it; that field must
be generated from the product version and must never be displayed as an independently owned
documentation version.

## Current 0.9.2 Surfaces

These sources are the active product-release anchors and must agree on BPM 0.9.2:

- `pyproject.toml` declares the project version.
- `app/core/config.py` exposes the runtime version from installed package metadata.
- `CHANGELOG.md` opens with the non-final 0.9.2 landing section.
- `docs/docs-index.md` is headed `BPM 0.9.2 Documentation Index`.
- `docs/architecture/current-system-map.md` identifies 0.9.2 as the current orientation point.
- `docs/architecture/dependency-currency-0.9.2.md`,
  `docs/architecture/product-documentation-release-contract-0.9.2.md`, and
  `docs/bpm_0_9_2_ui_compaction_documentation_coherence_backlog_2026-07-17.md` are active
  release-planning evidence.
- `tests/integration/app/test_current_version_surfaces.py` pins the maintained current-version contract to 0.9.2.

## Active Documentation-Version Fields

| Source and field | Current state | Classification | Owning follow-up | Required disposition |
| --- | --- | --- | --- | --- |
| `documentation/tools/build_docs.py`: localized `labels["version"]` and the `.bpm-docs-version` header paragraph | Displays `BPM 0.9.1 · Documentation 0.9.1`. | `remove` | `BPM092-M9-01`, `BPM092-M9-02` | Remove the documentation-version line and render the same compact BPM header as the main UI. |
| `documentation/assets/theme/bpm-docs.css`: `.bpm-docs-version` selectors | Styles the independent visible version line. | `remove` | `BPM092-M9-01` through `BPM092-M9-03` | Delete once its producer is removed; do not leave hidden duplicate version prose. |
| `documentation/tools/build_docs.py`: navigation `documentation_version` | Writes literal `0.9.1` into each navigation payload. | `derive` | `BPM092-M9-02` | Preserve the schema field only if consumers need it, deriving it from `pyproject.toml` through one documented build-time source. |
| `documentation/assets/theme/bpm-docs-search.js`: navigation identity check | Rejects any payload whose `documentation_version` is not literal `0.9.1`. | `derive` | `BPM092-M9-02`, `BPM092-M9-07` | Read the expected derived artifact value or remove the redundant comparison; no hard-coded release literal may remain. |
| `documentation/tools/build_docs.py`: search-index `versions.documentation_version` | Emits literal `0.9.1` beside `bpm_version`. | `derive` | `BPM092-M9-02` | Retain only as schema compatibility metadata and assign it from the same product-version value as `bpm_version`. |
| `documentation/tools/build_docs.py`: installed manifest `artifact.documentation_version` | Emits literal `0.9.1` beside `bpm_version`. | `derive` | `BPM092-M9-02`, `BPM092-M11-03` | Retain only for installed-artifact compatibility and derive it from the product version during a maintained build. |
| `documentation/config/search-corpus-and-results-0.9.0.json`: required `documentation_version` schema member | Requires the member for search-index compatibility. | `retain-for-compatibility` | `BPM092-M9-02` | Keep the schema requirement, but add/maintain a test that its runtime value equals the derived BPM version. |
| `documentation/config/toolchain-lock.json`: `target_bpm_version` and first-party-plugin version | Stale 0.9.0 toolchain metadata. | `derive` | `BPM092-M9-02`, `BPM092-M11-05` | Replace release literals with build/package-derived metadata or regenerate the lock through its owning toolchain procedure; dependency pins are not upgraded by this change. |
| `documentation/config/artifact-policy.json`: `target_bpm_version`, archive root, and archive filenames | 0.9.1 package naming for a release artifact. | `derive` | `BPM092-M11-03`, `BPM092-M11-05` | Generate/archive-name from the BPM version in the release package process; it is not a visible portal version. |
| `app/documentation/site/**`: generated manifest, navigation payloads, HTML, CSS, and JavaScript copies | Installed 0.9.1 generated artifact. | `retain-for-compatibility` | `BPM092-M9-01` through `BPM092-M11-03` | Never hand-edit. Regenerate and install from corrected maintained sources when the portal work is ready. |
| `documentation/PROJECT_SNAPSHOT.md`: target-version statement | Current documentation-workspace snapshot still says 0.9.1. | `derive` | `BPM092-M11-05` | Regenerate or revise only through its snapshot workflow, taking the product version from the release source. |
| `documentation/src/dita/**`: user/admin prose, `product="bpm-0-9-1"`, approved-ref examples, and release-boundary claims | Active DITA includes 0.9.1 references, many tied to accepted source-install evidence. | `retain-for-compatibility` | `BPM092-M10-01` through `BPM092-M11-01` | Review each user-facing claim against the shipped 0.9.2 support boundary; retain an explicit historical/evidence reference only where its provenance is necessary. Do not mass-replace versioned instructions before that review. |
| `documentation/tests/**`: literal 0.9.1 fixtures and expected artifact values | Tests protect existing 0.9.1 behavior and generated evidence. | `derive` | `BPM092-M9-07`, `BPM092-M11-08` | Replace active-current expectations with product-version derivation; retain fixtures that deliberately validate 0.9.1 provenance. |

## Bounded Update List

The following active sources require a task-owned update; none is changed by this audit:

1. M9 owns removal of the visible documentation version, generated-header parity, and conversion of
   navigation/search/manifest version literals to one derived BPM value.
2. M9 also owns the runtime JavaScript identity check and its contract/browser coverage.
3. M10 and M11 own review of DITA release claims, localized title/prose cleanup, context-help
   updates, snapshot refresh, artifact-policy regeneration, and generated-site installation.
4. M11 owns toolchain/package metadata regeneration and drift procedures that prevent a separate
   documentation version from returning.

## Historical And Provenance Exclusions

The following references are intentionally excluded from active-version cleanup:

- changelog entries below the 0.9.2 landing section;
- `docs/archive/` and earlier versioned backlogs, contracts, audits, inventories, and release
  evidence under `docs/architecture/`;
- versioned documentation configuration, screenshot, browser, source-install, and locale evidence
  whose filename or recorded outcome identifies BPM 0.9.0 or 0.9.1;
- immutable paths below `documentation/evidence/` and generated documentation artifacts until their
  maintained regeneration task runs;
- tests that deliberately assert a prior versioned contract or provenance record.

## Verification And Decision

The audit was bounded to active release anchors, maintained documentation generators and assets,
documentation configuration, DITA source, tests, and installed artifacts; vendor, dependency,
cache, build, and archive trees are not candidates for version replacement.

Use `./.venv/bin/pytest -q tests/integration/app/test_current_version_surfaces.py tests/contract/docs/general/test_docs_index.py` to
verify the current product anchors and indexed audit. M9 must add focused failures for a visible
independent documentation version and for any artifact version that does not derive from the BPM
product version.

No broad repository-wide replacement of `0.9.1` is approved for BPM 0.9.2. Each bounded item
above moves only in the approved task that owns its behavior or evidence.
