from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.services.schema_service import list_schemas, get_schema, get_boolean_policy_keys

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

@router.get("")
def api_list_schemas():
    return {"schemas": list_schemas()}

@router.get("/{version}")
def api_get_schema(version: str):
    try:
        return get_schema(version)
    except FileNotFoundError:
        raise HTTPException(404, detail="Schema not found")

@router.get("/{version}/booleans")
def api_get_booleans(version: str):
    try:
        return {"booleans": get_boolean_policy_keys(version)}
    except FileNotFoundError:
        raise HTTPException(404, detail="Schema not found")
