from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
EXPECTED_API_TOPICS = {
    "admin-concept-api-conventions.dita",
    "admin-concept-api-limitations.dita",
    "admin-concept-integration-audience.dita",
    "admin-concept-supported-integration-patterns.dita",
    "admin-task-check-health-readiness.dita",
    "admin-task-export-firefox-policies-json.dita",
    "admin-task-import-firefox-policies-json.dita",
    "admin-task-manage-profile-retirement.dita",
    "admin-task-run-import-review-export-scenario.dita",
    "admin-task-run-pull-compare-update-scenario.dita",
    "admin-task-sync-profile-lifecycle.dita",
    "admin-task-use-reusable-api-examples.dita",
    "admin-task-validate-firefox-policies-json.dita",
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
    # Structural parity is checked separately; this only rejects compact fallbacks.
    "zh-CN": 0.32,
    "fr": 0.75,
    "es-ES": 0.75,
}
REQUIRED_INVARIANT_TERMS = (
    "$BPM_BASE_URL",
    "BPM_BASE_URL",
    "BPM_SCHEMA_CHANNEL",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/help/",
    "/health",
    "/health/ready",
    "/api/profiles",
    "/api/profiles/stats",
    "/api/profiles/42",
    "/api/profiles/42/restore",
    "/api/profiles/42/hard",
    "/api/profiles/reset",
    "/api/profiles/import/firefox/policies.json",
    "/api/export/profiles/42/firefox/policies.json",
    "/api/validate/release-153",
    "/api/validate/beta-999",
    "GET",
    "POST",
    "PATCH",
    "DELETE",
    "application/json",
    "multipart/form-data",
    "Content-Disposition",
    "API-PROFILE-001",
    "API-PROFILE-002",
    "API-PROFILE-003",
    "API-PROFILE-004",
    "API-PROFILE-005",
    "API-PROFILE-006",
    "API-PROFILE-007",
    "API-PROFILE-008",
    "API-PROFILE-009",
    "API-FF-001",
    "API-FF-002",
    "API-VAL-001",
    "API-HEALTH-001",
    "API-HEALTH-002",
    "ProfileCreate",
    "ProfileRead",
    "ProfileUpdate",
    "ValidationRequest",
    "FirefoxPoliciesJsonImportRequest",
    "policies.json",
    "DisableTelemetry",
    "BlockAboutConfig",
    "Proxy",
    "release-153",
    "beta-999",
    "expected_revision",
    "include_deleted",
    "download=1",
    "pretty=1",
    "limit=50",
    "offset=0",
    "lifecycle=active",
    "status",
    "ready",
    "ok",
    "detail",
    "message",
    "error",
    "issues",
    "curl -fsS",
    "requests.Session",
    "raise_for_status",
    "timeout=10",
    "SEC-42",
    "docs-api-example",
)

pytestmark = pytest.mark.docs_contract


def _root(locale: str, topic_name: str) -> ET.Element:
    return ET.fromstring((DITA_ROOT / locale / "admin" / topic_name).read_text(encoding="utf-8"))


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
        "codeblock": Counter((element.text or "").strip() for element in root.iter("codeblock")),
    }


def _codeph_tokens(root: ET.Element) -> Counter[str]:
    return Counter(element.text or "" for element in root.iter("codeph"))


def test_api_authored_topics_are_parallel_in_every_locale() -> None:
    assert EXPECTED_API_TOPICS <= {
        path.name for path in (DITA_ROOT / "en/admin").glob("admin-*.dita")
    }
    assert not list((DITA_ROOT / "en/api").glob("*.dita"))
    for locale in LOCALIZED_LOCALES:
        assert EXPECTED_API_TOPICS <= {
            path.name for path in (DITA_ROOT / locale / "admin").glob("admin-*.dita")
        }
        assert not list((DITA_ROOT / locale / "api").glob("*.dita"))


def test_api_localized_topics_preserve_structure_links_warnings_and_examples() -> None:
    for english_topic in sorted(EXPECTED_API_TOPICS):
        english_root = _root("en", english_topic)
        english_signature = _topic_signature(english_root)
        english_codeph = _codeph_tokens(english_root)

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic)
            assert localized_root.attrib == {
                "id": english_root.attrib["id"],
                XML_LANG: locale,
                "audience": "administrator devops integrator security-reviewer",
                "product": "bpm-0-9-1",
                "platform": "web",
            }
            assert _topic_signature(localized_root) == english_signature
            assert _codeph_tokens(localized_root) >= english_codeph


def test_api_localized_topics_are_full_peers_not_compact_fallbacks() -> None:
    for english_topic in sorted(EXPECTED_API_TOPICS):
        english_root = _root("en", english_topic)
        english_text = _normalized_text(english_root)
        english_length = len(english_text)

        for locale in LOCALIZED_LOCALES:
            localized_root = _root(locale, english_topic)
            localized_text = _normalized_text(localized_root)
            localized_title = localized_root.findtext("title")

            assert localized_text != english_text
            assert localized_title
            assert len(localized_text) >= english_length * MIN_LOCALIZED_TEXT_RATIO[locale]
            assert all(marker not in localized_text for marker in COMPACT_OR_FALLBACK_MARKERS)


def test_api_localized_topics_preserve_contract_paths_payloads_and_identifiers() -> None:
    for locale in LOCALES:
        locale_text = "\n".join(
            _normalized_text(_root(locale, topic_name))
            for topic_name in sorted(EXPECTED_API_TOPICS)
        )
        casefolded_text = locale_text.casefold()

        for required in REQUIRED_INVARIANT_TERMS:
            assert required.casefold() in casefolded_text

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
            "Authorization: Bearer",
        ):
            assert forbidden.casefold() not in casefolded_text
