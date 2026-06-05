from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = REPO_ROOT / "app" / "static" / "vendor"
LOCK_PATH = VENDOR_DIR / "vendor-lock.json"
PACKAGE_PATH = REPO_ROOT / "package.json"
LOCKED_ASSET_PATHS = (
    "js-yaml.js",
    "js-yaml.LICENSE",
    "profiles_tailwind.css",
    "profiles_monaco.js",
    "profiles_monaco.css",
    "monaco-editor.worker.js",
    "monaco-json.worker.js",
    "monaco.LICENSE",
)
REQUIRED_LICENSE_SNIPPETS = {
    "js-yaml.LICENSE": ("The MIT License",),
    "profiles_monaco.js": (
        "Copyright (c) Microsoft Corporation. All rights reserved.",
        "Released under the MIT license",
    ),
    "monaco.LICENSE": ("The MIT License", "Microsoft Corporation"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_versions() -> dict[str, str]:
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    versions: dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        for name, version in package.get(section, {}).items():
            versions[name] = str(version)
    return versions


def build_lock() -> dict[str, Any]:
    versions = _package_versions()
    return {
        "schema_version": 1,
        "updated": "2026-06-03",
        "packages": {
            "js-yaml": versions["js-yaml"],
            "monaco-editor": versions["monaco-editor"],
            "esbuild": versions["esbuild"],
        },
        "assets": [
            {
                "path": relative_path,
                "size": (VENDOR_DIR / relative_path).stat().st_size,
                "sha256": _sha256(VENDOR_DIR / relative_path),
            }
            for relative_path in LOCKED_ASSET_PATHS
        ],
    }


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB"):
        if value < 1024 or unit == "MiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{size} B"
        value /= 1024
    return f"{size} B"


def _normalized_json(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _load_lock() -> dict[str, Any]:
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def _check_licenses() -> list[str]:
    errors: list[str] = []
    for relative_path, snippets in REQUIRED_LICENSE_SNIPPETS.items():
        source = (VENDOR_DIR / relative_path).read_text(encoding="utf-8", errors="replace")
        for snippet in snippets:
            if snippet not in source:
                errors.append(f"{relative_path}: missing license snippet {snippet!r}")
    return errors


def _size_report() -> str:
    expected = _load_lock()
    actual = build_lock()
    expected_assets = {entry["path"]: entry for entry in expected.get("assets", [])}
    lines = ["Frontend vendor size report:", "path | locked | current | delta"]
    for actual_entry in actual["assets"]:
        path = actual_entry["path"]
        locked_size = int(expected_assets.get(path, {}).get("size", 0))
        current_size = int(actual_entry["size"])
        delta = current_size - locked_size
        sign = "+" if delta > 0 else ""
        lines.append(
            f"{path} | {_human_size(locked_size)} | {_human_size(current_size)} | "
            f"{sign}{_human_size(delta) if delta else '0 B'}"
        )
    return "\n".join(lines)


def _check_lock() -> list[str]:
    expected = _load_lock()
    actual = build_lock()
    errors: list[str] = []

    if expected.get("schema_version") != actual["schema_version"]:
        errors.append("vendor-lock.json schema_version is not supported")

    if expected.get("packages") != actual["packages"]:
        errors.append("vendor package pins do not match package.json")

    expected_assets = {entry["path"]: entry for entry in expected.get("assets", [])}
    actual_assets = {entry["path"]: entry for entry in actual["assets"]}
    if set(expected_assets) != set(actual_assets):
        errors.append("vendor-lock.json asset list does not match expected vendored files")

    for path, actual_entry in actual_assets.items():
        expected_entry = expected_assets.get(path)
        if expected_entry is None:
            continue
        if expected_entry.get("size") != actual_entry["size"]:
            errors.append(f"{path}: size mismatch")
        if expected_entry.get("sha256") != actual_entry["sha256"]:
            errors.append(f"{path}: sha256 mismatch")

    if _normalized_json(expected) != LOCK_PATH.read_text(encoding="utf-8"):
        errors.append("vendor-lock.json is not normalized; run with --write")

    errors.extend(_check_licenses())

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify checked-in frontend vendor assets.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite app/static/vendor/vendor-lock.json from current assets.",
    )
    parser.add_argument(
        "--size-report",
        action="store_true",
        help="Print current vendor asset sizes compared with vendor-lock.json.",
    )
    parser.add_argument(
        "--check-licenses",
        action="store_true",
        help="Check required license headers/notices without validating checksums.",
    )
    args = parser.parse_args()

    if args.size_report:
        print(_size_report())
        return 0

    if args.check_licenses:
        errors = _check_licenses()
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("Frontend vendor license notices are present")
        return 0

    if args.write:
        LOCK_PATH.write_text(_normalized_json(build_lock()), encoding="utf-8")
        print(f"Wrote {LOCK_PATH.relative_to(REPO_ROOT)}")
        return 0

    errors = _check_lock()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("Run tools/verify_frontend_vendor.py --write after intentional rebuilds.", file=sys.stderr)
        return 1

    print("Frontend vendor assets match vendor-lock.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
