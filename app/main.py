import importlib
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# API routers must be imported at the top (ruff E402)
from app.api import export as export_api
from app.api import health as health_api
from app.api import policies as policies_api
from app.api import validation as validation_api

# Optional web router module (load via importlib to keep mypy happy)
profiles_web: ModuleType | None
try:
    profiles_web = importlib.import_module("app.web.profiles")
except ImportError:
    profiles_web = None


def _register_function_middleware(app: FastAPI, func: Callable[..., Any]) -> None:
    """
    Attach a function-based HTTP middleware without calling app.middleware(...) at runtime.
    This avoids mypy's "None not callable" complaint while keeping behavior identical.
    """

    @app.middleware("http")
    async def _dynamic_security_mw(request, call_next):
        return await func(request, call_next)


# Resolve security middleware:
# 1) prefer a function `add_security_headers(request, call_next)` → register via helper above
# 2) else, if class `SecurityHeadersMiddleware` exists → app.add_middleware(...)
try:
    security_mod = importlib.import_module("app.middleware.security")
    add_fn = getattr(security_mod, "add_security_headers", None)
    mw_cls = getattr(security_mod, "SecurityHeadersMiddleware", None)
except ImportError:
    add_fn = None
    mw_cls = None

# Application instance
# NOTE: Keep "Valery Ledovskoy" in metadata because tests rely on it.
app = FastAPI(
    title="Browser Policy Manager — Valery Ledovskoy",
    description=(
        "Manage Firefox enterprise policies (ESR/Release). "
        "Maintainer: Valery Ledovskoy"
    ),
    version="0.3.0",
)

# Attach security headers middleware if available
if callable(add_fn):
    _register_function_middleware(app, add_fn)
elif mw_cls is not None:
    app.add_middleware(mw_cls)

# Health endpoints must be reachable exactly at /health and /health/ready
app.include_router(health_api.router)

# Routers already define their own paths; do NOT add prefix here
app.include_router(policies_api.router)
app.include_router(export_api.router)
app.include_router(validation_api.router)

# Web routes (optional)
if profiles_web is not None:
    router = getattr(profiles_web, "router", None)
    if router is not None:
        app.include_router(router)


# Minimal root page expected by tests (must include the author's name)
@app.get("/", include_in_schema=False)
def root_page() -> HTMLResponse:
    """Simple landing page used by smoke tests to check availability and author name."""
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Browser Policy Manager — Valery Ledovskoy</title>
        <meta name="viewport" content="width=device-width,initial-scale=1">
      </head>
      <body>
        <h1>Browser Policy Manager</h1>
        <p>Maintainer: <strong>Valery Ledovskoy</strong></p>
      </body>
    </html>
    """
    return HTMLResponse(html, status_code=200)


# Static assets (optional)
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
