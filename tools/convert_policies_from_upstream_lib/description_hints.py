from __future__ import annotations

import re
from typing import Any

from .common import UpstreamPolicyEntry


def _collect_object_property_candidates(node: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    node_type = node.get("type")

    if node_type == "object":
        candidates.append(node)
        for child in (node.get("properties") or {}).values():
            if isinstance(child, dict):
                candidates.extend(_collect_object_property_candidates(child))
        additional_properties_schema = node.get("additional_properties_schema")
        if isinstance(additional_properties_schema, dict):
            candidates.extend(_collect_object_property_candidates(additional_properties_schema))

    if node_type == "array":
        items = node.get("items")
        if isinstance(items, dict):
            candidates.extend(_collect_object_property_candidates(items))

    return candidates


def _extract_enum_clause(description: str) -> str | None:
    patterns = [
        r"Possible values are\s+(.+?)(?:\.|$)",
        r"The valid strings are\s+(.+?)(?:\.|$)",
        r"Can be either\s+(.+?)(?:\.|$)",
        r"is either\s+(.+?)(?:\.|$)",
        r"Accepts a list of one or more of:\s+(.+?)(?:\.|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _coerce_enum_token(token: str, value_type: str) -> Any:
    normalized = token.strip().strip("`\"' ")
    if value_type == "boolean" and normalized.lower() in {"true", "false"}:
        return normalized.lower() == "true"
    if value_type == "integer" and re.fullmatch(r"-?\d+", normalized):
        return int(normalized)
    if value_type == "number" and re.fullmatch(r"-?\d+(?:\.\d+)?", normalized):
        return float(normalized) if "." in normalized else int(normalized)
    return normalized


def _extract_enum_values_from_description(description: str, value_type: str) -> list[Any] | None:
    clause = _extract_enum_clause(description)
    if not clause:
        return None

    clause = clause.split(" Note:", 1)[0].split(" **Note:**", 1)[0].strip()
    quoted_tokens = re.findall(r'"([^"]+)"', clause) or re.findall(r"`([^`]+)`", clause)
    if quoted_tokens:
        raw_tokens = quoted_tokens
    else:
        cleaned_clause = re.sub(r"\([^)]*\)", "", clause)
        raw_tokens = [
            part.strip()
            for part in re.split(r",|\band\b|\bor\b", cleaned_clause)
            if part.strip()
        ]

    if len(raw_tokens) < 2:
        return None

    values: list[Any] = []
    for token in raw_tokens:
        value = _coerce_enum_token(token, value_type)
        if value not in values:
            values.append(value)

    return values if len(values) >= 2 else None


def _extract_numeric_bounds_from_description(description: str, value_type: str) -> dict[str, int | float]:
    if value_type not in {"integer", "number"}:
        return {}

    bounds: dict[str, int | float] = {}
    number_pattern = r"-?\d+(?:\.\d+)?"

    def _coerce(value: str) -> int | float:
        if value_type == "integer":
            return int(float(value))
        return float(value)

    patterns: list[tuple[str, str | tuple[str, str]]] = [
        (rf"\bbetween\s+({number_pattern})\s+and\s+({number_pattern})\b", ("minimum", "maximum")),
        (rf"\bfrom\s+({number_pattern})\s+to\s+({number_pattern})\b", ("minimum", "maximum")),
        (rf"\bat least\s+({number_pattern})\b", "minimum"),
        (rf"\bat most\s+({number_pattern})\b", "maximum"),
        (rf"\bminimum of\s+({number_pattern})\b", "minimum"),
        (rf"\bmaximum of\s+({number_pattern})\b", "maximum"),
    ]

    for pattern, target in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if not match:
            continue
        if isinstance(target, tuple):
            bounds[target[0]] = _coerce(match.group(1))
            bounds[target[1]] = _coerce(match.group(2))
        else:
            bounds[target] = _coerce(match.group(1))

    return bounds


def _infer_property_schema_from_description(description: str) -> dict[str, Any] | None:
    lowered = description.lower()

    if "boolean" in lowered:
        return {"type": "boolean"}

    if re.search(r"\b(integer|int)\b", lowered):
        schema: dict[str, Any] = {"type": "integer"}
        if enum_values := _extract_enum_values_from_description(description, "integer"):
            schema["enum"] = enum_values
        return schema

    if re.search(r"\bnumber\b", lowered):
        schema = {"type": "number"}
        if enum_values := _extract_enum_values_from_description(description, "number"):
            schema["enum"] = enum_values
        return schema

    if any(phrase in lowered for phrase in ("list of", "array of", "accepts a list", "an array")):
        items_schema: dict[str, Any] = {"type": "string"}
        if enum_values := _extract_enum_values_from_description(description, "string"):
            items_schema["enum"] = enum_values
        return {
            "type": "array",
            "items": items_schema,
        }

    if any(phrase in lowered for phrase in ("maps to a string", "string that", "string indicating", "a string", "the url", "url from")):
        schema = {"type": "string"}
        if enum_values := _extract_enum_values_from_description(description, "string"):
            schema["enum"] = enum_values
        return schema

    return None


def _candidate_overlap_score(candidate: dict[str, Any], property_names: set[str]) -> int:
    candidate_properties = set((candidate.get("properties") or {}).keys())
    return len(candidate_properties & property_names)


def _find_target_candidate_for_property(
    node: dict[str, Any],
    property_name: str,
    known_property_names: set[str],
) -> dict[str, Any] | None:
    candidates = _collect_object_property_candidates(node)
    if not candidates:
        return None

    direct_matches = [candidate for candidate in candidates if property_name in (candidate.get("properties") or {})]
    if len(direct_matches) == 1:
        return direct_matches[0]
    if len(direct_matches) > 1:
        return max(direct_matches, key=lambda candidate: _candidate_overlap_score(candidate, known_property_names))

    scored_candidates = [
        (candidate, _candidate_overlap_score(candidate, known_property_names))
        for candidate in candidates
    ]
    scored_candidates = [(candidate, score) for candidate, score in scored_candidates if score > 0]
    if not scored_candidates:
        return None

    return max(scored_candidates, key=lambda item: item[1])[0]


def _apply_property_description_hints(entry: UpstreamPolicyEntry, node: dict[str, Any]) -> None:
    property_descriptions = entry.property_descriptions or {}
    if not property_descriptions:
        return

    known_property_names = set(property_descriptions)
    for property_name, description in property_descriptions.items():
        target = _find_target_candidate_for_property(node, property_name, known_property_names)
        if target is None:
            continue

        properties = target.setdefault("properties", {})
        prop_schema = properties.get(property_name)
        if not isinstance(prop_schema, dict):
            inferred_schema = _infer_property_schema_from_description(description)
            if inferred_schema is None:
                continue
            properties[property_name] = inferred_schema
            prop_schema = inferred_schema

        prop_type = prop_schema.get("type")
        if prop_type == "string":
            if enum_values := _extract_enum_values_from_description(description, "string"):
                prop_schema["enum"] = enum_values
        elif prop_type == "integer":
            if enum_values := _extract_enum_values_from_description(description, "integer"):
                prop_schema["enum"] = enum_values
            prop_schema.update(_extract_numeric_bounds_from_description(description, "integer"))
        elif prop_type == "number":
            if enum_values := _extract_enum_values_from_description(description, "number"):
                prop_schema["enum"] = enum_values
            prop_schema.update(_extract_numeric_bounds_from_description(description, "number"))
        elif prop_type == "array":
            items = prop_schema.setdefault("items", {"type": "string"})
            item_type = items.get("type") if isinstance(items, dict) else None
            if isinstance(items, dict) and item_type in {"string", "integer", "number"}:
                if enum_values := _extract_enum_values_from_description(description, item_type):
                    items["enum"] = enum_values
                if item_type in {"integer", "number"}:
                    items.update(_extract_numeric_bounds_from_description(description, item_type))


def _extract_required_property_names(section_text: str | None, node: dict[str, Any]) -> set[str]:
    if not section_text:
        return set()

    property_names = {
        prop_name
        for candidate in _collect_object_property_candidates(node)
        for prop_name in (candidate.get("properties") or {})
    }
    if not property_names:
        return set()

    required_names: set[str] = set()
    sentences = re.split(r"(?<=[.!?])\s+", section_text)

    for prop_name in property_names:
        if re.search(rf"\b{re.escape(prop_name)}\b.*\(\s*Required\s*\)", section_text):
            required_names.add(prop_name)

    for sentence in sentences:
        lowered = sentence.lower()
        if "required" not in lowered:
            continue
        if " are required" not in lowered and " is required" not in lowered:
            continue
        present = {
            prop_name
            for prop_name in property_names
            if re.search(rf"\b{re.escape(prop_name)}\b", sentence)
        }
        if present:
            required_names.update(present)

    return required_names


def _apply_required_property_hints(section_text: str | None, node: dict[str, Any]) -> None:
    required_names = _extract_required_property_names(section_text, node)
    if not required_names:
        return

    candidates = [
        candidate
        for candidate in _collect_object_property_candidates(node)
        if required_names.issubset(set((candidate.get("properties") or {}).keys()))
    ]
    if len(candidates) != 1:
        return

    target = candidates[0]
    for prop_name in required_names:
        target["properties"][prop_name]["required"] = True
