from __future__ import annotations

import importlib
import importlib.util
from contextlib import asynccontextmanager
from types import ModuleType
from typing import Optional, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Основной API для политик (обязательно подключается)
from .api import policies as policies_router

# Для автосоздания таблиц в dev/CI
from .db import engine
from .models.policy import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler (современная замена устаревшему @app.on_event).

    Выполняет автоматическое создание таблиц ORM для SQLite
    — полезно в локальной разработке и GitHub CI, где Alembic не запускается.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Здесь можно добавить shutdown-логику, например await engine.dispose()


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


def create_app() -> FastAPI:
    """Фабрика приложения FastAPI с Lifespan и всеми маршрутами."""
    app = FastAPI(
        title="Browser Policy Manager",
        version="0.2.3",
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

    # Локализация (если модуль существует)
    locale_mod = _optional_module("app.middleware.locale")
    LocalizeMiddleware = getattr(locale_mod, "LocalizeMiddleware", None) if locale_mod else None
    if LocalizeMiddleware is not None:
        app.add_middleware(LocalizeMiddleware)

    # --- Routers ---
    _include_if_present(app, _optional_module("app.api.health"), prefix="/api", tags=["health"])
    app.include_router(policies_router.router)  # /api/policies/*
    _include_if_present(app, _optional_module("app.api.export"))
    _include_if_present(app, _optional_module("app.api.import_policies"))
    _include_if_present(app, _optional_module("app.api.schemas"))
    _include_if_present(app, _optional_module("app.routes.ui"))

    return app


# Точка входа для Uvicorn/Gunicorn
app = create_app()
