from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.api import export, health, profiles, validation
from app.core.config import get_settings
from app.db import get_session, init_db
from app.middleware.security import SecurityHeadersMiddleware
from app.services.profile_schema_normalization import normalize_legacy_profile_schema_versions
from app.web import profiles as web_profiles

# Local settings instance for this module.
settings = get_settings()


def _resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return settings.ROOT_DIR / path


def create_app() -> FastAPI:
    """
    Application factory used by production runners and tests.

    It wires core middleware and includes all API routers.
    """
    async def _run_startup_profile_normalization() -> None:
        await init_db()
        session_dependency = app.dependency_overrides.get(get_session, get_session)
        session_generator = session_dependency()
        session = await session_generator.__anext__()
        try:
            await normalize_legacy_profile_schema_versions(session)
            await session.commit()
        finally:
            try:
                await session_generator.__anext__()
            except StopAsyncIteration:
                pass

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await _run_startup_profile_normalization()
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)

    # Basic CORS configuration. Tests do not depend on strict values here.
    allow_origins = settings.CORS_ALLOW_ORIGINS

    if settings.ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

    # Routers
    app.include_router(web_profiles.router)
    app.include_router(health.router)
    # DB-backed profiles CRUD with Firefox policy validation
    app.include_router(profiles.router)
    app.include_router(export.router)
    app.include_router(validation.router)

    @app.get("/i18n/{locale}.json", include_in_schema=False)
    async def locale_catalog(locale: str) -> Response:
        if locale not in settings.SUPPORTED_LOCALES:
            raise HTTPException(status_code=404, detail="Locale not supported")

        locale_path = _resolve_path(settings.I18N_DIR) / f"{locale}.json"
        if not locale_path.is_file():
            raise HTTPException(status_code=404, detail="Locale file not found")

        return Response(content=locale_path.read_text(encoding="utf-8"), media_type="application/json")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        favicon_path = settings.STATIC_DIR / "favicon.ico"
        return Response(content=favicon_path.read_bytes(), media_type="image/x-icon")

    @app.get("/")
    async def root() -> dict[str, str]:
        """
        Simple JSON landing endpoint used by smoke tests.
        """
        app_name = settings.APP_NAME
        return {
            "status": "ok",
            "app": app_name,  # explicitly required by tests
            "name": app_name,
            "version": settings.APP_VERSION,
            "message": "Browser Policy Manager API is running",
        }

    return app


# Backward-compatible alias if tests or utilities import make_app.
def make_app() -> FastAPI:
    """
    Alias for create_app used in some tests.
    """
    return create_app()


# Default application instance used by tests and ASGI servers.
app = create_app()
