from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api import validation as validation_module
from app.core.policy_validation import PolicyValidationError, PolicyValidationIssue


def test_get_schema_or_404_unknown_profile():
    with pytest.raises(HTTPException) as excinfo:
        validation_module._get_schema_or_404("beta-999")

    assert excinfo.value.status_code == 404
    assert "Unknown profile" in str(excinfo.value.detail)


def test_get_schema_or_404_loads_supported_profile(monkeypatch):
    sentinel = {"policies": {"DisableTelemetry": {"type": "boolean"}}}
    monkeypatch.setattr(validation_module, "load_policy_schema_for_channel", lambda profile: sentinel)

    result = validation_module._get_schema_or_404("esr-140")

    assert result is sentinel


@pytest.mark.anyio
async def test_validate_profile_422_with_empty_issues(monkeypatch):
    monkeypatch.setattr(validation_module, "_get_schema_or_404", lambda profile: {"policies": {}})

    def _raise_validation_error(document, schema):
        raise PolicyValidationError([])

    monkeypatch.setattr(validation_module, "validate_profile_policies_or_raise", _raise_validation_error)

    with pytest.raises(HTTPException) as excinfo:
        await validation_module.validate_profile(
            "esr-140",
            validation_module.ValidationRequest(document={"DisableTelemetry": True}),
        )

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == {"message": "Policy validation failed", "issues": []}


@pytest.mark.anyio
async def test_validate_profile_400_on_unexpected_error(monkeypatch):
    monkeypatch.setattr(validation_module, "_get_schema_or_404", lambda profile: {"policies": {}})

    def _raise_unexpected(document, schema):
        raise RuntimeError("boom")

    monkeypatch.setattr(validation_module, "validate_profile_policies_or_raise", _raise_unexpected)

    with pytest.raises(HTTPException) as excinfo:
        await validation_module.validate_profile(
            "release-145",
            validation_module.ValidationRequest(document={"DisableTelemetry": True}),
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == {"message": "Profile validation failed", "error": "boom"}


@pytest.mark.anyio
async def test_validate_profile_422_includes_first_issue_message(monkeypatch):
    monkeypatch.setattr(validation_module, "_get_schema_or_404", lambda profile: {"policies": {}})

    issues = [
        PolicyValidationIssue(
            policy="DisableTelemetry",
            path=["DisableTelemetry"],
            message="Expected type 'boolean', got 'str'",
        )
    ]

    def _raise_validation_error(document, schema):
        raise PolicyValidationError(issues)

    monkeypatch.setattr(validation_module, "validate_profile_policies_or_raise", _raise_validation_error)

    with pytest.raises(HTTPException) as excinfo:
        await validation_module.validate_profile(
            "esr-140",
            validation_module.ValidationRequest(document={"DisableTelemetry": "nope"}),
        )

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail["message"] == "Policy validation failed"
    assert excinfo.value.detail["issues"][0]["policy"] == "DisableTelemetry"
