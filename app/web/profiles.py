# app/web/profiles.py
# Web router for the Profiles management page with Monaco JSON/YAML editor.

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

router = APIRouter(tags=["web"])

settings = get_settings()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request) -> HTMLResponse:
    """Render the main Profiles editor page."""
    return templates.TemplateResponse(
        request,
        "profiles.html",
        {
            "title": "Profiles — Browser Policy Manager",
        },
    )
