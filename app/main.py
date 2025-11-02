from pathlib import Path
from typing import Optional, Callable

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# --- Middleware (robust import; skip gracefully if symbol name differs) ---
add_security_headers: Optional[Callable] = None
try:
    from app.middleware.security import add_security_headers as _add_security_headers  # type: ignore[attr-defined]
    add_security_headers = _add_security_headers
except Exception:
    try:
        from app.middleware.security import security_headers_middleware as _add_security_headers  # type: ignore[attr-defined]
        add_security_headers = _add_security_headers
    except Exception:
        add_security_headers = None  # no-op if not available

# --- API routers (already define their own paths in the snapshot) ---
from app.api import health as health_api
from app.api import policies as policies_api
from app.api import export as export_api
from app.api import validation as validation_api

# Optional web router (do not crash if the module is absent)
try:
    from app.web import profiles as profiles_web  # type: ignore
except Exception:
    profiles_web = None

# --- Application instance ---
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
if add_security_headers is not None:
    app.middleware("http")(add_security_headers)

# Health endpoints must be reachable exactly at /health and /health/ready
app.include_router(health_api.router)

# IMPORTANT:
# Do NOT add an extra prefix here. The routers in the snapshot already expose the correct paths.
app.include_router(policies_api.router)
app.include_router(export_api.router)
app.include_router(validation_api.router)

# Web routes (optional)
if profiles_web:
    app.include_router(profiles_web.router)

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
