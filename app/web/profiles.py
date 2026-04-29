# app/web/profiles.py
# Web router for the Profiles management page with Monaco JSON/YAML editor.

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.schema_channels import build_schema_channels_catalog
from app.db import get_session
from app.services.profile_service import ProfileService
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


def _build_profiles_page_context(
    request: Request,
    *,
    title: str,
    route_mode: str,
    editing_profile_id: int | None = None,
    return_url: str | None = None,
    focus_target: str | None = None,
    advanced_href: str | None = None,
) -> dict[str, object]:
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

    return {
        "title": title,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "asset_version": _resolve_profiles_asset_version(),
        "footer_year_range": footer_year_range,
        "profiles_route_mode": route_mode,
        "editing_profile_id": editing_profile_id,
        "return_url": return_url,
        "focus_target": focus_target,
        "advanced_href": advanced_href,
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
    }


def _resolve_safe_profiles_return_url(raw_return_url: str | None) -> str | None:
    if not raw_return_url:
        return None
    if not raw_return_url.startswith("/profiles"):
        return None
    if raw_return_url.startswith("//") or "://" in raw_return_url:
        return None
    return raw_return_url


def _resolve_focus_target(raw_focus_target: str | None) -> str | None:
    if not raw_focus_target:
        return None
    focus_target = raw_focus_target.strip()
    if not focus_target or len(focus_target) > 160:
        return None
    return focus_target


def _build_profile_advanced_href(
    profile_id: int,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
) -> str:
    params: list[str] = []
    if return_url:
        params.append(f"return={quote(return_url, safe='/')}")
    if focus_target:
        params.append(f"focus={quote(focus_target, safe=':-_')}")
    suffix = f"?{'&'.join(params)}" if params else ""
    return f"/profiles/{profile_id}/advanced{suffix}"


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request) -> HTMLResponse:
    """Render the profile library page."""
    return templates.TemplateResponse(
        request,
        "profiles_library.html",
        _build_profiles_page_context(
            request,
            title=f"Profile library — {settings.APP_NAME}",
            route_mode="library",
        ),
    )


@router.get("/profiles/new", response_class=HTMLResponse)
async def profiles_new_page(request: Request) -> HTMLResponse:
    """Render the visual wizard shell for a new profile draft."""
    return templates.TemplateResponse(
        request,
        "profiles_editor.html",
        _build_profiles_page_context(
            request,
            title=f"New profile draft — {settings.APP_NAME}",
            route_mode="new",
        ),
    )


@router.get("/profiles/{profile_id}/edit", response_class=HTMLResponse)
async def profiles_edit_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the visual wizard shell for an existing profile."""
    profile = await ProfileService.get(session, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return templates.TemplateResponse(
        request,
        "profiles_editor.html",
        _build_profiles_page_context(
            request,
            title=f"{profile.name} — Profile editor — {settings.APP_NAME}",
            route_mode="edit",
            editing_profile_id=profile_id,
            advanced_href=_build_profile_advanced_href(
                profile_id,
                return_url=f"/profiles/{profile_id}/edit",
            ),
        ),
    )


@router.get("/profiles/{profile_id}/advanced", response_class=HTMLResponse)
async def profiles_advanced_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the advanced policy document editor for an existing profile."""
    profile = await ProfileService.get(session, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return_url = _resolve_safe_profiles_return_url(request.query_params.get("return"))
    focus_target = _resolve_focus_target(request.query_params.get("focus"))

    return templates.TemplateResponse(
        request,
        "profiles_advanced.html",
        _build_profiles_page_context(
            request,
            title=f"{profile.name} — Advanced editor — {settings.APP_NAME}",
            route_mode="advanced",
            editing_profile_id=profile_id,
            return_url=return_url,
            focus_target=focus_target,
        ),
    )
