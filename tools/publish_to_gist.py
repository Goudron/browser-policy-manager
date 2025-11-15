#!/usr/bin/env python3
"""
Publish a snapshot of the repository to a GitHub Gist.

Behavior:
- Create a ZIP archive with the current repo contents (excluding .git, .venv, dist, __pycache__).
- Base64-encode the archive and upload it as a single file to a (private) Gist.
- If gist_manifest.json contains a valid gist_id, try to PATCH that Gist.
  If PATCH returns 404/422, fall back to creating a new Gist via POST.
- Update gist_manifest.json with the new gist_id and print the HTML URL to stdout.

This script is intentionally self-contained and defensive so it can be used
both locally and from CI.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys
import zipfile
from typing import Any, Dict

import requests


API_URL = "https://api.github.com/gists"
MANIFEST_NAME = "gist_manifest.json"


def repo_root_from_this_file() -> Path:
    """Return the repository root assuming tools/ directory layout."""
    return Path(__file__).resolve().parents[1]


def manifest_path() -> Path:
    """Return path to gist_manifest.json next to this script."""
    return Path(__file__).resolve().with_name(MANIFEST_NAME)


def load_manifest() -> Dict[str, Any]:
    """Load manifest or return a sensible default if it does not exist."""
    mpath = manifest_path()
    if not mpath.exists():
        return {
            "description": "Browser Policy Manager snapshot archive",
            "gist_id": None,
            "filename": "browser-policy-manager-snapshot.zip.b64",
        }

    with mpath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Ensure required keys exist, but keep any extra keys untouched.
    data.setdefault("description", "Browser Policy Manager snapshot archive")
    data.setdefault("gist_id", None)
    data.setdefault("filename", "browser-policy-manager-snapshot.zip.b64")
    return data


def save_manifest(manifest: Dict[str, Any]) -> None:
    """Persist manifest to disk with pretty JSON formatting."""
    mpath = manifest_path()
    with mpath.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)


def should_exclude(path: Path, root: Path) -> bool:
    """
    Decide whether a given path should be excluded from the snapshot.

    Exclude:
    - .git, .venv, dist, __pycache__ and their contents.
    """
    rel = path.relative_to(root)
    parts = rel.parts
    if not parts:
        return False

    if parts[0] in {".git", ".venv", "dist", "__pycache__"}:
        return True

    # Also skip nested __pycache__ directories
    if "__pycache__" in parts:
        return True

    return False


def create_zip_snapshot(root: Path) -> Path:
    """
    Create a ZIP archive with repository files under <root>/dist.

    Returns the path to the created ZIP file.
    """
    dist_dir = root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    zip_path = dist_dir / "browser-policy-manager-snapshot.zip"

    # Recreate archive every time to avoid stale contents.
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in root.rglob("*"):
            if not item.is_file():
                continue
            if should_exclude(item, root):
                continue
            arcname = item.relative_to(root)
            zf.write(item, arcname)

    return zip_path


def build_gist_payload(manifest: Dict[str, Any], archive_path: Path) -> Dict[str, Any]:
    """
    Build the JSON payload for GitHub Gist API.

    The archive is base64-encoded and uploaded as a single file.
    """
    raw = archive_path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")

    filename = manifest.get("filename") or "browser-policy-manager-snapshot.zip.b64"
    manifest["filename"] = filename

    description = manifest.get("description") or "Browser Policy Manager snapshot archive"

    payload: Dict[str, Any] = {
        "description": description,
        "public": False,
        "files": {
            filename: {
                "content": b64,
            }
        },
    }
    return payload


def get_gist_token() -> str:
    """
    Resolve GitHub token for Gist operations.

    Tries GIST_TOKEN first, then GITHUB_TOKEN. Raises if neither is set.
    """
    token = os.getenv("GIST_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing GitHub token: set GIST_TOKEN or GITHUB_TOKEN env variable")
    return token


def create_or_update_gist(manifest: Dict[str, Any], archive_path: Path) -> str:
    """
    Create or update a Gist with the given manifest and archive.

    Returns the HTML URL of the resulting Gist.
    """
    token = get_gist_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "browser-policy-manager-gist-publisher",
    }

    payload = build_gist_payload(manifest, archive_path)
    gist_id = manifest.get("gist_id")

    # Helper: create new Gist
    def _post_new() -> requests.Response:
        return requests.post(API_URL, headers=headers, json=payload, timeout=60)

    # Helper: patch existing Gist
    def _patch_existing(gid: str) -> requests.Response:
        url = f"{API_URL}/{gid}"
        return requests.patch(url, headers=headers, json=payload, timeout=60)

    response: requests.Response

    if gist_id:
        # First try to patch existing gist
        response = _patch_existing(str(gist_id))
        if response.status_code in (404, 422):
            # Stale or invalid gist; fall back to creating a new one
            print(
                f"Existing gist {gist_id} returned {response.status_code}, "
                "creating a new gist instead.",
                file=sys.stderr,
            )
            manifest["gist_id"] = None
            response = _post_new()
    else:
        # No gist_id in manifest, always create new gist
        response = _post_new()

    # Raise if still not successful
    response.raise_for_status()
    data = response.json()

    new_id = data.get("id")
    html_url = data.get("html_url")

    if not new_id or not html_url:
        raise RuntimeError(f"Unexpected Gist API response: {data!r}")

    manifest["gist_id"] = new_id
    save_manifest(manifest)

    return html_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish repository snapshot to GitHub Gist.")
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root_from_this_file(),
        help="Repository root to snapshot (default: project root inferred from tools/).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"Root path does not exist: {root}")

    archive_path = create_zip_snapshot(root)
    manifest = load_manifest()
    url = create_or_update_gist(manifest, archive_path)

    # Print URL to stdout so CI can capture it if needed.
    print(url)


if __name__ == "__main__":
    main()
