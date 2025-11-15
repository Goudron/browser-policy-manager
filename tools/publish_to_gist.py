#!/usr/bin/env python
"""
Publish a snapshot of the repository to a GitHub Gist, using a manifest file.

- Reads configuration from tools/gist_manifest.json
- Uses GIST_TOKEN environment variable (fine for CI and local runs)
- Supports both create (POST) and update (PATCH) modes
- Skips binary / non-UTF-8 files
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
MANIFEST_PATH = HERE / "gist_manifest.json"
GITHUB_API_URL = "https://api.github.com"


class GistError(RuntimeError):
    """Raised when the GitHub Gist API returns an error."""


def load_manifest(path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    if not path.exists():
        print(f"[gist] Manifest file not found: {path}", file=sys.stderr)
        raise SystemExit(1)

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Basic sanity checks
    if "description" not in data:
        data["description"] = "Browser Policy Manager snapshot"
    if "public" not in data:
        data["public"] = False

    include = data.get("include") or []
    exclude = data.get("exclude") or []

    if not isinstance(include, list) or not include:
        print("[gist] Manifest 'include' must be a non-empty list", file=sys.stderr)
        raise SystemExit(1)

    if not isinstance(exclude, list):
        print("[gist] Manifest 'exclude' must be a list (can be empty)", file=sys.stderr)
        raise SystemExit(1)

    return data


def _pattern_matches(patterns: List[str], rel_path: str) -> bool:
    """Return True if rel_path matches any of the patterns.

    Patterns support two simple forms:
    - "prefix"         → matches "prefix" and anything under "prefix/"
    - glob pattern     → if it contains *, ?, or [ ... ] then fnmatch is used
    """
    from fnmatch import fnmatch

    for pat in patterns:
        if not pat:
            continue
        if any(ch in pat for ch in "*?["):
            if fnmatch(rel_path, pat):
                return True
        else:
            # Treat as directory / prefix
            if rel_path == pat or rel_path.startswith(pat.rstrip("/") + "/"):
                return True
    return False


def _iter_candidate_files(include: List[str], exclude: List[str]) -> Iterable[Path]:
    """Yield repository files that match include and do not match exclude."""
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if not _pattern_matches(include, rel):
            continue
        if _pattern_matches(exclude, rel):
            continue
        yield path


def _is_text_file(path: Path) -> bool:
    """Heuristic: try to read as UTF-8. If it fails, treat as binary and skip."""
    try:
        with path.open("rb") as fh:
            chunk = fh.read(4096)
        chunk.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def build_files_payload(include: List[str], exclude: List[str]) -> Dict[str, Dict[str, str]]:
    files: Dict[str, Dict[str, str]] = {}

    for path in _iter_candidate_files(include, exclude):
        rel = path.relative_to(REPO_ROOT).as_posix()

        if not _is_text_file(path):
            print(f"[gist] Skipping non-text or non-UTF8 file: {rel}")
            continue

        # Sanitize filename for Gist: replace "/" with "__" to avoid any oddities
        filename = rel.replace("/", "__")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"[gist] Skipping file due to decode error: {rel}")
            continue

        files[filename] = {"content": content}

    return files


def create_or_update_gist(manifest: Dict[str, Any]) -> str:
    token = os.environ.get("GIST_TOKEN")
    if not token:
        print("[gist] Environment variable GIST_TOKEN is not set", file=sys.stderr)
        raise SystemExit(1)

    include = manifest.get("include", [])
    exclude = manifest.get("exclude", [])

    files_payload = build_files_payload(include, exclude)

    if not files_payload:
        print("[gist] No files selected for Gist (files_payload is empty)", file=sys.stderr)
        raise SystemExit(1)

    gist_id = manifest.get("gist_id")
    description = manifest.get("description", "Browser Policy Manager snapshot")
    public = bool(manifest.get("public", False))

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    payload: Dict[str, Any] = {
        "description": description,
        "public": public,
        "files": files_payload,
    }

    if gist_id:
        method = "PATCH"
        url = f"{GITHUB_API_URL}/gists/{gist_id}"
    else:
        method = "POST"
        url = f"{GITHUB_API_URL}/gists"

    print(f"[gist] {method} {url} with {len(files_payload)} files")

    resp = requests.request(method, url, headers=headers, json=payload, timeout=60)

    if resp.status_code >= 400:
        print("[gist] GitHub API error:")
        print(resp.text)
        raise GistError(f"GitHub API error {resp.status_code} for {url}")

    data = resp.json()
    gist_url = data.get("html_url") or data.get("url") or "<unknown>"

    # If this was a create operation, store the new gist_id in the manifest on disk.
    if not gist_id:
        new_id = data.get("id")
        if new_id:
            manifest["gist_id"] = new_id
            try:
                with MANIFEST_PATH.open("w", encoding="utf-8") as fh:
                    json.dump(manifest, fh, indent=2, ensure_ascii=False)
                print(f"[gist] Updated manifest with gist_id={new_id}")
            except OSError as exc:
                print(f"[gist] Warning: could not update manifest: {exc}", file=sys.stderr)

    print(f"[gist] Done: {gist_url}")
    return gist_url


def main() -> None:
    manifest = load_manifest()
    try:
        create_or_update_gist(manifest)
    except GistError:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
