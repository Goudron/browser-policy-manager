from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ui"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/ui/import", response_class=HTMLResponse)
async def ui_import(request: Request):
    # Starlette/fastapi: сначала request, потом имя шаблона
    return templates.TemplateResponse(request, "import.html", {})
