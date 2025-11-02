# app/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.api.health as health_module  # import the module to handle both names

# Routers
from app.api import export as export_router
from app.api import policies as policies_router
from app.api.validation import router as validation_router
from app.db import init_db
from app.middleware.security import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup and log shutdown."""
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Browser Policy Manager",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS (open during active development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Mount API routers
app.include_router(policies_router.router)
app.include_router(export_router.router)
app.include_router(validation_router)

# Health router: support either `router` or `health_router` and avoid double prefixing
_health_router = getattr(health_module, "router", None) or getattr(
    health_module, "health_router", None
)
if _health_router is None:
    raise RuntimeError("app.api.health must define `router` or `health_router`")

# If the health router already has a prefix (e.g., '/health'), include as-is.
# Otherwise, mount it under '/health' to satisfy tests expecting /health and /health/ready.
if getattr(_health_router, "prefix", ""):
    app.include_router(_health_router, tags=["health"])
else:
    app.include_router(_health_router, prefix="/health", tags=["health"])


# Simple root endpoint used by smoke tests
@app.get("/")
async def root() -> dict[str, str]:
    """Simple info endpoint."""
    return {"message": "Browser Policy Manager by Valery Ledovskoy"}
