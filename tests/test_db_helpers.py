from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import MetaData, create_engine, inspect

from app import db as db_module


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def scalars(self, *args, **kwargs):
        self.calls.append(("scalars", args, kwargs))
        return "scalars-result"

    def scalar(self, *args, **kwargs):
        self.calls.append(("scalar", args, kwargs))
        return "scalar-result"

    def execute(self, *args, **kwargs):
        self.calls.append(("execute", args, kwargs))
        return "execute-result"

    def flush(self):
        self.calls.append(("flush", (), {}))

    def refresh(self, instance):
        self.calls.append(("refresh", (instance,), {}))

    def commit(self):
        self.calls.append(("commit", (), {}))

    def rollback(self):
        self.calls.append(("rollback", (), {}))

    def close(self):
        self.calls.append(("close", (), {}))

    def add(self, instance):
        self.calls.append(("add", (instance,), {}))


def test_sqlite_url_helpers():
    assert db_module._is_sqlite_async_url("sqlite+aiosqlite:///./bpm.db") is True
    assert db_module._is_sqlite_async_url("postgresql+asyncpg://example") is False
    assert db_module._to_sync_sqlite_url("sqlite+aiosqlite:///./bpm.db") == "sqlite:///./bpm.db"


def test_normalize_database_url_keeps_empty_sqlite_path():
    assert db_module._normalize_database_url("sqlite:///") == "sqlite:///"


def test_normalize_database_url_resolves_bare_relative_sqlite_path(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(db_module._settings, "ROOT_DIR", tmp_path)

    normalized = db_module._normalize_database_url("sqlite:///data/app.db")

    assert normalized == f"sqlite:///{(tmp_path / 'data' / 'app.db').resolve()}"


def test_ensure_sqlite_parent_dir_skips_memory_and_non_sqlite_urls(tmp_path: Path):
    memory_target = tmp_path / "memory-parent"
    nonsqlite_target = tmp_path / "postgres-parent"

    db_module._ensure_sqlite_parent_dir(f"sqlite:///{memory_target}/:memory:")
    db_module._ensure_sqlite_parent_dir(f"postgresql:///{nonsqlite_target}/db")

    assert not memory_target.exists()
    assert not nonsqlite_target.exists()


def test_ensure_sqlite_parent_dir_creates_missing_parent(tmp_path: Path):
    target_dir = tmp_path / "nested" / "sqlite"
    db_url = f"sqlite:///{target_dir / 'app.db'}"

    db_module._ensure_sqlite_parent_dir(db_url)

    assert target_dir.is_dir()


def test_async_session_adapter_delegates_calls():
    session = _FakeSession()
    adapter = db_module.AsyncSessionAdapter(session)

    assert adapter.add("item") is None
    assert session.calls[-1] == ("add", ("item",), {})

    import asyncio

    async def _exercise():
        assert await adapter.scalars("stmt") == "scalars-result"
        assert await adapter.scalar("stmt") == "scalar-result"
        assert await adapter.execute("stmt") == "execute-result"
        await adapter.flush()
        await adapter.refresh("obj")
        await adapter.commit()
        await adapter.rollback()
        await adapter.close()

    asyncio.run(_exercise())

    called_methods = [name for name, _, _ in session.calls]
    for expected in ("scalars", "scalar", "execute", "flush", "refresh", "commit", "rollback", "close"):
        assert expected in called_methods


def test_resolve_metadata_prefers_app_models_base(monkeypatch):
    metadata = MetaData()
    fake_models = SimpleNamespace(Base=SimpleNamespace(metadata=metadata))

    monkeypatch.setattr(db_module.importlib, "import_module", lambda name: fake_models)

    assert db_module._resolve_metadata() is metadata


def test_resolve_metadata_prefers_app_models_metadata(monkeypatch):
    metadata = MetaData()
    fake_models = SimpleNamespace(metadata=metadata, Base=None)

    monkeypatch.setattr(db_module.importlib, "import_module", lambda name: fake_models)

    assert db_module._resolve_metadata() is metadata


def test_resolve_metadata_uses_profile_module_when_package_has_no_base(monkeypatch):
    metadata = MetaData()

    def _fake_import(name: str):
        if name == "app.models":
            return SimpleNamespace()
        if name == "app.models.profile":
            return SimpleNamespace(Base=SimpleNamespace(metadata=metadata))
        raise ImportError(name)

    monkeypatch.setattr(db_module.importlib, "import_module", _fake_import)

    assert db_module._resolve_metadata() is metadata


def test_resolve_metadata_uses_optional_base_module(monkeypatch):
    metadata = MetaData()

    def _fake_import(name: str):
        if name == "app.models":
            return SimpleNamespace()
        if name == "app.models.profile":
            raise ImportError(name)
        if name == "app.models.base":
            return SimpleNamespace(Base=SimpleNamespace(metadata=metadata))
        raise ImportError(name)

    monkeypatch.setattr(db_module.importlib, "import_module", _fake_import)
    monkeypatch.setattr(db_module.importlib.util, "find_spec", lambda name: object())

    assert db_module._resolve_metadata() is metadata


def test_resolve_metadata_falls_back_to_local_base(monkeypatch):
    def _raise_import_error(name: str):
        raise ImportError(name)

    monkeypatch.setattr(db_module.importlib, "import_module", _raise_import_error)
    monkeypatch.setattr(db_module.importlib.util, "find_spec", lambda name: None)

    metadata = db_module._resolve_metadata()

    assert isinstance(metadata, MetaData)


def test_resolve_metadata_falls_back_when_profile_and_base_have_no_metadata(monkeypatch):
    def _fake_import(name: str):
        if name == "app.models":
            return SimpleNamespace()
        if name == "app.models.profile":
            return SimpleNamespace(Base=object())
        if name == "app.models.base":
            return SimpleNamespace(Base=object())
        raise ImportError(name)

    monkeypatch.setattr(db_module.importlib, "import_module", _fake_import)
    monkeypatch.setattr(db_module.importlib.util, "find_spec", lambda name: object())

    metadata = db_module._resolve_metadata()

    assert isinstance(metadata, MetaData)


def test_resolve_metadata_falls_back_when_optional_base_import_errors(monkeypatch):
    def _fake_import(name: str):
        if name == "app.models":
            return SimpleNamespace()
        if name == "app.models.profile":
            return SimpleNamespace(Base=object())
        if name == "app.models.base":
            raise RuntimeError("broken optional module")
        raise ImportError(name)

    monkeypatch.setattr(db_module.importlib, "import_module", _fake_import)
    monkeypatch.setattr(db_module.importlib.util, "find_spec", lambda name: object())

    metadata = db_module._resolve_metadata()

    assert isinstance(metadata, MetaData)


def test_get_metadata_caches_resolved_metadata(monkeypatch):
    metadata = MetaData()
    calls = {"count": 0}

    def _fake_resolve():
        calls["count"] += 1
        return metadata

    monkeypatch.setattr(db_module, "_metadata", None)
    monkeypatch.setattr(db_module, "_resolve_metadata", _fake_resolve)

    assert db_module.get_metadata() is metadata
    assert db_module.get_metadata() is metadata
    assert calls["count"] == 1


def test_upgrade_legacy_sqlite_schema_noop_when_no_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}", future=True)
    try:
        db_module._upgrade_legacy_sqlite_schema(engine)
        inspector = inspect(engine)
        assert inspector.get_table_names() == []
    finally:
        engine.dispose()


def test_upgrade_legacy_sqlite_schema_skips_deleted_at_when_already_present(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'profiles.db'}", future=True)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """
                CREATE TABLE profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    schema_version VARCHAR(50) NOT NULL,
                    flags JSON NOT NULL,
                    owner VARCHAR(255),
                    deleted_at DATETIME,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )

        db_module._upgrade_legacy_sqlite_schema(engine)

        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("profiles")}
        assert "deleted_at" in columns
        assert "revision" in columns
    finally:
        engine.dispose()


def test_init_db_sync_mode_runs_upgrade_and_create_all(monkeypatch):
    calls = {}

    class _FakeMetadata:
        def create_all(self, bind):
            calls["bind"] = bind

    sentinel_engine = object()

    monkeypatch.setattr(db_module, "_SQLITE_SYNC_MODE", True)
    monkeypatch.setattr(db_module, "engine", sentinel_engine)
    monkeypatch.setattr(
        db_module,
        "_upgrade_legacy_sqlite_schema",
        lambda engine: calls.setdefault("upgraded", engine),
    )
    monkeypatch.setattr(db_module, "get_metadata", lambda: _FakeMetadata())

    asyncio.run(db_module.init_db())

    assert calls["upgraded"] is sentinel_engine
    assert calls["bind"] is sentinel_engine


def test_init_db_async_mode_runs_create_all_via_run_sync(monkeypatch):
    calls = {}

    class _FakeMetadata:
        def create_all(self, bind):
            calls["bind"] = bind

    class _FakeBeginContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def run_sync(self, fn):
            calls["run_sync"] = True
            fn("sync-connection")

    class _FakeEngine:
        def begin(self):
            return _FakeBeginContext()

    monkeypatch.setattr(db_module, "_SQLITE_SYNC_MODE", False)
    monkeypatch.setattr(db_module, "engine", _FakeEngine())
    monkeypatch.setattr(db_module, "get_metadata", lambda: _FakeMetadata())

    asyncio.run(db_module.init_db())

    assert calls["run_sync"] is True
    assert calls["bind"] == "sync-connection"


def test_get_session_sync_mode_yields_adapter_and_closes_session(monkeypatch):
    calls = {"closed": False}

    class _FakeSession:
        def close(self):
            calls["closed"] = True

    async def _fake_init_db():
        calls["initialized"] = True

    monkeypatch.setattr(db_module, "_SQLITE_SYNC_MODE", True)
    monkeypatch.setattr(db_module, "init_db", _fake_init_db)
    monkeypatch.setattr(db_module, "SessionLocal", lambda: _FakeSession())

    async def _exercise():
        generator = db_module.get_session()
        session = await anext(generator)
        assert isinstance(session, db_module.AsyncSessionAdapter)
        with pytest.raises(StopAsyncIteration):
            await anext(generator)

    asyncio.run(_exercise())

    assert calls["initialized"] is True
    assert calls["closed"] is True


def test_get_session_async_mode_uses_async_sessionmaker(monkeypatch):
    calls = {"closed": False}

    class _FakeSessionContext:
        async def __aenter__(self):
            return "async-session"

        async def __aexit__(self, exc_type, exc, tb):
            calls["closed"] = True
            return None

    async def _fake_init_db():
        calls["initialized"] = True

    monkeypatch.setattr(db_module, "_SQLITE_SYNC_MODE", False)
    monkeypatch.setattr(db_module, "init_db", _fake_init_db)
    monkeypatch.setattr(db_module, "SessionLocal", lambda: _FakeSessionContext())

    async def _exercise():
        generator = db_module.get_session()
        session = await anext(generator)
        assert session == "async-session"
        await generator.aclose()

    asyncio.run(_exercise())

    assert calls["initialized"] is True
    assert calls["closed"] is True


def test_db_module_switches_to_async_engine_for_non_sqlite(monkeypatch):
    from app.core import config as config_module

    live_db = db_module

    class _FakeAsyncEngine:
        def __init__(self) -> None:
            self.disposed = False

        def dispose(self) -> None:
            self.disposed = True

    with monkeypatch.context() as patch:
        patch.setenv("BPM_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/testdb")
        patch.setenv("BPM_DB_ECHO", "false")

        import sqlalchemy.ext.asyncio as sa_asyncio

        captured = {}
        fake_engine = _FakeAsyncEngine()

        def _fake_create_async_engine(url, echo):
            captured["engine_args"] = (url, echo)
            return fake_engine

        patch.setattr(
            sa_asyncio,
            "create_async_engine",
            _fake_create_async_engine,
        )
        patch.setattr(
            sa_asyncio,
            "async_sessionmaker",
            lambda engine, expire_on_commit=False: ("async_sessionmaker", engine, expire_on_commit),
        )

        config_module.get_settings.cache_clear()
        live_db.engine.dispose()
        reloaded = importlib.reload(live_db)

        assert reloaded._SQLITE_SYNC_MODE is False
        assert captured["engine_args"] == ("postgresql+asyncpg://user:pass@localhost/testdb", False)
        assert reloaded.SessionLocal == ("async_sessionmaker", reloaded.engine, False)
        assert isinstance(reloaded.engine, _FakeAsyncEngine)

    config_module.get_settings.cache_clear()
    live_db.engine.dispose()
    importlib.reload(live_db)
