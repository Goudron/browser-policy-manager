from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.db import _upgrade_legacy_sqlite_schema


def test_legacy_sqlite_schema_is_renamed_and_completed(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE policies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        schema_version VARCHAR(50) NOT NULL,
                        flags JSON NOT NULL,
                        owner VARCHAR(255),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            conn.execute(text("CREATE UNIQUE INDEX ix_policies_name ON policies (name)"))
            conn.execute(text("CREATE INDEX ix_policies_created_at ON policies (created_at)"))
            conn.execute(text("CREATE INDEX ix_policies_updated_at ON policies (updated_at)"))

        _upgrade_legacy_sqlite_schema(engine)

        inspector = inspect(engine)
        assert "profiles" in inspector.get_table_names()
        assert "policies" not in inspector.get_table_names()

        columns = {column["name"] for column in inspector.get_columns("profiles")}
        assert "deleted_at" in columns
        assert "revision" in columns

        index_names = {index["name"] for index in inspector.get_indexes("profiles")}
        assert "ix_profiles_name" in index_names
        assert "ix_profiles_created_at" in index_names
        assert "ix_profiles_updated_at" in index_names
        assert "ix_profiles_schema_version" in index_names
        assert "ix_profiles_owner" in index_names
        assert "ix_profiles_deleted_at" in index_names
        assert "ix_policies_name" not in index_names
    finally:
        engine.dispose()
