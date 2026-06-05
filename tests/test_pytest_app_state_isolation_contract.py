from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFTEST_PATH = REPO_ROOT / "tests" / "conftest.py"
SUPPORT_PATH = REPO_ROOT / "tests" / "support.py"
CACHE_HARNESS_PATH = REPO_ROOT / "tests" / "cache_harness.py"


def test_async_client_fixture_uses_fresh_app_and_restores_overrides():
    source = CONFTEST_PATH.read_text(encoding="utf-8")

    assert "def test_app(app_factory):" in source
    assert "async def client(test_app, test_session):" in source
    assert "httpx.ASGITransport(app=test_app)" in source
    assert "snapshot_dependency_overrides(test_app)" in source
    assert "restore_dependency_overrides(test_app, override_snapshot)" in source
    assert "httpx.ASGITransport(app=default_app)" not in source


def test_conftest_guards_default_app_overrides_between_tests():
    source = CONFTEST_PATH.read_text(encoding="utf-8")

    assert "def guard_default_app_dependency_overrides():" in source
    assert source.count("default_app.dependency_overrides.clear()") >= 2


def test_make_test_client_resolves_apps_and_restores_override_snapshot():
    source = SUPPORT_PATH.read_text(encoding="utf-8")

    assert "app = resolve_test_app(app)" in source
    assert "override_snapshot = snapshot_dependency_overrides(app)" in source
    assert "restore_dependency_overrides(app, override_snapshot)" in source


def test_cache_reset_registry_documents_required_process_local_caches():
    source = CACHE_HARNESS_PATH.read_text(encoding="utf-8")

    required_tokens = {
        'name="settings"',
        'name="raw_schema_loader"',
        'name="policy_schema_service"',
        'name="policy_validators"',
        'name="locale_catalogs"',
        'name="profile_asset_version"',
        "Immutable worker-local caches stay warm",
    }
    for token in required_tokens:
        assert token in source


def test_conftest_exposes_explicit_cache_reset_fixture():
    source = CONFTEST_PATH.read_text(encoding="utf-8")

    assert "def reset_app_caches():" in source
    assert "reset_registered_app_caches()" in source
    assert "yield reset_registered_app_caches" in source
