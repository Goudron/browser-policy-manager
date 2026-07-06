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
EXPECTED_WSL_TOPICS = (
    "admin-task-prepare-windows-wsl-source-deployment",
    "admin-task-set-up-windows-wsl-source-checkout",
    "admin-task-configure-windows-wsl-network-runtime",
    "admin-task-verify-windows-wsl-source-deployment",
)
EXPECTED_WSL_KEYREFS = [f"topic.{topic_id}" for topic_id in EXPECTED_WSL_TOPICS]
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
    "zh-CN": 0.38,
    "fr": 0.72,
    "es-ES": 0.72,
}
REQUIRED_WSL_TOKENS = (
    "Windows 10",
    "Windows 11",
    "WSL 2",
    "Ubuntu LTS",
    "wsl --status",
    "wsl --list --verbose",
    "wsl --install",
    "wsl --install -d Ubuntu",
    "/home/&lt;linux-user&gt;/browser-policy-manager",
    "/mnt/c",
    "sudo apt-get update",
    "sudo apt-get install -y git make curl python3 python3-venv python3-pip",
    "python3 --version",
    "python -m venv .venv",
    "python3 -m venv .venv",
    "source .venv/bin/activate",
    "pip install -e \".[dev]\"",
    "BPM_DATABASE_URL",
    "sqlite+aiosqlite:///./data/bpm.db",
    "alembic upgrade head",
    "BPM_HOST",
    "0.0.0.0",
    "BPM_PORT",
    "BPM_RELOAD",
    "make dev",
    "uvicorn app.main:app --reload --port 8000",
    "hostname -I",
    "http://localhost:8000/profiles",
    "http://&lt;wsl-ip&gt;:8000/profiles",
    "curl -fsS http://127.0.0.1:8000/health",
    "curl -fsS http://127.0.0.1:8000/health/ready",
    "Invoke-WebRequest http://localhost:8000/health",
    "Invoke-WebRequest http://localhost:8000/health/ready",
    "make test-fast",
)
REQUIRED_BOUNDARY_TERMS = (
    "native Windows",
    "MSI",
    "EXE",
    "Windows service",
    "Event Viewer",
    "Windows firewall",
    "reverse proxy",
    "TLS",
    "HA",
    "managed secrets",
    "backup automation",
    "production hardening",
)
FORBIDDEN_SUPPORTED_CLAIMS = (
    "native Windows service is supported",
    "MSI installer is provided",
    "EXE installer is provided",
    "IIS hosting is supported",
    "Windows service behavior is certified",
    "production-ready",
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
def test_administrator_guide_maps_include_windows_wsl_runbook_topics(locale: str) -> None:
    maps = DITA_ROOT / locale / "maps"
    admin_map = ET.parse(maps / "administrator-guide.ditamap").getroot()
    topicrefs = [topicref.attrib for topicref in admin_map.findall("topicref")]
    assert topicrefs[4 : 4 + len(EXPECTED_WSL_KEYREFS)] == [
        {"keyref": keyref} for keyref in EXPECTED_WSL_KEYREFS
    ]

    keydefs = {
        keydef.attrib["keys"]: keydef.attrib.get("href")
        for keydef in ET.parse(maps / "keys.ditamap").getroot().findall("keydef")
    }
    assert {
        key: f"../admin/{key.removeprefix('topic.')}.dita"
        for key in EXPECTED_WSL_KEYREFS
    }.items() <= keydefs.items()


@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_WSL_TOPICS)
def test_windows_wsl_runbook_topics_are_full_localized_dita_tasks(locale: str, topic_id: str) -> None:
    source = _source(locale, topic_id)
    assert '<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">' in source

    root = _root(locale, topic_id)
    assert root.tag == "task"
    assert root.attrib == {
        "id": topic_id,
        XML_LANG: locale,
        "audience": "administrator devops",
        "product": "bpm-0-9-0",
        "platform": "windows linux",
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
    assert "WSL" in source
    assert not any(marker in source for marker in COMPACT_OR_FALLBACK_MARKERS)


def test_english_windows_wsl_runbook_covers_wsl_commands_paths_networking_and_boundaries() -> None:
    combined = "\n".join(_source("en", topic_id) for topic_id in EXPECTED_WSL_TOPICS)

    for token in REQUIRED_WSL_TOKENS:
        assert token in combined
    for term in REQUIRED_BOUNDARY_TERMS:
        assert re.search(re.escape(term), combined, re.IGNORECASE), term
    assert not any(claim in combined for claim in FORBIDDEN_SUPPORTED_CLAIMS)

    assert "inside WSL" in combined
    assert "not a native Windows installation" in combined
    assert "localhost forwarding" in combined
    assert "avoid" in combined.casefold() and "/mnt/c" in combined


@pytest.mark.parametrize("locale", LOCALIZED_LOCALES)
@pytest.mark.parametrize("topic_id", EXPECTED_WSL_TOPICS)
def test_localized_windows_wsl_runbook_topics_preserve_parity_and_invariant_tokens(
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

    for token in ("WSL", "Windows"):
        assert token in localized
    if topic_id == "admin-task-prepare-windows-wsl-source-deployment":
        for token in ("wsl --status", "wsl --list --verbose", "wsl --install", "/mnt/c"):
            assert token in localized
    if topic_id == "admin-task-set-up-windows-wsl-source-checkout":
        for token in (
            "sudo apt-get update",
            "python -m venv .venv",
            "pip install -e \".[dev]\"",
            "BPM_DATABASE_URL",
            "/mnt/c",
        ):
            assert token in localized
    if topic_id == "admin-task-configure-windows-wsl-network-runtime":
        for token in (
            "BPM_HOST",
            "BPM_DATABASE_URL",
            "0.0.0.0",
            "hostname -I",
            "http://localhost:8000/profiles",
        ):
            assert token in localized
    if topic_id == "admin-task-verify-windows-wsl-source-deployment":
        for token in (
            "curl -fsS http://127.0.0.1:8000/health",
            "Invoke-WebRequest http://localhost:8000/health",
            "make test-fast",
        ):
            assert token in localized
