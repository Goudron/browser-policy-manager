# Browser Policy Manager

Browser Policy Manager (BPM) is a FastAPI application for building, reviewing, validating,
and exporting Firefox Enterprise policy profiles.

It is designed for system administrators and security teams who need a practical daily tool
for managing Firefox `policies.json` documents without forcing every workflow through raw JSON.

**Version:** `0.8.5`<br>
**License:** [MPL-2.0](LICENSE)<br>
**Python:** `3.14+`

## What's New In 0.8.5

BPM 0.8.5 is a maintenance and refactoring release focused on making the project easier to
change without altering its product contract.

- Split large frontend, backend, test, locale, and documentation ownership areas into smaller,
  more explicit modules and generated sources.
- Added reproducible frontend vendor, locale catalog, repository health, and release-readiness
  workflows through Make targets and contract checks.
- Introduced marker-based test layers, stronger database/app/cache isolation, and an opt-in
  pure-unit `pytest-xdist` pilot while keeping mandatory CI serial.
- Archived completed planning and audit documents behind a maintained docs index and manifest.

## Product Scope

BPM manages one canonical profile model and exposes it through four dedicated UI surfaces:

| Surface | Purpose |
|---|---|
| Profile library | Manage saved profiles, lifecycle state, schema channel, validation status, duplication, export, and editor entry points. |
| Guided editor | Build common Firefox policy profiles through a shorter task-first workflow. |
| All settings | Search and edit the full visual catalog of supported schema-backed controls. |
| JSON editor | Edit the complete Firefox Enterprise `policies.json` document directly. |

The UI is route-based rather than a single hidden-panel workspace. Saved profiles can be opened
in different modes in separate tabs. Unsaved drafts stay in the guided editor until the first save
creates a profile ID.

## Main Capabilities

- Database-backed Firefox policy profile library.
- Create, edit, duplicate, archive, restore, hard-delete, import, and export workflows.
- Firefox Enterprise `policies.json` import and export at the product boundary.
- Version-aware validation against bundled Firefox policy schemas.
- Guided editor for common administrator and security-team scenarios.
- Dedicated AI and smart browser features step for schema versions that support those policies.
- Schema-aware ESR/Release behavior, including ESR 140.11 handling for unsupported AI settings.
- All settings catalog for full visual inspection and policy editing outside the guided flow.
- JSON editor backed by the locally bundled Monaco editor.
- CIS Firefox hardening assets, starter presets, generated layers, and merge logic.
- English source UI with six active runtime locale catalogs.

## Supported Firefox Schemas

| Channel | Schema key | Status |
|---|---|---|
| Firefox ESR 140.11 | `esr-140.11` | Active |
| Firefox Release 151 | `release-151` | Active |

Bundled schema files live in `app/schemas/policies/`.

The selected schema controls validation, imported-profile normalization, available UI controls,
and schema-specific behavior. For example, Firefox ESR 140.11 does not expose supported AI policy
fields in the UI, while Firefox Release 151 exposes the current AI controls.

## Web Routes

| Route | Purpose |
|---|---|
| `GET /` | JSON root endpoint with app status and version. |
| `GET /profiles` | Profile library. |
| `GET /profiles/new` | Guided editor for a new draft. |
| `GET /profiles/{id}/edit` | Guided editor for an existing profile. |
| `GET /profiles/{id}/settings` | All settings catalog for an existing profile. |
| `GET /profiles/{id}/json` | JSON editor for an existing profile. |
| `GET /i18n/{locale}.json` | Localization catalog. |
| `GET /health` | Liveness probe. |
| `GET /health/ready` | Readiness probe. |

## API Surface

### Profiles

| Endpoint | Purpose |
|---|---|
| `GET /api/profiles` | List profiles with filtering, sorting, and pagination. |
| `GET /api/profiles/stats` | Get profile-library counts. |
| `GET /api/profiles/{id}` | Fetch one profile. |
| `POST /api/profiles` | Create a profile. |
| `PATCH /api/profiles/{id}` | Update a profile. |
| `DELETE /api/profiles/{id}` | Archive a profile. |
| `POST /api/profiles/{id}/restore` | Restore an archived profile. |
| `DELETE /api/profiles/{id}/hard` | Permanently delete a profile. |
| `DELETE /api/profiles/reset` | Permanently clear the profile library. |

### Firefox Import, Export, And Validation

| Endpoint | Purpose |
|---|---|
| `POST /api/profiles/import/firefox/policies.json` | Import a Firefox Enterprise `policies.json` document. |
| `GET /api/export/profiles/{id}/firefox/policies.json` | Export a profile as Firefox Enterprise `policies.json`. |
| `POST /api/validate/{profile}` | Validate a profile document against a supported schema channel. |

## Firefox `policies.json` Contract

BPM imports and exports the Firefox Enterprise `policies.json` shape at product boundaries.
Internally, profiles are stored in BPM's normalized model so the library, guided editor,
All settings, JSON editor, validation, and export flows can work on the same source of truth.

Choose the Firefox schema channel before import. The selected `schema_version` controls how the
document is validated and how the imported profile is normalized for editing.

Import endpoint:

```text
POST /api/profiles/import/firefox/policies.json
```

Export endpoint:

```text
GET /api/export/profiles/{id}/firefox/policies.json
```

JSON import example:

```json
{
  "name": "Workstation baseline",
  "description": "Imported Firefox deployment policy",
  "schema_version": "esr-140.11",
  "document": {
    "policies": {
      "DisableTelemetry": true,
      "Preferences": {
        "browser.tabs.warnOnClose": {
          "Value": true,
          "Status": "locked"
        }
      }
    }
  }
}
```

The import endpoint also accepts `multipart/form-data` with a `file` field containing a Firefox
`policies.json` file. Optional form fields include `name`, `description`, `schema_version`,
`owner`, and `compliance`.

Export example:

```json
{
  "policies": {
    "DisableTelemetry": true
  }
}
```

For migration and breaking-change notes around this contract, see
[`docs/firefox_policies_json_migration_notes_2026-04-14.md`](docs/firefox_policies_json_migration_notes_2026-04-14.md).

## UI Modes

### Profile Library

The library is the operational home for saved profiles. It supports profile search and filtering,
schema and lifecycle visibility, validation state, duplication, import, export, archive/restore,
and direct entry into the guided editor, All settings, or JSON editor.

### Guided Editor

The guided editor is the recommended starting point for most profile work. It uses scenario-first
sections, starter presets, compliance-aware baselines, and focused controls for common Firefox
administration tasks. It intentionally stays smaller than a full schema mirror.

The AI and smart browser features step remains a dedicated guided step. It shows current Firefox
Release AI controls where the selected schema supports them. For ESR 140.11, the step clearly
states that the schema does not support AI settings and does not render unsupported controls.

### All Settings

All settings is the full visual manager for schema-backed configuration. It provides search,
category navigation, guided-coverage markers, lower-level preference controls, and raw/unmapped
fallback handling for values that do not yet have a richer visual editor.

Use All settings when a profile needs complete inspection or detailed changes beyond the guided
workflow.

### JSON Editor

The JSON editor is the direct `policies.json` editing surface. It is useful for exact document
review, troubleshooting, migration checks, and values that are easier to handle as raw JSON.

## Localization

The primary project and UI source language is English. Product copy starts from
`app/i18n/en.json` and English maintainer documentation before it is localized.

BPM 0.8.5 ships a six-locale UI matrix:

| Locale | Native label | Status |
|---|---|---|
| `en` | English | Active source catalog |
| `ru` | Русский | Active localized catalog |
| `de` | Deutsch | Active localized catalog |
| `zh-CN` | 简体中文 | Active localized catalog |
| `fr` | Français | Active localized catalog |
| `es-ES` | Español | Active localized catalog |

Every listed locale is an active runtime catalog. A locale remains shippable only while its
`app/i18n/{locale}.json` file exists, keeps key and placeholder parity with English, passes
locale-quality checks, and receives terminology review. Unsupported or regional browser-language
matches fall back to the nearest active catalog, currently `en`, `ru`, `de`, `zh-CN`, `fr`, or
`es-ES`.

Mozilla, Firefox, browser UI, privacy, permission, add-on, translation, and policy terminology
should follow Mozilla Pontoon and SUMO style where applicable. English text should not appear in a
localized UI unless it is a brand name, policy key, product identifier, API term, JSON value, or
another intentionally untranslated technical value.

Current locale ownership is single-maintainer and manual-review based. External/community translation intake is not a separate maintained workflow yet; any proposed locale copy must follow
the project glossary, placeholder rules, Pontoon/SUMO terminology workflow, and locale QA runbook.

Localization catalogs are served from:

```text
GET /i18n/{locale}.json
```

Currently active runtime catalogs:

- `en`
- `ru`
- `de`
- `zh-CN`
- `fr`
- `es-ES`

## Architecture

- FastAPI application with Jinja templates.
- SQLAlchemy models with Alembic migrations.
- SQLite default database at `sqlite+aiosqlite:///./data/bpm.db`.
- Optional PostgreSQL support through the `postgres` extra.
- Self-hosted frontend assets under `app/static/`.
- Locally bundled Monaco editor for the JSON surface.
- Route-aware security headers and CSP middleware.
- Startup normalization for legacy stored schema versions.
- Bundled Firefox policy schemas under `app/schemas/policies/`.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
make dev
```

Open:

- API root: <http://127.0.0.1:8000/>
- Profile library: <http://127.0.0.1:8000/profiles>

## Development Commands

Quality checks:

```bash
make quality
```

Coverage-oriented run:

```bash
make coverage
```

Migrations:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Frontend vendor rebuild:

```bash
npm ci
make rebuild-frontend-vendor
make verify-frontend-vendor
```

## Testing

Default test runs exclude heavy browser-driven suites through project pytest settings.
Use the marker-aware Makefile targets for routine development:

```bash
make test-fast
make test-contract
make test-ui
make test-live
make test-release
```

The excluded heavy layers are:

- `browser_ui`
- `firefox_live`
- `firefox_live_amo`

Run them explicitly when needed:

```bash
make test-ui
make test-firefox-live
make test-firefox-live-amo
```

`browser_ui` is a compact Chromium/Selenium smoke layer. It checks Firefox
policies import, the Library, Guided editor, All settings, JSON editor, route
handoff links, and the Russian/Simplified Chinese locale pair. Deep UI behavior,
full locale quality, and edit/export edge cases stay in faster API and static
contract tests.

`pytest-xdist` is intentionally not enabled in mandatory BPM 0.8.5 CI. The
opt-in pure-unit pilot is available through `make test-unit-pilot` and
`make test-unit-xdist`. See
[`docs/architecture/pytest-xdist-readiness.md`](docs/architecture/pytest-xdist-readiness.md)
for the final BPM 0.8.5 decision and future adoption gates.

Live Firefox policy checks validate Firefox runtime behavior for exported `policies.json`
artifacts rather than the `/profiles` browser UI.

For local Chromium-based UI verification:

```bash
make local-chromium-ui-audit
```

That audit writes reports and screenshots under `artifacts/local_chromium_ui_audit/`.

## Project Layout

| Path | Purpose |
|---|---|
| `app/api/` | REST API routes. |
| `app/web/` | HTML route handlers and UI catalogs. |
| `app/static/` | Self-hosted frontend assets. |
| `app/templates/` | Jinja templates. |
| `app/schemas/` | Bundled policy schemas and schema helpers. |
| `app/services/` | Import, export, normalization, validation, and profile services. |
| `alembic/` | Database migrations. |
| `docs/` | Runbooks, migration notes, and project planning notes. |
| `tools/` | Local build, audit, conversion, and maintenance scripts. |
| `tests/` | Unit, API, web, browser UI, and live Firefox regression tests. |

## License

This project is licensed under the [MPL-2.0](LICENSE).

## Author

**Valery Ledovskoy**<br>
📧 [valery@ledovskoy.com](mailto:valery@ledovskoy.com)<br>
Only emails with `[BPM]` in the subject line are reviewed.

© 2025-2026 • Released under [Mozilla Public License 2.0](LICENSE)
