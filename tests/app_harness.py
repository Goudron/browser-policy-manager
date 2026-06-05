from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

DependencyOverrides = dict[Callable[..., Any], Callable[..., Any]]


def fresh_test_app() -> FastAPI:
    """Build a fresh FastAPI application instance for one test client or fixture."""
    from app.main import create_app

    return create_app()


def resolve_test_app(candidate: FastAPI | None = None) -> FastAPI:
    """
    Return an isolated app for tests.

    New tests should omit the candidate and receive a fresh app. Explicit app
    instances are preserved for legacy serial contracts and custom app tests;
    their dependency override maps are still snapshot/restored by client helpers.
    """
    if candidate is None:
        return fresh_test_app()
    return candidate


def snapshot_dependency_overrides(app: FastAPI) -> DependencyOverrides:
    return dict(app.dependency_overrides)


def restore_dependency_overrides(app: FastAPI, snapshot: DependencyOverrides) -> None:
    """Restore the complete dependency override mapping after a test client closes."""
    app.dependency_overrides.clear()
    app.dependency_overrides.update(snapshot)
