from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from bs4 import BeautifulSoup  # type: ignore[import-untyped]


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


def _iter_policy_section_nodes(start_node, policy_name: str) -> Iterable:
    """
    Yield nodes belonging to a single policy section.

    We start from the h3 that defines the policy and iterate until the next h3 or h2.
    """
    normalized_policy_name = _normalize_policy_heading_text(policy_name)
    current = start_node.next_sibling
    while current is not None:
        current_name = getattr(current, "name", None)
        if current_name == "h2":
            break
        if current_name == "h3":
            current_heading = _normalize_policy_heading_text(current.get_text(" ", strip=True))
            if not (
                current_heading == normalized_policy_name
                or current_heading.startswith(f"{normalized_policy_name} | ")
                or current_heading.startswith(f"{normalized_policy_name} -> ")
            ):
                break
        yield current
        current = current.next_sibling


def _normalize_policy_heading_text(text: str) -> str:
    """Normalize policy headings from the upstream docs for resilient matching."""
    normalized = re.sub(r"\s+", " ", text.strip())
    normalized = re.sub(r"\s*\([^)]*\)$", "", normalized)
    return normalized.casefold()


def _canonical_policy_name(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name.strip())
    collapsed = re.sub(r"\s*\([^)]*\)$", "", collapsed)
    return collapsed.replace(" ", "")


def _policy_heading_id_candidates(policy_name: str) -> list[str]:
    normalized = policy_name.strip()
    candidates = [
        normalized,
        normalized.casefold(),
        f"{normalized.casefold()}-deprecated",
    ]

    slug = normalized.casefold()
    slug = slug.replace(" | ", "--").replace(" -> ", "--")
    slug = re.sub(r"\s*\(([^)]*)\)$", r"-\1", slug)
    slug = re.sub(r"[^a-z0-9-]+", "", slug.replace(" ", "-"))
    candidates.append(slug)

    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def extract_policy_details(
    soup: BeautifulSoup,
    policy_name: str,
) -> tuple[str | None, str | None, str | None, dict[str, str]]:
    """
    For a given policy, extract compatibility text, section prose, example snippet, and field docs.
    """
    header = None
    for candidate_id in _policy_heading_id_candidates(policy_name):
        header = soup.find("h3", id=candidate_id)
        if header is not None:
            break

    if header is None:
        normalized_policy_name = _normalize_policy_heading_text(policy_name)
        for h3 in soup.find_all("h3"):
            if _normalize_policy_heading_text(h3.get_text(" ", strip=True)) == normalized_policy_name:
                header = h3
                break

    if header is None:
        return None, None, None, {}

    compatibility_line: str | None = None
    policies_json_snippet: str | None = None
    text_chunks: list[str] = []
    property_descriptions: dict[str, str] = {}

    for node in _iter_policy_section_nodes(header, policy_name):
        if not hasattr(node, "name"):
            continue

        node_text = node.get_text(" ", strip=True)
        if node_text:
            text_chunks.append(node_text)

        if node.name == "p" and node_text.startswith("Compatibility:"):
            compatibility_line = node_text

        if node.name in {"h4", "h5"}:
            title = node.get_text(" ", strip=True)
            if "policies.json" in title:
                code_block = node.find_next(["pre", "code"])
                if code_block is not None:
                    policies_json_snippet = code_block.get_text("\n", strip=True)

        if node.name == "table":
            for row in node.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                name_cell, description_cell = cells[0], cells[1]
                code_names = [
                    code.get_text(" ", strip=True)
                    for code in name_cell.find_all("code")
                    if code.get_text(" ", strip=True)
                ]
                property_name = (
                    code_names[0] if code_names else name_cell.get_text(" ", strip=True)
                ).replace("\xa0", " ").strip()
                property_name = property_name.strip("`\"' ")
                description_text = description_cell.get_text(" ", strip=True)
                if property_name and description_text and property_name not in property_descriptions:
                    property_descriptions[property_name] = description_text

    section_text = "\n".join(text_chunks) if text_chunks else None
    return compatibility_line, section_text, policies_json_snippet, property_descriptions
