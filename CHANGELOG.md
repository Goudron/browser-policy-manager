# Changelog

## Unreleased

Build target: `0.7.0`

### Added
- Added Firefox `policies.json` import as a first-class product workflow, including API support, validation, and profile-library import controls.
- Added dedicated profile workspace routes for library, visual editor, and advanced editor flows instead of treating `/profiles` as one combined surface.
- Added CIS Firefox compliance data, mappings, generated hardening layers, merge logic, tooling, and regression coverage.
- Added schema support for Firefox `release-150` and `esr-140.10`, plus migration coverage for stored profile schema versions.
- Added a local Chromium UI audit script and artifact/report flow for guided, advanced, layout, theme, and localization QA.
- Added explicit live Firefox setup guidance and version reporting for the isolated Selenium harness.

### Changed
- Moved the project from `0.6.0-dev` to `0.7.0`.
- Promoted Firefox Enterprise `policies.json` to the main user-facing import/export contract and removed internal JSON/YAML handoff routes from the primary product surface.
- Reworked `/profiles` into a library-first workspace and moved editing into dedicated visual and advanced routes.
- Expanded guided coverage across shared-device, trust/auth, extensions governance, privacy hardening, upkeep, site access, home/search, language, AI, and compliance-aware surfaces.
- Aligned guided mode, advanced editing, validation, export, compare, lifecycle, and clone flows around one canonical profile model.
- Updated English and Russian product copy, route titles, and advanced-workflow terminology to match the current split workspace.
- Refreshed schema-update, live-testing, migration, and workspace backlog documentation to match the current repository shape.
- Raised non-live coverage for `app/` to `100%`.

### Fixed
- Fixed route-context and frontend bootstrap regressions that affected locale switching, theme switching, step navigation, profile loading, and split-workspace rendering.
- Fixed multiple guided wizard bugs found during Chromium QA, including AI-step behavior, preset application, language switching, advanced handoff, export-step readiness, and `SearchEngines` document generation.
- Fixed dark-theme surface leaks, desktop/mobile overflow issues, and narrow-viewport regressions across library, guided, review, and advanced surfaces.
- Fixed profile-library state, labels, and rendering glitches that could surface stale fixtures, untranslated action copy, or inconsistent badges on first load.
- Fixed remaining advanced-workflow terminology drift where older `Advanced document` / `Техдокумент` copy still appeared.
- Fixed remaining SQLite URL normalization edge cases with explicit regression tests.

### Notes
- This release exposed architectural coupling across the library, guided editor, advanced editor, export/review surfaces, and shared frontend runtime. Those follow-up architecture issues are planned for `0.7.5-dev`.

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
