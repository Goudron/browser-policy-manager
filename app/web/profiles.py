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
from app.core.firefox_starter_catalog import CIS_LAYER_OPTIONS, STARTER_PRESETS
from app.db import get_session
from app.services.profile_service import ProfileService
from app.web.profile_navigation import (
    build_profile_json_href,
    build_profile_route_path,
    build_profile_settings_href,
    resolve_focus_target,
    resolve_guided_step_target,
    resolve_include_deleted_flag,
    resolve_json_focus_target_from_settings_focus,
    resolve_legacy_guided_step_target,
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
    preparation_mode: str | None = None,
    preparation_terminal_action_mode: str | None = None,
    preparation_source_state: str | None = None,
    preparation_source: dict[str, object] | None = None,
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
        preparation_mode=preparation_mode,
        preparation_terminal_action_mode=preparation_terminal_action_mode,
        preparation_source_state=preparation_source_state,
        preparation_source=preparation_source,
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


def _preparation_starter_label_key(starter_id: str) -> str:
    return {
        "blank": "profiles.wizard_starter_blank_label",
        "keep_current": "profiles.wizard_starter_keep_label",
        "basic_corporate": "profiles.wizard_starter_basic_label",
        "classroom_kiosk": "profiles.wizard_starter_classroom_label",
        "security_hardened": "profiles.wizard_starter_soc_label",
    }.get(starter_id, starter_id)


def _build_preparation_catalog(
    *,
    schema_channels_catalog: dict[str, object],
    starter_catalog: dict[str, object],
) -> dict[str, object]:
    """Expose only preparation identities, never a policy document.

    The dedicated preparation client can choose catalog identities but must not
    receive a browser-composed starter/CIS policy candidate. The server-owned
    preparation commands resolve those identities again at submission time.
    """

    schema_options = schema_channels_catalog.get("options", [])
    if not isinstance(schema_options, list):
        schema_options = []
    compact_schema_options = [
        {
            key: option[key]
            for key in ("value", "label", "i18n_key", "family", "support_state")
            if key in option
        }
        for option in schema_options
        if isinstance(option, dict) and option.get("selectable") is True
    ]

    presets = starter_catalog.get("presets", {})
    preset_ids = tuple(presets) if isinstance(presets, dict) else ()
    compliance_layers = starter_catalog.get("compliance_layers", {})
    if not isinstance(compliance_layers, dict):
        compliance_layers = {}

    return {
        "schema_options": compact_schema_options,
        "starter_options": [
            {
                "id": starter_id,
                "label_key": _preparation_starter_label_key(starter_id),
                "allowed_modes": ["duplicate"]
                if starter_id == "keep_current"
                else ["create", "duplicate"],
            }
            for starter_id in preset_ids
            if starter_id in STARTER_PRESETS
        ],
        "cis_options": [
            {
                "id": cis_id,
                "label_key": layer.get("label_key"),
                "available_schema_versions": layer.get("available_schema_versions", []),
                "unavailable_reason_codes": layer.get("unavailable_reason_codes", {}),
            }
            for cis_id, layer in compliance_layers.items()
            if cis_id in CIS_LAYER_OPTIONS and isinstance(layer, dict)
        ],
    }


@router.get("/profiles", response_class=HTMLResponse)
async def profiles_page(
    request: Request,
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
async def profiles_new_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> HTMLResponse:
    """Render the read-only create/duplicate preparation surface.

    GET only reads a requested source identity. It neither materializes an
    unsaved draft nor loads the Guided editor's policy document into the page.
    """

    raw_clone_source_id = request.query_params.get("clone_from")
    clone_source_id = _resolve_positive_int(raw_clone_source_id)
    preparation_mode = "create"
    preparation_source_state = "absent"
    preparation_source: dict[str, object] | None = None

    if raw_clone_source_id is not None:
        preparation_mode = "duplicate"
        if clone_source_id is None:
            preparation_source_state = "invalid"
        else:
            source = await ProfileService.get(session, clone_source_id, include_deleted=True)
            if source is None:
                preparation_source_state = "not-found"
            elif source.deleted_at is not None:
                preparation_source_state = "archived"
            else:
                preparation_source_state = "available"
                preparation_source = {
                    "id": source.id,
                    "name": source.name,
                    "revision": source.revision,
                    "schema_id": source.schema_version,
                }

    if preparation_mode == "duplicate" and preparation_source is None:
        preparation_terminal_action_mode = "unavailable"
        title = f"Duplicate source unavailable — {settings.APP_NAME}"
    elif preparation_mode == "duplicate":
        preparation_terminal_action_mode = "duplicate"
        assert preparation_source is not None
        title = f"Duplicate {preparation_source['name']} — {settings.APP_NAME}"
    else:
        preparation_terminal_action_mode = "create"
        title = f"Create profile — {settings.APP_NAME}"

    context = _build_profiles_page_context(
        request,
        title=title,
        route_mode="new",
        preparation_mode=preparation_mode,
        preparation_terminal_action_mode=preparation_terminal_action_mode,
        preparation_source_state=preparation_source_state,
        preparation_source=preparation_source,
    )
    schema_channels_catalog = context["schema_channels_catalog"]
    wizard_starter_catalog = context["wizard_starter_catalog"]
    assert isinstance(schema_channels_catalog, dict)
    assert isinstance(wizard_starter_catalog, dict)
    context["preparation_catalog"] = _build_preparation_catalog(
        schema_channels_catalog=schema_channels_catalog,
        starter_catalog=wizard_starter_catalog,
    )

    return templates.TemplateResponse(
        request,
        "profiles_preparation.html",
        context,
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
    focus_target = (
        resolve_focus_target(request.query_params.get("focus"))
        or resolve_guided_step_target(request.query_params.get("step"))
        or resolve_legacy_guided_step_target(request.query_params.get("legacy_step"))
    )
    duplicate_requested = request.query_params.get("duplicate", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

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
            focus_target=focus_target,
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
