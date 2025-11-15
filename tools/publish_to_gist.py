#!/usr/bin/env python
from __future__ import annotations

import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT_DIR / "tools" / "gist_manifest.json"


def load_manifest() -> dict[str, Any]:
    """
    Load gist manifest describing which project files to publish.

    Supported schema (JSON):

    1) Explicit mapping (legacy mode):

        {
          "description": "Snapshot",
          "gist_id": "...",
          "files": {
            "app/main.py": "app/main.py",
            "pyproject.toml": "pyproject.toml"
          }
        }

    2) Auto-discovery mode (recommended):

        {
          "description": "Snapshot",
          "gist_id": "...",
          "include": ["README.md", "pyproject.toml", "app", "tests", ".github"],
          "exclude": [".git", ".venv", "__pycache__", "*.pyc", "*.db", "dist", "build"]
        }
    """
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Manifest not found: {MANIFEST_PATH}")

    with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _is_excluded(rel_path: Path, patterns: list[str]) -> bool:
    """
    Return True if the given relative path matches any of the exclude patterns.

    Patterns support simple fnmatch-style wildcards (e.g. "*.pyc", "dist", ".venv").
    Matching is done against the POSIX-style string of the relative path,
    and also against each individual path part for convenience.
    """
    s = rel_path.as_posix()
    parts = rel_path.parts

    for pattern in patterns:
        # Direct full path match or wildcard over full path
        if fnmatch.fnmatch(s, pattern):
            return True
        # Also check each individual component (e.g. ".venv", "__pycache__")
        if any(fnmatch.fnmatch(p, pattern) for p in parts):
            return True
    return False


def _discover_files(manifest: dict[str, Any]) -> dict[str, str]:
    """
    Auto-discover project files based on include/exclude patterns from manifest.

    Returns a mapping {gist_filename: project_rel_path}.
    """
    include_patterns = manifest.get("include")
    if not include_patterns:
        raise SystemExit(
            "Manifest must define either 'files' or 'include' patterns " "for auto-discovery."
        )

    exclude_patterns = manifest.get("exclude", [])

    file_map: dict[str, str] = {}

    for pattern in include_patterns:
        # Allow both files and directories and glob patterns.
        matches = list(ROOT_DIR.glob(pattern))

        if not matches:
            # Non-fatal: just warn to stderr.
            sys.stderr.write(
                f"[gist] Warning: include pattern '{pattern}' did not match anything\n"
            )
            continue

        for path in matches:
            if path.is_file():
                rel = path.relative_to(ROOT_DIR)
                if _is_excluded(rel, exclude_patterns):
                    continue
                file_map[rel.as_posix()] = rel.as_posix()
            elif path.is_dir():
                for child in path.rglob("*"):
                    if not child.is_file():
                        continue
                    rel = child.relative_to(ROOT_DIR)
                    if _is_excluded(rel, exclude_patterns):
                        continue
                    file_map[rel.as_posix()] = rel.as_posix()

    if not file_map:
        raise SystemExit(
            "Auto-discovery produced no files. "
            "Check 'include'/'exclude' patterns in tools/gist_manifest.json."
        )

    return file_map


def build_files_payload(files_map: dict[str, str]) -> dict[str, dict[str, str]]:
    """
    Build the 'files' payload for GitHub Gist API from a mapping
    {gist_filename: relative_project_path}.

    Only text files are included. Binary files are skipped with a warning.
    """
    payload: dict[str, dict[str, str]] = {}

    for gist_name, rel_path in files_map.items():
        path = ROOT_DIR / rel_path
        if not path.exists():
            raise SystemExit(f"File listed in manifest does not exist: {rel_path}")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip binary / non-UTF-8 files; they are not very useful in the gist context.
            sys.stderr.write(f"[gist] Skipping non-text or non-UTF8 file: {rel_path}\n")
            continue

        payload[gist_name] = {"content": content}

    if not payload:
        raise SystemExit("No text files to upload to Gist (payload is empty).")

    return payload


def get_token() -> str:
    """
    Obtain GitHub token from environment.

    CI / локальный запуск ожидают переменную окружения GIST_TOKEN.
    """
    token = os.environ.get("GIST_TOKEN")
    if not token:
        raise SystemExit("Environment variable GIST_TOKEN must be set for Gist publish")
    return token


def create_or_update_gist(manifest: dict[str, Any]) -> str:
    """
    Create or update a Gist based on the manifest.

    If "gist_id" is present, a PATCH is issued to update an existing Gist.
    Otherwise, a new private Gist is created via POST.
    """
    description = manifest.get(
        "description", "Browser Policy Manager snapshot for ChatGPT (auto files)"
    )

    # Legacy explicit mapping mode
    if "files" in manifest and isinstance(manifest["files"], dict):
        files_map: dict[str, str] = manifest["files"]
    else:
        # Auto-discovery mode (recommended)
        files_map = _discover_files(manifest)

    files_payload = build_files_payload(files_map)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {get_token()}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    gist_id = manifest.get("gist_id")
    if gist_id:
        url = f"https://api.github.com/gists/{gist_id}"
        body: dict[str, Any] = {
            "description": description,
            "files": files_payload,
        }
        resp = requests.patch(url, headers=headers, json=body, timeout=60)
    else:
        url = "https://api.github.com/gists"
        body = {
            "description": description,
            "public": False,
            "files": files_payload,
        }
        resp = requests.post(url, headers=headers, json=body, timeout=60)

    try:
        resp.raise_for_status()
    except requests.HTTPError:
        sys.stderr.write(f"[gist] GitHub API error {resp.status_code}:\n{resp.text}\n")
        raise

    data = resp.json()
    html_url = data.get("html_url", "")
    print(html_url)
    return html_url


def main() -> None:
    manifest = load_manifest()
    create_or_update_gist(manifest)


if __name__ == "__main__":
    main()
