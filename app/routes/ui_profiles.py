from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

# Для dev-режима читаем in-memory хранилище из API-роута
try:
    from app.routes import policies as policies_api  # noqa: F401
except Exception:  # pragma: no cover
    policies_api = None  # type: ignore[assignment]

router = APIRouter(tags=["ui"])


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request):
    templates = request.app.state.templates
    profiles = []
    if policies_api is not None:
        # Берём значения напрямую из dev-STORE
        profiles = list(policies_api._STORE.values())  # type: ignore[attr-defined]
    return templates.TemplateResponse(
        request,
        "profiles.html",
        {"profiles": profiles},
    )
