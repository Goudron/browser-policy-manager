import json
import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.models.db import PolicyProfile, PolicyVersion, get_session
from app.services.policy_service import PolicyService
from app.services.schema_service import list_schemas

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

router = APIRouter(tags=["web"])


# ============================================================
# LIST + SEARCH
# ============================================================
@router.get("/profiles")
def profiles_list(request: Request, session: Session = Depends(get_session)):
    q: str | None = request.query_params.get("q")

    total_count = session.exec(select(func.count(PolicyProfile.id))).one()

    stmt = select(PolicyProfile).order_by(PolicyProfile.created_at.desc())
    if q:
        stmt = stmt.where(
            or_(
                PolicyProfile.name.contains(q),
                PolicyProfile.description.contains(q),
            )
        )

    rows = session.exec(stmt).all()
    filtered_count = len(rows)

    return templates.TemplateResponse(
        request,
        "profiles_list.html",
        {
            "profiles": rows,
            "q": q,
            "total_count": total_count,
            "filtered_count": filtered_count,
        },
    )


# ============================================================
# CREATE
# ============================================================
@router.get("/profiles/new")
def profile_new_get(request: Request):
    schema_options = list_schemas()
    default_schema = "firefox-release"
    return templates.TemplateResponse(
        request,
        "profile_new.html",
        {
            "schema_options": schema_options,
            "default_schema": default_schema,
        },
    )


@router.post("/profiles/new")
def profile_new_post(
    request: Request,
    name: str = Form(...),
    description: str | None = Form(None),
    schema_version: str = Form(...),
    flags_json: str | None = Form(None),
    doh_enabled: bool | None = Form(False),
    doh_provider_url: str | None = Form(None),
    doh_locked: bool | None = Form(False),
    preferences_json: str | None = Form(None),
    extension_settings_json: str | None = Form(None),
    advanced_json: str | None = Form(None),
    session: Session = Depends(get_session),
):
    # флаги (boolean)
    flags = {}
    if flags_json:
        try:
            flags = json.loads(flags_json)
            flags = {k: bool(v) for k, v in flags.items()}
        except Exception:
            flags = {}

    doh = {
        "Enabled": bool(doh_enabled),
        "ProviderURL": (doh_provider_url or "").strip(),
        "Locked": bool(doh_locked),
    }

    data = {
        "name": name,
        "description": description,
        "schema_version": schema_version,
        "flags": flags,
        "doh": doh,
        "preferences_json": preferences_json,
        "extension_settings_json": extension_settings_json,
        "advanced_json": advanced_json,
    }
    payload = PolicyService.build_payload(data)

    row = PolicyProfile(
        name=name,
        description=description,
        active_schema_version=schema_version,
        payload_json=json.dumps(payload),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    session.add(PolicyVersion(profile_id=row.id, author="ui", payload_json=row.payload_json))
    session.commit()

    return RedirectResponse(url="/profiles", status_code=303)


# ============================================================
# VIEW
# ============================================================
@router.get("/profiles/{profile_id}")
def profile_view(profile_id: int, request: Request, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Profile not found")

    payload = json.loads(row.payload_json)
    return templates.TemplateResponse(
        request,
        "profile_view.html",
        {
            "p": row,
            "payload_pretty": json.dumps(payload, indent=2, ensure_ascii=False),
        },
    )


# ============================================================
# EDIT
# ============================================================
@router.get("/profiles/{profile_id}/edit")
def profile_edit_get(profile_id: int, request: Request, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Profile not found")

    payload = json.loads(row.payload_json)
    pol = payload.get("policies", {}) if isinstance(payload, dict) else {}

    # флаги (только bool)
    flags = {k: v for k, v in pol.items() if isinstance(v, bool)}

    # DoH
    doh = pol.get("DNSOverHTTPS") if isinstance(pol, dict) else {}
    doh_enabled = bool(doh.get("Enabled")) if isinstance(doh, dict) else False
    doh_provider_url = (doh.get("ProviderURL") or "") if isinstance(doh, dict) else ""
    doh_locked = bool(doh.get("Locked")) if isinstance(doh, dict) else False

    # Preferences / ExtensionSettings / Advanced
    preferences_json = (
        json.dumps(pol.get("Preferences", {}), indent=2, ensure_ascii=False)
        if isinstance(pol.get("Preferences"), dict)
        else ""
    )
    extension_settings_json = (
        json.dumps(pol.get("ExtensionSettings", {}), indent=2, ensure_ascii=False)
        if isinstance(pol.get("ExtensionSettings"), dict)
        else ""
    )

    # Advanced нельзя восстановить из уже объединённого payload (мы его просто применяли поверх).
    # Для простоты оставляем пустым; пользователь может добавить новые оверрайды здесь.
    advanced_json = ""

    schema_options = list_schemas()

    return templates.TemplateResponse(
        request,
        "profile_edit.html",
        {
            "p": row,
            "flags": flags,
            "schema_options": schema_options,
            "doh_enabled": doh_enabled,
            "doh_provider_url": doh_provider_url,
            "doh_locked": doh_locked,
            "preferences_json": preferences_json,
            "extension_settings_json": extension_settings_json,
            "advanced_json": advanced_json,
        },
    )


@router.post("/profiles/{profile_id}/edit")
def profile_edit_post(
    profile_id: int,
    request: Request,
    name: str = Form(...),
    description: str | None = Form(None),
    schema_version: str = Form(...),
    flags_json: str | None = Form(None),
    doh_enabled: bool | None = Form(False),
    doh_provider_url: str | None = Form(None),
    doh_locked: bool | None = Form(False),
    preferences_json: str | None = Form(None),
    extension_settings_json: str | None = Form(None),
    advanced_json: str | None = Form(None),
    session: Session = Depends(get_session),
):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Profile not found")

    flags = {}
    if flags_json:
        try:
            flags = json.loads(flags_json)
            flags = {k: bool(v) for k, v in flags.items()}
        except Exception:
            flags = {}

    doh = {
        "Enabled": bool(doh_enabled),
        "ProviderURL": (doh_provider_url or "").strip(),
        "Locked": bool(doh_locked),
    }

    data = {
        "name": name,
        "description": description,
        "schema_version": schema_version,
        "flags": flags,
        "doh": doh,
        "preferences_json": preferences_json,
        "extension_settings_json": extension_settings_json,
        "advanced_json": advanced_json,
    }
    payload = PolicyService.build_payload(data)

    row.name = name
    row.description = description
    row.active_schema_version = schema_version
    row.payload_json = json.dumps(payload)
    row.updated_at = datetime.now(UTC)
    session.add(row)
    session.commit()
    session.refresh(row)

    session.add(PolicyVersion(profile_id=row.id, author="ui", payload_json=row.payload_json))
    session.commit()

    return RedirectResponse(url=f"/profiles/{row.id}", status_code=303)


# ============================================================
# DELETE
# ============================================================
@router.post("/profiles/{profile_id}/delete")
def profile_delete(profile_id: int, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if row:
        session.delete(row)
        session.commit()
    return RedirectResponse(url="/profiles", status_code=303)
