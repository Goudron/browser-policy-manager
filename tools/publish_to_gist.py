#!/usr/bin/env python
"""
Publish a snapshot of the repository to a single GitHub Gist file.

- Packs (almost) the whole repo into a ZIP archive.
- Encodes the ZIP as base64 and uploads it as one file:
  browser-policy-manager-snapshot.zip.b64
- Uses GIST_TOKEN from the environment.
- Reads optional configuration from tools/gist_manifest.json:
    {
      "description": "Browser Policy Manager snapshot for ChatGPT",
      "public": false,
      "gist_id": "4352f9974fb97696e139cc03c9fc1950"
    }

If gist_id is missing, a new gist is created and gist_id is written back
to tools/gist_manifest.json.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Any

import requests

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
MANIFEST_PATH = HERE / "gist_manifest.json"
GITHUB_API_URL = "https://api.github.com"

logger = logging.getLogger("publish_to_gist")


class GistError(RuntimeError):
    """Raised when the GitHub Gist API returns an error."""


def load_manifest() -> dict[str, Any]:
    """
    Load tools/gist_manifest.json if it exists.

    Minimal expected structure:
      {
        "description": "Browser Policy Manager snapshot for ChatGPT",
        "public": false,
        "gist_id": "...."   # optional, can be missing for first run
      }
    """
    if not MANIFEST_PATH.exists():
        # Reasonable defaults if file does not exist.
        return {
            "description": "Browser Policy Manager snapshot for ChatGPT",
            "public": False,
        }

    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to read manifest %s: %s", MANIFEST_PATH, exc)
        return {
            "description": "Browser Policy Manager snapshot for ChatGPT",
            "public": False,
        }

    if "description" not in data:
        data["description"] = "Browser Policy Manager snapshot for ChatGPT"
    if "public" not in data:
        data["public"] = False

    return data


def save_manifest(manifest: dict[str, Any]) -> None:
    """Write updated manifest back to disk."""
    try:
        with MANIFEST_PATH.open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
        logger.info("Updated manifest at %s", MANIFEST_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not update manifest: %s", exc)


def should_exclude(rel_path: str) -> bool:
    """Return True if a path (relative to repo root) should be excluded."""
    parts = rel_path.split("/")

    # Exclude some top-level / nested directories.
    excluded_dirs = {
        ".git",
        ".github",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }
    if any(part in excluded_dirs for part in parts):
        return True

    # Exclude some common binary / tooling artefacts.
    excluded_suffixes = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".so",
        ".dll",
        ".dylib",
        ".zip",
        ".tgz",
        ".gz",
        ".xz",
        ".whl",
        ".db",
        ".sqlite3",
        ".log",
    }
    if any(rel_path.endswith(suf) for suf in excluded_suffixes):
        return True

    return False


def build_repo_zip() -> bytes:
    """
    Walk the repository and pack files into an in-memory ZIP archive.

    Returns raw ZIP bytes.
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file():
                continue

            rel = path.relative_to(REPO_ROOT).as_posix()

            if should_exclude(rel):
                # Uncomment this line if you need verbose logging.
                # logger.debug("Excluding from ZIP: %s", rel)
                continue

            # Never include the snapshot itself if it ends up in the repo.
            if rel.endswith("browser-policy-manager-snapshot.zip") or rel.endswith(
                "browser-policy-manager-snapshot.zip.b64",
            ):
                continue

            zf.write(path, arcname=rel)

    return buf.getvalue()


def create_or_update_gist(manifest: dict[str, Any]) -> str:
    """
    Create or update the Gist with repo snapshot.

    Returns the Gist HTML URL.
    """
    token = os.environ.get("GIST_TOKEN")
    if not token:
        logger.error("Environment variable GIST_TOKEN is not set")
        raise SystemExit(1)

    zip_bytes = build_repo_zip()
    if not zip_bytes:
        logger.error("ZIP snapshot is empty, aborting")
        raise SystemExit(1)

    # Encode ZIP to base64 so it can be safely stored in a JSON string.
    b64_content = base64.b64encode(zip_bytes).decode("ascii")

    description = manifest.get(
        "description",
        "Browser Policy Manager snapshot for ChatGPT",
    )
    public = bool(manifest.get("public", False))
    gist_id = manifest.get("gist_id")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    # Single file in the Gist: base64-encoded ZIP.
    files_payload: dict[str, dict[str, str]] = {
        "browser-policy-manager-snapshot.zip.b64": {
            "content": b64_content,
        },
    }

    payload: dict[str, Any] = {
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

    logger.info(
        "%s %s (1 file, ZIP encoded as base64, %d bytes)",
        method,
        url,
        len(zip_bytes),
    )

    resp = requests.request(method, url, headers=headers, json=payload, timeout=120)

    if resp.status_code >= 400:
        logger.error("GitHub API error: %s", resp.text)
        raise GistError(f"GitHub API error {resp.status_code} for {url}")

    data = resp.json()
    gist_url = data.get("html_url") or data.get("url") or "<unknown>"

    # If it was a create, remember the new gist_id.
    if not gist_id:
        new_id = data.get("id")
        if new_id:
            manifest["gist_id"] = new_id
            save_manifest(manifest)
            logger.info("Created new Gist with id=%s", new_id)
        else:
            logger.warning(
                "Created Gist but response has no 'id', response=%s",
                data,
            )
    else:
        logger.info("Updated existing Gist id=%s", gist_id)

    logger.info("Gist URL: %s", gist_url)
    return gist_url


def main() -> None:
    """Entry point for CLI usage."""
    # Simple logging setup for CLI runs; CI can override root config.
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    manifest = load_manifest()
    try:
        create_or_update_gist(manifest)
    except GistError:
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
