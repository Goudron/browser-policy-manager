from __future__ import annotations

import re

from app.main import create_app
from tests.docs_index import doc_path_from_index

API_ROW_RE = re.compile(
    r"^\| `(?P<operation>API-[A-Z]+-[0-9]{3})` \| `(?P<method>GET|POST|PATCH|DELETE)` "
    r"\| `(?P<path>[^`]+)` \| .* \| `(?P<topic>(?:api|admin)-[a-z0-9-]+)` \|$"
)
WEB_ROW_RE = re.compile(
    r"^\| `(?P<operation>WEB-[0-9]{3})` \| `(?P<method>GET)` "
    r"\| `(?P<path>[^`]+)` \| .* \|$"
)


def _inventory() -> str:
    return doc_path_from_index(
        "architecture/api-documentation-inventory-0.9.0.md",
        status="active",
    ).read_text(encoding="utf-8")


def _openapi_operations() -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    integration: set[tuple[str, str]] = set()
    web: set[tuple[str, str]] = set()
    for path, path_item in create_app().openapi()["paths"].items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags", [])
            if "documentation-assistant" in tags:
                continue
            target = web if "web" in tags else integration
            target.add((method.upper(), path))
    return integration, web


def test_api_documentation_inventory_matches_openapi_operations():
    inventory = _inventory()
    api_rows = [
        match.groupdict()
        for line in inventory.splitlines()
        if (match := API_ROW_RE.match(line))
    ]
    web_rows = [
        match.groupdict()
        for line in inventory.splitlines()
        if (match := WEB_ROW_RE.match(line))
    ]
    integration_openapi, web_openapi = _openapi_operations()

    assert len(api_rows) == 15
    assert len({row["operation"] for row in api_rows}) == 15
    assert len({row["topic"] for row in api_rows}) == 6
    assert {(row["method"], row["path"]) for row in api_rows} == integration_openapi

    assert len(web_rows) == 6
    assert len({row["operation"] for row in web_rows}) == 6
    assert {(row["method"], row["path"]) for row in web_rows} == web_openapi


def test_api_documentation_inventory_covers_models_errors_and_parameters():
    inventory = _inventory()

    for model in (
        "ProfileCreate",
        "ProfileUpdate",
        "ProfileRead",
        "FirefoxPoliciesJsonImportRequest",
        "ValidationRequest",
        "Canonical Firefox export",
        "Error response",
    ):
        assert f"| `{model}` |" in inventory or f"| {model} |" in inventory

    for status in ("200", "201", "204", "400", "404", "409", "415", "422", "503"):
        assert f"| `{status}` |" in inventory

    for parameter in (
        "q",
        "schema_version",
        "validation_state",
        "lifecycle",
        "include_deleted",
        "limit",
        "offset",
        "sort",
        "order",
        "download",
        "indent",
        "pretty",
    ):
        assert f"| `{parameter}` |" in inventory


def test_api_documentation_inventory_records_exclusions_and_limitations():
    inventory = _inventory()

    for surface in (
        "/openapi.json",
        "/docs",
        "/redoc",
        "/i18n/{locale}.json",
        "/favicon.ico",
        "_list_profiles_core",
    ):
        assert f"`{surface}`" in inventory

    for limitation in (
        "There is no authentication or authorization layer",
        "There is no API version prefix",
        "There is no rate limiting",
        "Only PATCH supports optimistic concurrency",
        "There is no bulk profile CRUD/export endpoint",
        "Error bodies are not a single stable envelope",
        "does not promise transactional workflows",
    ):
        assert limitation in inventory

    assert "multipart OpenAPI schema declares only `file`" in inventory
    assert "all new examples use full `policies.json`" in inventory
