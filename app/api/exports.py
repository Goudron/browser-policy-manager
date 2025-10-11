from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session
from app.models.db import PolicyProfile, get_session
import json

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/{profile_id}/policies.json")
def export_policies(profile_id: int, session: Session = Depends(get_session)):
    row = session.get(PolicyProfile, profile_id)
    if not row:
        raise HTTPException(404, "Not found")
    return JSONResponse(content=json.loads(row.payload_json))
