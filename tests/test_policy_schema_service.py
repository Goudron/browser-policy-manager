from __future__ import annotations

import json

import pytest

from app.services import policy_schema_service as service


def _write_schema(path, *, channel: str = "release-145") -> None:
    payload = {
        "channel": channel,
        "version": "145.0",
        "source": "test-fixture",
        "policies": {
            "DisableTelemetry": {
                "id": "DisableTelemetry",
                "type": "boolean",
                "description_key": "policy.DisableTelemetry",
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_get_schema_path_unknown_channel_raises():
    with pytest.raises(service.UnknownPolicyChannelError):
        service._get_schema_path("beta-999")


def test_get_schema_path_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "SCHEMAS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        service._get_schema_path("release-145")


def test_load_policy_schema_and_get_definition(tmp_path, monkeypatch):
    release_file = tmp_path / "firefox-release-145.json"
    _write_schema(release_file)

    monkeypatch.setattr(service, "SCHEMAS_DIR", tmp_path)
    service.load_policy_schema.cache_clear()

    schema = service.load_policy_schema("release-145")
    definition = service.get_policy_definition("release-145", "DisableTelemetry")
    missing = service.get_policy_definition("release-145", "NoSuchPolicy")

    assert schema.channel == "release-145"
    assert definition is not None
    assert definition.id == "DisableTelemetry"
    assert missing is None

    # Cached result should survive file changes until cache_clear() is called.
    release_file.write_text(
        json.dumps(
            {
                "channel": "release-145",
                "version": "145.1",
                "source": "updated-fixture",
                "policies": {},
            }
        ),
        encoding="utf-8",
    )
    cached = service.load_policy_schema("release-145")
    assert cached.version == "145.0"

    service.load_policy_schema.cache_clear()
