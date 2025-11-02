#!/usr/bin/env python3
"""
Publish current project snapshot (ZIP + manifest.json + optional reports) to a secret GitHub Gist.

Requirements:
  - Environment variable: GIST_TOKEN (PAT with "gist" scope only)
  - requests (pip install requests)

Behavior:
  - Creates manifest.json with (path, size, sha256) for tracked project files.
  - Packs project into snapshot.zip (excludes .git/, .venv/, venv/, .ruff_cache/, __pycache__/).
  - If coverage.xml / pytest-report.txt exist in the project root, they are also uploaded as Gist files.
  - Finds an existing secret Gist with the same description and updates it; otherwise creates a new one.
  - Prints the resulting Gist URL and writes it to 'gist_url.txt' in the current working directory.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests

ROOT = Path(__file__).resolve().parents[1]
GIST_DESC = "Browser Policy Manager snapshot"
GIST_API = "https://api.github.com/gists"
TOKEN = os.getenv("GIST_TOKEN")

INCLUDE_REPORTS = ["coverage.xml", "pytest-report.txt"]
ZIP_NAME = "snapshot.zip"
MANIFEST_NAME = "manifest.json"

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache"}


def die(msg: str) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def project_files() -> Iterable[Path]:
    # Prefer git-tracked files; fall back to rglob if git fails.
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=ROOT).decode().splitlines()
        for rel in out:
            p = ROOT / rel
            if p.is_file() and not is_excluded(p):
                yield p
    except Exception:
        for p in ROOT.rglob("*"):
            if p.is_file() and not is_excluded(p):
                yield p


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info() -> dict:
    def cmd(*args: str) -> str:
        try:
            return subprocess.check_output(args, cwd=ROOT).decode().strip()
        except Exception:
            return "unknown"

    return {
        "branch": cmd("git", "rev-parse", "--abbrev-ref", "HEAD"),
        "commit": cmd("git", "rev-parse", "--short", "HEAD"),
        "dirty": cmd("git", "status", "--porcelain") != "",
    }


def make_manifest() -> dict:
    items = []
    for p in project_files():
        rel = p.relative_to(ROOT).as_posix()
        items.append({"path": rel, "size": p.stat().st_size, "sha256": sha256(p)})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": git_info(),
        "files": items,
    }


def make_zip(tmpdir: Path) -> Path:
    zip_path = tmpdir / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in project_files():
            rel = p.relative_to(ROOT).as_posix()
            zf.write(p, arcname=rel)
    return zip_path


def create_or_update_gist(manifest: dict, zip_path: Path) -> str:
    if not TOKEN:
        die("Please set GIST_TOKEN environment variable with your GitHub token (gist scope only).")

    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

    # Base payload with manifest + zip (zip as base64 to avoid binary issues via API)
    files_payload = {
        MANIFEST_NAME: {"content": json.dumps(manifest, ensure_ascii=False, indent=2)},
        ZIP_NAME: {"content": base64.b64encode(zip_path.read_bytes()).decode()},
    }

    # Optionally include reports if present at repository root
    for name in INCLUDE_REPORTS:
        p = ROOT / name
        if p.exists():
            files_payload[name] = {"content": p.read_text(errors="replace")}

    payload = {"description": GIST_DESC, "public": False, "files": files_payload}

    # Try to find an existing gist with the same description
    rlist = requests.get(GIST_API, headers=headers)
    rlist.raise_for_status()
    gist = next((g for g in rlist.json() if g.get("description") == GIST_DESC), None)

    if gist:
        gist_id = gist["id"]
        r = requests.patch(f"{GIST_API}/{gist_id}", headers=headers, json=payload)
        r.raise_for_status()
        return f"https://gist.github.com/{gist_id}"

    r = requests.post(GIST_API, headers=headers, json=payload)
    r.raise_for_status()
    gist_id = r.json()["id"]
    return f"https://gist.github.com/{gist_id}"


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        manifest = make_manifest()
        zpath = make_zip(tmp)
        url = create_or_update_gist(manifest, zpath)
        print(f"🔗 Gist URL: {url}")
        # Write URL for CI to pick up as artifact
        Path("gist_url.txt").write_text(url, encoding="utf-8")


if __name__ == "__main__":
    main()
