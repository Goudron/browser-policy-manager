# Browser Policy Manager

[![CI](https://github.com/Goudron/browser-policy-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Goudron/browser-policy-manager/actions/workflows/ci.yml)

**Browser Policy Manager** is an open-source, on-premise web service for centralized management of browser policies — starting with full compatibility for [Firefox Enterprise Policies](https://github.com/mozilla/policy-templates).

It is designed for corporate and educational environments where unified browser configuration and compliance with internal security standards are required.

> **Note:** This project is compatible with Firefox Enterprise Policies but is not affiliated with Mozilla Foundation.  
> The “Firefox” trademark should not be used in derived product names.

---

## 🚀 Features

- Web UI built with **FastAPI + Jinja2**
- Generation and editing of `policies.json`
- Automated testing and CI (GitHub Actions)
- Runs on Linux/Ubuntu; Docker-ready architecture
- Extensible for other browsers (Chromium, Edge, Yandex, etc.)

---

## 🧱 Technology Stack

| Layer | Tools |
|-------|--------|
| Language | Python 3.13 |
| Framework | FastAPI |
| ASGI server | Uvicorn |
| Templates | Jinja2 |
| Testing | Pytest |
| CI/CD | GitHub Actions |
| License | MPL 2.0 |

---

## ⚙️ Quickstart (local)

bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000


---

## 🧪 Running Tests

bash
pytest -q


---

## 🔁 Continuous Integration

Every push and pull request is validated by [GitHub Actions](.github/workflows/ci.yml).

The badge at the top of this README reflects the latest CI status for the main branch.

---

## 📜 License

This project is licensed under the **Mozilla Public License 2.0 (MPL 2.0)**.  
See the [LICENSE](LICENSE) file for the full text.

© 2025 Valery Ledovskoy  
Maintained at [github.com/Goudron/browser-policy-manager](https://github.com/Goudron/browser-policy-manager)
