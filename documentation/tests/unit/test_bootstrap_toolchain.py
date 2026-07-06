from __future__ import annotations

import importlib.util
import io
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "documentation/tools/bootstrap_toolchain.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_toolchain", MODULE_PATH)
assert SPEC and SPEC.loader
bootstrap_toolchain = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap_toolchain)


def test_lock_pins_supported_archives_and_test_dependencies() -> None:
    lock = bootstrap_toolchain.load_lock(ROOT / "documentation/config/toolchain-lock.json")

    assert lock["supported_platforms"] == ["linux-x86_64"]
    assert lock["components"]["dita_ot"]["version"] == "4.4"
    assert len(lock["components"]["dita_ot"]["archive"]["sha256"]) == 64
    java = lock["components"]["java"]
    assert java["version"] == "21.0.11+10"
    assert len(java["platforms"]["linux-x86_64"]["archive"]["sha256"]) == 64

    requirements = (ROOT / lock["python"]["requirements_lock"]).read_text(encoding="utf-8")
    pins = [line for line in requirements.splitlines() if line and not line.startswith("#")]
    assert pins
    assert all("==" in pin and not pin.endswith("==") for pin in pins)


def test_lock_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    lock = tmp_path / "lock.json"
    lock.write_text('{"schema_version": 1, "schema_version": 1}', encoding="utf-8")

    with pytest.raises(bootstrap_toolchain.BootstrapError, match="duplicate JSON key"):
        bootstrap_toolchain.load_lock(lock)


def test_zip_extraction_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        bundle.writestr("expected/../../escape", "unsafe")
    archive.write_bytes(buffer.getvalue())

    with pytest.raises(bootstrap_toolchain.BootstrapError, match="unsafe archive member"):
        bootstrap_toolchain.extract_archive(archive, tmp_path / "out", "zip", "expected")


def test_cached_archive_must_match_locked_digest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = tmp_path / "source.zip"
    payload.write_bytes(b"locked")
    digest = bootstrap_toolchain.sha256(payload)
    spec = {"url": "https://invalid.example/tool.zip", "sha256": digest}
    cache = tmp_path / "cache"
    cache.mkdir()
    cached = cache / f"{digest}-tool.zip"
    cached.write_bytes(b"locked")
    monkeypatch.setattr(bootstrap_toolchain.urllib.request, "urlopen", lambda *_a, **_k: None)

    assert bootstrap_toolchain.ensure_archive(spec, cache, offline=True) == cached

    cached.write_bytes(b"tampered")
    with pytest.raises(bootstrap_toolchain.BootstrapError, match="absent from offline cache"):
        bootstrap_toolchain.ensure_archive(spec, cache, offline=True)
