from __future__ import annotations

import importlib


def test_settings_ignore_unprefixed_debug_env(monkeypatch):
    monkeypatch.setenv("DEBUG", "release")
    monkeypatch.delenv("BPM_DEBUG", raising=False)

    from app.core import config as config_module

    config_module.get_settings.cache_clear()
    settings = config_module.Settings()

    assert settings.DEBUG is False


def test_db_module_uses_prefixed_database_settings(monkeypatch):
    monkeypatch.setenv("DEBUG", "release")
    monkeypatch.setenv("BPM_DATABASE_URL", "sqlite+aiosqlite:///./tmp-bootstrap.db")
    monkeypatch.setenv("BPM_DB_ECHO", "true")

    from app import db as db_module
    from app.core import config as config_module

    config_module.get_settings.cache_clear()
    db_module.engine.dispose()
    reloaded_db = importlib.reload(db_module)

    assert str(reloaded_db.engine.url) == "sqlite:///./tmp-bootstrap.db"
    assert reloaded_db.engine.echo is True

    config_module.get_settings.cache_clear()
    reloaded_db.engine.dispose()
    importlib.reload(db_module)


def test_main_module_import_survives_unrelated_debug_env(monkeypatch):
    monkeypatch.setenv("DEBUG", "release")
    monkeypatch.delenv("BPM_DEBUG", raising=False)

    from app import db as db_module
    from app import main as main_module
    from app.core import config as config_module

    config_module.get_settings.cache_clear()
    db_module.engine.dispose()
    reloaded_main = importlib.reload(main_module)

    app = reloaded_main.create_app()
    assert app.title == "Browser Policy Manager"

    config_module.get_settings.cache_clear()
    db_module.engine.dispose()
    importlib.reload(main_module)
