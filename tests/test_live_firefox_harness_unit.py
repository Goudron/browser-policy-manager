from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from tests.live_firefox.helpers import build_test_extension_xpi, resolve_binary_path


def test_resolve_binary_path_prefers_env_override(tmp_path: Path):
    env_binary = tmp_path / "custom-firefox"
    env_binary.write_text("", encoding="utf-8")

    fallback_binary = tmp_path / "fallback-firefox"
    fallback_binary.write_text("", encoding="utf-8")

    resolved = resolve_binary_path(str(env_binary), [fallback_binary])

    assert resolved == env_binary.resolve()


def test_resolve_binary_path_falls_back_to_project_candidate(tmp_path: Path):
    fallback_binary = tmp_path / "fallback-firefox"
    fallback_binary.write_text("", encoding="utf-8")

    resolved = resolve_binary_path(None, [fallback_binary])

    assert resolved == fallback_binary.resolve()


def test_resolve_binary_path_returns_none_when_nothing_exists(tmp_path: Path):
    missing = tmp_path / "missing-firefox"

    assert resolve_binary_path(None, [missing]) is None


def test_build_test_extension_xpi_packages_fixture_files(tmp_path: Path):
    source_dir = tmp_path / "extension-src"
    source_dir.mkdir()
    (source_dir / "manifest.json").write_text('{"name":"fixture"}', encoding="utf-8")
    (source_dir / "background.js").write_text("console.log('fixture');", encoding="utf-8")

    output_path = build_test_extension_xpi(source_dir, tmp_path / "out" / "fixture.xpi")

    assert output_path.is_file()
    with ZipFile(output_path) as archive:
        names = sorted(archive.namelist())

    assert names == ["background.js", "manifest.json"]
