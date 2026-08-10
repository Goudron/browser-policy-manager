# BPM Codex Orientation Snapshot

Generated only by `make codex-snapshot` (`docs/codex/generate_project_snapshot.py`); do not edit manually.
It deliberately has no Git, local-machine, generated-artifact, or report input.
Target BPM version: `0.9.4`
Declared-source digest: `2037ffa3809edad799a238b1a6ff79cb683001391e5eeccee4459ac55e28909c`

## Start Here

1. `AGENTS.md` and the one approved backlog task.
2. `docs/architecture/current-system-map.md` for owned entrypoints and boundaries.
3. The named owner and focused test below; expand only after a focused failure.

## Declared Source Owners

- System map — release architecture maintainers: `docs/architecture/current-system-map.md`
- Snapshot generator — documentation architecture and snapshot maintainers: `docs/codex/generate_project_snapshot.py`
- Architecture boundaries — release architecture maintainers: `docs/architecture/python-architecture-boundaries-0.9.4.md`
- Release boundary — release architecture maintainers: `docs/architecture/release-incubation-development-boundary-0.9.4.md`
- Application assembly — application runtime maintainers: `app/main.py`
- Configuration and database — application runtime maintainers: `app/core/config.py`, `app/db.py`
- Profile API/service — profile lifecycle maintainers: `app/api/profiles.py`, `app/services/profile_service.py`
- Firefox exchange — Firefox policy exchange maintainers: `app/services/firefox_policy_import.py`, `app/services/firefox_policy_export.py`
- Profile web route boundary — profile web maintainers: `app/web/profiles.py`, `app/web/profiles_context.py`, `app/templates/profiles/_page_document.html`
- Frontend source boundary — profile frontend maintainers: `app/static/profiles_modules/policy_document.mjs`, `app/static/profiles_css/README.md`, `tools/frontend_profile_graph_0_9_4.json`
- Documentation workspace — documentation architecture and snapshot maintainers: `documentation/PROJECT_SNAPSHOT.md`
- Current artifact ownership — release artifact maintainers: `tests/fixtures/current_artifact_owners_0_9_4.json`, `tests/contract/docs/general/test_current_artifact_ownership.py`

## Focused Verification Routes

- Architecture/import boundary: `make architecture`; `tests/integration/app/test_python_architecture_contracts.py`
- Profile API/service: `make test-integration`; `tests/integration/api/test_profiles_api.py`
- Profile frontend: `make test-profile-pure-modules`; `tests/unit/profiles/test_profile_frontend_bundles.py`
- Firefox policy exchange: `make test-firefox-schema-workflow`; `tests/integration/api/test_firefox_policies_import_api.py`
- Documentation pipeline: `make test-docs`; `documentation/tests/unit/test_build_docs_structure.py`

## Environment And Report Evidence Excluded From This Snapshot

- Git and local-machine state
- generated frontend bundles, CSS, locale catalogs, schemas, documentation artifacts, and installed sites
- vendor trees, dependencies, caches, reports, corpora, secrets, databases, and browser artifacts

A declared source change invalidates this Codex snapshot only. Regenerate it through its owning command; do not copy digests from evidence or edit this file by hand.
