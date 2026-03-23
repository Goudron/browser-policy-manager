# Changelog

## Unreleased

### Changed
- Consolidated the application around the canonical `/api/profiles` CRUD API.
- Removed the old `/api/policies` compatibility layer from the app.
- Updated supported bundled schema versions to ESR 140 and Release 145.
- Switched the web UI to use the canonical profiles API end-to-end.
- Added mounted web functionality for `/profiles`, `/i18n/{locale}.json`, and `/favicon.ico`.
- Enabled security headers in the running application through middleware.

### Fixed
- Resolved bootstrap/config issues around environment variable handling and DB settings.
- Stabilized SQLite execution in the current environment with the project-specific session adapter path.
- Fixed template loading paths for the web UI.
- Eliminated hangs caused by security/static response interaction by moving security headers to ASGI middleware.
- Aligned documentation and test naming with the current `profiles` architecture.

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
