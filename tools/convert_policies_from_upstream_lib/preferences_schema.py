from __future__ import annotations

from typing import Any

from .common import (
    PREFERENCES_STATUS_ENUM,
    PREFERENCES_TYPE_ENUM,
    SchemaPolicyDefinition,
    UpstreamPolicyEntry,
)
from .snippet_parser import parse_min_version_from_compatibility


def _build_preferences_entry_schema() -> dict[str, Any]:
    value_schema = {
        "oneOf": [
            {"type": "boolean"},
            {"type": "number"},
            {"type": "string"},
        ]
    }

    return {
        "type": "object",
        "properties": {
            "Value": value_schema,
            "Status": {
                "type": "string",
                "enum": PREFERENCES_STATUS_ENUM,
            },
            "Type": {
                "type": "string",
                "enum": PREFERENCES_TYPE_ENUM,
            },
        },
        "additional_properties": False,
        "allOf": [
            {
                "if": {
                    "properties": {
                        "Type": {"const": "boolean"},
                    },
                    "required": ["Type"],
                },
                "then": {
                    "properties": {
                        "Value": {"type": "boolean"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "Type": {"const": "number"},
                    },
                    "required": ["Type"],
                },
                "then": {
                    "properties": {
                        "Value": {"type": "number"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "Type": {"const": "string"},
                    },
                    "required": ["Type"],
                },
                "then": {
                    "properties": {
                        "Value": {"type": "string"},
                    }
                },
            },
        ],
    }


def _build_preferences_policy(entry: UpstreamPolicyEntry) -> SchemaPolicyDefinition:
    return SchemaPolicyDefinition(
        id=entry.name,
        type="object",
        description_key=f"policy.{entry.name}",
        categories=[],
        min_version=parse_min_version_from_compatibility(entry.compatibility),
        max_version=None,
        deprecated=False,
        enum=None,
        items_type=None,
        items=None,
        schema=None,
        properties={},
        additional_properties=True,
        additional_properties_schema=_build_preferences_entry_schema(),
    )
