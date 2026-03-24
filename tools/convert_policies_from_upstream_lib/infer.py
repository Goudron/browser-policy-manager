from __future__ import annotations

import json
from typing import Any

from .common import ENUM_WRAPPER_KEY, SCALAR_TYPES
from .snippet_parser import infer_value_type_from_python


def _is_enum_wrapper(value: Any) -> bool:
    return isinstance(value, dict) and set(value.keys()) == {ENUM_WRAPPER_KEY}


def _looks_like_dynamic_object_key(key: str) -> bool:
    if key == "*":
        return True
    if key.isupper():
        return True
    if any(token in key for token in ("NAME_OF_", "PATH_TO_", "URL_TO_", "CIPHER_", "HOSTNAME")):
        return True
    if key.startswith("http://") or key.startswith("https://"):
        return True
    if any(char in key for char in ("@", "/", "*")):
        return True
    if "." in key:
        return True
    return False


def _enum_schema_from_values(values: list[Any]) -> dict[str, Any]:
    unique_values: list[Any] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)

    scalar_type = infer_value_type_from_python(unique_values[0]) if unique_values else "string"
    schema: dict[str, Any] = {
        "type": scalar_type,
        "default": unique_values[0] if unique_values else None,
    }

    if not (scalar_type == "boolean" and set(unique_values) == {True, False}):
        schema["enum"] = unique_values

    return schema


def _merge_inferred_schemas(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not nodes:
        return None
    if len(nodes) == 1:
        return nodes[0]

    types = {node.get("type") for node in nodes}
    if len(types) != 1:
        return None

    node_type = types.pop()
    if node_type in SCALAR_TYPES:
        merged: dict[str, Any] = {"type": node_type}
        enum_values: list[Any] = []
        for node in nodes:
            values = node.get("enum")
            if values is None and node.get("default") is not None:
                values = [node["default"]]
            for value in values or []:
                if value not in enum_values:
                    enum_values.append(value)
        if enum_values and not (node_type == "boolean" and set(enum_values) == {True, False}):
            merged["enum"] = enum_values
        return merged

    if node_type == "array":
        merged = {"type": "array"}
        item_nodes = [node["items"] for node in nodes if node.get("items")]
        merged_items = _merge_array_item_schemas(item_nodes) if item_nodes else None
        if merged_items:
            merged["items"] = merged_items
        return merged

    if node_type == "object":
        merged = {"type": "object"}
        prop_buckets: dict[str, list[dict[str, Any]]] = {}
        for node in nodes:
            for prop_name, prop_schema in (node.get("properties") or {}).items():
                prop_buckets.setdefault(prop_name, []).append(prop_schema)

        merged_props = {
            prop_name: merged_prop
            for prop_name, prop_nodes in prop_buckets.items()
            if (merged_prop := _merge_object_property_schemas(prop_nodes)) is not None
        }
        if merged_props:
            merged["properties"] = merged_props

        dynamic_nodes = [node["additional_properties_schema"] for node in nodes if node.get("additional_properties_schema")]
        merged_dynamic = _merge_inferred_schemas(dynamic_nodes) if dynamic_nodes else None
        if merged_dynamic is not None:
            merged["additional_properties_schema"] = merged_dynamic
            merged["additional_properties"] = True
        else:
            merged["additional_properties"] = any(node.get("additional_properties", False) for node in nodes)

        return merged

    return None


def _merge_object_property_schemas(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not nodes:
        return None
    if len(nodes) == 1:
        return nodes[0]

    if (merged := _merge_non_enum_scalar_schemas(nodes)) is not None:
        return merged

    return _merge_inferred_schemas(nodes)


def _merge_array_item_schemas(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not nodes:
        return None
    if len(nodes) == 1:
        return nodes[0]

    if (merged := _merge_non_enum_scalar_schemas(nodes)) is not None:
        return merged

    return _merge_inferred_schemas(nodes)


def _merge_non_enum_scalar_schemas(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not nodes:
        return None

    types = {node.get("type") for node in nodes}
    if len(types) != 1:
        return None

    scalar_type = next(iter(types))
    if scalar_type not in SCALAR_TYPES:
        return None

    if any(node.get("enum") is not None for node in nodes):
        return None

    merged: dict[str, Any] = {"type": scalar_type}
    for keyword in ("pattern", "format", "minimum", "maximum", "const"):
        values = [node.get(keyword) for node in nodes]
        first = values[0]
        if first is not None and all(value == first for value in values):
            merged[keyword] = first
    return merged


def _dedupe_schema_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    fingerprints: set[str] = set()
    for node in nodes:
        fingerprint = json.dumps(node, sort_keys=True, ensure_ascii=False)
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        unique.append(node)
    return unique


def _combine_inferred_nodes(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    deduped = _dedupe_schema_nodes(nodes)
    if len(deduped) == 1:
        return deduped[0]

    merged = _merge_inferred_schemas(deduped)
    if merged is not None:
        return merged

    return {"oneOf": deduped}


def infer_schema_from_example_value(value: Any) -> dict[str, Any]:
    """Infer a recursive schema node from one example value."""
    if _is_enum_wrapper(value):
        return _enum_schema_from_values(value[ENUM_WRAPPER_KEY])

    if isinstance(value, dict):
        if not value:
            return {
                "type": "object",
                "properties": {},
                "additional_properties": True,
            }

        if all(_looks_like_dynamic_object_key(key) for key in value):
            value_schemas = [infer_schema_from_example_value(item) for item in value.values()]
            merged_dynamic = _merge_inferred_schemas(value_schemas)
            schema = {
                "type": "object",
                "properties": {},
                "additional_properties": True,
            }
            if merged_dynamic is not None:
                schema["additional_properties_schema"] = merged_dynamic
            return schema

        return {
            "type": "object",
            "properties": {
                key: infer_schema_from_example_value(item)
                for key, item in value.items()
            },
            "additional_properties": False,
        }

    if isinstance(value, list):
        schema: dict[str, Any] = {"type": "array"}
        if not value:
            return schema

        item_schemas = [infer_schema_from_example_value(item) for item in value]
        merged_items = _merge_array_item_schemas(item_schemas)
        if merged_items is not None:
            schema["items"] = merged_items

        if all(not isinstance(item, (list, dict)) and not _is_enum_wrapper(item) for item in value):
            schema["default"] = value

        return schema

    return {
        "type": infer_value_type_from_python(value),
        "default": value,
    }
