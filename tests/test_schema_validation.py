# tests/test_schema_validation.py
"""
Basic tests for schema loading and policy validation.

The tests assert:
- Schemas for "esr-140.11" and "release-151" are loadable.
- Validator is constructible for each supported profile.
- Passing a clearly wrong type (e.g., integer) fails validation.
- Bundled schema snapshots expose the expected Mozilla metadata for v7.11.
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from app.core.schema_channels import SCHEMA_FILENAMES
from app.core.schemas_loader import available_profiles, load_schema
from app.core.validation import PolicySchemaValidator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "app" / "schemas" / "policies"


def test_available_profiles_scope():
    profiles = available_profiles()
    assert set(profiles.keys()) == {"esr-140.11", "release-151"}
    assert profiles["esr-140.11"].endswith("firefox-esr-140.11.json")
    assert profiles["release-151"].endswith("firefox-release-151.json")


@pytest.mark.parametrize("profile", ["esr-140.11", "release-151"])
def test_load_schema_ok(profile):
    schema = load_schema(profile)
    assert isinstance(schema, dict)
    # Minimal sanity: schema should declare an object at top-level or have properties/anyOf/etc.
    assert isinstance(schema, dict) and len(schema) > 0


@pytest.mark.parametrize("profile", ["esr-140.11", "release-151"])
def test_validator_rejects_wrong_type(profile):
    validator = PolicySchemaValidator(profile)
    with pytest.raises(ValidationError):
        # Most Firefox policy schemas expect an object; int should be invalid
        validator.validate(123)


@pytest.mark.parametrize(
    ("profile", "expected_version"),
    [
        ("esr-140.11", "140.11"),
        ("release-151", "151.0"),
    ],
)
def test_bundled_schema_metadata_matches_mozilla_v711(profile, expected_version):
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES[profile]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["x-bpm-channel"] == profile
    assert schema["x-bpm-version"] == expected_version
    assert schema["x-bpm-source"] == "mozilla-policy-templates-v7.11"
    assert (
        schema["properties"]["ExtensionSettings"]["additionalProperties"]["properties"][
            "allowed_types"
        ]["items"]["enum"]
        == ["extension", "theme", "dictionary", "locale", "sitepermission"]
    )


def test_release_151_keeps_upstream_min_version_metadata():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES["release-151"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["properties"]["DisableRemoteImprovements"]["x-bpm-min-version"] == "148.0"


def test_release_151_includes_new_policy_templates_entries():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES["release-151"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "AIControls" in schema["properties"]
    assert "IPProtectionAvailable" in schema["properties"]
    assert "LocalNetworkAccess" in schema["properties"]
    assert "XSLTEnabled" in schema["properties"]
    assert (
        schema["properties"]["ExtensionSettings"]["additionalProperties"]["properties"][
            "update_url"
        ]["type"]
        == "string"
    )


def test_esr_140_11_does_not_include_release_only_new_entries():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES["esr-140.11"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "AIControls" not in schema["properties"]
    assert "IPProtectionAvailable" not in schema["properties"]
    assert "LocalNetworkAccess" not in schema["properties"]
    assert "XSLTEnabled" not in schema["properties"]
