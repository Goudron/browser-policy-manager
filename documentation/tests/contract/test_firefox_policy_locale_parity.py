from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
GENERATED_FIREFOX_ROOT = DOCUMENTATION_ROOT / "src/generated/firefox"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
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
    # Structural parity is checked separately; this only rejects compact fallbacks.
    "zh-CN": 0.30,
    "fr": 0.75,
    "es-ES": 0.75,
}

pytestmark = pytest.mark.docs_contract


def _root(locale: str, topic_name: str) -> ET.Element:
    return ET.fromstring((DITA_ROOT / locale / "firefox" / topic_name).read_text(encoding="utf-8"))


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
        "related": [link.attrib["keyref"] for link in root.findall("./related-links/link")],
        "codeph": Counter(element.text or "" for element in root.iter("codeph")),
    }


def test_firefox_policy_authored_topics_are_parallel_in_every_locale() -> None:
    expected = {path.name for path in (DITA_ROOT / "en/firefox").glob("*.dita")}

    assert expected == {
        "fx-concept-bpm-firefox-boundary.dita",
        "fx-concept-complex-policy-families.dita",
        "fx-concept-policy-selection.dita",
        "fx-concept-release-esr-differences.dita",
        "fx-concept-starter-presets.dita",
        "fx-reference-managed-preference-locking.dita",
        "fx-task-review-complex-policy-configuration.dita",
    }
    for locale in LOCALIZED_LOCALES:
        assert {path.name for path in (DITA_ROOT / locale / "firefox").glob("*.dita")} == expected


def test_firefox_policy_localized_topics_preserve_structure_links_and_technical_tokens() -> None:
    for english_topic in sorted((DITA_ROOT / "en/firefox").glob("*.dita")):
        english_root = _root("en", english_topic.name)
        english_signature = _topic_signature(english_root)

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic.name)
            assert localized_root.attrib == {
                "id": english_root.attrib["id"],
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert _topic_signature(localized_root) == english_signature


def test_firefox_policy_localized_topics_are_full_peers_not_english_fallbacks() -> None:
    for english_topic in sorted((DITA_ROOT / "en/firefox").glob("*.dita")):
        english_root = _root("en", english_topic.name)
        english_text = _normalized_text(english_root)
        english_title = english_root.findtext("title")
        english_length = len(english_text)

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic.name)
            localized_text = _normalized_text(localized_root)
            localized_title = localized_root.findtext("title")

            assert localized_text != english_text
            assert localized_title != english_title
            assert len(localized_text) >= english_length * MIN_LOCALIZED_TEXT_RATIO[locale]
            assert all(marker not in localized_text for marker in COMPACT_OR_FALLBACK_MARKERS)


def test_firefox_generated_policy_skeletons_remain_language_neutral_schema_facts() -> None:
    """Generated policy facts are not compact locale peers and must stay byte-stable.

    The localized authored Firefox Guide explains how to choose, review, validate, and use these
    generated schema-grounded policy references. Policy IDs, JSON examples, schema channels,
    Mozilla source facts, and provenance strings are intentionally language-neutral generated facts.
    """

    generated_policy_topics = sorted((GENERATED_FIREFOX_ROOT / "policies").glob("fx-policy-*.dita"))
    assert len(generated_policy_topics) == 121
    assert not any(
        list((DITA_ROOT / locale / "firefox").glob("fx-policy-*.dita")) for locale in LOCALES
    )

    sample = ET.parse(GENERATED_FIREFOX_ROOT / "policies/fx-policy-DisableTelemetry.dita").getroot()
    assert sample.attrib == {
        "id": "fx-policy-DisableTelemetry",
        "audience": "user",
        "product": "bpm-0-9-0",
        "platform": "web",
        "props": "firefox-release firefox-esr",
        "otherprops": "policy(DisableTelemetry)",
    }
    text = _normalized_text(sample)
    for required in (
        "DisableTelemetry",
        "policies",
        "esr-140.13",
        "esr-153.0",
        "release-153",
        "MPL-2.0",
        "mozilla-policy-templates-v7.12",
        "mozilla-policy-templates-v8.0",
        "BPM is not affiliated with or endorsed by Mozilla.",
    ):
        assert required in text
