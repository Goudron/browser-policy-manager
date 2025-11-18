from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PolicyValueType = Literal["boolean", "integer", "number", "string", "array", "object"]


class PolicyProperty(BaseModel):
    """Describes a single property inside an object-type policy."""

    name: str
    type: PolicyValueType
    description_key: str | None = None

    # Constraints
    enum: list[Any] | None = None
    items_type: PolicyValueType | None = None
    minimum: float | None = None
    maximum: float | None = None
    default: Any | None = None
    required: bool = False


class PolicyDefinition(BaseModel):
    """Describes a single enterprise policy."""

    id: str
    type: PolicyValueType
    description_key: str | None = None

    categories: list[str] = Field(default_factory=list)
    min_version: str | None = None
    max_version: str | None = None
    deprecated: bool = False

    # Simple constraints (for non-object policies)
    enum: list[Any] | None = None
    items_type: PolicyValueType | None = None

    # Object schema
    properties: dict[str, PolicyProperty] = Field(default_factory=dict)
    additional_properties: bool = True


class PolicySchema(BaseModel):
    """Top-level schema for all policies for a given channel/version."""

    channel: str  # e.g. "release-145", "esr-140"
    version: str  # e.g. "145.0" or "140.5.0"
    source: str  # e.g. "mozilla-policy-templates-v7.5"

    policies: dict[str, PolicyDefinition] = Field(default_factory=dict)

    def get_policy(self, policy_id: str) -> PolicyDefinition | None:
        """Return a policy definition by ID if it exists."""
        return self.policies.get(policy_id)
