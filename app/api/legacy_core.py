"""Shim module: поднимает JSON-роутер из app.routes.api в пространство app.api.

Временный адаптер для мягкой миграции. После переноса роутеров в app/api — удалить.
"""

from __future__ import annotations

# ruff: noqa: F401  — router используется внешне (через include_router в app.main)
from app.routes.api import router as router
