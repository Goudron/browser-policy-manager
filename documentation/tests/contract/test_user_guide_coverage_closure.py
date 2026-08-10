from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
DITA_ROOT = DOCUMENTATION_ROOT / "src/dita"
CASE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
CLOSURE = DOCUMENTATION_ROOT / "config/user-guide-coverage-closure-0.9.0.json"
CAPABILITY_INVENTORY = (
    REPOSITORY_ROOT / "docs/architecture/product-user-capability-inventory-0.9.0.md"
)
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

CAPABILITY_ROW_RE = re.compile(
    r"^\| `(?P<capability>CAP-[A-Z]+-[0-9]{3})` \| .* \| `(?P<topic>ug-[a-z0-9-]+)` \| "
    r"(?P<kind>task|concept|reference|troubleshooting) \|$"
)

pytestmark = pytest.mark.docs_contract


def _closure() -> dict[str, object]:
    return json.loads(CLOSURE.read_text(encoding="utf-8"))


def _case_map() -> dict[str, object]:
    return json.loads(CASE_MAP.read_text(encoding="utf-8"))


def _case_topics() -> list[dict[str, object]]:
    return [topic for section in _case_map()["sections"] for topic in section["topics"]]


def _inventory_rows() -> list[dict[str, str]]:
    rows = []
    for line in CAPABILITY_INVENTORY.read_text(encoding="utf-8").splitlines():
        if match := CAPABILITY_ROW_RE.match(line):
            rows.append(match.groupdict())
    return rows


def _readme_main_capability_bullets() -> list[str]:
    source = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    section = source.split("## Main Capabilities", 1)[1].split("## Supported Firefox Schemas", 1)[0]
    bullets: list[str] = []
    current: list[str] = []
    for line in section.splitlines():
        if line.startswith("- "):
            if current:
                bullets.append(" ".join(current))
            current = [line.removeprefix("- ").strip()]
        elif current and line.startswith("  "):
            current.append(line.strip())
    if current:
        bullets.append(" ".join(current))
    return bullets


def _topic_root(locale: str, topic_id: str) -> ET.Element:
    return ET.fromstring(
        (DITA_ROOT / locale / "user" / f"{topic_id}.dita").read_text(encoding="utf-8")
    )


def _expected_tag(kind: str) -> str:
    if kind == "concept":
        return "concept"
    if kind == "reference":
        return "reference"
    return "task"


def _section_keyrefs(locale: str) -> set[str]:
    root = ET.fromstring(
        (DITA_ROOT / locale / "maps/user-guide.ditamap").read_text(encoding="utf-8")
    )
    return {
        topicref.attrib["keyref"].removeprefix("topic.")
        for topicref in root.findall(".//topicref")
        if topicref.attrib.get("keyref", "").startswith("topic.")
    }


def test_user_guide_coverage_closure_artifact_is_complete_and_source_backed() -> None:
    closure = _closure()

    assert closure["schema_version"] == 1
    assert closure["target_bpm_version"] == "0.9.0"
    assert closure["guide_id"] == "user-guide"
    assert closure["status"] == "closed"
    assert closure["closed_by_backlog_item"] == "BPM090-M4-12"
    assert (
        closure["source_inventory"]
        == "docs/architecture/product-user-capability-inventory-0.9.0.md"
    )
    assert closure["case_map"] == "documentation/config/user-guide-map-0.9.0.json"

    summary = closure["summary"]
    assert summary == {
        "inventory_capability_count": 106,
        "planned_topic_count": 89,
        "localized_topic_count_per_locale": 89,
        "locales": list(LOCALES),
        "omissions": [],
    }

    for relative in closure["reviewed_sources"]:
        assert (REPOSITORY_ROOT / relative).is_file(), relative
    assert len(closure["release_gate_rules"]) >= 6


def test_every_inventory_capability_has_reachable_localized_dita_topic() -> None:
    closure = _closure()
    rows = _inventory_rows()
    case_topics = _case_topics()
    row_by_capability = {row["capability"]: row for row in rows}
    case_by_topic = {topic["topic_id"]: topic for topic in case_topics}

    assert len(rows) == closure["summary"]["inventory_capability_count"]
    assert len({row["topic"] for row in rows}) == closure["summary"]["planned_topic_count"]
    assert len(case_by_topic) == closure["summary"]["planned_topic_count"]

    mapped_capabilities = {
        capability for topic in case_topics for capability in topic["capability_ids"]
    }
    assert mapped_capabilities == set(row_by_capability)
    assert set(case_by_topic) == {row["topic"] for row in rows}

    for row in rows:
        topic = case_by_topic[row["topic"]]
        assert row["capability"] in topic["capability_ids"]
        assert row["kind"] == topic["kind"]

    for locale in LOCALES:
        keys = ET.fromstring((DITA_ROOT / locale / "maps/keys.ditamap").read_text(encoding="utf-8"))
        keydefs = {
            keydef.attrib["keys"]: keydef.attrib["href"]
            for keydef in keys.findall("keydef")
            if keydef.attrib["keys"].startswith("topic.")
        }
        reachable = _section_keyrefs(locale)
        for topic_id, topic in case_by_topic.items():
            root = _topic_root(locale, topic_id)
            assert root.tag == _expected_tag(topic["kind"])
            assert root.attrib == {
                "id": topic_id,
                XML_LANG: locale,
                "audience": "user",
                "product": "bpm-0-9-0",
                "platform": "web",
            }
            assert keydefs[f"topic.{topic_id}"] == f"../user/{topic_id}.dita"
            assert topic_id in reachable


def test_readme_routes_and_api_boundaries_are_closed_by_mapped_user_topics() -> None:
    closure = _closure()
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    case_topic_ids = {topic["topic_id"] for topic in _case_topics()}
    web_routes = (REPOSITORY_ROOT / "app/web/profiles.py").read_text(encoding="utf-8")
    main_app = (REPOSITORY_ROOT / "app/main.py").read_text(encoding="utf-8")

    assert _readme_main_capability_bullets() == closure["readme_capabilities"]

    for route in closure["product_routes"]:
        assert f"`{route['readme_route']}`" in readme
        source = main_app if route["app_route"].startswith("@app") else web_routes
        assert route["app_route"] in source
        assert set(route["topic_ids"]) <= case_topic_ids

    for route in closure["non_user_routes"]:
        assert f"`{route['readme_route']}`" in readme
        assert route["reason"]

    for boundary in closure["api_boundaries"]:
        assert f"`{boundary['readme_endpoint']}`" in readme
        source = (REPOSITORY_ROOT / boundary["source_file"]).read_text(encoding="utf-8")
        assert boundary["source_token"] in source
        assert set(boundary["topic_ids"]) <= case_topic_ids


def test_template_locale_and_browser_smoke_evidence_remain_covered() -> None:
    closure = _closure()
    case_topic_ids = {topic["topic_id"] for topic in _case_topics()}

    for evidence in closure["template_evidence"]:
        source = (REPOSITORY_ROOT / evidence["file"]).read_text(encoding="utf-8")
        for token in evidence["tokens"]:
            assert token in source, (evidence["file"], token)

    catalog_keysets = []
    for locale in LOCALES:
        catalog = json.loads(
            (REPOSITORY_ROOT / "app/i18n" / f"{locale}.json").read_text(encoding="utf-8")
        )
        catalog_keysets.append(set(catalog))
        assert "profiles.title" in catalog
        assert "profiles.nav_library" in catalog
        assert "profiles.theme_dark" in catalog
    assert all(keys == catalog_keysets[0] for keys in catalog_keysets)

    browser_smoke = (REPOSITORY_ROOT / "tests/browser/profiles/test_ui_browser_tabs.py").read_text(
        encoding="utf-8"
    )
    assert "pytest.mark.browser_ui," in browser_smoke
    assert 'SMOKE_LOCALES = ("ru", "zh-CN")' in browser_smoke
    for flow in closure["browser_smoke_flows"]:
        assert f"def {flow}" in browser_smoke

    for rule in closure["release_gate_rules"]:
        assert rule
    assert case_topic_ids >= {
        "ug-task-change-interface-language",
        "ug-task-use-profile-library",
        "ug-task-use-guided-editor",
        "ug-task-use-all-settings",
        "ug-task-use-json-editor",
        "ug-task-compare-profiles",
        "ug-troubleshoot-product-connection",
    }
