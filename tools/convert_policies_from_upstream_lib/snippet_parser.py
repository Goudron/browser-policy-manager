from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .common import ENUM_WRAPPER_KEY
from .html_parser import _canonical_policy_name


def infer_type_from_policies_json(policy_name: str, snippet: str | None) -> str:
    """Infer policy type from an upstream policies.json example."""
    if not snippet:
        return "object"

    pattern = rf'"{re.escape(policy_name)}"\s*:\s*(.+)'
    match = re.search(pattern, snippet)
    if not match:
        return "object"

    value_str = match.group(1).strip()
    for sep in [",", "\n", "\r", "}"]:
        idx = value_str.find(sep)
        if idx != -1:
            value_str = value_str[:idx].strip()
            break

    if "|" in value_str:
        return "boolean"

    value_str = value_str.rstrip(",;")
    if value_str in {"true", "false"}:
        return "boolean"
    if value_str.startswith('"') and value_str.endswith('"'):
        return "string"
    if value_str.startswith("["):
        return "array"
    if value_str.startswith("{"):
        return "object"
    if re.fullmatch(r"-?\d+", value_str):
        return "integer"
    if re.fullmatch(r"-?\d+\.\d+", value_str):
        return "number"
    return "object"


def parse_min_version_from_compatibility(line: str | None) -> str | None:
    """Extract the first Firefox version from a Compatibility line."""
    if not line:
        return None

    matches = re.findall(r"Firefox\s+(\d+(?:\.\d+)?)", line)
    if not matches:
        return None

    version = matches[0]
    if "." not in version:
        version = f"{version}.0"
    return version


def infer_value_type_from_python(value: Any) -> str:
    """Infer internal policy value type from a Python value loaded from JSON."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "object"


def _replace_string_unions(snippet: str) -> str:
    pattern = re.compile(r'"(?:[^"\\]|\\.)*"(?:\s*\|\s*"(?:[^"\\]|\\.)*")+')

    def _replace(match: re.Match[str]) -> str:
        values = [json.loads(token) for token in re.findall(r'"(?:[^"\\]|\\.)*"', match.group(0))]
        return json.dumps({ENUM_WRAPPER_KEY: values}, ensure_ascii=False)

    return pattern.sub(_replace, snippet)


def _replace_primitive_unions(snippet: str) -> str:
    pattern = re.compile(r"(?:true|false|-?\d+(?:\.\d+)?)(?:\s*\|\s*(?:true|false|-?\d+(?:\.\d+)?))+")

    def _replace(match: re.Match[str]) -> str:
        values = [json.loads(token.strip()) for token in match.group(0).split("|")]
        return json.dumps({ENUM_WRAPPER_KEY: values}, ensure_ascii=False)

    return pattern.sub(_replace, snippet)


def _escape_non_json_backslashes(snippet: str) -> str:
    return re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", snippet)


def _strip_trailing_commas(snippet: str) -> str:
    previous = None
    current = snippet
    while previous != current:
        previous = current
        current = re.sub(r",(\s*[}\]])", r"\1", current)
    return current


def _prepare_json_like_snippet(snippet: str) -> str:
    sanitized = snippet.strip()
    sanitized = _replace_string_unions(sanitized)
    sanitized = _replace_primitive_unions(sanitized)
    sanitized = _escape_non_json_backslashes(sanitized)
    sanitized = _strip_trailing_commas(sanitized)
    return sanitized


def _split_json_object_candidates(snippet: str) -> list[str]:
    candidates: list[str] = []
    start: int | None = None
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(snippet):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                start = index
            depth += 1
            continue

        if char == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start is not None:
                candidates.append(snippet[start : index + 1])
                start = None

    return candidates


def _try_parse_json_like(snippet: str) -> dict[str, Any] | None:
    """Try to parse a JSON-like snippet with a couple of cleanup heuristics."""
    snippet = snippet.strip()
    if not snippet:
        return None

    sanitized = _prepare_json_like_snippet(snippet)
    try:
        return json.loads(sanitized)
    except Exception:
        pass

    match = re.search(r"\{.*\}", sanitized, re.DOTALL)
    if not match:
        return None

    candidate = match.group(0)
    try:
        return json.loads(candidate)
    except Exception:
        return None


def _candidate_policy_keys(policy_name: str) -> list[str]:
    candidates = [policy_name, _canonical_policy_name(policy_name)]
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _extract_policy_value_nodes(policy_name: str, snippet: str | None) -> list[Any]:
    if not snippet:
        return []

    values: list[Any] = []
    object_candidates = _split_json_object_candidates(snippet)
    for candidate in object_candidates or [snippet]:
        data = _try_parse_json_like(candidate)
        if not isinstance(data, dict):
            continue

        policies_obj = data["policies"] if "policies" in data and isinstance(data["policies"], dict) else data
        for candidate_key in _candidate_policy_keys(policy_name):
            if candidate_key in policies_obj:
                values.append(policies_obj[candidate_key])
                break

    return values


def _extract_policy_keys_from_snippet(snippet: str | None) -> list[str]:
    if not snippet:
        return []

    keys: list[str] = []
    for candidate in _split_json_object_candidates(snippet) or [snippet]:
        data = _try_parse_json_like(candidate)
        if not isinstance(data, dict):
            continue
        policies_obj = data.get("policies")
        if not isinstance(policies_obj, dict):
            continue
        for key in policies_obj:
            if key not in keys:
                keys.append(key)
    return keys


def _extract_policy_value_node(policy_name: str, snippet: str | None) -> Any:
    """Extract the first raw JSON value node for a given policy from a snippet."""
    values = _extract_policy_value_nodes(policy_name, snippet)
    return values[0] if values else None


def load_linux_policy_examples(path: Path) -> dict[str, Any]:
    """Load the official Linux example policies file and return the policies mapping."""
    if not path.is_file():
        return {}

    data = _try_parse_json_like(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}

    policies = data.get("policies")
    if not isinstance(policies, dict):
        return {}

    return policies
