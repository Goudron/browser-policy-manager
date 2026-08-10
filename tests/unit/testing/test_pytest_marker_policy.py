from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.marker_policy import (
    AI_INCUBATION_TEST_FILES,
    DOMAIN_MARKERS,
    LAYER_MARKERS,
    OWNERSHIP_PATH,
    PRIMARY_LAYERS,
    OwnershipPolicyError,
    markers_for_path,
    ownership_for_path,
    ownership_rules,
    parse_ownership_rules,
    primary_layer_for_path,
    primary_markers,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("tests/integration/api/test_profiles_api.py", {"integration", "api"}),
        ("tests/unit/schema/general/test_policy_validation_with_schema.py", {"unit", "schema"}),
        ("tests/unit/tooling/test_locale_inventory.py", {"unit", "tooling"}),
        ("tests/unit/testing/test_app_harness_unit.py", {"unit"}),
        ("tests/unit/testing/test_cache_harness_unit.py", {"unit"}),
        ("tests/unit/tooling/test_ci_workflow_layers.py", {"unit"}),
        ("tests/unit/db/test_db_harness_unit.py", {"unit"}),
        ("tests/unit/tooling/test_frontend_vendor_rebuild_contract.py", {"unit"}),
        ("tests/unit/profiles/test_profile_frontend_bundles.py", {"unit"}),
        ("tests/unit/tooling/test_makefile_test_targets.py", {"unit"}),
        (
            "tests/contract/docs/general/test_api_documentation_inventory.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_cis_documentation_inventory.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_documentation_identifiers_and_url_conventions.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_documentation_runtime_route.py",
            {"contract", "docs_contract"},
        ),
        ("tests/contract/docs/general/test_docs_index.py", {"contract", "docs_contract"}),
        (
            "tests/contract/docs/general/test_firefox_policy_documentation_inventory.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_documentation_ownership_boundary.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/schema/test_product_documentation_manifest_schema.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_documentation_accessibility_security_contract.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_documentation_context_guide.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_documentation_provenance_review.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_documentation_scaffold.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_documentation_release_contract.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/docs/general/test_product_user_capability_inventory.py",
            {"contract", "docs_contract"},
        ),
        ("tests/contract/testing/test_pytest_app_state_isolation_contract.py", {"contract"}),
        ("tests/contract/testing/test_pytest_db_isolation_contract.py", {"contract"}),
        (
            "tests/contract/docs/general/test_pytest_xdist_isolation_audit_contract.py",
            {"contract", "docs_contract"},
        ),
        (
            "tests/contract/ui/localization/test_ui_runtime_i18n_contract.py",
            {"contract", "ui_contract"},
        ),
        (
            "tests/contract/ui/profiles/test_assets_i18n_contracts.py",
            {"contract", "ui_contract"},
        ),
        (
            "tests/contract/ui/profiles/test_route_dom_contracts.py",
            {"contract", "ui_contract", "slow"},
        ),
        ("tests/contract/compliance/test_cis_firefox_mapping_targets.py", {"contract", "slow"}),
        ("tests/browser/profiles/test_ui_browser_tabs.py", {"browser", "browser_ui", "slow"}),
        ("tests/live/firefox/test_policy_scenarios.py", {"live", "firefox_live", "slow"}),
        (
            "tests/live/firefox/test_extension_settings_amo.py",
            {"live", "firefox_live", "firefox_live_amo", "slow"},
        ),
    ],
)
def test_marker_policy_assigns_expected_layers(path, expected):
    assert expected <= markers_for_path(path)


def test_marker_policy_only_emits_registered_layer_markers():
    sample_paths = (
        "tests/integration/api/test_profiles_api.py",
        "tests/unit/schema/general/test_policy_validation_with_schema.py",
        "tests/contract/docs/general/test_docs_index.py",
        "tests/contract/ui/localization/test_ui_runtime_i18n_contract.py",
        "tests/browser/profiles/test_ui_browser_tabs.py",
        "tests/live/firefox/test_extension_settings_amo.py",
    )
    emitted = set().union(*(markers_for_path(path) for path in sample_paths))

    assert emitted <= LAYER_MARKERS


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("tests/unit/schema/general/test_policy_validation_unit.py", "unit"),
        ("tests/integration/api/test_profiles_api.py", "integration"),
        ("tests/contract/testing/test_pytest_db_isolation_contract.py", "contract"),
        ("tests/browser/profiles/test_ui_browser_tabs.py", "browser"),
        ("tests/live/firefox/test_policy_scenarios.py", "live"),
        ("documentation/tests/unit/test_build_docs.py", "unit"),
        ("documentation/tests/contract/test_guide_maps.py", "contract"),
        ("documentation/tests/browser/test_documentation_portal_browser_smoke.py", "browser"),
    ],
)
def test_primary_layer_is_exclusive_and_domains_are_orthogonal(path: str, expected: str) -> None:
    markers = markers_for_path(path)

    assert primary_layer_for_path(path) == expected
    assert primary_markers(markers) == {expected}
    assert not (primary_markers(markers) & DOMAIN_MARKERS)


def test_ai_incubation_manifest_is_explicit_existing_and_marked() -> None:
    project_root = Path(__file__).resolve().parents[3]

    assert AI_INCUBATION_TEST_FILES
    for path in AI_INCUBATION_TEST_FILES:
        assert (project_root / path).is_file(), path
        assert "ai_incubation" in markers_for_path(path)


def _owned_test_modules(project_root: Path) -> tuple[str, ...]:
    return tuple(
        path.relative_to(project_root).as_posix()
        for directory in (project_root / "tests", project_root / "documentation/tests")
        for path in sorted(directory.rglob("test_*.py"))
    )


def test_ownership_configuration_covers_every_product_and_documentation_test_module() -> None:
    project_root = Path(__file__).resolve().parents[3]
    test_modules = _owned_test_modules(project_root)
    metadata = json.loads(OWNERSHIP_PATH.read_text(encoding="utf-8"))

    assert test_modules
    assert OWNERSHIP_PATH.is_file()
    for path in test_modules:
        assert ownership_for_path(path).layer in LAYER_MARKERS
        if path.startswith("tests/"):
            assert Path(path).parts[1] in PRIMARY_LAYERS

    support_paths: set[str] = set()
    for owner in metadata["support_owners"]:
        assert ("paths" in owner) != ("prefix" in owner)
        if "paths" in owner:
            for path in owner["paths"]:
                assert path not in support_paths
                assert (project_root / path).is_file(), path
                support_paths.add(path)
        else:
            prefix = owner["prefix"]
            assert prefix.endswith("/")
            assert (project_root / prefix).is_dir(), prefix


def test_owned_directories_accept_new_tests_without_central_filename_edits() -> None:
    assert primary_layer_for_path("tests/integration/api/test_a_future_api.py") == "integration"
    assert (
        primary_layer_for_path("documentation/tests/contract/test_a_future_contract.py")
        == "contract"
    )


def test_unowned_test_path_stops_collection_instead_of_receiving_a_default_layer() -> None:
    with pytest.raises(OwnershipPolicyError, match="unowned test path"):
        markers_for_path("tests/test_a_future_root_test.py")


def test_duplicate_ownership_metadata_is_rejected_before_collection() -> None:
    payload = {
        "schema_version": 1,
        "owners": [
            {"id": "first", "paths": ["tests/test_example.py"], "layer": "unit", "markers": []},
            {
                "id": "second",
                "paths": ["tests/test_example.py"],
                "layer": "contract",
                "markers": [],
            },
        ],
    }

    with pytest.raises(OwnershipPolicyError, match="duplicates explicit path"):
        parse_ownership_rules(payload)


def test_overlapping_directory_ownership_metadata_is_rejected_before_collection() -> None:
    payload = {
        "schema_version": 1,
        "owners": [
            {"id": "all-tests", "prefix": "tests/", "layer": "integration", "markers": []},
            {"id": "api", "prefix": "tests/api/", "layer": "integration", "markers": ["api"]},
        ],
    }

    with pytest.raises(OwnershipPolicyError, match="prefixes overlap"):
        parse_ownership_rules(payload)


def test_current_metadata_has_one_owner_for_every_test_module() -> None:
    project_root = Path(__file__).resolve().parents[3]

    assert ownership_rules()
    for path in _owned_test_modules(project_root):
        assert ownership_for_path(path)


def test_test_suite_has_no_unenforced_order_markers() -> None:
    """Ordering is a test dependency only when its plugin is an owned runtime contract."""
    sources = tuple((REPO_ROOT / "tests").rglob("test_*.py"))
    legacy_marker_registration = '"order: test ' + 'order marker"'
    legacy_order_marker = "pytest.mark." + "order"

    assert legacy_marker_registration not in PYPROJECT.read_text(encoding="utf-8")
    assert all(legacy_order_marker not in path.read_text(encoding="utf-8") for path in sources)
