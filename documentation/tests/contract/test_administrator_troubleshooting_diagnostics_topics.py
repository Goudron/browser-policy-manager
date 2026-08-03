from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tests.support import make_test_client

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
TASK_DOCTYPE = '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">'

TROUBLESHOOTING_TOPICS = (
    "admin-troubleshoot-failed-startup-probes",
    "admin-troubleshoot-schema-cache-validation",
    "admin-troubleshoot-import-export-failures",
    "admin-troubleshoot-database-storage",
    "admin-troubleshoot-wsl-networking-dependencies",
    "admin-troubleshoot-documentation-portal-build-links",
)
TROUBLESHOOTING_KEYREFS = tuple(f"topic.{topic_id}" for topic_id in TROUBLESHOOTING_TOPICS)
PRODUCTION_BOUNDARY_KEYREF_COUNT = 4
LOCAL_ASSISTANT_KEYREF_COUNT = 3
MIN_LOCALIZED_TEXT_RATIO = {
    "ru": 0.72,
    "de": 0.72,
    "zh-CN": 0.38,
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
REQUIRED_INVARIANT_TERMS = (
    "make dev",
    "GET /health",
    "GET /health/ready",
    "BPM_DATABASE_URL",
    "BPM_SCHEMA_CACHE_DIR",
    "BPM_SCHEMA_HTTP_TIMEOUT",
    "POST $BPM_BASE_URL/api/validate/release-153",
    "POST $BPM_BASE_URL/api/profiles/import/firefox/policies.json",
    "GET $BPM_BASE_URL/api/export/profiles/42/firefox/policies.json",
    "multipart/form-data",
    "sqlite+aiosqlite:///./data/bpm.db",
    "data/bpm.db",
    "alembic upgrade head",
    "BPM_HOST=\"0.0.0.0\"",
    "pip install -e \".[dev]\"",
    "/help/",
    "/openapi.json",
)
FORBIDDEN_UNSAFE_RECOVERY = (
    "edit database rows",
    "hand-edit generated artifacts",
    "automatic rollback is supported",
    "production-ready",
)

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


def test_troubleshooting_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in TROUBLESHOOTING_TOPICS:
            root = _root(locale, topic_id)
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "administrator devops",
                "product": "bpm-0-9-1",
                "platform": "linux windows web",
            }
            assert root.findtext("title")
            assert root.findtext("shortdesc")
            signature = _signature(root)
            assert signature["steps"] == 5
            assert signature["has_prereq"]
            assert signature["has_context"]
            assert signature["has_result"]
            assert signature["has_postreq"]
            assert "warning" in signature["warning_notes"]
            assert len(signature["related"]) == 4


def test_troubleshooting_topics_are_keyed_and_reachable_from_admin_guide() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"] in TROUBLESHOOTING_KEYREFS
        }
        assert keydefs == {
            f"topic.{topic_id}": f"../admin/{topic_id}.dita"
            for topic_id in TROUBLESHOOTING_TOPICS
        }

        admin_guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/administrator-guide.ditamap").read_text(encoding="utf-8")
        )
        topicrefs = [topicref.attrib["keyref"] for topicref in admin_guide.findall(".//topicref")]
        troubleshooting_start = topicrefs.index(TROUBLESHOOTING_KEYREFS[0])
        assert topicrefs[
            troubleshooting_start : troubleshooting_start + len(TROUBLESHOOTING_KEYREFS)
        ] == list(TROUBLESHOOTING_KEYREFS)


def test_troubleshooting_topics_preserve_locale_structure_and_full_peer_content() -> None:
    for topic_id in TROUBLESHOOTING_TOPICS:
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


def test_english_troubleshooting_topics_cover_m12_10_diagnostic_families_and_boundaries() -> None:
    text = "\n".join(_normalized_text(_root("en", topic_id)) for topic_id in TROUBLESHOOTING_TOPICS)
    casefolded = text.casefold()

    for required in (
        "failed startup",
        "unreachable probes",
        "schema cache",
        "API validation errors",
        "import and export failures",
        "database and storage issues",
        "WSL networking",
        "stale Python dependencies",
        "unavailable documentation portal",
        "deployment owner",
        "preserve user data",
        "separate product defects from operator",
    ):
        assert required.casefold() in casefolded
    for term in REQUIRED_INVARIANT_TERMS:
        assert term in text
    for forbidden in FORBIDDEN_UNSAFE_RECOVERY:
        assert forbidden.casefold() not in casefolded


def test_troubleshooting_examples_execute_representative_api_diagnostics() -> None:
    with make_test_client() as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready", "ready": True}

        invalid_shape = client.post("/api/validate/release-153", json={"document": 123})
        assert invalid_shape.status_code == 200
        assert invalid_shape.json()["ok"] is False

        invalid_policies = client.post("/api/validate/release-153", json={"document": {"policies": []}})
        assert invalid_policies.status_code == 400

        unknown_profile = client.post(
            "/api/validate/beta-999",
            json={"document": {"policies": {"DisableTelemetry": True}}},
        )
        assert unknown_profile.status_code == 404

        duplicate_name = "docs-troubleshoot-duplicate"
        first = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": duplicate_name,
                "schema_version": "release-153",
                "document": {"policies": {"DisableTelemetry": True}},
            },
        )
        assert first.status_code == 201, first.text
        duplicate = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": duplicate_name,
                "schema_version": "release-153",
                "document": {"policies": {"DisableTelemetry": True}},
            },
        )
        assert duplicate.status_code == 409

        multipart = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "name": "docs-troubleshoot-multipart",
                "schema_version": "release-153",
                "compliance": json.dumps({"source": "troubleshooting"}),
            },
            files={
                "file": (
                    "policies.json",
                    json.dumps({"policies": {"DisablePrivateBrowsing": True}}),
                    "application/json",
                )
            },
        )
        assert multipart.status_code == 201, multipart.text

        missing_export = client.get("/api/export/profiles/999999/firefox/policies.json")
        assert missing_export.status_code == 404
