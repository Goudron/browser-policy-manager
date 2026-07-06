from __future__ import annotations

import fnmatch
import json
import tomllib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
BOUNDARY_CONTRACT = DOCUMENTATION_ROOT / "tests/suite-boundaries-0.9.0.json"
REQUIRED_DOMAINS = {
    "dita",
    "content",
    "manifest",
    "localization",
    "screenshot",
    "search",
    "links",
    "api_examples",
    "portal_integration",
    "fixtures",
    "diagnostics",
    "snapshot",
    "release_gate",
    "browser_smoke",
    "debugging_protocol",
    "administrator_guide_scope",
    "administrator_devops_operational_boundaries",
    "administrator_linux_deployment",
    "administrator_windows_wsl_deployment",
    "administrator_update_from_source",
    "api_rehome_audit",
}

pytestmark = pytest.mark.docs_contract


def _contract() -> dict[str, object]:
    return json.loads(BOUNDARY_CONTRACT.read_text(encoding="utf-8"))


def _as_repo_path(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def test_documentation_suite_boundary_contract_declares_required_suites_and_domains() -> None:
    contract = _contract()

    assert contract["schema_version"] == 1
    assert contract["backlog_item"] == "BPM090-M12-07"
    assert contract["target_bpm_version"] == "0.9.0"
    assert contract["status"] == "accepted"
    assert contract["pytest_discovery_boundary"] == {
        "current_default_testpaths": ["tests"],
        "documentation_tests_are_run_by_focused_make_targets": True,
        "implemented_make_targets_backlog_item": "BPM090-M12-07",
        "general_tests_tree_may_keep_cross_boundary_contracts": True,
    }

    make_targets = contract["make_targets"]
    assert set(make_targets) == {
        "test-docs",
        "test-docs-contract",
        "test-docs-ui",
        "test-docs-ui-contract",
        "test-docs-browser",
        "docs-snapshot",
        "docs-fast-check",
        "docs-coverage",
        "docs-release-check",
    }
    for target_name, target in make_targets.items():
        assert target["command"] == f"make {target_name}"
        assert target["paths"], target_name
        assert isinstance(target["browser_backed"], bool)
        if target["browser_backed"]:
            assert "sandbox" in target["sandbox_escalation_note"].casefold()

    suites = contract["suites"]
    assert set(suites) == {"unit", "contract", "browser"}
    for suite_id, suite in suites.items():
        assert (REPOSITORY_ROOT / suite["path"]).is_dir(), suite_id
        assert suite["owner"]
        assert suite["scope"]
        assert suite["must_not_require"]

    domains = contract["domains"]
    assert REQUIRED_DOMAINS <= set(domains)
    for domain_id, domain in domains.items():
        assert domain["primary_suite"] in suites, domain_id
        assert domain["path_globs"], domain_id
        assert domain["focused_rerun"], domain_id


def test_documentation_test_files_are_owned_by_an_explicit_domain() -> None:
    contract = _contract()
    patterns = [
        pattern
        for domain in contract["domains"].values()
        for pattern in domain["path_globs"]
    ]
    test_files = sorted(DOCUMENTATION_ROOT.glob("tests/**/*.py"))

    assert test_files
    assert all(_matches_any(_as_repo_path(path), patterns) for path in test_files)


def test_documentation_fixture_references_are_compact_existing_source_inputs() -> None:
    contract = _contract()
    forbidden_fragments = (
        "/build/",
        "/dist/",
        "/reports/",
        "/.cache/",
        "browser.tar",
        "firefox.tar",
        ".pdf",
    )

    for domain_id, domain in contract["domains"].items():
        for fixture in domain["fixtures"]:
            fixture_path = REPOSITORY_ROOT / fixture
            assert fixture_path.exists(), (domain_id, fixture)
            assert not any(fragment in fixture for fragment in forbidden_fragments), (domain_id, fixture)

    rules = contract["compact_fixture_rules"]
    assert "small synthetic JSON examples" in rules["allowed"]
    for forbidden in (
        "production databases",
        "customer profiles",
        "secrets",
        "full generated sites",
        "official CIS PDFs",
        "browser downloads",
    ):
        assert forbidden in rules["forbidden"]


def test_documentation_tests_remain_outside_default_pytest_discovery_after_m11_02() -> None:
    pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_options = pyproject["tool"]["pytest"]["ini_options"]
    contract = _contract()

    assert pytest_options["testpaths"] == contract["pytest_discovery_boundary"]["current_default_testpaths"]
    assert "documentation/tests" not in pytest_options["testpaths"]


def test_documentation_make_targets_are_focused_and_declared() -> None:
    contract = _contract()
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    for target_name, target in contract["make_targets"].items():
        assert f"{target_name}:" in makefile
        for path in target["paths"]:
            assert path.rstrip("/") in makefile

    assert "DOCS_UNIT_PATHS := documentation/tests/unit" in makefile
    assert "DOCS_CONTRACT_PATHS := documentation/tests/contract" in makefile
    assert "DOCS_COVERAGE_MODULES := documentation/tools/validate_metadata.py" in makefile
    assert "$(PYTHON) documentation/tools/generate_subsystem_snapshot.py" in makefile
    assert "DOCS_BROWSER_PATHS := documentation/tests/browser" in makefile
    assert "$(PYTEST) -o addopts= -q $(DOCS_UNIT_PATHS) $(DOCS_CONTRACT_PATHS)" in makefile
    assert "$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_CONTRACT_PATHS)" in makefile
    assert "$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_UI_CONTRACT_PATHS)" in makefile
    assert "$(PYTEST) -o addopts= -q -m browser_ui $(DOCS_BROWSER_PATHS)" in makefile
    assert "$(PYTHON) documentation/tools/build_docs.py validate" in makefile
    assert "$(PYTEST) -o addopts= -q -m docs_contract $(DOCS_RELEASE_GATE_PATHS)" in makefile
    assert "test-release: docs-release-check" in makefile
    assert "--cov-fail-under=100" in makefile


def test_general_tests_boundary_allows_only_cross_boundary_contracts() -> None:
    contract = _contract()
    general_boundary = contract["general_tests_boundary"]

    for allowed in (
        "architecture decisions under docs/architecture/",
        "runtime bridge contracts that must import app/documentation/",
        "repository-level docs index and context-guide contracts",
        "pytest marker policy and release-gate contracts",
    ):
        assert allowed in general_boundary["allowed_cross_boundary_contracts"]

    for excluded in (
        "DITA topic authoring failures",
        "locale parity failures",
        "search index fixture drift",
        "manifest generation internals",
        "screenshot capture issues",
        "API example source fixtures",
    ):
        assert excluded in general_boundary["must_not_debug_from_general_tests"]
