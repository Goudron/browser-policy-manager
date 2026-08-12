from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_frontend_vendor_has_npm_lockfile_for_ci_rebuilds():
    package_lock = json.loads((REPO_ROOT / "package-lock.json").read_text(encoding="utf-8"))

    assert package_lock["lockfileVersion"] == 3
    assert package_lock["packages"][""]["dependencies"] == {
        "monaco-editor": "0.56.0",
    }
    assert package_lock["packages"][""]["devDependencies"] == {
        "@cyclonedx/cyclonedx-npm": "6.0.0",
        "esbuild": "0.28.2",
    }


def test_package_scripts_expose_monaco_build_and_vendor_rebuild():
    package = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["build:monaco"] == "bash tools/build_monaco_bundle.sh"
    assert package["scripts"]["rebuild:vendor"] == "bash tools/rebuild_frontend_vendor.sh"


def test_package_scripts_expose_dependency_free_native_frontend_gates():
    package = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    scripts = package["scripts"]

    assert package["engines"]["node"] == ">=22.14"
    assert "node --test" in scripts["test:frontend"]
    assert "--test-timeout=10000" in scripts["test:frontend"]
    assert "--experimental-test-isolation=process" in scripts["test:frontend"]
    assert "tests/javascript/*/*/*.test.js" in scripts["test:frontend"]
    assert "--experimental-test-coverage" in scripts["test:frontend:coverage"]
    assert (
        "--test-coverage-include=app/static/profiles_modules/**"
        in scripts["test:frontend:coverage"]
    )
    assert "--test-coverage-lines=100" in scripts["test:frontend:coverage"]
    assert "--test-coverage-branches=100" in scripts["test:frontend:coverage"]
    assert "--test-coverage-functions=100" in scripts["test:frontend:coverage"]
    assert "test-coverage-exclude" not in scripts["test:frontend:coverage"]
    assert "vitest" not in json.dumps(package).lower()
    assert "jest" not in json.dumps(package).lower()


def test_frontend_vendor_rebuild_script_uses_reproducible_steps():
    source = (REPO_ROOT / "tools" / "rebuild_frontend_vendor.sh").read_text(encoding="utf-8")

    assert "npm ci" in source
    assert "npm run build:monaco" in source
    assert "tools/verify_frontend_vendor.py --check-licenses" in source
    assert "tools/verify_frontend_vendor.py --size-report" in source
    assert "tools/verify_frontend_vendor.py --write" in source
    assert "tools/verify_frontend_vendor.py" in source


def test_monaco_build_uses_json_only_contribution_and_patched_dompurify_source():
    entry = (REPO_ROOT / "app/static_src/profiles_monaco_entry.js").read_text(encoding="utf-8")
    build = (REPO_ROOT / "tools/build_monaco_bundle.sh").read_text(encoding="utf-8")

    assert "monaco.contribution.js" in entry
    assert "yaml" not in entry.lower()
    assert "DOMPurify 3.4.13" in build
    assert "purify.es.mjs" in build
