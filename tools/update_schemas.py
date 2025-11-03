#!/usr/bin/env python3
"""
CLI utility to fetch and cache Mozilla policies-schema.json files.

Examples:
    python tools/update_schemas.py --version esr140
    python tools/update_schemas.py --version release144
    python tools/update_schemas.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Local imports
# The tool is meant to be run from repository root. Adjust sys.path for app/*.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas import SchemaManager  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update cached Mozilla policy schemas")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--version", choices=["esr140", "release144"], help="Target schema version")
    g.add_argument("--all", action="store_true", help="Update all supported versions")
    p.add_argument("--force", action="store_true", help="Force re-download even if cache exists")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    manager = SchemaManager()

    keys = ["esr140", "release144"] if args.all else [args.version]

    exit_code = 0
    for key in keys:
        try:
            if args.force:
                meta = manager.update_cache(key)
            else:
                # load() will fetch if cache missing
                manager.load(key, force_refresh=False)
                # After load, compute meta-like output (without reading file contents)
                cache_path = manager.compute_cache_path(key)
                meta = f"(cached) {cache_path}"
                print(f"[ok] {key}: {meta}")
                continue

            print(
                f"[ok] {key}: saved to {meta.cache_path} "
                f"(ref={meta.source_ref}, sha256={meta.sha256[:12]}…)"
            )
        except Exception as e:  # noqa: BLE001
            print(f"[error] {key}: {e}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
