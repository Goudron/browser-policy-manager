from __future__ import annotations

import json

import pytest

from app.schemas.schema_manager import (
    SchemaDownloadError,
    SchemaManager,
    SchemaManagerError,
    SchemaNotFoundError,
    SchemaVersion,
    normalize_schema_for_internal_use,
)


def test_schema_version_refs_and_invalid_key():
    assert SchemaVersion.from_key("firefox-esr1409") is SchemaVersion.ESR1409
    assert SchemaVersion.from_key("firefox-release149") is SchemaVersion.RELEASE149
    assert SchemaVersion.ESR1409.cache_subdir == "esr1409"
    assert "main" in SchemaVersion.RELEASE149.refs

    with pytest.raises(ValueError):
        SchemaVersion.from_key("beta999")


def test_load_raises_not_found_without_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("app.schemas.schema_manager.DEFAULT_RETRY", 0)
    manager = SchemaManager(cache_dir=str(tmp_path / "cache"), fetcher=lambda url, timeout: (503, b""))

    with pytest.raises(SchemaNotFoundError):
        manager.load("esr1409")


def test_read_json_invalid_content_raises(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SchemaManagerError):
        SchemaManager._read_json(bad_file)


def test_update_cache_returns_schema_meta(tmp_path):
    payload = {"title": "Policies", "type": "object"}
    content = json.dumps(payload).encode("utf-8")
    manager = SchemaManager(cache_dir=str(tmp_path / "cache"), fetcher=lambda url, timeout: (200, content))

    meta = manager.update_cache("release149")

    assert meta.version is SchemaVersion.RELEASE149
    assert meta.cache_path.exists()
    assert meta.source_url.endswith("policies-schema.json")
    assert meta.sha256


def test_download_and_cache_raises_download_error_when_all_candidates_fail(tmp_path, monkeypatch):
    monkeypatch.setattr("app.schemas.schema_manager.DEFAULT_RETRY", 0)
    manager = SchemaManager(cache_dir=str(tmp_path / "cache"), fetcher=lambda url, timeout: (404, b""))

    with pytest.raises(SchemaDownloadError):
        manager.update_cache("esr1409")


def test_load_force_refresh_falls_back_to_existing_cache_on_download_error(tmp_path, monkeypatch):
    monkeypatch.setattr("app.schemas.schema_manager.DEFAULT_RETRY", 0)
    cache_dir = tmp_path / "cache"
    manager = SchemaManager(cache_dir=str(cache_dir), fetcher=lambda url, timeout: (200, b'{"title":"cached"}'))
    assert manager.load("release149")["title"] == "cached"

    failing = SchemaManager(cache_dir=str(cache_dir), fetcher=lambda url, timeout: (503, b""))

    assert failing.load("release149", force_refresh=True)["title"] == "cached"


def test_download_and_cache_continues_after_fetch_exception(tmp_path, monkeypatch):
    monkeypatch.setattr("app.schemas.schema_manager.DEFAULT_RETRY", 0)
    payload = json.dumps({"title": "Recovered"}).encode("utf-8")
    calls = {"count": 0}

    def _fetcher(url, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("transient failure")
        return 200, payload

    manager = SchemaManager(cache_dir=str(tmp_path / "cache"), fetcher=_fetcher)

    meta = manager.update_cache("esr1409")

    assert meta.cache_path.exists()
    assert json.loads(meta.cache_path.read_text(encoding="utf-8"))["title"] == "Recovered"


def test_default_fetcher_uses_requests(monkeypatch):
    class _Response:
        status_code = 200
        content = b"{}"

    called = {}

    def _fake_get(url, timeout):
        called["url"] = url
        called["timeout"] = timeout
        return _Response()

    monkeypatch.setattr("app.schemas.schema_manager.requests.get", _fake_get)

    status, content = SchemaManager._default_fetcher("https://example.test/schema.json", 7)

    assert status == 200
    assert content == b"{}"
    assert called == {"url": "https://example.test/schema.json", "timeout": 7}


def test_normalize_schema_for_internal_use_adds_meta(monkeypatch):
    monkeypatch.setattr("app.schemas.schema_manager.time.time", lambda: 1234567890)
    original = {"title": "Policies"}

    normalized = normalize_schema_for_internal_use(original, SchemaVersion.ESR1409)

    assert normalized["title"] == "Policies"
    assert normalized["$meta"]["bpm_source_version"] == "esr1409"
    assert normalized["$meta"]["bpm_generated_at"] == 1234567890


def test_schema_version_refs_fallback_branch_for_unknown_member():
    assert SchemaVersion.refs.fget(object()) == ["main"]
