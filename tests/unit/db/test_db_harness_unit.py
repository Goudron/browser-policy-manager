from __future__ import annotations

from pathlib import Path

from tests.db_harness import configure_worker_database, normalize_worker_id, sqlite_async_url


def test_normalize_worker_id_returns_safe_default_and_sanitized_value():
    assert normalize_worker_id(None) == "main"
    assert normalize_worker_id("") == "main"
    assert normalize_worker_id("gw0") == "gw0"
    assert normalize_worker_id(" worker / 1 ") == "worker-1"


def test_sqlite_async_url_uses_absolute_path(tmp_path: Path):
    database_path = tmp_path / "nested" / "bpm.db"

    assert sqlite_async_url(database_path) == f"sqlite+aiosqlite:///{database_path.resolve()}"


def test_configure_worker_database_sets_worker_local_environment(tmp_path: Path):
    env = {"PYTEST_XDIST_WORKER": "gw2"}

    context = configure_worker_database(env=env, temp_parent=tmp_path)
    try:
        assert context.worker_id == "gw2"
        assert context.root_dir.parent == tmp_path.resolve()
        assert context.root_dir.name.startswith("bpm-pytest-gw2-")
        assert context.database_path == context.root_dir / "bpm.db"
        assert env["BPM_DATABASE_URL"] == context.database_url
        assert env["BPM_TEST_DATABASE_PATH"] == str(context.database_path)
        assert env["BPM_TEST_WORKER_ID"] == "gw2"
    finally:
        context.cleanup()

    assert not context.root_dir.exists()


def test_configure_worker_database_uses_distinct_worker_directories(tmp_path: Path):
    first = configure_worker_database(
        env={"PYTEST_XDIST_WORKER": "gw0"},
        temp_parent=tmp_path,
    )
    second = configure_worker_database(
        env={"PYTEST_XDIST_WORKER": "gw1"},
        temp_parent=tmp_path,
    )
    try:
        assert first.root_dir != second.root_dir
        assert first.database_path != second.database_path
        assert first.database_url != second.database_url
    finally:
        first.cleanup()
        second.cleanup()


def test_configure_worker_database_nests_worker_under_configured_root(tmp_path: Path):
    configured_root = tmp_path / "worker-databases"
    stale_worker_root = configured_root / "gw3"
    stale_worker_root.mkdir(parents=True)
    (stale_worker_root / "stale.db").write_text("stale", encoding="utf-8")
    env = {
        "PYTEST_XDIST_WORKER": "gw3",
        "BPM_TEST_DATABASE_ROOT": str(configured_root),
    }

    context = configure_worker_database(env=env)
    try:
        assert context.root_dir == (configured_root / "gw3").resolve()
        assert context.database_path == context.root_dir / "bpm.db"
        assert not (context.root_dir / "stale.db").exists()
    finally:
        context.cleanup()
