#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import fnmatch

import requests

# Репозиторий: .../browser-policy-manager/
ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tools" / "gist_manifest.json"


@dataclass
class GistManifest:
    description: str
    public: bool
    include: list[str]
    exclude: list[str]
    gist_id: str | None = None

    @classmethod
    def load(cls) -> "GistManifest":
        if not MANIFEST_PATH.exists():
            print(f"[gist] Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
            sys.exit(1)
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return cls(
            description=data.get("description", "browser-policy-manager snapshot"),
            public=bool(data.get("public", False)),
            include=list(data.get("include", [])),
            exclude=list(data.get("exclude", [])),
            gist_id=data.get("gist_id") or None,
        )

    def save(self) -> None:
        data: Dict[str, Any] = {
            "description": self.description,
            "public": self.public,
            "include": self.include,
            "exclude": self.exclude,
        }
        if self.gist_id:
            data["gist_id"] = self.gist_id
        MANIFEST_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def _matches_any(path: str, patterns: list[str]) -> bool:
    """Check if relative path matches any of exclude patterns."""
    return any(
        fnmatch.fnmatch(path, pat) or path.startswith(pat.rstrip("/"))
        for pat in patterns
    )


def build_files_payload(manifest: GistManifest) -> Dict[str, Dict[str, str]]:
    files: Dict[str, Dict[str, str]] = {}
    included_paths: set[Path] = set()

    for pattern in manifest.include:
        # Глоб-паттерн
        if any(ch in pattern for ch in "*?[]"):
            matches = list(ROOT.glob(pattern))
            if not matches:
                print(f"[gist] Warning: include pattern '{pattern}' did not match anything")
                continue
            for m in matches:
                if m.is_file():
                    included_paths.add(m)
                elif m.is_dir():
                    included_paths.update(p for p in m.rglob("*") if p.is_file())
            continue

        # Прямой путь (файл или директория)
        p = ROOT / pattern
        if not p.exists():
            print(f"[gist] Warning: include pattern '{pattern}' did not match anything")
            continue
        if p.is_file():
            included_paths.add(p)
        elif p.is_dir():
            included_paths.update(f for f in p.rglob("*") if f.is_file())

    for path in sorted(included_paths):
        rel = path.relative_to(ROOT).as_posix()

        if _matches_any(rel, manifest.exclude):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"[gist] Skipping non-text or non-UTF8 file: {rel}")
            continue

        if not text:
            # Пустые файлы смысла тащить нет (GitHub ещё и капризничает)
            continue

        files[rel] = {"content": text}

    if not files:
        print("[gist] ERROR: No files collected to publish (files payload is empty).", file=sys.stderr)
        sys.exit(1)

    return files


def create_or_update_gist(manifest: GistManifest) -> str:
    token = os.getenv("GIST_TOKEN")
    if not token:
        print("[gist] ERROR: GIST_TOKEN environment variable is not set", file=sys.stderr)
        sys.exit(1)

    files_payload = build_files_payload(manifest)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    if manifest.gist_id:
        url = f"https://api.github.com/gists/{manifest.gist_id}"
        method = "PATCH"
    else:
        url = "https://api.github.com/gists"
        method = "POST"

    payload: Dict[str, Any] = {
        "description": manifest.description,
        "public": manifest.public,
        "files": files_payload,
    }

    print(f"[gist] {method} {url} with {len(files_payload)} files")
    resp = requests.request(method, url, headers=headers, json=payload, timeout=60)

    if resp.status_code == 422:
        print("[gist] GitHub API error 422:", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        # Явно падаем, чтобы в логах было видно, что именно не понравилось
        sys.exit(1)

    resp.raise_for_status()
    data = resp.json()
    gist_url = data.get("html_url") or data.get("url")

    # Если только что создали новый гист — сохраняем его id в манифест
    if not manifest.gist_id and data.get("id"):
        manifest.gist_id = data["id"]
        manifest.save()
        print(f"[gist] Created new gist: {gist_url}")
    else:
        print(f"[gist] Updated gist: {gist_url}")

    return str(gist_url)


def main() -> None:
    manifest = GistManifest.load()
    create_or_update_gist(manifest)


if __name__ == "__main__":
    main()
