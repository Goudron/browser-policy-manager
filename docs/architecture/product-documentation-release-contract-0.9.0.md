# BPM 0.9.0 Product Documentation Release Contract

Date: 2026-06-20

Backlog item: `BPM090-M1-05`

## Purpose

This contract defines the product documentation outcomes that block BPM 0.9.0. It is the
maintained release checklist for the documentation portal epic, not a statement that planned
features already exist.

The administrator guide scope is represented by the Administrator/DevOps Guide gates for source
deployment, operations, updates, API integration, and production-readiness boundaries.

BPM currently has one project maintainer. The owner column therefore names both the accountable
maintainer and the functional ownership area that must be reviewed. Ownership may be delegated
later, but no gate becomes ownerless.

Commands marked **planned** are normative command names that later backlog milestones must add.
A missing planned command is a failed release gate, not permission to verify the outcome manually
and ship anyway. Generated reports are release evidence and must remain outside hand-edited DITA
source.

## Blocking Gates

Every gate below is release-blocking. `Closed` means the recorded command passed for completed work;
`Open` means implementation or verification is still required.

| Gate | Required outcome | Accountable owner | Required evidence | Verification command | State |
| --- | --- | --- | --- | --- | --- |
| `DOC090-G01` | Package, runtime, active metadata, and version tests agree on BPM 0.9.0. | Project maintainer — release metadata | Version contract test and active release surfaces. | `pytest -q tests/test_current_version_surfaces.py tests/test_bootstrap_config.py::test_settings_version_matches_pyproject` | Closed |
| `DOC090-G02` | README and changelog identify 0.9.0 as in progress without claiming the portal is shipped. | Project maintainer — release documentation | Explicit README portal-status placeholder and in-progress changelog entry. | `pytest -q tests/test_current_version_surfaces.py tests/test_locale_matrix.py::test_readme_documents_target_and_active_locale_sets` | Closed |
| `DOC090-G03` | Reproducible DITA validation and static publishing build all five guide maps from hand-edited source. | Project maintainer — documentation platform | Clean-build report, pinned toolchain, validated maps, manifest, and generated output inventory. | **Planned:** `make docs-build` and `make test-docs-contract` | Open |
| `DOC090-G04` | The case-oriented User Guide covers every shipped BPM user capability and troubleshooting path. | Project maintainer — user documentation | Closed capability-to-topic matrix and built User Guide. | **Planned:** `make test-docs-contract` | Open |
| `DOC090-G05` | The Firefox Policy Guide covers every policy in the supported Release/ESR schema union with valid examples and provenance. | Project maintainer — Firefox policy documentation | Policy inventory parity, schema-valid examples, channel conditions, and source metadata. | **Planned:** `make test-docs-contract`; existing schema baseline: `make test-firefox-schema-contract` | Open |
| `DOC090-G06` | The CIS Settings Guide covers every shipped recommendation, mapping, manual-review state, supported level, and provenance constraint. | Project maintainer — CIS documentation | CIS coverage matrix, generated mapping checks, disclaimers, and source/version metadata. | **Planned:** `make test-docs-contract`; existing CIS baseline: `pytest -q tests/compliance` | Open |
| `DOC090-G07` | The API Integration Guide covers every current public operation, limitation, error family, and executable integration scenario without inventing new guarantees. | Project maintainer — API documentation | OpenAPI-to-DITA parity report and passing curl/Python example fixtures. | **Planned:** `make test-docs-contract`; existing API baseline: `pytest -q tests/api tests/test_openapi_surface.py` | Open |
| `DOC090-G08` | All five guides, navigation, metadata, search terms, alt text, and links have reviewed parity in `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. | Project maintainer — localization | Six-locale topic/map parity and terminology reports with no silent prose fallback. | **Planned:** `make test-docs-contract`; existing locale baseline: `make test-locale-contract` | Open |
| `DOC090-G09` | Every required User Guide illustration has a current, deterministic, locale-specific screenshot, caption, and alt text. | Project maintainer — localized visual content | Complete screenshot matrix, freshness report, size/orphan checks, and reviewed six-locale assets. | `make test-docs-ui`; **planned:** `make docs-screenshots-check` | Open |
| `DOC090-G10` | BPM serves packaged documentation under `/help/`, preserves OpenAPI `/docs`, and exposes working locale-aware Library and contextual help links. | Project maintainer — BPM portal integration | Route/manifest contracts and six-locale browser evidence for Library and deep links. | `make test-docs-contract` and `make test-docs-ui`; product UI baseline: `make test-ui` | Open |
| `DOC090-G11` | Offline deterministic smart search provides locale-aware exact lookup, aliases, typo tolerance, ranking, filters, and integrity checks without AI. | Project maintainer — documentation search | Six-locale quality fixtures, top-result thresholds, index integrity, size, and latency reports. | `make test-docs` and `make test-docs-ui` | Open |
| `DOC090-G12` | Documentation source, tools, fixtures, tests, diagnostics, coverage, and context guidance are isolated under the documented ownership boundary. | Project maintainer — documentation test platform | Focused unit/contract/browser commands, compact fixtures, rerun diagnostics, and 100% documentation-code coverage. | `make test-docs`, `make test-docs-contract`, and `make test-docs-ui` | Open |
| `DOC090-G13` | Portal output passes accessibility, CSP/security, responsive/theme, clean-package, licensing, and offline-use checks. | Project maintainer — release engineering and security | Accessibility/security reports and clean package-content inventory with no stale, unlicensed, cache, or debug artifacts. | `make docs-release-check` and `make test-docs-ui`; package verification must also run through `make test-release` | Open |
| `DOC090-G14` | Final product quality, release documentation, coverage, browser smoke, and repository handoff are complete. | Project maintainer — BPM release | Passing full suites, 100% covered code surface, final README/changelog/index, clean commit, and maintainer-run push command. | `make typecheck`, `make lint`, `pytest -q`, `make coverage`, `make test-ui`, and `make test-release` | Open |

## Gate Closing Rules

1. A gate closes only after its implementation is complete and every listed command exists and
   passes against a clean generated-output state.
2. Evidence must identify the BPM version, documentation build version, locale set, Firefox schema
   channels, and CIS source versions relevant to that gate.
3. All six locales are required. Missing localized prose, navigation, search metadata, alt text, or
   required screenshots keeps the affected gate open.
4. Falling below 100% coverage for owned executable code is not accepted as known debt.
5. Browser and screenshot commands require immediate sandbox escalation; do not attempt them in the
   filesystem sandbox first.
6. Search remains deterministic and offline. LLMs, embeddings, vector databases, RAG, generative
   answers, AI translation, and AI-generated alt text are prohibited for this release.
7. A backlog checkbox, manually opened page, or ad hoc command does not replace the named release
   command and its reproducible evidence.
8. Any product, API, Firefox schema, CIS mapping, locale, route, or packaging change reopens every
   gate whose evidence may have become stale.

## Explicitly Deferred Outcomes

The following outcomes do not block 0.9.0 because they are outside the approved epic scope:

- distribution-specific administrator installation variants, packaged services, high availability,
  official reverse-proxy recipes, and production-hardening guarantees;
- BPM distribution-format design itself;
- AI-assisted documentation search or question answering;
- extraction into a separate repository, service, or standalone product;
- new API endpoints or product-specific connectors created only for documentation examples.

Adding any deferred outcome requires a separately approved backlog task or epic; it must not be
silently folded into a release gate above.
