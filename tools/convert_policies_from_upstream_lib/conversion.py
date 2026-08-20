from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
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

    example_values.extend(
        _extract_policy_value_nodes(entry.policy_key, entry.policies_json_snippet)
    )

    if example_values:
        inferred_nodes = [
            infer_schema_from_example_value(example_value) for example_value in example_values
        ]
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
    schema_metadata: Mapping[str, Any] | None = None,
) -> dict:
    """Convert a list of SchemaPolicyDefinition to a raw JSON Schema bundle."""
    title_channel = str(channel or "Firefox").replace("-", " ").title()
    title = f"{title_channel} Policies"
    if version:
        title = f"{title} {version}"

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        "type": "object",
        "additionalProperties": False,
        "x-bpm-channel": channel,
        "x-bpm-version": version,
        "x-bpm-source": source,
        "properties": {p.id: _policy_definition_to_json_schema(p) for p in policies},
    }
    if schema_metadata is not None:
        schema.update(
            {
                "x-bpm-artifact-id": schema_metadata["artifact_id"],
                "x-bpm-line-id": schema_metadata["line_id"],
                "x-bpm-firefox-line": schema_metadata["firefox_line"],
                "x-bpm-firefox-version": schema_metadata["firefox_version"],
                "x-bpm-ui-label": schema_metadata["ui_label"],
                "x-bpm-source-provenance": schema_metadata["source_provenance"],
                "x-bpm-generator": schema_metadata["generator"],
            }
        )
    return schema


def _version_at_least(version: str, minimum: str) -> bool:
    return _version_tuple(version) >= _version_tuple(minimum)


def apply_documented_schema_overrides(
    schema: dict,
    target_version: str,
    *,
    target_channel: str | None = None,
) -> dict:
    """Fill documented upstream gaps that the retired policy-template Markdown omits.

    Mozilla's v8.0 release package points policy syntax to Firefox Administrator Reference. Its
    bundled Markdown omits several ExtensionSettings fields documented for Firefox 153 at
    https://firefox-admin-docs.mozilla.org/reference/policies/extensionsettings/ . Keep this bridge
    deliberately narrow and version-gated until the upstream package publishes the complete
    structure again.
    """
    extension_settings = schema.get("properties", {}).get("ExtensionSettings")
    if isinstance(extension_settings, dict):
        additional = extension_settings.setdefault(
            "additionalProperties",
            {"type": "object", "properties": {}, "additionalProperties": False},
        )
        if isinstance(additional, dict):
            properties = additional.setdefault("properties", {})
            if isinstance(properties, dict):
                base_properties = {
                    "default_area": {"type": "string", "enum": ["navbar", "menupanel"]},
                    "private_browsing": {"type": "boolean"},
                    "restricted_domains": {"type": "array", "items": {"type": "string"}},
                    "temporarily_allow_weak_signatures": {"type": "boolean"},
                }
                for name, definition in base_properties.items():
                    properties.setdefault(name, definition)

                installation_mode = properties.setdefault("installation_mode", {"type": "string"})
                if isinstance(installation_mode, dict):
                    installation_mode["enum"] = [
                        "allowed",
                        "blocked",
                        "force_installed",
                        "normal_installed",
                    ]

                allowed_types = properties.setdefault(
                    "allowed_types", {"type": "array", "items": {"type": "string"}}
                )
                if isinstance(allowed_types, dict):
                    allowed_type_items = allowed_types.setdefault("items", {"type": "string"})
                    if isinstance(allowed_type_items, dict):
                        allowed_type_items["enum"] = [
                            "extension",
                            "theme",
                            "dictionary",
                            "locale",
                            "sitepermission",
                        ]

                if _version_at_least(target_version, "153.0"):
                    firefox_153_properties = {
                        "allowed_permissions": {"type": "array", "items": {"type": "string"}},
                        "blocked_permissions": {"type": "array", "items": {"type": "string"}},
                        "runtime_allowed_hosts": {"type": "array", "items": {"type": "string"}},
                        "runtime_blocked_hosts": {"type": "array", "items": {"type": "string"}},
                    }
                    for name, definition in firefox_153_properties.items():
                        properties.setdefault(name, definition)

    _remove_unsupported_sanitize_exceptions(schema, target_version, target_channel)

    return schema


def _version_tuple(value: str | None) -> tuple[int, ...]:
    if not value:
        return ()
    return tuple(int(part) for part in value.split(".") if part.isdigit())


# Mozilla's policy-template Markdown is no longer complete after the documentation
# moved to Firefox Administrator Reference.  These declarations bridge only the
# entries present in master/linux-policies.json but missing compatibility metadata.
# A policy's release and ESR availability must be kept independent: a numerically
# newer ESR does not imply support for a release-only policy.
_MASTER_POLICY_CHANNEL_MINIMUMS: dict[str, dict[str, str | None]] = {
    "CNSA2KeyAgreementEnabled": {"release": "154.0", "esr": None},
    "DefaultBrowserSettingEnabled": {"release": "154.0", "esr": "153.0"},
    "SitePolicies": {"release": "150.0", "esr": None},
}


def _target_channel_family(target_channel: str | None) -> str | None:
    if target_channel is None:
        return None
    if target_channel.startswith("release-"):
        return "release"
    if target_channel.startswith("esr-"):
        return "esr"
    raise ValueError(f"Unknown Firefox schema channel family: {target_channel}")


def _remove_unsupported_sanitize_exceptions(
    schema: dict,
    target_version: str,
    target_channel: str | None,
) -> None:
    """Omit the Firefox-154 release-only nested field from older bundle shapes."""
    family = _target_channel_family(target_channel)
    if family is None or (family == "release" and _version_at_least(target_version, "154.0")):
        return

    sanitize = schema.get("properties", {}).get("SanitizeOnShutdown")
    if not isinstance(sanitize, dict):
        return
    branches = sanitize.get("oneOf")
    if not isinstance(branches, list):
        return

    retained: list[dict[str, Any]] = []
    fingerprints: set[str] = set()
    for branch in branches:
        if not isinstance(branch, dict):
            continue
        properties = branch.get("properties")
        if isinstance(properties, dict):
            properties.pop("Exceptions", None)
        fingerprint = json.dumps(branch, sort_keys=True, separators=(",", ":"))
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            retained.append(branch)
    sanitize["oneOf"] = retained


def filter_policies_for_target_version(
    policies: list[SchemaPolicyDefinition],
    target_version: str,
    *,
    target_channel: str | None = None,
) -> list[SchemaPolicyDefinition]:
    """Keep only policies available by the target Firefox version and family."""
    target = _version_tuple(target_version)
    if not target:
        return list(policies)

    family = _target_channel_family(target_channel)
    selected: list[SchemaPolicyDefinition] = []
    for policy in policies:
        compatibility = _MASTER_POLICY_CHANNEL_MINIMUMS.get(policy.id)
        if compatibility is not None and family is not None:
            minimum = compatibility[family]
            if minimum is None or not _version_at_least(target_version, minimum):
                continue
            selected.append(replace(policy, min_version=minimum))
            continue
        if not policy.min_version or _version_tuple(policy.min_version) <= target:
            selected.append(policy)
    return selected


def convert_upstream_html_to_policies(html_path) -> list[UpstreamPolicyEntry]:
    """Parse the upstream HTML and return a list of UpstreamPolicyEntry objects."""
    soup = load_html(html_path)
    table_entries = extract_policies_table(soup)
    result: list[UpstreamPolicyEntry] = []

    for name, description in table_entries:
        compatibility, section_text, policies_json, property_descriptions = extract_policy_details(
            soup, name
        )
        snippet_keys = _extract_policy_keys_from_snippet(policies_json)
        policy_key = (
            snippet_keys[0] if len(set(snippet_keys)) == 1 else _canonical_policy_name(name)
        )
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


def _markdown_plain_text(value: str) -> str:
    normalized = value.replace("\\", "").strip()
    normalized = re.sub(r"`([^`]*)`", r"\1", normalized)
    normalized = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", normalized)
    return re.sub(r"[*_]+", "", normalized).strip()


def _markdown_policy_property_descriptions(lines: list[str]) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for line in lines:
        if not line.startswith("|") or line.count("|") < 3:
            continue
        cells = [_markdown_plain_text(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0] or set(cells[0]) == {"-"}:
            continue
        if cells[0].casefold() in {"name", "key", "property", "setting"}:
            continue
        if cells[1] and cells[0] not in descriptions:
            descriptions[cells[0].strip("`\"' ")] = cells[1]
    return descriptions


def _markdown_policies_json_snippet(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if not line.casefold().startswith("#### policies.json"):
            continue
        for start in range(index + 1, len(lines)):
            if lines[start].strip().startswith("```"):
                end = next(
                    (
                        candidate
                        for candidate in range(start + 1, len(lines))
                        if lines[candidate].strip().startswith("```")
                    ),
                    None,
                )
                if end is not None:
                    return "\n".join(lines[start + 1 : end]).strip() or None
                return None
            if lines[start].startswith("### "):
                break
    return None


def convert_upstream_markdown_to_policies(markdown_path: Path) -> list[UpstreamPolicyEntry]:
    """Parse the official policy-template Markdown published with current Mozilla releases."""
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    section_indexes = [
        index
        for index, line in enumerate(lines)
        if line.startswith("### ") and not line.startswith("#### ")
    ]
    result: list[UpstreamPolicyEntry] = []

    for position, start in enumerate(section_indexes):
        end = section_indexes[position + 1] if position + 1 < len(section_indexes) else len(lines)
        heading = lines[start].removeprefix("### ").strip()
        section_lines = lines[start + 1 : end]
        compatibility = next(
            (
                _markdown_plain_text(line)
                for line in section_lines
                if line.startswith("**Compatibility:**")
            ),
            None,
        )
        snippet = _markdown_policies_json_snippet(section_lines)
        snippet_keys = _extract_policy_keys_from_snippet(snippet)
        base_heading = heading.split(" | ", maxsplit=1)[0]
        policy_key = (
            snippet_keys[0] if len(set(snippet_keys)) == 1 else _canonical_policy_name(base_heading)
        )
        description = next(
            (
                _markdown_plain_text(line)
                for line in section_lines
                if line.strip() and not line.startswith(("**Compatibility:**", "####", "```", "|"))
            ),
            f"Firefox policy {policy_key}.",
        )
        result.append(
            UpstreamPolicyEntry(
                name=heading,
                policy_key=policy_key,
                description=description,
                compatibility=compatibility,
                section_text="\n".join(section_lines) or None,
                policies_json_snippet=snippet,
                property_descriptions=_markdown_policy_property_descriptions(section_lines),
            )
        )

    if not result:
        raise RuntimeError(f"Could not find Markdown policy sections in {markdown_path}")
    return _merge_variant_entries(result)


def convert_upstream_document_to_policies(document_path: Path) -> list[UpstreamPolicyEntry]:
    """Parse the supported upstream documentation format selected by its source extension."""
    if document_path.suffix.casefold() in {".md", ".markdown"}:
        return convert_upstream_markdown_to_policies(document_path)
    return convert_upstream_html_to_policies(document_path)


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
    if policy_key == "DisableRemoteSettingsAndAcceptSecurityConsequences":
        return "153.0"
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
            key=lambda item: _version_tuple(
                parse_min_version_from_compatibility(item.compatibility)
            ),
        )
        primary = sorted_variants[0]
        combined_section_text = (
            "\n\n".join(
                text
                for text in dict.fromkeys(
                    item.section_text for item in variants if item.section_text
                )
            )
            or None
        )
        combined_snippet = (
            "\n\nor\n\n".join(
                snippet
                for snippet in dict.fromkeys(
                    item.policies_json_snippet for item in variants if item.policies_json_snippet
                )
            )
            or None
        )
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
