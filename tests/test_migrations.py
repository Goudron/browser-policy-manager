from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command


@pytest.mark.order(1)  # run early, but after environment setup
def test_alembic_upgrade_head_on_sqlite_tmp(tmp_path: Path):
    """
    Smoke test: run Alembic upgrade head on a temporary SQLite database
    and verify that the current 'profiles' table exists with soft-delete support.

    The test is skipped if the project has no alembic.ini.
    """
    ini = Path("alembic.ini")
    if not ini.exists():
        pytest.skip("alembic.ini not found; skipping alembic smoke test")

    db_path = tmp_path / "migrations.db"
    url = f"sqlite:///{db_path}"
    # Prepare Alembic config
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", url)

    # Create an empty database and run migrations
    engine = create_engine(url, future=True)
    try:
        command.upgrade(cfg, "head")
    finally:
        engine.dispose()

    # Verify the resulting schema
    engine = create_engine(url, future=True)
    try:
        insp = inspect(engine)
        assert "profiles" in insp.get_table_names()
        assert "policies" not in insp.get_table_names()
        cols = {c["name"] for c in insp.get_columns("profiles")}
        assert "deleted_at" in cols
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "20260323_normalize_profiles"
    finally:
        engine.dispose()


@pytest.mark.order(2)
def test_alembic_renames_legacy_policies_table_to_profiles(tmp_path: Path):
    ini = Path("alembic.ini")
    if not ini.exists():
        pytest.skip("alembic.ini not found; skipping alembic smoke test")

    db_path = tmp_path / "legacy-migrations.db"
    url = f"sqlite:///{db_path}"
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", url)

    engine = create_engine(url, future=True)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """
                CREATE TABLE policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    schema_version VARCHAR(50) NOT NULL,
                    flags TEXT NOT NULL,
                    owner VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted_at DATETIME
                )
                """
            )
            conn.exec_driver_sql("CREATE UNIQUE INDEX ix_policies_name ON policies (name)")
            conn.exec_driver_sql("CREATE INDEX ix_policies_created_at ON policies (created_at)")
            conn.exec_driver_sql("CREATE INDEX ix_policies_updated_at ON policies (updated_at)")
            conn.exec_driver_sql(
                "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
            )
            conn.exec_driver_sql(
                "INSERT INTO alembic_version (version_num) VALUES ('20251026_add_deleted_at')"
            )
    finally:
        engine.dispose()

    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    try:
        insp = inspect(engine)
        assert "profiles" in insp.get_table_names()
        assert "policies" not in insp.get_table_names()
        index_names = {idx["name"] for idx in insp.get_indexes("profiles")}
        assert "ix_profiles_name" in index_names
        assert "ix_profiles_deleted_at" in index_names
        assert "ix_policies_name" not in index_names
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "20260323_normalize_profiles"
    finally:
        engine.dispose()
