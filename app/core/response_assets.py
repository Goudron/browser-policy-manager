"""Immutable local response assets with safe development invalidation.

The application serves locale catalogs and its favicon directly rather than
through the general static mount.  Their bytes and response metadata are
immutable between file changes, so this module owns the process-local cache.
Each request still obtains a fresh ``Response`` from the cached snapshot.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImmutableResponseAsset:
    """Bytes and the stable metadata needed to construct a fresh response."""

    content: bytes
    media_type: str
    status_code: int = 200


def _asset_stat_identity(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


@cache
def _load_response_asset(
    path_text: str,
    mtime_ns: int,
    size: int,
    media_type: str,
) -> ImmutableResponseAsset:
    """Read an asset once for a concrete file identity.

    ``mtime_ns`` and ``size`` deliberately form the cache key: development
    edits receive a fresh snapshot without a server restart, while unchanged
    requests avoid synchronous file reads.
    """

    del mtime_ns, size
    return ImmutableResponseAsset(
        content=Path(path_text).read_bytes(),
        media_type=media_type,
    )


def _read_asset(path: Path, *, media_type: str) -> ImmutableResponseAsset | None:
    identity = _asset_stat_identity(path)
    if identity is None:
        return None
    return _load_response_asset(str(path), *identity, media_type)


@cache
def _load_validated_locale_response_asset(
    path_text: str,
    mtime_ns: int,
    size: int,
) -> ImmutableResponseAsset:
    asset = _load_response_asset(path_text, mtime_ns, size, "application/json")
    payload = json.loads(asset.content)
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in payload.items()
    ):
        raise ValueError(f"Locale catalog must be a string mapping: {path_text}")
    return asset


def load_locale_response_asset(path: Path) -> ImmutableResponseAsset | None:
    """Return a cached JSON locale response after validating its structure."""

    identity = _asset_stat_identity(path)
    if identity is None:
        return None
    return _load_validated_locale_response_asset(str(path), *identity)


def load_favicon_response_asset(path: Path) -> ImmutableResponseAsset | None:
    """Return the favicon snapshot, or ``None`` when it is absent."""

    return _read_asset(path, media_type="image/x-icon")


def clear_response_asset_cache() -> None:
    """Reset process-local assets when tests replace their source files."""

    _load_response_asset.cache_clear()
    _load_validated_locale_response_asset.cache_clear()
