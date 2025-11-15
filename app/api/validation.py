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
        { "ok": true }                       on success
        { "ok": false, "error": "<message>" } on validation failure
    """
    validator = _get_validator_or_404(profile)

    try:
        validator.validate(payload.document)
    except Exception as exc:  # noqa: BLE001 - we deliberately return a generic error payload
        return {"ok": False, "error": str(exc)}

    return {"ok": True}
