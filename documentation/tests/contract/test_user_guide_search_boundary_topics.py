from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
SEARCH_CONTRACT = DOCUMENTATION_ROOT / "config/search-corpus-and-results-0.9.0.json"
ACCESSIBILITY_SECURITY_CONTRACT = (
    REPOSITORY_ROOT / "docs/architecture/product-documentation-accessibility-security-contract-0.9.0.md"
)
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
TOPIC_ID = "ug-concept-documentation-search-boundary"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

pytestmark = pytest.mark.docs_contract


def _root(locale: str) -> ET.Element:
    return ET.fromstring((DITA_ROOT / locale / "user" / f"{TOPIC_ID}.dita").read_text(encoding="utf-8"))


def _normalized_text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


def test_search_boundary_architecture_contract_excludes_ai_functionality() -> None:
    search_contract = json.loads(SEARCH_CONTRACT.read_text(encoding="utf-8"))
    architecture = ACCESSIBILITY_SECURITY_CONTRACT.read_text(encoding="utf-8")

    assert search_contract["search_mode"] == "deterministic-local-static"
    assert search_contract["non_ai_boundary"]["mode"] == "no-ai-no-rag-no-embeddings-no-generative-answers"
    for term in (
        "conversational answers",
        "semantic embeddings",
        "vector retrieval",
        "RAG",
        "generative summaries",
        "Future AI-assisted documentation functionality requires a separate approved epic",
    ):
        assert term in architecture
    assert "external AI/search" in architecture
    assert "services" in architecture


def test_documentation_search_boundary_topic_is_reachable_in_every_locale() -> None:
    for locale in LOCALES:
        root = _root(locale)
        assert root.tag == "concept"
        assert root.attrib == {
            "id": TOPIC_ID,
            XML_LANG: locale,
            "audience": "user",
            "product": "bpm-0-9-0",
            "platform": "web",
        }

        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"].startswith("topic.")
        }
        assert keydefs[f"topic.{TOPIC_ID}"] == f"../user/{TOPIC_ID}.dita"

        guide = ET.fromstring((DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8"))
        orient = next(
            topichead
            for topichead in guide.findall("topichead")
            if topichead.find("./topicmeta/data[@name='intent-id']").attrib["value"] == "orient-and-plan"
        )
        assert orient is not None
        assert f"topic.{TOPIC_ID}" in [
            topicref.attrib["keyref"]
            for topicref in orient.findall("topicref")
        ]


def test_documentation_search_boundary_topics_have_full_locale_parity() -> None:
    english_text = _normalized_text(_root("en"))
    expected_sections = [
        "a-local-offline",
        "a-deterministic-results",
        "a-not-ai",
        "a-product-ai-policies",
    ]

    for locale in LOCALES:
        root = _root(locale)
        assert [section.attrib["id"] for section in root.findall("./conbody/section")] == expected_sections
        text = _normalized_text(root)
        for required in (
            "RAG",
            "policy IDs",
            "CIS recommendation IDs",
            "API operation IDs",
        ):
            assert required in text
        assert (
            "external search service" in text
            or "внешнему поисковому сервису" in text
            or "externen Suchdienst" in text
            or "外部搜索服务" in text
            or "service de recherche externe" in text
            or "servicio de búsqueda externo" in text
        )
        assert (
            "telemetry" in text
            or "телеметрии" in text
            or "Telemetrie" in text
            or "遥测" in text
            or "télémétrie" in text
            or "telemetría" in text
        )
        assert "AI" in text or "KI" in text or "IA" in text

    for locale in LOCALES[1:]:
        assert _normalized_text(_root(locale)) != english_text
