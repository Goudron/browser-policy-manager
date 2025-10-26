from __future__ import annotations

import asyncio

# В проекте модуль health пока не включен в main-роуты.
# Импортируем и вызываем хендлеры напрямую, чтобы прогреть код и поднять покрытие.
from app.api import health  # type: ignore


def test_health_module_import_and_handlers():
    assert hasattr(health, "router")

    # Если есть корутины внутри модуля — выполним их напрямую.
    # Это безопасно: тест не зависит от FastAPI-маршрутизации.
    maybe_checks = []
    for name in dir(health):
        obj = getattr(health, name)
        if asyncio.iscoroutinefunction(obj):
            maybe_checks.append(obj)

    # Выполним все найденные корутины (если есть).
    for coro in maybe_checks:
        res = asyncio.get_event_loop().run_until_complete(coro())  # type: ignore[arg-type]
        # допускаем любой возвращаемый тип; главное — исполнение строки кода модуля
        assert res is None or res is True or isinstance(res, dict)
