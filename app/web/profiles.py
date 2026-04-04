# app/web/profiles.py
# Web router for the Profiles management page with Monaco JSON/YAML editor.

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import cache
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.schema_channels import build_schema_channels_catalog
from app.web.firefox_manual_policy_controls import get_manual_policy_controls_catalog
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_settings_catalog import get_wizard_settings_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from app.web.firefox_wizard_steps import get_wizard_steps

router = APIRouter(tags=["web"])

settings = get_settings()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@cache
def _load_locale_catalog(locale: str) -> dict[str, str]:
    locale_path = Path(settings.ROOT_DIR) / settings.I18N_DIR / f"{locale}.json"
    if not locale_path.is_file():
        return {}
    return json.loads(locale_path.read_text(encoding="utf-8"))


@cache
def _resolve_profiles_asset_version() -> str:
    latest_mtime = 0
    for root in (settings.STATIC_DIR, settings.TEMPLATES_DIR):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            latest_mtime = max(latest_mtime, int(path.stat().st_mtime))
    return str(latest_mtime or settings.APP_VERSION)


def _resolve_request_locale(request: Request) -> str:
    supported = tuple(settings.SUPPORTED_LOCALES)
    header = request.headers.get("accept-language", "")

    weighted_locales: list[tuple[float, str]] = []
    for raw_part in header.split(","):
        part = raw_part.strip()
        if not part:
            continue
        lang_token, _, params = part.partition(";")
        lang = lang_token.strip().lower().split("-", 1)[0]
        if lang not in supported:
            continue
        weight = 1.0
        for param in params.split(";"):
            param = param.strip()
            if not param.startswith("q="):
                continue
            try:
                weight = float(param[2:])
            except ValueError:
                weight = 0.0
        weighted_locales.append((weight, lang))

    if not weighted_locales:
        return "en"

    weighted_locales.sort(key=lambda item: item[0], reverse=True)
    return weighted_locales[0][1]


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request) -> HTMLResponse:
    """Render the main Profiles editor page."""
    current_year = datetime.now(UTC).year
    footer_year_range = "2025" if current_year <= 2025 else f"2025-{current_year}"
    wizard_settings_catalog = get_wizard_settings_catalog()
    wizard_preferences_catalog = get_wizard_preferences_catalog(wizard_settings_catalog)
    initial_lang = _resolve_request_locale(request)
    initial_locale = _load_locale_catalog(initial_lang)

    def tr(key: str, fallback: str = "") -> str:
        value = initial_locale.get(key)
        if isinstance(value, str) and value:
            return value
        return fallback

    return templates.TemplateResponse(
        request,
        "profiles.html",
        {
            "title": "Profiles — Browser Policy Manager",
            "asset_version": _resolve_profiles_asset_version(),
            "footer_year_range": footer_year_range,
            "wizard_settings_catalog": wizard_settings_catalog,
            "wizard_preferences_catalog": wizard_preferences_catalog,
            "wizard_manual_policy_controls": get_manual_policy_controls_catalog(),
            "wizard_starter_catalog": get_wizard_starter_catalog(),
            "wizard_steps": get_wizard_steps(),
            "wizard_schema_shell_catalog": get_wizard_schema_shell_catalog(wizard_preferences_catalog),
            "schema_channels_catalog": build_schema_channels_catalog(),
            "initial_lang": initial_lang,
            "initial_locale": initial_locale,
            "tr": tr,
        },
    )
