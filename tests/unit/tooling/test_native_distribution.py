from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import native_distribution

REPO_ROOT = Path(__file__).resolve().parents[3]
NATIVE_ROOT = REPO_ROOT / "distributions" / "native"


def test_native_target_manifest_declares_the_five_documented_linux_targets() -> None:
    targets = native_distribution.load_targets()

    assert set(targets) == {
        "ubuntu-26-04",
        "debian-13-5",
        "fedora-44",
        "linux-mint-22-3",
        "manjaro-stable",
    }
    assert {target.package_format for target in targets.values()} == {"deb", "rpm", "arch"}
    assert targets["linux-mint-22-3"].builder_image == "bpm091/linux-mint:22.3-zena-amd64"
    assert targets["manjaro-stable"].artifact.endswith(".pkg.tar.zst")


def test_native_release_inputs_are_complete_and_bound_to_the_current_bpm_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "bpm-documentation-0.9.5.tar.gz"
    archive.write_bytes(b"verified unit-test documentation archive")
    checksum = archive.with_suffix(archive.suffix + ".sha256")
    checksum.write_text(
        f"{native_distribution._sha256(archive)}  {archive.name}\n", encoding="ascii"
    )
    monkeypatch.setattr(native_distribution, "_documentation_archive", lambda: (archive, checksum))

    targets = native_distribution.validate_release_inputs()

    assert native_distribution._project_version() == "0.9.5"
    assert len(targets) == 5


def test_native_payload_preserves_explicit_migration_and_unprivileged_service_boundaries() -> None:
    launcher = (NATIVE_ROOT / "templates" / "bpm").read_text(encoding="utf-8")
    migrator = (NATIVE_ROOT / "templates" / "bpm-migrate").read_text(encoding="utf-8")
    unit = (NATIVE_ROOT / "templates" / "bpm.service").read_text(encoding="utf-8")
    builder = (NATIVE_ROOT / "build-target.sh").read_text(encoding="utf-8")

    assert "exec /usr/bin/bpm-migrate" in launcher
    assert "alembic -c /opt/bpm/alembic.ini upgrade head" in migrator
    assert "User=bpm" in unit
    assert "ReadWritePaths=/var/lib/bpm" in unit
    assert "Do not migrate or start BPM during an upgrade." in builder
    assert "BPM migrations and service activation are explicit operator actions." in builder
    smoke = (NATIVE_ROOT / "smoke-target.sh").read_text(encoding="utf-8")
    assert "runuser -u bpm -- /usr/bin/bpm serve" in smoke
    assert 'wait "$process_id" || true' in smoke


def test_native_target_manifest_records_private_python_and_target_specific_artifact_names() -> None:
    manifest = json.loads((NATIVE_ROOT / "targets.json").read_text(encoding="utf-8"))

    assert manifest["runtime"]["python_version"] == "3.14.6"
    assert manifest["runtime"]["prefix"] == "/opt/bpm/runtime"
    assert manifest["targets"]["ubuntu-26-04"]["artifact"].endswith("ubuntu26.04_amd64.deb")
    assert manifest["targets"]["debian-13-5"]["artifact"].endswith("debian13_amd64.deb")
    assert manifest["targets"]["fedora-44"]["artifact"].endswith("fc44.x86_64.rpm")
    assert manifest["targets"]["linux-mint-22-3"]["artifact"].endswith("linuxmint22.3_amd64.deb")


def test_native_builder_retries_transient_release_input_downloads() -> None:
    builder = (NATIVE_ROOT / "build-target.sh").read_text(encoding="utf-8")

    assert "--connect-timeout 30 --max-time 900 --retry 5 --retry-all-errors" in builder
    assert "--retries 5 --timeout 60 --only-binary=:all:" in builder
    assert 'local build_source="$WORK_ROOT/bpm-source"' in builder
    assert 'cp --archive "$SOURCE_ROOT/app" "$build_source/app"' in builder
    assert 'sha256sum "$BPM_NATIVE_ARTIFACT" >"${BPM_NATIVE_ARTIFACT}.sha256"' in builder
    assert "id --user builder >/dev/null 2>&1 || useradd" in builder
    assert r'cp -a "\${startdir}/stage/." "\${pkgdir}/"' in builder
    assert "%global __brp_mangle_shebangs %{nil}" in builder
    assert "AutoReq: no" in builder


def test_native_make_targets_and_manual_release_workflow_stay_explicit() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    workflow = (
        REPO_ROOT / ".github" / "workflows" / "native-linux-distribution-smoke.yml"
    ).read_text(encoding="utf-8")

    assert "native-package-build: docs-package-verify native-package-validate" in makefile
    assert "native-package-smoke: native-package-validate" in makefile
    assert "native-package-release-gate: docs-package-verify native-package-validate" in makefile
    assert "tools/native_distribution.py build --target all" in makefile
    assert "tools/native_distribution.py smoke --target all" in makefile
    assert "native-package-stage-release: native-package-validate" in makefile
    assert "tools/native_distribution.py stage-release --target all" in makefile
    assert "workflow_dispatch:" in workflow
    assert "inputs.run_native_packages == 'RUN'" in workflow
    assert "make native-package-release-gate" in workflow
    assert "docker push" not in workflow
    assert "gh release" not in workflow


def test_versioned_native_release_store_keeps_metadata_in_git_and_assets_outside_it() -> None:
    release_store = REPO_ROOT / "distributions" / "releases" / "0.9.5"
    readme = (release_store / "README.md").read_text(encoding="utf-8")
    ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    tool = (REPO_ROOT / "tools" / "native_distribution.py").read_text(encoding="utf-8")

    assert "GitHub Release assets" in readme
    assert "Git LFS" in readme
    assert "/distributions/releases/[0-9]*/assets/*" in ignore
    assert "def stage_release_assets" in tool
    assert '"provider": "github-release-assets"' in tool
    assert "_retained_non_native_release_assets" in tool
