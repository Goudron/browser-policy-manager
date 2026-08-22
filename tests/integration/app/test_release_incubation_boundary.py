from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from tools import release_boundary_contract

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "tools" / "release_boundary_manifest_0_9_5.json"


def test_boundary_manifest_classifies_every_declared_delivery_extra() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["target_version"] == "0.9.6"
    assert set(manifest["categories"]) == {
        "default_release",
        "optional_incubation",
        "development_tooling",
        "release_optional_integration",
    }
    assert manifest["categories"]["optional_incubation"]["fixtures"] == []
    assert "tmp_path" in manifest["rules"]["optional_incubation_fixture_policy"]
    assert manifest["rules"]["release_safe_disabled_surfaces"] == [
        "/api/documentation-assistant/status?locale=en",
        "/api/local-model",
    ]


def test_boundary_contract_validates_manifest_without_running_the_expensive_wheel_smoke() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "tools/release_boundary_contract.py",
            "--skip-clean-wheel-smoke",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "release/incubation/development classification: OK" in completed.stdout


def test_boundary_contract_rejects_an_unclassified_extra(monkeypatch) -> None:
    manifest = release_boundary_contract._load_manifest()
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject["project"]["optional-dependencies"]["unexpected"] = []
    monkeypatch.setattr(release_boundary_contract.tomllib, "loads", lambda _: pyproject)

    try:
        release_boundary_contract._verify_classification(manifest)
    except AssertionError:
        pass
    else:
        raise AssertionError(
            "an unclassified optional extra must fail the release boundary contract"
        )
