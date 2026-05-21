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
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.schema_channels import build_schema_channels_catalog
from app.db import get_session
from app.services.profile_service import ProfileService
from app.web.firefox_all_settings_categories import get_all_settings_category_catalog
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
    editing_profile_schema_version: str | None = None,
    editing_profile_initial: dict[str, object] | None = None,
    include_deleted: bool = False,
    return_url: str | None = None,
    focus_target: str | None = None,
    advanced_href: str | None = None,
    settings_href: str | None = None,
    json_href: str | None = None,
    clone_source_id: int | None = None,
) -> dict[str, object]:
    current_year = datetime.now(UTC).year
    footer_year_range = "2025" if current_year <= 2025 else f"2025-{current_year}"
    wizard_settings_catalog = get_wizard_settings_catalog()
    wizard_preferences_catalog = get_wizard_preferences_catalog(wizard_settings_catalog)
    wizard_schema_shell_catalog = get_wizard_schema_shell_catalog(wizard_preferences_catalog)
    all_settings_category_catalog = get_all_settings_category_catalog()
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
        "editing_profile_schema_version": editing_profile_schema_version,
        "editing_profile_initial": editing_profile_initial,
        "include_deleted": include_deleted,
        "return_url": return_url,
        "focus_target": focus_target,
        "advanced_href": advanced_href,
        "settings_href": settings_href,
        "json_href": json_href,
        "clone_source_id": clone_source_id,
        "wizard_settings_catalog": wizard_settings_catalog,
        "wizard_preferences_catalog": wizard_preferences_catalog,
        "wizard_preferences_sections_by_id": {
            section["id"]: section
            for section in wizard_preferences_catalog.get("sections", [])
            if isinstance(section, dict) and section.get("id")
        },
        "wizard_manual_policy_controls": get_manual_policy_controls_catalog(),
        "wizard_starter_catalog": get_wizard_starter_catalog(),
        "wizard_steps": get_wizard_steps(),
        "wizard_schema_shell_catalog": wizard_schema_shell_catalog,
        "all_settings_category_catalog": all_settings_category_catalog,
        "settings_shell_step_to_open": _resolve_settings_shell_focus_step(
            focus_target,
            editing_profile_schema_version,
            wizard_schema_shell_catalog,
        ),
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


def _resolve_include_deleted_flag(raw_include_deleted: str | None) -> bool:
    if raw_include_deleted is None:
        return False
    return raw_include_deleted.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_positive_int(raw_value: str | None) -> int | None:
    if raw_value is None:
        return None
    try:
        value = int(raw_value)
    except ValueError:
        return None
    return value if value > 0 else None


def _resolve_settings_shell_focus_step(
    focus_target: str | None,
    schema_version: str | None,
    wizard_schema_shell_catalog: dict[str, object] | None = None,
) -> int | None:
    normalized_focus = (focus_target or "").strip()
    if not normalized_focus:
        return None
    if normalized_focus == "settings-schema-shell-step-8":
        return 8
    if normalized_focus.startswith("shell-policy:"):
        parts = normalized_focus.split(":", 2)
        if len(parts) >= 3:
            try:
                return int(parts[1])
            except ValueError:
                return None
    if (
        normalized_focus in {"raw", "deprecated", "unknown"}
        or normalized_focus.startswith("raw:")
        or normalized_focus.startswith("deprecated:")
        or normalized_focus.startswith("unknown:")
    ):
        return 8
    if not normalized_focus.startswith("policy:") or not schema_version:
        return None

    policy_id = normalized_focus.split(":", 1)[1].strip()
    if not policy_id:
        return None

    shell_catalog = wizard_schema_shell_catalog or get_wizard_schema_shell_catalog(
        get_wizard_preferences_catalog(get_wizard_settings_catalog())
    )
    channels = shell_catalog.get("channels", {})
    if not isinstance(channels, dict):
        return None
    channel_data = channels.get(schema_version, {})
    if not isinstance(channel_data, dict):
        return None
    channel_steps = channel_data.get("steps", {})
    if not isinstance(channel_steps, dict):
        return None
    for step_key, step_data in channel_steps.items():
        if not isinstance(step_data, dict):
            continue
        items = [
            *(step_data.get("recommended") or []),
            *(step_data.get("additional") or []),
            *(step_data.get("raw_fallback") or []),
        ]
        if any(item.get("id") == policy_id for item in items if isinstance(item, dict)):
            try:
                return int(step_key)
            except (TypeError, ValueError):
                return None
    return None


def _resolve_json_focus_target_from_settings_focus(
    focus_target: str | None,
) -> str | None:
    if not focus_target:
        return None
    normalized_focus = focus_target.strip()
    if not normalized_focus:
        return None
    if normalized_focus.startswith("policy:"):
        return normalized_focus
    if normalized_focus == "settings-schema-shell-step-8":
        return "raw"
    return None


def _resolve_settings_focus_target_from_json_focus(
    focus_target: str | None,
) -> str | None:
    if not focus_target:
        return None
    normalized_focus = focus_target.strip()
    if not normalized_focus or normalized_focus == "editor":
        return None
    if normalized_focus.startswith("policy:"):
        return normalized_focus
    if (
        normalized_focus in {"details", "download", "context", "raw", "deprecated", "unknown"}
        or normalized_focus.startswith("raw:")
        or normalized_focus.startswith("deprecated:")
        or normalized_focus.startswith("unknown:")
    ):
        return "settings-schema-shell-step-8"
    return normalized_focus


def _build_profile_json_href(
    profile_id: int,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
    include_deleted: bool = False,
) -> str:
    params: list[str] = []
    if include_deleted:
        params.append("include_deleted=true")
    if return_url:
        params.append(f"return={quote(return_url, safe='/')}")
    if focus_target:
        params.append(f"focus={quote(focus_target, safe=':-_')}")
    suffix = f"?{'&'.join(params)}" if params else ""
    return f"/profiles/{profile_id}/json{suffix}"


def _build_profile_advanced_href(
    profile_id: int,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
    include_deleted: bool = False,
) -> str:
    """Compatibility builder kept temporarily while `/advanced` redirects to `/json`."""
    params: list[str] = []
    if include_deleted:
        params.append("include_deleted=true")
    if return_url:
        params.append(f"return={quote(return_url, safe='/')}")
    if focus_target:
        params.append(f"focus={quote(focus_target, safe=':-_')}")
    suffix = f"?{'&'.join(params)}" if params else ""
    return f"/profiles/{profile_id}/advanced{suffix}"


def _build_profile_settings_href(
    profile_id: int,
    *,
    return_url: str | None = None,
    focus_target: str | None = None,
    include_deleted: bool = False,
) -> str:
    params: list[str] = []
    if include_deleted:
        params.append("include_deleted=true")
    if return_url:
        params.append(f"return={quote(return_url, safe='/')}")
    if focus_target:
        params.append(f"focus={quote(focus_target, safe=':-_')}")
    suffix = f"?{'&'.join(params)}" if params else ""
    return f"/profiles/{profile_id}/settings{suffix}"


def _build_profile_route_path(
    profile_id: int,
    mode: str,
    *,
    include_deleted: bool = False,
) -> str:
    if mode == "settings":
        base_path = f"/profiles/{profile_id}/settings"
    elif mode == "json":
        base_path = f"/profiles/{profile_id}/json"
    else:
        base_path = f"/profiles/{profile_id}/edit"
    return f"{base_path}?include_deleted=true" if include_deleted else base_path


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request) -> HTMLResponse:
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


@router.get("/profiles/new", response_class=HTMLResponse)
async def profiles_new_page(request: Request) -> HTMLResponse:
    """Render the visual wizard shell for a new profile draft."""
    clone_source_id = _resolve_positive_int(request.query_params.get("clone_from"))
    include_deleted = _resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    return templates.TemplateResponse(
        request,
        "profiles_editor.html",
        _build_profiles_page_context(
            request,
            title=f"New profile draft — Guided editor — {settings.APP_NAME}",
            route_mode="new",
            include_deleted=include_deleted,
            clone_source_id=clone_source_id,
        ),
    )


@router.get("/profiles/{profile_id}/edit", response_class=HTMLResponse)
async def profiles_edit_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the visual wizard shell for an existing profile."""
    include_deleted = _resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    current_route = _build_profile_route_path(profile_id, "edit", include_deleted=include_deleted)
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
            settings_href=_build_profile_settings_href(
                profile_id,
                return_url=current_route,
                include_deleted=include_deleted,
            ),
            json_href=_build_profile_json_href(
                profile_id,
                return_url=current_route,
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
    include_deleted = _resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return_url = _resolve_safe_profiles_return_url(request.query_params.get("return"))
    focus_target = _resolve_focus_target(request.query_params.get("focus"))
    current_route = _build_profile_route_path(profile_id, "settings", include_deleted=include_deleted)

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
            settings_href=_build_profile_settings_href(
                profile_id,
                return_url=return_url,
                focus_target=focus_target,
                include_deleted=include_deleted,
            ),
            json_href=_build_profile_json_href(
                profile_id,
                return_url=current_route,
                focus_target=_resolve_json_focus_target_from_settings_focus(focus_target)
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
    include_deleted = _resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return_url = _resolve_safe_profiles_return_url(request.query_params.get("return"))
    focus_target = _resolve_focus_target(request.query_params.get("focus"))
    current_route = _build_profile_route_path(profile_id, "json", include_deleted=include_deleted)

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
            settings_href=_build_profile_settings_href(
                profile_id,
                return_url=current_route,
                focus_target=_resolve_settings_focus_target_from_json_focus(focus_target),
                include_deleted=include_deleted,
            ),
            json_href=_build_profile_json_href(
                profile_id,
                return_url=current_route,
                focus_target="editor",
                include_deleted=include_deleted,
            ),
        ),
    )


@router.get("/profiles/{profile_id}/advanced", response_class=HTMLResponse)
async def profiles_advanced_page(
    request: Request,
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RedirectResponse:
    """Compatibility route that redirects the old advanced editor URL to `/json`."""
    include_deleted = _resolve_include_deleted_flag(request.query_params.get("include_deleted"))
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    redirect_href = _build_profile_json_href(
        profile_id,
        return_url=_resolve_safe_profiles_return_url(request.query_params.get("return")),
        focus_target=_resolve_focus_target(request.query_params.get("focus")),
        include_deleted=include_deleted,
    )
    return RedirectResponse(url=redirect_href, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
