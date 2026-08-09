from __future__ import annotations

import json

from tools.check_frontend_profile_graph import MANIFEST, check


def test_frontend_profile_graph_is_complete():
    assert check() == []


def test_frontend_profile_graph_keeps_route_and_conversion_boundaries_explicit():
    graph = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert graph["routes"]["library"] == ["shared", "library"]
    assert graph["routes"]["json"][-1] == "vendor-monaco"
    assert graph["vendor_boundaries"]["vendor-monaco"]["route"] == "json"
    assert graph["bundle_boundary"]["build"] == "make build-profile-frontend-bundles"
    assert graph["bundle_boundary"]["verify"] == "make check-profile-frontend-bundles"
    assert set(graph["bundle_boundary"]["entries"]) == {
        "library",
        "compare",
        "guided_edit",
        "settings",
        "json",
    }
    assert graph["pure_module_sources"] == sorted(graph["pure_module_sources"])
    assert "route entries import their direct consumers" in graph["pure_module_bridge"]
    assert any("catch-all coordinator" in item for item in graph["future_constraints"])
    assert len(graph["m6_stages"]) == 6


def test_frontend_profile_graph_keeps_component_css_in_cascade_order():
    graph = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert graph["styles"]["source_layers"] == [
        "profiles_css/00-foundation.css",
        "profiles_css/10-library.css",
        "profiles_css/20-shell.css",
        "profiles_css/21-settings.css",
        "profiles_css/22-guided-wizard.css",
        "profiles_css/23-workspace-editor.css",
        "profiles_css/24-theme-overrides.css",
        "profiles_css/30-responsive.css",
        "profiles_css/40-compact-shell.css",
    ]
