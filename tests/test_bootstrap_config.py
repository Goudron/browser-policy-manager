from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


def test_settings_ignore_unprefixed_debug_env(monkeypatch):
    monkeypatch.setenv("DEBUG", "release")
    monkeypatch.delenv("BPM_DEBUG", raising=False)

    from app.core import config as config_module

    config_module.get_settings.cache_clear()
    settings = config_module.Settings()

    assert settings.DEBUG is False


def test_settings_version_matches_pyproject():
    from app.core import config as config_module

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    settings = config_module.Settings()

    assert pyproject["project"]["version"] == "0.8.8"
    assert settings.APP_VERSION == pyproject["project"]["version"]


def test_project_version_falls_back_when_pyproject_cannot_be_read(monkeypatch):
    from app.core import config as config_module

    def _raise_os_error(*args, **kwargs):
        raise OSError("no pyproject")

    monkeypatch.setattr(config_module.Path, "read_text", _raise_os_error)

    assert config_module._read_project_version() == "0.0.0-dev"


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
