from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables (.env supported)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Browser Policy Manager"
    # Default to SQLite for local/dev and CI. For production, prefer PostgreSQL.
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./bpm.db")
    ECHO_SQL: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance to avoid re-parsing on each import."""
    return Settings()
