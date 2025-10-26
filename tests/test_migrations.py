from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


@pytest.mark.order(1)  # запускаем рано, но после окружения
def test_alembic_upgrade_head_on_sqlite_tmp(tmp_path: Path):
    """
    Smoke-тест: прогоняем Alembic upgrade head на временной SQLite-базе
    и проверяем наличие колонки 'deleted_at' в таблице 'policies'.

    Тест пропускается, если в проекте нет alembic.ini.
    """
    ini = Path("alembic.ini")
    if not ini.exists():
        pytest.skip("alembic.ini not found; skipping alembic smoke test")

    db_path = tmp_path / "migrations.db"
    url = f"sqlite:///{db_path}"
    # Готовим Alembic конфиг
    cfg = Config(str(ini))
    cfg.set_main_option("sqlalchemy.url", url)

    # Создаём пустую БД и прогоняем миграции
    engine = create_engine(url, future=True)
    try:
        command.upgrade(cfg, "head")
    finally:
        engine.dispose()

    # Проверяем структуру
    engine = create_engine(url, future=True)
    try:
        insp = inspect(engine)
        cols = {c["name"] for c in insp.get_columns("policies")}
        assert "deleted_at" in cols
    finally:
        engine.dispose()
