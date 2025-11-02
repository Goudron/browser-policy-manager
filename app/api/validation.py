# app/api/validation.py
# Validation API for Firefox Enterprise policies (ESR-140 / Release-144).
# - POST /api/validate/{profile}
#   Validates a JSON policy document (object) against the selected schema.
#   Supported profiles: "esr-140", "release-144".
#
# Notes:
# - No Beta, ESR 115/128 are supported in Sprint F.
# - Top-level type MUST be an object (enforced by validator, not by Pydantic).

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import BaseModel, ConfigDict

from app.core.validation import PolicySchemaValidator

router = APIRouter(tags=["validation"])


class ValidationRequest(BaseModel):
    """Input payload wrapper."""

    # Accept any JSON value; object requirement is enforced by the validator.
    document: Any

    # Pydantic v2 schema extras with request examples
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "document": {
                        "DisableTelemetry": True,
                        "DisableFirefoxAccounts": True,
                        "Preferences": {"browser.startup.homepage": "about:blank"},
                    }
                },
                {"document": 123},  # invalid: top-level must be object
            ]
        }
    )


class ValidationResponse(BaseModel):
    """Validation result DTO."""

    ok: bool
    profile: str
    detail: str | None = None

    # Pydantic v2 schema extras with response examples
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ok": True,
                    "profile": "esr-140",
                    "detail": None,
                },
                {
                    "ok": False,
                    "profile": "release-144",
                    "detail": "Top-level policy must be a JSON object",
                },
            ]
        }
    )


@router.post(
    "/api/validate/{profile}",
    response_model=ValidationResponse,
    summary="Validate a policy document against a Firefox Enterprise schema",
    description=(
        "Validate a JSON policy object against the selected schema.\n\n"
        "**Supported profiles:** `esr-140`, `release-144`.\n\n"
        '**Request body:** `{ "document": <any JSON> }` — the validator ensures the top-level is an object.\n\n'
        "**Notes:** Beta and legacy ESR (115/128) are not supported."
    ),
    responses={
        200: {
            "description": "Validation result",
            "content": {
                "application/json": {
                    "examples": {
                        "ok": {
                            "summary": "Valid document",
                            "value": {
                                "ok": True,
                                "profile": "esr-140",
                                "detail": None,
                            },
                        },
                        "failed": {
                            "summary": "Schema violation",
                            "value": {
                                "ok": False,
                                "profile": "release-144",
                                "detail": "Top-level policy must be a JSON object",
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Unsupported profile or initialization error",
            "content": {
                "application/json": {"example": {"detail": "Unsupported profile: beta"}}
            },
        },
        # 422 is FastAPI's validation error for malformed JSON / missing body, added implicitly.
    },
)
async def validate_policy(
    profile: str,
    payload: ValidationRequest = Body(
        ...,
        description="Wrapper object with the policy document to validate.",
    ),
) -> ValidationResponse:
    """
    Validate a policy document against the given profile schema.

    Parameters
    ----------
    profile : str
        One of: "esr-140", "release-144".
    payload : ValidationRequest
        JSON body: {"document": ...} (any JSON value; must be an object logically)

    Returns
    -------
    ValidationResponse
        ok=True if validation passes. Otherwise ok=False with detail.
    """
    try:
        validator = PolicySchemaValidator(profile)
    except Exception as e:
        # Provide a clean 400 for unsupported profile names or init issues
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        validator.validate(payload.document)
        return ValidationResponse(ok=True, profile=profile)
    except JsonSchemaValidationError as ve:
        # Normalized error path: 200 OK with ok=False and human-readable detail
        return ValidationResponse(
            ok=False,
            profile=profile,
            detail=str(ve.message or ve),
        )
