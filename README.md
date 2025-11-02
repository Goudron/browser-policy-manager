# Browser Policy Manager (BPM)

> **Enterprise browser configuration manager** built with FastAPI — a unified backend and web UI to manage, validate, and export browser policy profiles for Firefox (Release & ESR).

---

## 🧭 Overview

**Browser Policy Manager (BPM)** provides administrators and security teams with a centralized tool to manage Firefox enterprise policies.  
It validates, stores, and exports structured configuration profiles compatible with Firefox’s `policies.json` format.

**Author:** Valery Ledovskoy  
**Version:** `0.3.0 (Sprint F – Release Preview)`  
**License:** [MPL-2.0](LICENSE)  
**Backend:** FastAPI + SQLAlchemy (async) + Alembic  
**Frontend:** Jinja2 + TailwindCSS + Monaco Editor (planned)  
**Database:** SQLite (default, async via `aiosqlite`)  
**Python:** 3.13

---

## 🚀 Current Capabilities

### ✅ Core API
| Endpoint | Description |
|-----------|--------------|
| `POST /api/policies` | Create a new browser policy profile |
| `GET /api/policies` | List all profiles (with filtering & pagination) |
| `GET /api/policies/{id}` | Retrieve one profile |
| `PATCH /api/policies/{id}` | Update profile |
| `DELETE /api/policies/{id}` | Soft delete |
| `GET /api/export/{id}/policies.json` | Export to JSON |
| `GET /api/export/{id}/policies.yaml` | Export to YAML |
| `POST /api/validate/{version}` | Validate a policy document |
| `GET /healthz`, `GET /readyz` | Health probes |

> Duplicate names return `409 Conflict`.  
> Soft-deleted profiles can be restored via the API.

---

## 🧱 Technology Stack

| Layer | Implementation |
|-------|----------------|
| **Framework** | FastAPI (async, OpenAPI auto-docs) |
| **Database** | SQLite (`sqlalchemy.ext.asyncio` + Alembic migrations) |
| **Schemas** | JSON Schema v2020–12 for Firefox policies |
| **Validation** | `jsonschema` with version-aware schema loader |
| **Testing** | `pytest`, `mypy`, `ruff`, `coverage ≥ 85%` |
| **CI/CD** | GitHub Actions (`dev` branch trigger) |
| **Security** | Custom middleware with strict HTTP headers (CSP, HSTS, X-Frame-Options) |

---

## 🧪 Quick Start

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip

# Install for development
pip install -e ".[dev]"

# Run app
uvicorn app.main:app --reload
```

Then open: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧰 Database & Migrations

- Default DB: `bpm.db` (SQLite).  
- Migrations live in `alembic/`.  
- Auto-generated migrations are supported.

```bash
alembic revision --autogenerate -m "add new field"
alembic upgrade head
```

To verify migration integrity:

```bash
pytest -q -k test_alembic_upgrade_head_on_sqlite_tmp
```

---

## 🧩 Current Schema Versions

| Channel | Version | Status |
|----------|----------|---------|
| **ESR** | 140 | ✅ Active |
| **Release** | 144 | ✅ Current |
| **Beta / Dev** | — | ❌ Not supported |

> BPM tracks the official [Firefox release calendar](https://whattrainisitnow.com/calendar/) and will later auto-update schemas for new releases (e.g., 145, 146…).

---

## 🌍 Localization (i18n)

- Base language: **English**  
- Additional: **Russian (ru)**  
- All UI elements and validation messages are localized via `/app/i18n/*.json`.

---

## 🧠 Development Guidelines

- Code comments and docstrings — **English only**.  
- User documentation and this README may include bilingual notes.  
- Default branch for development: **`dev`**  
  - CI runs on push/pull-request to `dev`.  
  - Manual merge to `main` produces a release.  
- Test coverage goal: **≥ 85%**  
- Code style enforced by:
  ```bash
  ruff check . --fix
  ruff format .
  mypy app
  pytest -q
  ```

---

## 🧭 Road Ahead

**Next sprint (G, version 0.4.0):**
- Dynamic schema loader (auto-fetch current Firefox Release & ESR).
- Cached schema store (`/data/schemas`).
- Version-aware validation and schema endpoint (`/api/schemas/latest`).
- Prepare for full UI with policy section breakdown.

**Later sprints:**
- Interactive UI for all policies (Monaco-based).
- Import/export in `.reg` and `.mobileconfig`.
- Templates and preset policy bundles.
- Chrome/Edge schema compatibility.

---

## 👤 Maintainer

**Valery Ledovskoy**  
📧 [valery@ledovskoy.com](mailto:valery@ledovskoy.com)

© 2025–present • Released under [Mozilla Public License 2.0](LICENSE)

---
