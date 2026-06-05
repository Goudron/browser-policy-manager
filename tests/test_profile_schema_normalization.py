from __future__ import annotations

import asyncio
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import main as main_module
from app.core.schema_channels import CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL
from app.db import AsyncSessionAdapter
from app.models.profile import Base, Profile
from app.services.profile_schema_normalization import normalize_legacy_profile_schema_versions
from tools import backfill_profile_schema_versions

LEGACY_ESR_140_8 = f"esr-140.{8}"
LEGACY_ESR_140_9 = f"esr-140.{9}"
LEGACY_ESR_140_10 = f"esr-140.{10}"
LEGACY_RELEASE_148 = f"release-{148}"
LEGACY_RELEASE_149 = f"release-{149}"
LEGACY_RELEASE_150 = f"release-{150}"


def _make_session():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    return engine, session


def test_profile_schema_normalization_updates_only_selected_legacy_channels():
    engine, session = _make_session()
    try:
        session.add_all(
            [
                Profile(name="legacy-esr-9", schema_version=LEGACY_ESR_140_9, flags={"DisableTelemetry": True}),
                Profile(name="legacy-esr-10", schema_version=LEGACY_ESR_140_10, flags={"DisableTelemetry": True}),
                Profile(name="legacy-release-current-minus-one", schema_version=LEGACY_RELEASE_149, flags={"DisableTelemetry": True}),
                Profile(name="legacy-release-current-minus-one-copy", schema_version=LEGACY_RELEASE_149, flags={"DisableTelemetry": True}),
                Profile(name="legacy-release-current", schema_version=LEGACY_RELEASE_150, flags={"DisableTelemetry": True}),
                Profile(name="legacy-esr-8", schema_version=LEGACY_ESR_140_8, flags={"DisableTelemetry": True}),
                Profile(name="legacy-release-older", schema_version=LEGACY_RELEASE_148, flags={"DisableTelemetry": True}),
                Profile(
                    name="current-release",
                    schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL,
                    flags={"DisableTelemetry": True},
                ),
            ]
        )
        session.commit()

        result = asyncio.run(
            normalize_legacy_profile_schema_versions(AsyncSessionAdapter(session))
        )
        asyncio.run(AsyncSessionAdapter(session).commit())

        rows = {
            row.name: (row.schema_version, row.revision)
            for row in session.scalars(select(Profile).order_by(Profile.name)).all()
        }
        assert result.scanned == 5
        assert result.normalized == 5
        assert result.skipped_invalid == 0
        assert rows["legacy-esr-10"][0] == CURRENT_ESR_SCHEMA_CHANNEL
        assert rows["legacy-esr-9"][0] == CURRENT_ESR_SCHEMA_CHANNEL
        assert rows["legacy-release-current"][0] == CURRENT_RELEASE_SCHEMA_CHANNEL
        assert rows["legacy-release-current-minus-one"][0] == CURRENT_RELEASE_SCHEMA_CHANNEL
        assert rows["legacy-release-current-minus-one-copy"][0] == CURRENT_RELEASE_SCHEMA_CHANNEL
        assert rows["legacy-esr-8"][0] == LEGACY_ESR_140_8
        assert rows["legacy-release-older"][0] == LEGACY_RELEASE_148
        assert rows["current-release"][0] == CURRENT_RELEASE_SCHEMA_CHANNEL
        assert rows["legacy-esr-10"][1] == 2
        assert rows["legacy-esr-9"][1] == 2
        assert rows["legacy-release-current"][1] == 2
        assert rows["legacy-release-current-minus-one"][1] == 2
        assert rows["legacy-release-current-minus-one-copy"][1] == 2
    finally:
        session.close()
        engine.dispose()


def test_profile_schema_normalization_noops_when_no_legacy_channels_exist():
    engine, session = _make_session()
    try:
        session.add(
            Profile(
                name="current-only",
                schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL,
                flags={"DisableTelemetry": True},
            )
        )
        session.commit()

        result = asyncio.run(
            normalize_legacy_profile_schema_versions(AsyncSessionAdapter(session))
        )

        assert result.scanned == 0
        assert result.normalized == 0
        assert result.skipped_invalid == 0
    finally:
        session.close()
        engine.dispose()


def test_profile_schema_normalization_skips_invalid_profiles_for_target_schema():
    engine, session = _make_session()
    try:
        session.add(
            Profile(
                name="invalid-legacy-release",
                schema_version=LEGACY_RELEASE_149,
                flags={"HttpAllowlist": [42]},
            )
        )
        session.commit()

        result = asyncio.run(
            normalize_legacy_profile_schema_versions(AsyncSessionAdapter(session))
        )
        asyncio.run(AsyncSessionAdapter(session).commit())

        profile = session.scalar(select(Profile).where(Profile.name == "invalid-legacy-release"))
        assert result.scanned == 1
        assert result.normalized == 0
        assert result.skipped_invalid == 1
        assert profile is not None
        assert profile.schema_version == LEGACY_RELEASE_149
        assert profile.revision == 1
    finally:
        session.close()
        engine.dispose()


def test_profile_schema_backfill_command_runs_normalizer_and_commits(monkeypatch):
    events: list[str] = []

    class FakeSession:
        async def commit(self):
            events.append("commit")

    async def fake_init_db():
        events.append("init")

    async def fake_get_session():
        events.append("yield-session")
        yield FakeSession()
        events.append("close-session")

    async def fake_normalize(session):
        assert isinstance(session, FakeSession)
        events.append("normalize")
        return SimpleNamespace(scanned=3, normalized=2, skipped_invalid=1)

    monkeypatch.setattr(backfill_profile_schema_versions, "init_db", fake_init_db)
    monkeypatch.setattr(backfill_profile_schema_versions, "get_session", fake_get_session)
    monkeypatch.setattr(
        backfill_profile_schema_versions,
        "normalize_legacy_profile_schema_versions",
        fake_normalize,
    )

    summary = asyncio.run(backfill_profile_schema_versions.run_backfill())

    assert summary == {"scanned": 3, "normalized": 2, "skipped_invalid": 1}
    assert events == ["init", "yield-session", "normalize", "commit", "close-session"]


def test_app_startup_normalizes_selected_legacy_profile_channels():
    engine, session = _make_session()
    app = main_module.create_app()

    async def override_get_session():
        yield AsyncSessionAdapter(session)

    app.dependency_overrides[main_module.get_session] = override_get_session

    try:
        session.add_all(
            [
                Profile(name="startup-esr", schema_version=LEGACY_ESR_140_9, flags={"DisableTelemetry": True}),
                Profile(name="startup-release", schema_version=LEGACY_RELEASE_149, flags={"DisableTelemetry": True}),
                Profile(name="startup-untouched", schema_version=LEGACY_ESR_140_8, flags={"DisableTelemetry": True}),
            ]
        )
        session.commit()

        async def _run_lifespan():
            async with app.router.lifespan_context(app):
                return None

        asyncio.run(_run_lifespan())

        rows = {
            row.name: row.schema_version
            for row in session.scalars(select(Profile).order_by(Profile.name)).all()
        }
        assert rows["startup-esr"] == CURRENT_ESR_SCHEMA_CHANNEL
        assert rows["startup-release"] == CURRENT_RELEASE_SCHEMA_CHANNEL
        assert rows["startup-untouched"] == LEGACY_ESR_140_8
    finally:
        app.dependency_overrides.pop(main_module.get_session, None)
        session.close()
        engine.dispose()
