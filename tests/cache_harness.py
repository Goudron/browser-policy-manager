from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CacheResetCallback = Callable[[], Any]


@dataclass(frozen=True)
class CacheResetSpec:
    name: str
    module: str
    callback_path: str
    policy: str


APP_CACHE_RESET_REGISTRY = (
    CacheResetSpec(
        name="settings",
        module="app.core.config",
        callback_path="get_settings.cache_clear",
        policy="reset when tests mutate BPM_* environment or reload settings consumers",
    ),
    CacheResetSpec(
        name="raw_schema_loader",
        module="app.core.schemas_loader",
        callback_path="load_schema.cache_clear",
        policy="reset when tests replace schema directories or files",
    ),
    CacheResetSpec(
        name="policy_schema_service",
        module="app.services.policy_schema_service",
        callback_path="load_policy_schema.cache_clear",
        policy="reset when tests replace bundled policy schema directories or files",
    ),
    CacheResetSpec(
        name="policy_validators",
        module="app.core.policy_validation",
        callback_path="clear_policy_validator_cache",
        policy="reset when tests replace schema loaders or validator builders",
    ),
    CacheResetSpec(
        name="locale_catalogs",
        module="app.web.profiles_context",
        callback_path="clear_locale_catalog_cache",
        policy="reset when tests replace locale roots or locale files",
    ),
    CacheResetSpec(
        name="profile_asset_version",
        module="app.web.profiles_context",
        callback_path="_resolve_profiles_asset_version_from_paths.cache_clear",
        policy="worker-local immutable cache in normal tests; reset when files are replaced",
    ),
)


def _resolve_callback(spec: CacheResetSpec) -> CacheResetCallback:
    current: Any = importlib.import_module(spec.module)
    for part in spec.callback_path.split("."):
        current = getattr(current, part)
    if not callable(current):
        raise TypeError(f"Cache reset callback is not callable: {spec.name}")
    return current


def reset_app_caches(*names: str) -> None:
    """
    Reset registered application caches.

    Tests should call this through the `reset_app_caches` pytest fixture when
    monkeypatching cache inputs. Immutable worker-local caches stay warm unless
    a test explicitly requests a reset.
    """
    requested = set(names)
    known = {spec.name for spec in APP_CACHE_RESET_REGISTRY}
    unknown = requested - known
    if unknown:
        raise KeyError(f"Unknown app cache names: {', '.join(sorted(unknown))}")

    for spec in APP_CACHE_RESET_REGISTRY:
        if requested and spec.name not in requested:
            continue
        _resolve_callback(spec)()
