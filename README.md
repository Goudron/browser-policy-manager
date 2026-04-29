# Browser Policy Manager (BPM)

> Library-first manager for Firefox enterprise policy profiles: import, create, review, compare, validate, and export deployable Firefox `policies.json` documents through a FastAPI backend and split web workspaces.

---

## Overview

Browser Policy Manager helps administrators and security teams manage Firefox enterprise policy profiles without dropping straight into raw `policies.json` unless they explicitly want the advanced editor.

Today the project provides:

- a canonical `/api/profiles` CRUD API
- a library-first `/profiles` workspace plus dedicated visual and advanced editor routes
- schema-aware import, validation, and export for Firefox policy documents
- CIS Firefox compliance layers and merge-aware starter workflows
- profile review tools such as compare, clone-and-adjust, lifecycle review, and shareable summaries
- bundled ESR and Release Firefox policy schemas

**Author:** Valery Ledovskoy  
**Version:** `0.7.0`  
**License:** [MPL-2.0](LICENSE)  
**Backend:** FastAPI + SQLAlchemy + Alembic  
**Frontend:** Jinja2 + self-hosted CSS/JS + self-hosted Monaco Editor bundle  
**Database:** SQLite by default  
**Python:** 3.14

---

## Current Scope

### Profiles API

| Endpoint | Description |
|---|---|
| `POST /api/profiles` | Create a profile |
| `GET /api/profiles` | List profiles with filtering and pagination |
| `GET /api/profiles/{id}` | Read one profile |
| `PATCH /api/profiles/{id}` | Update profile metadata or flags |
| `DELETE /api/profiles/{id}` | Archive profile |
| `POST /api/profiles/{id}/restore` | Restore archived profile |
| `DELETE /api/profiles/{id}/hard` | Delete permanently |
| `DELETE /api/profiles/reset` | Clear the profile library |
| `POST /api/profiles/import/firefox/policies.json` | Import a Firefox `policies.json` document |
| `GET /api/export/profiles/{id}/firefox/policies.json` | Export Firefox `policies.json` |
| `POST /api/validate/{version}` | Validate a Firefox policy document |
| `GET /health`, `GET /health/ready` | Health probes |

### Firefox `policies.json` Contract

BPM imports and exports the Firefox Enterprise `policies.json` shape at product boundaries.
The profile library keeps its own normalized state internally, but deployment handoff should use:

- import: `POST /api/profiles/import/firefox/policies.json`
- export: `GET /api/export/profiles/{id}/firefox/policies.json`

Import accepts either an `application/json` request body or `multipart/form-data` with a
`file` field containing the Firefox `policies.json` document plus form fields such as
`name`, `schema_version`, `description`, and `owner`.

Choose the Firefox schema channel before import. The selected `schema_version` controls
validation, so use `esr-140.10` for Firefox ESR 140.10 deployments or `release-150` for
current Release deployments.

Example JSON import body:

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

The export endpoint returns the deployable document directly:

```json
{
  "policies": {
    "DisableTelemetry": true
  }
}
```

### Web UI

| Route | Description |
|---|---|
| `GET /profiles` | Profile library and command center |
| `GET /profiles/new` | Guided visual editor for a new profile draft |
| `GET /profiles/{id}/edit` | Guided visual editor for an existing profile |
| `GET /profiles/{id}/advanced` | Full advanced `policies.json` editor |
| `GET /i18n/{locale}.json` | Localization catalogs (`en`, `ru`) |
| `GET /favicon.ico` | App favicon |

### Guided Workflow Highlights

- scenario-first profile setup
- recommended baselines and preset previews
- optional CIS Level 1 / Level 2 hardening overlays
- step-level undo/reset
- cross-step recent-changes memory
- targeted handoff into `Advanced editor`
- export explainability and shareable guided summary
- compare two profiles
- clone-and-adjust flow for derived drafts
- lifecycle review for saved, archived, restored, and derived profiles

### Firefox Coverage Highlights

The guided UI now covers high-value enterprise clusters such as:

- shared-device and kiosk-oriented setup
- certificates, trust, and enterprise authentication
- extensions rollout governance
- privacy and security hardening
- updates and browser upkeep
- site access and intranet routing
- home, startup, and search surfaces
- language and locale posture
- AI and smart browser surfaces

Advanced-only and handoff-only boundaries are documented so the wizard stays task-first instead of regressing into a schema mirror.

### Compliance Highlights

- versioned CIS Firefox source data and mappings live in-repo
- generated Level 1 / Level 2 hardening layers validate against supported schema channels
- starter flows can layer operational baselines with CIS hardening
- merge behavior and mapping coverage are protected by dedicated compliance tests

---

## Architecture

- One canonical profile model powers API, library actions, guided editing, advanced editing, review, import, and export.
- `/profiles`, `/profiles/new`, `/profiles/{id}/edit`, and `/profiles/{id}/advanced` are separate entry points with shared route-context bootstrapping.
- Guided mode and `Advanced editor` are two views over the same profile state.
- Coverage accounting is updated whenever guided support is expanded, so review/export counters stay honest.
- Firefox schema placement is resolved through a dedicated UI registry with explicit overrides plus safe inference.
- The profiles page is split into reusable Jinja partials and modular frontend bundles instead of one monolithic page script.
- Frontend runtime assets are self-hosted and checked into the repository.
- Security headers are enforced through middleware.

---

## Technology Stack

| Layer | Implementation |
|---|---|
| Framework | FastAPI |
| Database | SQLite + Alembic migrations |
| Validation | `jsonschema` with version-aware schema loading |
| Testing | `pytest`, `ruff`, `mypy`, `pytest-cov` |
| Coverage | `100%` non-live coverage for `app/` |
| CI/CD | GitHub Actions |
| Security | Middleware with strict HTTP headers |

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

- API root: <http://127.0.0.1:8000/>
- Web UI: <http://127.0.0.1:8000/profiles>

Useful local commands:

```bash
ruff check .
mypy app
pytest --cov=app --cov-branch --cov-report=term-missing
```

When `/profiles` vendor assets need a refresh:

```bash
npm install
npm run build:monaco
```

By default, `pytest` excludes the live Firefox suites marked `firefox_live` and `firefox_live_amo`, so standard local and CI runs stay deterministic. Run those suites explicitly with `-m firefox_live` or `-m firefox_live_amo`.

Live Firefox policy checks run in an isolated project-local sandbox and validate Firefox's runtime handling of exported `policies.json`, not the BPM `/profiles` UI flow. See [`docs/firefox-live-testing.md`](docs/firefox-live-testing.md).

For product-level UI verification on local Chromium, use:

```bash
./.venv/bin/python tools/run_local_chromium_ui_audit.py
```

That audit script exercises the library, guided flow, advanced handoff, localization, dark theme, and desktop/mobile layout expectations, then writes screenshots and reports under `artifacts/local_chromium_ui_audit/`.

---

## Database and Migrations

- Default database URL: SQLite
- Migrations live in `alembic/`
- Auto-generated migrations are supported

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

To verify migration integrity:

```bash
pytest -q -k test_alembic_upgrade_head_on_sqlite_tmp
```

Existing profile rows are upgraded by Alembic during schema bumps. The current migration chain rewrites
stored `profiles.schema_version` values from the previous supported Release / ESR pair to
`release-150` / `esr-140.10` when you run `alembic upgrade head`.

---

## Supported Firefox Schema Versions

| Channel | Version | Status |
|---|---|---|
| ESR | `140.10` | Active |
| Release | `150` | Active |
| Beta / Dev | — | Not supported |

BPM ships bundled internal schemas for the supported ESR and Release channels and keeps its own converted schema pipeline for the current Firefox policy model.

Supporting tooling and update notes live in:

- [`docs/firefox-schema-update-runbook.md`](docs/firefox-schema-update-runbook.md)
- [`docs/firefox_policies_json_migration_notes_2026-04-14.md`](docs/firefox_policies_json_migration_notes_2026-04-14.md)

---

## Localization

- Base language: English
- Additional language: Russian
- UI catalogs are served at `/i18n/{locale}.json`

Russian UI copy now uses `Расширенный редактор` and `Полный policies.json` for the advanced workflow.

## Project Language

English is the canonical language for repository documentation, planning notes, source comments, test names, and user-facing product copy unless a file is explicitly part of localization. New Markdown documents under `docs/` should be written in English.

---

## Quality Status

- non-live suite status: full `app/` coverage at `100%`
- main non-live test suite is green
- guided-first viewport assumptions are documented and protected by regression checks
- accessibility follow-up for grouped controls, disclosure panels, and jump flows is completed
- live Firefox coverage remains intentionally separate from the non-live coverage target
- local Chromium audit exists for product-level wizard/library/advanced QA

## Architecture Follow-up

The current `0.7.0` cycle closed a large amount of product and QA work, but it also exposed architectural coupling between:

- the library workspace
- guided editor flows
- advanced editor flows
- review/export surfaces
- shared frontend bootstrap/runtime state

That follow-up simplification work is planned for `0.7.5-dev`.

Key project notes:

- [`docs/profile_wizard_ux_roadmap_2026-04-03.md`](docs/profile_wizard_ux_roadmap_2026-04-03.md)
- [`docs/profile_wizard_coverage_priority_register_2026-04-04.md`](docs/profile_wizard_coverage_priority_register_2026-04-04.md)
- [`docs/profile_wizard_advanced_only_boundaries_2026-04-04.md`](docs/profile_wizard_advanced_only_boundaries_2026-04-04.md)
- [`docs/wizard_viewport_qa_2026-03-31.md`](docs/wizard_viewport_qa_2026-03-31.md)
- [`docs/profile_workspace_split_simplification_backlog_2026-04-21.md`](docs/profile_workspace_split_simplification_backlog_2026-04-21.md)
- [`docs/wizard_ai_export_bugfix_backlog_2026-04-21.md`](docs/wizard_ai_export_bugfix_backlog_2026-04-21.md)
- [`docs/firefox_policies_json_import_export_backlog_2026-04-13.md`](docs/firefox_policies_json_import_export_backlog_2026-04-13.md)
- [`docs/cis_firefox_implementation_roadmap_2026-04-12.md`](docs/cis_firefox_implementation_roadmap_2026-04-12.md)

---

## Maintainer

**Valery Ledovskoy**  
📧 [valery@ledovskoy.com](mailto:valery@ledovskoy.com)  
Only emails with `[BPM]` in the subject line are reviewed.

© 2025-2026 • Released under [Mozilla Public License 2.0](LICENSE)
