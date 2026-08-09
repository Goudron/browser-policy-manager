from __future__ import annotations

import json

import pytest

from app.core import schemas_loader as loader

pytestmark = pytest.mark.usefixtures("reset_app_caches")


def test_minimal_schema_contains_expected_defaults():
    schema = loader._minimal_schema("Firefox ESR 140.13 Policies (stub)")

    assert schema["title"] == "Firefox ESR 140.13 Policies (stub)"
    assert schema["type"] == "object"
    assert schema["properties"]["DisableTelemetry"]["type"] == "boolean"
    assert schema["properties"]["DisablePrivateBrowsing"]["type"] == "boolean"


@pytest.mark.parametrize(
    ("profile", "expected_title"),
    [
        ("esr-140.13", "Firefox ESR 140.13 Policies (stub)"),
        ("release-153", "Firefox Release 153 Policies (stub)"),
    ],
)
def test_load_schema_returns_in_memory_stub_only_when_explicitly_allowed(
    tmp_path,
    monkeypatch,
    profile,
    expected_title,
):
    policies_dir = tmp_path / "policies"

    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    schema = loader.load_schema(profile, allow_stub_fallback=True)

    assert schema["title"] == expected_title
    assert not policies_dir.exists()


def test_load_schema_raises_when_every_source_is_missing_and_stub_fallback_is_disabled(
    tmp_path,
    monkeypatch,
):
    policies_dir = tmp_path / "policies"

    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    with pytest.raises(loader.SchemaNotFoundError, match="Bundled schema file not found"):
        loader.load_schema("release-153")


@pytest.mark.parametrize("profile", ("release-152", "esr-140.12"))
def test_load_schema_rejects_retired_channel(profile):
    with pytest.raises(loader.UnsupportedProfileError, match="Unsupported profile"):
        loader.load_schema(profile)


def test_normalize_schema_moves_array_enum_to_items():
    payload = {
        "type": "object",
        "properties": {
            "HttpAllowlist": {
                "type": "array",
                "items": {"type": "string"},
                "enum": ["http://example.org"],
            }
        },
    }

    normalized = loader._normalize_schema(payload)

    assert "enum" not in normalized["properties"]["HttpAllowlist"]
    assert normalized["properties"]["HttpAllowlist"]["items"]["enum"] == ["http://example.org"]


def test_normalize_schema_keeps_array_enum_when_items_already_define_enum():
    payload = {
        "type": "object",
        "properties": {
            "HttpAllowlist": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["http://example.org"],
                },
                "enum": ["legacy"],
            }
        },
    }

    normalized = loader._normalize_schema(payload)

    assert normalized["properties"]["HttpAllowlist"]["enum"] == ["legacy"]
    assert normalized["properties"]["HttpAllowlist"]["items"]["enum"] == ["http://example.org"]


def test_load_schema_reads_declared_bundled_json_schema(tmp_path, monkeypatch):
    policies_dir = tmp_path / "policies"
    bundled_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Release 153 Policies",
        "type": "object",
        "additionalProperties": False,
        "x-bpm-channel": "release-153",
        "x-bpm-version": "149.0",
        "x-bpm-source": "fixture",
        "properties": {
            "HttpAllowlist": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["http://example.org"],
                },
            },
            "Extensions": {
                "type": "object",
                "properties": {
                    "Install": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["https://example.org/addon.xpi"],
                        },
                    }
                },
                "additionalProperties": False,
                "required": ["Install"],
            },
        },
    }

    policies_dir.mkdir()
    (policies_dir / "firefox-release-153.json").write_text(
        json.dumps(bundled_schema), encoding="utf-8"
    )

    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    schema = loader.load_schema("release-153")

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["HttpAllowlist"]["items"]["enum"] == ["http://example.org"]
    assert schema["properties"]["Extensions"]["required"] == ["Install"]
