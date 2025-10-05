from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class PolicyInput(BaseModel):
    name: str
    description: Optional[str] = None
    schema_version: str = Field(..., description="e.g. firefox-ESR or 142")
    flags: Dict[str, bool] = {}
    dns_over_https: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    extension_settings: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None

class PolicyProfileOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schema_version: str
    payload: Dict[str, Any]
