# tests/test_schema_validation.py
"""
Basic tests for schema loading and policy validation.

The tests assert:
- Schemas for "esr-140" and "release-144" are loadable.
- Validator is constructible for each supported profile.
- Passing a clearly wrong type (e.g., integer) fails validation.
"""

import pytest
from jsonschema import ValidationError

from app.core.schemas_loader import available_profiles, load_schema
from app.core.validation import PolicySchemaValidator


def test_available_profiles_scope():
    profiles = available_profiles()
    assert set(profiles.keys()) == {"esr-140", "release-144"}
    assert profiles["esr-140"].endswith("firefox-esr140.json")
    assert profiles["release-144"].endswith("firefox-release.json")


@pytest.mark.parametrize("profile", ["esr-140", "release-144"])
def test_load_schema_ok(profile):
    schema = load_schema(profile)
    assert isinstance(schema, dict)
    # Minimal sanity: schema should declare an object at top-level or have properties/anyOf/etc.
    assert isinstance(schema, dict) and len(schema) > 0


@pytest.mark.parametrize("profile", ["esr-140", "release-144"])
def test_validator_rejects_wrong_type(profile):
    validator = PolicySchemaValidator(profile)
    with pytest.raises(ValidationError):
        # Most Firefox policy schemas expect an object; int should be invalid
        validator.validate(123)
