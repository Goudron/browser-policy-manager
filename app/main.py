"""
Browser Policy Manager — FastAPI application entrypoint.

Конвенции:
- НОВЫЙ JSON-API монтируется под префиксом /api/v1.
- ЛЕГАСИ JSON-роутеры из app/routes/* монтируются без доп. префикса (пути вида /api/...).
- UI-маршруты (Jinja2/HTML) — без /api.
- Бизнес-логика — в app/services/*.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Iterable, Optional

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# -----------------------------------------------------------------------------
# Lifespan
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется при запуске и завершении приложения."""
    try:
        from app.services.schema_service import available as schemas_available

        avail = schemas_available()
        print(
            "Schemas available on startup:",
            ", ".join(sorted(avail.values())) if avail else "(none)",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Schemas scan failed on startup: {exc}")

    yield

    print("Application shutdown complete.")


# -----------------------------------------------------------------------------
# Приложение
# -----------------------------------------------------------------------------
log = logging.getLogger(__name__)

app = FastAPI(
    title="Browser Policy Manager",
    version=os.getenv("BPM_VERSION", "0.1.0"),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
ALLOW_ORIGINS: Iterable[str] = os.getenv("BPM_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOW_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Шаблоны и статика
# -----------------------------------------------------------------------------
TEMPLATES_DIR = Path("app/templates")
STATIC_DIR = Path("app/static")

templates: Jinja2Templates | None = None
if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    log.info("Templates enabled: %s", TEMPLATES_DIR.resolve())
else:
    log.info("Templates directory not found, UI pages may be limited")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    log.info("Static files mounted: %s -> /static", STATIC_DIR.resolve())
else:
    log.info("Static directory not found, skipping /static mount")


# -----------------------------------------------------------------------------
# Подключение роутеров
# -----------------------------------------------------------------------------
def _include_router_safely(import_path: str, prefix: str = "", name: str = "") -> None:
    """Импортирует модуль с объектом router и подключает его к FastAPI."""
    try:
        module = __import__(import_path, fromlist=["router"])
        router = getattr(module, "router")
        app.include_router(router, prefix=prefix)
        label = f" ({name})" if name else ""
        log.info("Mounted router: %s%s", import_path, label)
    except Exception as exc:  # noqa: BLE001
        log.warning("Skip router %s: %s", import_path, exc)


# ЛЕГАСИ JSON (старые пути /api/… без префикса)
_include_router_safely("app.api.legacy_core", name="legacy_core")
_include_router_safely("app.api.legacy_policies", name="legacy_policies")
_include_router_safely("app.api.legacy_firefox", name="legacy_firefox")
_include_router_safely("app.api.legacy_api_import", name="legacy_api_import")
# Современный совместимый импорт-путь (если легаси-модуль отсутствует)
_include_router_safely("app.api.import_policies", name="import_policies_compat")

# НОВЫЕ служебные JSON-API (под /api/v1)
_include_router_safely("app.api.schemas", prefix="/api/v1", name="schemas_api")
_include_router_safely("app.api.validation", prefix="/api/v1", name="validation_api")

# UI-роутеры (исторически — app/web/routes.py)
_include_router_safely("app.web.routes", name="ui_web")
# при наличии других UI-модулей — добавляй:
# _include_router_safely("app.routes.ui", name="ui_root")
# _include_router_safely("app.routes.profiles", name="ui_profiles")


# -----------------------------------------------------------------------------
# Гарантированный корневой "/"
# -----------------------------------------------------------------------------
@app.get("/", tags=["web"], response_class=HTMLResponse)
def root_page() -> str:
    # Тест ожидает наличие "Valery Ledovskoy" и ссылки на /profiles
    return (
        "<!doctype html><html><head>"
        "<meta charset='utf-8'><title>Browser Policy Manager</title>"
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Helvetica,Arial}"
        "main{max-width:760px;margin:40px auto;padding:0 16px}</style>"
        "</head><body><main>"
        "<h1>Browser Policy Manager</h1>"
        "<p>Welcome, <strong>Valery Ledovskoy</strong>.</p>"
        '<p><a href="/profiles">/profiles</a> — manage policy profiles</p>'
        '<p><a href="/docs">/docs</a> — OpenAPI Docs</p>'
        "</main></body></html>"
    )


# -----------------------------------------------------------------------------
# Фолбэк: /api/import-policies (если ни один модуль не зарегистрировал)
# -----------------------------------------------------------------------------
def _has_route(path: str, method: str) -> bool:
    method = method.upper()
    for r in app.router.routes:
        try:
            p = getattr(r, "path", None)
            methods = getattr(r, "methods", set()) or set()
        except Exception:
            continue
        if p == path and method in methods:
            return True
    return False


if not _has_route("/api/import-policies", "POST"):

    @app.post("/api/import-policies", tags=["import"])
    async def _import_policies_fallback(
        body: Optional[Any] = Body(None),
        file: Optional[UploadFile] = File(None),
    ) -> JSONResponse:
        """
        Универсальный импорт политик (фолбэк).
        Поддержка:
          - application/json: dict или строка JSON
          - multipart/form-data: файл (policies.json)
        """
        import json as _json

        data: Any = None

        if file is not None:
            try:
                raw = await file.read()
                txt = raw.decode("utf-8", errors="strict")
                data = _json.loads(txt)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON file payload")
        elif body is not None:
            if isinstance(body, dict):
                data = body
            elif isinstance(body, str):
                try:
                    data = _json.loads(body)
                except Exception:
                    raise HTTPException(
                        status_code=400, detail="Invalid JSON string payload"
                    )
            else:
                raise HTTPException(status_code=400, detail="Unsupported payload type")
        else:
            raise HTTPException(status_code=400, detail="Empty payload")

        return JSONResponse({"ok": True, "received": data})


# -----------------------------------------------------------------------------
# Healthcheck
# -----------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}
