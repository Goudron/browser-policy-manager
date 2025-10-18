from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    schema_version: str = Field(default="firefox-ESR", max_length=50)
    flags: Dict[str, Any] = Field(default_factory=dict)


class PolicyUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=500)
    schema_version: Optional[str] = Field(None, max_length=50)
    flags: Optional[Dict[str, Any]] = None


class PolicyOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schema_version: str
    flags: Dict[str, Any]

    class Config:
        from_attributes = True
