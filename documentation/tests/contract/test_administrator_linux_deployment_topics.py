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
EXPECTED_ADMIN_TOPICS = (
    "admin-task-prepare-linux-source-deployment",
    "admin-task-set-up-linux-source-checkout",
    "admin-task-configure-linux-source-runtime",
    "admin-task-verify-linux-source-deployment",
)
EXPECTED_ADMIN_KEYREFS = [f"topic.{topic_id}" for topic_id in EXPECTED_ADMIN_TOPICS]
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
REQUIRED_SOURCE_TOKENS = (
    "Python 3.14+",
    "source .venv/bin/activate",
    "pip install -e \".[dev]\"",
    "alembic upgrade head",
    "make dev",
    "uvicorn app.main:app --reload --port 8000",
    "BPM_DATABASE_URL",
    "sqlite+aiosqlite:///./data/bpm.db",
    "data/bpm.db",
    "BPM_HOST",
    "BPM_PORT",
    "BPM_RELOAD",
    "BPM_ENABLE_CORS",
    "BPM_CORS_ALLOW_ORIGINS",
    "BPM_DOCUMENTATION_SITE_DIR",
    "curl -fsS http://127.0.0.1:8000/health",
    "curl -fsS http://127.0.0.1:8000/health/ready",
    "http://127.0.0.1:8000/profiles",
)
REQUIRED_BOUNDARY_TERMS = (
    "source-based Linux deployment",
    "organization-owned procedures",
    "services",
    "reverse proxy",
    "TLS",
    "secrets",
    "backups",
    "production hardening",
)
FORBIDDEN_SUPPORTED_CLAIMS = (
    "production-ready",
    "supported systemd unit is provided",
    "official reverse proxy recipe is provided",
    "HA topology is supported",
    "managed backup service is included",
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
def test_administrator_guide_maps_include_linux_source_runbook_topics(locale: str) -> None:
    maps = DITA_ROOT / locale / "maps"
    admin_map = ET.parse(maps / "administrator-guide.ditamap").getroot()
    topicrefs = [topicref.attrib for topicref in admin_map.findall(".//topicref")]
    linux_topics_start = 3
    assert topicrefs[linux_topics_start : linux_topics_start + len(EXPECTED_ADMIN_KEYREFS)] == [
        {"keyref": keyref} for keyref in EXPECTED_ADMIN_KEYREFS
    ]

    keydefs = {
        keydef.attrib["keys"]: keydef.attrib.get("href")
        for keydef in ET.parse(maps / "keys.ditamap").getroot().findall("keydef")
    }
    assert {
        key: f"../admin/{key.removeprefix('topic.')}.dita"
        for key in EXPECTED_ADMIN_KEYREFS
    }.items() <= keydefs.items()


@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_ADMIN_TOPICS)
def test_linux_source_runbook_topics_are_full_localized_dita_tasks(locale: str, topic_id: str) -> None:
    source = _source(locale, topic_id)
    assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source

    root = _root(locale, topic_id)
    assert root.tag == "task"
    assert root.attrib == {
        "id": topic_id,
        XML_LANG: locale,
        "audience": "administrator devops",
        "product": "bpm-0-9-1",
        "platform": "linux",
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


def test_english_linux_source_runbook_matches_current_repository_commands_and_settings() -> None:
    combined = "\n".join(_source("en", topic_id) for topic_id in EXPECTED_ADMIN_TOPICS)

    for token in REQUIRED_SOURCE_TOKENS:
        assert token in combined
    for term in REQUIRED_BOUNDARY_TERMS:
        assert re.search(re.escape(term), combined, re.IGNORECASE), term
    assert not any(claim in combined for claim in FORBIDDEN_SUPPORTED_CLAIMS)

    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    config = (REPOSITORY_ROOT / "app/core/config.py").read_text(encoding="utf-8")
    health = (REPOSITORY_ROOT / "app/api/health.py").read_text(encoding="utf-8")

    for token in (
        "3.14+",
        "python -m venv .venv",
        "source .venv/bin/activate",
        "pip install .",
        "make dev",
    ):
        assert token in readme
    assert "make dev" in combined
    assert "alembic upgrade head" in combined
    assert "uvicorn app.main:app --reload --port 8000" in makefile
    for token in (
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/bpm.db",
        "HOST",
        "PORT",
        "RELOAD",
        "ENABLE_CORS",
        "CORS_ALLOW_ORIGINS",
        "DOCUMENTATION_SITE_DIR",
    ):
        assert token in config
    assert '@router.get("/health"' in health
    assert '@router.get("/health/ready"' in health


@pytest.mark.parametrize("locale", LOCALIZED_LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_ADMIN_TOPICS)
def test_localized_linux_source_runbook_topics_preserve_parity_and_invariant_tokens(
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

    invariant_tokens = (
        ".venv",
        "BPM_DATABASE_URL",
        "sqlite+aiosqlite:///./data/bpm.db",
        "BPM_DOCUMENTATION_SITE_DIR",
        "/health",
        "/health/ready",
        "http://127.0.0.1:8000/profiles",
        "make dev",
    )
    assert any(token in localized for token in invariant_tokens)
    if topic_id == "admin-task-set-up-linux-source-checkout":
        for token in ("python -m venv .venv", "pip install -e \".[dev]\"", "alembic upgrade head"):
            assert token in localized
    if topic_id == "admin-task-verify-linux-source-deployment":
        for token in (
            "curl -fsS http://127.0.0.1:8000/health",
            "curl -fsS http://127.0.0.1:8000/health/ready",
        ):
            assert token in localized
