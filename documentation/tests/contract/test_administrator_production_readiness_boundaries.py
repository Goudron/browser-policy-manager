from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
TASK_DOCTYPE = '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">'

PRODUCTION_BOUNDARY_TOPICS = (
    "admin-task-assess-single-node-source-readiness",
    "admin-task-review-network-exposure-proxy-readiness",
    "admin-task-plan-monitoring-backup-update-windows",
    "admin-task-record-ha-production-deferred-boundaries",
)
PRODUCTION_BOUNDARY_KEYREFS = tuple(f"topic.{topic_id}" for topic_id in PRODUCTION_BOUNDARY_TOPICS)
DOCUMENTATION_ASSISTANT_KEYREFS = (
    "topic.admin-task-operate-local-documentation-assistant",
    "topic.admin-task-maintain-local-documentation-assistant",
)
MIN_LOCALIZED_TEXT_RATIO = {
    "ru": 0.72,
    "de": 0.72,
    "zh-CN": 0.30,
    "fr": 0.72,
    "es-ES": 0.72,
}
COMPACT_OR_FALLBACK_MARKERS = (
    "English source",
    "английский источник",
    "englische Quelle",
    "source anglaise",
    "fuente inglesa",
    "英文源",
    "compact summary",
    "translation pending",
    "TODO",
)
REQUIRED_CURRENT_STATE_TOKENS = (
    "current-state single-node source operation",
    "single-node source operation",
    "source-run",
    "make dev",
    "uvicorn app.main:app",
    "git rev-parse --short HEAD",
    "BPM_HOST",
    "BPM_PORT",
    "BPM_DATABASE_URL",
    "BPM_DOCUMENTATION_SITE_DIR",
    "BPM_SCHEMA_CACHE_DIR",
    "GET /health",
    "GET /health/ready",
    "curl -fsS http://127.0.0.1:8000/health",
    "curl -fsS http://127.0.0.1:8000/health/ready",
    "data/bpm.db",
    "policies.json",
    "GET $BPM_BASE_URL/api/export/profiles/42/firefox/policies.json",
    "sha256sum backups/bpm-pre-update.db",
    "/help/",
)
REQUIRED_PREPARATION_TERMS = (
    "network exposure",
    "proxy-readiness questions",
    "monitoring inputs",
    "backup/export evidence",
    "update window",
    "organization-owned controls",
)
REQUIRED_DEFERRED_TERMS = (
    "external responsibilities",
    "operating assumptions",
    "service and proxy responsibilities",
    "HA and upgrade design requirements",
    "organization-owned controls",
    "production hardening",
    "RTO/RPO",
)
FORBIDDEN_SUPPORTED_CLAIMS = (
    "production-ready",
    "TLS termination is supported",
    "reverse proxy is supported",
    "HA is supported",
    "rolling upgrades are supported",
    "restore automation is provided",
    "managed secrets are supported",
    "packaged service is provided",
)
INVARIANT_TOKENS_BY_TOPIC = {
    "admin-task-assess-single-node-source-readiness": (
        "BPM_DATABASE_URL",
        "BPM_DOCUMENTATION_SITE_DIR",
        "BPM_SCHEMA_CACHE_DIR",
        "make dev",
        "GET /health",
        "GET /health/ready",
        "data/bpm.db",
        "policies.json",
    ),
    "admin-task-review-network-exposure-proxy-readiness": (
        "127.0.0.1",
        'BPM_HOST="0.0.0.0"',
        'BPM_PORT="8000"',
        "BPM_CORS_ALLOW_ORIGINS",
        "TLS",
        "HA",
    ),
    "admin-task-plan-monitoring-backup-update-windows": (
        "stdout",
        "stderr",
        "GET /health",
        "GET /health/ready",
        "sha256sum backups/bpm-pre-update.db",
        "HA",
    ),
    "admin-task-record-ha-production-deferred-boundaries": (
        "TLS",
        "HA",
        "RTO/RPO",
    ),
}

pytestmark = pytest.mark.docs_contract


def _source(locale: str, topic_id: str) -> str:
    return (DITA_ROOT / locale / "admin" / f"{topic_id}.dita").read_text(encoding="utf-8")


def _root(locale: str, topic_id: str) -> ET.Element:
    source = _source(locale, topic_id)
    assert TASK_DOCTYPE in source
    return ET.fromstring(source)


def _normalized_text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


def _signature(root: ET.Element) -> dict[str, object]:
    taskbody = root.find("taskbody")
    assert taskbody is not None
    return {
        "steps": len(taskbody.findall("./steps/step")),
        "has_prereq": taskbody.find("prereq") is not None,
        "has_context": taskbody.find("context") is not None,
        "has_result": taskbody.find("result") is not None,
        "has_postreq": taskbody.find("postreq") is not None,
        "warning_notes": [note.attrib.get("type") for note in taskbody.findall(".//note")],
        "related": [link.attrib["keyref"] for link in root.findall("./related-links/link")],
    }


def test_production_boundary_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in PRODUCTION_BOUNDARY_TOPICS:
            root = _root(locale, topic_id)
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "administrator devops",
                "product": "bpm-0-9-1",
                "platform": "linux windows web",
            }
            assert root.findtext("title", "").strip()
            assert root.findtext("shortdesc", "").strip()
            signature = _signature(root)
            assert signature["steps"] == 4
            assert signature["has_prereq"]
            assert signature["has_context"]
            assert signature["has_result"]
            assert signature["has_postreq"]
            assert "warning" in signature["warning_notes"]
            assert len(signature["related"]) == 4


def test_production_boundary_topics_are_keyed_and_precede_the_local_assistant_section() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"] in PRODUCTION_BOUNDARY_KEYREFS
        }
        assert keydefs == {
            f"topic.{topic_id}": f"../admin/{topic_id}.dita"
            for topic_id in PRODUCTION_BOUNDARY_TOPICS
        }

        admin_guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/administrator-guide.ditamap").read_text(encoding="utf-8")
        )
        topicrefs = [topicref.attrib["keyref"] for topicref in admin_guide.findall(".//topicref")]
        assert topicrefs[-len(DOCUMENTATION_ASSISTANT_KEYREFS) :] == list(
            DOCUMENTATION_ASSISTANT_KEYREFS
        )
        assistant_start = topicrefs.index(DOCUMENTATION_ASSISTANT_KEYREFS[0])
        assert all(topicrefs.index(keyref) < assistant_start for keyref in PRODUCTION_BOUNDARY_KEYREFS)


def test_production_boundary_topics_preserve_locale_structure_and_full_peer_content() -> None:
    for topic_id in PRODUCTION_BOUNDARY_TOPICS:
        english_root = _root("en", topic_id)
        english_signature = _signature(english_root)
        english_text = _normalized_text(english_root)

        for locale in LOCALIZED_LOCALES:
            localized_source = _source(locale, topic_id)
            localized_root = _root(locale, topic_id)
            localized_text = _normalized_text(localized_root)
            assert _signature(localized_root) == english_signature
            assert localized_text != english_text
            assert len(localized_text) >= len(english_text) * MIN_LOCALIZED_TEXT_RATIO[locale]
            assert all(marker not in localized_source for marker in COMPACT_OR_FALLBACK_MARKERS)
            for token in INVARIANT_TOKENS_BY_TOPIC[topic_id]:
                assert token in localized_source


def test_english_production_boundary_topics_cover_current_preparation_and_operating_responsibilities() -> None:
    text = "\n".join(_normalized_text(_root("en", topic_id)) for topic_id in PRODUCTION_BOUNDARY_TOPICS)
    casefolded = text.casefold()

    for token in REQUIRED_CURRENT_STATE_TOKENS:
        assert token in text
    for term in (*REQUIRED_PREPARATION_TERMS, *REQUIRED_DEFERRED_TERMS):
        assert re.search(re.escape(term), text, re.IGNORECASE), term
    for forbidden in FORBIDDEN_SUPPORTED_CLAIMS:
        assert forbidden.casefold() not in casefolded


def test_production_boundary_links_point_to_existing_administrator_evidence_topics() -> None:
    existing_keyrefs = set()
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        existing_keyrefs = {keydef.attrib["keys"] for keydef in keys.findall("keydef")}
        for topic_id in PRODUCTION_BOUNDARY_TOPICS:
            for keyref in _signature(_root(locale, topic_id))["related"]:
                assert keyref in existing_keyrefs
