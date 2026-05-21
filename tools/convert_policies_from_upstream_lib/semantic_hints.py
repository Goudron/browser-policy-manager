from __future__ import annotations

from typing import Any

from .common import (
    HANDLER_ACTION_ENUM,
    HTTP_OR_HTTPS_PATTERN,
    HTTPS_URI_TEMPLATE_PATTERN,
    SEARCH_TERMS_PATTERN,
    UpstreamPolicyEntry,
)


def _set_property_pattern(node: dict[str, Any], property_name: str, pattern: str) -> None:
    prop = (node.get("properties") or {}).get(property_name)
    if isinstance(prop, dict) and prop.get("type") == "string":
        prop["pattern"] = pattern


def _set_array_items_pattern(node: dict[str, Any], property_name: str, pattern: str) -> None:
    prop = (node.get("properties") or {}).get(property_name)
    if not isinstance(prop, dict) or prop.get("type") != "array":
        return
    items = prop.get("items")
    if isinstance(items, dict) and items.get("type") == "string":
        items["pattern"] = pattern


def _apply_search_engines_semantic_hints(node: dict[str, Any]) -> None:
    add = (node.get("properties") or {}).get("Add")
    items = add.get("items") if isinstance(add, dict) else None
    if not isinstance(items, dict):
        return

    _set_property_pattern(items, "URLTemplate", SEARCH_TERMS_PATTERN)
    _set_property_pattern(items, "SuggestURLTemplate", SEARCH_TERMS_PATTERN)


def _apply_cookies_semantic_hints(node: dict[str, Any]) -> None:
    for prop_name in ("Allow", "AllowSession", "Block"):
        _set_array_items_pattern(node, prop_name, HTTP_OR_HTTPS_PATTERN)


def _apply_permissions_semantic_hints(node: dict[str, Any]) -> None:
    for permission_schema in (node.get("properties") or {}).values():
        if not isinstance(permission_schema, dict) or permission_schema.get("type") != "object":
            continue
        for prop_name in ("Allow", "Block"):
            _set_array_items_pattern(permission_schema, prop_name, HTTP_OR_HTTPS_PATTERN)


def _apply_handlers_semantic_hints(node: dict[str, Any]) -> None:
    def _walk_handler_scope(scope: dict[str, Any]) -> None:
        properties = scope.get("properties") or {}
        if not isinstance(properties, dict):
            return

        action = properties.get("action")
        if isinstance(action, dict) and action.get("type") == "string":
            action["enum"] = HANDLER_ACTION_ENUM

        handlers = properties.get("handlers")
        items = handlers.get("items") if isinstance(handlers, dict) else None
        if isinstance(items, dict) and items.get("type") == "object":
            _set_property_pattern(items, "uriTemplate", HTTPS_URI_TEMPLATE_PATTERN)

        for child in properties.values():
            if isinstance(child, dict) and child.get("type") == "object":
                _walk_handler_scope(child)

        additional_properties = scope.get("additional_properties_schema")
        if isinstance(additional_properties, dict) and additional_properties.get("type") == "object":
            _walk_handler_scope(additional_properties)

    _walk_handler_scope(node)


def _apply_extension_settings_semantic_hints(node: dict[str, Any]) -> None:
    additional_properties = node.get("additional_properties_schema")
    if not isinstance(additional_properties, dict):
        return

    properties = additional_properties.setdefault("properties", {})
    if not isinstance(properties, dict):
        return

    properties.setdefault(
        "update_url",
        {
            "type": "string",
        },
    )


def _apply_semantic_hints(entry: UpstreamPolicyEntry, node: dict[str, Any]) -> None:
    if entry.name == "SearchEngines":
        _apply_search_engines_semantic_hints(node)
    elif entry.name == "Cookies":
        _apply_cookies_semantic_hints(node)
    elif entry.name == "Permissions":
        _apply_permissions_semantic_hints(node)
    elif entry.name == "Handlers":
        _apply_handlers_semantic_hints(node)
    elif entry.name == "ExtensionSettings":
        _apply_extension_settings_semantic_hints(node)
