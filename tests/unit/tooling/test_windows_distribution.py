from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import windows_distribution

REPO_ROOT = Path(__file__).resolve().parents[3]
WINDOWS_ROOT = REPO_ROOT / "distributions" / "windows"


def test_windows_target_is_one_native_x64_msi_for_windows_10_and_11() -> None:
    target = windows_distribution.load_target()

    assert target.artifact == "browser-policy-manager-0.9.6-windows-x64.msi"
    assert target.python_version == "3.14.6"
    assert target.wix_version == "4.0.6"
    manifest = json.loads((WINDOWS_ROOT / "targets.json").read_text(encoding="utf-8"))
    assert manifest["supported_platforms"] == ["Windows 10 x64", "Windows 11 x64"]
    assert manifest["installer"]["service_account"] == "NT AUTHORITY\\LocalService"


def test_windows_release_inputs_are_complete_and_bound_to_current_bpm_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "bpm-documentation-0.9.5.tar.gz"
    archive.write_bytes(b"verified unit-test documentation archive")
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(
        f"{windows_distribution._sha256(archive)}  {archive.name}\n", encoding="ascii"
    )
    monkeypatch.setattr(windows_distribution, "_documentation_archive", lambda: (archive, checksum))

    target = windows_distribution.validate_release_inputs()

    assert windows_distribution._project_version() == "0.9.6"
    assert target.winsw_version == "2.12.0"


def test_windows_msi_payload_preserves_native_and_explicit_lifecycle_boundaries() -> None:
    product = (WINDOWS_ROOT / "Product.wxs").read_text(encoding="utf-8")
    builder = (WINDOWS_ROOT / "build-msi.ps1").read_text(encoding="utf-8")
    migrator = (WINDOWS_ROOT / "templates" / "bpm-migrate.cmd").read_text(encoding="utf-8")
    service = (WINDOWS_ROOT / "templates" / "bpm-service.xml").read_text(encoding="utf-8")
    smoke = (WINDOWS_ROOT / "smoke-msi.ps1").read_text(encoding="utf-8")

    assert 'Start="demand"' in product
    assert 'Account="NT AUTHORITY\\LocalService"' in product
    assert 'Permanent="yes" NeverOverwrite="yes">' in product
    assert '<ComponentGroupRef Id="BpmPayload" />' in product
    assert "<Files " not in product
    assert "New-HarvestedPayloadFragment" in builder
    assert "harvested-payload.wxs" in builder
    assert "Get-StableWixId" in builder
    assert "New-WindowsAlembicConfiguration" in builder
    assert "-Encoding ascii" in builder
    assert "net session" in migrator
    assert "alembic" in migrator
    assert "runtime\\python.exe" in migrator
    assert "bpm-service.cmd" in service
    assert "runtime\\python.exe" in (WINDOWS_ROOT / "templates" / "bpm-service.cmd").read_text(
        encoding="utf-8"
    )
    assert "MSI started BPM during installation" in smoke
    assert "ordinary MSI uninstall removed the operator-owned BPM database" in smoke
    assert "${Url}: expected" in builder


def test_windows_lock_keeps_base_runtime_without_optional_ai_or_unsupported_uvloop() -> None:
    lock = (WINDOWS_ROOT / "requirements.windows.lock").read_text(encoding="utf-8")

    assert "typing-inspection==0.4.4" in lock
    assert "uvloop==" not in lock
    assert "numpy==" not in lock
    assert "onnxruntime==" not in lock
    assert "tokenizers==" not in lock


def test_windows_make_targets_and_manual_workflows_keep_signing_and_platform_proof_explicit() -> (
    None
):
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    smoke_workflow = (
        REPO_ROOT / ".github" / "workflows" / "windows-native-distribution-smoke.yml"
    ).read_text(encoding="utf-8")
    publish_workflow = (
        REPO_ROOT / ".github" / "workflows" / "windows-native-release-publish.yml"
    ).read_text(encoding="utf-8")
    compatibility_workflow = (
        REPO_ROOT / ".github" / "workflows" / "windows-native-compatibility.yml"
    ).read_text(encoding="utf-8")

    assert "windows-package-build: docs-package-verify windows-package-validate" in makefile
    assert "windows-package-smoke: windows-package-validate" in makefile
    assert "windows-package-stage-release: windows-package-validate" in makefile
    assert "windows-package-release-gate: docs-package-verify windows-package-validate" in makefile
    assert "workflow_dispatch:" in smoke_workflow
    assert "inputs.run_windows_msi == 'RUN'" in smoke_workflow
    assert "runs-on: windows-2022" in smoke_workflow
    assert "actual Windows 10 x64" in smoke_workflow
    assert "actions/setup-node@v6" in smoke_workflow
    assert "make build-profile-frontend-bundles" in smoke_workflow
    assert "Restore byte-exact release sources" in smoke_workflow
    assert "core.autocrlf false" in smoke_workflow
    assert "inputs.publish_windows_release == 'PUBLISH'" in publish_workflow
    assert "BPM_WINDOWS_SIGNING_CERTIFICATE_BASE64" in publish_workflow
    assert "python tools/windows_distribution.py stage-release" in publish_workflow
    assert "gh release" in publish_workflow
    assert "make build-profile-frontend-bundles" in publish_workflow
    assert "Restore byte-exact release sources" in publish_workflow
    assert "self-hosted, windows, x64" in compatibility_workflow
    assert "windows-10-x64" in compatibility_workflow
    assert "windows-11-x64" in compatibility_workflow
    assert "Get-AuthenticodeSignature" in compatibility_workflow


def test_windows_release_staging_requires_signed_smoke_passed_asset() -> None:
    tool = (REPO_ROOT / "tools" / "windows_distribution.py").read_text(encoding="utf-8")

    assert "only an Authenticode-valid Windows MSI may be staged for release" in tool
    assert '"result": "passed"' in tool
    assert "_existing_release_assets" in tool
