# BPM 0.9.4 documentation-build baseline

Recorded: 2026-08-05.  This is a maintainer record for `BPM094-M7-05`, not
publishable product documentation.

## Proven artifact state

- Product and generated-artifact version: `0.9.4`.
- Locales: `en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`.
- Published-site and installed-dev-site source fingerprint:
  `3fb69bdeb11e35817115e8aee627b12e6174616ffa9f86ae2af928823242d047`.
- `documentation/build/site/manifest.json` and
  `app/documentation/site/manifest.json` have the complete locale matrix;
  the installed English portal header displays `v0.9.4`.
- `app/documentation/.site-dev-install.json` identifies BPM `0.9.4`, source
  `documentation/build/site`, and installed site `app/documentation/site`.
- `documentation/build/pdf/pdf-build-manifest.json` identifies BPM `0.9.4`.
- Package: `documentation/dist/bpm-documentation-0.9.4.tar.gz`, SHA-256
  `2f1e593810f3f5afe8feababf99669b35071a8d926606a6294e16ae145908bda`.

## Executed evidence

| Command | Result |
| --- | --- |
| `make docs-reproducibility-check` | Two independent six-locale trees and SHA-256 comparison completed; 1088 files. |
| `make docs-pdf-build` | 24/24 locale-guide build/render units, manifest validation, atomic promotion; exit 0. |
| `make docs-pdf-verify` | Passed. |
| `make docs-pdf-reproducibility` | Independent candidate comparison passed for 13 files; exit 0. |
| `make docs-package` | `bpm-documentation-0.9.4.tar.gz` built and atomically promoted; exit 0. |
| `make docs-package-verify` | Passed with the package SHA-256 recorded above. |
| `make docs-install-dev` | Six-locale site built, validated, atomically published and installed; exit 0. |
| Focused artifact/PDF contract suite | 8 passed. |

`make test-docs` was also run.  It is not a clean baseline: it fails in stale
tests that inspect implementation text or façade-only globals removed by
`BPM094-M7-01` (for example PDF functions now owned by `buildlib/pdf.py`).
The failures do not reject generated artifacts; their classification and
consolidation belong to M8.

## Deliberately unchanged M11 baseline defects

M11 is responsible for correcting these known PDF/documentation defects and
must retain this record as its before-state:

- figures lack captions and numbering;
- UI element names are not consistently distinguished in prose;
- note/warning labels are not consistently bold;
- covers lack the required page count and localized product-footer copyright;
- tables of contents lack printed page starts and active section links;
- non-cover PDF pages lack centered printed page numbers;
- placeholder/incomplete explanations (including locale-selection behaviour)
  remain to be replaced by factual text;
- import and export examples must consistently show the complete
  `{"policies": {...}}` document.

This task changes only technical version/artifact contracts and records the
baseline.  It makes no user-facing DITA, UI, PDF-layout, or Ruspell change.
