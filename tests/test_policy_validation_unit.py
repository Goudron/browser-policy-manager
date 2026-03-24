from __future__ import annotations

import pytest

from app.core import policy_validation as validation


def _rich_policy_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "DisableTelemetry": {"type": "boolean"},
            "Extensions": {
                "type": "object",
                "properties": {
                    "Install": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["Install"],
                "additionalProperties": False,
            },
            "Proxy": {"$ref": "#/$defs/proxy"},
            "Mode": {
                "oneOf": [
                    {"const": "auto"},
                    {"type": "integer", "minimum": 1},
                ]
            },
        },
        "$defs": {
            "proxy": {
                "type": "object",
                "properties": {
                    "Mode": {"enum": ["system", "manual"]},
                },
                "required": ["Mode"],
                "additionalProperties": False,
            }
        },
    }


def test_policy_validation_error_stores_issues():
    issues = [
        validation.PolicyValidationIssue(
            policy="DisableTelemetry",
            path=["DisableTelemetry"],
            message="Bad value",
        )
    ]

    error = validation.PolicyValidationError(issues)

    assert str(error) == "Policy validation failed"
    assert error.issues == issues


def test_load_policy_schema_for_channel_uses_shared_loader(monkeypatch):
    sentinel = {"title": "Policies"}
    monkeypatch.setattr(validation, "load_schema", lambda channel: sentinel)

    assert validation.load_policy_schema_for_channel("esr-140") is sentinel


def test_load_policy_schema_for_channel_rejects_unknown_channel():
    with pytest.raises(ValueError, match="Unsupported channel"):
        validation.load_policy_schema_for_channel("beta-999")


def test_normalize_policy_document_schema_rejects_unknown_top_level_policies():
    schema = {
        "type": "object",
        "properties": {
            "DisableTelemetry": {"type": "boolean"},
        },
        "additionalProperties": True,
    }

    issues = validation.validate_profile_policies({"UnknownOne": True}, schema)

    assert len(issues) == 1
    assert issues[0].policy == "UnknownOne"
    assert issues[0].path == ["UnknownOne"]
    assert "unexpected" in issues[0].message


def test_validate_profile_policies_uses_json_schema_features():
    issues = validation.validate_profile_policies(
        {
            "UnknownOne": True,
            "DisableTelemetry": "bad",
            "Extensions": {"Extra": True},
            "Proxy": {},
            "Mode": False,
        },
        _rich_policy_schema(),
    )

    summary = {(issue.policy, tuple(issue.path), issue.message) for issue in issues}

    assert any(policy == "UnknownOne" and path == ("UnknownOne",) for policy, path, _ in summary)
    assert any(
        policy == "DisableTelemetry"
        and path == ("DisableTelemetry",)
        and "is not of type 'boolean'" in message
        for policy, path, message in summary
    )
    assert any(
        policy == "Extensions"
        and path == ("Extensions", "Extra")
        and "Additional properties are not allowed" in message
        for policy, path, message in summary
    )
    assert any(
        policy == "Proxy"
        and path == ("Proxy", "Mode")
        and "required property" in message
        for policy, path, message in summary
    )
    assert any(
        policy == "Mode"
        and path == ("Mode",)
        and "is not valid under any of the given schemas" in message
        for policy, path, message in summary
    )


def test_validate_profile_policies_or_raise_raises_for_invalid_payload():
    with pytest.raises(validation.PolicyValidationError) as excinfo:
        validation.validate_profile_policies_or_raise(
            {"DisableTelemetry": "bad"},
            _rich_policy_schema(),
        )

    assert excinfo.value.issues[0].policy == "DisableTelemetry"


def test_validate_profile_payload_with_schema_defaults_channel_and_validates(monkeypatch):
    captured = {}

    def _fake_load(channel: str):
        captured["channel"] = channel
        return {
            "type": "object",
            "properties": {"DisableTelemetry": {"type": "boolean"}},
        }

    monkeypatch.setattr(validation, "load_policy_schema_for_channel", _fake_load)

    validation.validate_profile_payload_with_schema({"policies": {"DisableTelemetry": True}})

    assert captured["channel"] == "release-148"


def test_validate_profile_payload_with_schema_rejects_non_mapping_policies(monkeypatch):
    monkeypatch.setattr(
        validation,
        "load_policy_schema_for_channel",
        lambda channel: {"type": "object", "properties": {}},
    )

    with pytest.raises(validation.PolicyValidationError) as excinfo:
        validation.validate_profile_payload_with_schema({"channel": "esr-140", "policies": [1]})

    assert excinfo.value.issues == [
        validation.PolicyValidationIssue(
            policy=None,
            path=["policies"],
            message="Expected object with policy mappings",
        )
    ]


def test_validate_profile_payload_with_schema_passes_explicit_channel_to_loader(monkeypatch):
    captured = {}

    def _fake_load(channel: str):
        captured["channel"] = channel
        return {"type": "object", "properties": {}}

    monkeypatch.setattr(validation, "load_policy_schema_for_channel", _fake_load)

    validation.validate_profile_payload_with_schema({"channel": "esr-140", "policies": {}})

    assert captured["channel"] == "esr-140"


def test_normalize_policy_document_schema_leaves_non_object_schema_unchanged():
    schema = {"type": "string"}

    assert validation._normalize_policy_document_schema(schema) is schema


def test_extend_error_path_handles_unmatched_required_and_multiple_additional_properties():
    required_error = validation.ValidationError(
        "missing property",
        validator="required",
        path=["Proxy"],
    )
    additional_error = validation.ValidationError(
        "Additional properties are not allowed ('Foo', 'Bar' were unexpected)",
        validator="additionalProperties",
        path=["Extensions"],
    )

    assert validation._extend_error_path(required_error) == ["Proxy"]
    assert validation._extend_error_path(additional_error) == ["Extensions"]


def test_policy_for_path_returns_none_for_empty_or_non_string_paths():
    assert validation._policy_for_path([]) is None
    assert validation._policy_for_path([0, "policy"]) is None
