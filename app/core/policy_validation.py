"""
Policy validation helpers for Firefox Enterprise policies.

This module knows how to:
- Load internal JSON schemas for a given Firefox channel (ESR / release).
- Validate a mapping of policy_id -> value against those schemas.
- Provide a simple helper to validate a profile payload dict
  (intended to be called from services/API when saving a profile).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

JsonSchema = dict[str, Any]
JsonValue = Any


@dataclass
class PolicyValidationIssue:
    """Single validation problem for a policy or property."""

    policy: str | None
    path: list[str | int]
    message: str


class PolicyValidationError(ValueError):
    """Raised when policy validation fails for a profile."""

    def __init__(self, issues: list[PolicyValidationIssue]) -> None:
        super().__init__("Policy validation failed")
        self.issues = issues


def _project_root() -> Path:
    """
    Return project root directory.

    We assume this file is located at: <root>/app/core/policy_validation.py
    so root is two levels up from here.
    """
    return Path(__file__).resolve().parents[1]


def _schemas_dir() -> Path:
    """Return directory where internal policy schemas live."""
    return _project_root() / "schemas" / "policies"


@lru_cache(maxsize=4)
def load_policy_schema_for_channel(channel: str) -> JsonSchema:
    """
    Load internal policy schema JSON for the given channel.

    Supported channels (for now):
        - "esr-140"
        - "release-145"
    """

    if channel == "esr-140":
        filename = "firefox-esr-140.json"
    elif channel == "release-145":
        filename = "firefox-release-145.json"
    else:
        raise ValueError(f"Unsupported channel '{channel}'")

    path = _schemas_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(f"Internal policy schema not found: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def _python_type_matches(value: Any, expected: str) -> bool:
    """Check that Python runtime type matches the expected simple JSON type."""
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        # bool is a subclass of int; we explicitly exclude it here.
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    # If schema specifies an unknown type, do not block on it.
    return True


def _validate_scalar_or_array(
    value: Any,
    node_schema: JsonSchema,
    policy_id: str,
    path: list[str | int],
    issues: list[PolicyValidationIssue],
) -> None:
    """
    Validate scalar/array value against schema node.

    This function is used both for top-level policies and for object properties
    (where the property schema has the same shape: type/enum/items_type/etc).
    """
    expected_type = node_schema.get("type")
    enum = node_schema.get("enum")
    items_type = node_schema.get("items_type")

    if expected_type and not _python_type_matches(value, expected_type):
        issues.append(
            PolicyValidationIssue(
                policy=policy_id,
                path=list(path),
                message=f"Expected type '{expected_type}', got '{type(value).__name__}'",
            )
        )
        # If type is wrong, further checks are not useful here.
        return

    if expected_type == "array":
        if not isinstance(value, list):
            # Type mismatch was already recorded above, nothing more to do.
            return

        for idx, item in enumerate(value):
            elem_path = path + [idx]

            if enum is not None and item not in enum:
                issues.append(
                    PolicyValidationIssue(
                        policy=policy_id,
                        path=elem_path,
                        message=f"Value '{item}' is not allowed; expected one of {enum}",
                    )
                )

            if items_type and not _python_type_matches(item, items_type):
                issues.append(
                    PolicyValidationIssue(
                        policy=policy_id,
                        path=elem_path,
                        message=(
                            f"Expected item type '{items_type}', " f"got '{type(item).__name__}'"
                        ),
                    )
                )
    else:
        # Scalar value
        if enum is not None and value not in enum:
            issues.append(
                PolicyValidationIssue(
                    policy=policy_id,
                    path=list(path),
                    message=f"Value '{value}' is not allowed; expected one of {enum}",
                )
            )


def _validate_object_policy(
    value: Any,
    policy_schema: JsonSchema,
    policy_id: str,
    path: list[str | int],
    issues: list[PolicyValidationIssue],
) -> None:
    """
    Validate object-type policy.

    We only perform structural and type checks based on:
    - defined properties (if any),
    - additional_properties flag,
    - property-level type/enum/items_type.
    """
    if not isinstance(value, dict):
        issues.append(
            PolicyValidationIssue(
                policy=policy_id,
                path=list(path),
                message=(
                    f"Expected object for policy '{policy_id}', " f"got '{type(value).__name__}'"
                ),
            )
        )
        return

    properties: dict[str, JsonSchema] = policy_schema.get("properties") or {}
    additional = policy_schema.get("additional_properties", True)

    if properties and not additional:
        for key in value.keys():
            if key not in properties:
                issues.append(
                    PolicyValidationIssue(
                        policy=policy_id,
                        path=path + [key],
                        message=f"Unknown property '{key}' for policy '{policy_id}'",
                    )
                )

    for prop_name, prop_schema in properties.items():
        if prop_name not in value:
            # We do not enforce "required" here, because examples in Mozilla
            # templates are not strict spec; they are illustrative.
            continue

        prop_value = value[prop_name]
        prop_path = path + [prop_name]
        _validate_scalar_or_array(
            value=prop_value,
            node_schema=prop_schema,
            policy_id=policy_id,
            path=prop_path,
            issues=issues,
        )


def validate_profile_policies(
    profile_policies: dict[str, Any],
    schema: JsonSchema,
) -> list[PolicyValidationIssue]:
    """
    Validate a mapping of policy_id -> value against internal policy schema JSON.

    Returns list of issues (empty list means "valid").
    """
    issues: list[PolicyValidationIssue] = []
    policies_schema: dict[str, JsonSchema] = schema.get("policies") or {}

    for policy_id, value in profile_policies.items():
        policy_schema = policies_schema.get(policy_id)
        path: list[str | int] = ["policies", policy_id]

        if policy_schema is None:
            issues.append(
                PolicyValidationIssue(
                    policy=policy_id,
                    path=list(path),
                    message=f"Unknown policy '{policy_id}'",
                )
            )
            continue

        ptype = policy_schema.get("type")
        if ptype == "object":
            _validate_object_policy(
                value=value,
                policy_schema=policy_schema,
                policy_id=policy_id,
                path=path,
                issues=issues,
            )
        else:
            _validate_scalar_or_array(
                value=value,
                node_schema=policy_schema,
                policy_id=policy_id,
                path=path,
                issues=issues,
            )

    return issues


def validate_profile_policies_or_raise(
    profile_policies: dict[str, Any],
    schema: JsonSchema,
) -> None:
    """
    Validate a mapping of policy_id -> value and raise if any issues are found.
    """
    issues = validate_profile_policies(profile_policies, schema)
    if issues:
        raise PolicyValidationError(issues)


def validate_profile_payload_with_schema(payload: dict[str, Any]) -> None:
    """
    High-level helper for services/API.

    Expected payload shape (minimal):
        {
            "channel": "release-145" | "esr-140",
            "policies": {
                "DisableAppUpdate": true,
                "HttpAllowlist": ["http://example.org"],
                ...
            },
            ... other fields ignored ...
        }

    This helper:
      * figures out channel,
      * loads correct internal policy schema,
      * validates payload["policies"] against that schema.
    """

    channel = payload.get("channel") or "release-145"
    schema = load_policy_schema_for_channel(channel)

    policies = payload.get("policies") or {}
    if not isinstance(policies, dict):
        raise PolicyValidationError(
            [
                PolicyValidationIssue(
                    policy=None,
                    path=["policies"],
                    message="Expected object with policy mappings",
                )
            ]
        )

    validate_profile_policies_or_raise(policies, schema)
