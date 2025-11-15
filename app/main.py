from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import export, health, policies, validation
from app.core.config import Settings as AppSettings

# Local settings instance for this module.
settings = AppSettings()


def create_app() -> FastAPI:
    """
    Application factory used by production runners and tests.

    It wires core middleware and includes all API routers.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=getattr(settings, "APP_VERSION", "0.1.0"),
    )

    # Basic CORS configuration. Tests do not depend on strict values here.
    allow_origins = getattr(settings, "cors_allow_origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(policies.router)
    app.include_router(export.router)
    app.include_router(validation.router)

    @app.get("/")
    def root() -> dict[str, str]:
        """
        Simple JSON landing endpoint used by smoke tests.
        """
        app_name = settings.APP_NAME
        return {
            "status": "ok",
            "app": app_name,  # explicitly required by tests
            "name": app_name,
            "version": getattr(settings, "APP_VERSION", "0.1.0"),
            "message": "Browser Policy Manager API is running",
        }

    return app


# Backward-compatible alias if tests or utilities import make_app.
def make_app() -> FastAPI:
    """Alias for create_app used in some tests."""
    return create_app()


# Default application instance used by tests and ASGI servers.
app = create_app()
