from __future__ import annotations

from fastapi import FastAPI

from app.db import get_session
from app.main import app as default_app
from tests.app_harness import (
    fresh_test_app,
    resolve_test_app,
    restore_dependency_overrides,
    snapshot_dependency_overrides,
)
from tests.support import make_test_client


def test_fresh_test_app_builds_distinct_application_instances():
    first = fresh_test_app()
    second = fresh_test_app()

    assert first is not second
    assert first is not default_app
    assert second is not default_app


def test_resolve_test_app_builds_fresh_default_and_preserves_explicit_apps():
    custom_app = FastAPI()

    resolved_default = resolve_test_app()
    resolved_legacy_default = resolve_test_app(default_app)
    resolved_custom = resolve_test_app(custom_app)

    assert resolved_default is not default_app
    assert resolved_legacy_default is default_app
    assert resolved_custom is custom_app


def test_restore_dependency_overrides_restores_complete_snapshot():
    test_app = FastAPI()

    def original_dependency():
        return "original"

    def original_override():
        return "override"

    def later_dependency():
        return "later"

    test_app.dependency_overrides[original_dependency] = original_override
    snapshot = snapshot_dependency_overrides(test_app)
    test_app.dependency_overrides.clear()
    test_app.dependency_overrides[later_dependency] = original_override

    restore_dependency_overrides(test_app, snapshot)

    assert test_app.dependency_overrides == {original_dependency: original_override}


def test_make_test_client_restores_default_app_overrides():
    def sentinel_override():
        return "sentinel"

    default_app.dependency_overrides[get_session] = sentinel_override

    with make_test_client(default_app) as client:
        assert client.app is default_app
        assert client.app.dependency_overrides[get_session] is not sentinel_override

    assert default_app.dependency_overrides[get_session] is sentinel_override


def test_make_test_client_restores_all_custom_app_overrides():
    custom_app = fresh_test_app()

    def sentinel_dependency():
        return "dependency"

    def sentinel_override():
        return "override"

    custom_app.dependency_overrides[sentinel_dependency] = sentinel_override

    with make_test_client(custom_app) as client:
        assert client.app is custom_app
        assert get_session in custom_app.dependency_overrides

    assert custom_app.dependency_overrides == {sentinel_dependency: sentinel_override}
