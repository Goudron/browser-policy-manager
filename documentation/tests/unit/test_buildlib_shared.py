from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path

import pytest

from documentation.buildlib import shared


def test_shared_module_bootstraps_repository_path_when_imported_directly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = str(shared.REPOSITORY_ROOT)
    monkeypatch.setattr(sys, "path", [entry for entry in sys.path if entry != repository])
    runpy.run_path(str(Path(shared.__file__)), run_name="documentation_shared_direct")
    assert repository in sys.path


def test_product_header_labels_accept_current_catalog_and_wrap_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert shared._product_header_labels("en")["locales"]
    monkeypatch.setattr(shared, "REPOSITORY_ROOT", tmp_path)
    with pytest.raises(shared.BuildError, match="cannot read product locale catalog"):
        shared._product_header_labels("en")
    catalog = tmp_path / "app/i18n/en.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text("{}", encoding="utf-8")
    with pytest.raises(shared.BuildError, match="missing header labels"):
        shared._product_header_labels("en")


def test_product_version_and_toolchain_lock_are_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shared, "REPOSITORY_ROOT", tmp_path)
    project = tmp_path / "pyproject.toml"
    project.write_text('[project]\nversion = "0.9.4"\n', encoding="utf-8")
    assert shared._product_version() == "0.9.4"
    project.write_text("[", encoding="utf-8")
    with pytest.raises(shared.BuildError, match="cannot read product version"):
        shared._product_version()
    project.write_text('[project]\nversion = ""\n', encoding="utf-8")
    with pytest.raises(shared.BuildError, match="missing or invalid"):
        shared._product_version()

    lock_path = tmp_path / "lock.json"
    monkeypatch.setattr(shared, "LOCK_PATH", lock_path)
    lock_path.write_text(json.dumps({"cache_directory": ".cache"}), encoding="utf-8")
    assert shared._load_lock() == {"cache_directory": ".cache"}
    lock_path.write_text("{", encoding="utf-8")
    with pytest.raises(shared.BuildError, match="cannot read toolchain lock"):
        shared._load_lock()


def test_toolchain_resolves_both_locked_executables_and_names_missing_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = {
        "cache_directory": ".cache",
        "components": {"dita_ot": {"version": "4.4"}, "java": {"version": "21"}},
    }
    monkeypatch.setattr(shared, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(shared, "_load_lock", lambda: lock)
    dita = tmp_path / ".cache/installs/dita-ot-4.4/bin/dita"
    java = tmp_path / ".cache/installs/temurin-jre-21/bin/java"
    for executable in (dita, java):
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(executable.stat().st_mode | 0o111)

    assert shared.toolchain() == (dita, java.parent.parent)
    os.chmod(java, 0o644)
    with pytest.raises(shared.BuildError, match="locked toolchain executable is missing"):
        shared.toolchain()
