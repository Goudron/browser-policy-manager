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

    assert validation.load_policy_schema_for_channel("esr-140.12") is sentinel


def test_load_policy_schema_for_channel_rejects_unknown_channel():
    with pytest.raises(ValueError, match="Unsupported channel"):
        validation.load_policy_schema_for_channel("beta-999")


def test_load_policy_schema_for_channel_reports_missing_schema(monkeypatch):
    def _raise_missing(channel: str):
        raise validation.SchemaNotFoundError("missing")

    monkeypatch.setattr(validation, "load_schema", _raise_missing)

    with pytest.raises(ValueError, match="Schema for channel 'release-152' is not available"):
        validation.load_policy_schema_for_channel("release-152")


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


def test_validate_profile_policies_for_channel_reuses_compiled_validator(monkeypatch):
    validation.clear_policy_validator_cache()
    build_calls = []

    class _Validator:
        def iter_errors(self, profile_policies):
            assert profile_policies == {"DisableTelemetry": True}
            return []

    def _fake_load(channel: str):
        assert channel == "release-152"
        return {
            "type": "object",
            "properties": {"DisableTelemetry": {"type": "boolean"}},
        }

    def _fake_build(schema: dict):
        build_calls.append(schema)
        return _Validator()

    monkeypatch.setattr(validation, "load_policy_schema_for_channel", _fake_load)
    monkeypatch.setattr(validation, "_build_validator", _fake_build)

    for _ in range(2):
        assert (
            validation.validate_profile_policies_for_channel(
                {"DisableTelemetry": True},
                "release-152",
            )
            == []
        )

    assert len(build_calls) == 1
    validation.clear_policy_validator_cache()


def test_validate_profile_policies_or_raise_for_channel_raises_for_invalid_payload(monkeypatch):
    issues = [
        validation.PolicyValidationIssue(
            policy="DisableTelemetry",
            path=["DisableTelemetry"],
            message="Bad value",
        )
    ]
    monkeypatch.setattr(
        validation,
        "validate_profile_policies_for_channel",
        lambda profile_policies, channel: issues,
    )

    with pytest.raises(validation.PolicyValidationError) as excinfo:
        validation.validate_profile_policies_or_raise_for_channel(
            {"DisableTelemetry": "bad"},
            "release-152",
        )

    assert excinfo.value.issues == issues


def test_validate_profile_payload_with_schema_defaults_channel_and_validates(monkeypatch):
    captured = {}

    def _fake_validate(policies, channel: str):
        assert policies == {"DisableTelemetry": True}
        captured["channel"] = channel

    monkeypatch.setattr(validation, "validate_profile_policies_or_raise_for_channel", _fake_validate)

    validation.validate_profile_payload_with_schema({"policies": {"DisableTelemetry": True}})

    assert captured["channel"] == "release-152"


def test_validate_profile_payload_with_schema_rejects_non_mapping_policies():
    with pytest.raises(validation.PolicyValidationError) as excinfo:
        validation.validate_profile_payload_with_schema({"channel": "esr-140.12", "policies": [1]})

    assert excinfo.value.issues == [
        validation.PolicyValidationIssue(
            policy=None,
            path=["policies"],
            message="Expected object with policy mappings",
        )
    ]


def test_validate_profile_payload_with_schema_passes_explicit_channel_to_validator(monkeypatch):
    captured = {}

    def _fake_validate(policies, channel: str):
        assert policies == {}
        captured["channel"] = channel

    monkeypatch.setattr(validation, "validate_profile_policies_or_raise_for_channel", _fake_validate)

    validation.validate_profile_payload_with_schema({"channel": "esr-140.12", "policies": {}})

    assert captured["channel"] == "esr-140.12"


def test_normalize_policy_document_schema_leaves_non_object_schema_unchanged():
    schema = {"type": "string"}

    assert validation._normalize_policy_document_schema(schema) is schema


@pytest.mark.parametrize(
    "properties",
    [None, [], {}],
)
def test_normalize_policy_document_schema_leaves_objects_without_properties_unchanged(properties):
    schema = {"type": "object"}
    if properties is not None:
        schema["properties"] = properties

    assert validation._normalize_policy_document_schema(schema) is schema


def test_normalize_policy_document_schema_keeps_already_strict_object_schema():
    schema = {
        "type": "object",
        "properties": {"DisableTelemetry": {"type": "boolean"}},
        "additionalProperties": False,
    }

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
