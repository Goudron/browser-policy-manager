"""Immutable rendered-route fixtures for profile UI contracts.

The profile pages are large.  Contract tests should render a controlled route
state once, parse its DOM once, and share only an immutable semantic snapshot.
This module deliberately does not expose response bodies or BeautifulSoup
objects: callers assert user-agent-visible structure instead of repeatedly
scanning megabyte HTML strings or mutating a shared parse tree.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from tests.support import build_profile_payload, make_test_client

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PERFORMANCE_BUDGET = REPO_ROOT / "tools" / "profile_performance_budgets_0_9_4.json"

_SEMANTIC_SELECTORS = (
    "main",
    "script",
    'link[rel="stylesheet"]',
    "script[id]",
    "#library-lifecycle-filter option",
    "#compare-settings-table thead th",
    "#wizard-stepper button[aria-controls]",
    "[data-settings-mode-bar] button[data-settings-mode]",
    '[data-bpm-header-control="locale"] strong',
    "#lang option",
    '[data-clone-handoff-action="compare"]',
    "[data-compare-profile-id]",
)


def _normalise_attribute(value: Any) -> str | tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return str(value)


@dataclass(frozen=True, slots=True)
class SemanticElement:
    """Small immutable projection of an HTML element."""

    tag: str
    text: str
    attributes: tuple[tuple[str, str | tuple[str, ...]], ...]
    parent_tag: str | None
    parent_classes: tuple[str, ...]
    parent_id: str | None
    ancestor_ids: tuple[str, ...]

    def attr(self, name: str) -> str | tuple[str, ...] | None:
        return next((value for key, value in self.attributes if key == name), None)

    def has_attr(self, name: str) -> bool:
        return any(key == name for key, _value in self.attributes)


def _element_snapshot(element: Tag) -> SemanticElement:
    ancestor_ids: list[str] = []
    parent = element.parent
    immediate_parent = parent if isinstance(parent, Tag) else None
    parent_id: str | None = None
    while isinstance(parent, Tag):
        identifier = parent.get("id")
        if isinstance(identifier, str):
            ancestor_ids.append(identifier)
            if parent_id is None:
                parent_id = identifier
        parent = parent.parent
    return SemanticElement(
        tag=element.name,
        text=element.get_text(" ", strip=True),
        attributes=tuple(
            sorted(
                (str(name), _normalise_attribute(value)) for name, value in element.attrs.items()
            )
        ),
        parent_tag=immediate_parent.name if immediate_parent else None,
        parent_classes=(
            tuple(str(item) for item in immediate_parent.get("class", ()))
            if immediate_parent
            else ()
        ),
        parent_id=parent_id,
        ancestor_ids=tuple(ancestor_ids),
    )


@dataclass(frozen=True, slots=True)
class RenderedProfileRoute:
    """One response reduced to immutable, user-visible route semantics."""

    key: str
    path: str
    status_code: int
    elapsed_seconds: float
    response_bytes: int
    headers: Mapping[str, str]
    title: str
    html_attributes: tuple[tuple[str, str | tuple[str, ...]], ...]
    body_attributes: tuple[tuple[str, str | tuple[str, ...]], ...]
    elements_by_id: Mapping[str, SemanticElement]
    selected: Mapping[str, tuple[SemanticElement, ...]]
    script_paths: frozenset[str]
    stylesheet_paths: frozenset[str]
    catalog_ids: frozenset[str]

    def element(self, identifier: str) -> SemanticElement | None:
        return self.elements_by_id.get(identifier)

    def require(self, identifier: str) -> SemanticElement:
        element = self.element(identifier)
        assert element is not None, f"{self.key}: expected #{identifier}"
        return element

    def lacks(self, *identifiers: str) -> bool:
        return all(identifier not in self.elements_by_id for identifier in identifiers)

    def body_attr(self, name: str) -> str | tuple[str, ...] | None:
        return next((value for key, value in self.body_attributes if key == name), None)

    def html_attr(self, name: str) -> str | tuple[str, ...] | None:
        return next((value for key, value in self.html_attributes if key == name), None)

    def select(self, selector: str) -> tuple[SemanticElement, ...]:
        return self.selected.get(selector, ())


def _route_snapshot(
    key: str, path: str, response: Any, elapsed_seconds: float
) -> RenderedProfileRoute:
    soup = BeautifulSoup(response.text, "html.parser")
    html = soup.html
    body = soup.body
    title = soup.title.get_text(strip=True) if soup.title else ""
    elements_by_id = {
        str(element["id"]): _element_snapshot(element)
        for element in soup.select("[id]")
        if isinstance(element, Tag)
    }
    selected = {
        selector: tuple(
            _element_snapshot(element)
            for element in soup.select(selector)
            if isinstance(element, Tag)
        )
        for selector in _SEMANTIC_SELECTORS
    }

    def asset_paths(selector: str, attribute: str) -> frozenset[str]:
        return frozenset(
            urlparse(str(element.get(attribute))).path
            for element in soup.select(selector)
            if element.get(attribute)
        )

    catalog_ids = frozenset(
        str(element["id"])
        for element in soup.select("script[id]")
        if isinstance(element.get("id"), str)
    )
    return RenderedProfileRoute(
        key=key,
        path=path,
        status_code=response.status_code,
        elapsed_seconds=elapsed_seconds,
        response_bytes=len(response.content),
        headers=MappingProxyType({key.lower(): value for key, value in response.headers.items()}),
        title=title,
        html_attributes=tuple(
            sorted(
                (str(name), _normalise_attribute(value))
                for name, value in (html.attrs.items() if html else ())
            )
        ),
        body_attributes=tuple(
            sorted(
                (str(name), _normalise_attribute(value))
                for name, value in (body.attrs.items() if body else ())
            )
        ),
        elements_by_id=MappingProxyType(elements_by_id),
        selected=MappingProxyType(selected),
        script_paths=asset_paths("script[src]", "src"),
        stylesheet_paths=asset_paths('link[rel="stylesheet"]', "href"),
        catalog_ids=catalog_ids,
    )


@dataclass(frozen=True, slots=True)
class ProfileRouteSuite:
    routes: Mapping[str, RenderedProfileRoute]
    active_profile_id: int
    archived_profile_id: int
    build_seconds: float
    contract_layer_budget_seconds: float

    def route(self, key: str) -> RenderedProfileRoute:
        return self.routes[key]


def _load_contract_layer_budget() -> float:
    payload = json.loads(PROFILE_PERFORMANCE_BUDGET.read_text(encoding="utf-8"))
    return float(payload["current_guardrail"]["test_layers"]["ui_contract"]["max_wall_seconds"])


def build_profile_route_suite() -> ProfileRouteSuite:
    """Render the controlled profile route/state matrix exactly once."""

    started = perf_counter()
    snapshots: dict[str, RenderedProfileRoute] = {}
    with make_test_client() as client:
        active_response = client.post(
            "/api/profiles",
            json=build_profile_payload(
                name="Route contract profile",
                schema_version="release-153",
                flags={"DisableTelemetry": True},
            ),
        )
        assert active_response.status_code == 201
        active_profile_id = int(active_response.json()["id"])

        archived_response = client.post(
            "/api/profiles",
            json=build_profile_payload(
                name="Archived route contract profile",
                schema_version="release-153",
                flags={"DisableTelemetry": True},
            ),
        )
        assert archived_response.status_code == 201
        archived_profile_id = int(archived_response.json()["id"])
        assert client.delete(f"/api/profiles/{archived_profile_id}").status_code == 204

        route_paths = {
            "library": "/profiles",
            "compare": "/profiles/compare",
            "new": "/profiles/new",
            "edit": f"/profiles/{active_profile_id}/edit",
            "settings": f"/profiles/{active_profile_id}/settings",
            "json": f"/profiles/{active_profile_id}/json",
            "active_clone": (
                f"/profiles/new?clone_from={active_profile_id}&clone_name=Active%20copy"
            ),
            "active_duplicate": f"/profiles/{active_profile_id}/edit?duplicate=true",
            "active_settings_focus": (
                f"/profiles/{active_profile_id}/settings"
                f"?return=/profiles/{active_profile_id}/edit&focus=policy:DisableTelemetry"
            ),
            "active_json_focus": (
                f"/profiles/{active_profile_id}/json"
                f"?return=/profiles/{active_profile_id}/settings&focus=raw"
            ),
            "active_json_editor": (
                f"/profiles/{active_profile_id}/json"
                f"?return=/profiles/{active_profile_id}/edit&focus=editor"
            ),
            "missing_edit": "/profiles/999999/edit",
            "missing_settings": "/profiles/999999/settings",
            "missing_json": "/profiles/999999/json",
            "archived_hidden_edit": f"/profiles/{archived_profile_id}/edit",
            "archived_hidden_settings": f"/profiles/{archived_profile_id}/settings",
            "archived_hidden_json": f"/profiles/{archived_profile_id}/json",
            "archived_edit": f"/profiles/{archived_profile_id}/edit?include_deleted=true",
            "archived_settings": f"/profiles/{archived_profile_id}/settings?include_deleted=true",
            "archived_json": f"/profiles/{archived_profile_id}/json?include_deleted=true",
            "archived_clone": (
                f"/profiles/new?clone_from={archived_profile_id}&clone_name=Archived%20copy"
            ),
            "archived_settings_focus": (
                f"/profiles/{archived_profile_id}/settings?include_deleted=true"
                f"&return=/profiles/{archived_profile_id}/edit%3Finclude_deleted%3Dtrue"
                "&focus=policy:DisableTelemetry"
            ),
            "archived_json_raw": (
                f"/profiles/{archived_profile_id}/json?include_deleted=true"
                f"&return=/profiles/{archived_profile_id}/settings%3Finclude_deleted%3Dtrue"
                "&focus=raw"
            ),
            "archived_json_deprecated": (
                f"/profiles/{archived_profile_id}/json?include_deleted=true"
                "&focus=deprecated:LegacyPolicy"
            ),
            "archived_json_unknown": (
                f"/profiles/{archived_profile_id}/json?include_deleted=true"
                "&focus=unknown:FuturePolicy"
            ),
        }

        for key, path in route_paths.items():
            request_started = perf_counter()
            response = client.get(path)
            snapshots[key] = _route_snapshot(
                key,
                path,
                response,
                perf_counter() - request_started,
            )

        request_started = perf_counter()
        russian_response = client.get(
            "/profiles",
            headers={"Accept-Language": "ru-RU,ru;q=0.9"},
        )
        snapshots["russian_library"] = _route_snapshot(
            "russian_library",
            "/profiles",
            russian_response,
            perf_counter() - request_started,
        )

    return ProfileRouteSuite(
        routes=MappingProxyType(snapshots),
        active_profile_id=active_profile_id,
        archived_profile_id=archived_profile_id,
        build_seconds=perf_counter() - started,
        contract_layer_budget_seconds=_load_contract_layer_budget(),
    )
