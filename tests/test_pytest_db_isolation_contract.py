from __future__ import annotations

import os
from pathlib import Path

from tests.db_harness import WorkerDatabaseContext, configure_worker_database

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFTEST_PATH = REPO_ROOT / "tests" / "conftest.py"


def test_conftest_configures_worker_database_before_importing_app_db():
    source = CONFTEST_PATH.read_text(encoding="utf-8")

    configure_index = source.index("TEST_DATABASE_CONTEXT = configure_worker_database()")
    app_db_import_index = source.index("from app.db import AsyncSessionAdapter, get_session")

    assert configure_index < app_db_import_index


def test_worker_database_context_never_targets_project_data_db(
    worker_database_context: WorkerDatabaseContext,
):
    project_database_path = (REPO_ROOT / "data" / "bpm.db").resolve()

    assert worker_database_context.database_path.resolve() != project_database_path
    assert worker_database_context.database_url == os.environ["BPM_DATABASE_URL"]
    assert worker_database_context.database_path == Path(os.environ["BPM_TEST_DATABASE_PATH"])
    assert worker_database_context.worker_id == os.environ["BPM_TEST_WORKER_ID"]


def test_worker_database_paths_are_unique_for_xdist_worker_ids(tmp_path: Path):
    first = configure_worker_database(
        env={"PYTEST_XDIST_WORKER": "gw0"},
        temp_parent=tmp_path,
    )
    second = configure_worker_database(
        env={"PYTEST_XDIST_WORKER": "gw1"},
        temp_parent=tmp_path,
    )
    try:
        assert first.database_path != second.database_path
        assert first.database_url != second.database_url
        assert "gw0" in first.root_dir.name
        assert "gw1" in second.root_dir.name
    finally:
        first.cleanup()
        second.cleanup()


def test_conftest_session_guard_disposes_and_cleans_worker_database():
    source = CONFTEST_PATH.read_text(encoding="utf-8")

    assert "def guard_worker_database(worker_database_context: WorkerDatabaseContext):" in source
    assert "worker_database_context.database_path.resolve() != project_database_path" in source
    assert 'os.environ["BPM_DATABASE_URL"] == worker_database_context.database_url' in source
    assert "def pytest_unconfigure(config):" in source
    assert "_dispose_global_database_engine()" in source
    assert "worker_database_context.cleanup()" in source
