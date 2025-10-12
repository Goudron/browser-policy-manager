"""
Browser Policy Manager — FastAPI application entrypoint.

Конвенции:
- Весь JSON-API монтируется под префиксом /api/v1.
- UI-маршруты (Jinja2/HTML) монтируются без /api.
- Бизнес-логика находится в app/services/*.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# -----------------------------------------------------------------------------
# Lifespan: современный способ регистрации startup/shutdown-событий
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется при запуске и завершении приложения."""
    try:
        from app.services.schema_service import available as schemas_available

        avail = schemas_available()
        print(
            "Schemas available on startup:",
            ", ".join(sorted(avail.values())),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Schemas scan failed on startup: {exc}")

    # --- приложение работает ---
    yield

    # --- при завершении приложения ---
    print("Application shutdown complete.")


# -----------------------------------------------------------------------------
# Конфигурация приложения
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
# Универсальная функция подключения роутеров
# -
