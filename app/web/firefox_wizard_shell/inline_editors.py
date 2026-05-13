from __future__ import annotations

from typing import Any

from .serializer import humanize_identifier

INLINE_EDITOR_POLICY_IDS = {
    "AIControls",
    "AppAutoUpdate",
    "Authentication",
    "Bookmarks",
    "Certificates",
    "Cookies",
    "DNSOverHTTPS",
    "DisableAppUpdate",
    "DisableSystemAddonUpdate",
    "DontCheckDefaultBrowser",
    "ExtensionSettings",
    "GenerativeAI",
    "FirefoxHome",
    "FirefoxSuggest",
    "Handlers",
    "Homepage",
    "IPProtectionAvailable",
    "InstallAddonsPermission",
    "ManagedBookmarks",
    "NewTabPage",
    "Permissions",
    "PromptForDownloadLocation",
    "Proxy",
    "SanitizeOnShutdown",
    "SearchEngines",
    "UserMessaging",
    "VisualSearchEnabled",
    "WebsiteFilter",
    "WindowsSSO",
}


def build_inline_editor(definition) -> dict[str, Any] | None:
    if definition.id not in INLINE_EDITOR_POLICY_IDS:
        return None

    if definition.id == "SanitizeOnShutdown":
        return _build_branch_inline_editor(definition)

    if definition.additional_property_type == "object" and definition.additional_property_properties:
        return _build_dictionary_inline_editor(definition)

    if definition.type == "array" and definition.items_type == "object":
        return _build_array_inline_editor(definition)

    if definition.type == "boolean":
        return {
            "kind": "boolean-select",
            "managed_fields": [],
        }

    if definition.type != "object":
        return None

    fields: list[dict[str, Any]] = []
    unsupported_count = 0
    managed_fields: list[str] = []

    for prop_name, prop in definition.properties.items():
        field_spec = _build_object_field_spec(prop)
        if field_spec is None:
            unsupported_count += 1
            continue

        managed_fields.append(prop_name)
        fields.append(
            {
                "name": prop_name,
                "label": humanize_identifier(prop_name),
                **field_spec,
            }
        )

    if not fields:
        return None

    return {
        "kind": "object-card",
        "managed_fields": managed_fields,
        "fields": fields,
        "unsupported_field_count": unsupported_count,
    }


def _resolve_field_kind(prop) -> str | None:
    if prop.type == "boolean":
        return "boolean-select"
    if prop.type == "string":
        return "enum-select" if prop.enum else "text"
    if prop.type in {"integer", "number"}:
        return "number"
    if prop.type == "array" and prop.items_type == "string":
        return "string-list"
    if (
        prop.type == "object"
        and prop.additional_property_type == "boolean"
        and prop.additional_property_enum == [True]
    ):
        return "true-map"
    return None


def _build_object_field_spec(prop, *, allow_nested: bool = True) -> dict[str, Any] | None:
    field_kind = _resolve_field_kind(prop)
    if field_kind is not None:
        return {
            "kind": field_kind,
            "required": prop.required,
            "enum": list(prop.enum or []),
        }

    if allow_nested and prop.type == "object" and prop.properties:
        fields: list[dict[str, Any]] = []
        managed_fields: list[str] = []
        unsupported_count = 0

        for child_name, child_prop in prop.properties.items():
            child_spec = _build_object_field_spec(child_prop, allow_nested=True)
            if child_spec is None:
                unsupported_count += 1
                continue

            managed_fields.append(child_name)
            fields.append(
                {
                    "name": child_name,
                    "label": humanize_identifier(child_name),
                    **child_spec,
                }
            )

        if fields:
            return {
                "kind": "nested-object",
                "managed_fields": managed_fields,
                "fields": fields,
                "unsupported_field_count": unsupported_count,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }

    if allow_nested and prop.type == "object" and prop.additional_property_type == "object" and prop.additional_property_properties:
        nested_fields: list[dict[str, Any]] = []
        unsupported_count = 0

        for child_name, child_prop in prop.additional_property_properties.items():
            child_spec = _build_object_field_spec(child_prop, allow_nested=True)
            if child_spec is None:
                unsupported_count += 1
                continue

            nested_fields.append(
                {
                    "name": child_name,
                    "label": humanize_identifier(child_name),
                    **child_spec,
                }
            )

        if nested_fields:
            return {
                "kind": "nested-dictionary-object",
                "fields": nested_fields,
                "unsupported_field_count": unsupported_count,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }

    if allow_nested and prop.type == "array" and prop.items_type == "object" and prop.item_properties:
        array_item_fields: list[dict[str, Any]] = []
        unsupported_count = 0

        for child_name, child_prop in prop.item_properties.items():
            child_spec = _build_object_field_spec(child_prop, allow_nested=True)
            if child_spec is None:
                unsupported_count += 1
                continue

            array_item_fields.append(
                {
                    "name": child_name,
                    "label": humanize_identifier(child_name),
                    **child_spec,
                }
            )

        if array_item_fields:
            return {
                "kind": "nested-array-of-objects",
                "fields": array_item_fields,
                "unsupported_field_count": unsupported_count,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }

    return None


def _resolve_array_field_kind(prop) -> str | None:
    direct = _resolve_field_kind(prop)
    if direct is not None:
        return direct
    if prop.type in {"object", "array"}:
        return "json"
    return None


def _build_array_inline_editor(definition) -> dict[str, Any] | None:
    if not definition.item_properties:
        return None

    fields: list[dict[str, Any]] = []
    for prop_name, prop in definition.item_properties.items():
        field_kind = _resolve_array_field_kind(prop)
        if field_kind is None:
            continue
        fields.append(
            {
                "name": prop_name,
                "label": humanize_identifier(prop_name),
                "kind": field_kind,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }
        )

    if not fields:
        return None

    return {
        "kind": "array-of-objects",
        "fields": fields,
    }


def _build_dictionary_inline_editor(definition) -> dict[str, Any] | None:
    fields: list[dict[str, Any]] = []
    for prop_name, prop in definition.additional_property_properties.items():
        field_kind = _resolve_array_field_kind(prop)
        if field_kind is None:
            continue
        fields.append(
            {
                "name": prop_name,
                "label": humanize_identifier(prop_name),
                "kind": field_kind,
                "required": prop.required,
                "enum": list(prop.enum or []),
            }
        )

    if not fields:
        return None

    return {
        "kind": "dictionary-object",
        "fields": fields,
    }


def _build_branch_inline_editor(definition) -> dict[str, Any] | None:
    if not definition.branches:
        return None

    branches: list[dict[str, Any]] = []
    for branch in definition.branches:
        if branch.type == "boolean":
            branches.append(
                {
                    "id": "boolean",
                    "kind": "boolean-select",
                }
            )
            continue

        if branch.type != "object":
            continue

        fields: list[dict[str, Any]] = []
        managed_fields: list[str] = []
        unsupported_count = 0
        for prop_name, prop in branch.properties.items():
            field_spec = _build_object_field_spec(prop)
            if field_spec is None:
                unsupported_count += 1
                continue

            managed_fields.append(prop_name)
            fields.append(
                {
                    "name": prop_name,
                    "label": humanize_identifier(prop_name),
                    **field_spec,
                }
            )

        branches.append(
            {
                "id": "object",
                "kind": "object-card",
                "managed_fields": managed_fields,
                "fields": fields,
                "unsupported_field_count": unsupported_count,
            }
        )

    return {"kind": "branch", "branches": branches}
