import pytest

from app.core.policy_validation import (
    PolicyValidationError,
    load_policy_schema_for_channel,
    validate_profile_payload_with_schema,
    validate_profile_policies_or_raise,
)


def test_valid_profile_with_arrays_and_enums_release():
    """Happy-path: correct types and enum values must pass for release channel."""
    schema = load_policy_schema_for_channel("release-145")

    policies = {
        # array + enum + items_type from upstream example
        "HttpAllowlist": ["http://example.org"],
        # simple boolean
        "DisableAppUpdate": True,
        # object policy with nested array properties and enums/items_type
        "Extensions": {
            "Install": [
                "https://addons.mozilla.org/firefox/downloads/somefile.xpi",
            ],
            "Uninstall": ["bad_addon_id@mozilla.org"],
            "Locked": ["addon_id@mozilla.org"],
        },
    }

    # Should not raise
    validate_profile_policies_or_raise(policies, schema)


def test_invalid_enum_value_in_array_raises():
    """Array element not present in enum must be rejected."""
    schema = load_policy_schema_for_channel("release-145")

    policies = {
        "HttpAllowlist": ["http://evil.example"],
    }

    with pytest.raises(PolicyValidationError) as excinfo:
        validate_profile_policies_or_raise(policies, schema)

    issues = excinfo.value.issues
    assert issues
    assert any(issue.policy == "HttpAllowlist" for issue in issues)
    assert any("not allowed" in issue.message for issue in issues)


def test_invalid_item_type_in_array_raises():
    """Array item type must match items_type from schema."""
    schema = load_policy_schema_for_channel("release-145")

    # HttpAllowlist expects array of strings
    policies = {
        "HttpAllowlist": [42],
    }

    with pytest.raises(PolicyValidationError) as excinfo:
        validate_profile_policies_or_raise(policies, schema)

    issues = excinfo.value.issues
    assert issues
    assert any("Expected item type 'string'" in issue.message for issue in issues)


def test_unknown_policy_is_reported():
    """Unknown policy ids should be reported as a validation issue."""
    schema = load_policy_schema_for_channel("release-145")

    policies = {
        "NoSuchPolicy": True,
    }

    with pytest.raises(PolicyValidationError) as excinfo:
        validate_profile_policies_or_raise(policies, schema)

    issues = excinfo.value.issues
    assert any("Unknown policy 'NoSuchPolicy'" in issue.message for issue in issues)


def test_object_policy_unknown_property_rejected_when_additional_false():
    """
    Object policy with additional_properties=False must reject unknown fields.

    For example, Extensions in our schemas only allows a limited set of
    properties (Install / Uninstall / Locked).
    """
    schema = load_policy_schema_for_channel("release-145")

    policies = {
        "Extensions": {
            "Foo": [],
        }
    }

    with pytest.raises(PolicyValidationError) as excinfo:
        validate_profile_policies_or_raise(policies, schema)

    issues = excinfo.value.issues
    assert any("Unknown property 'Foo'" in issue.message for issue in issues)


def test_validate_profile_payload_helper_uses_channel_and_policies():
    """High-level helper must pick schema by channel and validate policies."""
    payload = {
        "channel": "release-145",
        "name": "Test profile",
        "policies": {
            "DisableAppUpdate": True,
            "HttpAllowlist": ["http://example.org"],
        },
    }

    # Should not raise for valid payload
    validate_profile_payload_with_schema(payload)


def test_validate_profile_payload_helper_invalid_policies():
    """High-level helper must surface PolicyValidationError on invalid content."""
    payload = {
        "channel": "release-145",
        "name": "Test profile",
        "policies": {
            "HttpAllowlist": ["http://evil.example"],
        },
    }

    with pytest.raises(PolicyValidationError):
        validate_profile_payload_with_schema(payload)
