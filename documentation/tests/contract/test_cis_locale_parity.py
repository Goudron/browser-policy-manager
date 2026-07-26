from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
GENERATED_CIS_ROOT = DOCUMENTATION_ROOT / "src/generated/cis"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
EXPECTED_CIS_TOPICS = {
    "cis-concept-levels-channels-layers.dita",
    "cis-concept-manual-review-exceptions.dita",
    "cis-concept-orientation.dita",
    "cis-concept-presets-layers-merge.dita",
    "cis-task-run-level-1-workflow.dita",
    "cis-task-run-level-2-hardened-workflow.dita",
    "cis-task-select-cis-baseline.dita",
    "cis-task-trace-cis-source.dita",
    "cis-task-verify-cis-deviation.dita",
}
COMPACT_OR_FALLBACK_MARKERS = (
    "English source",
    "английский источник",
    "englische Quelle",
    "source anglaise",
    "fuente inglesa",
    "英文源",
    "See the English topic",
    "Use the English topic",
    "compact summary",
    "reduced summary",
    "not localized",
    "translation pending",
    "TODO",
)
MIN_LOCALIZED_TEXT_RATIO = {
    "ru": 0.75,
    "de": 0.75,
    "zh-CN": 0.30,
    "fr": 0.75,
    "es-ES": 0.75,
}
REQUIRED_INVARIANT_TERMS = (
    "Firefox ESR 140.13",
    "49",
    "53",
    "55",
    "cis-l1.esr-140.13",
    "cis-l1.release-153",
    "cis-l2.esr-140.13",
    "cis-l2.release-153",
    "keep_current",
    "basic_corporate",
    "classroom_kiosk",
    "soc_hard",
    "added_from_cis",
    "already_satisfied",
    "cis_replaced_base",
    "kept_base_only",
    "kept_base_stricter",
    "manual_review_kept_base",
    "CIS",
    "AppAutoUpdate",
    "BackgroundAppUpdate",
    "DisableAppUpdate",
    "DisableSystemAddonUpdate",
    "Proxy.Locked",
    "Proxy.Mode",
    "SanitizeOnShutdown.FormData",
    "SanitizeOnShutdown.History",
    "SanitizeOnShutdown.Sessions",
    "policies.json",
    "cis-workflow-level-1-esr-fixture",
    "cis-workflow-level-2-release-fixture",
)
ENGLISH_SEMANTIC_TERMS = (
    "CIS Mozilla Firefox ESR GPO Benchmark",
    "Firefox Release 153",
    "Level 1",
    "Level 2",
    "blank",
    "baseline",
    "manual",
    "imported",
    "raw",
    "update governance",
    "proxy routing",
    "evidence-retention",
)
UI_CATALOG_KEYS = (
    "profiles.nav_library",
    "profiles.editor_chrome_title",
    "profiles.editor_chrome_settings_link",
    "profiles.compare_route_title",
    "profiles.library_action_export",
)

pytestmark = pytest.mark.docs_contract


def _root(locale: str, topic_name: str) -> ET.Element:
    return ET.fromstring((DITA_ROOT / locale / "cis" / topic_name).read_text(encoding="utf-8"))


def _normalized_text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


def _body(root: ET.Element) -> ET.Element:
    body = root.find("conbody")
    if body is None:
        body = root.find("taskbody")
    if body is None:
        body = root.find("refbody")
    assert body is not None
    return body


def _topic_signature(root: ET.Element) -> dict[str, object]:
    body = _body(root)
    return {
        "tag": root.tag,
        "sections": [section.attrib.get("id") for section in body.findall("section")],
        "steps": len(body.findall("./steps/step")),
        "step_notes": [step.find(".//note") is not None for step in body.findall("./steps/step")],
        "step_warning_notes": [
            note.attrib.get("type")
            for step in body.findall("./steps/step")
            for note in step.findall(".//note")
        ],
        "related": [link.attrib["keyref"] for link in root.findall("./related-links/link")],
        "codeph": Counter(element.text or "" for element in root.iter("codeph")),
        "tables": [
            (
                table.attrib.get("outputclass"),
                len(table.findall("strow")),
                len(table.findall("./sthead/stentry")),
            )
            for table in body.findall(".//simpletable")
        ],
    }


def test_cis_authored_topics_are_parallel_in_every_locale() -> None:
    assert {path.name for path in (DITA_ROOT / "en/cis").glob("*.dita")} == EXPECTED_CIS_TOPICS
    for locale in LOCALIZED_LOCALES:
        assert {path.name for path in (DITA_ROOT / locale / "cis").glob("*.dita")} == EXPECTED_CIS_TOPICS


def test_cis_localized_topics_preserve_structure_links_notes_and_tokens() -> None:
    for english_topic in sorted(EXPECTED_CIS_TOPICS):
        english_root = _root("en", english_topic)
        english_signature = _topic_signature(english_root)

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic)
            assert localized_root.attrib == {
                "id": english_root.attrib["id"],
                XML_LANG: locale,
                "audience": "user security-reviewer",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert _topic_signature(localized_root) == english_signature


def test_cis_localized_topics_are_full_peers_not_compact_fallbacks() -> None:
    for english_topic in sorted(EXPECTED_CIS_TOPICS):
        english_root = _root("en", english_topic)
        english_text = _normalized_text(english_root)
        english_title = english_root.findtext("title")
        english_length = len(english_text)

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic)
            localized_text = _normalized_text(localized_root)
            localized_title = localized_root.findtext("title")

            assert localized_text != english_text
            assert localized_title != english_title
            assert len(localized_text) >= english_length * MIN_LOCALIZED_TEXT_RATIO[locale]
            assert all(marker not in localized_text for marker in COMPACT_OR_FALLBACK_MARKERS)


def test_cis_localized_topics_preserve_required_cis_facts_and_boundaries() -> None:
    for locale in LOCALES:
        locale_text = "\n".join(
            _normalized_text(_root(locale, topic_name))
            for topic_name in sorted(EXPECTED_CIS_TOPICS)
        )
        casefolded_text = locale_text.casefold()

        for required in REQUIRED_INVARIANT_TERMS:
            assert required.casefold() in casefolded_text
        if locale == "en":
            for required in ENGLISH_SEMANTIC_TERMS:
                assert required.casefold() in casefolded_text
        catalog = json.loads(
            (DOCUMENTATION_ROOT.parent / f"app/i18n/{locale}.json").read_text(encoding="utf-8")
        )
        for key in UI_CATALOG_KEYS:
            assert catalog[key].casefold() in casefolded_text

        assert "RAG" not in locale_text
        for forbidden in (
            "CIS certified",
            "CIS-certified",
            "guarantees CIS compliance",
            "official CIS guidance",
            "embeddings",
            "generative answer",
        ):
            assert forbidden.casefold() not in casefolded_text


def test_cis_generated_recommendations_remain_language_neutral_mapping_facts() -> None:
    """Generated CIS facts are shared, not compact localized topic peers.

    The authored CIS Guide topics above explain selection, mapping review, source tracing, manual
    review, workflows, and verification in every locale. The generated recommendation references
    intentionally keep CIS identifiers, policy/preference paths, layer values, provenance hashes,
    and protected-source boundaries language-neutral.
    """

    generated_topics = sorted((GENERATED_CIS_ROOT / "recommendations").glob("cis-rec-*.dita"))
    assert len(generated_topics) == 53
    assert not any(
        list((DITA_ROOT / locale / "cis").glob("cis-rec-*.dita"))
        for locale in LOCALES
    )

    sample = ET.parse(GENERATED_CIS_ROOT / "recommendations/cis-rec-1-1-1-1.dita").getroot()
    assert XML_LANG not in sample.attrib
    assert sample.attrib == {
        "id": "cis-rec-1-1-1-1",
        "audience": "user security-reviewer",
        "product": "bpm-0-9-0",
        "platform": "web",
        "props": "cis-level-1",
        "otherprops": "cis(1.1.1.1)",
    }
    text = _normalized_text(sample)
    for required in (
        "CIS recommendation 1.1.1.1",
        "cis-firefox-esr-gpo",
        "CIS Mozilla Firefox ESR GPO Benchmark",
        "CC-BY-NC-SA-4.0",
        "source expression are not copied, translated, indexed, or packaged",
        "InstallAddonsPermission.Default",
        "fx-policy-InstallAddonsPermission",
        "cis-l1.esr-140.13",
        "cis-l2.release-153",
        "f3736db8a1e089b5cce4901698b5d871a469bea84c2e8335e9703a4f5629a85d",
    ):
        assert required in text
