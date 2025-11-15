from __future__ import annotations

import json
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Query, Request, Response

from .policies import _get_policy_or_404, _get_store

router = APIRouter(prefix="/api/export", tags=["export"])


def _serialize(policy: dict[str, Any]) -> dict[str, Any]:
    """Serialize internal policy dict to a public representation."""
    return {
        "id": policy["id"],
        "name": policy["name"],
        "description": policy["description"],
        "schema_version": policy["schema_version"],
        "flags": policy["flags"],
        "owner": policy["owner"],
        "deleted": policy["deleted"],
    }


def _build_envelope(
    items: list[dict[str, Any]],
    limit: int,
    offset: int,
    total: int,
) -> dict[str, Any]:
    """
    Build a collection envelope.

    Tests expect an object with at least "items", "limit", "offset" and "count"
    for collection exports.
    """
    return {
        "items": [_serialize(p) for p in items],
        "limit": limit,
        "offset": offset,
        "count": total,
    }


def _to_yaml(data: Any) -> str:
    """Serialize data to YAML in a readable form."""
    return yaml.safe_dump(data, sort_keys=False)


@router.get("/policies")
async def export_collection(
    request: Request,
    fmt: str = Query("json"),
    download: int = Query(0, ge=0, le=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_deleted: bool = Query(False),
    q: str | None = Query(None),
    order_by: str | None = Query(None),
    order: str = Query("asc"),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """
    Export a collection of policies.

    This endpoint is heavily exercised by tests with various combinations of:
    * fmt=json|yaml
    * download=0|1 (Content-Disposition header)
    * indent / pretty
    * include_deleted, q, limit/offset, order_by, order
    """
    store = _get_store(request)
    items = list(store.values())

    if not include_deleted:
        items = [p for p in items if not p["deleted"]]

    if q:
        q_lower = q.lower()
        items = [p for p in items if q_lower in p["name"].lower()]

    if order_by == "name":
        reverse = order.lower() == "desc"
        items.sort(key=lambda p: p["name"], reverse=reverse)

    total = len(items)
    sliced = items[offset : offset + limit]
    envelope = _build_envelope(sliced, limit=limit, offset=offset, total=total)

    headers: dict[str, str] = {}

    if fmt == "yaml":
        if download:
            headers["Content-Disposition"] = 'attachment; filename="policies.yaml"'
        body = _to_yaml(envelope)
        return Response(content=body, media_type="application/x-yaml", headers=headers)

    # Default JSON
    if indent is None and pretty:
        indent = 2
    body_json = json.dumps(envelope, indent=indent)
    if download:
        headers["Content-Disposition"] = 'attachment; filename="policies.json"'
    return Response(content=body_json, media_type="application/json", headers=headers)


@router.get("/{policy_id}/policies.json")
async def export_single_json_suffix(
    policy_id: int,
    request: Request,
    download: int = Query(0, ge=0, le=1),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """
    Export a single policy as JSON using suffix route:

        /api/export/{id}/policies.json

    Tests combine this with download, indent and pretty query parameters.
    """
    store = _get_store(request)
    policy = _get_policy_or_404(store, policy_id)

    if indent is None and pretty:
        indent = 2

    body_json = json.dumps(_serialize(policy), indent=indent)
    headers: dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="policy-{policy_id}.json"'
    return Response(content=body_json, media_type="application/json", headers=headers)


@router.get("/{policy_id}/policies.yaml")
async def export_single_yaml_suffix(
    policy_id: int,
    request: Request,
    download: int = Query(0, ge=0, le=1),
) -> Response:
    """
    Export a single policy as YAML using suffix route:

        /api/export/{id}/policies.yaml
    """
    store = _get_store(request)
    policy = _get_policy_or_404(store, policy_id)

    body = _to_yaml(_serialize(policy))
    headers: dict[str, str] = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="policy-{policy_id}.yaml"'
    return Response(content=body, media_type="application/x-yaml", headers=headers)


@router.get("/policies/{policy_id}")
async def export_single_queryparam(
    policy_id: int,
    request: Request,
    fmt: str = Query("json"),
    include_deleted: bool = Query(False),
    download: int = Query(0, ge=0, le=1),
    indent: int | None = Query(None, ge=0),
    pretty: int = Query(0, ge=0, le=1),
) -> Response:
    """
    Export a single policy using the query-parameter route:

        /api/export/policies/{id}?fmt={json|yaml}&include_deleted=true|false...

    Tests also cover 404 behaviour when include_deleted is false and the item
    has been soft-deleted.
    """
    store = _get_store(request)
    policy = store.get(policy_id)
    if policy is None or (policy["deleted"] and not include_deleted):
        raise HTTPException(status_code=404, detail="Policy not found")

    headers: dict[str, str] = {}

    if fmt == "yaml":
        body = _to_yaml(_serialize(policy))
        if download:
            headers["Content-Disposition"] = f'attachment; filename="policy-{policy_id}.yaml"'
        return Response(content=body, media_type="application/x-yaml", headers=headers)

    # Default JSON
    if indent is None and pretty:
        indent = 2
    body_json = json.dumps(_serialize(policy), indent=indent)
    if download:
        headers["Content-Disposition"] = f'attachment; filename="policy-{policy_id}.json"'
    return Response(content=body_json, media_type="application/json", headers=headers)
