# Changelog

## 0.7.7

### Added
- Added bundled Firefox policy schemas for Firefox Release 151 and Firefox ESR 140.11.
- Added profile schema migration and runtime library normalization so profiles stored on Firefox Release 149/150 or ESR 140.9/140.10 are upgraded to the current supported schema channels when the library opens.
- Added UI coverage for new Firefox 151 policies, including `LocalNetworkAccess` in the guided privacy/site-data flow and `XSLTEnabled` in the Privacy/Security settings catalog.
- Added schema-bump runbook steps for profile normalization, UI impact review, README version checks, and starter-preset review.

### Changed
- Moved the project from `0.7.6` to `0.7.7`.
- Updated the supported schema documentation, product header copy, schema labels, examples, CI guards, and generated CIS Firefox layers to Firefox Release 151 / ESR 140.11.
- Refreshed Mozilla policy conversion logic for the 7.11 policy template release, including handling for new Linux-example-only policy entries and `ExtensionSettings.update_url` metadata.
- Reviewed starter presets against the new policy docs and kept their defaults unchanged where new policies could surprise intranet, local-device, or compatibility workflows.

### Quality
- Kept `mypy app`, `ruff check .`, and fast pytest with branch coverage green.
- Confirmed non-live `app/` coverage remains at `100%`.

## 0.7.6

### Added
- Added a more complete profile-library manager with clearer search, schema, validation, lifecycle, duplicate, export, and editor-entry actions.
- Added a schema-aware All settings catalog for full visual policy inspection and editing beyond the guided path.

### Changed
- Moved the project from `0.7.5` to `0.7.6`.
- Reworked the guided editor into a shorter task-first workflow while keeping AI and smart browser features as a standalone step.
- Decoupled All settings from the guided editor and made Release/ESR behavior explicit, including unsupported AI settings on ESR 140.10.
- Refined English and Russian UI localization, removed future-documentation placeholders, and updated the README for the current product shape.

### Fixed
- Fixed Russian layout issues where profile-library action buttons could overflow.
- Fixed outdated AI-step wording, stale provider-handoff messaging, and terminology drift around All settings and JSON editing.
- Fixed browser UI regressions around mode separation, search, schema-aware rendering, and editor navigation.

### Quality
- Refreshed regression coverage and completed full non-browser plus browser UI passes for the UI/UX release candidate.

## 0.7.5

### Added
- Added Firefox `policies.json` import as a first-class product workflow, including API support, validation, and profile-library import controls.
- Added dedicated profile workspace routes for library, visual editor, and advanced editor flows instead of treating `/profiles` as one combined surface.
- Added CIS Firefox compliance data, mappings, generated hardening layers, merge logic, tooling, and regression coverage.
- Added schema support for Firefox `release-150` and `esr-140.10`, plus migration coverage for stored profile schema versions.
- Added a local Chromium UI audit script and artifact/report flow for guided, advanced, layout, theme, and localization QA.
- Added explicit live Firefox setup guidance and version reporting for the isolated Selenium harness.
- Added dedicated `settings` and `json` profile editor routes, templates, and frontend entrypoints.
- Added a shared editor chrome across guided, settings, and JSON modes with unified save/validate/status controls.
- Added mode-specific regression coverage for DOM structure, route behavior, and multi-tab editor flows.

### Changed
- Moved the project from `0.7.0` to `0.7.5`.
- Promoted Firefox Enterprise `policies.json` to the main user-facing import/export contract and removed internal JSON/YAML handoff routes from the primary product surface.
- Reworked `/profiles` into a library-first workspace and moved editing into dedicated visual and advanced routes.
- Expanded guided coverage across shared-device, trust/auth, extensions governance, privacy hardening, upkeep, site access, home/search, language, AI, and compliance-aware surfaces.
- Aligned guided mode, advanced editing, validation, export, compare, lifecycle, and clone flows around one canonical profile model.
- Updated English and Russian product copy, route titles, and advanced-workflow terminology to match the current split workspace.
- Refreshed schema-update, live-testing, migration, and workspace backlog documentation to match the current repository shape.
- Raised non-live coverage for `app/` to `100%`.
- Refreshed the dependency/tooling stack and aligned the project baseline with Python `3.14`, including CI workflows and local tooling metadata.
- Split the profiles UI into four clear modes: library, guided editor, advanced settings, and JSON editor.
- Switched cross-mode navigation to a new-tab-first model and removed editor-only surfaces from the library route.
- Reduced frontend asset loading per mode so each route boots only the runtime it actually needs.
- Separated guided editing from settings/JSON concerns, moved advanced settings into a searchable settings-only surface, and turned the Monaco workflow into a dedicated JSON mode.

### Fixed
- Fixed route-context and frontend bootstrap regressions that affected locale switching, theme switching, step navigation, profile loading, and split-workspace rendering.
- Fixed multiple guided wizard bugs found during Chromium QA, including AI-step behavior, preset application, language switching, advanced handoff, export-step readiness, and `SearchEngines` document generation.
- Fixed dark-theme surface leaks, desktop/mobile overflow issues, and narrow-viewport regressions across library, guided, review, and advanced surfaces.
- Fixed profile-library state, labels, and rendering glitches that could surface stale fixtures, untranslated action copy, or inconsistent badges on first load.
- Fixed remaining advanced-workflow terminology drift where older `Advanced document` / `Техдокумент` copy still appeared.
- Fixed remaining SQLite URL normalization edge cases with explicit regression tests.

### Notes
- This release exposed architectural coupling across the library, guided editor, advanced editor, export/review surfaces, and shared frontend runtime. Those follow-up architecture issues are planned for `0.7.5-dev`.

## 0.7.0

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

## Earlier (2025-10-26)

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
