from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
UPSTREAM_HTML_PATH = BASE_DIR / "data" / "upstream" / "policy-templates" / "policy-templates.html"

SCHEMAS_DIR = BASE_DIR / "app" / "schemas" / "policies"
RELEASE_SCHEMA_PATH = SCHEMAS_DIR / "firefox-release-150.json"
ESR_SCHEMA_PATH = SCHEMAS_DIR / "firefox-esr-140.10.json"
LINUX_POLICIES_PATH = (
    BASE_DIR / "data" / "upstream" / "policy-templates" / "v7.10" / "linux-policies.json"
)

ENUM_WRAPPER_KEY = "__bpm_enum__"
SCALAR_TYPES = {"boolean", "integer", "number", "string"}
PREFERENCES_STATUS_ENUM = ["default", "locked", "user", "clear"]
PREFERENCES_TYPE_ENUM = ["number", "boolean", "string"]
HTTP_OR_HTTPS_PATTERN = r"^https?://"
HTTPS_URI_TEMPLATE_PATTERN = r"^https://.*%s.*$"
SEARCH_TERMS_PATTERN = r"\{searchTerms\}"
HANDLER_ACTION_ENUM = ["saveToDisk", "useHelperApp", "useSystemDefault"]


@dataclass
class UpstreamPolicyEntry:
    """A single policy as extracted from the documentation site."""

    name: str
    policy_key: str
    description: str
    compatibility: str | None
    section_text: str | None
    policies_json_snippet: str | None
    property_descriptions: dict[str, str] | None = None


@dataclass
class SchemaPolicyDefinition:
    """Representation of a policy in our internal JSON schema."""

    id: str
    type: str
    description_key: str
    categories: list[str]
    min_version: str | None
    max_version: str | None
    deprecated: bool
    enum: list[Any] | None
    items_type: str | None
    items: dict[str, Any] | None
    properties: dict[str, dict]
    additional_properties: bool
    additional_properties_schema: dict[str, Any] | None
    schema: dict[str, Any] | None = None
