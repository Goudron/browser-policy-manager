#!/usr/bin/env python3
"""Check the bounded profile frontend graph without inspecting vendor output."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "frontend_profile_graph_0_9_5.json"
STATIC = ROOT / "app" / "static"
TEMPLATE = ROOT / "app" / "templates" / "profiles" / "_page_route_assets.html"


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    active: set[str] = set()
    complete: set[str] = set()

    def visit(node: str) -> bool:
        if node in complete:
            return False
        if node in active:
            return True
        active.add(node)
        cyclic = any(dependency in graph and visit(dependency) for dependency in graph[node])
        active.remove(node)
        complete.add(node)
        return cyclic

    return any(visit(node) for node in graph)


def check() -> list[str]:
    graph = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors: list[str] = []
    groups = graph["route_groups"]
    files = [item for group in groups.values() for item in group]
    actual = sorted(path.name for path in STATIC.glob("profiles*.js"))
    if sorted(files) != actual or len(files) != len(set(files)):
        errors.append("owned profile JS files must appear once in the route groups")
    pure_module_sources = graph.get("pure_module_sources", [])
    actual_pure_modules = sorted(
        str(path.relative_to(STATIC)) for path in (STATIC / "profiles_modules").glob("*.mjs")
    )
    if sorted(pure_module_sources) != actual_pure_modules:
        errors.append("pure profile module sources differ from the manifest")
    if not graph.get("pure_module_bridge"):
        errors.append("pure profile modules require an explicit classic-script bridge")
    layers = graph["styles"]["source_layers"]
    actual_layers = sorted(
        str(path.relative_to(STATIC)) for path in (STATIC / "profiles_css").glob("*.css")
    )
    if sorted(layers) != actual_layers:
        errors.append("owned CSS layers differ from the manifest")
    template = TEMPLATE.read_text(encoding="utf-8")
    if "profiles_frontend_assets.routes[profiles_route_mode]" not in template:
        errors.append("route template must use the generated profile bundle manifest")
    if 'type="module"' not in template:
        errors.append("route template must load profile route entries as native modules")
    bundle_boundary = graph.get("bundle_boundary", {})
    for field in (
        "entries",
        "manifest",
        "metafile",
        "build",
        "verify",
        "source_maps",
        "size_budget",
    ):
        if not bundle_boundary.get(field):
            errors.append(f"profile bundle boundary is missing {field}")
    for bundle_path in bundle_boundary.get("entries", {}).values():
        if not (ROOT / bundle_path).is_file():
            errors.append(f"missing declared profile route entry {bundle_path}")
    known = set(groups) | set(graph["vendor_boundaries"])
    for layer, dependencies in graph["dependency_layers"].items():
        unknown = set(dependencies) - known
        if unknown:
            errors.append(f"{layer} has unknown dependencies: {sorted(unknown)!r}")
    if _has_cycle(graph["dependency_layers"]):
        errors.append("profile dependency layers must be acyclic")
    for boundary in graph["vendor_boundaries"].values():
        for file in boundary["files"]:
            if not (ROOT / file).exists():
                errors.append(f"missing declared vendor boundary {file}")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("frontend profile graph: FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    graph = json.loads(MANIFEST.read_text(encoding="utf-8"))
    count = sum(len(group) for group in graph["route_groups"].values())
    print(
        f"frontend profile graph: OK ({count} owned JS modules, {len(graph['styles']['source_layers'])} CSS layers)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
