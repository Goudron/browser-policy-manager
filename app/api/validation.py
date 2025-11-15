from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.validation import PolicySchemaValidator

router = APIRouter(prefix="/api/validate", tags=["validation"])


class ValidationRequest(BaseModel):
    """Request body for validation endpoints."""

    document: Any


_SUPPORTED_PROFILES: set[str] = {"esr-140", "release-144"}


def _get_validator_or_404(profile: str) -> PolicySchemaValidator:
    """Return schema validator for a known profile or raise HTTP 404."""
    if profile not in _SUPPORTED_PROFILES:
        raise HTTPException(status_code=404, detail=f"Unknown profile '{profile}'")
    return PolicySchemaValidator(profile)


@router.post("/{profile}")
def validate_profile(profile: str, payload: ValidationRequest) -> dict[str, Any]:
    """
    Validate a policy document for the given profile.

    Response shape:
        { "ok": true, "profile": "<profile>" }
        { "ok": false, "profile": "<profile>", "detail": "<message>", "error": "<message>" }
    """
    validator = _get_validator_or_404(profile)

    try:
        validator.validate(payload.document)
    except Exception as exc:  # noqa: BLE001 - tests expect a generic error payload
        message = str(exc)
        return {
            "ok": False,
            "profile": profile,
            # tests look for "detail", so we provide it
            "detail": message,
            # keep "error" for potential consumers expecting this key
            "error": message,
        }

    return {
        "ok": True,
        "profile": profile,
    }
