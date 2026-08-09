# BPM Documentation Subsystem Snapshot

Generated only by `make docs-snapshot` (`documentation/tools/generate_subsystem_snapshot.py`); do not edit manually.
It has no Git, local-machine, generated-artifact, or report input.
Target BPM version: `0.9.4`
Declared source digest: `04ac293b4b9e3009a0fa7fc3b2e0ac93c68761ac2f778e1b669b436ac1819b78`

## Declared Source Owners

- Snapshot governance — documentation architecture and snapshot maintainers: `documentation/tools/generate_subsystem_snapshot.py`, `documentation/AGENTS.md`, `documentation/config/documentation-test-estate-inventory-0.9.4.json`
- Documentation build — documentation build tooling maintainers: `documentation/tools/build_docs.py`, `documentation/buildlib/lifecycle.py`, `documentation/buildlib/sources.py`, `documentation/buildlib/portal.py`, `documentation/buildlib/artifacts.py`, `documentation/buildlib/pdf.py`
- Source and publication authority — documentation source-contract maintainers: `documentation/src/dita/en/maps/user-guide.ditamap`, `documentation/src/dita/en/maps/administrator-guide.ditamap`, `documentation/src/dita/en/maps/keys.ditamap`, `documentation/config/artifact-policy.json`, `documentation/config/documentation-semantic-contracts-0.9.4.json`
- Runtime `/help/` bridge — documentation runtime maintainers: `app/documentation/router.py`, `app/documentation/assistant_contracts.py`, `app/documentation/assistant_service.py`
- Focused validation — documentation architecture and snapshot maintainers: `documentation/tests/unit/test_generate_subsystem_snapshot.py`, `documentation/tests/contract/test_documentation_subsystem_snapshot.py`, `documentation/tests/contract/test_maintained_index_snapshot_contract_0_9_3.py`, `documentation/tests/contract/test_documentation_test_estate_inventory_0_9_4.py`, `tests/contract/docs/general/test_codex_project_snapshot.py`
- Architecture entry points — documentation architecture maintainers:
  - `docs/architecture/product-documentation-ownership-boundary-0.9.0.md`
  - `docs/architecture/dita-publishing-toolchain-decision-0.9.0.md`
  - `docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md`
  - `docs/architecture/product-documentation-manifest-and-ui-target-schema-0.9.0.md`
  - `docs/architecture/product-documentation-provenance-review-0.9.0.md`
  - `docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md`
  - `docs/architecture/product-documentation-release-contract-0.9.0.md`
  - `docs/architecture/product-user-capability-inventory-0.9.0.md`
  - `docs/architecture/firefox-policy-documentation-inventory-0.9.0.json`
  - `docs/architecture/cis-documentation-inventory-0.9.0.json`
  - `docs/architecture/api-documentation-inventory-0.9.0.md`
  - `docs/architecture/ai-component-update-runbook-0.9.3.md`
  - `docs/architecture/documentation-assistant-presentation-0.9.3.md`
  - `docs/architecture/documentation-assistant-resource-state-0.9.3.md`
  - `docs/architecture/documentation-assistant-web-mode-0.9.3.md`

## Commands

- `make docs-snapshot`
- `make codex-snapshot`
- `make docs-fast-check DOCS_CHANGED="documentation/src/dita/en/user/example.dita"`
- `make test-docs`
- `make test-docs-contract`
- `make docs-release-handoff`

## Environment And Report Evidence Excluded From This Snapshot

- build, distribution, installed-site, PDF, package, and generated search output
- browser captures, test reports, coverage, diagnostics, caches, toolchains, dependencies, and vendor trees
- Git state, local-machine paths, credentials, databases, and live-install transcripts

A declared source change invalidates this documentation snapshot only. Regenerate it through its owning command; do not copy digests from evidence or edit this file by hand.
