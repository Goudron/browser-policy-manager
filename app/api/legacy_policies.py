"""Shim module: поднимает JSON-роутер из app.routes.policies в пространство app.api.

Временный адаптер для мягкой миграции. После переноса роутеров в app/api — удалить.
"""

from __future__ import annotations

# ruff: noqa: F401
from app.routes.policies import router as router
