from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.policy_validation import (
    PolicyValidationError,
    PolicyValidationIssue,
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)


@dataclass(frozen=True)
class FirefoxPoliciesImportIssue:
    """Single structural issue in an imported Firefox policies document."""

    path: list[str | int]
    message: str


class FirefoxPoliciesImportError(ValueError):
    """Raised when an imported Firefox policies document has an invalid shape."""

    def __init__(self, issues: list[FirefoxPoliciesImportIssue]) -> None:
        super().__init__("Firefox policies.json import failed")
        self.issues = issues


class FirefoxPoliciesDocumentValidationError(PolicyValidationError):
    """Raised when a Firefox policies document fails schema validation."""


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int | float):
        return "number"
    return type(value).__name__


def parse_firefox_policies_document(document: Any) -> dict[str, Any]:
    """
    Normalize a Firefox Enterprise ``policies.json`` document to internal flags.

    The public Firefox shape is ``{"policies": {...}}``. Browser Policy Manager
    stores only the inner policy mapping in ``Profile.flags``.
    """

    if not isinstance(document, dict):
        raise FirefoxPoliciesImportError(
            [
                FirefoxPoliciesImportIssue(
                    path=[],
                    message=f"Expected Firefox policies.json root object, got {_type_name(document)}",
                )
            ]
        )

    issues: list[FirefoxPoliciesImportIssue] = []

    if "policies" not in document:
        issues.append(
            FirefoxPoliciesImportIssue(
                path=["policies"],
                message="Missing required Firefox policies object",
            )
        )

    unsupported_keys = sorted(key for key in document if key != "policies")
    for key in unsupported_keys:
        shape_hint = ""
        if key == "flags":
            shape_hint = "; import Firefox policies.json with a top-level policies object instead"
        issues.append(
            FirefoxPoliciesImportIssue(
                path=[key],
                message=f"Unsupported top-level key '{key}'{shape_hint}",
            )
        )

    policies = document.get("policies")
    if "policies" in document and not isinstance(policies, dict):
        issues.append(
            FirefoxPoliciesImportIssue(
                path=["policies"],
                message=f"Expected policies to be an object, got {_type_name(policies)}",
            )
        )

    if issues:
        raise FirefoxPoliciesImportError(issues)

    assert isinstance(policies, dict)
    return dict(policies)


def validate_firefox_policies_document(document: Any, channel: str) -> dict[str, Any]:
    """
    Validate a Firefox Enterprise ``policies.json`` document for a schema channel.

    Returns normalized internal flags when the document is structurally valid and
    schema-valid. Schema validation issues are reported against the external
    Firefox document shape by prefixing paths with ``policies``.
    """

    flags = parse_firefox_policies_document(document)
    schema = load_policy_schema_for_channel(channel)

    try:
        validate_profile_policies_or_raise(flags, schema)
    except PolicyValidationError as exc:
        raise FirefoxPoliciesDocumentValidationError(
            [
                PolicyValidationIssue(
                    policy=issue.policy,
                    path=["policies", *issue.path],
                    message=issue.message,
                )
                for issue in exc.issues
            ]
        ) from exc

    return flags
