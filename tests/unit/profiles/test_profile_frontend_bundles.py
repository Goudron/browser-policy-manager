from __future__ import annotations

import json
from pathlib import Path

from tools import build_profile_frontend_bundles as bundles
from tools import verify_profile_frontend_bundles as verifier

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "app" / "static" / "profiles_bundles" / "profiles-bundles-manifest.json"


def test_profile_bundle_manifest_and_checksums_are_valid():
    assert verifier.check() == []


def test_profile_bundle_output_is_reproducible_without_rewriting_checked_in_assets():
    assert bundles.main(["--check"]) == 0


def test_profile_bundle_build_replaces_stale_generated_output(tmp_path: Path):
    output = tmp_path / "profiles_bundles"
    output.mkdir()
    (output / "obsolete-bundle.js").write_text("stale", encoding="utf-8")

    bundles._clean(output)

    assert output.is_dir()
    assert list(output.iterdir()) == []


def test_profile_bundle_manifest_keeps_route_entries_short_and_monaco_json_only():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    routes = manifest["routes"]

    assert set(routes) == {"library", "compare", "new", "edit", "settings", "json"}
    assert routes["new"]["scripts"] == routes["edit"]["scripts"]
    assert all(len(routes[route]["scripts"]) == 1 for route in routes if route != "json")
    assert routes["json"]["scripts"] == [
        "/static/vendor/profiles_monaco.js",
        "/static/profiles_bundles/profile-json.js",
    ]
    assert all(
        "/static/vendor/profiles_monaco.js" not in routes[route]["scripts"]
        for route in routes
        if route != "json"
    )
    assert manifest["license_strategy"]["third_party"].endswith("required notices.")
    assert manifest["bundle_budgets"] == {
        "max_generated_bytes": 1_211_000,
        "max_generated_javascript_bytes": 600_000,
        "route_max_javascript_bytes": {
            "library": 60_000,
            "compare": 60_000,
            "new": 600_000,
            "edit": 600_000,
            "settings": 600_000,
            "json": 600_000,
        },
    }


def test_profile_bundle_outputs_are_packaged_and_the_template_uses_runtime_manifest():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    template = (ROOT / "app" / "templates" / "profiles" / "_page_route_assets.html").read_text(
        encoding="utf-8"
    )

    assert '"static/profiles_bundles/*"' in pyproject
    assert "profiles_frontend_assets.routes[profiles_route_mode]" in template
    assert 'type="module"' in template
    assert "route_assets.scripts" in template
    assert "profiles_utils.js" not in template
