from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.core.policy_validation import validate_profile_policies_for_channel

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
FAMILY_FIXTURE = (
    DOCUMENTATION_ROOT
    / "fixtures/firefox-policy-families/complex-policy-family-examples-0.9.0.json"
)
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
DOCTYPES = {
    "concept": '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">',
    "task": '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">',
    "reference": '<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">',
}

TOPICS = {
    "fx-concept-policy-selection": {
        "kind": "concept",
        "sections": {
            "a-start-with-outcome",
            "a-check-channel",
            "a-pick-edit-surface",
            "a-review-value-shape",
            "bpm096-localized-current",
        },
    },
    "fx-concept-release-esr-differences": {
        "kind": "concept",
        "sections": {
            "a-current-channels",
            "a-support-badges",
            "a-release-only",
            "a-changed-definitions",
            "a-user-action",
            "bpm096-localized-current",
        },
    },
    "fx-concept-bpm-firefox-boundary": {
        "kind": "concept",
        "sections": {
            "a-profile-model",
            "a-boundary-document",
            "a-runtime-responsibility",
            "a-managed-preferences",
        },
    },
    "fx-concept-starter-presets": {
        "kind": "concept",
        "sections": {
            "a-purpose",
            "a-basic-corporate",
            "a-classroom-kiosk",
            "a-protected-station",
            "a-after-selection",
            "bpm096-localized-current",
        },
    },
    "fx-concept-complex-policy-families": {
        "kind": "concept",
        "sections": {
            "a-extensions",
            "a-permissions",
            "a-updates",
            "a-certificates",
            "a-proxy",
            "a-search-homepage",
            "a-privacy-ai",
        },
    },
    "fx-task-review-complex-policy-configuration": {
        "kind": "task",
        "sections": set(),
    },
    "fx-reference-managed-preference-locking": {
        "kind": "reference",
        "sections": {
            "a-container-policy",
            "a-status-values",
            "a-type-values",
            "a-source-conflicts",
            "a-safe-review",
        },
    },
}
FIREFOX_GUIDE_KEYREFS = [f"topic.{topic_id}" for topic_id in TOPICS]

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "firefox" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    assert DOCTYPES[TOPICS[topic_id]["kind"]] in source
    return ET.fromstring(source)


def test_firefox_policy_concepts_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id, topic_contract in TOPICS.items():
            root = _topic_root(locale, topic_id)
            topic_kind = topic_contract["kind"]
            section_ids = topic_contract["sections"]
            assert root.tag == topic_kind
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert root.find("title") is not None
            assert root.find("shortdesc") is not None
            if topic_kind == "concept":
                assert {
                    section.attrib["id"] for section in root.findall("./conbody/section")
                } == section_ids
            elif topic_kind == "reference":
                assert {
                    section.attrib["id"] for section in root.findall("./refbody/section")
                } == section_ids
            else:
                steps = root.findall("./taskbody/steps/step")
                assert len(steps) == 5
                assert root.find("./taskbody/prereq") is not None
                assert root.find("./taskbody/context") is not None
                assert root.find("./taskbody/result") is not None
                assert root.find("./taskbody/postreq") is not None
                assert root.find("./taskbody/steps/step/info/note[@type='warning']") is not None
            assert len(root.findall("./related-links/link")) >= 2


def test_firefox_policy_concepts_are_keyed_and_reachable_from_policy_guide_maps() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"] in FIREFOX_GUIDE_KEYREFS
        }
        assert keydefs == {
            f"topic.{topic_id}": f"../firefox/{topic_id}.dita" for topic_id in TOPICS
        }

        guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/firefox-policy-guide.ditamap").read_text(encoding="utf-8")
        )
        assert [
            topicref.attrib["keyref"] for topicref in guide.findall("topicref")
        ] == FIREFOX_GUIDE_KEYREFS


def test_english_firefox_policy_concepts_cover_selection_boundary_and_presets() -> None:
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)
    for required in (
        "Firefox Release 153",
        "ESR 140.13",
        "support badge",
        "Release-only",
        "AIControls",
        "VisualSearchEnabled",
        "Guided Editor",
        "All Settings",
        "JSON Editor",
        "policies.json",
        "managed preferences",
        "Preferences",
        "validation",
        "Firefox runtime",
        "Basic corporate",
        "classroom",
        "kiosk",
        "protected-station",
        "SOC-style",
        "CIS layer",
        "ExtensionSettings",
        "Extensions",
        "Permissions",
        "DisableAppUpdate",
        "AppAutoUpdate",
        "DisableSystemAddonUpdate",
        "Certificates",
        "Proxy",
        "SearchEngines",
        "Homepage",
        "EnableTrackingProtection",
        "Cookies",
        "locked",
        "raw fallback",
        "unknown preserved fields",
        "Release-only",
        "do not add AI functionality",
    ):
        assert required.casefold() in text.casefold()

    assert "administrator guide" not in text.casefold()


def test_complex_policy_family_fixture_is_schema_valid_for_declared_channels() -> None:
    fixture = json.loads(FAMILY_FIXTURE.read_text(encoding="utf-8"))

    assert fixture["schema_version"] == 1
    assert fixture["backlog_item"] == "BPM090-M5-06"
    assert fixture["target_bpm_version"] == "0.9.0"
    assert {example["family"] for example in fixture["examples"]} == {
        "updates",
        "extensions",
        "permissions",
        "certificates",
        "proxy",
        "search",
        "homepage",
        "privacy",
        "ai-controls",
        "managed-preferences",
    }
    assert len(fixture["examples"]) == 10

    examples_by_id = {example["id"]: example for example in fixture["examples"]}
    assert examples_by_id["ai-controls-baseline"]["channels"] == ["esr-153.0", "release-153"]

    for example in fixture["examples"]:
        assert example["channels"]
        for channel in example["channels"]:
            assert validate_profile_policies_for_channel(example["policies"], channel) == []
