from __future__ import annotations

import asyncio
import contextlib
import socket
import tempfile
import threading
import time
import uuid
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import requests
import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.schema_channels import CURRENT_ESR_SCHEMA_CHANNEL, CURRENT_RELEASE_SCHEMA_CHANNEL
from app.db import AsyncSessionAdapter, get_session
from app.models.profile import Base
from app.web.firefox_preferences import get_wizard_preferences_catalog
from app.web.firefox_starter_presets import get_wizard_starter_catalog
from app.web.firefox_wizard_shell import get_wizard_schema_shell_catalog
from tests.app_harness import (
    resolve_test_app,
    restore_dependency_overrides,
    snapshot_dependency_overrides,
)


class TestClient:
    """Sync-friendly test client backed by httpx ASGITransport."""

    __test__ = False

    def __init__(
        self,
        app: FastAPI,
        base_url: str = "http://testserver",
        on_close: Any | None = None,
        **kwargs: Any,
    ):
        self.app = app
        self.base_url = base_url
        self._on_close = on_close
        self._client_kwargs = kwargs
        self._runner = asyncio.Runner()
        self._closed = False

    async def _request_async(self, method: str, url: str, **kwargs: Any):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url=self.base_url,
            **self._client_kwargs,
        ) as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any):
        return self._runner.run(self._request_async(method, url, **kwargs))

    def get(self, url: str, **kwargs: Any):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any):
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs: Any):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any):
        return self.request("DELETE", url, **kwargs)

    def put(self, url: str, **kwargs: Any):
        return self.request("PUT", url, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return None

    def close(self):
        if self._closed:
            return
        if self._on_close is not None:
            self._on_close()
            self._on_close = None
        self._runner.close()
        self._closed = True

    def __del__(self):
        try:
            if self._closed:
                return
            self.close()
        except Exception:
            pass


@dataclass(frozen=True, slots=True)
class EnterpriseProfileFixture:
    name: str
    schema_version: str
    starter_key: str
    compliance_layer: str
    flags: dict[str, Any]
    compliance: dict[str, Any]
    payload: dict[str, Any]
    summary: dict[str, Any]
    decisions: list[dict[str, Any]]
    configured_policy_count: int
    configured_preference_count: int
    manual_review_count: int


@dataclass(frozen=True, slots=True)
class AllSettingsInventoryCounts:
    schema_version: str
    total_entries: int
    policy_entries: int
    preference_entries: int
    configured_entries: int
    configured_policy_entries: int
    configured_preference_entries: int
    unknown_policy_entries: int
    imported_preference_entries: int
    guided_policy_entries: int
    raw_fallback_policy_entries: int
    deprecated_policy_entries: int

    def as_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": self.schema_version,
            "total_entries": self.total_entries,
            "policy_entries": self.policy_entries,
            "preference_entries": self.preference_entries,
            "configured_entries": self.configured_entries,
            "configured_policy_entries": self.configured_policy_entries,
            "configured_preference_entries": self.configured_preference_entries,
            "unknown_policy_entries": self.unknown_policy_entries,
            "imported_preference_entries": self.imported_preference_entries,
            "guided_policy_entries": self.guided_policy_entries,
            "raw_fallback_policy_entries": self.raw_fallback_policy_entries,
            "deprecated_policy_entries": self.deprecated_policy_entries,
        }


@dataclass(frozen=True, slots=True)
class AllSettingsSourceStateExpectation:
    entry_id: str
    kind: str
    path: tuple[str, ...]
    expected_sources: tuple[str, ...]
    decision: str = ""
    review_required: bool = False
    raw_fallback: bool = False
    imported_unknown: bool = False
    manually_edited: bool = False


@dataclass(frozen=True, slots=True)
class AllSettingsManualEdit:
    path: tuple[str, ...]
    previous_value: Any
    current_value: Any
    reason: str


@dataclass(frozen=True, slots=True)
class AllSettingsSourceStateFixture:
    id: str
    schema_version: str
    flags: dict[str, Any]
    compliance: dict[str, Any]
    payload: dict[str, Any]
    expectation: AllSettingsSourceStateExpectation
    manual_edits: tuple[AllSettingsManualEdit, ...] = ()


def _iter_all_settings_policy_items(
    schema_version: str,
    wizard_schema_shell_catalog: Mapping[str, Any],
) -> Iterable[tuple[str, Mapping[str, Any]]]:
    channel_data = wizard_schema_shell_catalog["channels"][schema_version]
    seen_ids: set[str] = set()

    for step_meta in wizard_schema_shell_catalog.get("steps", []):
        step_data = channel_data.get("steps", {}).get(str(step_meta["step"]), {})
        for bucket_key in ("recommended", "additional", "raw_fallback"):
            for item in step_data.get(bucket_key, []) or []:
                item_id = item.get("id")
                if not item_id or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                yield bucket_key, item


def build_all_settings_inventory_counts(
    *,
    schema_version: str,
    flags: Mapping[str, Any] | None = None,
) -> AllSettingsInventoryCounts:
    """Mirror the All settings list inventory for test expectations."""

    source_flags = flags or {}
    preferences = (
        source_flags.get("Preferences")
        if isinstance(source_flags.get("Preferences"), Mapping)
        else {}
    )
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    wizard_schema_shell_catalog = get_wizard_schema_shell_catalog(wizard_preferences_catalog)

    policy_items = list(
        _iter_all_settings_policy_items(schema_version, wizard_schema_shell_catalog)
    )
    policy_ids = {item["id"] for _, item in policy_items}
    known_preference_names = {
        item["pref"]
        for item in wizard_preferences_catalog.get("known_preferences", [])
        if item.get("pref")
    }
    configured_policy_ids = {
        key for key in source_flags if key != "Preferences" and key in policy_ids
    }
    unknown_policy_ids = {
        key for key in source_flags if key != "Preferences" and key not in policy_ids
    }
    configured_preference_names = set(preferences)
    imported_preference_names = configured_preference_names - known_preference_names

    return AllSettingsInventoryCounts(
        schema_version=schema_version,
        total_entries=(
            len(policy_items)
            + len(unknown_policy_ids)
            + len(known_preference_names)
            + len(imported_preference_names)
        ),
        policy_entries=len(policy_items) + len(unknown_policy_ids),
        preference_entries=len(known_preference_names) + len(imported_preference_names),
        configured_entries=(
            len(configured_policy_ids)
            + len(unknown_policy_ids)
            + len(configured_preference_names)
        ),
        configured_policy_entries=len(configured_policy_ids) + len(unknown_policy_ids),
        configured_preference_entries=len(configured_preference_names),
        unknown_policy_entries=len(unknown_policy_ids),
        imported_preference_entries=len(imported_preference_names),
        guided_policy_entries=len([item for bucket, item in policy_items if bucket == "recommended"]),
        raw_fallback_policy_entries=len(
            [
                item
                for bucket, item in policy_items
                if bucket == "raw_fallback" or item.get("support_level") == "fallback"
            ]
        ),
        deprecated_policy_entries=len([item for _, item in policy_items if item.get("deprecated")]),
    )


def _decision_path(decision: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(part) for part in decision.get("path", []) if str(part))


def _find_cis_decision(
    decisions: Iterable[Mapping[str, Any]],
    *,
    decision_type: str | None = None,
    review_required: bool | None = None,
    path_prefix: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    for decision in decisions:
        if decision_type is not None and decision.get("decision") != decision_type:
            continue
        if review_required is not None and bool(decision.get("review_required")) is not review_required:
            continue
        path = _decision_path(decision)
        if path_prefix is not None and path[: len(path_prefix)] != path_prefix:
            continue
        return deepcopy(dict(decision))
    raise AssertionError(
        "No CIS decision matched "
        f"decision_type={decision_type!r}, review_required={review_required!r}, "
        f"path_prefix={path_prefix!r}"
    )


def _first_configured_raw_fallback_policy_id(
    *,
    schema_version: str,
    flags: Mapping[str, Any],
) -> str:
    wizard_preferences_catalog = get_wizard_preferences_catalog()
    wizard_schema_shell_catalog = get_wizard_schema_shell_catalog(wizard_preferences_catalog)
    for bucket_key, item in _iter_all_settings_policy_items(
        schema_version,
        wizard_schema_shell_catalog,
    ):
        item_id = item["id"]
        if item_id in flags and (
            bucket_key == "raw_fallback" or item.get("support_level") == "fallback"
        ):
            return item_id
    raise AssertionError(f"No configured raw fallback policy found for {schema_version}")


def _source_state_payload(
    *,
    case_id: str,
    schema_version: str,
    flags: dict[str, Any],
    compliance: dict[str, Any],
) -> dict[str, Any]:
    return build_profile_payload(
        name=f"All settings source-state {case_id}",
        description="Regression fixture for All settings source attribution",
        schema_version=schema_version,
        flags=deepcopy(flags),
        compliance=deepcopy(compliance),
    )


def _source_state_case(
    *,
    case_id: str,
    schema_version: str,
    flags: dict[str, Any],
    compliance: dict[str, Any],
    expectation: AllSettingsSourceStateExpectation,
    manual_edits: tuple[AllSettingsManualEdit, ...] = (),
) -> AllSettingsSourceStateFixture:
    return AllSettingsSourceStateFixture(
        id=case_id,
        schema_version=schema_version,
        flags=deepcopy(flags),
        compliance=deepcopy(compliance),
        payload=_source_state_payload(
            case_id=case_id,
            schema_version=schema_version,
            flags=flags,
            compliance=compliance,
        ),
        expectation=expectation,
        manual_edits=manual_edits,
    )


def build_all_settings_source_state_regression_fixtures(
    *,
    schema_version: str = CURRENT_RELEASE_SCHEMA_CHANNEL,
) -> tuple[AllSettingsSourceStateFixture, ...]:
    """Return compact All settings fixtures for future source attribution tests."""

    enterprise = build_corporate_cis_l2_profile_fixture(schema_version=schema_version)
    added_decision = _find_cis_decision(
        enterprise.decisions,
        decision_type="added_from_cis",
        path_prefix=("DisableDeveloperTools",),
    )
    baseline_decision = _find_cis_decision(
        enterprise.decisions,
        decision_type="kept_base_only",
        path_prefix=("BlockAboutConfig",),
    )
    manual_decision = _find_cis_decision(
        enterprise.decisions,
        review_required=True,
        path_prefix=("Proxy", "Mode"),
    )
    raw_fallback_id = _first_configured_raw_fallback_policy_id(
        schema_version=schema_version,
        flags=enterprise.flags,
    )

    replaced_flags = {
        "BlockAboutConfig": True,
    }
    replaced_decision = {
        "path": ["BlockAboutConfig"],
        "decision": "cis_replaced_base",
        "selected_source": "cis",
        "base_value": False,
        "cis_value": True,
        "selected_value": True,
        "recommendation_ids": ["fixture.cis-replaced"],
        "merge_rule": "boolean_true_is_stricter",
        "review_required": False,
        "reason": "Synthetic regression fixture for CIS replacing a weaker base value.",
    }
    replaced_compliance = {
        **deepcopy(enterprise.compliance),
        "summary": {"cis_replaced_base": 1, "review_required": 0},
        "decisions": [replaced_decision],
    }

    unknown_policy_flags = {
        "CustomEnterprisePolicy": {"Enabled": True},
    }
    unknown_preference_flags = {
        "Preferences": {
            "company.managed.preference": {
                "Value": "strict",
                "Status": "locked",
                "Type": "string",
            },
        },
    }

    manual_edit_path = ("DisableTelemetry",)
    manually_edited_flags = deepcopy(enterprise.flags)
    previous_manual_value = manually_edited_flags[manual_edit_path[0]]
    manually_edited_flags[manual_edit_path[0]] = False
    manual_edit = AllSettingsManualEdit(
        path=manual_edit_path,
        previous_value=previous_manual_value,
        current_value=manually_edited_flags[manual_edit_path[0]],
        reason="Maintainer override after applying the starter and CIS layer.",
    )

    return (
        _source_state_case(
            case_id="baseline-only",
            schema_version=schema_version,
            flags=enterprise.flags,
            compliance=enterprise.compliance,
            expectation=AllSettingsSourceStateExpectation(
                entry_id=baseline_decision["path"][0],
                kind="policy",
                path=_decision_path(baseline_decision),
                expected_sources=("baseline",),
                decision=baseline_decision["decision"],
            ),
        ),
        _source_state_case(
            case_id="cis-added",
            schema_version=schema_version,
            flags=enterprise.flags,
            compliance=enterprise.compliance,
            expectation=AllSettingsSourceStateExpectation(
                entry_id=added_decision["path"][0],
                kind="policy",
                path=_decision_path(added_decision),
                expected_sources=("cis",),
                decision=added_decision["decision"],
            ),
        ),
        _source_state_case(
            case_id="cis-replaced",
            schema_version=schema_version,
            flags=replaced_flags,
            compliance=replaced_compliance,
            expectation=AllSettingsSourceStateExpectation(
                entry_id="BlockAboutConfig",
                kind="policy",
                path=("BlockAboutConfig",),
                expected_sources=("cis", "baseline"),
                decision="cis_replaced_base",
            ),
        ),
        _source_state_case(
            case_id="manual-review",
            schema_version=schema_version,
            flags=enterprise.flags,
            compliance=enterprise.compliance,
            expectation=AllSettingsSourceStateExpectation(
                entry_id=manual_decision["path"][0],
                kind="policy",
                path=_decision_path(manual_decision),
                expected_sources=("baseline", "cis"),
                decision=manual_decision["decision"],
                review_required=True,
            ),
        ),
        _source_state_case(
            case_id="imported-unknown-policy",
            schema_version=schema_version,
            flags=unknown_policy_flags,
            compliance={},
            expectation=AllSettingsSourceStateExpectation(
                entry_id="CustomEnterprisePolicy",
                kind="policy",
                path=("CustomEnterprisePolicy",),
                expected_sources=("imported", "unknown"),
                imported_unknown=True,
            ),
        ),
        _source_state_case(
            case_id="imported-unknown-preference",
            schema_version=schema_version,
            flags=unknown_preference_flags,
            compliance={},
            expectation=AllSettingsSourceStateExpectation(
                entry_id="company.managed.preference",
                kind="preference",
                path=("Preferences", "company.managed.preference"),
                expected_sources=("imported", "unknown"),
                imported_unknown=True,
            ),
        ),
        _source_state_case(
            case_id="raw-fallback-policy",
            schema_version=schema_version,
            flags=enterprise.flags,
            compliance=enterprise.compliance,
            expectation=AllSettingsSourceStateExpectation(
                entry_id=raw_fallback_id,
                kind="policy",
                path=(raw_fallback_id,),
                expected_sources=("raw-fallback",),
                raw_fallback=True,
            ),
        ),
        _source_state_case(
            case_id="manually-edited-setting",
            schema_version=schema_version,
            flags=manually_edited_flags,
            compliance=enterprise.compliance,
            expectation=AllSettingsSourceStateExpectation(
                entry_id=manual_edit_path[0],
                kind="policy",
                path=manual_edit_path,
                expected_sources=("manual", "baseline", "cis"),
                decision="already_satisfied",
                manually_edited=True,
            ),
            manual_edits=(manual_edit,),
        ),
    )


def build_profile_payload(
    *,
    name_prefix: str = "Profile",
    description: str = "Test profile",
    schema_version: str = "esr-140.12",
    flags: dict[str, Any] | None = None,
    compliance: dict[str, Any] | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    payload = {
        "name": name or f"{name_prefix}-{uuid.uuid4().hex[:6]}",
        "description": description,
        "schema_version": schema_version,
        "flags": flags or {"DisableTelemetry": True},
    }
    if compliance is not None:
        payload["compliance"] = compliance
    return payload


def build_corporate_cis_l2_profile_fixture(
    *,
    schema_version: str = CURRENT_RELEASE_SCHEMA_CHANNEL,
    name: str | None = None,
) -> EnterpriseProfileFixture:
    catalog = get_wizard_starter_catalog()
    starter_key = "basic_corporate"
    compliance_layer = "cis_l2"
    merged = catalog["compliance_merged_presets"][starter_key][compliance_layer][schema_version]
    flags = deepcopy(merged["policy_values"])
    summary = deepcopy(merged["summary"])
    decisions = deepcopy(merged["decisions"])
    metadata = catalog["compliance_metadata"]
    compliance = {
        "framework": "cis",
        "benchmark_id": metadata.get("benchmark_id") or "cis-firefox-esr-gpo",
        "benchmark_version": metadata.get("upstream_version") or "1.0.0",
        "layer": compliance_layer,
        "summary": summary,
        "decisions": decisions,
    }
    fixture_name = name or f"Corporate CIS L2 {schema_version}"
    payload = build_profile_payload(
        name=fixture_name,
        description="Corporate baseline with CIS Level 2 overlay",
        schema_version=schema_version,
        flags=deepcopy(flags),
        compliance=deepcopy(compliance),
    )
    preferences = flags.get("Preferences") if isinstance(flags.get("Preferences"), dict) else {}

    return EnterpriseProfileFixture(
        name=fixture_name,
        schema_version=schema_version,
        starter_key=starter_key,
        compliance_layer=compliance_layer,
        flags=flags,
        compliance=compliance,
        payload=payload,
        summary=summary,
        decisions=decisions,
        configured_policy_count=len([key for key in flags if key != "Preferences"]),
        configured_preference_count=len(preferences),
        manual_review_count=len(
            [decision for decision in decisions if decision.get("review_required")]
        ),
    )


def build_corporate_cis_l2_profile_fixtures() -> tuple[EnterpriseProfileFixture, ...]:
    return (
        build_corporate_cis_l2_profile_fixture(schema_version=CURRENT_ESR_SCHEMA_CHANNEL),
        build_corporate_cis_l2_profile_fixture(schema_version=CURRENT_RELEASE_SCHEMA_CHANNEL),
    )


def make_test_client(app: FastAPI | None = None, **kwargs: Any) -> TestClient:
    """
    Build a sync-friendly ASGI test client.

    No application resolves to a fresh app instance. Explicit app instances are
    preserved, with their complete dependency override maps restored on close.
    """
    app = resolve_test_app(app)

    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    testing_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = testing_session_factory()
    override_snapshot = snapshot_dependency_overrides(app)

    async def override_get_session():
        yield AsyncSessionAdapter(session)

    app.dependency_overrides[get_session] = override_get_session

    def _cleanup() -> None:
        restore_dependency_overrides(app, override_snapshot)
        session.close()
        engine.dispose()

    return TestClient(app, on_close=_cleanup, **kwargs)


def assert_contains_all(text: str, snippets: Iterable[str]) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"Missing expected snippets: {missing[:10]}"


def assert_has_keys(mapping: Mapping[str, Any], keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in mapping]
    assert not missing, f"Missing expected keys: {missing[:10]}"


def pick_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


@dataclass
class TestAppServerHandle:
    base_url: str
    session_factory: Any


@contextlib.contextmanager
def run_test_app_server_handle(
    *,
    host: str = "127.0.0.1",
    log_level: str = "warning",
    startup_timeout: float = 20.0,
):
    """
    Run a fresh app instance behind a local uvicorn server for browser tests.

    This variant also exposes the sync SQLAlchemy session factory so tests can
    seed legacy or otherwise non-API-representable data directly into the
    temporary browser-test database.
    """

    app = resolve_test_app()
    with tempfile.TemporaryDirectory(prefix="bpm-ui-server-") as tmp_dir:
        db_path = Path(tmp_dir) / "bpm-ui.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
        testing_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        Base.metadata.create_all(bind=engine)

        async def override_get_session():
            session = testing_session_factory()
            try:
                yield AsyncSessionAdapter(session)
            finally:
                session.close()

        override_snapshot = snapshot_dependency_overrides(app)
        app.dependency_overrides[get_session] = override_get_session
        port = pick_free_port(host)
        config = uvicorn.Config(app=app, host=host, port=port, log_level=log_level)
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        base_url = f"http://{host}:{port}"
        deadline = time.time() + startup_timeout
        last_error: str | None = None

        try:
            while time.time() < deadline:
                try:
                    response = requests.get(f"{base_url}/i18n/en.json", timeout=2)
                    if response.status_code == 200:
                        break
                    last_error = f"probe returned {response.status_code}"
                except requests.RequestException as exc:
                    last_error = str(exc)
                time.sleep(0.2)
            else:
                raise RuntimeError(f"Timed out waiting for test app server at {base_url}: {last_error}")

            yield TestAppServerHandle(
                base_url=base_url,
                session_factory=testing_session_factory,
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            restore_dependency_overrides(app, override_snapshot)
            engine.dispose()


@contextlib.contextmanager
def run_test_app_server(
    *,
    host: str = "127.0.0.1",
    log_level: str = "warning",
    startup_timeout: float = 20.0,
):
    """
    Run a fresh app instance behind a local uvicorn server for browser tests.

    The server uses a temporary SQLite database and request-scoped sessions so
    multi-tab browser regressions can exercise the real HTTP surface safely.
    """

    with run_test_app_server_handle(
        host=host,
        log_level=log_level,
        startup_timeout=startup_timeout,
    ) as handle:
        yield handle.base_url
