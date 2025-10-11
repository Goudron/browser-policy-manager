# 🧭 Browser Policy Manager

**Browser Policy Manager (BPM)** — a lightweight **FastAPI**-based backend for managing and exporting browser policy configurations (e.g., Firefox ESR `policies.json`).  
It serves as both a practical example and a backend core for enterprise browser-management solutions.

---

## 🚀 Features

- REST API for managing browser policy profiles (CRUD)
- Export profiles as `policies.json`
- Import policies (via JSON body or upload UI)
- Built-in localization (English / Russian)
- Minimal Jinja2 web UI
- SQLite or in-memory storage
- Full test coverage with **pytest**
- Code linting and formatting via **Ruff**
- Continuous integration via **GitHub Actions**

---

## 🧩 Project Structure

```
app/
├── api/                # REST endpoints (health, policies, export, schemas)
├── routes/             # UI routes (index, import, etc.)
├── i18n/               # en.json / ru.json localization catalogs
├── middleware/         # locale middleware
├── models/             # SQLModel entities and DTOs
├── services/           # business logic (policy_service, schema_service)
├── exporters/          # exporters (e.g., Firefox policies.json)
├── templates/          # Jinja2 templates (index.html, import.html)
└── main.py             # FastAPI entry point
```

---

## ⚙️ Installation & Run

### Requirements
- Python ≥ 3.13  
- pip ≥ 24.0  

### Local run

```bash
git clone https://github.com/Goudron/browser-policy-manager.git
cd browser-policy-manager
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
# For development & CI:
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

Open in browser:  
👉 http://localhost:8000

---

## 🌐 API Examples

Create a policy profile:
```bash
curl -X POST http://localhost:8000/api/policies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Default",
    "description": "Base profile",
    "schema_version": "firefox-ESR",
    "flags": {"DisableTelemetry": true, "DisablePocket": true}
  }'
```

Export a profile:
```bash
curl http://localhost:8000/api/export/<profile_id>/policies.json
```

Import policies:
```bash
curl -X POST http://localhost:8000/api/import-policies \
  -H "Content-Type: application/json" \
  -d '{"policies": {"DisableTelemetry": true}}'
```

---

## 🌍 Localization (i18n)

- Language catalogs: `app/i18n/en.json`, `app/i18n/ru.json`  
- Middleware: `app/middleware/locale.py`  
- Template filter: `t("key")`  
- Language auto-selected via `lang` cookie or `Accept-Language` header  

---

## 🧪 Testing

```bash
pytest -q
```

All 15 tests pass ✅  
Covers CRUD, import/export, and UI smoke tests.

---

## 🧼 Lint & Format

Handled by **Ruff**:

```bash
ruff check --fix .
ruff format .
```

Configuration: `pyproject.toml` (Python 3.13, line length 100).

---

## 🧰 Continuous Integration

GitHub Actions workflow runs:
1. Install dependencies (`requirements.txt` + `requirements-dev.txt`)
2. Lint & format checks (Ruff)
3. Full pytest suite  

Workflow file: `.github/workflows/ci.yml`

---

## 🧾 License

Licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.  
See the [LICENSE](LICENSE) file for full text.  

© 2025 **Valery Ledovskoy** ([Goudron](https://github.com/Goudron))

---

## 📈 Development Roadmap

| Stage | Status | Description |
|--------|---------|-------------|
| Sprint A | ✅ Completed | Core architecture, CRUD API, i18n, tests, CI pipeline |
| Sprint B | 🔜 Planned | Web CRUD UI, JSON upload import, dark theme, session storage |
| Sprint C | ⏳ Backlog | Chrome / Edge policy support, REST authorization |

---

## 🤝 Contacts

- Author: **Valery Ledovskoy** ([Goudron](https://github.com/Goudron))  
- Repository: [github.com/Goudron/browser-policy-manager](https://github.com/Goudron/browser-policy-manager)

---
