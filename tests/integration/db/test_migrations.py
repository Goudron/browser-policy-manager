from __future__ import annotations

import json
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command

CURRENT_HEAD = "20260804_add_profile_name_casefold"
PRE_M4_04_HEAD = "20260721_upgrade_profiles_to_firefox153_dual_esr"
PRE_FIREFOX_153_HEAD = "20260620_upgrade_profiles_to_firefox152"
OWNER_DROP_HEAD = "20260606_drop_profile_owner"
PRE_OWNER_DROP_HEAD = "20260521_upgrade_profiles_to_firefox151"


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
        assert "compliance" in cols
        assert "name_casefold" in cols
        assert "revision" in cols
        assert "owner" not in cols
        index_names = {idx["name"] for idx in insp.get_indexes("profiles")}
        assert "ix_profiles_owner" not in index_names
        assert "ix_profiles_name_casefold" in index_names
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == CURRENT_HEAD
    finally:
        engine.dispose()


def test_alembic_repairs_only_the_retained_root_alias_data_path(tmp_path: Path):
    db_path = tmp_path / "root-alias.db"
    url = f"sqlite:///{db_path}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)

    engine = create_engine(url, future=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    CREATE TABLE policies (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        schema_version VARCHAR(50) NOT NULL,
                        flags TEXT NOT NULL,
                        owner VARCHAR(255),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """)
            )
            conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(64) NOT NULL)"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('5cb73fdb68ed')"))
            conn.execute(
                text("""
                    INSERT INTO policies (
                        id, name, description, schema_version, flags, owner, created_at, updated_at
                    ) VALUES (
                        101, 'root-alias', 'retained legacy row', 'release-148',
                        :flags, 'discarded-owner', '2025-10-22 08:30:00', '2025-10-23 09:45:00'
                    )
                    """),
                {"flags": json.dumps({"Proxy": {"Mode": "none"}}, sort_keys=True)},
            )
    finally:
        engine.dispose()

    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    try:
        inspector = inspect(engine)
        assert "policies" not in inspector.get_table_names()
        assert "owner" not in {column["name"] for column in inspector.get_columns("profiles")}
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text("""
                    SELECT id, name, description, schema_version, flags, compliance, revision,
                           created_at, updated_at, deleted_at
                    FROM profiles
                    """)
                )
                .mappings()
                .one()
            )
            revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert dict(row) == {
            "id": 101,
            "name": "root-alias",
            "description": "retained legacy row",
            "schema_version": "release-153",
            "flags": json.dumps({"Proxy": {"Mode": "none"}}, sort_keys=True),
            "compliance": None,
            "revision": 1,
            "created_at": "2025-10-22 08:30:00",
            "updated_at": "2025-10-23 09:45:00",
            "deleted_at": None,
        }
        assert revision == CURRENT_HEAD
    finally:
        engine.dispose()


def test_alembic_refuses_mixed_profile_tables_with_data(tmp_path: Path):
    db_path = tmp_path / "mixed-profile-tables.db"
    url = f"sqlite:///{db_path}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, PRE_M4_04_HEAD)

    engine = create_engine(url, future=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO profiles (name, schema_version, flags)
                    VALUES ('already-profile', 'release-153', '{}')
                    """)
            )
            conn.execute(
                text("""
                    CREATE TABLE policies (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        schema_version VARCHAR(50) NOT NULL,
                        flags TEXT NOT NULL,
                        owner VARCHAR(255),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """)
            )
    finally:
        engine.dispose()

    with pytest.raises(RuntimeError, match="profile-table shape"):
        command.upgrade(cfg, "head")


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
            conn.exec_driver_sql("""
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
                """)
            conn.exec_driver_sql("CREATE UNIQUE INDEX ix_policies_name ON policies (name)")
            conn.exec_driver_sql("CREATE INDEX ix_policies_created_at ON policies (created_at)")
            conn.exec_driver_sql("CREATE INDEX ix_policies_updated_at ON policies (updated_at)")
            conn.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
            conn.exec_driver_sql(
                "INSERT INTO alembic_version (version_num) VALUES ('20251026_add_deleted_at')"
            )
            conn.exec_driver_sql("""
                INSERT INTO policies (name, description, schema_version, flags, owner, created_at, updated_at)
                VALUES
                    ('legacy-release', NULL, 'release-148', '{}', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                    ('legacy-esr', NULL, 'esr-140.8', '{}', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """)
    finally:
        engine.dispose()

    command.upgrade(cfg, "head")

    engine = create_engine(url, future=True)
    try:
        insp = inspect(engine)
        assert "profiles" in insp.get_table_names()
        assert "policies" not in insp.get_table_names()
        columns = {column["name"] for column in insp.get_columns("profiles")}
        assert "revision" in columns
        assert "owner" not in columns
        index_names = {idx["name"] for idx in insp.get_indexes("profiles")}
        assert "ix_profiles_name" in index_names
        assert "ix_profiles_deleted_at" in index_names
        assert "ix_profiles_owner" not in index_names
        assert "ix_policies_name" not in index_names
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            schema_versions = conn.execute(
                text("SELECT name, schema_version FROM profiles ORDER BY name")
            ).all()
        assert version == CURRENT_HEAD
        assert schema_versions == [
            ("legacy-esr", "esr-140.13"),
            ("legacy-release", "release-153"),
        ]
    finally:
        engine.dispose()


def test_m4_04_downgrade_is_rejected_in_favor_of_verified_backup(tmp_path: Path):
    db_path = tmp_path / "m4-downgrade.db"
    url = f"sqlite:///{db_path}"
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    with pytest.raises(NotImplementedError, match="verified backup"):
        command.downgrade(cfg, PRE_M4_04_HEAD)


def test_alembic_profile_owner_drop_upgrade_and_downgrade(tmp_path: Path):
    ini = Path("alembic.ini")
    if not ini.exists():
        pytest.skip("alembic.ini not found; skipping alembic smoke test")

    db_path = tmp_path / "owner-drop.db"
    url = f"sqlite:///{db_path}"
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", url)

    engine = create_engine(url, future=True)
    try:
        command.upgrade(cfg, PRE_OWNER_DROP_HEAD)
        insp = inspect(engine)
        columns = {column["name"] for column in insp.get_columns("profiles")}
        assert "owner" in columns
        assert "ix_profiles_owner" in {idx["name"] for idx in insp.get_indexes("profiles")}
    finally:
        engine.dispose()

    command.upgrade(cfg, OWNER_DROP_HEAD)

    engine = create_engine(url, future=True)
    try:
        insp = inspect(engine)
        columns = {column["name"] for column in insp.get_columns("profiles")}
        assert "owner" not in columns
        assert "ix_profiles_owner" not in {idx["name"] for idx in insp.get_indexes("profiles")}
    finally:
        engine.dispose()

    command.downgrade(cfg, PRE_OWNER_DROP_HEAD)

    engine = create_engine(url, future=True)
    try:
        insp = inspect(engine)
        columns = {column["name"] for column in insp.get_columns("profiles")}
        assert "owner" in columns
        assert "ix_profiles_owner" in {idx["name"] for idx in insp.get_indexes("profiles")}
    finally:
        engine.dispose()


def test_alembic_firefox_153_migration_preserves_dual_esr_lines(tmp_path: Path):
    ini = Path("alembic.ini")
    if not ini.exists():
        pytest.skip("alembic.ini not found; skipping alembic smoke test")

    db_path = tmp_path / "firefox-153-migration.db"
    url = f"sqlite:///{db_path}"
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, PRE_FIREFOX_153_HEAD)
    engine = create_engine(url, future=True)
    try:
        with engine.begin() as conn:
            for name, schema_version in (
                ("release-149", "release-149"),
                ("release-150", "release-150"),
                ("release-151", "release-151"),
                ("release-152", "release-152"),
                ("esr-140-9", "esr-140.9"),
                ("esr-140-10", "esr-140.10"),
                ("esr-140-11", "esr-140.11"),
                ("esr-140-12", "esr-140.12"),
                ("supported-esr-140", "esr-140.13"),
                ("supported-esr-153", "esr-153.0"),
            ):
                conn.execute(
                    text(
                        "INSERT INTO profiles (name, schema_version, flags) "
                        "VALUES (:name, :schema_version, '{}')"
                    ),
                    {"name": name, "schema_version": schema_version},
                )
    finally:
        engine.dispose()

    command.upgrade(cfg, PRE_M4_04_HEAD)

    engine = create_engine(url, future=True)
    try:
        with engine.connect() as conn:
            schema_versions = dict(
                conn.execute(text("SELECT name, schema_version FROM profiles")).all()
            )
        assert schema_versions == {
            "release-149": "release-153",
            "release-150": "release-153",
            "release-151": "release-153",
            "release-152": "release-153",
            "esr-140-9": "esr-140.13",
            "esr-140-10": "esr-140.13",
            "esr-140-11": "esr-140.13",
            "esr-140-12": "esr-140.13",
            "supported-esr-140": "esr-140.13",
            "supported-esr-153": "esr-153.0",
        }
    finally:
        engine.dispose()

    command.downgrade(cfg, PRE_FIREFOX_153_HEAD)

    engine = create_engine(url, future=True)
    try:
        with engine.connect() as conn:
            schema_versions = dict(
                conn.execute(text("SELECT name, schema_version FROM profiles")).all()
            )
        assert schema_versions == {
            "release-149": "release-152",
            "release-150": "release-152",
            "release-151": "release-152",
            "release-152": "release-152",
            "esr-140-9": "esr-140.12",
            "esr-140-10": "esr-140.12",
            "esr-140-11": "esr-140.12",
            "esr-140-12": "esr-140.12",
            "supported-esr-140": "esr-140.12",
            "supported-esr-153": "esr-153.0",
        }
    finally:
        engine.dispose()
