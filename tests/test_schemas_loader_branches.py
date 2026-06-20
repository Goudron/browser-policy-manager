from __future__ import annotations

import json

import pytest

from app.core import schemas_loader as loader

pytestmark = pytest.mark.usefixtures("reset_app_caches")


def test_json_helpers_round_trip(tmp_path):
    path = tmp_path / "nested" / "schema.json"
    payload = {"title": "Round trip", "properties": {"DisableTelemetry": {"type": "boolean"}}}

    loader._write_json_file(path, payload)

    assert loader._read_json_file(path) == payload


def test_minimal_schema_contains_expected_defaults():
    schema = loader._minimal_schema("Firefox ESR 140.12 Policies (stub)")

    assert schema["title"] == "Firefox ESR 140.12 Policies (stub)"
    assert schema["type"] == "object"
    assert schema["properties"]["DisableTelemetry"]["type"] == "boolean"
    assert schema["properties"]["DisablePrivateBrowsing"]["type"] == "boolean"


def test_load_schema_prefers_static_file_over_cache(tmp_path, monkeypatch):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    mozilla_dir = tmp_path / "mozilla"
    policies_dir = tmp_path / "policies"
    filename = loader.available_profiles()["esr-140.12"]
    static_payload = {"title": "static", "source": "static"}
    cache_payload = {"title": "cache", "source": "cache"}

    loader._write_json_file(static_dir / filename, static_payload)
    loader._write_json_file(cache_dir / filename, cache_payload)

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(loader, "_MOZILLA_DIR", mozilla_dir)
    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    assert loader.load_schema("esr-140.12") == static_payload


def test_load_schema_prefers_raw_mozilla_schema_over_legacy_cache(tmp_path, monkeypatch):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    mozilla_dir = tmp_path / "mozilla"
    policies_dir = tmp_path / "policies"
    cache_filename = loader.available_profiles()["release-152"]
    mozilla_payload = {"title": "raw", "source": "mozilla"}
    cache_payload = {"title": "cache", "source": "cache"}

    loader._write_json_file(cache_dir / cache_filename, cache_payload)
    loader._write_json_file(mozilla_dir / "release152" / "policies-schema.json", mozilla_payload)

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(loader, "_MOZILLA_DIR", mozilla_dir)
    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    assert loader.load_schema("release-152") == mozilla_payload


def test_load_schema_uses_cache_when_static_missing(tmp_path, monkeypatch):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    mozilla_dir = tmp_path / "mozilla"
    policies_dir = tmp_path / "policies"
    filename = loader.available_profiles()["release-152"]
    cache_payload = {"title": "cache-only", "source": "cache"}

    loader._write_json_file(cache_dir / filename, cache_payload)

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(loader, "_MOZILLA_DIR", mozilla_dir)
    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    assert loader.load_schema("release-152") == cache_payload


@pytest.mark.parametrize(
    ("profile", "expected_title"),
    [
        ("esr-140.12", "Firefox ESR 140.12 Policies (stub)"),
        ("release-152", "Firefox Release 152 Policies (stub)"),
    ],
)
def test_load_schema_generates_and_persists_stub_when_missing_when_explicitly_allowed(
    tmp_path,
    monkeypatch,
    profile,
    expected_title,
):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    mozilla_dir = tmp_path / "mozilla"
    policies_dir = tmp_path / "policies"
    filename = loader.available_profiles()[profile]

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(loader, "_MOZILLA_DIR", mozilla_dir)
    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    schema = loader.load_schema(profile, allow_stub_fallback=True)
    cached_path = cache_dir / filename

    assert schema["title"] == expected_title
    assert cached_path.exists()
    assert json.loads(cached_path.read_text(encoding="utf-8")) == schema


def test_load_schema_raises_when_every_source_is_missing_and_stub_fallback_is_disabled(
    tmp_path,
    monkeypatch,
):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    mozilla_dir = tmp_path / "mozilla"
    policies_dir = tmp_path / "policies"

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(loader, "_MOZILLA_DIR", mozilla_dir)
    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    with pytest.raises(loader.SchemaNotFoundError, match="Schema file not found"):
        loader.load_schema("release-152")


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


def test_load_schema_reads_bundled_raw_json_schema(tmp_path, monkeypatch):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    mozilla_dir = tmp_path / "mozilla"
    policies_dir = tmp_path / "policies"
    bundled_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Release 152 Policies",
        "type": "object",
        "additionalProperties": False,
        "x-bpm-channel": "release-152",
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

    loader._write_json_file(
        policies_dir / "firefox-release-152.json",
        bundled_schema,
    )

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(loader, "_MOZILLA_DIR", mozilla_dir)
    monkeypatch.setattr(loader, "_POLICIES_DIR", policies_dir)

    schema = loader.load_schema("release-152")

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["HttpAllowlist"]["items"]["enum"] == ["http://example.org"]
    assert schema["properties"]["Extensions"]["required"] == ["Install"]
