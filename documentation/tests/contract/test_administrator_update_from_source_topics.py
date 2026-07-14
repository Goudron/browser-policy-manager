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
EXPECTED_UPDATE_TOPICS = (
    "admin-task-prepare-source-update-evidence",
    "admin-task-refresh-source-revision-dependencies",
    "admin-task-run-source-update-migrations-docs",
    "admin-task-verify-source-update-rollback-stop",
)
EXPECTED_UPDATE_KEYREFS = [f"topic.{topic_id}" for topic_id in EXPECTED_UPDATE_TOPICS]
UPDATE_TOPICREF_OFFSET = 17
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
REQUIRED_UPDATE_TOKENS = (
    "git status --short",
    "git rev-parse --short HEAD",
    "git fetch --tags",
    "git checkout <approved-new-ref>",
    "source .venv/bin/activate",
    "python -m pip install --upgrade pip",
    'pip install -e ".[dev]"',
    "mkdir -p backups",
    "cp data/bpm.db backups/bpm-pre-update.db",
    "sha256sum backups/bpm-pre-update.db",
    "BPM_DATABASE_URL",
    "BPM_DOCUMENTATION_SITE_DIR",
    "BPM_SCHEMA_CACHE_DIR",
    "alembic upgrade head",
    "make test-fast",
    "make docs-validate",
    "make docs-build",
    "make dev",
    "curl -fsS http://127.0.0.1:8000/health",
    "curl -fsS http://127.0.0.1:8000/health/ready",
    "http://127.0.0.1:8000/profiles",
    "/help/",
    "policies.json",
)
REQUIRED_BOUNDARY_TERMS = (
    "automatic rollback",
    "database downgrade",
    "managed backup",
    "packaged upgrade tooling",
    "alembic downgrade",
    "pre-update database backup",
    "stop",
    "escalate",
    "production readiness",
    "reverse proxy",
    "HA",
)
FORBIDDEN_SUPPORTED_CLAIMS = (
    "automatic rollback is supported",
    "database downgrade is guaranteed",
    "alembic downgrade is supported by default",
    "production-ready",
)
INVARIANT_TOKENS_BY_TOPIC = {
    "admin-task-prepare-source-update-evidence": (
        "git status --short",
        "git rev-parse --short HEAD",
        "cp data/bpm.db backups/bpm-pre-update.db",
        "sha256sum backups/bpm-pre-update.db",
        "policies.json",
    ),
    "admin-task-refresh-source-revision-dependencies": (
        "git fetch --tags",
        "git checkout <approved-new-ref>",
        "source .venv/bin/activate",
        'pip install -e ".[dev]"',
    ),
    "admin-task-run-source-update-migrations-docs": (
        "BPM_DATABASE_URL",
        "alembic upgrade head",
        "make test-fast",
        "make docs-validate",
        "make docs-build",
    ),
    "admin-task-verify-source-update-rollback-stop": (
        "make dev",
        "curl -fsS http://127.0.0.1:8000/health",
        "http://127.0.0.1:8000/profiles",
        "/help/",
    ),
}

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
def test_administrator_guide_maps_include_update_from_source_topics(locale: str) -> None:
    maps = DITA_ROOT / locale / "maps"
    admin_map = ET.parse(maps / "administrator-guide.ditamap").getroot()
    topicrefs = [topicref.attrib for topicref in admin_map.findall("topicref")]
    assert topicrefs[
        UPDATE_TOPICREF_OFFSET : UPDATE_TOPICREF_OFFSET + len(EXPECTED_UPDATE_KEYREFS)
    ] == [
        {"keyref": keyref} for keyref in EXPECTED_UPDATE_KEYREFS
    ]

    keydefs = {
        keydef.attrib["keys"]: keydef.attrib.get("href")
        for keydef in ET.parse(maps / "keys.ditamap").getroot().findall("keydef")
    }
    assert {
        key: f"../admin/{key.removeprefix('topic.')}.dita"
        for key in EXPECTED_UPDATE_KEYREFS
    }.items() <= keydefs.items()


@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_UPDATE_TOPICS)
def test_update_from_source_topics_are_full_localized_dita_tasks(locale: str, topic_id: str) -> None:
    source = _source(locale, topic_id)
    assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source

    root = _root(locale, topic_id)
    assert root.tag == "task"
    assert root.attrib == {
        "id": topic_id,
        XML_LANG: locale,
        "audience": "administrator devops",
        "product": "bpm-0-9-0",
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


def test_english_update_from_source_topics_match_current_commands_and_boundaries() -> None:
    combined = "\n".join(_source("en", topic_id) for topic_id in EXPECTED_UPDATE_TOPICS)
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

    for token in REQUIRED_UPDATE_TOKENS:
        assert token in combined
    for term in REQUIRED_BOUNDARY_TERMS:
        assert re.search(re.escape(term), combined, re.IGNORECASE), term
    assert not any(claim in combined for claim in FORBIDDEN_SUPPORTED_CLAIMS)

    for token in ('pip install -e ".[dev]"', "alembic upgrade head", "make test-fast"):
        assert token in readme
        assert token in combined
    for target in ("test-fast:", "docs-validate:", "docs-build:"):
        assert target in makefile


@pytest.mark.parametrize("locale", LOCALIZED_LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_UPDATE_TOPICS)
def test_localized_update_from_source_topics_preserve_parity_and_invariant_tokens(
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

    for token in INVARIANT_TOKENS_BY_TOPIC[topic_id]:
        assert token in localized
