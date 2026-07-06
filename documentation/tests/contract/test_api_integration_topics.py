from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4

import pytest

from tests.support import make_test_client

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
API_INVENTORY_PATH = REPOSITORY_ROOT / "docs/architecture/api-documentation-inventory-0.9.0.md"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
CONCEPT_DOCTYPE = '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">'
TASK_DOCTYPE = '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">'

TOPICS = {
    "admin-concept-integration-audience": {
        "kind": "concept",
        "sections": {
            "a-audience",
            "a-evidence-boundary",
            "a-supported-consumers",
            "a-unsupported-claims",
            "a-data-ownership",
        },
    },
    "admin-concept-supported-integration-patterns": {
        "kind": "concept",
        "sections": {
            "a-profile-synchronization",
            "a-validation-gates",
            "a-import-export",
            "a-compliance-metadata",
            "a-inventory-and-health",
            "a-unsupported-patterns",
        },
    },
    "admin-concept-api-conventions": {
        "kind": "concept",
        "sections": {
            "a-base-url",
            "a-content-types",
            "a-identifiers",
            "a-schemas",
            "a-query",
            "a-errors",
        },
    },
    "admin-concept-api-limitations": {
        "kind": "concept",
        "sections": {
            "a-security",
            "a-versioning",
            "a-concurrency",
            "a-bulk-transactions",
            "a-errors",
            "a-exclusions",
            "a-health",
        },
    },
    "admin-task-sync-profile-lifecycle": {
        "kind": "task",
        "api_ids": {
            "API-PROFILE-001",
            "API-PROFILE-002",
            "API-PROFILE-003",
            "API-PROFILE-004",
            "API-PROFILE-005",
        },
    },
    "admin-task-manage-profile-retirement": {
        "kind": "task",
        "api_ids": {
            "API-PROFILE-006",
            "API-PROFILE-007",
            "API-PROFILE-008",
            "API-PROFILE-009",
        },
    },
    "admin-task-import-firefox-policies-json": {
        "kind": "task",
        "api_ids": {
            "API-FF-001",
        },
    },
    "admin-task-export-firefox-policies-json": {
        "kind": "task",
        "api_ids": {
            "API-FF-002",
        },
    },
    "admin-task-validate-firefox-policies-json": {
        "kind": "task",
        "api_ids": {
            "API-VAL-001",
        },
    },
    "admin-task-check-health-readiness": {
        "kind": "task",
        "api_ids": {
            "API-HEALTH-001",
            "API-HEALTH-002",
        },
    },
    "admin-task-run-pull-compare-update-scenario": {
        "kind": "task",
        "api_ids": {
            "API-PROFILE-001",
            "API-PROFILE-003",
            "API-PROFILE-005",
            "API-VAL-001",
        },
    },
    "admin-task-run-import-review-export-scenario": {
        "kind": "task",
        "api_ids": {
            "API-HEALTH-001",
            "API-HEALTH-002",
            "API-FF-001",
            "API-PROFILE-003",
            "API-VAL-001",
            "API-FF-002",
        },
    },
    "admin-task-use-reusable-api-examples": {
        "kind": "task",
        "api_ids": {
            "API-HEALTH-001",
            "API-HEALTH-002",
            "API-PROFILE-001",
            "API-PROFILE-003",
            "API-PROFILE-004",
            "API-PROFILE-005",
            "API-FF-001",
            "API-VAL-001",
            "API-FF-002",
        },
    },
}
ADMIN_API_KEYREFS = [f"topic.{topic_id}" for topic_id in TOPICS]
POST_API_KEYREF_COUNT = 15

pytestmark = pytest.mark.docs_contract


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    path = DITA_ROOT / locale / "admin" / f"{topic_id}.dita"
    source = path.read_text(encoding="utf-8")
    if topic_id.startswith("admin-task-"):
        assert TASK_DOCTYPE in source
    else:
        assert CONCEPT_DOCTYPE in source
    return ET.fromstring(source)


def test_api_integration_topics_exist_in_every_locale_with_stable_metadata() -> None:
    for locale in LOCALES:
        for topic_id, topic_contract in TOPICS.items():
            root = _topic_root(locale, topic_id)

            assert root.tag == topic_contract["kind"]
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "administrator devops integrator security-reviewer",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert root.find("title") is not None
            assert root.find("shortdesc") is not None
            assert len(root.findall("./related-links/link")) >= 4
            if topic_contract["kind"] == "concept":
                section_ids = {section.attrib["id"] for section in root.findall("./conbody/section")}
                assert section_ids == topic_contract["sections"]
                assert all("".join(section.itertext()).strip() for section in root.findall("./conbody/section"))
            else:
                taskbody = root.find("taskbody")
                assert taskbody is not None
                assert taskbody.find("prereq") is not None
                assert taskbody.find("context") is not None
                assert taskbody.find("result") is not None
                assert taskbody.find("postreq") is not None
                assert len(taskbody.findall("./steps/step")) == 6
                text = "".join(root.itertext())
                assert all(api_id in text for api_id in topic_contract["api_ids"])
                assert "Request example:" in text
                assert "Response example:" in text
                assert "Error example" in text or "Error examples" in text
                assert any(note.attrib.get("type") == "warning" for note in taskbody.findall(".//note"))


def test_api_integration_topics_are_keyed_and_reachable_from_administrator_guide_maps() -> None:
    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"] in ADMIN_API_KEYREFS
        }
        assert keydefs == {
            f"topic.{topic_id}": f"../admin/{topic_id}.dita"
            for topic_id in TOPICS
        }

        admin_guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/administrator-guide.ditamap").read_text(encoding="utf-8")
        )
        topicrefs = [topicref.attrib["keyref"] for topicref in admin_guide.findall("topicref")]
        api_block_end = len(topicrefs) - POST_API_KEYREF_COUNT
        assert topicrefs[api_block_end - len(ADMIN_API_KEYREFS) : api_block_end] == ADMIN_API_KEYREFS


def test_api_integration_guide_is_thin_compatibility_landing() -> None:
    for locale in LOCALES:
        guide = ET.fromstring(
            (DITA_ROOT / locale / "maps/api-integration-guide.ditamap").read_text(encoding="utf-8")
        )
        assert [topicref.attrib["keyref"] for topicref in guide.findall("topicref")] == [
            "topic.api-concept-administrator-integration-landing"
        ]

        landing = ET.fromstring((DITA_ROOT / locale / "api/api-concept-administrator-integration-landing.dita").read_text(encoding="utf-8"))
        assert landing.attrib == {
            "id": "api-concept-administrator-integration-landing",
            XML_LANG: locale,
            "audience": "integrator security-reviewer",
            "product": "bpm-0-9-0",
            "platform": "web",
        }
        landing_links = [link.attrib["keyref"] for link in landing.findall("./related-links/link")]
        assert landing_links == ADMIN_API_KEYREFS[:10]


def test_english_api_topics_cover_audience_patterns_and_current_api_boundaries() -> None:
    inventory = " ".join(API_INVENTORY_PATH.read_text(encoding="utf-8").split())
    text = "\n".join("".join(_topic_root("en", topic_id).itertext()) for topic_id in TOPICS)

    assert "15 programmatic/service operations" in inventory
    assert "six HTML product routes" in inventory

    for required in (
        "configuration",
        "compliance",
        "orchestration",
        "inventory",
        "control product",
        "profile synchronization",
        "validation gates",
        "policy import/export",
        "compliance metadata",
        "health checks",
        "generated OpenAPI contract",
        "maintained API inventory",
        "route/model source",
        "focused API tests",
        "configuration manager",
        "compliance scanner",
        "policy review gate",
        "profile inventory collector",
        "deployment orchestrator",
        "operational monitor",
        "service, profile, Firefox import/export, validation, and health operations",
        "product-specific connector",
        "marketplace integration",
        "certified integration",
        "partnership",
        "managed agent",
        "vendor workflow",
        "HTML routes",
        "static assets",
        "generated schema UIs",
        "underscore-prefixed Python helpers",
        "opaque compliance object",
        "runtime verification outside BPM",
        "list profiles",
        "read a profile by ID",
        "create a normalized profile",
        "patch mutable profile fields",
        "archive, restore, permanently delete, or reset",
        "profile ID and revision",
        "bulk operations",
        "automatic rollback",
        "policies.json",
        "ok=false",
        "canonical Firefox JSON",
        "normalized profile model",
        "versioned schema",
        "per-dependency diagnostics",
        "authentication",
        "authorization",
        "rate limits",
        "idempotency keys",
        "request IDs",
        "webhooks",
        "bulk export",
        "cursor pagination",
        "transactional orchestration",
        "$BPM_BASE_URL",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/help/",
        "application/json",
        "multipart/form-data",
        "415",
        "Content-Disposition",
        "ProfileUpdate",
        "active, archived, and all",
        "ProfileCreate",
        "ProfileRead",
        "ValidationRequest",
        "Firefox ESR and Release",
        "limit=50",
        "maximum 200",
        "offset=0",
        "created_at",
        "updated_at",
        "schema_version",
        "asc",
        "desc",
        "200",
        "201",
        "204",
        "detail",
        "message",
        "error",
        "issues",
        "no authentication or authorization layer",
        "CORS",
        "* origins",
        "no version prefix",
        "compatibility policy",
        "deprecation header",
        "media-type version",
        "expected_revision",
        "ETags",
        "precondition headers",
        "duplicate-name recovery",
        "bulk profile CRUD endpoint",
        "multi-operation transaction contract",
        "400",
        "404",
        "409",
        "422",
        "503",
        "/i18n/{locale}.json",
        "/favicon.ico",
        "/static/*",
        "/health",
        "/health/ready",
        "database details",
        "schema health",
        "documentation portal status",
        "API-PROFILE-001",
        "API-PROFILE-002",
        "API-PROFILE-003",
        "API-PROFILE-004",
        "API-PROFILE-005",
        "API-PROFILE-006",
        "API-PROFILE-007",
        "API-PROFILE-008",
        "API-PROFILE-009",
        "GET $BPM_BASE_URL/api/profiles?q=corp",
        "GET $BPM_BASE_URL/api/profiles/stats?q=corp",
        "GET $BPM_BASE_URL/api/profiles/42?include_deleted=false",
        "POST $BPM_BASE_URL/api/profiles",
        "PATCH $BPM_BASE_URL/api/profiles/42",
        "DELETE $BPM_BASE_URL/api/profiles/42",
        "POST $BPM_BASE_URL/api/profiles/42/restore",
        "DELETE $BPM_BASE_URL/api/profiles/42/hard",
        "DELETE $BPM_BASE_URL/api/profiles/reset",
        "no bulk confirmation token",
        "no undo endpoint for permanent delete",
        "approval record",
        "external audit record",
        "Reset permanently deletes every profile",
        "API-FF-001",
        "API-FF-002",
        "POST $BPM_BASE_URL/api/profiles/import/firefox/policies.json",
        "GET $BPM_BASE_URL/api/export/profiles/42/firefox/policies.json",
        "GET $BPM_BASE_URL/api/export/profiles/42/firefox/policies.json?download=1",
        "GET $BPM_BASE_URL/api/export/profiles/42/firefox/policies.json?pretty=1",
        "GET $BPM_BASE_URL/api/export/profiles/42/firefox/policies.json?include_deleted=true",
        "POST $BPM_BASE_URL/api/validate/release-152",
        '{"document":{"policies":{"DisableTelemetry":true,"BlockAboutConfig":true}}}',
        "FirefoxPoliciesJsonImportRequest",
        "multipart/form-data",
        "file=@policies.json",
        "OpenAPI multipart schema currently declares file",
        "document.policies",
        "profile flags",
        "BPM-only metadata",
        "compliance metadata are not exported",
        "source document hash",
        "exported document hash",
        "API-VAL-001",
        "candidate policies.json",
        "preflight gate",
        "POST $BPM_BASE_URL/api/validate/release-152",
        "POST $BPM_BASE_URL/api/validate/beta-999",
        '{"document":123}',
        '{"document":{"policies":[]}}',
        '{"document":{"policies":{"Proxy":{"Mode":"bogus"}}}}',
        "Expected object with policy mappings",
        "Firefox policies.json validation failed",
        "Unknown profile 'beta-999'",
        "A registered but unavailable schema returns 503",
        "HTTP status alone",
        "plain policy mapping",
        "structured issues",
        "candidate document hash",
        "API-HEALTH-001",
        "API-HEALTH-002",
        "GET $BPM_BASE_URL/health",
        "GET $BPM_BASE_URL/health/ready",
        '{"status":"ok"}',
        '{"status":"ready","ready":true}',
        "source-deployment Administrator Guide",
        "this API topic only documents the integration handshake",
        "does not expose dependency diagnostics",
        "no degraded-state or dependency-detail body",
        "database health details",
        "schema cache details",
        "documentation portal status",
        "does not declare a polling interval",
        "retry-after header",
        "service-level objective",
        "one small preflight signal",
        "pull/compare/update",
        "import-review-export",
        "control product owns comparison logic",
        "BPM does not expose a compare API",
        "desired-state calculation",
        "reviewer approval",
        "retry decisions",
        "changed policy keys",
        "missing keys",
        "PATCH $BPM_BASE_URL/api/profiles/42",
        "safe retry contract",
        "compliance scan result",
        "compliance handoff",
        "scanner",
        "SEC-42",
        "source hash",
        "export hash",
        "failure recovery record",
        "do not retry blindly",
        "data ownership",
        "curl -fsS",
        "BPM_BASE_URL",
        "BPM_SCHEMA_CHANNEL",
        "BPM_JSON_IMPORT_PATH",
        "docs-api-example",
        "language-neutral request patterns",
        "environment templates",
        "copyable curl commands",
        "multipart samples",
        "Python helpers",
        "response assertions",
        "requests.Session",
        "raise_for_status",
        "session.post",
        "timeout=10",
        "exported document hash",
        "Do not copy real host names",
    ):
        assert required.casefold() in text.casefold()

    for forbidden in (
        "BPM ships a connector for",
        "certified connector",
        "partner-certified",
        "guaranteed retry",
        "BPM guarantees backward compatibility",
        "OAuth is available",
        "API token authentication is available",
        "rate-limit header",
        "webhook delivery",
        "transactional rollback",
        "localhost",
        "127.0.0.1",
        "Authorization: Bearer",
    ):
        assert forbidden.casefold() not in text.casefold()


def test_firefox_import_export_documented_examples_execute_against_api_test_app() -> None:
    json_import = {
        "name": "Docs API JSON Import",
        "description": "Imported by control product",
        "schema_version": "release-152",
        "compliance": {"framework": "cis", "layer": "cis_l1"},
        "document": {
            "policies": {
                "DisableTelemetry": True,
                "BlockAboutConfig": True,
            }
        },
    }
    multipart_document = {
        "policies": {
            "DisablePrivateBrowsing": True,
        }
    }

    with make_test_client() as client:
        json_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json=json_import,
        )
        assert json_response.status_code == 201, json_response.text
        json_profile = json_response.json()
        assert json_profile["schema_version"] == "release-152"
        assert json_profile["compliance"] == {"framework": "cis", "layer": "cis_l1"}
        assert json_profile["flags"] == json_import["document"]["policies"]

        multipart_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "name": "Docs API Multipart Import",
                "description": "Uploaded policies.json",
                "schema_version": "release-152",
                "compliance": json.dumps({"framework": "cis", "layer": "cis_l2"}),
            },
            files={
                "file": (
                    "policies.json",
                    json.dumps(multipart_document),
                    "application/json",
                )
            },
        )
        assert multipart_response.status_code == 201, multipart_response.text
        assert multipart_response.json()["flags"] == multipart_document["policies"]

        export_response = client.get(
            f"/api/export/profiles/{json_profile['id']}/firefox/policies.json"
            "?download=1&pretty=1"
        )
        assert export_response.status_code == 200, export_response.text
        assert export_response.headers["content-type"].startswith("application/json")
        assert export_response.headers["content-disposition"] == (
            f'attachment; filename="profile-{json_profile["id"]}-policies.json"'
        )
        exported_document = export_response.json()
        assert exported_document == {"policies": json_import["document"]["policies"]}
        assert "compliance" not in exported_document
        assert "\n  \"policies\"" in export_response.text

        validation_response = client.post("/api/validate/release-152", json={"document": exported_document})
        assert validation_response.status_code == 200, validation_response.text
        assert validation_response.json()["ok"] is True


def test_validation_gate_documented_examples_execute_against_api_test_app() -> None:
    with make_test_client() as client:
        success_response = client.post(
            "/api/validate/release-152",
            json={
                "document": {
                    "policies": {
                        "DisableTelemetry": True,
                        "BlockAboutConfig": True,
                    }
                }
            },
        )
        assert success_response.status_code == 200, success_response.text
        assert success_response.json() == {"ok": True, "profile": "release-152"}

        ok_false_response = client.post(
            "/api/validate/release-152",
            json={"document": 123},
        )
        assert ok_false_response.status_code == 200, ok_false_response.text
        assert ok_false_response.json() == {
            "ok": False,
            "profile": "release-152",
            "detail": "Expected object with policy mappings",
            "error": "Expected object with policy mappings",
        }

        malformed_response = client.post(
            "/api/validate/release-152",
            json={"document": {"policies": []}},
        )
        assert malformed_response.status_code == 400, malformed_response.text
        malformed_detail = malformed_response.json()["detail"]
        assert malformed_detail["message"] == "Firefox policies.json validation failed"
        assert malformed_detail["issues"][0]["path"] == ["policies"]

        unknown_channel_response = client.post(
            "/api/validate/beta-999",
            json={"document": {"policies": {"DisableTelemetry": True}}},
        )
        assert unknown_channel_response.status_code == 404, unknown_channel_response.text
        assert unknown_channel_response.json()["detail"] == "Unknown profile 'beta-999'"

        policy_failure_response = client.post(
            "/api/validate/release-152",
            json={"document": {"policies": {"Proxy": {"Mode": "bogus"}}}},
        )
        assert policy_failure_response.status_code == 422, policy_failure_response.text
        policy_failure_detail = policy_failure_response.json()["detail"]
        assert policy_failure_detail["message"] == "Policy validation failed"
        assert policy_failure_detail["issues"][0]["policy"] == "Proxy"
        assert policy_failure_detail["issues"][0]["path"] == ["policies", "Proxy", "Mode"]


def test_health_handshake_documented_examples_execute_against_api_test_app() -> None:
    with make_test_client() as client:
        liveness_response = client.get("/health")
        readiness_response = client.get("/health/ready")

    assert liveness_response.status_code == 200, liveness_response.text
    assert liveness_response.json() == {"status": "ok"}

    assert readiness_response.status_code == 200, readiness_response.text
    assert readiness_response.json() == {"status": "ready", "ready": True}


def test_pull_compare_update_scenario_executes_against_api_test_app() -> None:
    suffix = uuid4().hex[:8]
    profile_payload = {
        "name": f"Docs Pull Compare {suffix}",
        "description": "Scenario source",
        "schema_version": "release-152",
        "flags": {"DisableTelemetry": False},
        "compliance": {"source": "bpm-library"},
    }
    desired_flags = {
        "DisableTelemetry": True,
        "BlockAboutConfig": True,
    }

    with make_test_client() as client:
        created_response = client.post("/api/profiles", json=profile_payload)
        assert created_response.status_code == 201, created_response.text
        created = created_response.json()

        list_response = client.get(f"/api/profiles?q={suffix}&lifecycle=active&limit=50&offset=0")
        assert list_response.status_code == 200, list_response.text
        assert [item["id"] for item in list_response.json()] == [created["id"]]

        read_response = client.get(f"/api/profiles/{created['id']}")
        assert read_response.status_code == 200, read_response.text
        read_profile = read_response.json()
        assert read_profile["revision"] == created["revision"]

        changed_keys = sorted(
            key
            for key, value in desired_flags.items()
            if read_profile["flags"].get(key) != value
        )
        assert changed_keys == ["BlockAboutConfig", "DisableTelemetry"]

        validation_response = client.post(
            "/api/validate/release-152",
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
                    "decision": "approved",
                },
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["flags"] == desired_flags
        assert updated["revision"] == read_profile["revision"] + 1
        assert updated["compliance"] == {
            "source": "control-product",
            "decision": "approved",
        }

        stale_update_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "description": "stale retry must stop",
                "expected_revision": read_profile["revision"],
            },
        )
        assert stale_update_response.status_code == 409


def test_import_review_export_compliance_scenario_executes_against_api_test_app() -> None:
    suffix = uuid4().hex[:8]
    policies = {
        "DisableTelemetry": True,
        "BlockAboutConfig": True,
    }
    compliance = {
        "scanner": "external-control",
        "result": "passed",
        "ticket": f"SEC-{suffix}",
    }

    with make_test_client() as client:
        health_response = client.get("/health")
        ready_response = client.get("/health/ready")
        assert health_response.json() == {"status": "ok"}
        assert ready_response.json() == {"status": "ready", "ready": True}

        import_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": f"Docs Reviewed Baseline {suffix}",
                "schema_version": "release-152",
                "compliance": compliance,
                "document": {"policies": policies},
            },
        )
        assert import_response.status_code == 201, import_response.text
        imported = import_response.json()
        assert imported["flags"] == policies
        assert imported["compliance"] == compliance

        read_response = client.get(f"/api/profiles/{imported['id']}")
        assert read_response.status_code == 200, read_response.text
        assert read_response.json()["revision"] == imported["revision"]

        validation_response = client.post(
            "/api/validate/release-152",
            json={"document": {"policies": policies}},
        )
        assert validation_response.status_code == 200, validation_response.text
        assert validation_response.json() == {"ok": True, "profile": "release-152"}

        export_response = client.get(
            f"/api/export/profiles/{imported['id']}/firefox/policies.json"
            "?download=1&pretty=1"
        )
        assert export_response.status_code == 200, export_response.text
        assert export_response.headers["content-disposition"] == (
            f'attachment; filename="profile-{imported["id"]}-policies.json"'
        )
        exported = export_response.json()
        assert exported == {"policies": policies}
        assert "compliance" not in exported


def test_reusable_api_examples_execute_against_api_test_app_without_environment_hosts() -> None:
    suffix = uuid4().hex[:8]
    policies = {
        "DisableTelemetry": True,
        "BlockAboutConfig": True,
    }

    topic_source = (DITA_ROOT / "en/admin/admin-task-use-reusable-api-examples.dita").read_text(
        encoding="utf-8"
    )
    for required in (
        'export BPM_BASE_URL="${BPM_BASE_URL:?set BPM_BASE_URL first}"',
        "BPM_JSON_IMPORT_PATH=./policies.json",
        'curl -fsS "$BPM_BASE_URL/health"',
        'curl -fsS "$BPM_BASE_URL/health/ready"',
        '"$BPM_BASE_URL/api/profiles"',
        '"$BPM_BASE_URL/api/profiles?q=docs-api-example&lifecycle=active&limit=50&offset=0"',
        '"$BPM_BASE_URL/api/profiles/$PROFILE_ID"',
        'PATCH',
        "expected_revision",
        '"$BPM_BASE_URL/api/validate/$BPM_SCHEMA_CHANNEL"',
        '"$BPM_BASE_URL/api/profiles/import/firefox/policies.json"',
        'multipart/form-data',
        'file=@$BPM_JSON_IMPORT_PATH;type=application/json',
        '"$BPM_BASE_URL/api/export/profiles/$PROFILE_ID/firefox/policies.json?pretty=1"',
        'base_url = os.environ["BPM_BASE_URL"].rstrip("/")',
        'schema_channel = os.environ.get("BPM_SCHEMA_CHANNEL", "release-152")',
        "requests.Session()",
        "ready.raise_for_status()",
        "validation.raise_for_status()",
        'assert validation.json() == {"ok": True, "profile": schema_channel}',
        'assert exported.json() == {"policies": payload["document"]["policies"]}',
    ):
        assert required in topic_source
    for forbidden in (
        "http://localhost",
        "https://localhost",
        "127.0.0.1",
        "example.com",
        "Authorization:",
        "Bearer ",
        "api_key",
        "password",
        "private.example",
    ):
        assert forbidden.casefold() not in topic_source.casefold()

    with make_test_client() as client:
        health_response = client.get("/health")
        ready_response = client.get("/health/ready")
        assert health_response.status_code == 200, health_response.text
        assert health_response.json() == {"status": "ok"}
        assert ready_response.status_code == 200, ready_response.text
        assert ready_response.json() == {"status": "ready", "ready": True}

        create_response = client.post(
            "/api/profiles",
            json={
                "name": f"docs-api-example-{suffix}",
                "schema_version": "release-152",
                "flags": policies,
            },
        )
        assert create_response.status_code == 201, create_response.text
        created = create_response.json()
        assert created["flags"] == policies
        assert created["schema_version"] == "release-152"

        list_response = client.get(f"/api/profiles?q={suffix}&lifecycle=active&limit=50&offset=0")
        assert list_response.status_code == 200, list_response.text
        assert [profile["id"] for profile in list_response.json()] == [created["id"]]

        read_response = client.get(f"/api/profiles/{created['id']}")
        assert read_response.status_code == 200, read_response.text
        read_profile = read_response.json()
        assert read_profile["revision"] == created["revision"]

        update_response = client.patch(
            f"/api/profiles/{created['id']}",
            json={
                "flags": policies,
                "expected_revision": read_profile["revision"],
            },
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["revision"] == read_profile["revision"] + 1

        validation_response = client.post(
            "/api/validate/release-152",
            json={"document": {"policies": policies}},
        )
        assert validation_response.status_code == 200, validation_response.text
        assert validation_response.json() == {"ok": True, "profile": "release-152"}

        json_import_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": f"docs-json-import-example-{suffix}",
                "schema_version": "release-152",
                "compliance": {"source": "docs-devops-template"},
                "document": {"policies": {"DisableTelemetry": True}},
            },
        )
        assert json_import_response.status_code == 201, json_import_response.text
        assert json_import_response.json()["compliance"] == {"source": "docs-devops-template"}

        multipart_response = client.post(
            "/api/profiles/import/firefox/policies.json",
            data={
                "name": f"docs-multipart-import-example-{suffix}",
                "schema_version": "release-152",
                "compliance": json.dumps({"source": "docs-devops-template"}),
            },
            files={
                "file": (
                    "policies.json",
                    json.dumps({"policies": {"DisablePrivateBrowsing": True}}),
                    "application/json",
                )
            },
        )
        assert multipart_response.status_code == 201, multipart_response.text
        assert multipart_response.json()["flags"] == {"DisablePrivateBrowsing": True}

        export_response = client.get(
            f"/api/export/profiles/{created['id']}/firefox/policies.json?pretty=1"
        )
        assert export_response.status_code == 200, export_response.text
        assert export_response.headers["content-type"].startswith("application/json")
        assert export_response.json() == {"policies": policies}
        assert "\n  \"policies\"" in export_response.text
