# Browser Policy Manager (BPM)

A minimal FastAPI backend to manage and export enterprise browser policy profiles.

- **Backend:** FastAPI (Python 3.13)
- **DB:** SQLAlchemy (Async) + Alembic
- **Default DB:** SQLite (aiosqlite) for local & CI
- **API:** `/api/policies/*` (CRUD), `/api/export/{id}/policies.json`
- **Health:** `/healthz`, `/readyz`

## Project status

Started in **2025**. Current sprint: **E** (“DB & Validation Foundation”).
Legacy UI (Jinja/i18n) and legacy import/export endpoints were removed to simplify the core.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip

# Install project (dev)
python -m pip install -e ".[dev]"

# Run
uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000/

## API

- `POST /api/policies` — create profile  
- `GET  /api/policies` — list profiles  
- `GET  /api/policies/{id}` — get profile  
- `PATCH /api/policies/{id}` — update profile  
- `DELETE /api/policies/{id}` — delete profile  
- `GET /api/export/{id}/policies.json` — export as JSON  
- `GET /healthz`, `GET /readyz` — probes  

Duplicate profile names return **409 Conflict**.

## Database & Migrations

- Default DB is SQLite (file `bpm.db`).  
- Alembic is configured in `alembic/` with initial migration for `policies`.

Create & upgrade:

```bash
alembic revision --autogenerate -m "your change"
alembic upgrade head
```

## Tests & QA

```bash
ruff check . --fix
ruff format .

mypy app
pytest -q
```

## Maintainer

© 2025–present Valery Ledovskoy  
License: **MPL-2.0**
