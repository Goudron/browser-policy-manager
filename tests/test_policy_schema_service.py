from __future__ import annotations

import json

import pytest

from app.services import policy_schema_service as service


def _write_schema(path, *, channel: str = "release-149") -> None:
    payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Release Policies 149.0",
        "type": "object",
        "additionalProperties": False,
        "x-bpm-channel": channel,
        "x-bpm-version": "149.0",
        "x-bpm-source": "test-fixture",
        "properties": {
            "DisableTelemetry": {
                "type": "boolean",
                "x-bpm-id": "DisableTelemetry",
                "x-bpm-description-key": "policy.DisableTelemetry",
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_custom_schema(path, properties: dict[str, object], *, channel: str = "release-149") -> None:
    payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Release Policies 149.0",
        "type": "object",
        "additionalProperties": False,
        "x-bpm-channel": channel,
        "x-bpm-version": "149.0",
        "x-bpm-source": "test-fixture",
        "properties": properties,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_get_schema_path_unknown_channel_raises():
    with pytest.raises(service.UnknownPolicyChannelError):
        service._get_schema_path("beta-999")


def test_get_schema_path_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "SCHEMAS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        service._get_schema_path("release-149")


def test_load_policy_schema_and_get_definition(tmp_path, monkeypatch):
    release_file = tmp_path / "firefox-release-149.json"
    _write_schema(release_file)

    monkeypatch.setattr(service, "SCHEMAS_DIR", tmp_path)
    service.load_policy_schema.cache_clear()

    schema = service.load_policy_schema("release-149")
    definition = service.get_policy_definition("release-149", "DisableTelemetry")
    missing = service.get_policy_definition("release-149", "NoSuchPolicy")

    assert schema.channel == "release-149"
    assert definition is not None
    assert definition.id == "DisableTelemetry"
    assert missing is None

    # Cached result should survive file changes until cache_clear() is called.
    release_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "Release Policies 148.1",
                "type": "object",
                "additionalProperties": False,
                "x-bpm-channel": "release-149",
                "x-bpm-version": "148.1",
                "x-bpm-source": "updated-fixture",
                "properties": {},
            }
        ),
        encoding="utf-8",
    )
    cached = service.load_policy_schema("release-149")
    assert cached.version == "149.0"

    service.load_policy_schema.cache_clear()


def test_load_policy_schema_attaches_ui_metadata(tmp_path, monkeypatch):
    release_file = tmp_path / "firefox-release-149.json"
    _write_schema(release_file)

    monkeypatch.setattr(service, "SCHEMAS_DIR", tmp_path)
    service.load_policy_schema.cache_clear()

    schema = service.load_policy_schema("release-149")
    definition = schema.get_policy("DisableTelemetry")

    assert schema.ui_sections
    assert definition is not None
    assert definition.ui is not None
    assert definition.ui.section == "privacy_security"
    assert definition.ui.subsection == "data_collection"
    assert definition.ui.widget == "toggle"
    assert definition.ui.support_level == "mapped"

    service.load_policy_schema.cache_clear()


def test_load_policy_schema_uses_safe_fallback_ui_metadata(tmp_path, monkeypatch):
    release_file = tmp_path / "firefox-release-149.json"
    _write_custom_schema(
        release_file,
        {
            "CustomPortal": {
                "type": "object",
                "properties": {
                    "URL": {"type": "string"},
                    "Locked": {"type": "boolean"},
                },
                "additionalProperties": False,
            }
        },
    )

    monkeypatch.setattr(service, "SCHEMAS_DIR", tmp_path)
    service.load_policy_schema.cache_clear()

    definition = service.load_policy_schema("release-149").get_policy("CustomPortal")

    assert definition is not None
    assert definition.ui is not None
    assert definition.ui.section == "advanced"
    assert definition.ui.subsection == "unmapped"
    assert definition.ui.widget == "object-card"
    assert definition.ui.support_level == "fallback"
    assert definition.ui.preserve_unknown_fields is False

    service.load_policy_schema.cache_clear()


def test_real_policy_schemas_expose_ui_metadata_for_every_policy():
    service.load_policy_schema.cache_clear()
    section_ids = {section.id for section in service.load_policy_schema("release-149").ui_sections}

    for channel in service.CHANNEL_TO_FILENAME:
        schema = service.load_policy_schema(channel)
        assert schema.ui_sections
        for definition in schema.policies.values():
            assert definition.ui is not None, definition.id
            assert definition.ui.widget
            assert definition.ui.section in section_ids


def test_real_policy_schemas_expose_expected_widgets_and_sections():
    service.load_policy_schema.cache_clear()
    schema = service.load_policy_schema("release-149")

    assert schema.get_policy("Proxy").ui.widget == "object-card"
    assert schema.get_policy("Proxy").ui.section == "network_access"
    assert schema.get_policy("ExtensionSettings").ui.widget == "dictionary"
    assert schema.get_policy("ExtensionSettings").ui.section == "extensions_integrations"
    assert schema.get_policy("Bookmarks").ui.widget == "array-of-objects"
    assert schema.get_policy("SearchBar").ui.widget == "enum-select"
    assert schema.get_policy("SanitizeOnShutdown").ui.widget == "branch"
    assert schema.get_policy("SanitizeOnShutdown").ui.section == "privacy_security"


def test_real_policy_schemas_capture_nested_map_and_branch_metadata():
    service.load_policy_schema.cache_clear()
    schema = service.load_policy_schema("release-149")

    authentication = schema.get_policy("Authentication")
    sanitize = schema.get_policy("SanitizeOnShutdown")
    permissions = schema.get_policy("Permissions")

    assert authentication is not None
    assert authentication.properties["AllowProxies"].additional_property_type == "boolean"
    assert authentication.properties["AllowProxies"].additional_property_enum == [True]

    assert sanitize is not None
    assert len(sanitize.branches) == 2
    assert sanitize.branches[0].type == "object"
    assert sanitize.branches[0].properties["Cache"].type == "boolean"
    assert sanitize.branches[1].type == "boolean"
    assert permissions is not None
    assert permissions.properties["Camera"].properties["Allow"].type == "array"
    assert permissions.properties["Camera"].properties["Locked"].type == "boolean"
    assert permissions.properties["Autoplay"].properties["Default"].enum == [
        "allow-audio-video",
        "block-audio",
        "block-audio-video",
    ]


def test_real_policy_schemas_capture_array_item_metadata():
    service.load_policy_schema.cache_clear()
    schema = service.load_policy_schema("release-149")

    bookmarks = schema.get_policy("Bookmarks")
    managed_bookmarks = schema.get_policy("ManagedBookmarks")

    assert bookmarks is not None
    assert bookmarks.items_type == "object"
    assert bookmarks.item_properties["Title"].required is True
    assert bookmarks.item_properties["Placement"].enum == ["toolbar", "menu"]

    assert managed_bookmarks is not None
    assert managed_bookmarks.items_type == "object"
    assert managed_bookmarks.item_properties["children"].type == "array"
    assert managed_bookmarks.item_properties["children"].items_type == "object"


def test_real_policy_schemas_capture_definition_additional_properties_schema():
    service.load_policy_schema.cache_clear()
    schema = service.load_policy_schema("release-149")

    extension_settings = schema.get_policy("ExtensionSettings")

    assert extension_settings is not None
    assert extension_settings.additional_property_type == "object"
    assert extension_settings.additional_property_properties["installation_mode"].enum == [
        "allowed",
        "blocked",
        "force_installed",
        "normal_installed",
    ]
    assert extension_settings.additional_property_properties["updates_disabled"].type == "boolean"


def test_json_schema_type_handles_oneof_non_dict_properties_items_and_fallback():
    assert service._json_schema_type({"oneOf": []}) == "object"
    assert service._json_schema_type({"oneOf": ["skip", {"type": "array"}]}) == "array"
    assert service._json_schema_type({"oneOf": [{"type": ""}, {"items": {"type": "string"}}]}) == "array"
    assert service._json_schema_type({"properties": {"Enabled": {"type": "boolean"}}}) == "object"
    assert service._json_schema_type({"items": {"type": "string"}}) == "array"
    assert service._json_schema_type({"title": "fallback"}) == "object"


def test_json_schema_to_policy_branch_handles_schema_additional_properties():
    branch = service._json_schema_to_policy_branch(
        {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["Enabled"],
                "properties": {
                    "Enabled": {"type": "boolean"},
                },
            },
        }
    )

    assert branch.type == "object"
    assert branch.additional_properties is True


def test_json_schema_to_policy_definition_normalizes_item_additional_properties_schema():
    definition = service._json_schema_to_policy_definition(
        "ManagedMap",
        {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": {
                    "type": "string",
                },
            },
        },
    )

    assert definition.type == "array"
    assert definition.item_additional_properties is True
