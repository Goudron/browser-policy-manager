from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
GUIDES = {
    "user-guide.ditamap": "map-user-guide",
    "firefox-policy-guide.ditamap": "map-firefox-policy-guide",
    "cis-settings-guide.ditamap": "map-cis-settings-guide",
    "api-integration-guide.ditamap": "map-api-integration-guide",
    "administrator-guide.ditamap": "map-administrator-guide",
}
PORTAL_REFERENCES = tuple(GUIDES)
FIREFOX_GUIDE_KEYREFS = [
    "topic.fx-concept-policy-selection",
    "topic.fx-concept-release-esr-differences",
    "topic.fx-concept-bpm-firefox-boundary",
    "topic.fx-concept-starter-presets",
    "topic.fx-concept-complex-policy-families",
    "topic.fx-task-review-complex-policy-configuration",
    "topic.fx-reference-managed-preference-locking",
]
CIS_GUIDE_KEYREFS = [
    "topic.cis-concept-orientation",
    "topic.cis-concept-levels-channels-layers",
    "topic.cis-task-select-cis-baseline",
    "topic.cis-concept-presets-layers-merge",
    "topic.cis-task-trace-cis-source",
    "topic.cis-concept-manual-review-exceptions",
    "topic.cis-task-verify-cis-deviation",
    "topic.cis-task-run-level-1-workflow",
    "topic.cis-task-run-level-2-hardened-workflow",
]
API_GUIDE_KEYREFS = [
    "topic.api-concept-administrator-integration-landing",
]
ADMIN_GUIDE_KEYREFS = [
    "topic.admin-task-prepare-linux-source-deployment",
    "topic.admin-task-set-up-linux-source-checkout",
    "topic.admin-task-configure-linux-source-runtime",
    "topic.admin-task-verify-linux-source-deployment",
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
]
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

pytestmark = pytest.mark.docs_contract


def _root(path: Path) -> ET.Element:
    source = path.read_text(encoding="utf-8")
    assert '<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">' in source
    return ET.fromstring(source)


def test_all_locales_have_the_exact_guide_and_portal_map_set() -> None:
    expected = {*GUIDES, "portal.ditamap", "keys.ditamap"}

    assert {path.name for path in DITA_ROOT.iterdir() if path.is_dir()} == set(LOCALES)
    for locale in LOCALES:
        maps = DITA_ROOT / locale / "maps"
        assert {path.name for path in maps.glob("*.ditamap")} == expected


@pytest.mark.parametrize("locale", LOCALES)
def test_guide_maps_are_independent_localized_dita_inputs(locale: str) -> None:
    for filename, map_id in GUIDES.items():
        root = _root(DITA_ROOT / locale / "maps" / filename)
        assert root.tag == "map"
        assert root.attrib == {"id": map_id, XML_LANG: locale}
        title = root.find("title")
        assert title is not None and title.text and title.text.strip()
        key_map = root.find("mapref")
        assert key_map is not None
        assert key_map.attrib == {
            "href": "keys.ditamap",
            "format": "ditamap",
            "processing-role": "resource-only",
        }
        if filename == "user-guide.ditamap":
            topicheads = root.findall("topichead")
            assert len(topicheads) == 8
            assert all(topichead.attrib == {"outputclass": "case-oriented-section"} for topichead in topicheads)
            assert list(root) == [title, key_map, *topicheads]
        elif filename == "firefox-policy-guide.ditamap":
            topicrefs = root.findall("topicref")
            assert [topicref.attrib for topicref in topicrefs] == [
                {"keyref": keyref} for keyref in FIREFOX_GUIDE_KEYREFS
            ]
            assert list(root) == [title, key_map, *topicrefs]
        elif filename == "cis-settings-guide.ditamap":
            topicrefs = root.findall("topicref")
            assert [topicref.attrib for topicref in topicrefs] == [
                {"keyref": keyref} for keyref in CIS_GUIDE_KEYREFS
            ]
            assert list(root) == [title, key_map, *topicrefs]
        elif filename == "api-integration-guide.ditamap":
            topicrefs = root.findall("topicref")
            assert [topicref.attrib for topicref in topicrefs] == [
                {"keyref": keyref} for keyref in API_GUIDE_KEYREFS
            ]
            assert list(root) == [title, key_map, *topicrefs]
        elif filename == "administrator-guide.ditamap":
            topicrefs = root.findall("topicref")
            assert [topicref.attrib for topicref in topicrefs] == [
                {"keyref": keyref} for keyref in ADMIN_GUIDE_KEYREFS
            ]
            assert list(root) == [title, key_map, *topicrefs]
        else:
            assert list(root) == [title, key_map]


@pytest.mark.parametrize("locale", LOCALES)
def test_portal_map_aggregates_each_guide_once_in_stable_order(locale: str) -> None:
    maps = DITA_ROOT / locale / "maps"
    root = _root(maps / "portal.ditamap")

    assert root.tag == "map"
    assert root.attrib == {"id": "map-portal", XML_LANG: locale}
    title = root.find("title")
    assert title is not None and title.text and title.text.strip()
    all_references = root.findall("mapref")
    key_map, *references = all_references
    assert key_map.attrib == {
        "href": "keys.ditamap",
        "format": "ditamap",
        "processing-role": "resource-only",
    }
    assert tuple(reference.attrib["href"] for reference in references) == PORTAL_REFERENCES
    assert all(reference.attrib["format"] == "ditamap" for reference in references)
    assert all(set(reference.attrib) == {"href", "format"} for reference in references)
    assert all((maps / reference.attrib["href"]).is_file() for reference in references)
    assert list(root) == [title, key_map, *references]


def test_publishable_source_boundary_contains_only_dita_xml() -> None:
    source_files = {
        path.suffix for path in DITA_ROOT.rglob("*") if path.is_file() and path.name != ".gitkeep"
    }
    assert ".ditamap" in source_files
    assert source_files <= {".ditamap", ".dita"}
