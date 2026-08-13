#!/usr/bin/env python3
"""Build deterministic route-specific /profiles JavaScript bundles.

The input files are owned ESM modules with direct dependency edges. Only the
five route entries are emitted into HTML; shared chunks are resolved by native
ESM imports. Monaco deliberately remains its separately verified JSON-only
vendor boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = REPO_ROOT / "app" / "static"
SOURCE_ROOT = REPO_ROOT / "app" / "static_src"
ENTRY_ROOT = SOURCE_ROOT / "profile_bundle_entries"
OUTPUT_DIR = STATIC_ROOT / "profiles_bundles"
VERIFY_DIR = STATIC_ROOT / "profiles_bundles.check"
ESBUILD = REPO_ROOT / "node_modules" / ".bin" / ("esbuild.cmd" if os.name == "nt" else "esbuild")
PACKAGE_LOCK = REPO_ROOT / "package-lock.json"
MANIFEST_NAME = "profiles-bundles-manifest.json"
METAFILE_NAME = "profiles-bundles-metafile.json"

ENTRIES = {
    "library": ENTRY_ROOT / "library.js",
    "compare": ENTRY_ROOT / "compare.js",
    "guided": ENTRY_ROOT / "guided.js",
    "settings": ENTRY_ROOT / "settings.js",
    "json": ENTRY_ROOT / "json.js",
}
ROUTE_ENTRIES = {
    "library": "profile-library.js",
    "compare": "profile-compare.js",
    "new": "profile-guided.js",
    "edit": "profile-guided.js",
    "settings": "profile-settings.js",
    "json": "profile-json.js",
}
SHARED_STYLES = (
    "/static/vendor/profiles_tailwind.css",
    "/static/profiles.css",
)
HEAD_SCRIPT = "/static/profiles_head_bootstrap.js"
MONACO_ASSETS = (
    "/static/vendor/profiles_monaco.css",
    "/static/vendor/profiles_monaco.js",
)
BUNDLE_BUDGETS = {
    # The shared conversion review is carried by the three editor routes and
    # its checksum-locked source maps. Keep the cap tight while admitting the
    # reviewed M5 UI state machine rather than silently disabling a guard.
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normal_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _ensure_esbuild() -> None:
    if not ESBUILD.is_file() or not ESBUILD.stat().st_mode & 0o111:
        raise RuntimeError(
            f"Missing pinned esbuild at {ESBUILD.relative_to(REPO_ROOT)}; run npm ci first."
        )
    package_lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    expected = package_lock["packages"]["node_modules/esbuild"]["version"]
    resolved = json.loads(
        (REPO_ROOT / "node_modules" / "esbuild" / "package.json").read_text(encoding="utf-8")
    )["version"]
    if resolved != expected:
        raise RuntimeError(f"esbuild version {resolved} does not match locked {expected}")


def _clean(directory: Path) -> None:
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def _build_esbuild_output(directory: Path) -> dict[str, Any]:
    _clean(directory)
    raw_metafile = directory / ".esbuild-metafile.json"
    command = [
        str(ESBUILD),
        *(str(path) for path in ENTRIES.values()),
        "--bundle",
        "--format=esm",
        "--splitting",
        "--minify",
        "--platform=browser",
        "--target=es2020",
        f"--outdir={directory}",
        "--entry-names=profile-[name]",
        f"--outbase={ENTRY_ROOT}",
        "--chunk-names=chunk-[hash]",
        "--sourcemap=linked",
        "--sources-content=false",
        f"--metafile={raw_metafile}",
        "--log-level=warning",
    ]
    print("Building route entries with pinned esbuild:", " ".join(command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)
    raw = json.loads(raw_metafile.read_text(encoding="utf-8"))
    raw_metafile.unlink()
    return raw


def _relative_entrypoint(value: str) -> str:
    path = Path(value)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return value


def _write_canonical_metafile(directory: Path, raw: dict[str, Any]) -> dict[str, Any]:
    outputs = []
    for raw_path, details in sorted(raw["outputs"].items()):
        path = Path(raw_path)
        try:
            output_path = str(path.relative_to(directory))
        except ValueError:
            output_path = path.name
        outputs.append(
            {
                "bytes": details["bytes"],
                "entry_point": (
                    _relative_entrypoint(details["entryPoint"]) if "entryPoint" in details else None
                ),
                "imports": [
                    {"external": bool(item.get("external", False)), "path": Path(item["path"]).name}
                    for item in details.get("imports", [])
                ],
                "path": output_path,
            }
        )
    metafile = {
        "schema_version": 1,
        "inputs": sorted(_relative_entrypoint(path) for path in raw["inputs"]),
        "outputs": outputs,
    }
    (directory / METAFILE_NAME).write_text(_normal_json(metafile), encoding="utf-8")
    return metafile


def _asset_record(directory: Path, path: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(directory)),
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def _build_manifest(directory: Path) -> dict[str, Any]:
    generated = sorted(
        path for path in directory.iterdir() if path.is_file() and path.name not in {MANIFEST_NAME}
    )
    generated_names = {path.name for path in generated}
    missing_entries = sorted(set(ROUTE_ENTRIES.values()) - generated_names)
    if missing_entries:
        raise RuntimeError(f"esbuild did not produce required route entries: {missing_entries!r}")
    if not any(path.name.startswith("chunk-") and path.suffix == ".js" for path in generated):
        raise RuntimeError("esbuild did not produce a shared profile chunk")

    routes: dict[str, dict[str, object]] = {}
    for route, entry in ROUTE_ENTRIES.items():
        scripts = [f"/static/profiles_bundles/{entry}"]
        styles = list(SHARED_STYLES)
        if route == "json":
            # Monaco is a classic IIFE and must execute before the ESM entry.
            scripts.insert(0, MONACO_ASSETS[1])
            styles.insert(1, MONACO_ASSETS[0])
        routes[route] = {"scripts": scripts, "styles": styles}

    manifest = {
        "schema_version": 1,
        "builder": {
            "command": "make build-profile-frontend-bundles",
            "esbuild": json.loads(
                (REPO_ROOT / "node_modules" / "esbuild" / "package.json").read_text(
                    encoding="utf-8"
                )
            )["version"],
        },
        "head_script": HEAD_SCRIPT,
        "routes": routes,
        "generated_assets": [_asset_record(directory, path) for path in generated],
        "bundle_budgets": BUNDLE_BUDGETS,
        "vendor_boundary": {
            "monaco": {
                "assets": list(MONACO_ASSETS),
                "route": "json",
                "verification": "make verify-frontend-vendor",
            },
            "verification": "make verify-profile-frontend-bundles",
        },
        "license_strategy": {
            "application_bundles": (
                "BPM-owned source only; checksums cover every generated JS, map, and canonical metafile."
            ),
            "third_party": (
                "Monaco and Tailwind remain outside route bundles and are verified by vendor-lock.json and required notices."
            ),
        },
    }
    (directory / MANIFEST_NAME).write_text(_normal_json(manifest), encoding="utf-8")
    return manifest


def build(directory: Path) -> None:
    raw = _build_esbuild_output(directory)
    _write_canonical_metafile(directory, raw)
    _build_manifest(directory)


def _tree_files(directory: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def check() -> int:
    if not OUTPUT_DIR.is_dir():
        print(
            f"Missing {OUTPUT_DIR.relative_to(REPO_ROOT)}; run make build-profile-frontend-bundles.",
            file=sys.stderr,
        )
        return 1
    build(VERIFY_DIR)
    try:
        expected = _tree_files(OUTPUT_DIR)
        actual = _tree_files(VERIFY_DIR)
        if expected != actual:
            print(
                "Profile frontend bundles are out of date; run make build-profile-frontend-bundles.",
                file=sys.stderr,
            )
            return 1
    finally:
        shutil.rmtree(VERIFY_DIR, ignore_errors=True)
    print("Profile frontend bundles are reproducible")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Verify checked-in output without modifying it."
    )
    args = parser.parse_args(argv)
    try:
        _ensure_esbuild()
        if args.check:
            return check()
        build(OUTPUT_DIR)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"profile frontend bundle build failed: {error}", file=sys.stderr)
        return 1
    print(f"Built {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
