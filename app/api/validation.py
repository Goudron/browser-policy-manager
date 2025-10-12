from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.services.schema_service import validate_policy

router = APIRouter(prefix="/policies", tags=["policies"])

@router.post("/validate")
def validate(doc: dict, channel: str | None = Query(None), version: str | None = Query(None)):
    ok, err = validate_policy(doc, channel=channel, version=version)
    if not ok:
        raise HTTPException(status_code=422, detail={"message": "Schema validation failed", "error": err})
    return {"ok": True}
