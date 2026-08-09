from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
UPSTREAM_HTML_PATH = BASE_DIR / "data" / "upstream" / "policy-templates" / "policy-templates.html"

SCHEMAS_DIR = BASE_DIR / "app" / "schemas" / "policies"
DEFAULT_SCHEMA_TARGETS_PATH = BASE_DIR / "tools" / "firefox_schema_targets.json"

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


@dataclass(frozen=True)
class SchemaBuildTarget:
    """One independently generated bundled Firefox policy schema."""

    channel: str
    version: str
    source_tag: str
    documentation_input: Path
    linux_policies_input: Path
    output: Path


def _repository_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def load_schema_build_targets(
    path: Path = DEFAULT_SCHEMA_TARGETS_PATH,
) -> tuple[SchemaBuildTarget, ...]:
    """Load and validate the declarative, multi-channel schema build manifest."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ValueError(f"Schema target manifest {path} must contain a non-empty targets list")

    required = {
        "channel",
        "version",
        "source_tag",
        "documentation_input",
        "linux_policies_input",
        "output",
    }
    targets: list[SchemaBuildTarget] = []
    for raw_target in raw_targets:
        if not isinstance(raw_target, dict) or set(raw_target) != required:
            raise ValueError(
                f"Schema target manifest {path} has invalid target fields; expected {sorted(required)}"
            )
        if not all(isinstance(raw_target[field], str) and raw_target[field] for field in required):
            raise ValueError(f"Schema target manifest {path} contains an empty target field")
        targets.append(
            SchemaBuildTarget(
                channel=raw_target["channel"],
                version=raw_target["version"],
                source_tag=raw_target["source_tag"],
                documentation_input=_repository_path(raw_target["documentation_input"]),
                linux_policies_input=_repository_path(raw_target["linux_policies_input"]),
                output=_repository_path(raw_target["output"]),
            )
        )

    channels = [target.channel for target in targets]
    outputs = [target.output for target in targets]
    if len(channels) != len(set(channels)) or len(outputs) != len(set(outputs)):
        raise ValueError(f"Schema target manifest {path} contains duplicate channels or outputs")
    return tuple(targets)
