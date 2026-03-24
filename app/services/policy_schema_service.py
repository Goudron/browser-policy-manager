from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from app.models.policy_schema import PolicyBranch, PolicyDefinition, PolicySchema
from app.services.firefox_policy_ui_registry import get_policy_ui_sections, resolve_policy_ui_metadata

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = BASE_DIR / "schemas" / "policies"


# Channels we support and their corresponding schema files.
CHANNEL_TO_FILENAME: dict[str, str] = {
    "release-148": "firefox-release-148.json",
    "esr-140": "firefox-esr-140.json",
}


class UnknownPolicyChannelError(ValueError):
    """Raised when an unknown policy channel is requested."""


def _get_schema_path(channel: str) -> Path:
    try:
        filename = CHANNEL_TO_FILENAME[channel]
    except KeyError as exc:
        raise UnknownPolicyChannelError(f"Unknown policy channel: {channel!r}") from exc

    path = SCHEMAS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Policy schema file not found: {path}")
    return path


@cache
def load_policy_schema(channel: str) -> PolicySchema:
    """Load and cache the policy schema for a given channel.

    The result is cached in memory for the lifetime of the process.
    """
    path = _get_schema_path(channel)
    data = json.loads(path.read_text(encoding="utf-8"))
    return _raw_json_schema_to_policy_schema(channel, data)


def get_policy_definition(channel: str, policy_id: str) -> PolicyDefinition | None:
    """Return a specific policy definition by ID for the given channel."""
    schema = load_policy_schema(channel)
    return schema.get_policy(policy_id)


def _json_schema_type(node: dict[str, Any]) -> str:
    node_type = node.get("type")
    if isinstance(node_type, str):
        return node_type

    one_of = node.get("oneOf")
    if isinstance(one_of, list):
        for branch in one_of:
            if isinstance(branch, dict):
                branch_type = _json_schema_type(branch)
                if branch_type:
                    return branch_type

    if isinstance(node.get("properties"), dict) or "additionalProperties" in node:
        return "object"
    if isinstance(node.get("items"), dict):
        return "array"

    return "object"


def _json_schema_to_policy_property(name: str, node: dict[str, Any], required: bool = False):
    property_type = _json_schema_type(node)
    enum = node.get("enum")
    items = node.get("items") if isinstance(node.get("items"), dict) else None
    items_type = items.get("type") if isinstance(items, dict) and isinstance(items.get("type"), str) else None
    if property_type == "array" and enum is None and isinstance(items, dict):
        enum = items.get("enum")
    additional_properties_node = node.get("additionalProperties", True)
    additional_properties = additional_properties_node
    additional_property_type = None
    additional_property_enum = None
    if isinstance(additional_properties_node, dict):
        additional_property_type = _json_schema_type(additional_properties_node)
        additional_property_enum = additional_properties_node.get("enum")
        additional_properties = True

    required_properties = set(node.get("required") or [])
    properties = {
        prop_name: _json_schema_to_policy_property(
            prop_name,
            prop_schema,
            required=prop_name in required_properties,
        )
        for prop_name, prop_schema in (node.get("properties") or {}).items()
        if isinstance(prop_schema, dict)
    }
    item_required_properties = set(items.get("required") or []) if isinstance(items, dict) else set()
    item_properties = {
        prop_name: _json_schema_to_policy_property(
            prop_name,
            prop_schema,
            required=prop_name in item_required_properties,
        )
        for prop_name, prop_schema in ((items or {}).get("properties") or {}).items()
        if isinstance(prop_schema, dict)
    }
    additional_property_schema = additional_properties_node if isinstance(additional_properties_node, dict) else {}
    additional_property_required_properties = set(additional_property_schema.get("required") or [])
    additional_property_properties = {
        prop_name: _json_schema_to_policy_property(
            prop_name,
            prop_schema,
            required=prop_name in additional_property_required_properties,
        )
        for prop_name, prop_schema in (additional_property_schema.get("properties") or {}).items()
        if isinstance(prop_schema, dict)
    }

    return {
        "name": name,
        "type": property_type,
        "description_key": node.get("x-bpm-description-key"),
        "enum": enum,
        "items_type": items_type,
        "minimum": node.get("minimum"),
        "maximum": node.get("maximum"),
        "default": node.get("default"),
        "required": required,
        "additional_properties": additional_properties,
        "additional_property_type": additional_property_type,
        "additional_property_enum": additional_property_enum,
        "item_properties": item_properties,
        "properties": properties,
        "additional_property_properties": additional_property_properties,
    }


def _json_schema_to_policy_branch(node: dict[str, Any]) -> PolicyBranch:
    branch_type = _json_schema_type(node)
    required_properties = set(node.get("required") or [])
    properties = {
        prop_name: _json_schema_to_policy_property(
            prop_name,
            prop_schema,
            required=prop_name in required_properties,
        )
        for prop_name, prop_schema in (node.get("properties") or {}).items()
        if isinstance(prop_schema, dict)
    }
    additional_properties = node.get("additionalProperties", True)
    additional_property_type = None
    additional_property_properties = {}
    if isinstance(additional_properties, dict):
        additional_property_type = _json_schema_type(additional_properties)
        additional_required_properties = set(additional_properties.get("required") or [])
        additional_property_properties = {
            prop_name: _json_schema_to_policy_property(
                prop_name,
                prop_schema,
                required=prop_name in additional_required_properties,
            )
            for prop_name, prop_schema in (additional_properties.get("properties") or {}).items()
            if isinstance(prop_schema, dict)
        }
        additional_properties = True

    return PolicyBranch.model_validate(
        {
            "type": branch_type,
            "enum": node.get("enum"),
            "properties": properties,
            "additional_properties": additional_properties,
        }
    )


def _json_schema_to_policy_definition(policy_id: str, node: dict[str, Any]) -> PolicyDefinition:
    policy_type = _json_schema_type(node)
    items = node.get("items") if isinstance(node.get("items"), dict) else None
    enum = node.get("enum")
    items_type = items.get("type") if isinstance(items, dict) and isinstance(items.get("type"), str) else None
    if policy_type == "array" and enum is None and isinstance(items, dict):
        enum = items.get("enum")

    required_properties = set(node.get("required") or [])
    properties = {
        prop_name: _json_schema_to_policy_property(
            prop_name,
            prop_schema,
            required=prop_name in required_properties,
        )
        for prop_name, prop_schema in (node.get("properties") or {}).items()
        if isinstance(prop_schema, dict)
    }
    item_required_properties = set(items.get("required") or []) if isinstance(items, dict) else set()
    item_properties = {
        prop_name: _json_schema_to_policy_property(
            prop_name,
            prop_schema,
            required=prop_name in item_required_properties,
        )
        for prop_name, prop_schema in ((items or {}).get("properties") or {}).items()
        if isinstance(prop_schema, dict)
    }

    additional_properties = node.get("additionalProperties", True)
    additional_property_type = None
    additional_property_properties = {}
    if isinstance(additional_properties, dict):
        additional_property_type = _json_schema_type(additional_properties)
        additional_required_properties = set(additional_properties.get("required") or [])
        additional_property_properties = {
            prop_name: _json_schema_to_policy_property(
                prop_name,
                prop_schema,
                required=prop_name in additional_required_properties,
            )
            for prop_name, prop_schema in (additional_properties.get("properties") or {}).items()
            if isinstance(prop_schema, dict)
        }
        additional_properties = True
    item_additional_properties = (items or {}).get("additionalProperties", True) if isinstance(items, dict) else True
    if isinstance(item_additional_properties, dict):
        item_additional_properties = True
    branches = [
        _json_schema_to_policy_branch(branch)
        for branch in (node.get("oneOf") or [])
        if isinstance(branch, dict)
    ]

    return PolicyDefinition.model_validate(
        {
            "id": node.get("x-bpm-id") or policy_id,
            "type": policy_type,
            "description_key": node.get("x-bpm-description-key"),
            "categories": node.get("x-bpm-categories") or [],
            "min_version": node.get("x-bpm-min-version"),
            "max_version": node.get("x-bpm-max-version"),
            "deprecated": bool(node.get("x-bpm-deprecated", False)),
            "enum": enum,
            "items_type": items_type,
            "item_properties": item_properties,
            "item_additional_properties": item_additional_properties,
            "additional_property_type": additional_property_type,
            "additional_property_properties": additional_property_properties,
            "properties": properties,
            "additional_properties": additional_properties,
            "branches": [branch.model_dump() for branch in branches],
            "ui": resolve_policy_ui_metadata(policy_id, policy_type, schema_node=node).model_dump(),
        }
    )


def _raw_json_schema_to_policy_schema(channel: str, data: dict[str, Any]) -> PolicySchema:
    properties = data.get("properties") or {}
    policies = {
        policy_id: _json_schema_to_policy_definition(policy_id, policy_schema)
        for policy_id, policy_schema in properties.items()
        if isinstance(policy_schema, dict)
    }

    return PolicySchema.model_validate(
        {
            "channel": data.get("x-bpm-channel") or channel,
            "version": data.get("x-bpm-version") or "",
            "source": data.get("x-bpm-source") or "raw-json-schema",
            "policies": policies,
            "ui_sections": [section.model_dump() for section in get_policy_ui_sections()],
        }
    )
