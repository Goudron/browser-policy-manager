import pytest

from app.core.schemas_loader import UnsupportedProfileError, available_profiles, load_schema


def test_load_schema_success_and_cache():
    """Covers normal and cached load of known schemas in schemas_loader."""
    profiles = available_profiles()
    assert "esr-140" in profiles and "release-144" in profiles

    for key in profiles:
        schema = load_schema(key)
        assert isinstance(schema, dict)
        assert "policies" in schema or "title" in schema

    # Call again to hit the lru_cache branch (should not raise)
    cached = load_schema("esr-140")
    assert isinstance(cached, dict)


def test_load_schema_unsupported_profile():
    """Covers UnsupportedProfileError branch."""
    with pytest.raises(UnsupportedProfileError):
        load_schema("unknown-profile")
