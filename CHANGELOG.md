# Changelog

## Unreleased

Build target: `0.6.0-dev`

### Added
- Completed the guided profile-wizard redesign and the follow-up polish stream.
- Added scenario-first setup, recommended baselines, preset diff previews, and shared-device workflow guidance.
- Added step-level undo/reset and cross-step recent-changes memory.
- Added targeted guided-to-advanced handoff, advanced drill-down review, and stronger export explainability.
- Added compare-by-guided-area, clone-and-adjust, lifecycle review, and shareable guided summaries.
- Added workflow and governance layers across high-value Firefox enterprise clusters.
- Added advanced-only boundary and coverage-priority project registers in `docs/`.
- Added viewport regression coverage for guided-first landing assumptions.
- Added targeted tests for the remaining SQLite URL normalization branches in [`app/db.py`](app/db.py).

### Changed
- Moved the project from `0.5.0-dev` to `0.6.0-dev`.
- Expanded guided coverage across shared-device, trust/auth, extensions governance, privacy hardening, upkeep, site access, home/search, language, and AI surfaces.
- Aligned guided mode, `Advanced document`, review, export, compare, lifecycle, and clone flows around one canonical profile model.
- Updated the profiles shell so guided setup remains the primary path on mobile and narrow screens.
- Reworked the profile library into a wider table-style workspace surface with a sticky header, search, stronger dark-theme actions, and clearer primary/secondary row actions.
- Consolidated runtime behavior around one active application database at `data/bpm.db` and reseeded the default workspace with the two canonical starter profiles.
- Cleaned up English and Russian UI copy, removed mixed anglicisms from RU, and standardized the term `Техдокумент`.
- Updated the roadmap and UX docs to reflect the completed roadmap, PB backlog, and post-roadmap backlog.
- Raised non-live coverage for `app/` to `100%`.

### Fixed
- Fixed remaining RU terminology drift where `Технический документ` still appeared instead of `Техдокумент`.
- Fixed frontend bootstrap regressions that blocked locale switching, theme switching, step navigation, and initial profile-library rendering after the guided redesign.
- Fixed multiple dark-theme surface leaks across review, lifecycle, advanced, and guided summary cards, plus improved low-contrast helper copy in dark mode.
- Fixed the profile library data source so test artifacts and legacy fallback databases no longer repopulate the UI with stray `SVC-*` profiles.
- Fixed first-load library action labels and review badges so they remain visible before a manual locale switch.
- Fixed spacing and footer-layout regressions around wizard navigation actions and the `License Mozilla Public License 2.0` footer copy.
- Fixed advanced-document lower-section layout so right-column guidance no longer overflows off-screen.
- Fixed wizard step-title alignment for wrapped Russian labels and updated step five to the browser-native RU wording `Приватность и защита`.
- Fixed export-step rendering so `Shareable summary`/`Выжимка для передачи` now populates and copies correctly on step 8.
- Fixed schema-shell guided coverage rendering by removing a `ReferenceError` that interrupted locale refreshes and downstream wizard review updates.
- Fixed accessibility gaps in compare, clone handoff, lifecycle, export, disclosure, and review/jump flows.
- Fixed viewport regression risk by locking in guided-first shell ordering.
- Fixed remaining SQLite URL normalization edge cases with explicit regression tests.

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
