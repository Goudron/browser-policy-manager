# app/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import export as export_router
from app.api import policies as policies_router
from app.db import init_db

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("DB initialized")
    yield
    # Shutdown
    logger.info("App shutdown complete")


app = FastAPI(title="Browser Policy Manager", version="0.1.0", lifespan=lifespan)

# CORS (open during early dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(policies_router.router)
app.include_router(export_router.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Healthcheck."""
    return {"message": "Browser Policy Manager by Valery Ledovskoy"}
