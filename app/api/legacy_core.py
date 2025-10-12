# app/api/legacy_core.py
from __future__ import annotations

# Переназначаем существующий JSON-роутер, не трогая его исходник
from app.routes.api import router as router  # noqa: F401
