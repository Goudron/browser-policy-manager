# tests/test_schema_validation.py
"""
Basic tests for schema loading and policy validation.

The tests assert:
- Schemas for "esr-140.10" and "release-150" are loadable.
- Validator is constructible for each supported profile.
- Passing a clearly wrong type (e.g., integer) fails validation.
- Bundled schema snapshots expose the expected Mozilla metadata for v7.10.
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
    assert set(profiles.keys()) == {"esr-140.10", "release-150"}
    assert profiles["esr-140.10"].endswith("firefox-esr-140.10.json")
    assert profiles["release-150"].endswith("firefox-release-150.json")


@pytest.mark.parametrize("profile", ["esr-140.10", "release-150"])
def test_load_schema_ok(profile):
    schema = load_schema(profile)
    assert isinstance(schema, dict)
    # Minimal sanity: schema should declare an object at top-level or have properties/anyOf/etc.
    assert isinstance(schema, dict) and len(schema) > 0


@pytest.mark.parametrize("profile", ["esr-140.10", "release-150"])
def test_validator_rejects_wrong_type(profile):
    validator = PolicySchemaValidator(profile)
    with pytest.raises(ValidationError):
        # Most Firefox policy schemas expect an object; int should be invalid
        validator.validate(123)


@pytest.mark.parametrize(
    ("profile", "expected_version"),
    [
        ("esr-140.10", "140.10"),
        ("release-150", "150.0"),
    ],
)
def test_bundled_schema_metadata_matches_mozilla_v710(profile, expected_version):
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES[profile]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["x-bpm-channel"] == profile
    assert schema["x-bpm-version"] == expected_version
    assert schema["x-bpm-source"] == "mozilla-policy-templates-v7.10"
    assert (
        schema["properties"]["ExtensionSettings"]["additionalProperties"]["properties"][
            "allowed_types"
        ]["items"]["enum"]
        == ["extension", "theme", "dictionary", "locale", "sitepermission"]
    )


def test_release_150_keeps_upstream_min_version_metadata():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES["release-150"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["properties"]["DisableRemoteImprovements"]["x-bpm-min-version"] == "148.0"


def test_release_150_includes_new_policy_templates_entries():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES["release-150"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "AIControls" in schema["properties"]
    assert "IPProtectionAvailable" in schema["properties"]


def test_esr_140_10_does_not_include_release_only_new_entries():
    schema_path = SCHEMAS_DIR / SCHEMA_FILENAMES["esr-140.10"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "AIControls" not in schema["properties"]
    assert "IPProtectionAvailable" not in schema["properties"]
