from __future__ import annotations

from typing import Any

from .common import SchemaPolicyDefinition, UpstreamPolicyEntry
from .html_parser import (
    _canonical_policy_name,
    extract_policies_table,
    extract_policy_details,
    load_html,
)
from .schema_inference import (
    _apply_property_description_hints,
    _apply_required_property_hints,
    _apply_semantic_hints,
    _build_preferences_policy,
    _combine_inferred_nodes,
    _legacy_property_to_json_schema,
    _policy_definition_from_inferred_node,
    infer_schema_from_example_value,
)
from .snippet_parser import (
    _extract_policy_keys_from_snippet,
    _extract_policy_value_node,
    _extract_policy_value_nodes,
    infer_type_from_policies_json,
    infer_value_type_from_python,
    parse_min_version_from_compatibility,
)


def extract_policy_properties_from_snippet(
    policy_name: str, snippet: str | None
) -> dict[str, dict]:
    """Extract top-level object properties from a policy example snippet."""
    if not snippet:
        return {}

    value = _extract_policy_value_node(policy_name, snippet)
    if not isinstance(value, dict):
        return {}

    properties: dict[str, dict] = {}
    for prop_name, prop_value in value.items():
        prop_type = infer_value_type_from_python(prop_value)
        enum: list[Any] | None = None
        items_type: str | None = None

        if isinstance(prop_value, list) and prop_value:
            scalar_elems = all(not isinstance(e, (list, dict)) for e in prop_value)
            if scalar_elems:
                elem_type = infer_value_type_from_python(prop_value[0])
                if all(infer_value_type_from_python(e) == elem_type for e in prop_value):
                    prop_type = "array"
                    items_type = elem_type
                    unique_vals: list[Any] = []
                    for e in prop_value:
                        if e not in unique_vals:
                            unique_vals.append(e)
                    if 1 < len(unique_vals) <= 20:
                        enum = unique_vals
                default_value: Any = prop_value
            else:
                default_value = None
        elif isinstance(prop_value, (str, int, float, bool)):
            default_value = prop_value
        else:
            default_value = None

        properties[prop_name] = {
            "name": prop_name,
            "type": prop_type,
            "description_key": f"policy.{policy_name}.{prop_name}",
            "enum": enum,
            "items_type": items_type,
            "minimum": None,
            "maximum": None,
            "default": default_value,
            "required": False,
        }

    return properties


def extract_policy_array_metadata_from_snippet(
    policy_name: str,
    snippet: str | None,
) -> tuple[str | None, list[Any] | None]:
    """Infer array item type and enum values from a top-level array policy example."""
    value = _extract_policy_value_node(policy_name, snippet)
    if not isinstance(value, list) or not value:
        return None, None

    scalar_elems = all(not isinstance(e, (list, dict)) for e in value)
    if not scalar_elems:
        return None, None

    elem_type = infer_value_type_from_python(value[0])
    if not all(infer_value_type_from_python(e) == elem_type for e in value):
        return None, None

    unique_vals: list[Any] = []
    for e in value:
        if e not in unique_vals:
            unique_vals.append(e)

    enum = unique_vals if 1 < len(unique_vals) <= 20 else None
    return elem_type, enum


def _policy_definition_to_json_schema(policy: SchemaPolicyDefinition) -> dict[str, Any]:
    if policy.schema is not None:
        schema = _legacy_property_to_json_schema(policy.schema)
    else:
        legacy_node: dict[str, Any] = {
            "type": policy.type,
            "enum": policy.enum,
            "items_type": policy.items_type,
            "items": policy.items,
        }
        if policy.type == "object":
            legacy_node["properties"] = policy.properties
            legacy_node["additional_properties"] = policy.additional_properties
            legacy_node["additional_properties_schema"] = policy.additional_properties_schema

        schema = _legacy_property_to_json_schema(legacy_node)

    schema["x-bpm-id"] = policy.id
    if policy.description_key:
        schema["x-bpm-description-key"] = policy.description_key
    if policy.categories:
        schema["x-bpm-categories"] = policy.categories
    if policy.min_version is not None:
        schema["x-bpm-min-version"] = policy.min_version
    if policy.max_version is not None:
        schema["x-bpm-max-version"] = policy.max_version
    if policy.deprecated:
        schema["x-bpm-deprecated"] = True

    return schema


def build_schema_policy(
    entry: UpstreamPolicyEntry,
    linux_policy_examples: dict[str, Any] | None = None,
) -> SchemaPolicyDefinition:
    """Convert an UpstreamPolicyEntry to our internal SchemaPolicyDefinition."""
    if entry.name == "Preferences":
        return _build_preferences_policy(entry)

    example_values: list[Any] = []
    if linux_policy_examples:
        linux_value = linux_policy_examples.get(entry.policy_key)
        if linux_value is not None:
            example_values.append(linux_value)

    example_values.extend(_extract_policy_value_nodes(entry.policy_key, entry.policies_json_snippet))

    if example_values:
        inferred_nodes = [infer_schema_from_example_value(example_value) for example_value in example_values]
        inferred = _combine_inferred_nodes(inferred_nodes)
        _apply_required_property_hints(entry.section_text, inferred)
        _apply_property_description_hints(entry, inferred)
        _apply_semantic_hints(entry, inferred)
        return _policy_definition_from_inferred_node(entry, inferred)

    min_version = parse_min_version_from_compatibility(entry.compatibility)
    ptype = infer_type_from_policies_json(entry.name, entry.policies_json_snippet)
    return SchemaPolicyDefinition(
        id=entry.policy_key,
        type=ptype,
        description_key=f"policy.{entry.policy_key}",
        categories=[],
        min_version=min_version,
        max_version=None,
        deprecated=False,
        enum=None,
        items_type=None,
        items=None,
        schema=None,
        properties={},
        additional_properties=True,
        additional_properties_schema=None,
    )


def schema_to_json_schema(
    channel: str,
    version: str,
    source: str,
    policies: list[SchemaPolicyDefinition],
) -> dict:
    """Convert a list of SchemaPolicyDefinition to a raw JSON Schema bundle."""
    title_channel = str(channel or "Firefox").replace("-", " ").title()
    title = f"{title_channel} Policies"
    if version:
        title = f"{title} {version}"

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "additionalProperties": False,
        "x-bpm-channel": channel,
        "x-bpm-version": version,
        "x-bpm-source": source,
        "properties": {
            p.id: _policy_definition_to_json_schema(p)
            for p in policies
        },
    }


def _version_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()
    return tuple(int(part) for part in value.split(".") if part.isdigit())


def filter_policies_for_target_version(
    policies: list[SchemaPolicyDefinition],
    target_version: str,
) -> list[SchemaPolicyDefinition]:
    """Keep only policies available by the target Firefox version."""
    target = _version_tuple(target_version)
    if not target:
        return list(policies)

    return [
        policy
        for policy in policies
        if not policy.min_version or _version_tuple(policy.min_version) <= target
    ]


def convert_upstream_html_to_policies(html_path) -> list[UpstreamPolicyEntry]:
    """Parse the upstream HTML and return a list of UpstreamPolicyEntry objects."""
    soup = load_html(html_path)
    table_entries = extract_policies_table(soup)
    result: list[UpstreamPolicyEntry] = []

    for name, description in table_entries:
        compatibility, section_text, policies_json, property_descriptions = extract_policy_details(soup, name)
        snippet_keys = _extract_policy_keys_from_snippet(policies_json)
        policy_key = snippet_keys[0] if len(set(snippet_keys)) == 1 else _canonical_policy_name(name)
        result.append(
            UpstreamPolicyEntry(
                name=name,
                policy_key=policy_key,
                description=description,
                compatibility=compatibility,
                section_text=section_text,
                policies_json_snippet=policies_json,
                property_descriptions=property_descriptions,
            )
        )

    return _merge_variant_entries(result)


def add_missing_linux_example_entries(
    entries: list[UpstreamPolicyEntry],
    linux_policy_examples: dict[str, Any],
) -> list[UpstreamPolicyEntry]:
    """Add policies present in the official example file but absent from legacy docs HTML."""
    existing_keys = {entry.policy_key for entry in entries}
    augmented = list(entries)

    for policy_key in linux_policy_examples:
        if policy_key in existing_keys:
            continue
        augmented.append(
            UpstreamPolicyEntry(
                name=policy_key,
                policy_key=policy_key,
                description=f"Firefox policy {policy_key}.",
                compatibility=f"Compatibility: Firefox {_min_version_for_policy_key(policy_key) or '1.0'}",
                section_text=None,
                policies_json_snippet=None,
                property_descriptions={},
            )
        )

    return _merge_variant_entries(augmented)


def _min_version_for_policy_key(policy_key: str) -> str | None:
    release_only_v151 = {
        "LocalNetworkAccess",
        "XSLTEnabled",
    }
    if policy_key in release_only_v151:
        return "151.0"
    return None


def _merge_variant_entries(entries: list[UpstreamPolicyEntry]) -> list[UpstreamPolicyEntry]:
    grouped: dict[str, list[UpstreamPolicyEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.policy_key, []).append(entry)

    merged_entries: list[UpstreamPolicyEntry] = []
    for policy_key, variants in grouped.items():
        if len(variants) == 1:
            merged_entries.append(variants[0])
            continue

        sorted_variants = sorted(
            variants,
            key=lambda item: _version_tuple(parse_min_version_from_compatibility(item.compatibility)),
        )
        primary = sorted_variants[0]
        combined_section_text = "\n\n".join(
            text for text in dict.fromkeys(item.section_text for item in variants if item.section_text)
        ) or None
        combined_snippet = "\n\nor\n\n".join(
            snippet for snippet in dict.fromkeys(item.policies_json_snippet for item in variants if item.policies_json_snippet)
        ) or None
        combined_property_descriptions: dict[str, str] = {}
        for item in variants:
            for prop_name, description in (item.property_descriptions or {}).items():
                combined_property_descriptions.setdefault(prop_name, description)

        merged_entries.append(
            UpstreamPolicyEntry(
                name=policy_key,
                policy_key=policy_key,
                description=primary.description,
                compatibility=primary.compatibility,
                section_text=combined_section_text,
                policies_json_snippet=combined_snippet,
                property_descriptions=combined_property_descriptions,
            )
        )

    return merged_entries
