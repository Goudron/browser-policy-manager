#!/usr/bin/env python3
"""Verify the checked-in manifest, checksums, source maps, and route boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"
BUNDLE_DIR = STATIC_ROOT / "profiles_bundles"
MANIFEST = BUNDLE_DIR / "profiles-bundles-manifest.json"
EXPECTED_ROUTES = {"library", "compare", "new", "edit", "settings", "json"}
SHARED_STYLES = ["/static/vendor/profiles_tailwind.css", "/static/profiles.css"]
MONACO = {"/static/vendor/profiles_monaco.js", "/static/vendor/profiles_monaco.css"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _static_path(public_path: str) -> Path | None:
    if not public_path.startswith("/static/") or ".." in Path(public_path).parts:
        return None
    return STATIC_ROOT / public_path.removeprefix("/static/")


def _route_bundle_bytes(manifest: dict[str, Any], route: str) -> int | None:
    """Return one route's transitive native-module payload, excluding Monaco."""

    try:
        metafile = json.loads(
            (BUNDLE_DIR / "profiles-bundles-metafile.json").read_text(encoding="utf-8")
        )
        entry_path = next(
            script.removeprefix("/static/profiles_bundles/")
            for script in manifest["routes"][route]["scripts"]
            if script.startswith("/static/profiles_bundles/")
        )
    except (KeyError, OSError, StopIteration, json.JSONDecodeError):  # fmt: skip
        return None
    outputs = {item["path"]: item for item in metafile.get("outputs", []) if "path" in item}
    pending = [entry_path]
    visited: set[str] = set()
    total = 0
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        details = outputs.get(path)
        if not isinstance(details, dict):
            return None
        visited.add(path)
        total += int(details.get("bytes", 0))
        pending.extend(
            item["path"]
            for item in details.get("imports", [])
            if not item.get("external") and isinstance(item.get("path"), str)
        )
    return total


def check() -> list[str]:
    errors: list[str] = []
    try:
        manifest: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read profile bundle manifest: {error}"]

    if manifest.get("schema_version") != 1:
        errors.append("unsupported profile bundle manifest schema")
    if set(manifest.get("routes", {})) != EXPECTED_ROUTES:
        errors.append("profile bundle manifest must declare each supported route exactly once")
    if manifest.get("head_script") != "/static/profiles_head_bootstrap.js":
        errors.append("profile bundle manifest must retain the ordered head bootstrap")
    if not manifest.get("license_strategy"):
        errors.append("profile bundle manifest is missing its license strategy")

    locked_assets = manifest.get("generated_assets", [])
    locked_paths = {item.get("path") for item in locked_assets if isinstance(item, dict)}
    actual_paths = {
        path.name for path in BUNDLE_DIR.iterdir() if path.is_file() and path.name != MANIFEST.name
    }
    if locked_paths != actual_paths:
        errors.append("profile bundle manifest assets do not match generated output")
    for item in locked_assets:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("profile bundle manifest contains an invalid asset record")
            continue
        path = BUNDLE_DIR / item["path"]
        if not path.is_file():
            errors.append(f"missing generated profile asset {item['path']}")
            continue
        if item.get("size") != path.stat().st_size:
            errors.append(f"profile bundle size mismatch: {item['path']}")
        if item.get("sha256") != _sha256(path):
            errors.append(f"profile bundle checksum mismatch: {item['path']}")

    budgets = manifest.get("bundle_budgets", {})
    generated_bytes = sum(path.stat().st_size for path in BUNDLE_DIR.iterdir() if path.is_file())
    generated_javascript_bytes = sum(path.stat().st_size for path in BUNDLE_DIR.glob("*.js"))
    if generated_bytes > budgets.get("max_generated_bytes", -1):
        errors.append("generated profile bundle byte budget exceeded")
    if generated_javascript_bytes > budgets.get("max_generated_javascript_bytes", -1):
        errors.append("generated profile bundle JavaScript byte budget exceeded")

    for script in sorted(path for path in BUNDLE_DIR.glob("*.js")):
        source_map = script.with_suffix(f"{script.suffix}.map")
        if not source_map.is_file():
            errors.append(f"missing source map for {script.name}")
        if f"sourceMappingURL={source_map.name}" not in script.read_text(encoding="utf-8"):
            errors.append(f"source map link missing from {script.name}")

    routes = manifest.get("routes", {})
    for route in EXPECTED_ROUTES:
        details = routes.get(route, {})
        scripts = details.get("scripts", []) if isinstance(details, dict) else []
        styles = details.get("styles", []) if isinstance(details, dict) else []
        if not isinstance(scripts, list) or not isinstance(styles, list):
            errors.append(f"{route}: route assets must be lists")
            continue
        expected_styles = (
            SHARED_STYLES
            if route != "json"
            else [
                SHARED_STYLES[0],
                "/static/vendor/profiles_monaco.css",
                SHARED_STYLES[1],
            ]
        )
        if styles != expected_styles:
            errors.append(f"{route}: stylesheet order or ownership drifted")
        has_monaco = "/static/vendor/profiles_monaco.js" in scripts
        if has_monaco != (route == "json"):
            errors.append(f"{route}: Monaco must be loaded only by the JSON route")
        route_bytes = _route_bundle_bytes(manifest, route)
        if route_bytes is None or route_bytes > budgets.get("route_max_javascript_bytes", {}).get(
            route, -1
        ):
            errors.append(f"{route}: transitive route bundle byte budget exceeded")
        for public_path in [*scripts, *styles]:
            static_path = _static_path(public_path) if isinstance(public_path, str) else None
            if static_path is None or not static_path.is_file():
                errors.append(f"{route}: missing or unsafe static asset {public_path!r}")
    if any("js-yaml" in str(item) for item in routes.values()):
        errors.append("removed YAML editor assets must not return through the bundle manifest")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("profile frontend bundles: FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(
        "profile frontend bundles: manifest, checksums, source maps, and route boundaries are valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
