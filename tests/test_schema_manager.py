"""
Tests for SchemaManager.

These tests avoid real network calls by injecting a fake fetcher.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas import SchemaManager


def fake_fetcher_factory(payload: dict, status: int = 200):
    """
    Returns a fetcher(url, timeout) -> (status, content) that ignores URL
    and returns the given payload/status. Useful for deterministic tests.
    """
    data = json.dumps(payload).encode("utf-8")

    def _fetcher(_url: str, _timeout: int) -> tuple[int, bytes]:
        return status, data

    return _fetcher


def test_compute_cache_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    manager = SchemaManager(cache_dir=str(tmp_path / "cache"))
    p_esr = manager.compute_cache_path("esr140")
    p_rel = manager.compute_cache_path("release144")

    assert p_esr.name == "policies-schema.json"
    assert p_esr.parent.name == "esr140"
    assert p_rel.parent.name == "release144"


def test_load_writes_cache_and_reads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Arrange: a minimal valid schema payload
    payload = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Policies",
        "type": "object",
    }
    manager = SchemaManager(
        cache_dir=str(tmp_path / "cache"),
        fetcher=fake_fetcher_factory(payload),
    )

    # Act: load (no cache present yet -> triggers download)
    result = manager.load("esr140", force_refresh=False)

    # Assert: got the payload back and file exists
    assert result["title"] == "Policies"
    cache_file = manager.compute_cache_path("esr140")
    assert cache_file.exists()
    # File content matches
    on_disk = json.loads(cache_file.read_text(encoding="utf-8"))
    assert on_disk == payload


def test_load_falls_back_to_cache_on_network_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # First, populate cache with a successful fetcher
    initial_payload = {"title": "CachedPolicies"}
    ok_fetcher = fake_fetcher_factory(initial_payload)
    manager = SchemaManager(cache_dir=str(tmp_path / "cache"), fetcher=ok_fetcher)
    assert manager.load("release144")["title"] == "CachedPolicies"

    # Now simulate network failure
    def failing_fetcher(_url: str, _timeout: int):
        return 503, b""

    manager_fail = SchemaManager(cache_dir=str(tmp_path / "cache"), fetcher=failing_fetcher)
    # Should fall back to cache and still return the cached payload
    assert manager_fail.load("release144")["title"] == "CachedPolicies"
