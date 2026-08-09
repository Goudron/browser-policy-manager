# Browser Policy Manager Current System Map

Date: 2026-08-04

This is the first orientation point for BPM 0.9.4 work. Read this map before
opening a subsystem. It names owned entrypoints and narrow verification routes;
it is not an inventory of dependencies, generated files, caches, secrets, or
the implementation of every feature. Import direction rules are executable in
`docs/architecture/python-architecture-boundaries-0.9.4.md`.

## Release Application

`app/main.py:create_app` is the ASGI factory and release assembly. Each app owns
an injectable `app/db.py:DatabaseRuntime` with a native async engine and session
factory. Its lifespan initializes that runtime, verifies the exact Alembic head
without writing, and disposes the database and documentation-assistant runtimes.
Alembic, not application startup or a request path, owns every retained schema
and stored-channel upgrade.

| Concern | Owner and minimum reading route | Focused verification |
| --- | --- | --- |
| Configuration and HTTP shell | `app/core/config.py`, `app/main.py`, `app/middleware/security.py` | `tests/unit/app/test_bootstrap_config.py`, `tests/integration/app/test_current_version_surfaces.py` |
| Database lifecycle | `app/db.py`, `app/models/profile.py`, `alembic/env.py`, `alembic/versions/` | `tests/unit/db/test_db_helpers.py`, `tests/integration/db/test_migrations.py`, `tests/integration/db/test_database_integration.py`, `tests/integration/db/test_database_recovery.py` |
| Profile data/API lifecycle | `app/api/profiles.py` -> `app/services/profile_service.py` -> `app/schemas/profile.py`/`app/models/profile.py` | `tests/integration/api/test_profiles_api.py`, `tests/unit/profiles/test_profiles_core_unit.py`, `tests/integration/profiles/test_profiles_update_and_pagination.py` |
| Firefox boundary | `app/services/firefox_policy_import.py`, `app/services/firefox_policy_export.py`, `app/api/export.py`, `app/api/validation.py` | `tests/integration/api/test_firefox_policies_import_api.py`, `tests/integration/api/test_openapi_surface.py` |
| Rendered profile routes | `app/web/profiles.py`, `app/web/profiles_context.py`, `app/web/profile_navigation.py`, `app/templates/profiles/` | `tests/contract/ui/profiles/`, `tests/contract/ui/localization/test_web_profiles_page.py` |

The public policy exchange format is a complete Firefox `policies.json` object;
database storage is normalized around `Profile.flags`. Schema channels start at
`app/core/schema_channels.py`; `app/core/schemas_loader.py` reads only the
three pinned bundled policy schemas. CIS YAML source and generated compliance
layers are owned by `app/compliance/firefox/cis/`, with tests in
`tests/contract/compliance/`.

## Browser Runtime And Generated Boundaries

The browser application is Jinja-rendered and self-hosted. The wrapper
`app/templates/profiles/_page_document.html` selects the five profile surfaces:
library, comparison, guided editor, all settings, and JSON editor.
`app/templates/profiles/_page_route_assets.html` reads the generated manifest
and loads each route-specific native ESM entry. Route source uses direct imports;
there is no profile-global compatibility bridge or load-order contract.

- CSS source is `app/static/profiles_css/`; rebuild its checked-in output
  `app/static/profiles.css` with `make build-profiles-css`.
- `tools/frontend_profile_graph_0_9_4.json` freezes the owned profile
  frontend: direct-import module sources, route entries, vendor boundary,
  public DOM test owner, and conversion stage. Run
  `make frontend-profile-graph` before moving an owned profile asset.
- `app/static/profiles_modules/` contains side-effect-free ES-module sources.
  Use `make test-profile-pure-modules` for native Node import/parity contracts.
- `app/static/profiles_bundles/` is generated M6-04 output: five route entries,
  shared chunks, external source maps, a canonical metafile, and a checksum
  manifest. Rebuild only with `make build-profile-frontend-bundles`; run
  `make check-profile-frontend-bundles` before review. The template reads that
  manifest, while Monaco remains the separately verified JSON-only vendor
  boundary. The manifest holds generated/JavaScript/per-route byte ceilings,
  so generated output is sized even before it enters Git. Do not hand-edit
  bundle output or use it as general source context.
- Monaco source input is `app/static_src/profiles_monaco_entry.js`; rebuild
  vendor output with `tools/build_monaco_bundle.sh` or
  `make rebuild-frontend-vendor`.
- `app/static/vendor/`, `app/static/profiles.css`,
  `app/compliance/firefox/cis/generated/`, runtime locale catalogs in
  `app/i18n/`, and bundled schemas in `app/schemas/policies/` are generated or
  vendored boundaries. Do not use them for broad context; change their owned
  source and run the relevant rebuild/check command instead.
- Locale ownership starts at `app/core/locales.py` and `app/i18n_src/`.
  Use `make check-locale-catalogs` and locale-contract tests after changes.

## Documentation And Optional AI Are Separate Contours

The installed documentation HTTP surface is assembled by `app/main.py` from
`app/documentation/router.py`. Its release-safe assistant transport is
`app/documentation/assistant_contracts.py` and
`app/documentation/assistant_service.py`; the visible default is a training
notice, not local model/RAG execution.

`app/ai/` and `app/documentation/local_assistant_runtime.py` are optional
incubation/development assembly. They are reached only through explicit
development commands (`make dev`, `make ai-*-dev`) or named offline tooling.
Install `[dev,ai]`, run `make ai-extra-check`, and use
`make test-ai-incubation` for this separate contour;
they must not become a transitive dependency of `app.main`. Documentation
build sources and tools live in `documentation/` and are likewise not release
runtime. Their maintained entrypoint is `documentation/tools/build_docs.py`;
its owned library responsibilities live in `documentation/buildlib/` (source
validation, portal/catalog generation, PDF, and publication). Use
`make docs-validate` or `make test-docs` rather than loading its corpus.

## Test Contours And Fast Commands

| Change area | Start here | Escalate when needed |
| --- | --- | --- |
| Python ownership/imports | `make architecture` | `tests/integration/app/test_python_architecture_contracts.py` |
| Optional AI incubation | `make ai-extra-check` | `make test-ai-incubation` |
| Product unit/API/route contracts | `make test-unit`, `make test-integration`, or a named test file | `make test-contract`, `make test-browser` |
| Firefox schema bundles | `make test-firefox-schema-workflow` | `make test-firefox-schema-contract` |
| Firefox policy behavior | `make setup-firefox-live-browsers FIREFOX_CHANNEL=<release|esr153|esr140>` | `make firefox-live-workflow FIREFOX_CHANNEL=<channel>` |
| Documentation tooling/portal | `make test-docs` | `make docs-validate` |
| Performance/repository health | `make profile-performance-gate` | `make repo-health` |
| Profile frontend graph | `make frontend-profile-graph` | named DOM/browser contracts in `tests/contract/ui/profiles/` |
| Profile route bundles | `make check-profile-frontend-bundles` | `tests/unit/profiles/test_profile_frontend_bundles.py`, route/browser asset contracts |

`browser_ui`, `firefox_live`, and `firefox_live_amo` are deliberately outside
the default pytest selection. Generated artifacts, dependency trees, local
artifacts, and credentials are excluded from this map and from routine context
loading.

## Machine-Checked Drift Contract

The following bounded manifest is verified by
`tests/contract/docs/general/test_current_system_map.py`. When moving an owner, entrypoint, test
contour, or command listed here, update the map in the same change. It only
checks named paths and commands; it does not recursively scan the repository.

```json system-map-contract
{
  "version": "0.9.4",
  "paths": [
    "app/main.py",
    "app/core/config.py",
    "app/db.py",
    "app/models/profile.py",
    "app/schemas/profile.py",
    "app/api/profiles.py",
    "app/api/export.py",
    "app/api/validation.py",
    "app/services/profile_service.py",
    "app/services/firefox_policy_import.py",
    "app/services/firefox_policy_export.py",
    "app/web/profiles.py",
    "app/web/profiles_context.py",
    "app/templates/profiles/_page_document.html",
    "app/static_src/profiles_monaco_entry.js",
    "app/static/profiles_modules/",
    "app/static/profiles_bundles/",
    "app/core/schema_channels.py",
    "app/core/schemas_loader.py",
    "app/documentation/router.py",
    "app/documentation/assistant_contracts.py",
    "app/documentation/assistant_service.py",
    "app/documentation/local_assistant_runtime.py",
    "app/ai/",
    "documentation/tools/build_docs.py",
    "documentation/buildlib/",
    "tests/contract/ui/profiles/",
    "tests/live/firefox/",
    "tests/contract/compliance/"
  ],
  "commands": [
    "make architecture",
    "make ai-extra-check",
    "make test-ai-incubation",
    "make test-fast",
    "make test-unit",
    "make test-integration",
    "make test-contract",
    "make test-browser",
    "make test-firefox-schema-workflow",
    "make test-firefox-schema-contract",
    "make test-live",
    "make test-docs",
    "make docs-validate",
    "make profile-performance-gate",
    "make repo-health",
    "make test-profile-pure-modules",
    "make check-profile-frontend-bundles"
  ],
  "excluded_boundaries": [
    "app/static/vendor/",
    "app/static/profiles.css",
    "app/compliance/firefox/cis/generated/",
    "app/i18n/",
    "app/schemas/policies/"
  ]
}
```
