from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.api import profiles as profiles_module
from app.core.policy_validation import PolicyValidationError, PolicyValidationIssue
from app.schemas.profile import ProfileCreate, ProfileUpdate


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def _profile_read(**overrides):
    base = {
        "id": 1,
        "name": "Profile",
        "description": "Base",
        "schema_version": "esr-140.12",
        "flags": {"DisableTelemetry": True},
        "revision": 1,
        "created_at": datetime(2026, 1, 1),
        "updated_at": datetime(2026, 1, 2),
        "deleted_at": None,
        "is_deleted": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_validate_profile_policies_or_422_returns_early_without_flags(monkeypatch):
    called = {"validated": False}

    monkeypatch.setattr(
        profiles_module,
        "validate_profile_payload_with_schema",
        lambda payload: called.__setitem__("validated", True),
    )

    profiles_module._validate_profile_policies_or_422(
        name="Empty",
        schema_version="esr-140.12",
        flags={},
    )

    assert called["validated"] is False


def test_validate_profile_policies_or_422_returns_422_with_issues(monkeypatch):
    def _raise_validation(payload):
        raise PolicyValidationError(
            [
                PolicyValidationIssue(
                    policy="DisableTelemetry",
                    path=["policies", "DisableTelemetry"],
                    message="Bad value",
                )
            ]
        )

    monkeypatch.setattr(profiles_module, "validate_profile_payload_with_schema", _raise_validation)

    with pytest.raises(HTTPException) as excinfo:
        profiles_module._validate_profile_policies_or_422(
            name="Broken",
            schema_version="esr-140.12",
            flags={"DisableTelemetry": "bad"},
        )

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail["issues"][0]["policy"] == "DisableTelemetry"


def test_validate_profile_policies_or_422_returns_400_on_unexpected_error(monkeypatch):
    monkeypatch.setattr(
        profiles_module,
        "validate_profile_payload_with_schema",
        lambda payload: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(HTTPException) as excinfo:
        profiles_module._validate_profile_policies_or_422(
            name="Broken",
            schema_version="esr-140.12",
            flags={"DisableTelemetry": True},
        )

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == {"message": "Profile validation failed", "error": "boom"}


@pytest.mark.anyio
async def test_create_profile_core_skips_validation_when_disabled(monkeypatch):
    session = _FakeSession()
    payload = ProfileCreate(name="Created", description="ok", schema_version="esr-140.12", flags={})
    created = _profile_read(name="Created", description="ok")
    called = {"validated": False}

    monkeypatch.setattr(
        profiles_module,
        "_validate_profile_policies_or_422",
        lambda **kwargs: called.__setitem__("validated", True),
    )

    async def _fake_create(_session, model):
        assert model is payload
        return created

    monkeypatch.setattr(profiles_module.ProfileService, "create", _fake_create)

    result = await profiles_module._create_profile_core(
        payload,
        session,
        validate_policies=False,
    )

    assert result is created
    assert session.commits == 1
    assert called["validated"] is False


@pytest.mark.anyio
async def test_create_profile_core_rolls_back_on_integrity_error(monkeypatch):
    session = _FakeSession()
    payload = ProfileCreate(name="Dup", description=None, schema_version="esr-140.12", flags={})

    async def _raise_integrity(_session, _payload):
        raise IntegrityError("insert", {"name": "Dup"}, Exception("duplicate"))

    monkeypatch.setattr(profiles_module.ProfileService, "create", _raise_integrity)

    with pytest.raises(HTTPException) as excinfo:
        await profiles_module._create_profile_core(payload, session, validate_policies=False)

    assert excinfo.value.status_code == 409
    assert session.rollbacks == 1


@pytest.mark.anyio
async def test_update_profile_core_replaces_flags_and_skips_validation_when_disabled(monkeypatch):
    session = _FakeSession()
    current = _profile_read(flags={"DisableTelemetry": True})
    captured = {}
    updated = _profile_read(
        description="Updated",
        flags={"DisablePrivateBrowsing": True},
    )

    async def _fake_get(*args, **kwargs):
        return current

    async def _fake_update(_session, profile_id, payload):
        captured["profile_id"] = profile_id
        captured["payload"] = payload
        return updated

    monkeypatch.setattr(profiles_module, "_get_profile_or_404_core", _fake_get)
    monkeypatch.setattr(profiles_module.ProfileService, "update", _fake_update)

    result = await profiles_module._update_profile_core(
        5,
        ProfileUpdate(description="Updated", flags={"DisablePrivateBrowsing": True}),
        session,
        validate_policies=False,
    )

    assert result is updated
    assert captured["profile_id"] == 5
    assert captured["payload"].flags == {
        "DisablePrivateBrowsing": True,
    }
    assert "schema_version" not in captured["payload"].model_fields_set
    assert session.commits == 1


@pytest.mark.anyio
async def test_update_profile_core_rejects_stale_expected_revision(monkeypatch):
    session = _FakeSession()
    current = _profile_read(revision=3)
    called = {"updated": False}

    async def _fake_get(*args, **kwargs):
        return current

    async def _fake_update(*args, **kwargs):
        called["updated"] = True
        return current

    monkeypatch.setattr(profiles_module, "_get_profile_or_404_core", _fake_get)
    monkeypatch.setattr(profiles_module.ProfileService, "update", _fake_update)

    with pytest.raises(HTTPException) as excinfo:
        await profiles_module._update_profile_core(
            5,
            ProfileUpdate(description="Stale", expected_revision=2),
            session,
            validate_policies=False,
        )

    assert excinfo.value.status_code == 409
    assert excinfo.value.detail == {
        "message": "Profile has been modified since it was loaded",
        "profile_id": 5,
        "current_revision": 3,
        "expected_revision": 2,
    }
    assert called["updated"] is False
    assert session.commits == 0


@pytest.mark.anyio
async def test_update_profile_core_raises_when_service_returns_none(monkeypatch):
    session = _FakeSession()
    current = _profile_read()

    async def _fake_get(*args, **kwargs):
        return current

    async def _fake_update(_session, profile_id, payload):
        return None

    monkeypatch.setattr(profiles_module, "_get_profile_or_404_core", _fake_get)
    monkeypatch.setattr(profiles_module.ProfileService, "update", _fake_update)

    with pytest.raises(HTTPException) as excinfo:
        await profiles_module._update_profile_core(
            9,
            ProfileUpdate(description="Nope"),
            session,
            validate_policies=False,
        )

    assert excinfo.value.status_code == 404
