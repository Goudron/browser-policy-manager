from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
FIXTURES_ROOT = DOCUMENTATION_ROOT / "fixtures/import-export"
API_INVENTORY = REPOSITORY_ROOT / "docs/architecture/api-documentation-inventory-0.9.0.md"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

TOPICS = {
    "ug-task-import-policies-json": "create-and-start",
    "ug-task-export-policies-json": "review-validate-and-finish",
}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "user" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source
    return ET.fromstring(source)


def _section_keyrefs(locale: str) -> dict[str, list[str]]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8")
    )
    sections: dict[str, list[str]] = {}
    for topichead in root.findall("topichead"):
        intent = topichead.find("./topicmeta/data[@name='intent-id']")
        assert intent is not None
        sections[intent.attrib["value"]] = [
            topicref.attrib["keyref"].removeprefix("topic.")
            for topicref in topichead.findall("topicref")
        ]
    return sections


def _case_topics() -> dict[str, dict[str, object]]:
    case_map = json.loads(USER_GUIDE_MAP.read_text(encoding="utf-8"))
    return {
        topic["topic_id"]: topic for section in case_map["sections"] for topic in section["topics"]
    }


def test_import_export_fixtures_are_canonical_and_safe() -> None:
    import_doc = json.loads((FIXTURES_ROOT / "firefox-policies-import.example.json").read_text())
    json_request = json.loads((FIXTURES_ROOT / "api-json-import-request.example.json").read_text())
    multipart = json.loads((FIXTURES_ROOT / "multipart-import-fields.example.json").read_text())
    export_doc = json.loads((FIXTURES_ROOT / "firefox-policies-export.example.json").read_text())

    assert set(import_doc) == {"policies"}
    assert set(export_doc) == {"policies"}
    assert "policies" in json_request["document"]
    assert json_request["schema_version"] == "release-153"
    assert "channel" not in json_request
    assert multipart["endpoint"] == "/api/profiles/import/firefox/policies.json"
    assert multipart["content_type"] == "multipart/form-data"
    assert multipart["fields"]["file"] == "firefox-policies-import.example.json"
    assert multipart["fields"]["schema_version"] == "release-153"
    assert "channel" not in multipart["fields"]
    assert json.loads(multipart["fields"]["compliance"]) == {"source": "documentation-fixture"}
    fixture_text = json.dumps([import_doc, json_request, multipart, export_doc], sort_keys=True)
    assert "example.invalid" in fixture_text
    assert "localhost" not in fixture_text


def test_import_export_topics_exist_in_every_locale_with_task_contract() -> None:
    for locale in LOCALES:
        for topic_id in TOPICS:
            root = _topic_root(locale, topic_id)
            assert root.tag == "task"
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            taskbody = root.find("taskbody")
            assert taskbody is not None
            assert taskbody.find("prereq") is not None
            assert taskbody.find("context") is not None
            assert taskbody.findall("./steps/step")
            assert taskbody.find("result") is not None
            assert taskbody.find("postreq") is not None
            assert taskbody.find(".//note[@type='warning']") is not None
            assert root.findall("./related-links/link")


def test_import_export_topics_are_keyed_reachable_and_case_mapped() -> None:
    case_topics = _case_topics()
    assert case_topics["ug-task-import-policies-json"]["capability_ids"] == [
        "CAP-LIB-009",
        "CAP-BOUNDARY-003",
    ]
    assert case_topics["ug-task-export-policies-json"]["capability_ids"] == [
        "CAP-LIB-016",
        "CAP-JSON-006",
        "CAP-BOUNDARY-004",
    ]

    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"].startswith("topic.")
        }
        sections = _section_keyrefs(locale)
        for topic_id, section_id in TOPICS.items():
            assert keydefs[f"topic.{topic_id}"] == f"../user/{topic_id}.dita"
            assert topic_id in sections[section_id]


def test_english_topics_document_boundary_shapes_and_link_to_admin_api_options() -> None:
    import_text = "".join(_topic_root("en", "ug-task-import-policies-json").itertext())
    export_text = "".join(_topic_root("en", "ug-task-export-policies-json").itertext())
    api_inventory = API_INVENTORY.read_text(encoding="utf-8")

    for required in (
        "boundary document",
        "normalized",
        "top-level policies",
        "Release",
        "ESR",
        "malformed JSON",
        "duplicate name",
        "unsupported content type",
        "validation errors",
    ):
        assert required.casefold() in import_text.casefold()
    assert "API-adjacent import shapes" not in import_text
    assert "firefox-release" not in import_text
    for required in (
        "application/json",
        "download=1",
        "pretty=1",
        "indent",
        "include_deleted",
        "Archived profiles",
        "BPM profile metadata",
        "not exported",
    ):
        assert required.casefold() in export_text.casefold()
    assert "JSON `FirefoxPoliciesJsonImportRequest` or multipart import fields" in api_inventory
    assert "Profile CRUD exposes BPM's normalized `flags`" in api_inventory
