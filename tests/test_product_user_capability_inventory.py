from __future__ import annotations

import re

from tests.docs_index import doc_path_from_index

CAPABILITY_ROW_RE = re.compile(
    r"^\| `(?P<capability>CAP-[A-Z]+-[0-9]{3})` \| .* \| `(?P<topic>ug-[a-z0-9-]+)` \| "
    r"(?P<topic_type>task|concept|reference|troubleshooting) \|$"
)


def _inventory() -> str:
    return doc_path_from_index(
        "architecture/product-user-capability-inventory-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")


def test_user_capability_inventory_has_unique_capabilities_and_dita_topics():
    inventory = _inventory()
    rows = [
        match.groupdict()
        for line in inventory.splitlines()
        if (match := CAPABILITY_ROW_RE.match(line))
    ]

    assert len(rows) == 106
    capability_ids = [row["capability"] for row in rows]
    assert len(capability_ids) == len(set(capability_ids))
    assert len({row["topic"] for row in rows}) == 89
    assert {row["topic_type"] for row in rows} == {
        "task",
        "concept",
        "reference",
        "troubleshooting",
    }


def test_user_capability_inventory_closes_readme_and_product_surfaces():
    inventory = _inventory()

    for heading in (
        "Global Shell And Cross-Surface Capabilities",
        "Profile Library Capabilities",
        "Profile Comparison Capabilities",
        "Guided Editor Capabilities",
        "All Settings Capabilities",
        "JSON Editor Capabilities",
        "Firefox Boundary, Schema, And CIS User Workflows",
        "Troubleshooting And Recovery Capabilities",
        "README Main-Capability Closure Matrix",
        "Route And State Closure",
    ):
        assert f"## {heading}" in inventory

    for readme_capability in (
        "Database-backed Firefox policy profile library",
        "Create, edit, duplicate, archive, restore, permanently delete, import, and export workflows",
        "Named clone drafts",
        "Dedicated saved-profile comparison",
        "Firefox Enterprise `policies.json` import and export",
        "Version-aware validation against bundled schemas",
        "Guided editor for common scenarios",
        "Dedicated AI and smart browser features step",
        "Schema-aware ESR/Release behavior",
        "Triage-first All Settings",
        "JSON editor backed by local Monaco",
        "CIS assets, starter presets, generated layers, and merge logic",
        "English source UI with six runtime locales",
    ):
        assert f"| {readme_capability} |" in inventory

    for route in (
        "/profiles",
        "/profiles/compare",
        "/profiles/new",
        "/profiles/{id}/edit",
        "/profiles/{id}/settings",
        "/profiles/{id}/json",
    ):
        assert f"| `{route}` |" in inventory


def test_user_capability_inventory_records_scope_boundaries():
    inventory = _inventory()

    for backlog_item in ("BPM090-M2-02", "BPM090-M2-03", "BPM090-M2-04"):
        assert f"`{backlog_item}`" in inventory
    assert "Administrator/distribution documentation remains explicitly deferred." in inventory
    assert "every README `Main Capabilities` bullet" in inventory
