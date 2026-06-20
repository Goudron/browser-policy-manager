from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.policy_validation import (
    PolicyValidationError,
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)
from app.core.schema_channels import SUPPORTED_SCHEMA_CHANNEL_SET
from app.services.firefox_policy_import import (
    FirefoxPoliciesDocumentValidationError,
    FirefoxPoliciesImportError,
    validate_firefox_policies_document,
)

router = APIRouter(prefix="/api/validate", tags=["validation"])


class ValidationRequest(BaseModel):
    """Request body for policy validation endpoints."""

    document: Any = Field(
        ...,
        description=(
            "Firefox policies.json document to validate. A plain policy mapping "
            "is still accepted for internal compatibility."
        ),
        examples=[
            {
                "policies": {
                    "DisableAppUpdate": True,
                    "HttpAllowlist": ["http://example.org"],
                }
            }
        ],
    )


# Supported profiles are aligned with the bundled internal policy schemas.
_SUPPORTED_PROFILES: set[str] = set(SUPPORTED_SCHEMA_CHANNEL_SET)


def _get_schema_or_404(profile: str) -> dict[str, Any]:
    """Return schema JSON for the given profile or raise 404 if it is unknown."""
    if profile not in _SUPPORTED_PROFILES:
        raise HTTPException(status_code=404, detail=f"Unknown profile '{profile}'")
    try:
        return load_policy_schema_for_channel(profile)
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Schema for profile '{profile}' is not available",
        ) from exc


@router.post("/{profile}")
async def validate_profile(profile: str, payload: ValidationRequest) -> dict[str, Any]:
    """
    Validate a policy document for the given profile.

    Request example:
        POST /api/validate/release-152
        {
          "document": {
            "policies": {
              "DisableAppUpdate": true,
              "HttpAllowlist": ["http://example.org"]
            }
          }
        }

    Successful response:
        { "ok": true, "profile": "release-152" }

    Validation error response:
        {
          "ok": false,
          "profile": "release-152",
          "detail": "HttpAllowlist: Value 'http://evil.example' is not allowed; expected one of [...]",
          "error":  "HttpAllowlist: Value 'http://evil.example' is not allowed; expected one of [...]"
        }
    """
    schema = _get_schema_or_404(profile)
    document = payload.document

    if not isinstance(document, dict):
        message = "Expected object with policy mappings"
        return {
            "ok": False,
            "profile": profile,
            "detail": message,
            "error": message,
        }

    if "policies" in document:
        try:
            validate_firefox_policies_document(document, profile)
        except FirefoxPoliciesImportError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Firefox policies.json validation failed",
                    "issues": [
                        {
                            "policy": None,
                            "path": issue.path,
                            "message": issue.message,
                        }
                        for issue in exc.issues
                    ],
                },
            ) from exc
        except FirefoxPoliciesDocumentValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Policy validation failed",
                    "issues": [
                        {
                            "policy": issue.policy,
                            "path": issue.path,
                            "message": issue.message,
                        }
                        for issue in exc.issues
                    ],
                },
            ) from exc
        return {
            "ok": True,
            "profile": profile,
        }

    try:
        validate_profile_policies_or_raise(document, schema)
    except PolicyValidationError as exc:
        if exc.issues:
            first = exc.issues[0]
            policy_prefix = f"{first.policy}: " if first.policy else ""
            message = f"{policy_prefix}{first.message}"
        else:
            message = "Policy validation failed"

        raise HTTPException(
            status_code=422,
            detail={
                "message": "Policy validation failed",
                "issues": [
                    {
                        "policy": issue.policy,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in exc.issues
                ],
            },
        ) from exc
    except Exception as exc:
        message = str(exc)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Profile validation failed",
                "error": message,
            },
        ) from exc

    return {
        "ok": True,
        "profile": profile,
    }
