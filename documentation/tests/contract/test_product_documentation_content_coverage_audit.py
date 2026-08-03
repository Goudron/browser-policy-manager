from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.docs_index import doc_path_from_index

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
AUDIT_JSON = REPOSITORY_ROOT / "docs/architecture/product-documentation-content-coverage-audit-0.9.0.json"
AUDIT_MD = REPOSITORY_ROOT / "docs/architecture/product-documentation-content-coverage-audit-0.9.0.md"
USER_INVENTORY = REPOSITORY_ROOT / "docs/architecture/product-user-capability-inventory-0.9.0.md"
FIREFOX_INVENTORY = REPOSITORY_ROOT / "docs/architecture/firefox-policy-documentation-inventory-0.9.0.json"
CIS_INVENTORY = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
API_INVENTORY = REPOSITORY_ROOT / "docs/architecture/api-documentation-inventory-0.9.0.md"
API_REHOME_AUDIT = REPOSITORY_ROOT / "docs/architecture/api-integration-rehome-audit-0.9.0.json"
ADMIN_VALIDATION = DOCUMENTATION_ROOT / "fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json"
SCREENSHOT_FIXTURE = DOCUMENTATION_ROOT / "fixtures/screenshot-states/screenshot-states-0.9.0.json"
ARTIFACT_POLICY = DOCUMENTATION_ROOT / "config/artifact-policy.json"
SEARCH_CONTRACT = DOCUMENTATION_ROOT / "config/search-corpus-and-results-0.9.0.json"
RELEASE_CONTRACT = REPOSITORY_ROOT / "docs/architecture/product-documentation-release-contract-0.9.0.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDE_FAMILIES = (
    "user-guide",
    "firefox-policy-guide",
    "cis-settings-guide",
    "api-integration-guide",
    "administrator-guide",
)
REQUIRED_DOMAIN_IDS = {
    "user_capabilities",
    "administrator_linux_source_deployment",
    "administrator_windows_wsl_source_deployment",
    "administrator_devops_operations",
    "administrator_update_from_source",
    "administrator_api_integration",
    "administrator_control_product_runbooks",
    "administrator_troubleshooting_diagnostics",
    "administrator_production_readiness_boundaries",
    "firefox_policy_schema",
    "cis_settings",
    "api_operations",
    "locale_parity",
    "localized_screenshots",
    "manifest_target_map",
    "search_indexes",
    "portal_runtime",
}
CAPABILITY_ROW_RE = re.compile(
    r"^\| `(?P<capability>CAP-[A-Z]+-[0-9]{3})` \| .* \| `(?P<topic>ug-[a-z0-9-]+)` \| "
    r"(?P<topic_type>task|concept|reference|troubleshooting) \|$"
)
API_ROW_RE = re.compile(
    r"^\| `(?P<operation>API-[A-Z]+-[0-9]{3})` \| `(?P<method>GET|POST|PATCH|DELETE)` "
    r"\| `(?P<path>[^`]+)` \| .* \| `(?P<topic>(?:api|admin)-[a-z0-9-]+)` \|$"
)
WEB_ROW_RE = re.compile(
    r"^\| `(?P<operation>WEB-[0-9]{3})` \| `(?P<method>GET)` "
    r"\| `(?P<path>[^`]+)` \| .* \|$"
)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _audit() -> dict[str, object]:
    return _json(AUDIT_JSON)


def _domain(domain_id: str) -> dict[str, object]:
    domains = {
        domain["id"]: domain
        for domain in _audit()["domains"]
        if isinstance(domain, dict) and isinstance(domain.get("id"), str)
    }
    return domains[domain_id]


def _path_exists(relative: str) -> bool:
    return (REPOSITORY_ROOT / relative).exists()


def _user_capability_rows() -> list[dict[str, str]]:
    return [
        match.groupdict()
        for line in USER_INVENTORY.read_text(encoding="utf-8").splitlines()
        if (match := CAPABILITY_ROW_RE.match(line))
    ]


def _api_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    api_rows: list[dict[str, str]] = []
    web_rows: list[dict[str, str]] = []
    for line in API_INVENTORY.read_text(encoding="utf-8").splitlines():
        if match := API_ROW_RE.match(line):
            api_rows.append(match.groupdict())
        if match := WEB_ROW_RE.match(line):
            web_rows.append(match.groupdict())
    return api_rows, web_rows


def test_content_coverage_audit_is_indexed_and_declares_m14_07_scope() -> None:
    assert doc_path_from_index(
        "architecture/product-documentation-content-coverage-audit-0.9.0.json",
        status="active",
    ) == AUDIT_JSON
    assert doc_path_from_index(
        "architecture/product-documentation-content-coverage-audit-0.9.0.md",
        status="active",
    ) == AUDIT_MD

    audit = _audit()
    summary = AUDIT_MD.read_text(encoding="utf-8")

    assert audit["schema_version"] == 1
    assert audit["backlog_item"] == "BPM090-M14-07"
    assert audit["target_bpm_version"] == "0.9.0"
    assert audit["status"] == "accepted-with-release-blockers"
    assert audit["locales"] == list(LOCALES)
    assert audit["guide_families"] == list(GUIDE_FAMILIES)
    assert audit["coverage_policy"] == {
        "all_domains_must_be": "covered_or_release_blocker",
        "silent_gaps_forbidden": True,
        "source_authority_must_be_tested": True,
        "locale_peer_equivalence_required": True,
        "generated_artifacts_are_evidence_not_hand_edited_source": True,
    }
    assert "Backlog item: `BPM090-M14-07`" in summary
    assert "Accepted with release blockers" in summary
    assert "localized screenshot capture and review" in summary


def test_every_audit_domain_has_evidence_or_named_release_blocker() -> None:
    audit = _audit()
    domains = audit["domains"]
    by_id = {domain["id"]: domain for domain in domains}

    assert set(by_id) == REQUIRED_DOMAIN_IDS
    assert len(domains) == len(by_id)

    for domain in domains:
        assert domain["disposition"] in {"covered", "release-blocker"}
        assert domain["release_gates"]
        assert domain["summary"]
        assert domain["source_inventories"]
        assert domain["evidence_files"]
        assert domain["gate_tests"]
        for path in domain["source_inventories"]:
            assert _path_exists(path), (domain["id"], path)
        for path in domain["evidence_files"]:
            assert _path_exists(path), (domain["id"], path)
        for gate in domain["gate_tests"]:
            if not gate.startswith("make "):
                assert _path_exists(gate), (domain["id"], gate)

        if domain["disposition"] == "covered":
            assert "release_blockers" not in domain
            assert not domain.get("blocks_release", False)
        else:
            assert domain["blocks_release"] is True
            assert domain["release_blockers"]

    assert {
        domain["id"] for domain in domains if domain["disposition"] == "release-blocker"
    } == {"localized_screenshots"}


def test_audit_counts_match_current_product_admin_firefox_cis_and_api_inventories() -> None:
    user_domain = _domain("user_capabilities")
    capability_rows = _user_capability_rows()
    assert user_domain["summary"] == {
        "capability_count": len(capability_rows),
        "planned_topic_count": len({row["topic"] for row in capability_rows}),
        "localized_topic_count_per_locale": 89,
    }

    admin_fixture = _json(ADMIN_VALIDATION)
    admin_groups = admin_fixture["admin_topic_groups"]
    assert _domain("administrator_linux_source_deployment")["summary"]["topic_count"] == len(
        admin_groups["linux_source_deployment"]
    )
    assert _domain("administrator_windows_wsl_source_deployment")["summary"]["topic_count"] == len(
        admin_groups["windows_wsl_deployment"]
    )
    assert _domain("administrator_devops_operations")["summary"]["topic_count"] == len(
        admin_groups["operate_and_update_source_deployment"][:4]
    )
    assert _domain("administrator_update_from_source")["summary"]["topic_count"] == len(
        admin_groups["operate_and_update_source_deployment"][4:8]
    )
    assert _domain("administrator_control_product_runbooks")["summary"]["topic_count"] == len(
        admin_groups["lifecycle_workflows_and_recovery"][2:]
    )
    assert _domain("administrator_troubleshooting_diagnostics")["summary"]["topic_count"] == len(
        admin_groups["troubleshooting_and_production_readiness"][:6]
    )
    assert _domain("administrator_production_readiness_boundaries")["summary"]["topic_count"] == len(
        admin_groups["requirements_and_scope"][1:]
        + admin_groups["troubleshooting_and_production_readiness"][6:]
    )
    assert _domain("administrator_api_integration")["summary"]["migrated_admin_topic_count"] == len(
        _json(API_REHOME_AUDIT)["api_topics_to_rehome"]
    )

    firefox = _json(FIREFOX_INVENTORY)
    policies = firefox["policies"]
    preferences = firefox["managed_preferences"]
    assert _domain("firefox_policy_schema")["summary"] == {
        "policy_count": len(policies),
        "managed_preference_count": len(preferences),
        "release_only_policy_count": sum(
            entry["channel_scope"] == "release-only" for entry in policies
        ),
    }

    cis = _json(CIS_INVENTORY)
    recommendations = cis["recommendations"]
    assert _domain("cis_settings")["summary"] == {
        "recommendation_count": len(recommendations),
        "planned_topic_count": sum(
            entry["publication_disposition"] == "planned-dita-topic"
            for entry in recommendations
        ),
        "provenance_only_count": sum(
            entry["publication_disposition"] == "provenance-only-non-publishable"
            for entry in recommendations
        ),
        "manual_review_paths": len(cis["manual_review_paths"]),
    }

    api_rows, web_rows = _api_rows()
    assert _domain("api_operations")["summary"] == {
        "integration_operation_count": len(api_rows),
        "web_route_count": len(web_rows),
        "inventory_topic_count": len({row["topic"] for row in api_rows}),
    }


def test_locale_manifest_search_and_screenshot_states_are_reconciled() -> None:
    artifact_policy = _json(ARTIFACT_POLICY)
    search_contract = _json(SEARCH_CONTRACT)
    screenshot_fixture = _json(SCREENSHOT_FIXTURE)
    release_contract = RELEASE_CONTRACT.read_text(encoding="utf-8")

    assert _domain("locale_parity")["summary"] == {
        "locale_count": len(LOCALES),
        "guide_count": len(GUIDE_FAMILIES),
        "full_peer_content_required": True,
    }
    assert _domain("manifest_target_map")["summary"] == {
        "guide_count": len(GUIDE_FAMILIES),
        "locale_count": len(LOCALES),
        "ui_target_map_required": True,
    }
    assert _domain("search_indexes")["summary"] == {
        "locale_index_count": len(search_contract["locales"]),
        "search_mode": search_contract["search_mode"],
        "non_ai_boundary": search_contract["non_ai_boundary"]["mode"],
    }

    screenshot_domain = _domain("localized_screenshots")
    assert screenshot_domain["disposition"] == "release-blocker"
    assert screenshot_domain["summary"]["current_fixture_capture_rows"] == len(
        screenshot_fixture["capture_matrix"]
    )
    assert "localized screenshot capture and review" in artifact_policy[
        "current_runtime_contract"
    ]["required_before_shipping"]
    assert "DOC090-G09" in release_contract
    assert "Every required User Guide illustration" in release_contract


def test_audit_release_blockers_match_artifact_policy_and_no_other_domain_blocks_release() -> None:
    audit = _audit()
    artifact_policy = _json(ARTIFACT_POLICY)

    assert audit["release_blockers"] == artifact_policy["current_runtime_contract"][
        "required_before_shipping"
    ]
    assert "localized screenshot capture and review" in _domain("localized_screenshots")[
        "release_blockers"
    ]
    assert all(
        domain["id"] == "localized_screenshots"
        for domain in audit["domains"]
        if domain["disposition"] == "release-blocker"
    )
    assert audit["focused_rerun"] == (
        "./.venv/bin/pytest -q -m docs_contract "
        "documentation/tests/contract/test_product_documentation_content_coverage_audit.py"
    )
    assert audit["full_release_rerun"] == "make docs-release-check"
