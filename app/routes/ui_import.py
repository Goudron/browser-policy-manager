from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/ui/import", response_class=HTMLResponse)
async def ui_import(request: Request):
    """
    Render the import page.
    Uses the shared Jinja2Templates instance with registered translation function `t()`.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "import.html", {})
