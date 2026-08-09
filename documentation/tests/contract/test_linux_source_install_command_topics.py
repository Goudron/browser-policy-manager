from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "documentation"
DITA = DOCS / "src/dita"
CONTRACT = DOCS / "config/linux-source-install-command-contract-0.9.1.json"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
COMMON = (
    "<approved-0.9.1-ref>",
    "git clone",
    "git checkout --detach",
    "-m venv .venv",
    'pip install -e ".[dev]"',
    "alembic upgrade head",
    "make dev",
    "/health",
    "/health/ready",
    "/profiles",
)

pytestmark = pytest.mark.docs_contract


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _path(locale: str, topic_id: str) -> Path:
    return DITA / locale / "admin" / f"{topic_id}.dita"


def _resolved_commands(locale: str, topic_id: str) -> list[str]:
    path = _path(locale, topic_id)
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    commands = []
    for node in root.findall(".//codeblock"):
        if "conref" not in node.attrib:
            commands.append("".join(node.itertext()))
            continue
        relative, fragment = node.attrib["conref"].split("#", 1)
        owner = ET.fromstring((path.parent / relative).resolve().read_text(encoding="utf-8"))
        resolved = owner.find(f".//*[@id='{fragment.split('/')[-1]}']")
        assert resolved is not None
        commands.append("".join(resolved.itertext()))
    return commands


def _normalized_command_lines(locale: str, topic_id: str) -> list[str]:
    return [
        line
        for block in _resolved_commands(locale, topic_id)
        for line in block.splitlines()
        if line.strip()
    ]


def test_command_contract_freezes_five_authored_targets_with_validation_handoff() -> None:
    contract = _contract()
    assert contract["backlog_item"] == "BPM091-M6-05"
    assert contract["status"] == "authored-validation-attempted"
    assert contract["locales"] == list(LOCALES)
    assert len(contract["targets"]) == 5
    assert contract["validation_owner"] == "BPM091-M6-06"
    assert (
        contract["validation_report"]
        == "docs/architecture/linux-source-install-validation-0.9.1.json"
    )
    assert (
        contract["python_source"]["sha256"]
        == "143b1dddefaec3bd2e21e3b839b34a2b7fb9842272883c576420d605e9f30c63"
    )


@pytest.mark.parametrize("target", _contract()["targets"], ids=lambda item: item["id"])
def test_english_target_has_exact_end_to_end_commands(target: dict) -> None:
    source = _path("en", target["topic_id"]).read_text(encoding="utf-8")
    root = ET.fromstring(source)
    assert root.attrib["product"] == "bpm-0-9-1"
    assert root.find("./taskbody/prereq") is not None
    assert root.find("./taskbody/result") is not None
    assert root.find("./taskbody/postreq") is not None
    for token in COMMON:
        assert token in source, (target["id"], token)
    text = " ".join(root.itertext()).casefold()
    assert "stop" in text or "failure" in text
    assert "alembic downgrade" in source


def test_distribution_specific_python_and_package_paths_are_explicit() -> None:
    sources = {
        item["id"]: _path("en", item["topic_id"]).read_text(encoding="utf-8")
        for item in _contract()["targets"]
    }
    assert "python3.14-venv" in sources["ubuntu-26-04"]
    assert "sudo dnf install" in sources["fedora-44"]
    assert "sudo pacman -Syu" in sources["manjaro-stable-2026-06-26"]
    assert "pacman-mirrors -G" in sources["manjaro-stable-2026-06-26"]
    for target_id in ("debian-13-5", "linux-mint-22-3"):
        assert _contract()["python_source"]["sha256"] in sources[target_id]
        assert "make altinstall" in sources[target_id]


@pytest.mark.parametrize("locale", LOCALES[1:])
def test_localized_peers_resolve_invariant_command_blocks(locale: str) -> None:
    for target in _contract()["targets"]:
        path = _path(locale, target["topic_id"])
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        assert (
            root.attrib["xml:lang"] == locale
            if "xml:lang" in root.attrib
            else root.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == locale
        )
        assert root.attrib["product"] == "bpm-0-9-1"
        assert root.findtext("title", "").strip()
        assert root.find("./taskbody/result") is not None
        if locale != "ru":
            conrefs = [node.attrib["conref"] for node in root.findall(".//codeblock[@conref]")]
            assert len(conrefs) >= 5
            for conref in conrefs:
                rel, fragment = conref.split("#", 1)
                owner = (path.parent / rel).resolve()
                assert owner.is_file()
                owner_root = ET.fromstring(owner.read_text(encoding="utf-8"))
                assert owner_root.find(f".//*[@id='{fragment.split('/')[-1]}']") is not None


@pytest.mark.parametrize("target", _contract()["targets"], ids=lambda item: item["id"])
def test_all_six_locale_peers_preserve_exact_command_parity(target: dict) -> None:
    expected = _normalized_command_lines("en", target["topic_id"])

    assert len(expected) >= 5
    for locale in LOCALES[1:]:
        assert _normalized_command_lines(locale, target["topic_id"]) == expected, (
            locale,
            target["id"],
        )


def test_every_locale_records_clean_container_result_and_native_host_boundary() -> None:
    boundary_tokens = {
        "en": ("userspace container", "native boot"),
        "ru": ("контейнере пользовательского пространства", "нативную загрузку"),
        "de": ("Userspace-Container", "nativer Systemstart"),
        "zh-CN": ("用户空间容器", "原生启动"),
        "fr": ("conteneur d’espace utilisateur", "démarrage natif"),
        "es-ES": ("contenedor limpio de espacio de usuario", "arranque nativo"),
    }
    for locale in LOCALES:
        for target in _contract()["targets"]:
            root = ET.fromstring(_path(locale, target["topic_id"]).read_text(encoding="utf-8"))
            postreq = " ".join(root.find("./taskbody/postreq").itertext())
            assert all(token in postreq for token in boundary_tokens[locale]), (
                locale,
                target["id"],
            )


@pytest.mark.parametrize("target_id", ("debian-13-5", "linux-mint-22-3"))
def test_cpython_source_targets_record_reviewed_optional_module_result(target_id: str) -> None:
    topic_id = next(
        target["topic_id"] for target in _contract()["targets"] if target["id"] == target_id
    )
    for locale in LOCALES:
        root = ET.fromstring(_path(locale, topic_id).read_text(encoding="utf-8"))
        postreq = " ".join(root.find("./taskbody/postreq").itertext())
        assert "_dbm" in postreq
        assert "_zstd" in postreq
