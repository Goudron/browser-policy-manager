from typing import Any

from pydantic import BaseModel, Field


class PolicyInput(BaseModel):
    name: str
    description: str | None = None
    schema_version: str = Field(..., description="e.g. firefox-ESR or 142")
    flags: dict[str, bool] = {}
    dns_over_https: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None
    extension_settings: dict[str, Any] | None = None
    extra: dict[str, Any] | None = None


class PolicyProfileOut(BaseModel):
    id: int
    name: str
    description: str | None
    schema_version: str
    payload: dict[str, Any]
