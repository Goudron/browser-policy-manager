from __future__ import annotations

import hashlib
import json
import os
import tarfile
from pathlib import Path

import pytest

from tools.provision_firefox_live_browsers import (
    ProvisioningError,
    installation_root,
    load_spec,
    provision,
    verify_installation,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "tools" / "firefox_live_browsers_manifest_0_9_4.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_executable(path: Path, output: str) -> None:
    path.write_text(f"#!/usr/bin/env bash\necho '{output}'\n", encoding="utf-8")
    path.chmod(0o755)


def _archive_fixture(tmp_path: Path) -> tuple[Path, Path]:
    firefox_tree = tmp_path / "firefox-source" / "firefox"
    firefox_tree.mkdir(parents=True)
    _write_executable(firefox_tree / "firefox", "Mozilla Firefox 153.0.1")
    firefox_archive = tmp_path / "firefox.tar.xz"
    with tarfile.open(firefox_archive, "w:xz") as archive:
        archive.add(firefox_tree, arcname="firefox")

    geckodriver = tmp_path / "geckodriver"
    _write_executable(geckodriver, "geckodriver 0.37.1 (fixture)")
    geckodriver_archive = tmp_path / "geckodriver.tar.gz"
    with tarfile.open(geckodriver_archive, "w:gz") as archive:
        archive.add(geckodriver, arcname="geckodriver")
    return firefox_archive, geckodriver_archive


def _fixture_manifest(tmp_path: Path) -> Path:
    firefox_archive, geckodriver_archive = _archive_fixture(tmp_path)
    payload = {
        "schema_version": 1,
        "platforms": {
            "linux-x86_64": {
                "firefox": {
                    "release": {
                        "version": "153.0.1",
                        "url": firefox_archive.as_uri(),
                        "sha256": _sha256(firefox_archive),
                        "archive": firefox_archive.name,
                    }
                },
                "geckodriver": {
                    "version": "0.37.1",
                    "url": geckodriver_archive.as_uri(),
                    "sha256": _sha256(geckodriver_archive),
                    "archive": geckodriver_archive.name,
                },
            }
        },
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_pinned_manifest_covers_exact_release_and_both_esr_channels() -> None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    firefox = payload["platforms"]["linux-x86_64"]["firefox"]

    assert {channel: firefox[channel]["version"] for channel in firefox} == {
        "release": "153.0.1",
        "esr153": "153.0esr",
        "esr140": "140.13.0esr",
    }
    for entry in [*firefox.values(), payload["platforms"]["linux-x86_64"]["geckodriver"]]:
        assert entry["url"].startswith("https://")
        assert len(entry["sha256"]) == 64


def test_provisioning_reuses_only_verified_archive_and_reports_versions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = load_spec(_fixture_manifest(tmp_path), channel="release", platform_name="linux-x86_64")
    root = tmp_path / "browsers"

    installed, provenance = provision(root, spec)

    assert installed == installation_root(root, spec)
    assert provenance["policy_root_mode"] == "clone-per-test-run"
    assert provenance["firefox"]["actual_version"] == "Mozilla Firefox 153.0.1"
    assert provenance["geckodriver"]["actual_version"].startswith("geckodriver 0.37.1")
    assert not os.access(installed / "firefox", os.W_OK)
    first_output = capsys.readouterr().out
    assert "Downloading Firefox 153.0.1" in first_output
    assert "downloaded " in first_output
    assert "Verified Firefox SHA-256" in first_output

    provision(root, spec, force=True)
    assert "Reusing checksum-verified Firefox archive" in capsys.readouterr().out
    assert verify_installation(root, spec)["channel"] == "release"


def test_provisioning_rejects_tampered_provenance_before_reuse(tmp_path: Path) -> None:
    spec = load_spec(_fixture_manifest(tmp_path), channel="release", platform_name="linux-x86_64")
    root = tmp_path / "browsers"
    installed, _provenance = provision(root, spec)
    provenance_path = installed / "installation.json"
    provenance_path.chmod(0o644)
    tampered = json.loads(provenance_path.read_text(encoding="utf-8"))
    tampered["firefox"]["sha256"] = "0" * 64
    provenance_path.write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(ProvisioningError, match="provenance"):
        verify_installation(root, spec)


def test_provisioning_discards_a_corrupt_cache_entry_before_extraction(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = load_spec(_fixture_manifest(tmp_path), channel="release", platform_name="linux-x86_64")
    root = tmp_path / "browsers"
    provision(root, spec)
    cache_path = root / "cache" / "sha256" / spec.firefox.sha256 / spec.firefox.archive
    cache_path.write_bytes(b"not the manifest-pinned archive")

    provision(root, spec, force=True)

    assert "Discarding corrupt cached Firefox archive" in capsys.readouterr().out
    assert hashlib.sha256(cache_path.read_bytes()).hexdigest() == spec.firefox.sha256
