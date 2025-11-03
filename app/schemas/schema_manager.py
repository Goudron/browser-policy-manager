"""
Schema Manager for Mozilla Firefox Enterprise Policies.

This module handles:
- Resolving remote URLs for official Mozilla policy schemas
- Downloading and caching policies-schema.json per target version
- Returning parsed schemas as Python dicts
- Optional transformation hook to normalize/annotate the schema

The manager is designed to work in CI and offline environments:
- If online fetch fails, it falls back to the cached file (if present)
- Timeouts and clear error messages help diagnose network issues

Target versions in Sprint G:
- ESR 140   -> version key: "esr140"
- Release 144 -> version key: "release144"
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import requests

# === Constants & Defaults =====================================================

DEFAULT_BASE_URL = "https://raw.githubusercontent.com/mozilla/policy-templates"
# Candidate paths inside the mozilla/policy-templates repo where
# policies-schema.json is commonly found; we try them in order.
CANDIDATE_SCHEMA_PATHS = [
    # The primary, current path in policy-templates repository
    "src/schema/policies-schema.json",
    # Historical/alternative locations (kept for robustness)
    "policy_templates/schema/policies-schema.json",
    "schemas/policies-schema.json",
]

DEFAULT_CACHE_DIR = "app/schemas/mozilla"

DEFAULT_HTTP_TIMEOUT = 15  # seconds
DEFAULT_RETRY = 2  # small retry for transient network issues


class SchemaManagerError(Exception):
    """Raised for schema manager operational errors."""


class SchemaDownloadError(SchemaManagerError):
    """Raised when remote schema cannot be downloaded."""


class SchemaNotFoundError(SchemaManagerError):
    """Raised when neither remote nor cache provides a schema."""


class SchemaVersion(Enum):
    """Logical versions we support in Sprint G.

    Each logical version maps to one or more upstream git refs.
    We try refs top-to-bottom until we download successfully.
    """

    ESR140 = "esr140"
    RELEASE144 = "release144"

    @property
    def refs(self) -> list[str]:
        # We keep several plausible refs for robustness:
        # tags (e.g., "release-144.0"), the "release" branch, and ESR branches.
        if self is SchemaVersion.ESR140:
            return [
                # Try exact tags first (most stable)
                "esr-140.0",
                "esr140",
                # Fallback to esr branch if exists
                "esr",
                # Final fallback to main
                "main",
            ]
        elif self is SchemaVersion.RELEASE144:
            return [
                "release-144.0",
                "release",  # rolling branch for releases
                "main",  # ultimate fallback
            ]
        return ["main"]

    @property
    def cache_subdir(self) -> str:
        return "esr140" if self is SchemaVersion.ESR140 else "release144"

    @staticmethod
    def from_key(key: str) -> SchemaVersion:
        k = key.strip().lower()
        if k in {"esr140", "firefox-esr140"}:
            return SchemaVersion.ESR140
        if k in {"release144", "firefox-release144"}:
            return SchemaVersion.RELEASE144
        raise ValueError(f"Unsupported schema version key: {key!r}")


@dataclass(frozen=True)
class SchemaMeta:
    """Metadata describing a cached schema file."""

    version: SchemaVersion
    sha256: str
    fetched_at: float
    source_ref: str
    source_url: str
    cache_path: Path


FetchFunc = Callable[[str, int], tuple[int, bytes]]
# Signature: (url, timeout_seconds) -> (status_code, content_bytes)


class SchemaManager:
    """
    Manages downloading and caching Mozilla Firefox Enterprise policy schemas.

    Typical usage:
        manager = SchemaManager()
        schema = manager.load("esr140")         # dict with the raw JSON schema
        schema = manager.load("release144", force_refresh=True)

    For testing, you can inject a custom fetcher:
        manager = SchemaManager(fetcher=my_fake_fetcher)
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache_dir: str = DEFAULT_CACHE_DIR,
        http_timeout: int = DEFAULT_HTTP_TIMEOUT,
        fetcher: FetchFunc | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.http_timeout = int(http_timeout)
        self._fetcher = fetcher or self._default_fetcher

        # Ensure base cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- Public API ------------------------------------------------------------

    def load(self, version_key: str, force_refresh: bool = False) -> dict:
        """
        Load schema dict for the given version key.

        If force_refresh is True, attempts to re-download from upstream.
        Otherwise, it tries cache first and falls back to download as needed.
        """
        version = SchemaVersion.from_key(version_key)
        cache_path = self._cache_file_for(version)

        if not force_refresh and cache_path.exists():
            return self._read_json(cache_path)

        # Try to fetch from upstream; on success, overwrite cache
        try:
            meta = self._download_and_cache(version)
            # Final read from cache to ensure we always return what's on disk
            return self._read_json(meta.cache_path)
        except SchemaDownloadError as e:
            # If download failed, attempt to use existing cache (if any)
            if cache_path.exists():
                return self._read_json(cache_path)
            raise SchemaNotFoundError(
                f"Failed to fetch schema for {version.value}, "
                f"and no cache found. Root cause: {e}"
            ) from e

    def update_cache(self, version_key: str) -> SchemaMeta:
        """
        Force download and update the cached schema.
        Returns SchemaMeta with details about the cached file.
        """
        version = SchemaVersion.from_key(version_key)
        return self._download_and_cache(version)

    def compute_cache_path(self, version_key: str) -> Path:
        """
        Returns the expected cache path for the given version key.
        """
        version = SchemaVersion.from_key(version_key)
        return self._cache_file_for(version)

    # -- Internals -------------------------------------------------------------

    def _download_and_cache(self, version: SchemaVersion) -> SchemaMeta:
        last_error: Exception | None = None

        # Try candidate refs and paths in a nested loop for robustness.
        for ref in version.refs:
            for rel_path in CANDIDATE_SCHEMA_PATHS:
                url = f"{self.base_url}/{ref}/{rel_path}"
                try:
                    status, content = self._retry_fetch(url)
                    if status == 200 and content:
                        # Validate JSON and write to cache
                        parsed = json.loads(content.decode("utf-8"))
                        cache_path = self._cache_file_for(version)
                        cache_path.parent.mkdir(parents=True, exist_ok=True)
                        cache_path.write_text(
                            json.dumps(parsed, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        sha = hashlib.sha256(content).hexdigest()
                        return SchemaMeta(
                            version=version,
                            sha256=sha,
                            fetched_at=time.time(),
                            source_ref=ref,
                            source_url=url,
                            cache_path=cache_path,
                        )
                except Exception as e:  # noqa: BLE001
                    last_error = e
                    # Try the next candidate
                    continue

        # If we reached here, we failed all candidates
        raise SchemaDownloadError(
            f"Unable to download policies-schema.json for {version.value}. "
            f"Last error: {last_error}"
        )

    def _retry_fetch(self, url: str) -> tuple[int, bytes]:
        # Simple retry for transient network hiccups
        backoff = 0.5
        for _attempt in range(1, DEFAULT_RETRY + 2):
            status, content = self._fetcher(url, self.http_timeout)
            if status == 200 and content:
                return status, content
            time.sleep(backoff)
            backoff *= 2
        return status, content

    def _cache_file_for(self, version: SchemaVersion) -> Path:
        return self.cache_dir.joinpath(version.cache_subdir, "policies-schema.json")

    @staticmethod
    def _read_json(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SchemaManagerError(f"Cached schema at {path} is not valid JSON") from e

    # -- Default HTTP fetcher --------------------------------------------------

    @staticmethod
    def _default_fetcher(url: str, timeout: int) -> tuple[int, bytes]:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code, resp.content


# === Optional normalization hook =============================================
# You can add a transformation function here to adapt upstream schema for
# internal UX (e.g., add "category" fields, versions array, etc.). For sprint G,
# we first deliver raw upstream compatibility; subsequent steps can build on it.


def normalize_schema_for_internal_use(schema: dict, version: SchemaVersion) -> dict:
    """
    Placeholder for optional normalization stage.

    For now, we simply annotate the root with a tiny metadata struct.
    """
    annotated = dict(schema)  # shallow copy
    annotated.setdefault("$meta", {})
    annotated["$meta"]["bpm_source_version"] = version.value
    annotated["$meta"]["bpm_generated_at"] = int(time.time())
    return annotated
