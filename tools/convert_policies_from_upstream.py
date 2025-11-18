#!/usr/bin/env python
"""
Convert Mozilla policy-templates documentation to internal JSON policy schemas.

Usage (from project root):

    python tools/convert_policies_from_upstream.py

This script expects that you have already downloaded the HTML documentation
from https://mozilla.github.io/policy-templates/ and saved it to:

    data/upstream/policy-templates/policy-templates.html

It will generate two JSON schema files:

    app/schemas/policies/firefox-release-145.json
    app/schemas/policies/firefox-esr-140.json

The format of these files matches the internal PolicySchema model used by
Browser Policy Manager.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup  # type: ignore[import-untyped]

# ---- Project paths ---------------------------------------------------------------------------


BASE_DIR = Path(__file__).resolve().parents[1]
UPSTREAM_HTML_PATH = BASE_DIR / "data" / "upstream" / "policy-templates" / "policy-templates.html"

SCHEMAS_DIR = BASE_DIR / "app" / "schemas" / "policies"
RELEASE_SCHEMA_PATH = SCHEMAS_DIR / "firefox-release-145.json"
ESR_SCHEMA_PATH = SCHEMAS_DIR / "firefox-esr-140.json"


# ---- Internal data structures ---------------------------------------------------------------


@dataclass
class UpstreamPolicyEntry:
    """A single policy as extracted from the documentation site."""

    name: str  # e.g. "DisableAppUpdate"
    description: str  # short textual description from the table
    compatibility: str | None  # raw "Compatibility: ..." line
    policies_json_snippet: str | None  # the example policies.json block as plain text


@dataclass
class SchemaPolicyDefinition:
    """Representation of a policy in our internal JSON schema."""

    id: str
    type: str
    description_key: str
    categories: list[str]
    min_version: str | None
    max_version: str | None
    deprecated: bool
    enum: list[Any] | None
    items_type: str | None
    properties: dict[str, dict]
    additional_properties: bool


# ---- HTML parsing helpers -------------------------------------------------------------------


def load_html(path: Path) -> BeautifulSoup:
    """Load upstream HTML file and return a BeautifulSoup instance."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Upstream documentation file not found: {path}\n"
            "Please download https://mozilla.github.io/policy-templates/ "
            "and save it to this path."
        )

    text = path.read_text(encoding="utf-8")
    return BeautifulSoup(text, "html.parser")


def extract_policies_table(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """
    Extract the list of policies (name + short description) from the top table.

    We look for the first table whose header row contains "Policy Name" and "Description".
    """
    for table in soup.find_all("table"):
        header_cells = [th.get_text(strip=True) for th in table.find_all("th")]
        if (
            len(header_cells) >= 2
            and header_cells[0] == "Policy Name"
            and header_cells[1] == "Description"
        ):
            policies: list[tuple[str, str]] = []
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                name_link = cells[0].find("a")
                if not name_link:
                    continue
                name = name_link.get_text(strip=True)
                desc = cells[1].get_text(" ", strip=True)
                if not name:
                    continue
                policies.append((name, desc))
            return policies

    raise RuntimeError("Could not find policy table with headers 'Policy Name' and 'Description'.")


def _iter_policy_section_nodes(start_node) -> Iterable:
    """
    Yield nodes belonging to a single policy section.

    We start from the h3 that defines the policy (e.g. <h3 id="DisableAppUpdate">DisableAppUpdate</h3>)
    and iterate over its following siblings until the next h3 or h2.
    """
    current = start_node.next_sibling
    while current is not None:
        # Stop when we hit the next top-level policy heading or a new big section
        if getattr(current, "name", None) in {"h2", "h3"}:
            break
        yield current
        current = current.next_sibling


def extract_policy_details(soup: BeautifulSoup, policy_name: str) -> tuple[str | None, str | None]:
    """
    For a given policy, extract:
      - compatibility line text
      - policies.json code block text

    Returns (compatibility_line, policies_json_snippet).
    """
    # Try to locate the <h3> heading that marks the beginning of the policy section.
    header = soup.find("h3", id=policy_name)
    if header is None:
        # Fallback: search by text (exact match, stripped)
        for h3 in soup.find_all("h3"):
            if h3.get_text(strip=True) == policy_name:
                header = h3
                break

    if header is None:
        # Policy exists in the table but not in the detailed sections.
        # This should be rare but we handle it gracefully.
        return None, None

    compatibility_line: str | None = None
    policies_json_snippet: str | None = None

    for node in _iter_policy_section_nodes(header):
        # Inline text node? Skip.
        if not hasattr(node, "name"):
            continue

        # Compatibility:<...>
        if node.name == "p":
            text = node.get_text(" ", strip=True)
            if text.startswith("Compatibility:"):
                compatibility_line = text

        # policies.json block
        if node.name in {"h4", "h5"}:
            title = node.get_text(" ", strip=True)
            if "policies.json" in title:
                # Look for the next <pre> or <code> block
                code_block = node.find_next(["pre", "code"])
                if code_block is not None:
                    policies_json_snippet = code_block.get_text("\n", strip=True)

    return compatibility_line, policies_json_snippet


# ---- Type and version inference -------------------------------------------------------------


def infer_type_from_policies_json(policy_name: str, snippet: str | None) -> str:
    """
    Try to infer the type of the policy value (boolean, string, number, array, object)
    from the policies.json snippet.

    If inference fails, defaults to "object" as the most general type.
    """
    if not snippet:
        # We do not know; policies are often objects, so default to object.
        return "object"

    # Try to locate the value expression for this policy, e.g.:
    #   "DisableAppUpdate": true
    #   "AllowedDomainsForApps": "managedfirefox.com,example.com"
    #   "SanitizeOnShutdown": { ... }
    pattern = rf'"{re.escape(policy_name)}"\s*:\s*(.+)'
    match = re.search(pattern, snippet)
    if not match:
        # Some policies modify subfields or are nested; again, default to object.
        return "object"

    value_str = match.group(1).strip()

    # Cut at the first comma or newline or closing brace to isolate a single value expression.
    for sep in [",", "\n", "\r", "}"]:
        idx = value_str.find(sep)
        if idx != -1:
            value_str = value_str[:idx].strip()
            break

    # Handle cases like "true | false"
    if "|" in value_str:
        # It usually means "true | false" or "0x1 | 0x0", which is still a boolean-like toggle.
        # We'll classify such cases as boolean.
        return "boolean"

    # Remove trailing commas or semicolons if any.
    value_str = value_str.rstrip(",;")

    # Heuristic checks:
    if value_str in {"true", "false"}:
        return "boolean"

    if value_str.startswith('"') and value_str.endswith('"'):
        return "string"

    if value_str.startswith("["):
        # Could refine later, but for now treat as generic array.
        return "array"

    if value_str.startswith("{"):
        return "object"

    # Try numeric
    if re.fullmatch(r"-?\d+", value_str):
        return "integer"
    if re.fullmatch(r"-?\d+\.\d+", value_str):
        return "number"

    # Fallback
    return "object"


def parse_min_version_from_compatibility(line: str | None) -> str | None:
    """
    Parse a "Compatibility: ..." line and return a minimal Firefox version as a string.

    Examples:
        "Compatibility: Firefox 68"           -> "68.0"
        "Compatibility: Firefox 89, Firefox ESR 78.11" -> "68.0" (first Firefox version)
        "Compatibility: Firefox 124"          -> "124.0"
    """
    if not line:
        return None

    # Look for "Firefox <version>" occurrences.
    matches = re.findall(r"Firefox\s+(\d+(?:\.\d+)?)", line)
    if not matches:
        return None

    # Take the first match as the minimal version.
    version = matches[0]
    # Normalize to have at least one dot for consistency.
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
    # Fallback to object for anything unknown
    return "object"


def _try_parse_json_like(snippet: str) -> dict[str, Any] | None:
    """
    Try to parse a snippet that should contain JSON.

    The documentation usually shows full JSON, but in case of surrounding text or formatting
    we try a couple of heuristics.
    """
    snippet = snippet.strip()
    if not snippet:
        return None

    # First try direct parsing.
    try:
        return json.loads(snippet)
    except Exception:
        pass

    # Fallback: try to extract the first {...} block and parse that.
    match = re.search(r"\{.*\}", snippet, re.DOTALL)
    if not match:
        return None

    candidate = match.group(0)
    try:
        return json.loads(candidate)
    except Exception:
        return None


def _extract_policy_value_node(policy_name: str, snippet: str | None) -> Any:
    """
    Extract the raw JSON value node for a given policy from a policies.json snippet.

    Returns the Python value (bool/int/str/list/dict/...), or None if not found.
    """
    if not snippet:
        return None

    data = _try_parse_json_like(snippet)
    if not isinstance(data, dict):
        return None

    # Most examples look like: { "policies": { "PolicyName": <value> } }
    if "policies" in data and isinstance(data["policies"], dict):
        policies_obj = data["policies"]
    else:
        # In case the snippet is just the contents of the policies object itself.
        policies_obj = data

    return policies_obj.get(policy_name)


def extract_policy_properties_from_snippet(
    policy_name: str, snippet: str | None
) -> dict[str, dict]:
    """
    For an object-type policy, attempt to extract nested properties from the policies.json example.

    We try to locate the "policies" object and then the dict for the given policy_name inside it.
    Each top-level key of that dict becomes a PolicyProperty in our schema.

    For array-valued properties, we also attempt to infer:
      - items_type (type of array elements)
      - enum (set of allowed element values), when all elements are scalar and homogeneous.
    """
    if not snippet:
        return {}

    data = _try_parse_json_like(snippet)
    if not isinstance(data, dict):
        return {}

    if "policies" in data and isinstance(data["policies"], dict):
        policies_obj = data["policies"]
    else:
        policies_obj = data

    policy_value = policies_obj.get(policy_name)
    if not isinstance(policy_value, dict):
        return {}

    properties: dict[str, dict] = {}

    for prop_name, prop_value in policy_value.items():
        prop_type = infer_value_type_from_python(prop_value)
        enum: list[Any] | None = None
        items_type: str | None = None

        # Only keep "simple" defaults; complex objects/arrays as defaults are not set for now.
        default_value: Any

        if isinstance(prop_value, list) and prop_value:
            # Try to treat this as an array-of-enum or array-of-homogeneous scalars.
            scalar_elems = all(not isinstance(e, (list, dict)) for e in prop_value)
            if scalar_elems:
                elem_type = infer_value_type_from_python(prop_value[0])
                if all(infer_value_type_from_python(e) == elem_type for e in prop_value):
                    prop_type = "array"
                    items_type = elem_type

                    # Build a stable list of unique element values in order of appearance.
                    unique_vals: list[Any] = []
                    for e in prop_value:
                        if e not in unique_vals:
                            unique_vals.append(e)

                    # If the list is reasonably small, treat it as an enum of allowed values.
                    if 1 < len(unique_vals) <= 20:
                        enum = unique_vals

                default_value = prop_value
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
    """
    For a policy whose top-level value is an array, infer items_type and enum (if possible).

    We consider it an enum-array if:
      - value is a list of scalar elements (no nested lists/objects),
      - all elements are of the same type,
      - number of unique elements is small enough (<= 20).
    """
    value = _extract_policy_value_node(policy_name, snippet)
    if not isinstance(value, list) or not value:
        return None, None

    scalar_elems = all(not isinstance(e, (list, dict)) for e in value)
    if not scalar_elems:
        return None, None

    elem_type = infer_value_type_from_python(value[0])
    if not all(infer_value_type_from_python(e) == elem_type for e in value):
        return None, None

    items_type: str | None = elem_type

    unique_vals: list[Any] = []
    for e in value:
        if e not in unique_vals:
            unique_vals.append(e)

    if 1 < len(unique_vals) <= 20:
        enum: list[Any] | None = unique_vals
    else:
        enum = None

    return items_type, enum


# ---- Conversion logic -----------------------------------------------------------------------


def build_schema_policy(entry: UpstreamPolicyEntry) -> SchemaPolicyDefinition:
    """Convert an UpstreamPolicyEntry to our internal SchemaPolicyDefinition."""
    min_version = parse_min_version_from_compatibility(entry.compatibility)
    ptype = infer_type_from_policies_json(entry.name, entry.policies_json_snippet)

    properties: dict[str, dict] = {}
    additional_properties = True
    enum: list[Any] | None = None
    items_type: str | None = None

    if ptype == "object":
        # For object-type policies, try to infer nested properties from policies.json example.
        properties = extract_policy_properties_from_snippet(entry.name, entry.policies_json_snippet)
        if properties:
            # If we have an explicit list of properties, disallow arbitrary extra keys by default.
            additional_properties = False
    elif ptype == "array":
        # For array-type policies, try to infer items_type and enum at the policy level.
        items_type, enum = extract_policy_array_metadata_from_snippet(
            entry.name,
            entry.policies_json_snippet,
        )

    return SchemaPolicyDefinition(
        id=entry.name,
        type=ptype,
        description_key=f"policy.{entry.name}",
        categories=[],  # category information is not present in upstream docs
        min_version=min_version,
        max_version=None,
        deprecated=False,
        enum=enum,
        items_type=items_type,
        properties=properties,
        additional_properties=additional_properties,
    )


def schema_to_dict(
    channel: str,
    version: str,
    source: str,
    policies: list[SchemaPolicyDefinition],
) -> dict:
    """Convert a list of SchemaPolicyDefinition to the JSON-serializable schema dict."""
    return {
        "channel": channel,
        "version": version,
        "source": source,
        "policies": {
            p.id: {
                "id": p.id,
                "type": p.type,
                "description_key": p.description_key,
                "categories": p.categories,
                "min_version": p.min_version,
                "max_version": p.max_version,
                "deprecated": p.deprecated,
                "enum": p.enum,
                "items_type": p.items_type,
                "properties": p.properties,
                "additional_properties": p.additional_properties,
            }
            for p in policies
        },
    }


def convert_upstream_html_to_policies(html_path: Path) -> list[UpstreamPolicyEntry]:
    """Parse the upstream HTML and return a list of UpstreamPolicyEntry objects."""
    soup = load_html(html_path)

    table_entries = extract_policies_table(soup)
    result: list[UpstreamPolicyEntry] = []

    for name, description in table_entries:
        compatibility, policies_json = extract_policy_details(soup, name)
        result.append(
            UpstreamPolicyEntry(
                name=name,
                description=description,
                compatibility=compatibility,
                policies_json_snippet=policies_json,
            )
        )

    return result


# ---- CLI ------------------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Mozilla policy-templates documentation to internal JSON schemas."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=UPSTREAM_HTML_PATH,
        help=(
            "Path to the downloaded HTML from https://mozilla.github.io/policy-templates/ "
            f"(default: {UPSTREAM_HTML_PATH})"
        ),
    )
    parser.add_argument(
        "--release-output",
        type=Path,
        default=RELEASE_SCHEMA_PATH,
        help=f"Output path for Firefox Release schema (default: {RELEASE_SCHEMA_PATH})",
    )
    parser.add_argument(
        "--esr-output",
        type=Path,
        default=ESR_SCHEMA_PATH,
        help=f"Output path for Firefox ESR schema (default: {ESR_SCHEMA_PATH})",
    )
    parser.add_argument(
        "--release-channel",
        default="release-145",
        help="Channel string stored in the Release schema (default: release-145).",
    )
    parser.add_argument(
        "--release-version",
        default="145.0",
        help="Version string stored in the Release schema (default: 145.0).",
    )
    parser.add_argument(
        "--esr-channel",
        default="esr-140",
        help="Channel string stored in the ESR schema (default: esr-140).",
    )
    parser.add_argument(
        "--esr-version",
        default="140.5.0",
        help="Version string stored in the ESR schema (default: 140.5.0).",
    )
    parser.add_argument(
        "--source-tag",
        default="mozilla-policy-templates-v7.5",
        help=(
            "Source tag identifier stored in the schemas (default: mozilla-policy-templates-v7.5). "
            "Useful for tracking which upstream snapshot was used."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    upstream_entries = convert_upstream_html_to_policies(args.input)

    # Convert upstream entries to our internal schema representation.
    schema_policies: list[SchemaPolicyDefinition] = [
        build_schema_policy(entry) for entry in upstream_entries
    ]

    # For now, Release and ESR schemas contain the same set of policies.
    # The difference is encoded only in the channel/version fields.
    # Later we can filter policies by min_version for ESR if needed.
    release_schema = schema_to_dict(
        channel=args.release_channel,
        version=args.release_version,
        source=args.source_tag,
        policies=schema_policies,
    )

    esr_schema = schema_to_dict(
        channel=args.esr_channel,
        version=args.esr_version,
        source=args.source_tag,
        policies=schema_policies,
    )

    # Ensure output directory exists.
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    args.release_output.write_text(
        json.dumps(release_schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    args.esr_output.write_text(
        json.dumps(esr_schema, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Wrote Release schema to {args.release_output}")
    print(f"Wrote ESR schema to {args.esr_output}")


if __name__ == "__main__":
    main()
