# Changelog

## Unreleased

### Added
- Introduced a schema-driven Firefox policy editing experience for `/profiles` with modular catalogs for guided settings, starter presets, manual policy controls, preferences, and schema-shell editing.
- Added a dedicated `firefox_policy_ui_registry` service layer to map policy schemas into UI sections, widgets, tags, and fallback placement metadata.
- Added modular frontend bundles and Jinja partials for the profiles page instead of one monolithic template/script pair.
- Added a reusable `tools.convert_policies_from_upstream_lib` package to split the schema conversion pipeline into parser, inference, semantic hint, emission, and CLI modules.
- Added targeted tests for Firefox UI registry inference, preferences, starter presets, wizard shell behavior, settings catalog builders, and manual policy controls.

### Changed
- Consolidated the application around the canonical `/api/profiles` CRUD API.
- Removed the old `/api/policies` compatibility layer from the app.
- Updated supported bundled schema versions to ESR 140 and Release 148.
- Switched the web UI to use the canonical profiles API end-to-end.
- Added mounted web functionality for `/profiles`, `/i18n/{locale}.json`, and `/favicon.ico`.
- Enabled security headers in the running application through middleware.
- Refactored Firefox schema loading and policy metadata handling around the new UI registry and richer policy schema models.
- Reworked the test suite to use a shared sync client helper, narrower HTTP assertions, and decomposed large scenario files into smaller, more focused tests.
- Raised automated coverage for `app/` to `100%`, including branch coverage.

### Fixed
- Resolved bootstrap/config issues around environment variable handling and DB settings.
- Stabilized SQLite execution in the current environment with the project-specific session adapter path.
- Fixed template loading paths for the web UI.
- Eliminated hangs caused by security/static response interaction by moving security headers to ASGI middleware.
- Aligned documentation and test naming with the current `profiles` architecture.
- Fixed CI quality-gate failures caused by Ruff and Mypy issues in the new Firefox UI and schema tooling modules.
- Restored successful coverage artifact generation in GitHub Actions by ensuring the lint/type/test pipeline completes end-to-end.

## Sprint F (2025-10-26)

### Added
- ESR-140 / Release-144 schemas, validators, and `/api/validate/{profile}`.
- CRUD for policies with soft delete and restore.
- Export API with JSON/YAML routes:
  - `/api/export/{id}/policies.json|yaml`
- Web UI `/profiles`:
  - Monaco editor (JSON/YAML), create/update/delete/restore, validation.
  - i18n (EN base, RU added), download JSON/YAML buttons.
- CI (GitHub Actions) for `dev` branch:
  - ruff, black, mypy, pytest with coverage ≥85%.
- Alembic migration for `deleted_at` (idempotent, creates table if missing).
- Security headers middleware (CSP, X-Frame-Options, etc.).
- Pre-commit hooks (ruff/black/mypy/pytest).

### Fixed
- JSON serialization for datetimes in export responses (`model_dump(mode="json")`).
- Pydantic v2 deprecations (ConfigDict).
- Package discovery / editable install via `pyproject.toml`.

### Notes
- No Beta; legacy ESR 115/128 dropped (enterprise focus).
- Default language: English; Russian available via `/i18n/ru.json`.
