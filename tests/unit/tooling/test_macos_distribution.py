from __future__ import annotations

import json
from pathlib import Path

from tools import macos_distribution

REPO_ROOT = Path(__file__).resolve().parents[3]
MACOS_ROOT = REPO_ROOT / "distributions" / "macos"


def test_macos_targets_are_separate_native_intel_and_apple_silicon_dmgs() -> None:
    targets = macos_distribution.load_targets()

    assert [(target.identifier, target.architecture, target.runner) for target in targets] == [
        ("macos-14-arm64", "arm64", "macos-14"),
        ("macos-14-x64", "x64", "macos-15-intel"),
    ]
    manifest = json.loads((MACOS_ROOT / "targets.json").read_text(encoding="utf-8"))
    assert manifest["installer_format"] == "dmg"
    assert manifest["minimum_macos_version"] == "14"
    assert manifest["application"]["state_directory"].startswith("~/Library/")


def test_macos_release_inputs_are_complete_and_bound_to_current_bpm_version() -> None:
    targets = macos_distribution.validate_release_inputs()

    assert macos_distribution._project_version() == "0.9.5"
    assert all(target.artifact.endswith(".dmg") for target in targets)


def test_macos_bundle_preserves_native_runtime_and_explicit_lifecycle_boundaries() -> None:
    builder = (MACOS_ROOT / "build-dmg.sh").read_text(encoding="utf-8")
    smoke = (MACOS_ROOT / "smoke-dmg.sh").read_text(encoding="utf-8")
    launcher = (MACOS_ROOT / "launcher.py").read_text(encoding="utf-8")
    migrator = (MACOS_ROOT / "BPM Migrate.command.in").read_text(encoding="utf-8")

    assert "PyInstaller" in builder
    assert 'PYTHON="${PYTHON_EXECUTABLE:-python}"' in builder
    assert "--hidden-import migration_support.retirement_owner_v1" in builder
    assert "--collect-submodules app" not in builder
    assert "file --brief \"$candidate\" | grep --quiet 'Mach-O'" in builder
    assert 'codesign --force --sign - "$APP_ROOT"' in builder
    assert "hdiutil create" in builder
    assert "system Python" not in builder
    assert "BPM_DATABASE_URL" in launcher
    assert 'choices=("migrate", "serve")' in launcher
    assert "command.upgrade" in launcher
    assert "migrate" in migrator
    assert 'test ! -e "$STATE_ROOT/bpm.db"' in smoke
    assert "start_verify_stop" in smoke
    assert "codesign --verify --deep --strict" in smoke


def test_macos_make_targets_and_manual_workflow_keep_test_status_explicit() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    workflow = (
        REPO_ROOT / ".github" / "workflows" / "macos-native-distribution-smoke.yml"
    ).read_text(encoding="utf-8")

    assert "macos-package-build: docs-package-verify macos-package-validate" in makefile
    assert "macos-package-smoke: macos-package-validate" in makefile
    assert "macos-package-release-gate: docs-package-verify macos-package-validate" in makefile
    assert "workflow_dispatch:" in workflow
    assert "inputs.run_macos_dmg == 'RUN'" in workflow
    assert "macos-15-intel" in workflow
    assert "macos-14" in workflow
    assert "ad-hoc test signature only" in workflow
    assert "Apple notarization" in workflow
