# Browser Policy Manager (BPM)

> **Enterprise browser configuration manager** built with FastAPI — a unified backend and web UI to manage, validate, and export browser policy profiles for Firefox (Release & ESR).

---

## 🧭 Overview

**Browser Policy Manager (BPM)** provides administrators and security teams with a centralized tool to manage Firefox enterprise policies.  
It validates, stores, and exports structured configuration profiles compatible with Firefox’s `profiles.json` format.

**Author:** Valery Ledovskoy  
**Version:** `0.4.0-dev`  
**License:** [MPL-2.0](LICENSE)  
**Backend:** FastAPI + SQLAlchemy + Alembic  
**Frontend:** Jinja2 + TailwindCSS + Monaco Editor  
**Database:** SQLite (default)  
**Python:** 3.13

---

## 🚀 Current Capabilities

### ✅ Core API
| Endpoint | Description |
|-----------|--------------|
| `POST /api/profiles` | Create a new browser policy profile |
| `GET /api/profiles` | List all profiles (with filtering & pagination) |
| `GET /api/profiles/{id}` | Retrieve one profile |
| `PATCH /api/profiles/{id}` | Update profile |
| `DELETE /api/profiles/{id}` | Soft delete |
| `POST /api/profiles/{id}/restore` | Restore a soft-deleted profile |
| `GET /api/export/profiles` | Export profile collections as JSON or YAML |
| `GET /api/export/profiles/{id}` | Export one profile via `fmt=json|yaml` |
| `GET /api/export/profiles/{id}.json` | Export to JSON |
| `GET /api/export/profiles/{id}.yaml` | Export to YAML |
| `POST /api/validate/{version}` | Validate a policy document |
| `GET /health`, `GET /health/ready` | Health probes |

### ✅ Web UI
| Route | Description |
|-------|-------------|
| `GET /profiles` | Main browser UI for profile editing and guided Firefox policy composition |
| `GET /i18n/{locale}.json` | Localization catalogs (`en`, `ru`) |
| `GET /favicon.ico` | App favicon |

> Duplicate names return `409 Conflict`.  
> Soft-deleted profiles can be restored via the profiles API.
> The canonical CRUD API is `/api/profiles`; the old `/api/policies` layer has been removed.

### ✅ Current Architecture

- Canonical CRUD flow: `profiles` API + `PolicyService` + SQLite/Alembic.
- Export endpoints read from the same DB-backed model as the main API.
- Firefox policy validation is enforced on profile create/update.
- The `/profiles` UI uses the canonical `/api/profiles` API directly.
- The Firefox web experience is now schema-driven and split into modular catalogs for general settings, home/startup, privacy, search, sync, starter presets, manual controls, and inline editors for complex policies.
- Policy UI placement is resolved through a dedicated Firefox policy UI registry with explicit overrides plus safe fallbacks inferred from schema structure.
- The profile editor page has been decomposed into reusable Jinja partials and modular frontend bundles instead of one monolithic template/script.
- Security headers are enabled for HTTP responses.

---

## 🧱 Technology Stack

| Layer | Implementation |
|-------|----------------|
| **Framework** | FastAPI (OpenAPI auto-docs) |
| **Database** | SQLite + Alembic migrations |
| **Schemas** | JSON Schema v2020–12 for Firefox policies |
| **Validation** | `jsonschema` with version-aware schema loader |
| **Testing** | `pytest`, `mypy`, `ruff`, branch coverage, `coverage ≥ 85%` gate |
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

Then open:

- API root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Web UI: [http://127.0.0.1:8000/profiles](http://127.0.0.1:8000/profiles)

Useful local quality commands:

```bash
ruff check .
mypy app
pytest --cov=app --cov-branch --cov-report=term-missing
```

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
| **Release** | 148 | ✅ Current |
| **Beta / Dev** | — | ❌ Not supported |

> BPM currently ships with bundled internal schemas for the supported ESR and Release channels.
> Mozilla's official `v7.8` release package for Firefox 148 / ESR 140.8 ships docs and platform templates, but not a standalone raw `policies-schema.json`, so BPM keeps a local converted schema pipeline.

### Schema Tooling

- `tools/convert_policies_from_upstream.py` is now a thin entrypoint over a reusable `tools.convert_policies_from_upstream_lib` package.
- The conversion pipeline is split into HTML parsing, snippet parsing, inference, semantic hints, schema emission, and CLI layers.
- Bundled release schema has been advanced from Firefox Release 145 to Release 148.

---

## 🌍 Localization (i18n)

- Base language: **English**  
- Additional: **Russian (ru)**  
- UI localization catalogs are served at `/i18n/{locale}.json`.

---

## 🧠 Development Guidelines

- Code comments and docstrings — **English only**.  
- User documentation and this README may include bilingual notes.  
- Default branch for development: **`dev`**  
  - CI runs on push/pull-request to `dev`.  
  - Manual merge to `main` produces a release.  
- Test coverage goal: **≥ 85%**  
- Current local suite status: `236 passed`, `100%` line coverage, `100%` branch coverage for `app/`.  
- Code style enforced by:
  ```bash
  ruff check . --fix
  ruff format .
  mypy app
  pytest --cov=app --cov-branch --cov-report=term-missing
  ```

---

## 🧭 Current Focus

- Keep the `profiles` API and web UI aligned around one data model.
- Expand and refine the schema-driven Firefox workflow in `/profiles`.
- Continue simplifying schema/version management around bundled ESR/Release schemas.
- Keep CI quality gates green across `ruff`, `mypy`, and coverage artifact generation.

## 🗺️ Roadmap

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
