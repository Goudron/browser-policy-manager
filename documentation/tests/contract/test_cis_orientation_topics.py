from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
INVENTORY_PATH = REPOSITORY_ROOT / "docs/architecture/cis-documentation-inventory-0.9.0.json"
WORKFLOW_FIXTURE_PATH = DOCUMENTATION_ROOT / "fixtures/cis-workflows/level-workflows-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
DOCTYPES = {
    "concept": '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">',
    "task": '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">',
}

TOPICS = {
    "cis-concept-orientation": {
        "kind": "concept",
        "sections": {
            "a-benchmark",
            "a-what-bpm-publishes",
            "a-what-bpm-does-not-prove",
            "a-when-appropriate",
        },
    },
    "cis-concept-levels-channels-layers": {
        "kind": "concept",
        "sections": {
            "a-level-1",
            "a-level-2",
            "a-supported-channels",
            "a-generated-layers",
            "a-manual-review",
        },
    },
    "cis-task-select-cis-baseline": {
        "kind": "task",
        "sections": set(),
    },
    "cis-concept-presets-layers-merge": {
        "kind": "concept",
        "sections": {
            "a-source-order",
            "a-starter-presets",
            "a-layer-decisions",
            "a-conflicts-manual-review",
            "a-attribution-boundary",
        },
    },
    "cis-task-trace-cis-source": {
        "kind": "task",
        "sections": set(),
    },
    "cis-concept-manual-review-exceptions": {
        "kind": "concept",
        "sections": {
            "a-manual-review-scope",
            "a-update-governance",
            "a-proxy-routing",
            "a-evidence-retention",
            "a-exception-boundary",
        },
    },
    "cis-task-verify-cis-deviation": {
        "kind": "task",
        "sections": set(),
    },
    "cis-task-run-level-1-workflow": {
        "kind": "task",
        "sections": set(),
    },
    "cis-task-run-level-2-hardened-workflow": {
        "kind": "task",
        "sections": set(),
    },
}
CIS_GUIDE_KEYREFS = [f"topic.{topic_id}" for topic_id in TOPICS]

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "cis" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    assert DOCTYPES[TOPICS[topic_id]["kind"]] in source
    return ET.fromstring(source)


def _inventory() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _workflow_fixture() -> dict[str, object]:
    return json.loads(WORKFLOW_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_cis_orientation_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id, topic_contract in TOPICS.items():
            root = _topic_root(locale, topic_id)
            topic_kind = topic_contract["kind"]

            assert root.tag == topic_kind
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user security-reviewer",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert root.find("title") is not None
            assert root.find("shortdesc") is not None
            assert len(root.findall("./related-links/link")) >= 4

            if topic_kind == "concept":
                section_ids = {
                    section.attrib["id"] for section in root.findall("./conbody/section")
                }
                assert section_ids == topic_contract["sections"]
                assert all(
                    "".join(section.itertext()).strip()
                    for section in root.findall("./conbody/section")
                )
            else:
                steps = root.findall("./taskbody/steps/step")
                assert len(steps) == 6
                assert root.find("./taskbody/prereq") is not None
                assert root.find("./taskbody/context") is not None
                assert root.find("./taskbody/result") is not None
                assert root.find("./taskbody/postreq") is not None
                assert root.find("./taskbody/steps/step/info/note[@type='warning']") is not None


def test_cis_orientation_topics_are_keyed_and_reachable_from_cis_guide_maps() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"] in CIS_GUIDE_KEYREFS
        }
        assert keydefs == {f"topic.{topic_id}": f"../cis/{topic_id}.dita" for topic_id in TOPICS}

        guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/cis-settings-guide.ditamap").read_text(encoding="utf-8")
        )
        assert [
            topicref.attrib["keyref"] for topicref in guide.findall("topicref")
        ] == CIS_GUIDE_KEYREFS


def test_english_cis_orientation_covers_selection_scope_and_benchmark_facts() -> None:
    inventory = _inventory()
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    starter_presets = {preset["starter_id"]: preset for preset in inventory["starter_presets"]}

    for required in (
        inventory["benchmark"]["upstream_name"],
        inventory["benchmark"]["upstream_version"],
        inventory["benchmark"]["exact_release_date"],
        "Firefox ESR 115.39",
        "Firefox ESR 140.13",
        "Firefox Release 153",
        "Level 1",
        "Level 2",
        "49 mapped recommendations",
        "53 mapped recommendations",
        "55 recommendation records",
        "two unresolved records",
        "cis-l1.esr-115.39",
        "cis-l1.esr-140.13",
        "cis-l1.release-153",
        "cis-l2.esr-115.39",
        "cis-l2.esr-140.13",
        "cis-l2.release-153",
        "manual review",
        "Basic corporate",
        "classroom",
        "kiosk",
        "protected station",
        "SOC-style",
        "starter preset",
        "blank",
        "keep_current",
        "basic_corporate",
        "classroom_kiosk",
        "soc_hard",
        "source attribution",
        "baseline",
        "manual",
        "imported",
        "raw fallback",
        "added_from_cis",
        "already_satisfied",
        "cis_replaced_base",
        "kept_base_only",
        "kept_base_stricter",
        "manual_review_kept_base",
        "17 added_from_cis",
        "15 already_satisfied",
        "20 kept_base_only",
        "4 manual_review_kept_base",
        "30 policy top-level values",
        "33",
        "update governance",
        "proxy mode and lock state",
        "sanitize-on-shutdown",
        "policies.json",
        "AppAutoUpdate",
        "BackgroundAppUpdate",
        "DisableAppUpdate",
        "DisableSystemAddonUpdate",
        "Proxy.Locked",
        "Proxy.Mode",
        "SanitizeOnShutdown.FormData",
        "SanitizeOnShutdown.History",
        "SanitizeOnShutdown.Sessions",
        "enterprise patch management",
        "proxy routing",
        "evidence-retention",
        "external ticket",
        "deployment note",
        "change-control record",
        "no separate persisted CIS exception or waiver model",
        "Firefox runtime behavior",
        "does not mean BPM has tested",
        "do not describe it as compliant",
        "recommendation ID",
        "review date",
        "owner",
        "cis-workflow-level-1-esr-fixture",
        "cis-workflow-level-2-release-fixture",
        "External verification",
        "cis-l1.esr-140.13",
        "cis-l2.release-153",
        "basic_corporate",
        "soc_hard",
        "blank-esr-140.13",
        "cis-workflow-level-1-release-reference",
        "generated mapping table",
        "affected Firefox policy topic",
        "independent deployment verification",
        "not authorized, sponsored, endorsed, certified, or approved by CIS",
        "not a substitute for the official CIS benchmark",
        "does not prove CIS compliance",
    ):
        assert required.casefold() in text.casefold()

    expected_l2_counts = {
        "basic_corporate": {
            "esr-115.39": 42,
            "esr-140.13": 43,
            "esr-153.0": 43,
            "release-153": 43,
        },
        "classroom_kiosk": {
            "esr-115.39": 44,
            "esr-140.13": 45,
            "esr-153.0": 45,
            "release-153": 45,
        },
        "soc_hard": {
            "esr-115.39": 43,
            "esr-140.13": 45,
            "esr-153.0": 45,
            "release-153": 45,
        },
    }
    variant_counts = {
        (starter_id, variant["layer_id"], variant["schema_channel"]): variant[
            "policy_top_level_count"
        ]
        for starter_id in expected_l2_counts
        for variant in starter_presets[starter_id]["variants"]
        if variant["layer_id"] == "cis_l2"
    }
    assert variant_counts == {
        (starter_id, "cis_l2", channel): count
        for starter_id, expected in expected_l2_counts.items()
        for channel, count in expected.items()
    }
    assert inventory["merge_contract"]["decision_types"] == [
        "added_from_cis",
        "already_satisfied",
        "cis_replaced_base",
        "kept_base_only",
        "kept_base_stricter",
        "manual_review_kept_base",
    ]

    for forbidden in (
        "CIS certified",
        "CIS-certified",
        "guarantees CIS compliance",
        "official CIS guidance",
        "administrator guide",
        "RAG",
        "embeddings",
        "generative answer",
    ):
        assert forbidden.casefold() not in text.casefold()


def test_cis_workflows_are_backed_by_deterministic_fixtures() -> None:
    fixture = _workflow_fixture()
    workflow_text = "\n".join(
        "".join(_topic_root("en", topic_id).itertext())
        for topic_id in (
            "cis-task-run-level-1-workflow",
            "cis-task-run-level-2-hardened-workflow",
        )
    )

    assert fixture["backlog_item"] == "BPM090-M6-07"
    assert fixture["target_bpm_version"] == "0.9.0"
    english_catalog = json.loads((REPOSITORY_ROOT / "app/i18n/en.json").read_text(encoding="utf-8"))
    expected_surfaces = [
        english_catalog["profiles.nav_library"],
        english_catalog["profiles.editor_chrome_title"],
        english_catalog["profiles.editor_chrome_settings_link"],
        english_catalog["profiles.compare_route_title"],
        english_catalog["profiles.library_action_export"],
    ]
    assert fixture["route_order"] == [*expected_surfaces, "External verification"]

    workflows = {workflow["workflow_id"]: workflow for workflow in fixture["workflows"]}
    assert workflows["cis-workflow-level-1-esr-fixture"] == {
        "workflow_id": "cis-workflow-level-1-esr-fixture",
        "level": 1,
        "schema_channel": "esr-140.13",
        "cis_layer_id": "cis-l1.esr-140.13",
        "starter_preset": "basic_corporate",
        "comparison_profile": "blank-esr-140.13",
        "expected_mapped_recommendations": 49,
        "manual_review_decision_categories": [
            "update governance",
            "proxy routing",
            "evidence-retention",
            "unsupported mapping research",
            "deprecated target",
            "local deployment requirement",
        ],
        "required_user_surfaces": expected_surfaces,
        "verification_boundary": (
            "BPM validates schema/export/source attribution; runtime verification is external."
        ),
    }
    assert workflows["cis-workflow-level-2-release-fixture"]["level"] == 2
    assert workflows["cis-workflow-level-2-release-fixture"]["schema_channel"] == "release-153"
    assert (
        workflows["cis-workflow-level-2-release-fixture"]["expected_mapped_recommendations"] == 53
    )

    for workflow in fixture["workflows"]:
        assert workflow["workflow_id"] in workflow_text
        assert workflow["cis_layer_id"] in workflow_text
        assert workflow["starter_preset"] in workflow_text
        assert workflow["comparison_profile"] in workflow_text
        for surface in workflow["required_user_surfaces"]:
            assert surface in workflow_text
