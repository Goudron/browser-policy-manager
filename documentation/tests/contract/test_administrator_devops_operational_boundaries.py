from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

DOCUMENTATION_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
LOCALIZED_LOCALES = tuple(locale for locale in LOCALES if locale != "en")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
EXPECTED_DEVOPS_TOPICS = (
    "admin-task-review-devops-configuration-sources",
    "admin-task-plan-devops-storage-logs-backups",
    "admin-task-review-devops-network-cors-security",
    "admin-task-record-devops-operational-boundaries",
)
EXPECTED_DEVOPS_KEYREFS = [f"topic.{topic_id}" for topic_id in EXPECTED_DEVOPS_TOPICS]
DEVOPS_TOPICREF_OFFSET = 13
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
    "ru": 0.72,
    "de": 0.72,
    "zh-CN": 0.30,
    "fr": 0.72,
    "es-ES": 0.72,
}
REQUIRED_CONFIGURATION_TOKENS = (
    "BPM_APP_NAME",
    "BPM_APP_VERSION",
    "BPM_DEBUG",
    "BPM_HOST",
    "BPM_PORT",
    "BPM_RELOAD",
    "BPM_API_PREFIX",
    "BPM_DEFAULT_LOCALE",
    "BPM_SUPPORTED_LOCALES",
    "BPM_I18N_DIR",
    "BPM_DOCUMENTATION_SITE_DIR",
    "BPM_DATABASE_URL",
    "BPM_DB_ECHO",
    "BPM_ENABLE_CORS",
    "BPM_CORS_ALLOW_ORIGINS",
    "BPM_SCHEMA_BASE_URL",
    "BPM_SCHEMA_CACHE_DIR",
    "BPM_SCHEMA_HTTP_TIMEOUT",
    ".env",
    "app/core/config.py",
)
REQUIRED_STORAGE_LOG_TOKENS = (
    "sqlite+aiosqlite:///./data/bpm.db",
    "data/bpm.db",
    "data/",
    "app/schemas/mozilla",
    "app/documentation/site",
    "/mnt/c",
    "foreground terminal",
    "stdout",
    "stderr",
    "Uvicorn",
    "policies.json",
    "checksum",
)
REQUIRED_NETWORK_TOKENS = (
    'BPM_HOST="0.0.0.0"',
    'BPM_PORT="8000"',
    'BPM_RELOAD="true"',
    'BPM_ENABLE_CORS="true"',
    '["*"]',
    "127.0.0.1",
    "0.0.0.0",
    "GET /health",
    "GET /health/ready",
    "BPM_CORS_ALLOW_ORIGINS",
)
REQUIRED_BOUNDARY_TERMS = (
    "authentication",
    "authorization",
    "managed secrets",
    "encryption-at-rest",
    "token rotation",
    "tenant isolation",
    "automated backup",
    "point-in-time recovery",
    "restore orchestration",
    "log rotation",
    "request ID",
    "audit log",
    "TLS",
    "reverse proxy",
    "firewall",
    "rate limiting",
    "SSO",
    "OAuth/OIDC",
    "role-based access control",
    "vulnerability scanning",
    "HA",
    "systemd",
    "Windows service",
    "production hardening",
)
FORBIDDEN_SUPPORTED_CLAIMS = (
    "authentication is supported",
    "managed secrets are supported",
    "production-ready",
    "HA is supported",
    "restore orchestration is provided",
    "Windows service is supported",
    "systemd unit is provided",
)

pytestmark = pytest.mark.docs_contract


def _topic_path(locale: str, topic_id: str) -> Path:
    return DITA_ROOT / locale / "admin" / f"{topic_id}.dita"


def _source(locale: str, topic_id: str) -> str:
    return _topic_path(locale, topic_id).read_text(encoding="utf-8")


def _root(locale: str, topic_id: str) -> ET.Element:
    return ET.fromstring(_source(locale, topic_id))


def _normalized_text(root: ET.Element) -> str:
    return " ".join("".join(root.itertext()).split())


@pytest.mark.parametrize("locale", LOCALES)
def test_administrator_guide_maps_include_devops_operational_topics(locale: str) -> None:
    maps = DITA_ROOT / locale / "maps"
    admin_map = ET.parse(maps / "administrator-guide.ditamap").getroot()
    topicrefs = [topicref.attrib for topicref in admin_map.findall("topicref")]
    assert topicrefs[
        DEVOPS_TOPICREF_OFFSET : DEVOPS_TOPICREF_OFFSET + len(EXPECTED_DEVOPS_KEYREFS)
    ] == [
        {"keyref": keyref} for keyref in EXPECTED_DEVOPS_KEYREFS
    ]

    keydefs = {
        keydef.attrib["keys"]: keydef.attrib.get("href")
        for keydef in ET.parse(maps / "keys.ditamap").getroot().findall("keydef")
    }
    assert {
        key: f"../admin/{key.removeprefix('topic.')}.dita"
        for key in EXPECTED_DEVOPS_KEYREFS
    }.items() <= keydefs.items()


@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_DEVOPS_TOPICS)
def test_devops_operational_topics_are_full_localized_dita_tasks(locale: str, topic_id: str) -> None:
    source = _source(locale, topic_id)
    assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source

    root = _root(locale, topic_id)
    assert root.tag == "task"
    assert root.attrib == {
        "id": topic_id,
        XML_LANG: locale,
        "audience": "administrator devops",
        "product": "bpm-0-9-1",
        "platform": "linux windows web",
    }
    assert root.findtext("title", "").strip()
    assert root.findtext("shortdesc", "").strip()
    taskbody = root.find("taskbody")
    assert taskbody is not None
    for element_name in ("prereq", "context", "steps", "result", "postreq"):
        assert taskbody.find(element_name) is not None, (locale, topic_id, element_name)
    steps = taskbody.find("steps")
    assert steps is not None
    assert len(steps.findall("step")) == 4
    assert all(step.find("cmd") is not None for step in steps.findall("step"))
    assert not any(marker in source for marker in COMPACT_OR_FALLBACK_MARKERS)


def test_english_devops_operational_topics_match_current_config_and_boundaries() -> None:
    combined = "\n".join(_source("en", topic_id) for topic_id in EXPECTED_DEVOPS_TOPICS)
    config = (REPOSITORY_ROOT / "app/core/config.py").read_text(encoding="utf-8")

    for token in REQUIRED_CONFIGURATION_TOKENS:
        assert token in combined
    for token in REQUIRED_STORAGE_LOG_TOKENS:
        assert token in combined
    for token in REQUIRED_NETWORK_TOKENS:
        assert token in combined
    for term in REQUIRED_BOUNDARY_TERMS:
        assert re.search(re.escape(term), combined, re.IGNORECASE), term
    assert not any(claim in combined for claim in FORBIDDEN_SUPPORTED_CLAIMS)

    for source_setting in (
        "APP_NAME",
        "APP_VERSION",
        "DEBUG",
        "HOST",
        "PORT",
        "RELOAD",
        "DATABASE_URL",
        "DB_ECHO",
        "DEFAULT_LOCALE",
        "SUPPORTED_LOCALES",
        "I18N_DIR",
        "API_PREFIX",
        "ENABLE_CORS",
        "CORS_ALLOW_ORIGINS",
        "SCHEMA_BASE_URL",
        "SCHEMA_CACHE_DIR",
        "SCHEMA_HTTP_TIMEOUT",
        "DOCUMENTATION_SITE_DIR",
    ):
        assert source_setting in config


@pytest.mark.parametrize("locale", LOCALIZED_LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_DEVOPS_TOPICS)
def test_localized_devops_operational_topics_preserve_parity_and_invariant_tokens(
    locale: str, topic_id: str
) -> None:
    localized = _source(locale, topic_id)
    english = _source("en", topic_id)
    localized_text = _normalized_text(_root(locale, topic_id))
    english_text = _normalized_text(_root("en", topic_id))

    assert len(localized_text) >= int(len(english_text) * MIN_LOCALIZED_TEXT_RATIO[locale])
    assert localized != english
    assert localized.count("<step>") == english.count("<step>") == 4
    assert localized.count("<related-links>") == english.count("<related-links>")

    if topic_id == "admin-task-review-devops-configuration-sources":
        for token in ("BPM_DATABASE_URL", "BPM_CORS_ALLOW_ORIGINS", "BPM_DOCUMENTATION_SITE_DIR", ".env"):
            assert token in localized
    if topic_id == "admin-task-plan-devops-storage-logs-backups":
        for token in ("data/bpm.db", "app/schemas/mozilla", "stdout", "stderr", "policies.json"):
            assert token in localized
    if topic_id == "admin-task-review-devops-network-cors-security":
        for token in ("BPM_HOST", "0.0.0.0", "127.0.0.1", "GET /health", "BPM_CORS_ALLOW_ORIGINS"):
            assert token in localized
    if topic_id == "admin-task-record-devops-operational-boundaries":
        for token in ("make dev", "uvicorn app.main:app --reload --port 8000", "/health", "/health/ready"):
            assert token in localized
