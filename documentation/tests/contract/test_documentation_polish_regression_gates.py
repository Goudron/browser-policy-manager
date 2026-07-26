from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DOC_ROOT = ROOT / "documentation"
DITA_ROOT = DOC_ROOT / "src/dita"
GATES = DOC_ROOT / "config/documentation-polish-regression-gates-0.9.1.json"
VISIBLE_REVIEW = DOC_ROOT / "config/visible-english-prose-review-0.9.1.json"
API_REHOME = ROOT / "docs/architecture/api-integration-rehome-audit-0.9.0.json"
SUITE_BOUNDARIES = DOC_ROOT / "tests/suite-boundaries-0.9.0.json"
BUILD_MODULE = DOC_ROOT / "tools/build_docs.py"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
VISIBLE_TAGS = {
    "title",
    "navtitle",
    "shortdesc",
    "p",
    "cmd",
    "entry",
    "note",
    "figdesc",
    "alt",
}

SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_MODULE)
assert SPEC and SPEC.loader
build_docs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _expanded_sources(source: str) -> list[Path]:
    if "{locale}" not in source:
        return [ROOT / source]
    return [ROOT / source.format(locale=locale) for locale in LOCALES]


def _navigation_manifest() -> dict:
    guides: dict[str, dict] = {}
    topics: dict[str, dict] = {}
    hrefs_by_locale = {locale: build_docs._localized_map_keydefs(locale) for locale in LOCALES}
    for guide_id, filename, _anchor, url_root in build_docs.GUIDE_MAPS:
        guide_titles = build_docs._guide_titles(filename)
        guides[guide_id] = {
            "url_root": url_root,
            "home_topic_id": guide_id,
            "title": guide_titles,
        }
        topics[guide_id] = {
            "title": guide_titles,
            "output": {locale: f"{locale}/index.html" for locale in LOCALES},
        }
        for keyref in build_docs._guide_topic_keyrefs("en", filename):
            topic_id = keyref.removeprefix("topic.")
            roots = build_docs._localized_topic_roots(keyref, hrefs_by_locale)
            topics[topic_id] = {
                "title": {
                    locale: build_docs._element_text(root.find("title"))
                    for locale, root in roots.items()
                },
                "output": {
                    locale: (
                        f"{locale}/{hrefs_by_locale[locale][keyref].parent.name}/{topic_id}.html"
                    )
                    for locale in LOCALES
                },
            }
    product_version = build_docs._product_version()
    return {
        "artifact": {
            "bpm_version": product_version,
            "documentation_version": product_version,
        },
        "guides": guides,
        "topics": topics,
    }


def _node_count(node: dict) -> int:
    return 1 + sum(_node_count(child) for child in node["children"])


def _navigation_payload(manifest: dict, locale: str = "ru") -> dict:
    root = build_docs._manifest_navigation_root(manifest, locale)
    return {
        "$schema": "../schemas/product-documentation-navigation-v1.schema.json",
        "schema_version": 1,
        "documentation_version": build_docs._product_version(),
        "locale": locale,
        "node_count": _node_count(root),
        "root": root,
    }


def _payload_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _record(payload: dict, content: bytes) -> dict:
    return {
        "path": f"{payload['locale']}/navigation.json",
        "sha256": hashlib.sha256(content).hexdigest(),
        "format_version": payload["schema_version"],
        "node_count": payload["node_count"],
    }


def _first_topic(root: dict) -> dict:
    pending = [root]
    while pending:
        node = pending.pop(0)
        if node["node_type"] == "topic":
            return node
        pending.extend(node["children"])
    raise AssertionError("navigation fixture has no topic node")


def test_regression_gate_contract_is_complete_and_release_wired() -> None:
    contract = _json(GATES)
    expected_gate_ids = {
        "standalone-api-guide-absent",
        "administrator-api-ownership-complete",
        "locale-navigation-source-complete",
        "navigation-manifest-integrity",
        "embedded-navigation-tree-absent",
        "localized-safe-navigation-labels",
        "ui-term-catalog-parity",
        "visible-english-leakage-absent",
        "locale-review-coverage-complete",
        "allowlist-entries-live-and-bounded",
    }

    assert contract["schema_version"] == 1
    assert contract["gate_id"] == "bpm-0.9.1-documentation-polish-regression-gates"
    assert contract["target_bpm_version"] == "0.9.1"
    assert contract["backlog_item"] == "BPM091-M10-08"
    assert contract["status"] == "accepted"
    assert contract["locales"] == list(LOCALES)
    assert contract["non_english_locales"] == list(LOCALES[1:])
    assert set(contract["release_gates"]) == {
        "make test-docs-contract",
        "make docs-release-check",
        "make test-release",
    }
    gates = {gate["id"]: gate for gate in contract["gates"]}
    assert set(gates) == expected_gate_ids

    suite = _json(SUITE_BOUNDARIES)["domains"]["bpm_0_9_1_completion"]
    assert (
        "documentation/tests/contract/test_documentation_polish_regression_gates.py"
        in suite["path_globs"]
    )
    assert (
        "documentation/config/documentation-polish-regression-gates-0.9.1.json" in suite["fixtures"]
    )

    for gate in gates.values():
        assert gate["fails_when"]
        assert gate["checks"]
        for source in gate["source_files"]:
            assert all(path.exists() for path in _expanded_sources(source)), source
        for check in gate["checks"]:
            relative_path, function_name = check.split("::", 1)
            path = ROOT / relative_path
            assert path.is_file(), check
            assert function_name in _definitions(path), check


def test_api_retirement_and_administrator_ownership_are_complete_in_every_locale() -> None:
    expected_topics = {
        entry["future_topic_id"] for entry in _json(API_REHOME)["api_topics_to_rehome"]
    }
    assert len(expected_topics) == 13

    for locale in LOCALES:
        locale_root = DITA_ROOT / locale
        assert not (locale_root / "maps/api-integration-guide.ditamap").exists()
        portal = (locale_root / "maps/portal.ditamap").read_text(encoding="utf-8")
        assert "api-integration-guide" not in portal

        admin_root = ET.parse(locale_root / "maps/administrator-guide.ditamap").getroot()
        admin_topics = {
            element.attrib["keyref"].removeprefix("topic.")
            for element in admin_root.iter("topicref")
            if element.attrib.get("keyref", "").startswith("topic.")
        }
        assert expected_topics <= admin_topics

        keys_root = ET.parse(locale_root / "maps/keys.ditamap").getroot()
        keydefs = {
            element.attrib["keys"].removeprefix("topic."): element.attrib["href"]
            for element in keys_root.findall("keydef")
            if element.attrib.get("keys", "").startswith("topic.")
        }
        for topic_id in expected_topics:
            assert keydefs[topic_id] == f"../admin/{topic_id}.dita"
            assert (locale_root / f"admin/{topic_id}.dita").is_file()


def test_navigation_artifact_record_rejects_stale_hash() -> None:
    manifest = _navigation_manifest()
    payload = _navigation_payload(manifest)
    content = _payload_bytes(payload)
    record = _record(payload, content)
    record["sha256"] = "0" * 64

    with pytest.raises(build_docs.BuildError, match="navigation SHA-256 mismatch"):
        build_docs._validate_navigation_artifact_record(
            "ru", record, content, manifest, context="archived"
        )


@pytest.mark.parametrize(
    "mutation",
    ("english_root_fallback", "unsafe_label", "unsafe_href", "missing_topic", "wrong_locale"),
)
def test_navigation_artifact_record_rejects_semantic_mutations(mutation: str) -> None:
    manifest = _navigation_manifest()
    payload = copy.deepcopy(_navigation_payload(manifest))
    if mutation == "english_root_fallback":
        payload["root"]["label"] = build_docs.SHELL_LABELS["en"]["navigation_root"]
    elif mutation == "unsafe_label":
        payload["root"]["label"] = "<img src=x onerror=alert(1)>"
    elif mutation == "unsafe_href":
        _first_topic(payload["root"])["href"] = "https://outside.invalid/topic"
    elif mutation == "missing_topic":
        first_guide = payload["root"]["children"][0]
        first_group = first_guide["children"][0]
        topic_parent = first_group if first_group["node_type"] == "section" else first_guide
        topic_parent["children"].pop()
        payload["node_count"] = _node_count(payload["root"])
    elif mutation == "wrong_locale":
        payload["locale"] = "en"
    else:
        raise AssertionError(mutation)
    content = _payload_bytes(payload)
    record = _record(payload, content)
    record["path"] = "ru/navigation.json"

    with pytest.raises(build_docs.BuildError):
        build_docs._validate_navigation_artifact_record(
            "ru", record, content, manifest, context="archived"
        )


def test_navigation_artifact_accepts_reviewed_technical_labels() -> None:
    manifest = _navigation_manifest()
    payload = _navigation_payload(manifest)
    content = _payload_bytes(payload)
    labels = json.dumps(payload["root"], ensure_ascii=False)

    assert all(token in labels for token in ("BPM", "CIS", "API", "DevOps"))
    build_docs._validate_navigation_artifact_record(
        "ru", _record(payload, content), content, manifest, context="archived"
    )


def test_generated_html_rejects_embedded_tree_copy(tmp_path: Path) -> None:
    for locale in LOCALES:
        locale_root = tmp_path / locale
        locale_root.mkdir()
        embedded = (
            '<div role="tree"><a data-docs-tree href="topic.html">Topic</a></div>'
            if locale == "ru"
            else ""
        )
        (locale_root / "index.html").write_text(
            f'<!doctype html><html lang="{locale}"><body class="bpm-docs-shell">'
            '<nav aria-label="primary"></nav><nav aria-label="secondary"></nav>'
            '<nav aria-label="breadcrumbs"></nav><div data-docs-tree-host></div>'
            f'{embedded}<main id="main-content"><h1>Documentation</h1></main>'
            "</body></html>",
            encoding="utf-8",
        )

    with pytest.raises(build_docs.BuildError, match="must not embed navigation tree nodes"):
        build_docs.validate_output(tmp_path)


def test_exact_peer_allowlist_entries_are_live_and_bounded() -> None:
    review = _json(VISIBLE_REVIEW)
    entries = review["reviewed_exact_peer_homographs"]
    seen: set[tuple[str, str, str]] = set()

    for entry in entries:
        item = (entry["locale"], entry["source"], entry["text"])
        assert item not in seen
        seen.add(item)
        assert entry["locale"] in LOCALES[1:]
        assert entry["classification"]
        assert len(re.findall(r"[A-Za-z]+", entry["text"])) < 6

        localized_path = ROOT / entry["source"]
        relative = localized_path.relative_to(DITA_ROOT / entry["locale"])
        english_path = DITA_ROOT / "en" / relative
        for path in (localized_path, english_path):
            root = ET.parse(path).getroot()
            visible_blocks = {
                " ".join("".join(element.itertext()).split())
                for element in root.iter()
                if element.tag in VISIBLE_TAGS
            }
            assert entry["text"] in visible_blocks, (entry, path)

    assert len(entries) == review["result"]["release_blocking_exact_peer_carryover_blocks"] + 4
    assert review["result"]["release_blocking_exact_peer_carryover_blocks"] == 0
