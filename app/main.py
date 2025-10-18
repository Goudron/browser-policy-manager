from __future__ import annotations

import asyncio
import importlib
import importlib.util
from contextlib import asynccontextmanager
from types import ModuleType
from typing import Optional, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Основной API для политик (обязательно подключается)
from .api import policies as policies_router

# Для автосоздания таблиц в dev/CI
from .db import engine
from .models.policy import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler: создаёт таблицы перед стартом (для дев/CI).
    Alembic остаётся источником истины для продакшена.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def _optional_module(path: str) -> Optional[ModuleType]:
    """Импортирует модуль, если он существует, иначе возвращает None."""
    spec = importlib.util.find_spec(path)
    if spec is None:
        return None
    return importlib.import_module(path)


def _include_if_present(
    app: FastAPI,
    mod: Optional[ModuleType],
    *,
    prefix: str = "",
    tags: Optional[Sequence[str]] = None,
) -> None:
    """Подключает router из необязательного модуля, если он найден."""
    if mod is None:
        return
    router = getattr(mod, "router", None)
    if router is None:
        return
    app.include_router(router, prefix=prefix, tags=list(tags) if tags else None)


async def _ensure_tables_async() -> None:
    """Асинхронно создаёт таблицы ORM (идемпотентно)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _ensure_tables_blocking() -> None:
    """
    Страхующая инициализация таблиц.
    На некоторых связках TestClient(app) может не запускать lifespan —
    поэтому вызываем создание таблиц при сборке приложения.
    """
    try:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_ensure_tables_async())
        finally:
            loop.close()
    except Exception:
        # Lifespan всё равно повторит попытку на старте
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Browser Policy Manager",
        version="0.3.0",
        lifespan=lifespan,
    )

    # --- Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(policies_router.router)  # /api/policies/*

    # Подключаем экспорт как опциональный модуль (есть в репозитории)
    _include_if_present(app, _optional_module("app.api.export"))

    # Корневой маршрут (минимальный UI-плейсхолдер)
    @app.get("/", response_class=HTMLResponse)
    async def root() -> str:
        return """<!doctype html>
<html>
  <head><title>Browser Policy Manager</title></head>
  <body>
    <h1>Browser Policy Manager</h1>
    <p>Owner: Valery Ledovskoy</p>
    <nav><a href="/api/policies">API: Policies</a></nav>
  </body>
</html>"""

    # Страхующая инициализация таблиц (важно для CI/тестов без lifespan)
    _ensure_tables_blocking()

    return app


# Точка входа для Uvicorn/Gunicorn
app = create_app()
