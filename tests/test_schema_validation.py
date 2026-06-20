# tests/test_schema_validation.py
"""
Basic tests for schema loading and policy validation.

The tests assert:
- Schemas for supported channels are loadable.
- Validator is constructible for each supported profile.
- Passing a clearly wrong type (e.g., integer) fails validation.
- Bundled schema snapshots expose the expected Mozilla metadata for v7.12.
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from app.core.schema_channels import (
    CURRENT_ESR_SCHEMA_CHANNEL,
    CURRENT_RELEASE_SCHEMA_CHANNEL,
    SCHEMA_FILENAMES,
    SCHEMA_MOZILLA_VERSIONS,
    SUPPORTED_SCHEMA_CHANNELS,
)
from app.core.schemas_loader import available_profiles, load_schema
from app.core.validation import PolicySchemaValidator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "app" / "schemas" / "policies"


def test_available_profiles_scope():
    profiles = available_profiles()
    assert set(profiles.keys()) == set(SUPPORTED_SCHEMA_CHANNELS)
    for channel, filename in SCHEMA_FILENAMES.items():
        assert profiles[channel].endswith(filename)


@pytest.mark.parametrize("profile", SUPPORTED_SCHEMA_CHANNELS)
def test_load_schema_ok(profile):
    schema = load_schema(profile)
    assert isinstance(schema, dict)
    # Minimal sanity: schema should declare an object at top-level or have properties/anyOf/etc.
    assert isinstance(schema, dict) and len(schema) > 0


@pytest.mark.parametrize("profile", SUPPORTED_SCHEMA_CHANNELS)
def test_validator_rejects_wrong_type(profile):
    validator = PolicySchemaValidator(profile)
    with pytest.raises(ValidationError):
        # Most Firefox policy schemas expect an object; int should be invalid
        validator.validate(123)


@pytest.mark.parametrize(
    ("profile", "expected_version"),
    [(channel, SCHEMA_MOZILLA_VERSIONS[channel]) for channel in SUPPORTED_SCHEMA_CHANNELS],
)
def test_bundled_schema_metadata_matches_mozilla_v712(profile, expected_version):
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES[profile]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["x-bpm-channel"] == profile
    assert schema["x-bpm-version"] == expected_version
    assert schema["x-bpm-source"] == "mozilla-policy-templates-v7.12"
    assert (
        schema["properties"]["ExtensionSettings"]["additionalProperties"]["properties"][
            "allowed_types"
        ]["items"]["enum"]
        == ["extension", "theme", "dictionary", "locale", "sitepermission"]
    )


def test_release_152_keeps_upstream_min_version_metadata():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES[CURRENT_RELEASE_SCHEMA_CHANNEL]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["properties"]["DisableRemoteImprovements"]["x-bpm-min-version"] == "148.0"


def test_release_152_includes_new_policy_templates_entries():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES[CURRENT_RELEASE_SCHEMA_CHANNEL]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "AIControls" in schema["properties"]
    assert "IPProtectionAvailable" in schema["properties"]
    assert "LocalNetworkAccess" in schema["properties"]
    assert "XSLTEnabled" in schema["properties"]
    assert schema["properties"]["DefaultSerialGuardSetting"]["enum"] == [2, 3]
    assert schema["properties"]["FirefoxHome"]["properties"]["Weather"]["type"] == "boolean"
    assert (
        schema["properties"]["ExtensionSettings"]["additionalProperties"]["properties"][
            "update_url"
        ]["type"]
        == "string"
    )


def test_esr_140_12_includes_shared_new_entries_but_not_release_only_entries():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES[CURRENT_ESR_SCHEMA_CHANNEL]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "AIControls" not in schema["properties"]
    assert "IPProtectionAvailable" not in schema["properties"]
    assert "LocalNetworkAccess" not in schema["properties"]
    assert "XSLTEnabled" not in schema["properties"]
    assert schema["properties"]["DefaultSerialGuardSetting"]["enum"] == [2, 3]
    assert schema["properties"]["FirefoxHome"]["properties"]["Weather"]["type"] == "boolean"
