"""Semantic contracts for the complete profile-route state matrix.

The module-scoped fixture performs the expensive work once.  Each response is
parsed once into an immutable projection, so the assertions below describe DOM
and navigation semantics without megabyte response-string scans.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

import pytest

from tests.profile_route_contracts import ProfileRouteSuite, build_profile_route_suite


@pytest.fixture(scope="module")
def profile_routes() -> ProfileRouteSuite:
    return build_profile_route_suite()


@dataclass(frozen=True, slots=True)
class RouteExpectation:
    title: str
    mode: str
    template: str
    required_ids: tuple[str, ...]
    forbidden_ids: tuple[str, ...]


def test_profile_route_matrix_preserves_every_canonical_shell(profile_routes: ProfileRouteSuite):
    profile_id = profile_routes.active_profile_id
    expectations = {
        "library": RouteExpectation(
            "Library — Browser Policy Manager",
            "library",
            "library",
            (
                "library-panel",
                "search",
                "library-schema-filter",
                "library-lifecycle-filter",
                "library-validation-filter",
                "sort",
                "order",
                "create-profile-link",
                "compare-profiles-link",
                "import-firefox-policies",
                "import-firefox-policies-file",
                "status",
                "list",
            ),
            ("wizard-panel", "settings-panel", "editor-panel", "compare-panel"),
        ),
        "compare": RouteExpectation(
            "Compare profile settings — Browser Policy Manager",
            "compare",
            "compare",
            (
                "compare-page",
                "compare-page-title",
                "compare-left-search",
                "compare-right-search",
                "compare-left-results",
                "compare-right-results",
                "compare-left-profile",
                "compare-right-profile",
                "compare-settings-table",
                "compare-preferences-catalog",
            ),
            ("library-panel", "wizard-panel", "settings-panel", "editor-panel"),
        ),
        "new": RouteExpectation(
            "New profile draft — Guided editor — Browser Policy Manager",
            "new",
            "editor",
            (
                "wizard-panel",
                "wizard-schema",
                "wizard-starter-catalog",
                "wizard-settings-search-input",
                "editor-mode-settings",
                "editor-mode-json",
                "save",
                "validate",
            ),
            ("library-panel", "settings-panel", "editor-panel", "editor", "format"),
        ),
        "edit": RouteExpectation(
            "Route contract profile — Guided editor — Browser Policy Manager",
            "edit",
            "editor",
            (
                "overview-panel",
                "current-name",
                "profile-state-badge",
                "wizard-panel",
                "wizard-schema",
                "editor-mode-settings",
                "editor-mode-json",
                "save",
                "validate",
            ),
            ("library-panel", "settings-panel", "editor-panel", "editor", "format"),
        ),
        "settings": RouteExpectation(
            "Route contract profile — All settings — Browser Policy Manager",
            "settings",
            "settings",
            (
                "overview-panel",
                "settings-panel",
                "all-settings-review-panel",
                "all-settings-list-panel",
                "all-settings-list",
                "all-settings-detail-panel",
                "all-settings-catalog-advanced",
                "wizard-settings-search-input",
                "editor-mode-guided",
                "editor-mode-json",
                "save",
                "validate",
            ),
            ("library-panel", "wizard-panel", "editor-panel", "editor", "format"),
        ),
        "json": RouteExpectation(
            "Route contract profile — JSON editor — Browser Policy Manager",
            "json",
            "json",
            (
                "overview-panel",
                "editor-mode-guided",
                "editor-mode-settings",
                "editor-panel",
                "editor",
                "save",
                "validate",
                "format",
                "download-firefox-policies",
                "status",
            ),
            ("library-panel", "wizard-panel", "settings-panel", "details-panel"),
        ),
    }

    for key, expected in expectations.items():
        route = profile_routes.route(key)
        assert route.status_code == 200
        assert route.title == expected.title
        assert route.body_attr("data-profiles-route-mode") == expected.mode
        assert route.body_attr("data-profiles-template-kind") == expected.template
        assert all(route.element(identifier) for identifier in expected.required_ids)
        assert route.lacks(*expected.forbidden_ids)

    for key in ("edit", "settings", "json"):
        assert profile_routes.route(key).body_attr("data-editing-profile-id") == str(profile_id)
    assert profile_routes.route("library").body_attr("data-editing-profile-id") is None
    assert profile_routes.route("new").body_attr("data-editing-profile-id") is None

    for key in ("missing_edit", "missing_settings", "missing_json"):
        assert profile_routes.route(key).status_code == 404


def test_profile_route_components_are_accessible_and_owned_by_the_right_shell(
    profile_routes: ProfileRouteSuite,
):
    library = profile_routes.route("library")
    assert library.select("main")
    assert library.require("create-profile-link").attr("href") == "/profiles/new"
    assert library.require("create-profile-link").attr("target") == "_blank"
    assert library.require("create-profile-link").attr("rel") == ("noopener",)
    assert library.require("compare-profiles-link").attr("href") == "/profiles/compare"
    assert library.require("import-firefox-policies").attr("aria-describedby") == (
        "import-firefox-policies-status"
    )
    assert library.require("import-firefox-policies-file").attr("accept") == (
        ".json,application/json"
    )
    assert library.require("status").attr("aria-live") == "polite"
    assert {item.attr("value") for item in library.select("#library-lifecycle-filter option")} == {
        "active",
        "archived",
        "all",
    }
    assert not library.select("[data-compare-profile-id]")

    compare = profile_routes.route("compare")
    assert compare.require("compare-page").attr("aria-labelledby") == "compare-page-title"
    for side in ("left", "right"):
        search = compare.require(f"compare-{side}-search")
        results = compare.require(f"compare-{side}-results")
        assert search.attr("type") == "search"
        assert search.attr("data-compare-search") == side
        assert results.attr("role") == "listbox"
    assert [
        header.attr("scope") for header in compare.select("#compare-settings-table thead th")
    ] == ["col", "col", "col"]

    guided = profile_routes.route("new")
    steps = guided.select("#wizard-stepper button[aria-controls]")
    assert len(steps) == 6
    assert steps[0].attr("aria-current") == "step"
    assert guided.require("wizard-settings-search-input").attr("type") == "search"
    assert guided.require("editor-mode-settings").attr("aria-disabled") == "true"
    assert guided.require("editor-mode-json").attr("aria-disabled") == "true"
    for step in range(1, 7):
        panel = guided.require(f"wizard-step-{step}")
        assert panel.parent_tag == "div"
        assert "wizard-panels" in panel.parent_classes
        assert panel.parent_id == "wizard-panel"
    step_owners = {
        1: ("wizard-name", "wizard-schema", "wizard-starter-grid"),
        2: ("wizard-step-2-basics", "wizard-step-2-proxy", "wizard-step-2-review"),
        3: ("wizard-hardening-presets", "wizard-cleanup-presets"),
        4: ("wizard-step-4-accounts", "wizard-step-4-extensions"),
        5: ("wizard-ai-posture-presets", "wizard-ai-policy-controls"),
        6: ("wizard-export-ready-card", "wizard-export-summary-ai"),
    }
    for step, identifiers in step_owners.items():
        for identifier in identifiers:
            assert f"wizard-step-{step}" in guided.require(identifier).ancestor_ids
        other_prefixes = tuple(f"wizard-step-{other}-" for other in range(1, 7) if other != step)
        leaking = [
            identifier
            for identifier, element in guided.elements_by_id.items()
            if identifier.startswith(other_prefixes)
            and f"wizard-step-{step}" in element.ancestor_ids
        ]
        assert leaking == []

    settings = profile_routes.route("settings")
    mode_buttons = settings.select("[data-settings-mode-bar] button[data-settings-mode]")
    assert [item.attr("data-settings-mode") for item in mode_buttons] == [
        "review",
        "configured",
        "catalog",
    ]
    assert [item.attr("aria-pressed") for item in mode_buttons] == [
        "true",
        "false",
        "false",
    ]
    assert settings.require("all-settings-list").attr("role") == "rowgroup"

    json_page = profile_routes.route("json")
    assert "editor-panel" in json_page.require("editor").ancestor_ids
    assert json_page.require("download-firefox-policies").attr("target") == "_blank"
    assert json_page.require("download-firefox-policies").attr("rel") == ("noopener",)


def test_profile_route_assets_catalogs_and_security_follow_route_tables(
    profile_routes: ProfileRouteSuite,
):
    canonical = {
        "library": "/static/profiles_bundles/profile-library.js",
        "compare": "/static/profiles_bundles/profile-compare.js",
        "new": "/static/profiles_bundles/profile-guided.js",
        "settings": "/static/profiles_bundles/profile-settings.js",
        "json": "/static/profiles_bundles/profile-json.js",
    }
    expected_catalogs = {
        "library": {"schema-channels-catalog"},
        "compare": {"schema-channels-catalog"},
        "new": {
            "wizard-starter-catalog",
            "wizard-settings-catalog",
            "wizard-preferences-catalog",
            "wizard-manual-policy-controls",
            "wizard-schema-shell-catalog",
            "schema-channels-catalog",
        },
        "settings": {
            "wizard-settings-catalog",
            "wizard-preferences-catalog",
            "wizard-schema-shell-catalog",
            "all-settings-category-catalog",
            "schema-channels-catalog",
            "all-settings-row-help-links",
            "all-settings-row-help-status",
        },
        "json": {"wizard-schema-shell-catalog", "schema-channels-catalog"},
    }
    known_catalogs = frozenset().union(*expected_catalogs.values())

    for key, route_bundle in canonical.items():
        route = profile_routes.route(key)
        csp = route.headers["content-security-policy"]
        assert "script-src 'self'" in csp
        assert "'unsafe-eval'" not in csp
        assert "worker-src 'self'" in csp
        assert route_bundle in route.script_paths
        assert "/static/profiles.css" in route.stylesheet_paths
        assert "/static/vendor/profiles_tailwind.css" in route.stylesheet_paths
        assert route.catalog_ids & known_catalogs == expected_catalogs[key]
        for script in route.select("script"):
            if script.attr("type") == "application/json":
                continue
            source = script.attr("src")
            assert isinstance(source, str) and source.startswith("/static/")
            assert script.text == ""
        for stylesheet in route.select('link[rel="stylesheet"]'):
            href = stylesheet.attr("href")
            assert isinstance(href, str) and href.startswith("/static/")

    assert "/static/vendor/profiles_monaco.js" in profile_routes.route("json").script_paths
    for key in ("new", "settings"):
        assert "/static/vendor/profiles_monaco.js" not in profile_routes.route(key).script_paths


def test_profile_route_variants_are_observable_isolated_and_within_budget(
    profile_routes: ProfileRouteSuite,
):
    active_id = profile_routes.active_profile_id
    archived_id = profile_routes.archived_profile_id

    clone = profile_routes.route("active_clone")
    assert clone.body_attr("data-clone-source-id") == str(active_id)
    assert clone.body_attr("data-clone-name") == "Active copy"
    assert profile_routes.route("active_duplicate").body_attr("data-clone-source-id") == str(
        active_id
    )

    settings_focus = profile_routes.route("active_settings_focus")
    advanced = settings_focus.require("all-settings-catalog-advanced")
    assert advanced.attr("data-settings-focus-open") == "true"
    assert not advanced.has_attr("hidden")
    assert not settings_focus.require("settings-schema-shell-step-5-details").has_attr("hidden")
    assert not settings_focus.require("settings-advanced-schema-privacy-security-details").has_attr(
        "hidden"
    )
    assert profile_routes.route("active_json_focus").body_attr("data-json-focus-target") == "raw"
    json_editor = profile_routes.route("active_json_editor")
    assert json_editor.body_attr("data-json-focus-target") == "editor"
    assert json_editor.body_attr("data-json-return-url") == f"/profiles/{active_id}/edit"

    for key in ("archived_hidden_edit", "archived_hidden_settings", "archived_hidden_json"):
        assert profile_routes.route(key).status_code == 404
    for key in ("archived_edit", "archived_settings", "archived_json"):
        route = profile_routes.route(key)
        assert route.status_code == 200
        assert route.body_attr("data-include-deleted") == "true"
        assert route.body_attr("data-editing-profile-id") == str(archived_id)
        assert route.require("profile-state-badge").text == "Deleted"

    archived_clone = profile_routes.route("archived_clone")
    assert archived_clone.body_attr("data-clone-source-id") == str(archived_id)
    assert archived_clone.body_attr("data-clone-name") == "Archived copy"
    archived_settings = profile_routes.route("archived_settings_focus")
    assert archived_settings.body_attr("data-json-return-url") == (
        f"/profiles/{archived_id}/edit?include_deleted=true"
    )
    assert (
        archived_settings.require("all-settings-catalog-advanced").attr("data-settings-focus-open")
        == "true"
    )
    focus_expectations = {
        "archived_json_raw": "raw",
        "archived_json_deprecated": "deprecated:LegacyPolicy",
        "archived_json_unknown": "unknown:FuturePolicy",
    }
    for key, focus in focus_expectations.items():
        route = profile_routes.route(key)
        assert route.body_attr("data-include-deleted") == "true"
        assert route.body_attr("data-json-focus-target") == focus

    russian = profile_routes.route("russian_library")
    assert russian.html_attr("lang") == "ru"
    assert russian.select('[data-bpm-header-control="locale"] strong')[0].text == "Локаль"
    assert russian.require("status").text == "Библиотека готова."
    assert {item.attr("value") for item in russian.select("#lang option")} >= {
        "system",
        "en",
        "ru",
        "de",
        "es-ES",
        "fr",
        "zh-CN",
    }

    with pytest.raises(TypeError):
        profile_routes.routes["leak"] = russian  # type: ignore[index]
    with pytest.raises(TypeError):
        russian.elements_by_id["leak"] = russian.require("status")  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        russian.require("status").text = "mutated"  # type: ignore[misc]
    assert profile_routes.route("russian_library").require("status").text == ("Библиотека готова.")

    assert profile_routes.build_seconds <= profile_routes.contract_layer_budget_seconds
