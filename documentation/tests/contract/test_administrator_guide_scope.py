from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ADMIN_GUIDE_KEYREFS = [
    "topic.admin-task-prepare-linux-source-deployment",
    "topic.admin-task-set-up-linux-source-checkout",
    "topic.admin-task-configure-linux-source-runtime",
    "topic.admin-task-verify-linux-source-deployment",
    "topic.admin-task-install-ubuntu-26-04-source",
    "topic.admin-task-install-debian-13-source",
    "topic.admin-task-install-fedora-44-source",
    "topic.admin-task-install-linux-mint-22-3-source",
    "topic.admin-task-install-manjaro-stable-source",
    "topic.admin-task-prepare-windows-wsl-source-deployment",
    "topic.admin-task-set-up-windows-wsl-source-checkout",
    "topic.admin-task-configure-windows-wsl-network-runtime",
    "topic.admin-task-verify-windows-wsl-source-deployment",
    "topic.admin-task-review-devops-configuration-sources",
    "topic.admin-task-plan-devops-storage-logs-backups",
    "topic.admin-task-review-devops-network-cors-security",
    "topic.admin-task-record-devops-operational-boundaries",
    "topic.admin-task-prepare-source-update-evidence",
    "topic.admin-task-refresh-source-revision-dependencies",
    "topic.admin-task-run-source-update-migrations-docs",
    "topic.admin-task-verify-source-update-rollback-stop",
    "topic.admin-concept-integration-audience",
    "topic.admin-concept-supported-integration-patterns",
    "topic.admin-concept-api-conventions",
    "topic.admin-concept-api-limitations",
    "topic.admin-task-sync-profile-lifecycle",
    "topic.admin-task-manage-profile-retirement",
    "topic.admin-task-import-firefox-policies-json",
    "topic.admin-task-export-firefox-policies-json",
    "topic.admin-task-validate-firefox-policies-json",
    "topic.admin-task-check-health-readiness",
    "topic.admin-task-run-pull-compare-update-scenario",
    "topic.admin-task-run-import-review-export-scenario",
    "topic.admin-task-use-reusable-api-examples",
    "topic.admin-task-run-control-product-inventory-pull",
    "topic.admin-task-run-validate-before-apply-update",
    "topic.admin-task-run-import-review-export-handoff",
    "topic.admin-task-gate-control-product-startup",
    "topic.admin-task-record-integration-failure-audit",
    "topic.admin-troubleshoot-failed-startup-probes",
    "topic.admin-troubleshoot-schema-cache-validation",
    "topic.admin-troubleshoot-import-export-failures",
    "topic.admin-troubleshoot-database-storage",
    "topic.admin-troubleshoot-wsl-networking-dependencies",
    "topic.admin-troubleshoot-documentation-portal-build-links",
    "topic.admin-task-assess-single-node-source-readiness",
    "topic.admin-task-review-network-exposure-proxy-readiness",
    "topic.admin-task-plan-monitoring-backup-update-windows",
    "topic.admin-task-record-ha-production-deferred-boundaries",
    "topic.admin-reference-minimum-system-requirements",
    "topic.admin-task-operate-local-documentation-assistant",
    "topic.admin-task-maintain-local-documentation-assistant",
]

pytestmark = pytest.mark.docs_contract


def test_administrator_guide_has_stable_map_key_and_portal_slot_in_every_locale() -> None:
    for locale in LOCALES:
        maps = DITA_ROOT / locale / "maps"
        admin_map = maps / "administrator-guide.ditamap"
        root = ET.parse(admin_map).getroot()

        assert root.attrib == {"id": "map-administrator-guide", XML_LANG: locale}
        assert root.find("title") is not None
        assert root.find("mapref").attrib == {
            "href": "keys.ditamap",
            "format": "ditamap",
            "processing-role": "resource-only",
        }
        sections = root.findall("topichead")
        assert len(sections) == 8
        assert all(
            section.attrib == {"outputclass": "case-oriented-section"} for section in sections
        )
        assert sections[0].findall("topicref")[0].attrib == {
            "keyref": "topic.admin-reference-minimum-system-requirements"
        }
        assert {
            topicref.attrib["keyref"]
            for section in sections
            for topicref in section.findall("topicref")
        } == set(ADMIN_GUIDE_KEYREFS)

        portal_refs = [
            element.attrib["href"]
            for element in ET.parse(maps / "portal.ditamap").getroot().findall("mapref")
            if element.attrib.get("processing-role") != "resource-only"
        ]
        assert portal_refs == [
            "user-guide.ditamap",
            "firefox-policy-guide.ditamap",
            "cis-settings-guide.ditamap",
            "administrator-guide.ditamap",
        ]

        guide_keys = {
            element.attrib["keys"]
            for element in ET.parse(maps / "keys.ditamap").getroot().findall("keydef")
            if element.attrib["keys"].startswith("guide.")
        }
        assert "guide.administrator-guide" in guide_keys
        topic_keys = {
            element.attrib["keys"]
            for element in ET.parse(maps / "keys.ditamap").getroot().findall("keydef")
            if element.attrib["keys"].startswith("topic.admin-")
        }
        assert topic_keys == set(ADMIN_GUIDE_KEYREFS)
        assert (DITA_ROOT / locale / "admin").is_dir()


def test_administrator_guide_is_registered_in_manifest_schema_and_build_tool() -> None:
    schema = json.loads(
        (
            REPOSITORY_ROOT
            / "docs/architecture/schemas/product-documentation-manifest-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    guide_catalog = (DOCUMENTATION_ROOT / "buildlib/shared.py").read_text(encoding="utf-8")
    identifiers = (
        REPOSITORY_ROOT / "docs/architecture/documentation-identifiers-and-url-conventions-0.9.0.md"
    ).read_text(encoding="utf-8")

    assert "administrator-guide" in schema["$defs"]["guides"]["required"]
    assert "admin" in schema["$defs"]["guide"]["properties"]["url_root"]["enum"]
    assert '"administrator-guide.ditamap", "a-administrator-guide", "admin"' in guide_catalog
    assert "| `administrator-guide` | `admin/` |" in identifiers
    assert "`admin-*` IDs reserved for source deployment" in identifiers


def test_administrator_guide_scope_separates_current_source_operations_from_deferred_installers() -> (
    None
):
    release_contract = (
        REPOSITORY_ROOT / "docs/architecture/product-documentation-release-contract-0.9.0.md"
    ).read_text(encoding="utf-8")
    provenance = (
        REPOSITORY_ROOT / "docs/architecture/product-documentation-provenance-review-0.9.0.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "Administrator And DevOps Guide",
        "source deployment",
        "source-based updates",
        "operations boundaries",
        "integration runbooks",
    ):
        assert phrase in provenance

    for deferred in (
        "packaged installers",
        "official reverse-proxy recipes",
        "HA clustering",
        "production hardening",
    ):
        assert deferred in provenance

    assert "all five guide maps" in release_contract
    assert "All five guides" in release_contract
    assert "distribution-specific administrator installation variants" in release_contract
