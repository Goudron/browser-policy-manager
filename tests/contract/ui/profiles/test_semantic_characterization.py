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
            "Create profile — Browser Policy Manager",
            "new",
            "preparation",
            (
                "profile-preparation",
                "profile-preparation-title",
                "profile-preparation-catalog",
            ),
            (
                "library-panel",
                "overview-panel",
                "wizard-panel",
                "settings-panel",
                "editor-panel",
                "editor",
                "format",
                "save",
                "validate",
                "wizard-starter-catalog",
                "profiles-initial-profile",
            ),
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
                "profile-schema-fact",
                "profile-starter-fact",
                "profile-cis-fact",
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

    preparation = profile_routes.route("new")
    assert preparation.require("profile-preparation").attr("aria-labelledby") == (
        "profile-preparation-title"
    )
    assert preparation.body_attr("data-preparation-mode") == "create"
    assert preparation.body_attr("data-preparation-terminal-action-mode") == "create"
    assert preparation.body_attr("data-preparation-source-state") == "absent"
    assert "profile-preparation-catalog" in preparation.catalog_ids

    preparation_form = preparation.require("profile-preparation-form")
    assert preparation_form.tag == "form"
    assert preparation_form.attr("data-preparation-form-state") == "ready"
    assert preparation_form.attr("novalidate") == ""
    for field_id, error_id in (
        ("profile-preparation-name", "profile-preparation-name-error"),
        ("profile-preparation-schema", "profile-preparation-schema-error"),
        ("profile-preparation-starter", "profile-preparation-starter-error"),
        ("profile-preparation-cis", "profile-preparation-cis-error"),
    ):
        control = preparation.require(field_id)
        assert control.attr("required") == ""
        assert control.attr("aria-describedby") == error_id
        assert control.attr("aria-errormessage") == error_id
        assert preparation.require(error_id).attr("role") == "alert"
    assert preparation.require("profile-preparation-state").attr("role") == "status"
    assert preparation.require("profile-preparation-state").attr("aria-live") == "polite"
    assert (
        preparation.require("profile-preparation-submit").attr("data-preparation-terminal-action")
        == "create"
    )

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
        "new": "/static/profiles_bundles/profile-preparation.js",
        "settings": "/static/profiles_bundles/profile-settings.js",
        "json": "/static/profiles_bundles/profile-json.js",
    }
    expected_catalogs = {
        "library": {"schema-channels-catalog"},
        "compare": {"schema-channels-catalog"},
        "new": {"profile-preparation-catalog"},
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
    assert clone.body_attr("data-preparation-mode") == "duplicate"
    assert clone.body_attr("data-preparation-terminal-action-mode") == "duplicate"
    assert clone.body_attr("data-preparation-source-state") == "available"
    assert clone.body_attr("data-preparation-source-id") == str(active_id)
    assert clone.body_attr("data-preparation-source-revision") == "1"
    assert clone.body_attr("data-clone-name") is None
    assert profile_routes.route("active_duplicate").body_attr("data-clone-source-id") is None

    for key, source_state in (("invalid_clone", "invalid"), ("missing_clone", "not-found")):
        route = profile_routes.route(key)
        assert route.body_attr("data-preparation-mode") == "duplicate"
        assert route.body_attr("data-preparation-terminal-action-mode") == "unavailable"
        assert route.body_attr("data-preparation-source-state") == source_state
        assert (
            route.require("profile-preparation-source-error").attr("data-preparation-source-state")
            == source_state
        )
    assert profile_routes.profile_count_after_routes == profile_routes.profile_count_before_routes

    settings_focus = profile_routes.route("active_settings_focus")
    advanced = settings_focus.require("all-settings-catalog-advanced")
    assert advanced.attr("data-settings-focus-open") == "true"
    assert not advanced.has_attr("hidden")
    assert not settings_focus.require("settings-schema-shell-step-3-details").has_attr("hidden")
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
    assert archived_clone.body_attr("data-preparation-mode") == "duplicate"
    assert archived_clone.body_attr("data-preparation-terminal-action-mode") == "unavailable"
    assert archived_clone.body_attr("data-preparation-source-state") == "archived"
    unavailable_action = archived_clone.require("profile-preparation-submit")
    assert unavailable_action.attr("disabled") == ""
    assert "profile-preparation-source-error" in unavailable_action.attr("aria-describedby")
    assert unavailable_action.attr("data-preparation-terminal-action") == "unavailable"
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
