from __future__ import annotations

import importlib
import importlib.util
from types import ModuleType
from typing import Optional, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Mandatory: DB-backed policies API (Sprint E)
from .api import policies as policies_router


def _optional_module(path: str) -> Optional[ModuleType]:
    """Return imported module if found, otherwise None (mypy-safe)."""
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
    """
    Include FastAPI router from an optional module if it exposes `router`.

    `tags` uses `Sequence[str]` to satisfy mypy type check; `prefix` is always str.
    """
    if mod is None:
        return None
    router = getattr(mod, "router", None)
    if router is None:
        return None
    app.include_router(router, prefix=prefix, tags=list(tags) if tags else None)
    return None


def create_app() -> FastAPI:
    app = FastAPI(title="Browser Policy Manager", version="0.2.0")

    # Basic CORS for local development; tighten in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # i18n middleware (optional)
    locale_mod = _optional_module("app.middleware.locale")
    LocalizeMiddleware = getattr(locale_mod, "LocalizeMiddleware", None) if locale_mod else None
    if LocalizeMiddleware is not None:
        app.add_middleware(LocalizeMiddleware)

    # --- API routers ---
    _include_if_present(app, _optional_module("app.api.health"), prefix="/api", tags=["health"])

    # Policies (DB-backed; mandatory for Sprint E)
    app.include_router(policies_router.router)  # already prefixed with /api/policies

    # Newly added to satisfy tests:
    _include_if_present(app, _optional_module("app.api.export"))  # has absolute paths
    _include_if_present(app, _optional_module("app.api.import_policies"))  # has absolute paths
    _include_if_present(app, _optional_module("app.api.schemas"))  # uses /api/v1/*

    # --- UI routes (server-rendered Jinja) ---
    _include_if_present(app, _optional_module("app.routes.ui"))

    return app


# ASGI app entry-point for Uvicorn/Gunicorn
app = create_app()
