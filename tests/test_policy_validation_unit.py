from __future__ import annotations

import json

import pytest

from app.core import policy_validation as validation


def test_policy_validation_error_stores_issues():
    issues = [
        validation.PolicyValidationIssue(
            policy="DisableTelemetry",
            path=["policies", "DisableTelemetry"],
            message="Bad value",
        )
    ]

    error = validation.PolicyValidationError(issues)

    assert str(error) == "Policy validation failed"
    assert error.issues == issues


def test_project_root_and_schemas_dir_are_resolved():
    root = validation._project_root()
    schemas_dir = validation._schemas_dir()

    assert root.name == "app"
    assert schemas_dir == root / "schemas" / "policies"


def test_load_policy_schema_for_channel_reads_files_from_schemas_dir(tmp_path, monkeypatch):
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    esr = {"policies": {"DisableTelemetry": {"type": "boolean"}}}
    release = {"policies": {"DisablePrivateBrowsing": {"type": "boolean"}}}
    (schemas_dir / "firefox-esr-140.json").write_text(json.dumps(esr), encoding="utf-8")
    (schemas_dir / "firefox-release-145.json").write_text(json.dumps(release), encoding="utf-8")
    validation.load_policy_schema_for_channel.cache_clear()
    monkeypatch.setattr(validation, "_schemas_dir", lambda: schemas_dir)

    assert validation.load_policy_schema_for_channel("esr-140") == esr
    assert validation.load_policy_schema_for_channel("release-145") == release


def test_load_policy_schema_for_channel_rejects_unknown_channel():
    validation.load_policy_schema_for_channel.cache_clear()

    with pytest.raises(ValueError, match="Unsupported channel"):
        validation.load_policy_schema_for_channel("beta-999")


def test_load_policy_schema_for_channel_raises_when_file_missing(tmp_path, monkeypatch):
    validation.load_policy_schema_for_channel.cache_clear()
    monkeypatch.setattr(validation, "_schemas_dir", lambda: tmp_path)

    with pytest.raises(FileNotFoundError, match="Internal policy schema not found"):
        validation.load_policy_schema_for_channel("esr-140")


@pytest.mark.parametrize(
    ("value", "expected", "matches"),
    [
        (True, "boolean", True),
        ("yes", "string", True),
        (7, "integer", True),
        (True, "integer", False),
        (1.5, "number", True),
        (True, "number", False),
        (["a"], "array", True),
        ({"a": 1}, "object", True),
        ("anything", "mystery", True),
    ],
)
def test_python_type_matches(value, expected, matches):
    assert validation._python_type_matches(value, expected) is matches


def test_validate_scalar_or_array_reports_type_mismatch():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_scalar_or_array(
        value="wrong",
        node_schema={"type": "boolean"},
        policy_id="DisableTelemetry",
        path=["policies", "DisableTelemetry"],
        issues=issues,
    )

    assert len(issues) == 1
    assert issues[0].message == "Expected type 'boolean', got 'str'"


def test_validate_scalar_or_array_reports_array_enum_and_item_type_issues():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_scalar_or_array(
        value=["bad", 2],
        node_schema={"type": "array", "enum": ["ok"], "items_type": "string"},
        policy_id="AllowedHosts",
        path=["policies", "AllowedHosts"],
        issues=issues,
    )

    assert len(issues) == 3
    assert issues[0].path == ["policies", "AllowedHosts", 0]
    assert "expected one of ['ok']" in issues[0].message
    assert issues[-1].path == ["policies", "AllowedHosts", 1]
    assert issues[-1].message == "Expected item type 'string', got 'int'"


def test_validate_scalar_or_array_reports_scalar_enum_issue():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_scalar_or_array(
        value="bad",
        node_schema={"type": "string", "enum": ["good"]},
        policy_id="HomepageLocation",
        path=["policies", "HomepageLocation"],
        issues=issues,
    )

    assert len(issues) == 1
    assert issues[0].message == "Value 'bad' is not allowed; expected one of ['good']"


def test_validate_scalar_or_array_array_branch_noops_when_type_checker_allows_non_list(monkeypatch):
    issues: list[validation.PolicyValidationIssue] = []
    monkeypatch.setattr(validation, "_python_type_matches", lambda value, expected: True)

    validation._validate_scalar_or_array(
        value="still-not-a-list",
        node_schema={"type": "array"},
        policy_id="AllowedHosts",
        path=["policies", "AllowedHosts"],
        issues=issues,
    )

    assert issues == []


def test_validate_object_policy_requires_dict():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_object_policy(
        value="nope",
        policy_schema={"type": "object"},
        policy_id="Preferences",
        path=["policies", "Preferences"],
        issues=issues,
    )

    assert len(issues) == 1
    assert issues[0].message == "Expected object for policy 'Preferences', got 'str'"


def test_validate_object_policy_reports_unknown_properties_and_nested_issues():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_object_policy(
        value={"known": "bad", "extra": True},
        policy_schema={
            "type": "object",
            "additional_properties": False,
            "properties": {"known": {"type": "boolean"}},
        },
        policy_id="Preferences",
        path=["policies", "Preferences"],
        issues=issues,
    )

    assert len(issues) == 2
    assert issues[0].path == ["policies", "Preferences", "extra"]
    assert issues[0].message == "Unknown property 'extra' for policy 'Preferences'"
    assert issues[1].path == ["policies", "Preferences", "known"]
    assert issues[1].message == "Expected type 'boolean', got 'str'"


def test_validate_object_policy_ignores_missing_known_properties():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_object_policy(
        value={},
        policy_schema={
            "type": "object",
            "additional_properties": False,
            "properties": {"known": {"type": "boolean"}},
        },
        policy_id="Preferences",
        path=["policies", "Preferences"],
        issues=issues,
    )

    assert issues == []


def test_validate_object_policy_allows_unknown_properties_when_additional_enabled():
    issues: list[validation.PolicyValidationIssue] = []

    validation._validate_object_policy(
        value={"extra": True},
        policy_schema={"type": "object", "additional_properties": True, "properties": {}},
        policy_id="Preferences",
        path=["policies", "Preferences"],
        issues=issues,
    )

    assert issues == []


def test_validate_profile_policies_collects_unknown_and_known_policy_issues():
    schema = {
        "policies": {
            "DisableTelemetry": {"type": "boolean"},
            "AllowedHosts": {"type": "array", "items_type": "string"},
            "Preferences": {
                "type": "object",
                "additional_properties": False,
                "properties": {"Enabled": {"type": "boolean"}},
            },
        }
    }

    issues = validation.validate_profile_policies(
        {
            "UnknownOne": True,
            "DisableTelemetry": "bad",
            "AllowedHosts": ["ok", 5],
            "Preferences": {"Enabled": "no", "Extra": 1},
        },
        schema,
    )

    assert [issue.policy for issue in issues] == [
        "UnknownOne",
        "DisableTelemetry",
        "AllowedHosts",
        "Preferences",
        "Preferences",
    ]


def test_validate_profile_policies_or_raise_raises_for_invalid_payload():
    with pytest.raises(validation.PolicyValidationError) as excinfo:
        validation.validate_profile_policies_or_raise(
            {"DisableTelemetry": "bad"},
            {"policies": {"DisableTelemetry": {"type": "boolean"}}},
        )

    assert excinfo.value.issues[0].policy == "DisableTelemetry"


def test_validate_profile_payload_with_schema_defaults_channel_and_validates(monkeypatch):
    captured = {}

    def _fake_load(channel: str):
        captured["channel"] = channel
        return {"policies": {"DisableTelemetry": {"type": "boolean"}}}

    monkeypatch.setattr(validation, "load_policy_schema_for_channel", _fake_load)

    validation.validate_profile_payload_with_schema({"policies": {"DisableTelemetry": True}})

    assert captured["channel"] == "release-145"


def test_validate_profile_payload_with_schema_rejects_non_mapping_policies(monkeypatch):
    monkeypatch.setattr(validation, "load_policy_schema_for_channel", lambda channel: {"policies": {}})

    with pytest.raises(validation.PolicyValidationError) as excinfo:
        validation.validate_profile_payload_with_schema({"channel": "esr-140", "policies": [1]})

    assert excinfo.value.issues[0].path == ["policies"]
    assert excinfo.value.issues[0].message == "Expected object with policy mappings"


def test_validate_profile_payload_with_schema_passes_explicit_channel_to_loader(monkeypatch):
    captured = {}

    def _fake_load(channel: str):
        captured["channel"] = channel
        return {"policies": {}}

    monkeypatch.setattr(validation, "load_policy_schema_for_channel", _fake_load)

    validation.validate_profile_payload_with_schema({"channel": "esr-140", "policies": {}})

    assert captured["channel"] == "esr-140"
