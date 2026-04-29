# app/schemas/profile.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.schema_channels import DEFAULT_SCHEMA_CHANNEL


class ProfileBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    # Keep free-form; business logic enforces supported values elsewhere
    schema_version: str = Field(default=DEFAULT_SCHEMA_CHANNEL, max_length=50)
    flags: dict[str, Any] = Field(default_factory=dict)
    compliance: dict[str, Any] | None = None
    owner: str | None = Field(default=None, max_length=255)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    description: str | None = None
    schema_version: str | None = Field(default=None, max_length=50)
    flags: dict[str, Any] | None = None
    compliance: dict[str, Any] | None = None
    owner: str | None = Field(default=None, max_length=255)
    expected_revision: int | None = Field(default=None, ge=1)


class ProfileRead(ProfileBase):
    id: int
    revision: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    is_deleted: bool

    # Pydantic v2 style config (replaces deprecated class Config)
    model_config = ConfigDict(from_attributes=True)
