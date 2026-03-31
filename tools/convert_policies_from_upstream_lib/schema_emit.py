from __future__ import annotations

from typing import Any

from .common import SCALAR_TYPES, SchemaPolicyDefinition, UpstreamPolicyEntry
from .snippet_parser import parse_min_version_from_compatibility


def _primary_type_from_schema_node(node: dict[str, Any]) -> str:
    node_type = node.get("type")
    if isinstance(node_type, str):
        return node_type

    if isinstance(node.get("oneOf"), list) and node["oneOf"]:
        for branch in node["oneOf"]:
            if isinstance(branch, dict):
                branch_type = _primary_type_from_schema_node(branch)
                if branch_type:
                    return branch_type

    if isinstance(node.get("properties"), dict) or "additional_properties" in node or "additional_properties_schema" in node:
        return "object"
    if isinstance(node.get("items"), dict):
        return "array"
    return "object"


def _schema_node_to_property_dict(
    prop_name: str,
    description_key: str,
    node: dict[str, Any],
) -> dict[str, Any]:
    property_dict: dict[str, Any] = {
        "name": prop_name,
        "type": node["type"],
        "description_key": description_key,
        "enum": node.get("enum"),
        "items_type": node.get("items", {}).get("type") if node.get("type") == "array" and node.get("items", {}).get("type") in SCALAR_TYPES else None,
        "minimum": node.get("minimum"),
        "maximum": node.get("maximum"),
        "default": node.get("default"),
        "required": False,
    }

    if node.get("pattern") is not None:
        property_dict["pattern"] = node["pattern"]
    if node.get("format") is not None:
        property_dict["format"] = node["format"]

    if node.get("type") == "array":
        items_schema = node.get("items")
        if isinstance(items_schema, dict):
            item_type = items_schema.get("type")
            item_has_extra_constraints = any(
                key in items_schema for key in ("pattern", "format", "minimum", "maximum", "const", "oneOf", "anyOf", "allOf")
            )
        else:
            item_type = None
            item_has_extra_constraints = False

        if isinstance(items_schema, dict) and (item_type not in SCALAR_TYPES or item_has_extra_constraints):
            property_dict["items"] = items_schema
        elif isinstance(items_schema, dict) and items_schema.get("enum") is not None:
            property_dict["enum"] = items_schema["enum"]

    if node.get("type") == "object":
        property_dict["properties"] = {
            child_name: _schema_node_to_property_dict(
                child_name,
                f"{description_key}.{child_name}",
                child_schema,
            )
            for child_name, child_schema in (node.get("properties") or {}).items()
        }
        property_dict["additional_properties"] = node.get("additional_properties", True)
        if node.get("additional_properties_schema") is not None:
            property_dict["additional_properties_schema"] = node["additional_properties_schema"]

    return property_dict


def _policy_definition_from_inferred_node(
    entry: UpstreamPolicyEntry,
    node: dict[str, Any],
) -> SchemaPolicyDefinition:
    node_type = _primary_type_from_schema_node(node)
    properties = {
        prop_name: _schema_node_to_property_dict(
            prop_name,
            f"policy.{entry.policy_key}.{prop_name}",
            prop_schema,
        )
        for prop_name, prop_schema in (node.get("properties") or {}).items()
    }

    items_schema = node.get("items")
    items_type = items_schema.get("type") if isinstance(items_schema, dict) and items_schema.get("type") in SCALAR_TYPES else None
    enum = None
    items = None
    if node_type == "array" and isinstance(items_schema, dict):
        if items_schema.get("enum") is not None:
            enum = items_schema["enum"]
        if items_schema.get("type") not in SCALAR_TYPES or any(
            key in items_schema for key in ("pattern", "format", "minimum", "maximum", "const", "oneOf", "anyOf", "allOf")
        ):
            items = items_schema

    return SchemaPolicyDefinition(
        id=entry.policy_key,
        type=node_type,
        description_key=f"policy.{entry.policy_key}",
        categories=[],
        min_version=parse_min_version_from_compatibility(entry.compatibility),
        max_version=None,
        deprecated=False,
        enum=enum if node_type == "array" else node.get("enum"),
        items_type=items_type,
        items=items,
        schema=node,
        properties=properties,
        additional_properties=node.get("additional_properties", True),
        additional_properties_schema=node.get("additional_properties_schema"),
    )


def _legacy_property_to_json_schema(node: dict[str, Any]) -> dict[str, Any]:
    schema: dict[str, Any] = {}
    node_type = node.get("type")

    if node_type is not None:
        schema["type"] = node_type

    description_key = node.get("description_key")
    if description_key:
        schema["x-bpm-description-key"] = description_key

    if node.get("default") is not None:
        schema["default"] = node["default"]
    if node.get("minimum") is not None:
        schema["minimum"] = node["minimum"]
    if node.get("maximum") is not None:
        schema["maximum"] = node["maximum"]
    if node.get("pattern") is not None:
        schema["pattern"] = node["pattern"]
    if node.get("format") is not None:
        schema["format"] = node["format"]

    if node_type == "array" or node.get("items_type") is not None or isinstance(node.get("items"), dict):
        items_schema = (
            _legacy_property_to_json_schema(node["items"])
            if isinstance(node.get("items"), dict)
            else dict(node.get("items") or {})
        )
        items_type = node.get("items_type")
        if items_type is not None:
            items_schema.setdefault("type", items_type)
        if node.get("enum") is not None:
            items_schema["enum"] = node["enum"]
        if items_schema:
            schema["items"] = items_schema
    elif node.get("enum") is not None:
        schema["enum"] = node["enum"]

    if "const" in node:
        schema["const"] = node["const"]

    has_object_shape = (
        node_type == "object"
        or bool(node.get("properties"))
        or "additional_properties" in node
        or "additional_properties_schema" in node
    )
    if has_object_shape:
        properties = {
            prop_name: _legacy_property_to_json_schema(prop_schema)
            for prop_name, prop_schema in (node.get("properties") or {}).items()
        }
        schema["properties"] = properties

        additional_properties_schema = node.get("additional_properties_schema")
        if isinstance(additional_properties_schema, dict):
            schema["additionalProperties"] = _legacy_property_to_json_schema(additional_properties_schema)
        else:
            schema["additionalProperties"] = node.get("additional_properties", True)

        required = [
            prop_name
            for prop_name, prop_schema in (node.get("properties") or {}).items()
            if prop_schema.get("required")
        ]
        if required:
            schema["required"] = required

    if isinstance(node.get("required"), list):
        schema["required"] = node["required"]

    for keyword in ("oneOf", "anyOf", "allOf"):
        if isinstance(node.get(keyword), list):
            schema[keyword] = [
                _legacy_property_to_json_schema(branch) if isinstance(branch, dict) else branch
                for branch in node[keyword]
            ]

    for keyword in ("if", "then", "else", "not"):
        branch = node.get(keyword)
        if isinstance(branch, dict):
            schema[keyword] = _legacy_property_to_json_schema(branch)

    return schema
