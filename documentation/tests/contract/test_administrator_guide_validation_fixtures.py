from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tests.support import make_test_client

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
FIXTURE = DOCUMENTATION_ROOT / "fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json"
SUITE_BOUNDARIES = DOCUMENTATION_ROOT / "tests/suite-boundaries-0.9.0.json"
MAKEFILE = REPOSITORY_ROOT / "Makefile"
README = REPOSITORY_ROOT / "README.md"
CONFIG = REPOSITORY_ROOT / "app/core/config.py"
ADMIN_GUIDE = "administrator-guide.ditamap"
KEYS = "keys.ditamap"
README_READER_ENTRYPOINTS = ("/profiles", "/help/", "/docs")
README_MAINTAINER_COMMANDS = ("python -m venv .venv", "pip install .", "make dev")

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture() -> dict[str, object]:
    return _json(FIXTURE)


def _source(locale: str, topic_id: str) -> str:
    return (DITA_ROOT / locale / "admin" / f"{topic_id}.dita").read_text(encoding="utf-8")


def _map_keyrefs(locale: str, map_name: str) -> list[str]:
    root = ET.parse(DITA_ROOT / locale / "maps" / map_name).getroot()
    return [topicref.attrib["keyref"] for topicref in root.findall(".//topicref")]


def _keydefs(locale: str) -> dict[str, str | None]:
    root = ET.parse(DITA_ROOT / locale / "maps" / KEYS).getroot()
    return {keydef.attrib["keys"]: keydef.attrib.get("href") for keydef in root.findall("keydef")}


def _all_admin_sources(locale: str) -> dict[str, str]:
    fixture = _fixture()
    topics = [topic_id for group in fixture["admin_topic_groups"].values() for topic_id in group]
    return {topic_id: _source(locale, topic_id) for topic_id in topics}


def test_administrator_validation_fixture_is_compact_and_registered() -> None:
    fixture = _fixture()
    boundaries = _json(SUITE_BOUNDARIES)
    domain = boundaries["domains"]["administrator_guide_validation"]

    assert fixture["schema_version"] == 1
    assert fixture["backlog_item"] == "BPM090-M12-12"
    assert fixture["target_bpm_version"] == "0.9.0"
    assert fixture["fixture_kind"] == "administrator-guide-validation"
    assert fixture["synthetic"] is True
    assert fixture["locales"] == ["en", "ru", "de", "zh-CN", "fr", "es-ES"]
    assert FIXTURE.stat().st_size <= 16384
    assert (
        "documentation/tests/contract/test_administrator_guide_validation_fixtures.py"
        in domain["path_globs"]
    )
    assert (
        "documentation/fixtures/admin-guide-validation/admin-guide-validation-0.9.0.json"
        in domain["fixtures"]
    )
    assert domain["focused_rerun"] == (
        "./.venv/bin/pytest -q -m docs_contract "
        "documentation/tests/contract/test_administrator_guide_validation_fixtures.py"
    )


def test_fixture_topic_groups_match_administrator_guide_maps_keys_and_locale_peers() -> None:
    fixture = _fixture()
    expected_keyrefs = [
        f"topic.{topic_id}"
        for group in fixture["admin_topic_groups"].values()
        for topic_id in group
    ]

    for locale in fixture["locales"]:
        admin_keyrefs = _map_keyrefs(locale, ADMIN_GUIDE)
        keydefs = _keydefs(locale)
        assert admin_keyrefs == expected_keyrefs
        assert set(expected_keyrefs) <= set(keydefs)
        for keyref in expected_keyrefs:
            topic_id = keyref.removeprefix("topic.")
            assert keydefs[keyref] == f"../admin/{topic_id}.dita"
            source = _source(locale, topic_id)
            assert f'id="{topic_id}"' in source
            assert f'xml:lang="{locale}"' in source

        assert not (DITA_ROOT / locale / "maps/api-integration-guide.ditamap").exists()


def test_fixture_commands_config_names_paths_and_health_endpoints_stay_current() -> None:
    fixture = _fixture()
    english_text = "\n".join(_all_admin_sources("en").values())
    makefile = MAKEFILE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")

    for target in fixture["required_make_targets"]:
        assert f"{target}:" in makefile
    for command in fixture["required_commands"]:
        assert command in english_text
        if command.startswith("make "):
            assert f"{command.removeprefix('make ')}:" in makefile
    for entrypoint in README_READER_ENTRYPOINTS:
        assert entrypoint in readme
    for command in README_MAINTAINER_COMMANDS:
        assert command not in readme
    assert "make dev" in english_text
    assert "alembic upgrade head" in english_text
    for config_name in fixture["required_config_names"]:
        assert re.search(rf"\b{re.escape(config_name)}\b", config), config_name
    for env_var in fixture["required_env_vars"]:
        assert env_var in english_text
    for path in fixture["required_paths"]:
        assert path in english_text

    with make_test_client() as client:
        for endpoint in fixture["required_health_endpoints"]:
            response = client.get(endpoint)
            assert response.status_code == 200
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready", "ready": True}


def test_fixture_api_examples_and_migrated_topics_execute_representative_paths() -> None:
    fixture = _fixture()
    english_text = "\n".join(_all_admin_sources("en").values())

    for api_example in fixture["required_api_examples"]:
        assert api_example in english_text
    for api_id in fixture["required_api_ids"]:
        assert api_id in english_text

    with make_test_client() as client:
        validation = client.post(
            "/api/validate/release-153",
            json={"document": {"policies": {"DisableTelemetry": True}}},
        )
        assert validation.status_code == 200
        assert validation.json() == {"ok": True, "profile": "release-153"}

        created = client.post(
            "/api/profiles/import/firefox/policies.json",
            json={
                "name": "docs-admin-validation-fixture",
                "schema_version": "release-153",
                "document": {"policies": {"DisableTelemetry": True}},
            },
        )
        assert created.status_code == 201, created.text
        profile_id = created.json()["id"]

        exported = client.get(f"/api/export/profiles/{profile_id}/firefox/policies.json")
        assert exported.status_code == 200
        assert exported.json()["policies"] == {"DisableTelemetry": True}


def test_fixture_wsl_caveats_and_deferred_warnings_are_preserved_without_supported_claims() -> None:
    fixture = _fixture()
    forbidden = [claim.casefold() for claim in fixture["forbidden_supported_claims"]]

    for locale in fixture["locales"]:
        localized_text = "\n".join(_all_admin_sources(locale).values())
        localized_casefolded = localized_text.casefold()
        for caveat in ("Windows 10", "Windows 11", "WSL 2", "Ubuntu LTS", "/mnt/c"):
            assert caveat in localized_text
        if locale == "en":
            for caveat in fixture["required_wsl_caveats"]:
                assert caveat in localized_text
            for caveat in fixture["required_english_wsl_caveats"]:
                assert caveat in localized_text
            for warning in fixture["required_deferred_warnings"]:
                assert warning in localized_text
        else:
            for technical_boundary in ("TLS", "HA", "MSI", "EXE", "IIS"):
                assert technical_boundary in localized_text
        for claim in forbidden:
            assert claim not in localized_casefolded
