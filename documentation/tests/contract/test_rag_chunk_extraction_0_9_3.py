from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
CONFIG_PATH = DOCUMENTATION_ROOT / "config/rag-chunk-extraction-0.9.3.json"
EXTRACTOR_PATH = DOCUMENTATION_ROOT / "tools/extract_rag_chunks_0_9_3.py"
BUILD_DOCS_PATH = DOCUMENTATION_ROOT / "tools/build_docs.py"
TOOLS_ROOT = DOCUMENTATION_ROOT / "tools"

if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

EXTRACTOR_SPEC = importlib.util.spec_from_file_location("rag_chunk_extractor", EXTRACTOR_PATH)
assert EXTRACTOR_SPEC and EXTRACTOR_SPEC.loader
extractor = importlib.util.module_from_spec(EXTRACTOR_SPEC)
EXTRACTOR_SPEC.loader.exec_module(extractor)

BUILD_DOCS_SPEC = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS_PATH)
assert BUILD_DOCS_SPEC and BUILD_DOCS_SPEC.loader
build_docs = importlib.util.module_from_spec(BUILD_DOCS_SPEC)
BUILD_DOCS_SPEC.loader.exec_module(build_docs)

pytestmark = pytest.mark.docs_contract


def test_chunk_extraction_contract_is_bounded_manifest_backed_and_six_locale() -> None:
    contract = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert contract["contract_id"] == "bpm-rag-chunk-extraction-0.9.3"
    assert contract["backlog_item"] == "BPM093-M5-01"
    assert contract["chunk_schema_version"] == "rag-chunk-v1"
    assert contract["locales"] == list(build_docs.LOCALES)
    assert contract["source_boundary"]["published_manifest_required"] is True
    assert contract["bounds"]["overlap_characters"] == 0
    assert contract["bounds"]["maximum_characters"] > contract["bounds"]["target_characters"]
    assert {"steps", "table", "code", "example"} <= set(contract["units"]["preserve_kinds"])


def test_dita_to_chunks_is_byte_deterministic_and_keeps_published_boundaries(
    tmp_path: Path,
) -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    manifest = {
        "_path": str(manifest_path),
        "artifact": {
            "source_revision": "test-source-revision",
            "documentation_version": "0.9.3",
            "bpm_version": "0.9.3",
        },
    }
    chunks = []
    for locale in build_docs.LOCALES:
        root = ET.fromstring("""
            <task id="ug-task-export-policies-json">
              <title>Export policy JSON</title>
              <shortdesc>Export the reviewed policy document.</shortdesc>
              <taskbody><steps><step><cmd>Open Export.</cmd></step></steps></taskbody>
              <section id="a-example"><title>Example</title><example><title>JSON</title><codeblock>{&quot;policy&quot;: true}</codeblock></example><table><tgroup><tbody><row><entry>Field</entry><entry>Value</entry></row></tbody></tgroup></table></section>
            </task>
            """)
        source = DOCUMENTATION_ROOT / f"src/dita/{locale}/user/ug-task-export-policies-json.dita"
        topic = {
            "_roots": {locale: root},
            "_source_paths": {locale: source},
            "output": {locale: f"{locale}/user/ug-task-export-policies-json.html"},
            "guide_id": "user-guide",
            "dita_key": "topic.ug-task-export-policies-json",
            "anchors": {"a-example": {}},
        }
        chunks.extend(
            extractor._topic_chunks(
                locale,
                "ug-task-export-policies-json",
                topic,
                manifest,
                ["ug-task-export-policies-json", "a-example", "API-VAL-001"],
                config,
            )
        )
    first = {
        "chunk_count": len(chunks),
        "chunks": sorted(chunks, key=lambda item: (item["locale"], item["chunk_id"])),
    }
    second = {
        "chunk_count": len(chunks),
        "chunks": sorted(chunks, key=lambda item: (item["locale"], item["chunk_id"])),
    }
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    extractor.write_manifest(first, first_path)
    extractor.write_manifest(second, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["chunk_count"] == len(first["chunks"])
    assert first["chunk_count"] > 0
    assert {chunk["locale"] for chunk in first["chunks"]} == set(build_docs.LOCALES)

    contract = config
    required = set(contract["manifest"]["required_chunk_fields"])
    maximum = contract["bounds"]["maximum_characters"]
    ids = [chunk["chunk_id"] for chunk in first["chunks"]]
    assert len(ids) == len(set(ids))
    assert {"steps", "table", "code", "example"} <= {
        kind for chunk in first["chunks"] for kind in chunk["content_kinds"]
    }

    for chunk in first["chunks"]:
        assert required <= set(chunk)
        assert chunk["chunk_schema_version"] == "rag-chunk-v1"
        assert chunk["character_count"] == len(chunk["text"]) <= maximum
        assert chunk["publication_state"] == "published"
        assert (
            chunk["provenance_class"] in contract["source_boundary"]["allowed_provenance_classes"]
        )
        assert chunk["chunk_id"] == "ragc-v1:{locale}:{topic_id}:{anchor}:{ordinal}".format(
            locale=chunk["locale"],
            topic_id=chunk["topic_id"],
            anchor=chunk["anchor_id_or_root"],
            ordinal=chunk["ordinal"],
        )
        assert (
            f"/help/{chunk['locale']}/user/ug-task-export-policies-json.html"
            in chunk["published_url"]
        )
        if chunk["anchor_id_or_root"] != "root":
            assert chunk["published_url"].endswith(f"#{chunk['anchor_id_or_root']}")
