from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from sqlalchemy import or_, func
from typing import Optional
import os
import json
from datetime import datetime, timezone

from app.models.db import get_session, PolicyProfile, PolicyVersion
from app.services.policy_service import PolicyService

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "..", "templates")
)

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
    return templates.TemplateResponse(
        request,
        "profile_new.html",
        {
            "defaults": {
                "schema_version": "firefox-ESR",
                "DisableTelemetry": True,
                "DisablePocket": True,
            }
        },
    )


@router.post("/profiles/new")
def profile_new_post(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    schema_version: str = Form(...),
    disable_telemetry: Optional[bool] = Form(False),
    disable_pocket: Optional[bool] = Form(False),
    session: Session = Depends(get_session),
):
    data = {
        "name": name,
        "description": description,
        "schema_version": schema_version,
        "flags": {
            "DisableTelemetry": bool(disable_telemetry),
            "DisablePocket": bool(disable_pocket),
        },
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

    session.add(
        PolicyVersion(profile_id=row.id, author="ui", payload_json=row.payload_json)
    )
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
    flags = {
        "DisableTelemetry": bool(payload.get("policies", {}).get("DisableTelemetry", False)),
        "DisablePocket": bool(payload.get("policies", {}).get("DisablePocket", False)),
    }

    return templates.TemplateResponse(
        request,
        "profile_edit.html",
        {"p": row, "flags": flags},
    )


@router.post("/profiles/{profile_id}/edit")
def profile_edit_post(
    profile_id: int,
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    schema_version: str = Form(...),
    disable_telemetry: Optional[bool] = Form(False),
    disable_pocket: Optional[bool] = Form(False),
    session: Session = Depends(get_session),
):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Profile not found")

    data = {
        "name": name,
        "description": description,
        "schema_version": schema_version,
        "flags": {
            "DisableTelemetry": bool(disable_telemetry),
            "DisablePocket": bool(disable_pocket),
        },
    }
    payload = PolicyService.build_payload(data)

    row.name = name
    row.description = description
    row.active_schema_version = schema_version
    row.payload_json = json.dumps(payload)
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)

    session.add(
        PolicyVersion(profile_id=row.id, author="ui", payload_json=row.payload_json)
    )
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
