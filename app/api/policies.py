import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.models.db import PolicyProfile, PolicyVersion, get_session
from app.models.dto import PolicyInput, PolicyProfileOut
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.get("", response_model=list[PolicyProfileOut])
def list_profiles(session: Session = Depends(get_session)):
    rows = session.exec(select(PolicyProfile)).all()
    return [
        PolicyProfileOut(
            id=r.id,
            name=r.name,
            description=r.description,
            schema_version=r.active_schema_version,
            payload=json.loads(r.payload_json),
        )
        for r in rows
    ]


@router.post("", response_model=PolicyProfileOut, status_code=201)
def create_profile(body: PolicyInput, session: Session = Depends(get_session)):
    payload = PolicyService.build_payload(body.model_dump())
    row = PolicyProfile(
        name=body.name,
        description=body.description,
        active_schema_version=body.schema_version,
        payload_json=json.dumps(payload),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    session.add(PolicyVersion(profile_id=row.id, author="system", payload_json=row.payload_json))
    session.commit()

    return PolicyProfileOut(
        id=row.id,
        name=row.name,
        description=row.description,
        schema_version=row.active_schema_version,
        payload=payload,
    )


@router.get("/{profile_id}", response_model=PolicyProfileOut)
def get_profile(profile_id: int, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Not found")
    return PolicyProfileOut(
        id=row.id,
        name=row.name,
        description=row.description,
        schema_version=row.active_schema_version,
        payload=json.loads(row.payload_json),
    )


@router.put("/{profile_id}", response_model=PolicyProfileOut)
def update_profile(profile_id: int, body: PolicyInput, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Not found")

    payload = PolicyService.build_payload(body.model_dump())
    row.name = body.name
    row.description = body.description
    row.active_schema_version = body.schema_version
    row.payload_json = json.dumps(payload)
    row.updated_at = datetime.utcnow()

    session.add(row)
    session.commit()
    session.refresh(row)

    session.add(PolicyVersion(profile_id=row.id, author="system", payload_json=row.payload_json))
    session.commit()

    return PolicyProfileOut(
        id=row.id,
        name=row.name,
        description=row.description,
        schema_version=row.active_schema_version,
        payload=payload,
    )


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        return
    session.delete(row)
    session.commit()
