# Browser Policy Manager (BPM)

A management and export tool for enterprise browser policies (inspired by Firefox Enterprise Policies).
The project provides a REST API (FastAPI), JSON/YAML schema validation, a Jinja-based UI, and export functionality.

- Backend: FastAPI (Python 3.13)
- Templates: Jinja2
- Validation: Pydantic + JSON Schema
- Localization: i18n (app/i18n/en.json, app/i18n/ru.json)
- Database: SQLAlchemy (Async)
  - Default: SQLite (aiosqlite) for local & CI use
  - Optional: PostgreSQL for production
- Migrations: Alembic
- Testing: pytest (+ pytest-asyncio), httpx
- Static analysis: Ruff, mypy

---------------------------------------------------------------------

## Project structure

app/
  api/                # REST endpoints
    policies.py
  core/
    config.py         # environment / settings
  services/
    policy_service.py # business logic for policies
  models/
    policy.py         # ORM model
  templates/          # Jinja2 templates (UI)
  i18n/
    en.json
    ru.json
  db.py               # async engine / session factory
  main.py             # FastAPI application entry
alembic/
  env.py
  script.py.mako
  versions/
.github/workflows/
  ci.yml
pyproject.toml
README.md

---------------------------------------------------------------------

## Installation

Requirements: Python 3.13

Commands:
  git clone https://github.com/Goudron/browser-policy-manager.git
  cd browser-policy-manager

  # install core dependencies (PEP 621)
  pip install -e .

  # install dev / CI extras
  pip install -e ".[dev]"

  # optional PostgreSQL extras
  pip install -e ".[postgres]"

This project uses pyproject.toml, not requirements.txt.
All dependencies follow PEP 621 and are grouped into optional extras.

---------------------------------------------------------------------

## Configuration

Environment variables are read from .env if present:

DATABASE_URL  – database connection string
  default: sqlite+aiosqlite:///./bpm.db
  PostgreSQL example (async): postgresql+asyncpg://user:pass@localhost:5432/bpm
ECHO_SQL      – true / false (enable SQL logging)

Example .env:
  DATABASE_URL=sqlite+aiosqlite:///./bpm.db
  ECHO_SQL=false

---------------------------------------------------------------------

## Database migrations (Alembic)

Alembic migrations live in the alembic/ directory.
Initial setup and upgrade:
  alembic upgrade head

Alembic reads the URL from alembic.ini by default.
For production, use a sync PostgreSQL URL (e.g., psycopg://...) or pass it via the -x argument if preferred.

---------------------------------------------------------------------

## Run the application

  uvicorn app.main:app --reload

The app will start on http://127.0.0.1:8000

---------------------------------------------------------------------

## REST API overview

Method | Path | Description
-------|------|-------------
GET    | /api/policies          | List policies
POST   | /api/policies          | Create a policy
GET    | /api/policies/{id}     | Retrieve a policy
PATCH  | /api/policies/{id}     | Update a policy
DELETE | /api/policies/{id}     | Delete a policy

Request/response schemas are defined in app/schemas/policy.py.

---------------------------------------------------------------------

## Testing

Command:
  pytest

Fixtures spin up an in-memory SQLite async engine and override the FastAPI DB dependency, so no external DB is required.
Integration tests for PostgreSQL can be added later in CI.

---------------------------------------------------------------------

## Localization (i18n)

- Stored in app/i18n/en.json and app/i18n/ru.json
- The middleware handles language selection automatically
- When adding new UI strings, update both localization files

---------------------------------------------------------------------

## Policy export

Exporters (JSON/YAML) are built from schema definitions and flag sets.
When adding new policies or schema versions, include corresponding validation tests.

---------------------------------------------------------------------

## Continuous Integration

GitHub Actions workflow performs:

1. Dependency installation via PEP 621:
     pip install -e ".[dev]"
2. Static analysis (Ruff, mypy)
3. Test suite run (pytest)

Target: always keep CI green.

---------------------------------------------------------------------

## Roadmap / Sprint plan

We use letter-based sprint identifiers.

Sprints A–D (completed):
  A: Core FastAPI scaffold + Jinja UI + i18n stubs
  B: Base policy schemas, JSON/YAML export, initial tests
  C: API / services refactor, stable CI (Ruff + mypy + pytest)
  D: Import/export pipeline and initial UI for profiles

Current Sprint E (BPM05):
  1. Replace temporary in-memory CRUD (/api/policies) with SQLAlchemy async backend
  2. Configure Alembic migrations and initial policies schema
  3. Extend JSON/YAML schemas and validation tests
  4. Begin a simple UI policy editor (Jinja + fetch API)
  5. Keep CI green (Ruff / Black / mypy / pytest)

Next planned sprints:
  F: Preset editor with i18n + export preview
  G: RBAC / authentication for multi-user instances
  H: Advanced imports (from files / URLs) + policy versioning + audit logging

---------------------------------------------------------------------

## Contribution guide

Pull requests are welcome — please include tests and keep CI passing.
Branch naming convention: feature/*, fix/*.
Main flow: dev → main.

---------------------------------------------------------------------

## License

This project is licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.
See the LICENSE file for details.

© 2025 Valery Ledovskoy. All rights reserved.
