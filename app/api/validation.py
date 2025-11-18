from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.policy_validation import (
    PolicyValidationError,
    load_policy_schema_for_channel,
    validate_profile_policies_or_raise,
)

router = APIRouter(prefix="/api/validate", tags=["validation"])


class ValidationRequest(BaseModel):
    """Request body for policy validation endpoints."""

    # The document to validate. Expected to be a mapping of policy_id -> value,
    # for example:
    # {
    #   "DisableAppUpdate": true,
    #   "HttpAllowlist": ["http://example.org"],
    # }
    document: Any


# Add the new channel release-144 to the list of supported profiles.
_SUPPORTED_PROFILES: set[str] = {"esr-140", "release-144", "release-145"}


def _get_schema_or_404(profile: str) -> dict[str, Any]:
    """Return schema JSON for the given profile or raise 404 if it is unknown."""
    if profile not in _SUPPORTED_PROFILES:
        raise HTTPException(status_code=404, detail=f"Unknown profile '{profile}'")
    return load_policy_schema_for_channel(profile)


@router.post("/{profile}")
def validate_profile(profile: str, payload: ValidationRequest) -> dict[str, Any]:
    """
    Validate a policy document for the given profile.

    Request example:
        POST /api/validate/release-145
        {
          "document": {
            "DisableAppUpdate": true,
            "HttpAllowlist": ["http://example.org"]
          }
        }

    Successful response:
        { "ok": true, "profile": "release-145" }

    Validation error response:
        {
          "ok": false,
          "profile": "release-145",
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
