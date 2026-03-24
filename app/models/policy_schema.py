from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PolicyValueType = Literal["boolean", "integer", "number", "string", "array", "object"]


class PolicyUiSection(BaseModel):
    """Describes a top-level wizard section for policy editing."""

    id: str
    title_key: str
    fallback: str
    order: int


class PolicyUiMetadata(BaseModel):
    """UI metadata used to place a policy in the guided wizard."""

    section: str
    subsection: str
    widget: str
    complexity: Literal["basic", "advanced"]
    recommended: bool = False
    preserve_unknown_fields: bool = True
    support_level: Literal["mapped", "fallback"] = "fallback"
    tags: list[str] = Field(default_factory=list)


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
    additional_properties: bool = True
    additional_property_type: PolicyValueType | None = None
    additional_property_enum: list[Any] | None = None
    item_properties: dict[str, PolicyProperty] = Field(default_factory=dict)
    properties: dict[str, PolicyProperty] = Field(default_factory=dict)
    additional_property_properties: dict[str, PolicyProperty] = Field(default_factory=dict)


class PolicyBranch(BaseModel):
    """Describes a single branch inside a oneOf policy."""

    type: PolicyValueType
    enum: list[Any] | None = None
    properties: dict[str, PolicyProperty] = Field(default_factory=dict)
    additional_properties: bool = True


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
    item_properties: dict[str, PolicyProperty] = Field(default_factory=dict)
    item_additional_properties: bool = True
    additional_property_type: PolicyValueType | None = None
    additional_property_properties: dict[str, PolicyProperty] = Field(default_factory=dict)

    # Object schema
    properties: dict[str, PolicyProperty] = Field(default_factory=dict)
    additional_properties: bool = True
    branches: list[PolicyBranch] = Field(default_factory=list)
    ui: PolicyUiMetadata | None = None


class PolicySchema(BaseModel):
    """Top-level schema for all policies for a given channel/version."""

    channel: str  # e.g. "release-148", "esr-140"
    version: str  # e.g. "148.0" or "140.8"
    source: str  # e.g. "mozilla-policy-templates-v7.8"

    policies: dict[str, PolicyDefinition] = Field(default_factory=dict)
    ui_sections: list[PolicyUiSection] = Field(default_factory=list)

    def get_policy(self, policy_id: str) -> PolicyDefinition | None:
        """Return a policy definition by ID if it exists."""
        return self.policies.get(policy_id)
