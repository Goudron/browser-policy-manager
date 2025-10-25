# app/schemas/policy.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PolicyBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    schema_version: str = Field(default="firefox-ESR", max_length=50)
    flags: Dict[str, Any] = Field(default_factory=dict)
    owner: Optional[str] = Field(default=None, max_length=255)


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    description: Optional[str] = None
    schema_version: Optional[str] = Field(default=None, max_length=50)
    flags: Optional[Dict[str, Any]] = None
    owner: Optional[str] = Field(default=None, max_length=255)


class PolicyRead(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
