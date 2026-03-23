from __future__ import annotations

import json

import pytest

from app.core import schemas_loader as loader


@pytest.fixture(autouse=True)
def clear_schema_loader_cache():
    loader.load_schema.cache_clear()
    yield
    loader.load_schema.cache_clear()


def test_json_helpers_round_trip(tmp_path):
    path = tmp_path / "nested" / "schema.json"
    payload = {"title": "Round trip", "properties": {"DisableTelemetry": {"type": "boolean"}}}

    loader._write_json_file(path, payload)

    assert loader._read_json_file(path) == payload


def test_minimal_schema_contains_expected_defaults():
    schema = loader._minimal_schema("Firefox ESR 140 Policies (stub)")

    assert schema["title"] == "Firefox ESR 140 Policies (stub)"
    assert schema["type"] == "object"
    assert schema["properties"]["DisableTelemetry"]["type"] == "boolean"
    assert schema["properties"]["DisablePrivateBrowsing"]["type"] == "boolean"


def test_load_schema_prefers_static_file_over_cache(tmp_path, monkeypatch):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    filename = loader.available_profiles()["esr-140"]
    static_payload = {"title": "static", "source": "static"}
    cache_payload = {"title": "cache", "source": "cache"}

    loader._write_json_file(static_dir / filename, static_payload)
    loader._write_json_file(cache_dir / filename, cache_payload)

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)

    assert loader.load_schema("esr-140") == static_payload


def test_load_schema_uses_cache_when_static_missing(tmp_path, monkeypatch):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    filename = loader.available_profiles()["release-145"]
    cache_payload = {"title": "cache-only", "source": "cache"}

    loader._write_json_file(cache_dir / filename, cache_payload)

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)

    assert loader.load_schema("release-145") == cache_payload


@pytest.mark.parametrize(
    ("profile", "expected_title"),
    [
        ("esr-140", "Firefox ESR 140 Policies (stub)"),
        ("release-145", "Firefox Release 145 Policies (stub)"),
    ],
)
def test_load_schema_generates_and_persists_stub_when_missing(
    tmp_path,
    monkeypatch,
    profile,
    expected_title,
):
    static_dir = tmp_path / "static"
    cache_dir = tmp_path / "cache"
    filename = loader.available_profiles()[profile]

    monkeypatch.setattr(loader, "_STATIC_DIR", static_dir)
    monkeypatch.setattr(loader, "_CACHE_DIR", cache_dir)

    schema = loader.load_schema(profile)
    cached_path = cache_dir / filename

    assert schema["title"] == expected_title
    assert cached_path.exists()
    assert json.loads(cached_path.read_text(encoding="utf-8")) == schema
