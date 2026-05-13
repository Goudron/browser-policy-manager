# Browser Policy Manager

Browser Policy Manager is a FastAPI application for managing Firefox enterprise policy profiles.
It combines a profile library, a guided editor, an advanced settings surface, and a raw JSON editor
on top of one canonical profile model.

The project is aimed at administrators and security teams who need to create, review, validate,
compare, import, and export deployable Firefox Enterprise `policies.json` documents without being
forced into raw JSON for every workflow.

**Version:** `0.7.5`  
**License:** [MPL-2.0](LICENSE)  
**Python:** `3.14+`

## What the project provides

- A database-backed profile library with create, update, archive, restore, and hard-delete flows.
- A guided editor for scenario-first profile authoring.
- A searchable advanced settings surface for policy-level editing without living in raw JSON.
- A dedicated JSON editor for direct `policies.json` work.
- Version-aware validation against bundled Firefox policy schemas.
- Firefox Enterprise `policies.json` import and export at the product boundary.
- CIS Firefox hardening layers and starter presets for common profile baselines.
- English and Russian UI catalogs served directly by the app.

## Current web routes

| Route | Purpose |
|---|---|
| `GET /` | JSON root endpoint with app status and version |
| `GET /profiles` | Profile library |
| `GET /profiles/new` | Guided editor for a new unsaved draft |
| `GET /profiles/{id}/edit` | Guided editor for an existing profile |
| `GET /profiles/{id}/settings` | Advanced settings editor |
| `GET /profiles/{id}/json` | Raw JSON editor |
| `GET /profiles/{id}/advanced` | Compatibility redirect to `/profiles/{id}/json` |
| `GET /i18n/{locale}.json` | Localization catalogs |
| `GET /health` | Liveness probe |
| `GET /health/ready` | Readiness probe |

The UI is split into four product modes:

- `Library`
- `Guided editor`
- `Advanced settings`
- `JSON editor`

Cross-mode navigation is new-tab-first for saved profiles. Unsaved drafts stay on `/profiles/new`
until the first save creates a real profile ID.

## Current API surface

### Profiles

| Endpoint | Purpose |
|---|---|
| `GET /api/profiles` | List profiles with filtering, sorting, and pagination |
| `GET /api/profiles/stats` | Get library counts |
| `GET /api/profiles/{id}` | Fetch one profile |
| `POST /api/profiles` | Create a profile |
| `PATCH /api/profiles/{id}` | Update a profile |
| `DELETE /api/profiles/{id}` | Archive a profile |
| `POST /api/profiles/{id}/restore` | Restore an archived profile |
| `DELETE /api/profiles/{id}/hard` | Permanently delete a profile |
| `DELETE /api/profiles/reset` | Hard-delete the whole profile library |

### Firefox import, export, and validation

| Endpoint | Purpose |
|---|---|
| `POST /api/profiles/import/firefox/policies.json` | Import a Firefox Enterprise `policies.json` document into the library |
| `GET /api/export/profiles/{id}/firefox/policies.json` | Export a profile as Firefox Enterprise `policies.json` |
| `POST /api/validate/{profile}` | Validate a document against a supported schema channel |

## Firefox `policies.json` contract

BPM imports and exports the Firefox Enterprise `policies.json` shape at product boundaries.
Internally, profiles are stored in BPM's own normalized model, but deployment handoff is always
through Firefox's public document format.

Canonical endpoints:

- import: `POST /api/profiles/import/firefox/policies.json`
- export: `GET /api/export/profiles/{id}/firefox/policies.json`

Choose the Firefox schema channel before import. The selected `schema_version` controls how the
document is validated and how the imported profile is normalized for editing.

Currently supported schema channels:

- `esr-140.10`
- `release-150`

JSON import example:

```json
{
  "name": "Workstation baseline",
  "description": "Imported Firefox deployment policy",
  "schema_version": "esr-140.10",
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

For the migration and breaking-change notes around this contract, see
[`docs/firefox_policies_json_migration_notes_2026-04-14.md`](docs/firefox_policies_json_migration_notes_2026-04-14.md).

## Supported Firefox schema versions

| Channel | Status |
|---|---|
| `esr-140.10` | Active |
| `release-150` | Active |

Bundled schema files currently live under `app/schemas/policies/`.

Schema maintenance references:

- [`docs/firefox-schema-update-runbook.md`](docs/firefox-schema-update-runbook.md)
- [`docs/firefox_policies_json_migration_notes_2026-04-14.md`](docs/firefox_policies_json_migration_notes_2026-04-14.md)

## Guided editing and compliance

The guided editor is built around scenario-first authoring rather than a raw schema mirror.
The current product surface includes:

- starter presets such as blank, basic corporate, classroom kiosk, and SOC hardening
- guided coverage for enterprise browser areas like homepage/search, extensions, privacy,
  updates, certificates, authentication, site access, language, and AI-related controls
- save and validate flows shared with the other editor modes
- explicit handoff into advanced settings or JSON when a task no longer fits guided editing

The repository also contains CIS Firefox compliance assets and merge logic for combining starter
profiles with hardening layers. Relevant references:

- [`docs/cis_firefox_update_runbook_2026-04-13.md`](docs/cis_firefox_update_runbook_2026-04-13.md)
- [`docs/cis_firefox_benchmark_feature_analysis_2026-04-12.md`](docs/cis_firefox_benchmark_feature_analysis_2026-04-12.md)

## Architecture notes

- FastAPI application with SQLAlchemy models and Alembic migrations.
- SQLite is the default database via `sqlite+aiosqlite:///./data/bpm.db`.
- Optional PostgreSQL drivers are included through the `postgres` extra.
- Profiles UI assets are self-hosted under `app/static/`.
- Monaco is bundled locally rather than pulled from a CDN.
- Security headers are applied by middleware with a route-aware CSP for `/profiles`.
- Legacy stored schema versions are normalized on application startup.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

- API root: <http://127.0.0.1:8000/>
- Profiles UI: <http://127.0.0.1:8000/profiles>

## Development commands

Quality checks:

```bash
ruff check .
mypy app
pytest
```

Coverage-oriented run:

```bash
pytest --cov=app --cov-branch --cov-report=term-missing
```

Migrations:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Frontend vendor rebuild:

```bash
npm install
npm run build:monaco
```

## Testing notes

Default test runs exclude the heavy browser-driven suites through project pytest settings:

- `browser_ui`
- `firefox_live`
- `firefox_live_amo`

Run them explicitly when needed:

```bash
pytest -m browser_ui
pytest -m firefox_live
pytest -m firefox_live_amo
```

Live Firefox policy checks validate Firefox runtime behavior for exported `policies.json`
artifacts rather than the `/profiles` browser UI. See
[`docs/firefox-live-testing.md`](docs/firefox-live-testing.md).

For local Chromium-based UI verification:

```bash
./.venv/bin/python tools/run_local_chromium_ui_audit.py
```

That audit writes reports and screenshots under `artifacts/local_chromium_ui_audit/`.

## Project layout

| Path | Purpose |
|---|---|
| `app/api/` | REST API routes |
| `app/web/` | HTML route handlers and UI catalogs |
| `app/static/` | Self-hosted frontend assets |
| `app/templates/` | Jinja templates |
| `app/schemas/` | Bundled policy schemas and schema helpers |
| `app/services/` | Import, export, normalization, and profile services |
| `alembic/` | Database migrations |
| `docs/` | Runbooks, migration notes, and product backlogs |
| `tools/` | Local build, audit, and maintenance scripts |

## Localization

- Default locale: English
- Additional locale: Russian
- Catalog route: `/i18n/{locale}.json`

## License

This project is licensed under the [MPL-2.0](LICENSE).

## Author

**Valery Ledovskoy**  
📧 [valery@ledovskoy.com](mailto:valery@ledovskoy.com)  
Only emails with `[BPM]` in the subject line are reviewed.

© 2025-2026 • Released under [Mozilla Public License 2.0](LICENSE)
