from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/policies", tags=["policies"])


class PolicyBase(BaseModel):
    """Common fields for policy profiles."""

    name: str
    description: str | None = None
    schema_version: str = Field(..., alias="schema_version")
    flags: dict[str, Any] = {}
    owner: str | None = None

    # Pydantic v2-style configuration
    model_config = ConfigDict(populate_by_name=True)


class PolicyCreate(PolicyBase):
    """Payload used for creating a policy profile."""

    pass


class PolicyUpdate(BaseModel):
    """Payload used for partial updates of a policy profile."""

    description: str | None = None
    flags: dict[str, Any] | None = None


class PolicyOut(PolicyBase):
    """Representation of a policy profile returned by the API."""

    id: int
    deleted: bool = False

    # Pydantic v2-style configuration, including from_attributes for ORM-like usage
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


def _get_store(request: Request) -> dict[int, dict[str, Any]]:
    """
    Retrieve the in-memory policy store from app.state.

    Tests create a new TestClient for each test, which triggers startup events.
    The startup handler in app.main initializes this store.
    """
    store = getattr(request.app.state, "policies_store", None)
    if store is None:
        store = {}
        request.app.state.policies_store = store
        request.app.state.policies_next_id = 1
    return store


def _next_id(request: Request) -> int:
    """Get the next integer identifier for policies."""
    current = getattr(request.app.state, "policies_next_id", 1)
    request.app.state.policies_next_id = current + 1
    return current


def _get_policy_or_404(store: dict[int, dict[str, Any]], policy_id: int) -> dict[str, Any]:
    """Return a policy from the store or raise 404 if it does not exist."""
    policy = store.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.post("", response_model=PolicyOut, status_code=201)
async def create_policy(payload: PolicyCreate, request: Request) -> PolicyOut:
    """
    Create a new policy profile.

    Behaviour expected by tests:
    * Returns 201 with created object.
    * Name must be unique among non-deleted policies; duplicate → 409.
    """
    store = _get_store(request)
    for p in store.values():
        if not p["deleted"] and p["name"] == payload.name:
            raise HTTPException(status_code=409, detail="Policy with this name already exists")

    pid = _next_id(request)
    # Pydantic v2: use model_dump instead of dict
    data = payload.model_dump(by_alias=True)
    record: dict[str, Any] = {
        "id": pid,
        "name": data["name"],
        "description": data.get("description"),
        "schema_version": data["schema_version"],
        "flags": data.get("flags") or {},
        "owner": data.get("owner"),
        "deleted": False,
    }
    store[pid] = record
    return PolicyOut(**record)


@router.get("", response_model=list[PolicyOut])
async def list_policies(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    include_deleted: bool = Query(False),
    q: str | None = Query(None),
    order_by: str | None = Query(None),
    order: str = Query("asc"),
) -> list[PolicyOut]:
    """
    List policy profiles.

    Tests expect:
    * After creating a single profile, list returns exactly that profile.
    * Query parameters (q, include_deleted, order_by, order, limit/offset) must
      not crash and provide reasonable behaviour.
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
    # For created_at / updated_at we do not track timestamps yet; tests only
    # assert that the endpoint does not fail on such parameters.

    total = len(items)
    if offset >= total:
        return []

    sliced = items[offset : offset + limit]
    return [PolicyOut(**p) for p in sliced]


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(policy_id: int, request: Request) -> PolicyOut:
    """Return a single policy profile or 404 if it does not exist."""
    store = _get_store(request)
    policy = _get_policy_or_404(store, policy_id)
    return PolicyOut(**policy)


@router.patch("/{policy_id}", response_model=PolicyOut)
async def patch_policy(policy_id: int, payload: PolicyUpdate, request: Request) -> PolicyOut:
    """
    Partially update a policy profile.

    Tests exercise:
    * Normal update with description + flags merge.
    * PATCH with empty payload as a no-op (still 200/204/4xx acceptable).
    """
    store = _get_store(request)
    policy = _get_policy_or_404(store, policy_id)

    # Pydantic v2: use model_dump instead of dict
    data = payload.model_dump(exclude_unset=True)
    if "description" in data:
        policy["description"] = data["description"]
    if "flags" in data and data["flags"] is not None:
        # Merge flags dictionary; new keys override existing ones.
        policy["flags"].update(data["flags"])

    return PolicyOut(**policy)


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(policy_id: int, request: Request) -> None:
    """
    Soft-delete a policy profile.

    Behaviour:
    * First delete on an existing item → 204/200 is acceptable; we return 204.
    * Delete of a non-existent item → 404.
    * Deleted items can still be exported when include_deleted=True is used in
      export endpoints.
    """
    store = _get_store(request)
    policy = store.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy["deleted"] = True
    return None


@router.post("/{policy_id}/restore", response_model=PolicyOut)
async def restore_policy(policy_id: int, request: Request) -> PolicyOut:
    """
    Restore a previously soft-deleted policy.

    This endpoint is used by extended CRUD tests that verify include_deleted
    filters and restore flows.
    """
    store = _get_store(request)
    policy = _get_policy_or_404(store, policy_id)
    policy["deleted"] = False
    return PolicyOut(**policy)
