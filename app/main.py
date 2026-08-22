from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.api import documentation_assistant, export, health, local_model, profiles, validation
from app.core.config import Settings, get_settings
from app.core.response_assets import load_favicon_response_asset, load_locale_response_asset
from app.db import DatabaseRuntime
from app.documentation import router as documentation_router
from app.documentation.assistant_service import TrainingDocumentationAssistantService
from app.middleware.security import SecurityHeadersMiddleware
from app.services.amo_search import AmoSearchAdapter
from app.web import profiles as web_profiles

# Local settings instance for this module.
settings = get_settings()


def _resolve_path(path_value: str | Path, *, root_dir: Path | None = None) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return (root_dir or settings.ROOT_DIR) / path


def create_app(
    *,
    app_settings: Settings | None = None,
    database_runtime: DatabaseRuntime | None = None,
) -> FastAPI:
    """
    Application factory used by production runners and tests.

    It wires core middleware and includes all API routers.
    """
    configured_settings = app_settings or settings
    owned_database_runtime = database_runtime or DatabaseRuntime(configured_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            await owned_database_runtime.init()
            await owned_database_runtime.verify_release_schema()
            yield
        finally:
            try:
                amo_search_adapter = getattr(app.state, "amo_search_adapter", None)
                clear_amo_search_state = getattr(amo_search_adapter, "clear_all", None)
                if callable(clear_amo_search_state):
                    clear_amo_search_state()
                service = getattr(app.state, "documentation_assistant_service", None)
                shutdown_service = getattr(service, "shutdown", None)
                if callable(shutdown_service):
                    shutdown_service()
                runtime = getattr(app.state, "documentation_assistant_runtime", None)
                if runtime is not None:
                    runtime.shutdown()
            finally:
                await owned_database_runtime.dispose()

    app = FastAPI(
        title=configured_settings.APP_NAME,
        version=configured_settings.APP_VERSION,
        lifespan=lifespan,
    )
    app.state.database_runtime = owned_database_runtime
    # The adapter allocates no network resources. It owns only bounded, process-local
    # session-private AMO cache/rate state and is replaced by deterministic tests.
    app.state.amo_search_adapter = AmoSearchAdapter()

    # Model training and RAG promotion are intentionally beyond the 0.9.3 release boundary.
    # Keep the visible assistant functional without loading or inspecting local AI artifacts.
    app.state.documentation_assistant_service = TrainingDocumentationAssistantService()

    app.add_middleware(SecurityHeadersMiddleware)

    # Basic CORS configuration. Tests do not depend on strict values here.
    allow_origins = configured_settings.CORS_ALLOW_ORIGINS

    if configured_settings.ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.mount(
        "/static",
        StaticFiles(directory=str(configured_settings.STATIC_DIR)),
        name="static",
    )

    # Routers
    app.include_router(web_profiles.router)
    app.include_router(health.router)
    # DB-backed profiles CRUD with Firefox policy validation
    app.include_router(profiles.router)
    app.include_router(export.router)
    app.include_router(validation.router)
    app.include_router(local_model.router)
    app.include_router(documentation_assistant.router)
    app.include_router(documentation_router.router)

    @app.get("/i18n/{locale}.json", include_in_schema=False)
    async def locale_catalog(locale: str) -> Response:
        if locale not in configured_settings.SUPPORTED_LOCALES:
            raise HTTPException(status_code=404, detail="Locale not supported")

        locale_path = (
            _resolve_path(
                configured_settings.I18N_DIR,
                root_dir=configured_settings.ROOT_DIR,
            )
            / f"{locale}.json"
        )
        asset = load_locale_response_asset(locale_path)
        if asset is None:
            raise HTTPException(status_code=404, detail="Locale file not found")

        return Response(
            content=asset.content,
            media_type=asset.media_type,
            status_code=asset.status_code,
        )

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        favicon_path = configured_settings.STATIC_DIR / "favicon.ico"
        asset = load_favicon_response_asset(favicon_path)
        if asset is None:
            raise HTTPException(status_code=404, detail="Favicon file not found")
        return Response(
            content=asset.content,
            media_type=asset.media_type,
            status_code=asset.status_code,
        )

    @app.get("/")
    async def root() -> dict[str, str]:
        """
        Simple JSON landing endpoint used by smoke tests.
        """
        app_name = configured_settings.APP_NAME
        return {
            "status": "ok",
            "app": app_name,  # explicitly required by tests
            "name": app_name,
            "version": configured_settings.APP_VERSION,
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
