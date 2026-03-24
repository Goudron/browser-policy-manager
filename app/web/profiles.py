# app/web/profiles.py
# Web router for the Profiles management page with Monaco JSON/YAML editor.

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog

router = APIRouter(tags=["web"])

settings = get_settings()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request) -> HTMLResponse:
    """Render the main Profiles editor page."""
    current_year = datetime.now(UTC).year
    footer_year_range = "2025" if current_year <= 2025 else f"2025-{current_year}"
    wizard_settings_catalog = get_wizard_settings_catalog()
    wizard_preferences_catalog = get_wizard_preferences_catalog(wizard_settings_catalog)

    return templates.TemplateResponse(
        request,
        "profiles.html",
        {
            "title": "Profiles — Browser Policy Manager",
            "footer_year_range": footer_year_range,
            "wizard_settings_catalog": wizard_settings_catalog,
            "wizard_preferences_catalog": wizard_preferences_catalog,
            "wizard_manual_policy_controls": get_manual_policy_controls_catalog(),
            "wizard_starter_catalog": get_wizard_starter_catalog(),
            "wizard_schema_shell_catalog": get_wizard_schema_shell_catalog(wizard_preferences_catalog),
        },
    )
