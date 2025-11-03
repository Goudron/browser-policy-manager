"""
Application configuration for Browser Policy Manager.

This file lives in app/core/config.py (not app/config.py).
It defines strongly-typed settings using Pydantic v2 BaseSettings.
Defaults target local/dev usage; values can be overridden via environment
variables or a .env file at the project root.

Sprint G additions:
- Schema management settings (SCHEMA_*) for Mozilla policy schemas
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables (.env supported)."""

    # Load from .env at repo root; ignore unknown variables to keep flexibility
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # -------------------------------------------------------------------------
    # Core application info
    # -------------------------------------------------------------------------
    APP_NAME: str = "Browser Policy Manager"
    APP_VERSION: str = "0.4.0-dev"
    DEBUG: bool = False

    # -------------------------------------------------------------------------
    # Server configuration
    # -------------------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # -------------------------------------------------------------------------
    # Database configuration
    # -------------------------------------------------------------------------
    # Local/dev default uses SQLite (async driver); override in production.
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bpm.db"
    DB_ECHO: bool = False

    # -------------------------------------------------------------------------
    # Internationalization / Localization
    # -------------------------------------------------------------------------
    DEFAULT_LOCALE: str = "en"
    SUPPORTED_LOCALES: list[str] = ["en", "ru"]
    I18N_DIR: str = "app/i18n"

    # -------------------------------------------------------------------------
    # Security / API
    # -------------------------------------------------------------------------
    API_PREFIX: str = "/api"
    ENABLE_CORS: bool = True
    CORS_ALLOW_ORIGINS: list[str] = ["*"]

    # -------------------------------------------------------------------------
    # Schema management (Sprint G)
    # -------------------------------------------------------------------------
    # Base URL of upstream Mozilla policy-templates repository (raw content)
    SCHEMA_BASE_URL: str = "https://raw.githubusercontent.com/mozilla/policy-templates"
    # Where we cache actual upstream policies-schema.json files in repo
    SCHEMA_CACHE_DIR: str = "app/schemas/mozilla"
    # HTTP timeout (seconds) for schema downloads
    SCHEMA_HTTP_TIMEOUT: int = 15

    # -------------------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------------------
    # This file is app/core/config.py → APP_DIR is .../app
    APP_DIR: Path = Path(__file__).resolve().parent.parent
    # Project root is one level above /app
    ROOT_DIR: Path = APP_DIR.parent
    DATA_DIR: Path = ROOT_DIR / "data"
    TEMPLATES_DIR: Path = APP_DIR / "templates"
    STATIC_DIR: Path = APP_DIR / "static"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton-like)."""
    return Settings()
