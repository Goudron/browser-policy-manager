# app/schemas/policy.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    # Keep free-form; business logic enforces supported values elsewhere
    schema_version: str = Field(default="esr-140", max_length=50)
    flags: dict[str, Any] = Field(default_factory=dict)
    owner: str | None = Field(default=None, max_length=255)


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    description: str | None = None
    schema_version: str | None = Field(default=None, max_length=50)
    flags: dict[str, Any] | None = None
    owner: str | None = Field(default=None, max_length=255)


class PolicyRead(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    is_deleted: bool

    # Pydantic v2 style config (replaces deprecated class Config)
    model_config = ConfigDict(from_attributes=True)
