from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.core.schemas_loader import load_schema
from tests.cache_harness import APP_CACHE_RESET_REGISTRY, reset_app_caches


def test_app_cache_reset_registry_covers_mutable_application_caches():
    names = {spec.name for spec in APP_CACHE_RESET_REGISTRY}

    assert names == {
        "settings",
        "raw_schema_loader",
        "policy_schema_service",
        "policy_validators",
        "locale_catalogs",
        "profile_asset_version",
    }
    assert all(spec.policy for spec in APP_CACHE_RESET_REGISTRY)


def test_reset_app_caches_can_reset_one_named_cache_without_flushing_another():
    reset_app_caches()
    get_settings()
    load_schema("release-152")

    assert get_settings.cache_info().currsize == 1
    assert load_schema.cache_info().currsize == 1

    reset_app_caches("settings")

    assert get_settings.cache_info().currsize == 0
    assert load_schema.cache_info().currsize == 1

    reset_app_caches()


def test_reset_app_caches_rejects_unknown_names():
    with pytest.raises(KeyError, match="Unknown app cache names"):
        reset_app_caches("missing-cache")
