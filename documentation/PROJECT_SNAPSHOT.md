# BPM Product Documentation Workspace Snapshot

Updated: 2026-07-16
Target BPM version: `0.9.1`
Current completed backlog item: `BPM091-M13-10`
Next backlog item: `BPM091-M13-11`

## Current State

The maintained subsystem has a browser-verified accessible return-safe hierarchical duplicate-free
static portal shell/theme, an Administrator/DevOps Guide map/key/root contract, an API/integration
re-home audit, five manifest-backed contextual help links, localized unavailable/stale/incomplete
documentation states, and focused `/help/` accessibility/responsive/CSP/theme integration
contracts. It also has isolated documentation test suite boundaries, focused documentation make
targets, a documentation-only source fast loop, isolated documentation coverage reporting, a
compact deterministic fixture catalog, ignored failure diagnostics, a generated subsystem
snapshot, a release-blocking documentation gate, a browser-backed documentation portal smoke, a
final content coverage audit, a refreshed implemented-product README, and a documentation-only
debugging protocol.

The localized User Guide screenshot workflow has a frozen capture-state contract, 36 normalized
PNG source assets, and `capture_user_guide_screenshots.py`. The `administrator-guide` includes
DevOps configuration/storage/logs/backups/CORS/security limits, update-from-source
evidence/migrations/docs rebuild/rollback-stop runbooks, a migrated API integration corpus, DevOps
integration runbooks for external control products, reusable DevOps environment
templates/curl/Python/multipart examples, and failed
startup/probe/schema/API/import/export/storage/WSL/dependency/documentation-portal diagnostics.
Its boundaries cover single-node source readiness, network exposure/proxy-readiness questions,
HA/deferred production boundary records, compact validation fixtures for stale
command/API/env/path/locale/deferred-claim drift, and final no-fallback/no-short-summary locale
parity review.

Milestones M10, M11, and M12 are complete and linked from the active release contract. M13-01
through M13-10 are accepted: static quality, full suites and coverage, clean documentation
validation/build, Chromium/Selenium smoke, milestone handoff, changelog finalization, and release
procedure verification all pass, and the reviewed epic commit is ready. The repeated documentation
gate reports 754 passed and 4 deselected after two stale Administrator deployment contract paths
were corrected and guarded. `DOC091-G14` and overall BPM 0.9.1 release readiness remain open only
until the M13-11 maintainer handoff completes.

`make dev` refreshes the current local documentation build through `make docs-install-dev` before
starting BPM. The maintainer manual review acceptance and final `runtime_ready=false` blockers stay
release evidence rather than generated source edits.

Not implemented yet:

- Windows 10/11 WSL validation on actual hosts; current outcomes remain explicitly unverified.
- Product screenshot coverage beyond the approved minimal User Guide matrix.
- Packaged installers, production hardening, HA, managed secrets, and AI/RAG documentation search.
- No `make docs-screenshots-check` target exists yet.

## Maintained Entry Points

| Area | Paths |
| --- | --- |
| Backlog | `docs/bpm_0_9_0_product_documentation_portal_backlog_2026-06-20.md` |
| Ownership | `docs/architecture/product-documentation-ownership-boundary-0.9.0.md` |
| Toolchain | `docs/architecture/dita-publishing-toolchain-decision-0.9.0.md` |
| Identity | `docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md` |
| Manifest | `docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md` |
| Provenance | `docs/architecture/product-documentation-provenance-review-0.9.0.md` |
| Accessibility | `docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md` |
| Theme | `docs/architecture/product-documentation-visual-theme-contract-0.9.1.md`, `docs/architecture/bpm-documentation-theme-token-audit-0.9.1.md` |
| Sufficiency | `documentation/config/documentation-sufficiency-review-protocol-0.9.1.json` |
| Capability inventory | `docs/architecture/product-user-capability-inventory-0.9.0.md` |
| User Guide | `documentation/config/user-guide-map-0.9.0.json`, `documentation/config/user-guide-screenshot-matrix-0.9.1.json` |
| Search | `documentation/config/search-corpus-and-results-0.9.0.json`, `documentation/config/search-facets-filters-0.9.0.json`, `documentation/config/search-ui-filter-contract-0.9.1.json`, `documentation/config/search-quality-performance-0.9.0.json`, `documentation/config/search-integrity-drift-0.9.0.json` |
| Navigation/help | `documentation/config/navigation-tree-contract-0.9.1.json`, `documentation/config/all-settings-row-help-link-contract-0.9.1.json`, `documentation/config/documentation-polish-guardrails-0.9.1.json` |
| Coverage/diagnostics | `documentation/config/coverage-policy-0.9.0.json`, `documentation/config/diagnostics-policy-0.9.0.json` |
| Fixtures | `documentation/fixtures/fixture-catalog-0.9.0.json`, `documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json` |
| Linux selection | `docs/architecture/linux-distribution-selection-0.9.1.md` |
| Generated snapshot | `documentation/PROJECT_SNAPSHOT.generated.md` |
| Suite boundaries | `documentation/tests/suite-boundaries-0.9.0.json` |
| Release/browser gates | `documentation/tests/contract/test_documentation_release_gate.py`, `documentation/tests/browser/test_documentation_portal_browser_smoke.py` |
| Debugging | `documentation/runbooks/debugging-protocol.md` |
| Administrator scope | `documentation/tests/contract/test_administrator_guide_scope.py` |
| Administrator operations | `documentation/tests/contract/test_administrator_devops_operational_boundaries.py`, `documentation/tests/contract/test_administrator_linux_deployment_topics.py`, `documentation/tests/contract/test_administrator_windows_wsl_deployment_topics.py`, `documentation/tests/contract/test_administrator_update_from_source_topics.py`, `documentation/tests/contract/test_administrator_troubleshooting_diagnostics_topics.py`, `documentation/tests/contract/test_administrator_production_readiness_boundaries.py`, `documentation/tests/contract/test_administrator_guide_validation_fixtures.py` |
| API contracts | `documentation/tests/contract/test_api_integration_topics.py`, `documentation/tests/contract/test_api_locale_parity.py`, `documentation/tests/contract/test_api_openapi_drift.py`, `documentation/tests/contract/test_api_rehome_audit.py`, `documentation/tests/contract/test_api_devops_integration_runbooks.py` |
| API re-home | `docs/architecture/api-integration-rehome-audit-0.9.0.json`, `docs/architecture/api-integration-rehome-audit-0.9.0.md`, `documentation/runbooks/README.md` |
| Firefox/CIS/API inventories | `docs/architecture/firefox-policy-documentation-inventory-0.9.0.json`, `docs/architecture/cis-documentation-inventory-0.9.0.json`, `docs/architecture/api-documentation-inventory-0.9.0.md` |

## Commands Available Now

```bash
make setup-docs-toolchain
make test-docs
make test-docs-contract
make test-docs-ui
make test-docs-ui-contract
make test-docs-browser
make docs-snapshot
make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"
make docs-coverage
make docs-release-check
make docs-validate
make docs-build
make docs-install-dev
make docs-reproducibility-check
make docs-package
make docs-package-verify
./.venv/bin/python documentation/tools/validate_metadata.py
./.venv/bin/pytest -q tests/test_product_documentation_scaffold.py
./.venv/bin/pytest -q -m docs_contract
./.venv/bin/ruff check <changed_python_files>
git diff --check -- <changed_files>
```

Build/package commands are offline after toolchain setup. Browser commands use one bounded
Chromium/Selenium process. Generated build, installed-site, package, report, cache, and container
evidence remain outside hand-edited DITA source.
