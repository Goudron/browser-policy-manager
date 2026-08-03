from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4

import pytest

from tests.support import make_test_client

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
TASK_DOCTYPE = '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">'

DEVOPS_RUNBOOK_TOPICS = (
    "admin-task-run-control-product-inventory-pull",
    "admin-task-run-validate-before-apply-update",
    "admin-task-run-import-review-export-handoff",
    "admin-task-gate-control-product-startup",
    "admin-task-record-integration-failure-audit",
)
DEVOPS_RUNBOOK_KEYREFS = tuple(f"topic.{topic_id}" for topic_id in DEVOPS_RUNBOOK_TOPICS)
TROUBLESHOOTING_KEYREF_COUNT = 6
PRODUCTION_BOUNDARY_KEYREF_COUNT = 4
LOCAL_ASSISTANT_KEYREF_COUNT = 3
REQUIRED_INVARIANT_TERMS = (
    "$BPM_BASE_URL",
    "API-PROFILE-001",
    "API-PROFILE-002",
    "API-PROFILE-003",
    "API-PROFILE-005",
    "API-FF-001",
    "API-FF-002",
    "API-VAL-001",
    "API-HEALTH-001",
    "API-HEALTH-002",
    "/api/profiles",
    "/api/profiles/stats",
    "/api/validate/release-153",
    "/api/profiles/import/firefox/policies.json",
    "/api/export/profiles/42/firefox/policies.json",
    "/health/ready",
    "expected_revision",
    "revision",
    "409",
)
MIN_LOCALIZED_TEXT_RATIO = {
    "ru": 0.75,
    "de": 0.70,
    # CJK characters carry substantially more information than Latin characters.
    "zh-CN": 0.32,
    "fr": 0.70,
    "es-ES": 0.70,
}

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "admin" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    assert TASK_DOCTYPE in source
    return ET.fromstring(source)


def _normalized_text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


def _topic_signature(root: ET.Element) -> dict[str, object]:
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


def test_devops_integration_runbooks_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id in DEVOPS_RUNBOOK_TOPICS:
            root = _topic_root(locale, topic_id)
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "administrator devops integrator security-reviewer",
                "product": "bpm-0-9-1",
                "platform": "web",
            }
            assert root.findtext("title")
            assert root.findtext("shortdesc")
            signature = _topic_signature(root)
            assert signature["steps"] == 6
            assert signature["has_prereq"]
            assert signature["has_context"]
            assert signature["has_result"]
            assert signature["has_postreq"]
            assert "warning" in signature["warning_notes"]
            assert len(signature["related"]) == 4


def test_devops_integration_runbooks_are_keyed_and_reachable_from_admin_guide() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"] in DEVOPS_RUNBOOK_KEYREFS
        }
        assert keydefs == {
            f"topic.{topic_id}": f"../admin/{topic_id}.dita"
            for topic_id in DEVOPS_RUNBOOK_TOPICS
        }

        admin_guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/administrator-guide.ditamap").read_text(encoding="utf-8")
        )
        topicrefs = [topicref.attrib["keyref"] for topicref in admin_guide.findall(".//topicref")]
        workflows_start = topicrefs.index(DEVOPS_RUNBOOK_KEYREFS[0])
        assert topicrefs[workflows_start : workflows_start + len(DEVOPS_RUNBOOK_KEYREFS)] == list(
            DEVOPS_RUNBOOK_KEYREFS
        )


def test_devops_integration_runbooks_preserve_locale_structure_and_full_peer_content() -> None:
    for topic_id in DEVOPS_RUNBOOK_TOPICS:
        english_root = _topic_root("en", topic_id)
        english_signature = _topic_signature(english_root)
        english_text = _normalized_text(english_root)

        for locale in LOCALIZED_LOCALES:
            localized_root = _topic_root(locale, topic_id)
            localized_text = _normalized_text(localized_root)

            assert _topic_signature(localized_root) == english_signature
            assert localized_text != english_text
            assert len(localized_text) >= len(english_text) * MIN_LOCALIZED_TEXT_RATIO[locale]
            assert "translation pending" not in localized_text.casefold()
            assert "compact summary" not in localized_text.casefold()


def test_devops_integration_runbooks_preserve_invariant_api_terms_in_every_locale() -> None:
    for locale in LOCALES:
        text = "\n".join(_normalized_text(_topic_root(locale, topic_id)) for topic_id in DEVOPS_RUNBOOK_TOPICS)
        assert all(term in text for term in REQUIRED_INVARIANT_TERMS)


def test_english_devops_integration_runbooks_cover_m12_08_acceptance_boundaries() -> None:
    text = "\n".join(_normalized_text(_topic_root("en", topic_id)) for topic_id in DEVOPS_RUNBOOK_TOPICS)

    for required in (
        "pull/list/read",
        "API-PROFILE-001",
        "API-PROFILE-002",
        "API-PROFILE-003",
        "API-PROFILE-005",
        "API-FF-001",
        "API-FF-002",
        "API-VAL-001",
        "API-HEALTH-001",
        "API-HEALTH-002",
        "expected_revision",
        "validate-before-apply",
        "import-review-export",
        "compliance metadata handoff",
        "health-gated startup",
        "audit evidence",
        "data ownership",
        "Do not retry the same PATCH blindly",
        "stale revision",
        "failure recovery",
        "$BPM_BASE_URL",
        "/api/profiles",
        "/api/profiles/stats",
        "/api/validate/release-153",
        "/api/profiles/import/firefox/policies.json",
        "/api/export/profiles/42/firefox/policies.json",
        "/health/ready",
        "BPM does not expose cursor pagination",
        "BPM does not provide ETags",
        "BPM does not provide distributed tracing",
        "external product",
        "operator-approved",
    ):
        assert required.casefold() in text.casefold()

    for forbidden in (
        "OAuth is available",
        "API token authentication is available",
        "guaranteed retry",
        "transactional rollback",
        "BPM guarantees backward compatibility",
        "webhook delivery is supported",
    ):
        assert forbidden.casefold() not in text.casefold()


def test_devops_pull_validate_update_export_workflow_executes_against_api_test_app() -> None:
    suffix = uuid4().hex[:8]
    source_flags = {"DisableTelemetry": False}
    desired_flags = {"DisableTelemetry": True, "BlockAboutConfig": True}
    profile_payload = {
        "name": f"Docs DevOps M12-08 {suffix}",
        "description": "M12-08 integration runbook source",
        "schema_version": "release-153",
        "flags": source_flags,
        "compliance": {"source": "inventory-pull"},
    }

    with make_test_client() as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready", "ready": True}

        created_response = client.post("/api/profiles", json=profile_payload)
        assert created_response.status_code == 201, created_response.text
        created = created_response.json()

        list_response = client.get(f"/api/profiles?q={suffix}&lifecycle=active&limit=50&offset=0")
        assert list_response.status_code == 200, list_response.text
        assert [profile["id"] for profile in list_response.json()] == [created["id"]]

        stats_response = client.get(f"/api/profiles/stats?q={suffix}&lifecycle=active")
        assert stats_response.status_code == 200, stats_response.text
        assert stats_response.json()["total"] == 1

        read_response = client.get(f"/api/profiles/{created['id']}")
        assert read_response.status_code == 200, read_response.text
        read_profile = read_response.json()
        assert read_profile["revision"] == created["revision"]

        validation_response = client.post(
            "/api/validate/release-153",
            json={"document": {"policies": desired_flags}},
        )
        assert validation_response.status_code == 200, validation_response.text
        assert validation_response.json()["ok"] is True

        update_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "flags": desired_flags,
                "expected_revision": read_profile["revision"],
                "compliance": {
                    "source": "control-product",
                    "ticket": "SEC-42",
                    "decision": "approved",
                },
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["revision"] == read_profile["revision"] + 1
        assert updated["flags"] == desired_flags

        stale_update_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "description": "blind replay must stop",
                "expected_revision": read_profile["revision"],
            },
        )
        assert stale_update_response.status_code == 409

        export_response = client.get(
            f"/api/export/profiles/{created['id']}/firefox/policies.json?pretty=1"
        )
        assert export_response.status_code == 200, export_response.text
        exported = export_response.json()
        assert exported == {"policies": desired_flags}
