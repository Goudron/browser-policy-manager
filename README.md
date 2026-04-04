# Browser Policy Manager (BPM)

> Guided-first manager for Firefox enterprise policy profiles: create, review, compare, validate, and export profiles through a FastAPI backend and a task-oriented web UI.

---

## Overview

Browser Policy Manager helps administrators and security teams manage Firefox enterprise policy profiles without dropping straight into raw JSON or YAML.

Today the project provides:

- a canonical `/api/profiles` CRUD API
- a guided `/profiles` web workflow with targeted fallback into `Advanced document`
- schema-aware validation and export for Firefox policy documents
- profile review tools such as compare, clone-and-adjust, lifecycle review, and shareable summaries
- bundled ESR and Release Firefox policy schemas

**Author:** Valery Ledovskoy  
**Version:** `0.6.0-dev`  
**License:** [MPL-2.0](LICENSE)  
**Backend:** FastAPI + SQLAlchemy + Alembic  
**Frontend:** Jinja2 + self-hosted CSS/JS + self-hosted Monaco Editor bundle  
**Database:** SQLite by default  
**Python:** 3.13

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
| `GET /api/export/profiles` | Export profile collections as JSON or YAML |
| `GET /api/export/profiles/{id}` | Export one profile via `fmt=json|yaml` |
| `GET /api/export/profiles/{id}.json` | Export JSON |
| `GET /api/export/profiles/{id}.yaml` | Export YAML |
| `POST /api/validate/{version}` | Validate a Firefox policy document |
| `GET /health`, `GET /health/ready` | Health probes |

### Web UI

| Route | Description |
|---|---|
| `GET /profiles` | Main guided web UI for profile work |
| `GET /i18n/{locale}.json` | Localization catalogs (`en`, `ru`) |
| `GET /favicon.ico` | App favicon |

### Guided Workflow Highlights

- scenario-first profile setup
- recommended baselines and preset previews
- step-level undo/reset
- cross-step recent-changes memory
- targeted handoff into `Advanced document`
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

---

## Architecture

- One canonical data model powers API, guided UI, advanced editing, review, and export.
- Guided mode and `Advanced document` are two views over the same profile state.
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

Live Firefox policy checks run in an isolated project-local sandbox. See [`docs/firefox-live-testing.md`](docs/firefox-live-testing.md).

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

---

## Supported Firefox Schema Versions

| Channel | Version | Status |
|---|---|---|
| ESR | `140.9` | Active |
| Release | `149` | Active |
| Beta / Dev | — | Not supported |

BPM ships bundled internal schemas for the supported ESR and Release channels and keeps its own converted schema pipeline for the current Firefox policy model.

Supporting tooling and update notes live in:

- [`docs/firefox-schema-update-runbook.md`](docs/firefox-schema-update-runbook.md)

---

## Localization

- Base language: English
- Additional language: Russian
- UI catalogs are served at `/i18n/{locale}.json`

Russian UI copy has been cleaned up and standardized around the term `Техдокумент`.

---

## Quality Status

- non-live suite status: full `app/` coverage at `100%`
- guided-first viewport assumptions are documented and protected by regression checks
- accessibility follow-up for grouped controls, disclosure panels, and jump flows is completed
- live Firefox coverage remains intentionally separate from the non-live coverage target

Key project notes:

- [`docs/profile_wizard_ux_roadmap_2026-04-03.md`](docs/profile_wizard_ux_roadmap_2026-04-03.md)
- [`docs/profile_wizard_coverage_priority_register_2026-04-04.md`](docs/profile_wizard_coverage_priority_register_2026-04-04.md)
- [`docs/profile_wizard_advanced_only_boundaries_2026-04-04.md`](docs/profile_wizard_advanced_only_boundaries_2026-04-04.md)
- [`docs/wizard_viewport_qa_2026-03-31.md`](docs/wizard_viewport_qa_2026-03-31.md)

---

## Maintainer

**Valery Ledovskoy**  
📧 [valery@ledovskoy.com](mailto:valery@ledovskoy.com)  
Only emails with `[BPM]` in the subject line are reviewed.

© 2025-2026 • Released under [Mozilla Public License 2.0](LICENSE)
