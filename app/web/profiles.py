# app/web/profiles.py
# Web router for the Profiles management page with Monaco JSON/YAML editor.

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_session
from app.services.profile_service import ProfileService
from app.web.profile_navigation import (
    build_profile_json_href,
    build_profile_route_path,
    build_profile_settings_href,
    resolve_focus_target,
    resolve_include_deleted_flag,
    resolve_json_focus_target_from_settings_focus,
    resolve_safe_profiles_return_url,
    resolve_settings_focus_target_from_json_focus,
    resolve_settings_shell_focus_step,
)
from app.web.profiles_context import (
    build_profiles_page_context,
    clear_locale_catalog_cache,
    load_locale_catalog,
    resolve_profiles_asset_version,
    resolve_request_locale,
)

router = APIRouter(tags=["web"])

settings = get_settings()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


def _load_locale_catalog(locale: str) -> dict[str, str]:
    return load_locale_catalog(locale, settings)


_load_locale_catalog.cache_clear = clear_locale_catalog_cache  # type: ignore[attr-defined]


def _resolve_profiles_asset_version() -> str:
    return resolve_profiles_asset_version(settings)


def _resolve_request_locale(request: Request) -> str:
    return resolve_request_locale(request, settings)


def _build_profiles_page_context(
    request: Request,
    *,
    title: str,
    route_mode: str,
    editing_profile_id: int | None = None,
    editing_profile_schema_version: str | None = None,
    editing_profile_initial: dict[str, object] | None = None,
    include_deleted: bool = False,
    return_url: str | None = None,
    focus_target: str | None = None,
    settings_href: str | None = None,
    json_href: str | None = None,
    clone_source_id: int | None = None,
    clone_name: str | None = None,
) -> dict[str, object]:
    return build_profiles_page_context(
        request,
        settings_obj=settings,
        settings_shell_focus_resolver=resolve_settings_shell_focus_step,
        now=datetime.now(UTC),
        title=title,
        route_mode=route_mode,
        editing_profile_id=editing_profile_id,
        editing_profile_schema_version=editing_profile_schema_version,
        editing_profile_initial=editing_profile_initial,
        include_deleted=include_deleted,
        return_url=return_url,
        focus_target=focus_target,
        settings_href=settings_href,
        json_href=json_href,
        clone_source_id=clone_source_id,
        clone_name=clone_name,
    )


def _resolve_positive_int(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    try:
        value = int(raw_value)
    except ValueError:
        return None
    return value if value > 0 else None


def _resolve_clone_name(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the profile library page."""
    return templates.TemplateResponse(
        request,
        "profiles_library.html",
        _build_profiles_page_context(
            request,
            title=f"Library — {settings.APP_NAME}",
            route_mode="library",
        ),
    )


@router.get("/profiles/compare", response_class=HTMLResponse)
async def profiles_compare_page(request: Request) -> HTMLResponse:
    """Render the dedicated saved-profile comparison shell."""
    return templates.TemplateResponse(
        request,
        "profiles_compare.html",
        _build_profiles_page_context(
            request,
            title=f"Compare profile settings — {settings.APP_NAME}",
            route_mode="compare",
        ),
    )


@router.get("/profiles/new", response_class=HTMLResponse)
async def profiles_new_page(request: Request) -> HTMLResponse:
    """Render the visual wizard shell for a new profile draft."""
    clone_source_id = _resolve_positive_int(request.query_params.get("clone_from"))
    clone_name = _resolve_clone_name(request.query_params.get("clone_name"))
    include_deleted = resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    return templates.TemplateResponse(
        request,
        "profiles_editor.html",
        _build_profiles_page_context(
            request,
            title=f"New profile draft — Guided editor — {settings.APP_NAME}",
            route_mode="new",
            include_deleted=include_deleted,
            clone_source_id=clone_source_id,
            clone_name=clone_name,
        ),
    )


@router.get("/profiles/{profile_id}/edit", response_class=HTMLResponse)
async def profiles_edit_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the visual wizard shell for an existing profile."""
    include_deleted = resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    current_route = build_profile_route_path(profile_id, "edit", include_deleted=include_deleted)
    duplicate_requested = request.query_params.get("duplicate", "").strip().lower() in {"1", "true", "yes", "on"}

    return templates.TemplateResponse(
        request,
        "profiles_editor.html",
        _build_profiles_page_context(
            request,
            title=f"{profile.name} — Guided editor — {settings.APP_NAME}",
            route_mode="edit",
            editing_profile_id=profile_id,
            editing_profile_schema_version=profile.schema_version,
            editing_profile_initial=profile.model_dump(mode="json"),
            include_deleted=include_deleted,
            settings_href=build_profile_settings_href(
                profile_id,
                return_url=current_route,
                include_deleted=include_deleted,
            ),
            json_href=build_profile_json_href(
                profile_id,
                focus_target="editor",
                include_deleted=include_deleted,
            ),
            clone_source_id=profile_id if duplicate_requested else None,
        ),
    )


@router.get("/profiles/{profile_id}/settings", response_class=HTMLResponse)
async def profiles_settings_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the All settings shell for an existing profile."""
    include_deleted = resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return_url = resolve_safe_profiles_return_url(request.query_params.get("return"))
    focus_target = resolve_focus_target(request.query_params.get("focus"))
    return templates.TemplateResponse(
        request,
        "profiles_settings.html",
        _build_profiles_page_context(
            request,
            title=f"{profile.name} — All settings — {settings.APP_NAME}",
            route_mode="settings",
            editing_profile_id=profile_id,
            editing_profile_schema_version=profile.schema_version,
            editing_profile_initial=profile.model_dump(mode="json"),
            include_deleted=include_deleted,
            return_url=return_url,
            focus_target=focus_target,
            settings_href=build_profile_settings_href(
                profile_id,
                return_url=return_url,
                focus_target=focus_target,
                include_deleted=include_deleted,
            ),
            json_href=build_profile_json_href(
                profile_id,
                focus_target=resolve_json_focus_target_from_settings_focus(focus_target)
                or "editor",
                include_deleted=include_deleted,
            ),
        ),
    )


@router.get("/profiles/{profile_id}/json", response_class=HTMLResponse)
async def profiles_json_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the JSON policy document editor for an existing profile."""
    include_deleted = resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return_url = resolve_safe_profiles_return_url(request.query_params.get("return"))
    focus_target = resolve_focus_target(request.query_params.get("focus"))
    current_route = build_profile_route_path(profile_id, "json", include_deleted=include_deleted)

    return templates.TemplateResponse(
        request,
        "profiles_json.html",
        _build_profiles_page_context(
            request,
            title=f"{profile.name} — JSON editor — {settings.APP_NAME}",
            route_mode="json",
            editing_profile_id=profile_id,
            editing_profile_schema_version=profile.schema_version,
            editing_profile_initial=profile.model_dump(mode="json"),
            include_deleted=include_deleted,
            return_url=return_url,
            focus_target=focus_target,
            settings_href=build_profile_settings_href(
                profile_id,
                return_url=current_route,
                focus_target=resolve_settings_focus_target_from_json_focus(focus_target),
                include_deleted=include_deleted,
            ),
            json_href=build_profile_json_href(
                profile_id,
                return_url=current_route,
                focus_target="editor",
                include_deleted=include_deleted,
            ),
        ),
    )
