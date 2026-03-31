"""
Policy validation helpers for Firefox Enterprise policies.

This module wraps the jsonschema engine used by Mozilla-style policy schemas and
converts validation failures into the project-specific issue format consumed by
the API and web layers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jsonschema import FormatChecker, ValidationError
from jsonschema.validators import validator_for

from app.core.schema_channels import DEFAULT_RELEASE_SCHEMA_CHANNEL
from app.core.schemas_loader import SchemaNotFoundError, UnsupportedProfileError, load_schema

JsonSchema = dict[str, Any]

_REQUIRED_PROPERTY_RE = re.compile(r"'([^']+)' is a required property")
_UNEXPECTED_PROPERTIES_RE = re.compile(r"'([^']+)'")


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


def load_policy_schema_for_channel(channel: str) -> JsonSchema:
    """Load the JSON Schema used to validate policies for the given channel."""
    try:
        return load_schema(channel)
    except UnsupportedProfileError as exc:
        raise ValueError(f"Unsupported channel '{channel}'") from exc
    except SchemaNotFoundError as exc:
        raise ValueError(f"Schema for channel '{channel}' is not available") from exc


def _normalize_policy_document_schema(schema: JsonSchema) -> JsonSchema:
    """
    Apply BPM-specific strictness at the root policy-document level.

    Mozilla schemas describe the shape of known policy keys under ``properties``.
    For profile validation we reject undeclared top-level policies even when a
    cached schema snapshot was generated with ``additionalProperties: true``.
    """

    if schema.get("type") != "object":
        return schema

    properties = schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        return schema

    if schema.get("additionalProperties") is False:
        return schema

    normalized = dict(schema)
    normalized["additionalProperties"] = False
    return normalized


def _build_validator(schema: JsonSchema):
    prepared_schema = _normalize_policy_document_schema(schema)
    validator_class = validator_for(prepared_schema)
    validator_class.check_schema(prepared_schema)
    return validator_class(prepared_schema, format_checker=FormatChecker())


def _extend_error_path(error: ValidationError) -> list[str | int]:
    path = list(error.absolute_path)

    if error.validator == "required":
        match = _REQUIRED_PROPERTY_RE.search(error.message)
        if match:
            path.append(match.group(1))
            return path

    if error.validator == "additionalProperties":
        unexpected = _UNEXPECTED_PROPERTIES_RE.findall(error.message)
        if len(unexpected) == 1:
            path.append(unexpected[0])
            return path

    return path


def _policy_for_path(path: list[str | int]) -> str | None:
    if path and isinstance(path[0], str):
        return path[0]
    return None


def _issue_from_validation_error(error: ValidationError) -> PolicyValidationIssue:
    path = _extend_error_path(error)
    return PolicyValidationIssue(
        policy=_policy_for_path(path),
        path=path,
        message=error.message,
    )


def _validation_error_sort_key(error: ValidationError) -> tuple[list[str], list[str], str]:
    return (
        [str(part) for part in error.absolute_path],
        [str(part) for part in error.absolute_schema_path],
        error.message,
    )


def validate_profile_policies(
    profile_policies: dict[str, Any],
    schema: JsonSchema,
) -> list[PolicyValidationIssue]:
    """
    Validate a mapping of policy_id -> value against a Mozilla-compatible JSON Schema.

    Returns list of issues (empty list means "valid").
    """

    validator = _build_validator(schema)
    errors = sorted(validator.iter_errors(profile_policies), key=_validation_error_sort_key)
    return [_issue_from_validation_error(error) for error in errors]


def validate_profile_policies_or_raise(
    profile_policies: dict[str, Any],
    schema: JsonSchema,
) -> None:
    """Validate a mapping of policy_id -> value and raise if any issues are found."""
    issues = validate_profile_policies(profile_policies, schema)
    if issues:
        raise PolicyValidationError(issues)


def validate_profile_payload_with_schema(payload: dict[str, Any]) -> None:
    """
    High-level helper for services/API.

    Expected payload shape (minimal):
        {
            "channel": "release-149" | "esr-140.9",
            "policies": {
                "DisableAppUpdate": true,
                "HttpAllowlist": ["http://example.org"],
                ...
            },
            ... other fields ignored ...
        }
    """

    channel = payload.get("channel") or DEFAULT_RELEASE_SCHEMA_CHANNEL
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
