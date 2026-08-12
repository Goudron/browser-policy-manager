# BPM Product Documentation Workspace Snapshot

Updated: 2026-08-09
Target BPM version: `0.9.5`

## Current State

Documentation build ownership is split between the compatible CLI facade
`documentation/tools/build_docs.py` and `documentation/buildlib/`: source validation,
portal/catalog creation, PDF generation, artifact packaging, and atomic publication have separate
owners. The release application serves the installed portal through
`app/documentation/router.py`; build tooling remains outside the runtime import graph. Published
source remains six-locale DITA (`en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`), with reviewed source
assets and deterministic generated artifacts. Ordinary PDF builds reuse only SHA-256-verified
locale-guide HTML/PDF cache entries; independent PDF reproducibility bypasses that cache.

Use this file with `documentation/AGENTS.md`; then read the one approved backlog row, one relevant
runbook, the exact owner below, and its focused test. Do not use historical backlogs or generated
site/PDF output as current implementation ownership.

## Maintained Entry Points

| Concern | Start with | Focused proof |
| --- | --- | --- |
| Build facade and ownership | `documentation/tools/build_docs.py`, `documentation/buildlib/` | `documentation/tests/unit/test_build_docs_structure.py` |
| Build lifecycle/publication | `documentation/buildlib/lifecycle.py`, `documentation/buildlib/publishing.py` | `documentation/tests/unit/test_build_lifecycle.py` |
| Portal/catalog/artifacts | `documentation/buildlib/portal.py`, `documentation/buildlib/catalog.py`, `documentation/buildlib/artifacts.py` | `documentation/tests/unit/test_buildlib_portal.py`, `documentation/tests/unit/test_buildlib_artifacts.py` |
| PDF output | `documentation/buildlib/pdf.py`, `documentation/config/pdf-generation-contract-0.9.3.json`, `documentation/config/pdf-pipeline-optimization-benchmark-0.9.4.json` | `documentation/tests/contract/test_pdf_generation_contract_0_9_3.py`, `documentation/tests/contract/test_pdf_pipeline_optimization_benchmark_0_9_4.py` |
| DITA, maps, and locale source | `documentation/src/dita/`, `documentation/config/`, relevant `documentation/runbooks/` file | exact topic/locale contract |
| Runtime portal boundary | `app/documentation/router.py`, `app/documentation/assistant_contracts.py` | `tests/contract/docs/general/test_product_documentation_context_guide.py` |
| Ownership/release boundary | `docs/architecture/current-system-map.md`, `tests/fixtures/current_artifact_owners_0_9_4.json` | `tests/contract/docs/general/test_current_artifact_ownership.py` |
| Firefox schema handoff | `docs/architecture/schema-channel-surface-inventory-0.9.5.md`, `docs/firefox-schema-update-runbook.md` | `tests/contract/docs/schema/test_firefox_schema_lifecycle_catalog_contract.py`, `make docs-validate` |
| Snapshot generation | `documentation/tools/generate_subsystem_snapshot.py` | `documentation/tests/unit/test_generate_subsystem_snapshot.py`, `documentation/tests/contract/test_documentation_subsystem_snapshot.py` |

## Commands Available Now

```bash
make setup-docs-toolchain
make setup-docs-toolchain DOCS_TOOLCHAIN_OFFLINE=1
make test-docs
make test-docs-contract
make test-docs-ui
make test-docs-ui-contract
make test-docs-browser
make docs-snapshot
make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"
make docs-coverage
make docs-release-check
make docs-release-handoff
make docs-validate
make docs-build
make docs-install-dev
make docs-pdf-verify
make docs-reproducibility-check
make docs-package
make docs-package-verify
./.venv/bin/python documentation/tools/validate_metadata.py
./.venv/bin/pytest -q tests/contract/docs/general/test_product_documentation_scaffold.py
./.venv/bin/pytest -q -m docs_contract
./.venv/bin/ruff check <changed_python_files>
git diff --check -- <changed_files>
```

## Boundaries

- `documentation/src/generated/`, `documentation/build/`, `documentation/dist/`,
  `documentation/reports/`, caches, toolchains, dependency/vendor trees, screenshots, corpora,
  secrets, local installed sites, and package artifacts are not routine source context.
- Generated portal, search, PDF, package, and installed-site artifacts are rebuilt through their
  owner; never hand-edit them.
- Browser and release checks are escalation paths after the focused contract; use the debugging
  runbook to select them.
