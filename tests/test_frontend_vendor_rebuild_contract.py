from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_frontend_vendor_has_npm_lockfile_for_ci_rebuilds():
    package_lock = json.loads((REPO_ROOT / "package-lock.json").read_text(encoding="utf-8"))

    assert package_lock["lockfileVersion"] == 3
    assert package_lock["packages"][""]["dependencies"] == {
        "js-yaml": "4.2.0",
        "monaco-editor": "0.52.0",
    }
    assert package_lock["packages"][""]["devDependencies"] == {"esbuild": "0.25.3"}


def test_package_scripts_expose_monaco_build_and_vendor_rebuild():
    package = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["build:monaco"] == "bash tools/build_monaco_bundle.sh"
    assert package["scripts"]["rebuild:vendor"] == "bash tools/rebuild_frontend_vendor.sh"


def test_frontend_vendor_rebuild_script_uses_reproducible_steps():
    source = (REPO_ROOT / "tools" / "rebuild_frontend_vendor.sh").read_text(encoding="utf-8")

    assert "npm ci" in source
    assert "npm run build:monaco" in source
    assert "tools/verify_frontend_vendor.py --check-licenses" in source
    assert "tools/verify_frontend_vendor.py --size-report" in source
    assert "tools/verify_frontend_vendor.py --write" in source
    assert "tools/verify_frontend_vendor.py" in source
