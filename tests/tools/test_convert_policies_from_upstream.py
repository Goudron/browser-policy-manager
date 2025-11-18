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
        return "object"

    # Try to locate the value expression for this policy, e.g.:
    #   "DisableAppUpdate": true
    #   "AllowedDomainsForApps": "managedfirefox.com,example.com"
    #   "SanitizeOnShutdown": { ... }
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


def _try_parse_json_like(snippet: str) -> dict[str, Any] | None:
    snippet = snippet.strip()
    if not snippet:
        return None

    try:
        return json.loads(snippet)
    except Exception:
        pass

    match = re.search(r"\{.*\}", snippet, re.DOTALL)
    if not match:
        return None

    candidate = match.group(0)
    try:
        return json.loads(candidate)
    except Exception:
        return None


def extract_policy_properties_from_snippet(
    policy_name: str, snippet: str | None
) -> dict[str, dict]:
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
        prop_type = infer_type_from_policies_json(policy_name, snippet)
        enum: list[Any] | None = None
        items_type: str | None = None

        if isinstance(prop_value, list) and prop_value:
            scalar_elems = all(not isinstance(e, (list, dict)) for e in prop_value)
            if scalar_elems:
                elem_type = infer_type_from_policies_json(policy_name, snippet)
                if all(infer_type_from_policies_json(e, snippet) == elem_type for e in prop_value):
                    prop_type = "array"
                    items_type = elem_type

                    unique_vals: list[Any] = []
                    for e in prop_value:
                        if e not in unique_vals:
                            unique_vals.append(e)

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
