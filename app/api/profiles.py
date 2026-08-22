from __future__ import annotations

import asyncio
import json
import secrets
import threading
from contextlib import suppress
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.profile_conversion_compliance import recompute_pinned_cis_compliance
from app.core.policy_validation import (
    PolicyValidationError,
    validate_profile_payload_with_schema,
)
from app.core.profile_conversion_planner import (
    ConversionPlanningError,
    plan_profile_conversion,
)
from app.core.schema_channels import DEFAULT_SCHEMA_CHANNEL, SchemaChannelError, get_schema_channel
from app.db import get_session
from app.schemas.profile import (
    ConversionApplyErrorEnvelope,
    ConversionApplyRequest,
    ConversionApplyResponse,
    ConversionPreviewErrorEnvelope,
    ConversionPreviewRequest,
    ConversionPreviewResponse,
    DuplicateProfilePreparationPreview,
    DuplicateProfilePreparationPreviewRequest,
    DuplicateProfilePreparationRequest,
    NewProfilePreparationRequest,
    ProfileCreate,
    ProfilePreparationErrorEnvelope,
    ProfileRead,
    ProfileUpdate,
    ProfileUpdateConflictErrorEnvelope,
)
from app.services.amo_search import AmoSearchAdapter, AmoSearchResult
from app.services.firefox_policy_import import (
    FirefoxPoliciesDocumentValidationError,
    FirefoxPoliciesImportError,
    validate_firefox_policies_document,
)
from app.services.profile_service import (
    ConversionApplyFailure,
    ConversionApplyOutcome,
    DuplicateProfilePreparationFailure,
    NewProfilePreparationFailure,
    ProfilePageResult,
    ProfileService,
)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

AMO_SEARCH_SESSION_COOKIE = "bpm_amo_search_session"
AMO_SEARCH_SESSION_COOKIE_PATH = "/api/profiles/extensions/amo-search"
AMO_SEARCH_SESSION_MINIMUM_LENGTH = 20
AMO_SEARCH_SESSION_MAXIMUM_LENGTH = 128
AMO_SEARCH_CACHE_CONTROL = "no-store, max-age=0"


class AmoSearchApiResult(BaseModel):
    """Inert values that may be returned from the fixed AMO projection only."""

    guid: str = Field(description="Verified Firefox extension GUID.")
    name: str = Field(description="Plain localized extension name.")
    version: str = Field(description="Plain extension version label.")


class AmoSearchApiResponse(BaseModel):
    """Same-origin AMO lookup state; unavailable always keeps manual entry possible."""

    availability: Literal["available", "unavailable"]
    reason_code: str = Field(
        description=(
            "Stable value-free availability code. It never contains the lookup, locale, "
            "provider response or transport detail."
        )
    )
    results: list[AmoSearchApiResult] = Field(
        default_factory=list,
        description="At most ten normalized text-only extension identities.",
    )
    cache_hit: bool = Field(
        description="Whether this browser session used its private fresh cache."
    )


def _amo_search_adapter(request: Request) -> AmoSearchAdapter:
    """Read the process-local adapter without accepting any caller transport or upstream URL."""

    adapter = getattr(request.app.state, "amo_search_adapter", None)
    return adapter if isinstance(adapter, AmoSearchAdapter) else AmoSearchAdapter()


def _amo_search_request_is_same_origin(request: Request) -> bool:
    """Allow browser fetches from this origin only; cross-site GETs must not start AMO work."""

    return request.headers.get("sec-fetch-site", "").casefold() == "same-origin"


def _amo_search_session_secret(request: Request) -> tuple[str, bool]:
    """Issue one opaque session-only cookie without exposing it to JavaScript or AMO."""

    presented = request.cookies.get(AMO_SEARCH_SESSION_COOKIE)
    if (
        isinstance(presented, str)
        and AMO_SEARCH_SESSION_MINIMUM_LENGTH <= len(presented) <= AMO_SEARCH_SESSION_MAXIMUM_LENGTH
    ):
        return presented, False
    session_secret = secrets.token_urlsafe(32)
    return session_secret, True


def _set_amo_search_session_cookie(
    request: Request, response: Response, session_secret: str
) -> None:
    """Keep the opaque browser-session cache key out of JavaScript and AMO requests."""

    response.set_cookie(
        AMO_SEARCH_SESSION_COOKIE,
        session_secret,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
        path=AMO_SEARCH_SESSION_COOKIE_PATH,
    )


def _amo_search_response(
    result: AmoSearchResult, *, status_code: int = status.HTTP_200_OK
) -> Response:
    """Serialize no more than the adapter's inert local projection with non-cacheable headers."""

    payload = AmoSearchApiResponse(
        availability=result.availability,
        reason_code=result.reason_code,
        results=[
            AmoSearchApiResult(guid=item.guid, name=item.name, version=item.version)
            for item in result.results
        ],
        cache_hit=result.cache_hit,
    )
    response = Response(
        content=payload.model_dump_json(),
        media_type="application/json",
        status_code=status_code,
    )
    response.headers["Cache-Control"] = AMO_SEARCH_CACHE_CONTROL
    response.headers["Pragma"] = "no-cache"
    return response


def _unavailable_amo_search() -> AmoSearchResult:
    """Keep route-local refusals value-free and in the adapter's manual-entry state shape."""

    return AmoSearchResult(availability="unavailable", reason_code="unexpected")


def _amo_search_parameters(request: Request) -> tuple[object, object]:
    """Reject duplicate/unknown query keys before the adapter can issue an outbound request."""

    query_params = request.query_params
    if set(query_params) != {"q", "locale"}:
        return None, None
    q_values = query_params.getlist("q")
    locale_values = query_params.getlist("locale")
    if len(q_values) != 1 or len(locale_values) != 1:
        return None, None
    return q_values[0], locale_values[0]


async def _watch_amo_search_disconnect(request: Request, cancelled: threading.Event) -> None:
    """Set a thread-safe cancellation flag while the bounded synchronous adapter is running."""

    while not cancelled.is_set():
        if await request.is_disconnected():
            cancelled.set()
            return
        await asyncio.sleep(0.025)


async def _run_amo_search(
    request: Request,
    *,
    adapter: AmoSearchAdapter,
    query: object,
    locale: object,
    session_secret: str,
) -> AmoSearchResult:
    """Avoid blocking the ASGI loop and fail closed if the browser disconnects mid-lookup."""

    if await request.is_disconnected():
        return adapter.search(
            query=query,
            locale=locale,
            session_secret=session_secret,
            cancellation_check=lambda: True,
        )
    cancelled = threading.Event()
    watcher = asyncio.create_task(_watch_amo_search_disconnect(request, cancelled))
    try:
        return await asyncio.to_thread(
            adapter.search,
            query=query,
            locale=locale,
            session_secret=session_secret,
            cancellation_check=cancelled.is_set,
        )
    finally:
        cancelled.set()
        watcher.cancel()
        with suppress(asyncio.CancelledError):
            await watcher


FIREFOX_POLICIES_JSON_IMPORT_EXAMPLE: dict[str, Any] = {
    "name": "Workstation baseline",
    "description": "Imported from Firefox policies.json",
    "schema_version": DEFAULT_SCHEMA_CHANNEL,
    "document": {
        "policies": {
            "DisableTelemetry": True,
            "Preferences": {
                "browser.tabs.warnOnClose": {
                    "Value": True,
                    "Status": "locked",
                }
            },
        }
    },
}


class FirefoxPoliciesJsonImportRequest(BaseModel):
    """Create a profile from a Firefox Enterprise policies.json document."""

    name: str = Field(..., max_length=255, description="Library profile name to create.")
    description: str | None = Field(
        default=None,
        description="Optional library profile description.",
    )
    schema_version: str = Field(
        default=DEFAULT_SCHEMA_CHANNEL,
        max_length=50,
        description="Firefox policy schema channel used to validate the imported document.",
    )
    document: Any = Field(
        ...,
        description=(
            "Full Firefox Enterprise policies.json document. "
            "The value must be an object with a top-level policies object."
        ),
    )
    compliance: dict[str, Any] | None = Field(
        default=None,
        description="Optional internal compliance metadata to attach to the created profile.",
    )

    model_config = ConfigDict(json_schema_extra={"example": FIREFOX_POLICIES_JSON_IMPORT_EXAMPLE})


def _decode_json_document(raw: bytes | str, *, source: str) -> Any:
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Invalid JSON in {source}",
                "error": str(exc),
            },
        ) from exc


def _validate_import_request_payload(data: dict[str, Any]) -> FirefoxPoliciesJsonImportRequest:
    try:
        return FirefoxPoliciesJsonImportRequest.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.errors(),
        ) from exc


async def _read_firefox_policies_import_request(
    request: Request,
) -> FirefoxPoliciesJsonImportRequest:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file") or form.get("document")
        if upload is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Firefox policies.json import failed",
                    "error": "Multipart import requires a file field",
                },
            )
        try:
            if hasattr(upload, "read"):
                raw_document = await upload.read()
            elif isinstance(upload, str):
                raw_document = upload
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Firefox policies.json import failed",
                        "error": "Unsupported multipart document field",
                    },
                )

            compliance: dict[str, Any] | None = None
            raw_compliance = form.get("compliance")
            if isinstance(raw_compliance, str) and raw_compliance.strip():
                parsed_compliance = _decode_json_document(raw_compliance, source="compliance")
                if not isinstance(parsed_compliance, dict):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "message": "Firefox policies.json import failed",
                            "error": "Multipart compliance field must be a JSON object",
                        },
                    )
                compliance = parsed_compliance

            name = form.get("name")
            if not isinstance(name, str) or not name.strip():
                filename = getattr(upload, "filename", "") or ""
                name = filename.removesuffix(".json").strip() or "Imported policies.json"

            return _validate_import_request_payload(
                {
                    "name": name,
                    "description": form.get("description") or None,
                    "schema_version": form.get("schema_version") or DEFAULT_SCHEMA_CHANNEL,
                    "document": _decode_json_document(raw_document, source="policies.json"),
                    "compliance": compliance,
                }
            )
        finally:
            close = getattr(upload, "close", None)
            if callable(close):
                await close()

    if content_type.startswith("application/json"):
        try:
            data = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid JSON in request body",
                    "error": str(exc),
                },
            ) from exc
        return _validate_import_request_payload(data)

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail={
            "message": "Unsupported import content type",
            "error": "Use application/json or multipart/form-data",
        },
    )


def _validate_profile_policies_or_422(
    *,
    name: str,
    schema_version: str,
    flags: dict[str, Any] | None,
) -> None:
    """
    Validate profile policies (flags) against internal Firefox schemas.

    `schema_version` corresponds to the channel ("esr‑140", "release‑145"),
    `flags` is interpreted as a mapping of Firefox policy_id -> value.
    """
    payload = {
        "name": name,
        "channel": schema_version,
        "policies": flags,
    }

    try:
        validate_profile_payload_with_schema(payload)
    except SchemaChannelError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": "Schema channel is not available", "code": exc.code},
        ) from exc
    except PolicyValidationError as exc:
        issues_payload = [
            {
                "policy": issue.policy,
                "path": issue.path,
                "message": issue.message,
            }
            for issue in exc.issues
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Policy validation failed",
                "issues": issues_payload,
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Profile validation failed",
                "error": str(exc),
            },
        ) from exc


async def _list_profiles_core(
    session: AsyncSession,
    *,
    q: str | None = None,
    schema_version: str | None = None,
    validation_state: str | None = None,
    lifecycle: str = "active",
    include_deleted: bool = False,
    limit: int = 50,
    offset: int = 0,
    sort: str = "updated_at",
    order: str = "desc",
) -> list[ProfileRead]:
    page = await _profile_library_page_core(
        session,
        q=q,
        schema_version=schema_version,
        validation_state=validation_state,
        lifecycle=lifecycle,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )
    return list(page.items)


async def _profile_library_page_core(
    session: AsyncSession,
    *,
    q: str | None = None,
    schema_version: str | None = None,
    validation_state: str | None = None,
    lifecycle: str = "active",
    include_deleted: bool = False,
    limit: int = 50,
    offset: int = 0,
    sort: str = "updated_at",
    order: str = "desc",
    include_items: bool = True,
) -> ProfilePageResult:
    return await ProfileService.page(
        session,
        q=q,
        schema_version=schema_version,
        validation_state=validation_state,
        lifecycle=lifecycle,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
        include_items=include_items,
    )


async def _profile_library_stats_core(
    session: AsyncSession,
    *,
    q: str | None = None,
    schema_version: str | None = None,
    validation_state: str | None = None,
    lifecycle: str = "active",
    include_deleted: bool = False,
) -> dict[str, int]:
    page = await _profile_library_page_core(
        session,
        q=q,
        schema_version=schema_version,
        validation_state=validation_state,
        lifecycle=lifecycle,
        include_deleted=include_deleted,
        include_items=False,
    )
    return {
        "filtered": page.filtered,
        "total": page.total,
    }


async def _get_profile_or_404_core(
    profile_id: int,
    session: AsyncSession,
    *,
    include_deleted: bool = False,
    not_found_detail: str = "Profile not found",
) -> ProfileRead:
    profile = await ProfileService.get(session, profile_id, include_deleted=include_deleted)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)
    return profile


async def _create_profile_core(
    payload: ProfileCreate,
    session: AsyncSession,
    *,
    validate_policies: bool = True,
    conflict_detail: str = "Profile with this name already exists",
    provenance_origin: str = "generic-create",
) -> ProfileRead:
    if validate_policies:
        _validate_profile_policies_or_422(
            name=payload.name,
            schema_version=payload.schema_version,
            flags=payload.flags,
        )

    try:
        if provenance_origin == "firefox-import":
            profile = await ProfileService.create_firefox_import(session, payload)
        else:
            profile = await ProfileService.create(session, payload)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        ) from exc

    return profile


async def _update_profile_core(
    profile_id: int,
    payload: ProfileUpdate,
    session: AsyncSession,
    *,
    validate_policies: bool = True,
    not_found_detail: str = "Profile not found",
) -> ProfileRead:
    current = await _get_profile_or_404_core(
        profile_id,
        session,
        not_found_detail=not_found_detail,
    )
    payload_data = payload.model_dump(exclude_unset=True)
    expected_revision = payload_data.pop("expected_revision", None)
    if expected_revision is not None and expected_revision != current.revision:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Profile has been modified since it was loaded",
                "profile_id": profile_id,
                "current_revision": current.revision,
                "expected_revision": expected_revision,
            },
        )
    normalized_payload_data = dict(payload_data)
    if "compliance" in payload_data:
        normalized_payload_data["compliance"] = payload_data["compliance"]
    normalized_payload = ProfileUpdate.model_validate(normalized_payload_data)

    if (
        "schema_version" in payload_data
        and normalized_payload.schema_version is not None
        and normalized_payload.schema_version != current.schema_version
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Schema conversion preview is required for channel changes",
                "code": "profile_schema_conversion_required",
            },
        )

    if validate_policies:
        new_schema_version = normalized_payload.schema_version or current.schema_version
        new_flags = (
            normalized_payload.flags if normalized_payload.flags is not None else current.flags
        )

        _validate_profile_policies_or_422(
            name=current.name,
            schema_version=new_schema_version,
            flags=new_flags,
        )

    updated = await ProfileService.update(session, profile_id, normalized_payload)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()
    return updated


async def _delete_profile_core(
    profile_id: int,
    session: AsyncSession,
    *,
    not_found_detail: str = "Profile not found",
) -> None:
    ok = await ProfileService.soft_delete(session, profile_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()


async def _restore_profile_core(
    profile_id: int,
    session: AsyncSession,
    *,
    not_found_detail: str = "Profile not found",
) -> ProfileRead:
    restored = await ProfileService.restore(session, profile_id)
    if restored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()
    return restored


async def _hard_delete_profile_core(
    profile_id: int,
    session: AsyncSession,
    *,
    not_found_detail: str = "Profile not found",
) -> None:
    ok = await ProfileService.hard_delete(session, profile_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found_detail)

    await session.commit()


async def _reset_profiles_library_core(session: AsyncSession) -> dict[str, int]:
    deleted = await ProfileService.hard_delete_all(session)
    await session.commit()
    return {"deleted": deleted}


@router.get("", response_model=list[ProfileRead], summary="List profiles")
async def list_profiles(
    response: Response,
    session: AsyncSession = Depends(get_session),
    q: str | None = Query(None, description="Substring filter for profile name/description"),
    schema_version: str | None = Query(None, description="Filter by schema_version (channel)"),
    validation_state: str | None = Query(
        None,
        description="Filter by validation state: valid/invalid/not_validated",
    ),
    lifecycle: str = Query("active", description="Lifecycle filter: active/archived/all"),
    include_deleted: bool = Query(False, description="Include soft‑deleted profiles"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query(
        "updated_at", description="Sort field: created_at/updated_at/name/schema_version/id"
    ),
    order: str = Query("desc", description="Sort order: asc/desc"),
) -> list[ProfileRead]:
    page = await _profile_library_page_core(
        session,
        q=q,
        schema_version=schema_version,
        validation_state=validation_state,
        lifecycle=lifecycle,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )
    # Preserve the exact JSON list contract. The library reads same-origin
    # headers to render its already-existing summary without a second request.
    response.headers["X-BPM-Profile-Filtered"] = str(page.filtered)
    response.headers["X-BPM-Profile-Total"] = str(page.total)
    return list(page.items)


@router.get("/stats", summary="Get profile library stats")
async def profile_library_stats(
    session: AsyncSession = Depends(get_session),
    q: str | None = Query(None, description="Substring filter for profile name/description"),
    schema_version: str | None = Query(None, description="Filter by schema_version (channel)"),
    validation_state: str | None = Query(
        None,
        description="Filter by validation state: valid/invalid/not_validated",
    ),
    lifecycle: str = Query("active", description="Lifecycle filter: active/archived/all"),
    include_deleted: bool = Query(False, description="Include soft-deleted profiles"),
) -> dict[str, int]:
    return await _profile_library_stats_core(
        session,
        q=q,
        schema_version=schema_version,
        validation_state=validation_state,
        lifecycle=lifecycle,
        include_deleted=include_deleted,
    )


@router.get(
    "/extensions/amo-search",
    response_model=AmoSearchApiResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": AmoSearchApiResponse,
            "description": "Rejected cross-site request; no AMO request was started.",
        }
    },
    summary="Search AMO extensions through BPM",
    openapi_extra={
        "parameters": [
            {
                "name": "q",
                "in": "query",
                "required": True,
                "description": "Explicit extension-name lookup; 1--100 NFC characters.",
                "schema": {"type": "string", "minLength": 1, "maxLength": 100},
            },
            {
                "name": "locale",
                "in": "query",
                "required": True,
                "description": "One supported BPM UI locale.",
                "schema": {"type": "string", "enum": ["en", "ru", "de", "es-ES", "fr", "zh-CN"]},
            },
        ]
    },
)
async def search_amo_extensions(request: Request) -> Response:
    """Perform one explicit, same-origin lookup without exposing AMO as a general proxy."""

    if not _amo_search_request_is_same_origin(request):
        return _amo_search_response(
            _unavailable_amo_search(), status_code=status.HTTP_403_FORBIDDEN
        )

    query, locale = _amo_search_parameters(request)
    session_secret, should_set_session = _amo_search_session_secret(request)
    result = await _run_amo_search(
        request,
        adapter=_amo_search_adapter(request),
        query=query,
        locale=locale,
        session_secret=session_secret,
    )
    response = _amo_search_response(result)
    if should_set_session:
        _set_amo_search_session_cookie(request, response, session_secret)
    return response


@router.delete("/reset", summary="Hard-delete all profiles from the library")
async def reset_profiles_library(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return await _reset_profiles_library_core(session)


@router.get("/{profile_id}", response_model=ProfileRead, summary="Get profile")
async def get_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
    include_deleted: bool = Query(False, description="Include soft-deleted profile"),
) -> ProfileRead:
    return await _get_profile_or_404_core(profile_id, session, include_deleted=include_deleted)


@router.post(
    "",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create profile",
)
async def create_profile(
    payload: ProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _create_profile_core(
        payload,
        session,
        validate_policies=True,
    )


def _profile_preparation_error(
    *,
    code: str,
    http_status: int,
    parameters: dict[str, str | int | bool | None] | None = None,
) -> HTTPException:
    """Return a stable, value-free error that the preparation UI can localize."""

    return HTTPException(
        status_code=http_status,
        detail={
            "kind": "profile-preparation-error",
            "contract_version": 1,
            "code": code,
            "i18n_key": f"profiles.preparation_error_{code}",
            "http_status": http_status,
            "mutation": "none",
            "parameters": parameters or {},
        },
    )


async def _read_new_profile_preparation_request(request: Request) -> NewProfilePreparationRequest:
    """Parse preparation input without returning Pydantic's value-bearing errors."""

    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError
        return NewProfilePreparationRequest.model_validate(body)
    except json.JSONDecodeError, ValidationError, ValueError:
        raise _profile_preparation_error(
            code="preparation_request_invalid",
            http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        ) from None


async def _read_duplicate_profile_preparation_request(
    request: Request,
) -> DuplicateProfilePreparationRequest:
    """Parse duplicate preparation input without echoing policy or source values."""

    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError
        return DuplicateProfilePreparationRequest.model_validate(body)
    except json.JSONDecodeError, ValidationError, ValueError:
        raise _profile_preparation_error(
            code="preparation_request_invalid",
            http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        ) from None


async def _read_duplicate_profile_preparation_preview_request(
    request: Request,
) -> DuplicateProfilePreparationPreviewRequest:
    """Parse a value-safe duplicate-planning refresh without echoing inputs."""

    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError
        return DuplicateProfilePreparationPreviewRequest.model_validate(body)
    except json.JSONDecodeError, ValidationError, ValueError:
        raise _profile_preparation_error(
            code="preparation_request_invalid",
            http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        ) from None


async def _create_prepared_new_profile_in_transaction(
    session: AsyncSession,
    payload: NewProfilePreparationRequest,
) -> ProfileRead:
    """Commit exactly one new prepared profile or roll the entire attempt back."""

    if session.get_bind().dialect.name == "sqlite":
        if session.in_transaction():
            raise RuntimeError("new profile preparation requires a fresh API session transaction")
        try:
            # SQLite needs the write reservation before composition and INSERT
            # so a competing name cannot create a half-observed candidate.
            await session.execute(text("BEGIN IMMEDIATE"))
            profile = await ProfileService.create_prepared_new_profile(session, payload)
            await session.commit()
            return profile
        except BaseException:
            if session.in_transaction():
                await session.rollback()
            raise

    try:
        async with session.begin():
            return await ProfileService.create_prepared_new_profile(session, payload)
    except BaseException:
        if session.in_transaction():
            await session.rollback()
        raise


async def _create_prepared_duplicate_profile_in_transaction(
    session: AsyncSession,
    payload: DuplicateProfilePreparationRequest,
) -> ProfileRead:
    """Replan and create exactly one duplicate, or roll the whole attempt back."""

    if session.get_bind().dialect.name == "sqlite":
        if session.in_transaction():
            raise RuntimeError(
                "duplicate profile preparation requires a fresh API session transaction"
            )
        try:
            # SQLite has no SELECT FOR UPDATE.  Its write reservation is taken
            # before the source read so validation, replan, and INSERT observe
            # one serialized write boundary.
            await session.execute(text("BEGIN IMMEDIATE"))
            profile = await ProfileService.create_prepared_duplicate_profile(session, payload)
            await session.commit()
            return profile
        except BaseException:
            if session.in_transaction():
                await session.rollback()
            raise

    try:
        async with session.begin():
            return await ProfileService.create_prepared_duplicate_profile(session, payload)
    except BaseException:
        if session.in_transaction():
            await session.rollback()
        raise


@router.post(
    "/prepare/new",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create prepared new profile",
    description=(
        "Atomically create one profile from server-resolved schema, starter, and CIS catalog "
        "identities. Policy flags, compliance, and baseline provenance are never accepted from "
        "the caller."
    ),
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The name is already in use; no profile was created.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The request or selected catalog candidate is invalid; no profile was created.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The preparation transaction failed; no profile was created.",
        },
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": NewProfilePreparationRequest.model_json_schema(),
                }
            },
        }
    },
)
async def create_prepared_new_profile(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    """M3-04's dedicated atomic create command; generic CRUD remains unchanged."""

    payload = await _read_new_profile_preparation_request(request)
    try:
        return await _create_prepared_new_profile_in_transaction(session, payload)
    except NewProfilePreparationFailure as exc:
        raise _profile_preparation_error(
            code=exc.code,
            http_status=(
                status.HTTP_409_CONFLICT
                if exc.code == "preparation_idempotency_key_reused"
                else status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
        ) from exc
    except IntegrityError as exc:
        # PostgreSQL may report either the name or idempotency constraint first
        # when concurrent exact replays collide on both.  The durable key is
        # authoritative after every insert conflict, irrespective of which
        # constraint text the driver happened to return.
        try:
            replay = await ProfileService.reconcile_prepared_new_profile(session, payload)
        except NewProfilePreparationFailure as replay_exc:
            raise _profile_preparation_error(
                code=replay_exc.code,
                http_status=status.HTTP_409_CONFLICT,
            ) from replay_exc
        if replay is not None:
            return replay
        raise _profile_preparation_error(
            code=_preparation_integrity_error_code(exc),
            http_status=status.HTTP_409_CONFLICT,
        ) from exc
    except (SQLAlchemyError, RuntimeError) as exc:
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
    except Exception as exc:
        # The transaction helper rolls every unknown composer/serialization
        # failure back before this value-free terminal response is emitted.
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc


def _preparation_integrity_error_code(exc: IntegrityError) -> str:
    """Classify the two preparation uniqueness boundaries without values."""

    if "preparation_idempotency_key" in str(exc.orig).lower():
        return "preparation_idempotency_key_reused"
    return "preparation_name_conflict"


def _duplicate_preparation_failure_status(code: str) -> int:
    """Keep duplicate state races distinct from malformed catalog selection."""

    if code == "preparation_duplicate_source_not_found":
        return status.HTTP_404_NOT_FOUND
    if code in {
        "preparation_schema_unavailable",
        "preparation_starter_unavailable",
        "preparation_cis_unavailable",
        "preparation_candidate_invalid",
    }:
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    return status.HTTP_409_CONFLICT


@router.post(
    "/prepare/duplicate/preview",
    response_model=DuplicateProfilePreparationPreview,
    summary="Preview prepared duplicate",
    description=(
        "Read-only, value-safe duplicate planning for one source revision and selected catalog "
        "identities. This endpoint never creates or modifies a profile."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The duplicate source does not exist; no profile was created.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The planning request is invalid; no profile was created.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "Duplicate planning failed without creating a profile.",
        },
    },
)
async def preview_prepared_duplicate_profile(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> DuplicateProfilePreparationPreview:
    """Expose M3-03's read-only planning identity to the preparation form."""

    payload = await _read_duplicate_profile_preparation_preview_request(request)
    try:
        duplicate_plan = await ProfileService.plan_duplicate(
            session,
            payload.source_id,
            expected_source_revision=payload.expected_source_revision,
            target_schema_id=payload.target_schema_id,
            preset_id=payload.starter_id,
            cis_baseline_id=payload.cis_baseline_id,
        )
    except (SQLAlchemyError, RuntimeError) as exc:
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
    except Exception as exc:
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc

    if duplicate_plan is None:
        raise _profile_preparation_error(
            code="preparation_duplicate_source_not_found",
            http_status=status.HTTP_404_NOT_FOUND,
        )

    plan = duplicate_plan.plan
    plan_digest = plan.get("plan_digest")
    if not isinstance(plan_digest, str):
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return DuplicateProfilePreparationPreview(
        kind="profile-duplicate-plan",
        contract_version=1,
        status=duplicate_plan.status,
        reason_code=duplicate_plan.reason_code,
        plan_digest=plan_digest,
    )


@router.post(
    "/prepare/duplicate",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create prepared duplicate profile",
    description=(
        "Atomically rederive a duplicate from one fixed source revision and current server catalogs. "
        "The source is never converted or otherwise modified."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The duplicate source does not exist; no profile was created.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The source, duplicate composition, name, or idempotency boundary rejected the command.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The selected catalog candidate is unavailable or invalid; no profile was created.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ProfilePreparationErrorEnvelope,
            "description": "The duplicate transaction failed; no profile was created.",
        },
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": DuplicateProfilePreparationRequest.model_json_schema(),
                }
            },
        }
    },
)
async def create_prepared_duplicate_profile(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    """M3-05's source-preserving atomic duplicate command."""

    payload = await _read_duplicate_profile_preparation_request(request)
    try:
        return await _create_prepared_duplicate_profile_in_transaction(session, payload)
    except DuplicateProfilePreparationFailure as exc:
        raise _profile_preparation_error(
            code=exc.code,
            http_status=_duplicate_preparation_failure_status(exc.code),
        ) from exc
    except IntegrityError as exc:
        # A concurrent same-key duplicate can also collide on the target name
        # first.  Re-read its authoritative key before classifying any raw
        # constraint text, so either engine preserves exactly-once replay.
        try:
            replay = await ProfileService.reconcile_prepared_duplicate_profile(session, payload)
        except DuplicateProfilePreparationFailure as replay_exc:
            raise _profile_preparation_error(
                code=replay_exc.code,
                http_status=_duplicate_preparation_failure_status(replay_exc.code),
            ) from replay_exc
        if replay is not None:
            return replay
        raise _profile_preparation_error(
            code=_preparation_integrity_error_code(exc),
            http_status=status.HTTP_409_CONFLICT,
        ) from exc
    except (SQLAlchemyError, RuntimeError) as exc:
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc
    except Exception as exc:
        raise _profile_preparation_error(
            code="preparation_transaction_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        ) from exc


def _conversion_preview_error(
    *,
    code: str,
    http_status: int,
    profile_id: int | None,
    expected_revision: int | None = None,
    current_revision: int | None = None,
    plan_digest: str | None = None,
    retry_preview_required: bool = False,
    parameters: dict[str, str | int | bool | None] | None = None,
) -> HTTPException:
    """Return the M2-04 value-free, no-mutation error envelope."""
    return HTTPException(
        status_code=http_status,
        detail={
            "kind": "profile-conversion-error",
            "contract_version": 1,
            "code": code,
            "http_status": http_status,
            "profile_id": profile_id,
            "expected_revision": expected_revision,
            "current_revision": current_revision,
            "plan_digest": plan_digest,
            "retry_preview_required": retry_preview_required,
            "mutation": "none",
            "parameters": parameters or {},
        },
    )


def _conversion_preview_status(
    code: str,
    *,
    source_artifact_id: str,
) -> int:
    """Map planner preconditions to the exact M2-04 preview statuses."""
    if code == "conversion_source_not_active":
        return status.HTTP_409_CONFLICT
    if code == "schema_channel_unknown":
        return (
            status.HTTP_409_CONFLICT
            if get_schema_channel(source_artifact_id) is None
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
    if code == "schema_channel_retired_requires_migration":
        return status.HTTP_409_CONFLICT
    if code in {"conversion_source_schema_missing", "conversion_target_schema_missing"}:
        return status.HTTP_503_SERVICE_UNAVAILABLE
    return status.HTTP_422_UNPROCESSABLE_CONTENT


async def _conversion_preview_core(
    profile_id: int,
    payload: ConversionPreviewRequest,
    session: AsyncSession,
) -> ConversionPreviewResponse:
    """Derive a preview solely from the currently stored profile state.

    This is intentionally a read service boundary: it loads exactly one source
    profile, passes server-owned policy/compliance/context to the pure planner,
    and returns its value-free public projection.  It never commits, flushes,
    refreshes, assigns ORM state, or accepts a caller-authored source document.
    """
    profile = await ProfileService.get_conversion_preview_source(session, profile_id)
    if profile is None:
        raise _conversion_preview_error(
            code="conversion_profile_not_found",
            http_status=status.HTTP_404_NOT_FOUND,
            profile_id=profile_id,
        )
    if profile.deleted_at is not None:
        raise _conversion_preview_error(
            code="conversion_source_not_active",
            http_status=status.HTTP_409_CONFLICT,
            profile_id=profile_id,
            current_revision=profile.revision,
        )

    try:
        result = plan_profile_conversion(
            {"policies": profile.flags},
            source_artifact_id=profile.schema_version,
            target_artifact_id=payload.target_artifact_id,
            context=ProfileService.conversion_planning_context(
                profile,
                compliance_replanner=recompute_pinned_cis_compliance,
            ),
        )
    except ConversionPlanningError as exc:
        raise _conversion_preview_error(
            code=exc.code,
            http_status=_conversion_preview_status(
                exc.code,
                source_artifact_id=profile.schema_version,
            ),
            profile_id=profile.id,
            current_revision=profile.revision,
            parameters={"target_artifact_id": payload.target_artifact_id},
        ) from exc

    # M4-03 availability means the exact artifacts could be planned.  It is
    # intentionally independent from compatibility.applicable, which remains
    # false for a safely returned blocked candidate.
    return ConversionPreviewResponse.model_validate({"available": True, **result.plan})


async def _read_conversion_preview_request(
    request: Request,
    *,
    profile_id: int,
) -> ConversionPreviewRequest:
    """Parse the narrow preview request without reflecting rejected raw input.

    FastAPI's default request-validation body includes an ``input`` echo.  That
    is unsuitable here because callers must not be able to make a policy value
    appear in a conversion error.  The target-only DTO is therefore parsed at
    this API boundary and failures use the same value-free error envelope.
    """
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise ValueError
        return ConversionPreviewRequest.model_validate(data)
    except json.JSONDecodeError, ValidationError, ValueError:
        raise _conversion_preview_error(
            code="conversion_preview_request_invalid",
            http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            profile_id=profile_id,
        ) from None


def _conversion_apply_status(code: str, *, source_artifact_id: str) -> int:
    """Map apply preconditions to the immutable M2-04 status vocabulary."""
    if code == "conversion_profile_not_found":
        return status.HTTP_404_NOT_FOUND
    if code in {
        "conversion_source_not_active",
        "schema_channel_retired_requires_migration",
        "conversion_revision_stale",
        "conversion_source_identity_stale",
        "conversion_plan_stale",
        "conversion_schema_identity_stale",
        "conversion_recipe_registry_stale",
        "conversion_plan_blocked",
    }:
        return status.HTTP_409_CONFLICT
    if code == "conversion_apply_failed":
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    return _conversion_preview_status(code, source_artifact_id=source_artifact_id)


def _conversion_apply_retry_preview_required(code: str) -> bool:
    return code in {
        "conversion_revision_stale",
        "conversion_source_identity_stale",
        "conversion_plan_stale",
        "conversion_schema_identity_stale",
        "conversion_recipe_registry_stale",
    }


async def _read_conversion_apply_request(
    request: Request,
    *,
    profile_id: int,
) -> ConversionApplyRequest:
    """Parse a confirmation without reflecting rejected profile data."""
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise ValueError
        return ConversionApplyRequest.model_validate(data)
    except json.JSONDecodeError, ValidationError, ValueError:
        raise _conversion_preview_error(
            code="conversion_apply_request_invalid",
            http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            profile_id=profile_id,
        ) from None


def _conversion_apply_request_example() -> dict[str, object]:
    """Return the reviewed OpenAPI example without relying on Pydantic's union config type."""
    config = ConversionApplyRequest.model_config
    if not isinstance(config, dict):
        raise RuntimeError("conversion apply schema configuration is invalid")
    schema_extra = config.get("json_schema_extra")
    if not isinstance(schema_extra, dict):
        raise RuntimeError("conversion apply schema example is missing")
    example = schema_extra.get("example")
    if not isinstance(example, dict):
        raise RuntimeError("conversion apply schema example is invalid")
    return dict(example)


async def _conversion_apply_in_transaction(
    session: AsyncSession,
    *,
    profile_id: int,
    payload: ConversionApplyRequest,
) -> ConversionApplyOutcome:
    """Own the API transaction while leaving the domain service commit-free."""
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "sqlite":
        # A deferred SQLite read transaction can fail while upgrading to a
        # writer if two applies derive their plans at once.  Taking the write
        # reservation before the read serializes replan/write, and the service
        # conditional UPDATE still proves revision ownership on every dialect.
        if session.in_transaction():
            raise RuntimeError("conversion apply requires a fresh API session transaction")
        try:
            await session.execute(text("BEGIN IMMEDIATE"))
            outcome = await ProfileService.apply_conversion(
                session,
                profile_id,
                payload,
                compliance_replanner=recompute_pinned_cis_compliance,
            )
            await session.commit()
            return outcome
        except BaseException:
            if session.in_transaction():
                await session.rollback()
            raise

    async with session.begin():
        return await ProfileService.apply_conversion(
            session,
            profile_id,
            payload,
            compliance_replanner=recompute_pinned_cis_compliance,
        )


def _conversion_apply_response(outcome: ConversionApplyOutcome) -> ConversionApplyResponse:
    plan = outcome.plan
    source = plan["source"]
    target = plan["target"]
    profile = plan["profile"]
    assert isinstance(source, dict)
    assert isinstance(target, dict)
    assert isinstance(profile, dict)
    source_artifact = source["artifact"]
    target_artifact = target["artifact"]
    assert isinstance(source_artifact, dict)
    assert isinstance(target_artifact, dict)
    return ConversionApplyResponse.model_validate(
        {
            "kind": "profile-conversion-result",
            "contract_version": 1,
            "status": "applied",
            "profile_id": profile["id"],
            "source_revision": outcome.source_revision,
            "result_revision": outcome.result_revision,
            "source": {
                "line_id": source_artifact["line_id"],
                "artifact_id": source_artifact["artifact_id"],
            },
            "target": {
                "line_id": target_artifact["line_id"],
                "artifact_id": target_artifact["artifact_id"],
            },
            "plan_digest": plan["plan_digest"],
            "result_document_digest": target["candidate_document_digest"],
            "result_compliance_digest": plan["compliance"]["target_digest"],
            "compliance": plan["compliance"],
            "target_validation": plan["target_validation"],
            "field_accounting": {
                "application_write_fields": [
                    "schema_version",
                    "flags",
                    "compliance",
                    "extension_provenance",
                    "certificate_provenance",
                    "revision",
                ],
                "database_managed_fields": ["updated_at"],
                "preserved_fields": [
                    "id",
                    "name",
                    "name_casefold",
                    "description",
                    "baseline_provenance",
                    "preparation_idempotency_key",
                    "preparation_request_fingerprint",
                    "created_at",
                    "deleted_at",
                ],
                "updated_at_changed": outcome.updated_at_changed,
            },
        }
    )


@router.post(
    "/import/firefox/policies.json",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import Firefox policies.json",
    description=(
        "Create a library profile from a full Firefox Enterprise policies.json document. "
        "The document is validated before the profile is created. Accepts either an "
        "application/json body or multipart/form-data with a file field."
    ),
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["name", "document"],
                        "properties": {
                            "name": {"type": "string", "maxLength": 255},
                            "description": {"type": "string", "nullable": True},
                            "schema_version": {"type": "string", "default": DEFAULT_SCHEMA_CHANNEL},
                            "document": {
                                "type": "object",
                                "description": "Full Firefox policies.json document.",
                                "properties": {
                                    "policies": {"type": "object"},
                                },
                                "required": ["policies"],
                            },
                            "compliance": {"type": "object", "nullable": True},
                        },
                        "example": FIREFOX_POLICIES_JSON_IMPORT_EXAMPLE,
                    },
                },
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "Firefox policies.json file.",
                            },
                            "name": {"type": "string", "maxLength": 255},
                            "schema_version": {"type": "string", "default": DEFAULT_SCHEMA_CHANNEL},
                            "description": {"type": "string"},
                            "compliance": {
                                "type": "string",
                                "description": "Optional JSON object with compliance metadata.",
                            },
                        },
                    }
                },
            },
            "required": True,
        }
    },
)
async def import_firefox_policies_json(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    """Create a profile from a canonical Firefox enterprise policies.json payload."""
    payload = await _read_firefox_policies_import_request(request)
    try:
        flags = validate_firefox_policies_document(
            payload.document,
            payload.schema_version,
        )
    except FirefoxPoliciesImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Firefox policies.json import failed",
                "issues": [
                    {
                        "policy": None,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in exc.issues
                ],
            },
        ) from exc
    except FirefoxPoliciesDocumentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Policy validation failed",
                "issues": [
                    {
                        "policy": issue.policy,
                        "path": issue.path,
                        "message": issue.message,
                    }
                    for issue in exc.issues
                ],
            },
        ) from exc
    except SchemaChannelError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": "Schema channel is not available", "code": exc.code},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Profile validation failed",
                "error": str(exc),
            },
        ) from exc

    return await _create_profile_core(
        ProfileCreate(
            name=payload.name,
            description=payload.description,
            schema_version=payload.schema_version,
            flags=flags,
            compliance=payload.compliance,
        ),
        session,
        validate_policies=False,
        conflict_detail="Profile with this name already exists",
        provenance_origin="firefox-import",
    )


@router.post(
    "/{profile_id}/conversion-preview",
    response_model=ConversionPreviewResponse,
    summary="Preview Firefox schema conversion",
    description=(
        "Build a deterministic, value-free conversion plan from the current stored profile and "
        "one caller-selected target artifact. This operation never writes the profile. A blocked "
        "but available plan is returned as HTTP 200 with compatibility.applicable=false."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ConversionPreviewErrorEnvelope,
            "description": "The source profile does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ConversionPreviewErrorEnvelope,
            "description": "The source is inactive or cannot be manually converted.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ConversionPreviewErrorEnvelope,
            "description": "The target or source precondition is invalid.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ConversionPreviewErrorEnvelope,
            "description": "An exact required schema artifact is unavailable.",
        },
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": ConversionPreviewRequest.model_json_schema(),
                    "example": {"target_artifact_id": "esr-153.0"},
                }
            },
        }
    },
)
async def preview_profile_conversion(
    profile_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ConversionPreviewResponse:
    payload = await _read_conversion_preview_request(request, profile_id=profile_id)
    return await _conversion_preview_core(profile_id, payload, session)


@router.post(
    "/{profile_id}/conversion-apply",
    response_model=ConversionApplyResponse,
    summary="Apply Firefox schema conversion",
    description=(
        "Atomically rederive and apply one exact, current conversion preview. The request binds "
        "only digests and schema/registry identities; policy and compliance candidates are always "
        "derived again on the server."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ConversionApplyErrorEnvelope,
            "description": "The source profile does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ConversionApplyErrorEnvelope,
            "description": "The preview is stale, blocked, or its active source changed.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ConversionApplyErrorEnvelope,
            "description": "The apply request or current conversion precondition is invalid.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ConversionApplyErrorEnvelope,
            "description": "The transaction failed and no conversion was committed.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ConversionApplyErrorEnvelope,
            "description": "An exact required schema artifact is unavailable.",
        },
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": ConversionApplyRequest.model_json_schema(),
                    "example": _conversion_apply_request_example(),
                }
            },
        }
    },
)
async def apply_profile_conversion(
    profile_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ConversionApplyResponse:
    payload = await _read_conversion_apply_request(request, profile_id=profile_id)
    try:
        outcome = await _conversion_apply_in_transaction(
            session,
            profile_id=profile_id,
            payload=payload,
        )
    except ConversionApplyFailure as exc:
        code = exc.code
        raise _conversion_preview_error(
            code=code,
            http_status=_conversion_apply_status(
                code,
                source_artifact_id=exc.source_artifact_id or payload.source.artifact_id,
            ),
            profile_id=profile_id,
            expected_revision=payload.expected_revision,
            current_revision=exc.current_revision,
            plan_digest=payload.plan_digest,
            retry_preview_required=_conversion_apply_retry_preview_required(code),
        ) from exc
    except (SQLAlchemyError, RuntimeError) as exc:
        raise _conversion_preview_error(
            code="conversion_apply_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            profile_id=profile_id,
            expected_revision=payload.expected_revision,
            plan_digest=payload.plan_digest,
        ) from exc
    except Exception as exc:
        # Planner/adapter defects are never allowed to escape as a partial
        # mutation or an unstructured server response. The transaction helper
        # has rolled the session back before this boundary observes the error.
        raise _conversion_preview_error(
            code="conversion_apply_failed",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            profile_id=profile_id,
            expected_revision=payload.expected_revision,
            plan_digest=payload.plan_digest,
        ) from exc
    return _conversion_apply_response(outcome)


@router.patch(
    "/{profile_id}",
    response_model=ProfileRead,
    summary="Update profile",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ProfileUpdateConflictErrorEnvelope,
            "description": (
                "The revision is stale or the request tried to relabel a saved profile. "
                "Use the explicit conversion preview/apply flow for a schema change."
            ),
        },
    },
)
async def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _update_profile_core(
        profile_id,
        payload,
        session,
        validate_policies=True,
    )


@router.delete(
    "/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete profile"
)
async def delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _delete_profile_core(profile_id, session)
    return None


@router.delete(
    "/{profile_id}/hard",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard-delete profile",
)
async def hard_delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    await _hard_delete_profile_core(profile_id, session)
    return None


@router.post("/{profile_id}/restore", response_model=ProfileRead, summary="Restore profile")
async def restore_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    return await _restore_profile_core(profile_id, session)
