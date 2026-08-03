"""Build a deterministic, manifest-bound DITA chunk manifest for local RAG work.

The generated manifest is evidence/artifact output only. It never enables a model, retrieval,
network request, or change to BPM's independent lexical documentation search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    from . import build_docs
except ImportError:
    import build_docs


DOCUMENTATION_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = DOCUMENTATION_ROOT.parent
CONFIG_PATH = DOCUMENTATION_ROOT / "config/rag-chunk-extraction-0.9.3.json"
EXCLUSIONS_PATH = DOCUMENTATION_ROOT / "config/rag-corpus-exclusions-0.9.3.json"
ANCHOR_PATTERN = re.compile(r"a-[a-z0-9]+(?:-[a-z0-9]+)*$")
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?。！？])\s+")


class ChunkExtractionError(ValueError):
    """Raised when a published DITA unit cannot form a safe deterministic chunk."""


def retrieval_diagnostic(chunk: dict[str, Any], rejection_category: str) -> dict[str, Any]:
    policy = _read_json(EXCLUSIONS_PATH)
    fields = policy["diagnostics"]["allowed_fields"]
    diagnostic = {field: chunk.get(field, "") for field in fields if field != "rejection_category"}
    diagnostic["rejection_category"] = rejection_category
    return diagnostic


def validate_retrieval_chunk(chunk: dict[str, Any]) -> None:
    policy = _read_json(EXCLUSIONS_PATH)
    allowed = policy["allow"]
    path = str(chunk.get("source_dita_path", ""))
    normalized = f"/{path.strip('/')}/"
    if any(fragment in normalized for fragment in policy["deny"]["path_fragments"]):
        raise ChunkExtractionError(json.dumps(retrieval_diagnostic(chunk, "excluded-path"), sort_keys=True))
    if not any(path.startswith(prefix) for prefix in allowed["source_path_prefixes"]):
        raise ChunkExtractionError(json.dumps(retrieval_diagnostic(chunk, "unapproved-source"), sort_keys=True))
    if chunk.get("publication_state") != allowed["publication_state"]:
        raise ChunkExtractionError(json.dumps(retrieval_diagnostic(chunk, "not-published"), sort_keys=True))
    if chunk.get("provenance_class") not in allowed["provenance_classes"]:
        raise ChunkExtractionError(json.dumps(retrieval_diagnostic(chunk, "blocked-provenance"), sort_keys=True))
    if not str(chunk.get("published_url", "")).startswith(allowed["published_url_prefix"]):
        raise ChunkExtractionError(json.dumps(retrieval_diagnostic(chunk, "unpublished-url"), sort_keys=True))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def _kind(tag: str) -> str:
    return {
        "shortdesc": "shortdesc",
        "p": "paragraph",
        "li": "paragraph",
        "steps": "steps",
        "table": "table",
        "codeblock": "code",
        "screen": "code",
        "example": "example",
        "note": "note",
        "dlentry": "definition",
    }[tag]


def _heading_path(root: ET.Element, unit: ET.Element) -> list[str]:
    parent = {child: node for node in root.iter() for child in node}
    headings: list[str] = []
    current: ET.Element | None = unit
    while current is not None:
        title = _text(current.find("title"))
        if title:
            headings.append(title)
        current = parent.get(current)
    return list(reversed(headings))


def _blocks(unit: ET.Element, config: dict[str, Any]) -> list[tuple[str, str]]:
    block_tags = set(config["units"]["block_tags"])
    blocks: list[tuple[str, str]] = []

    def visit(element: ET.Element, is_unit: bool = False) -> None:
        if not is_unit and ANCHOR_PATTERN.fullmatch(element.attrib.get("id", "")):
            return
        tag = _tag(element)
        if tag == "title":
            return
        if tag == "example":
            title = _text(element.find("title"))
            if title:
                blocks.append(("example", title))
            for child in element:
                visit(child)
            return
        if tag in block_tags:
            value = _text(element)
            if value:
                blocks.append((_kind(tag), value))
            return
        for child in element:
            visit(child)

    visit(unit, is_unit=True)
    return blocks


def _split_plain_text(text: str, maximum: int) -> list[str]:
    if len(text) <= maximum:
        return [text]
    result: list[str] = []
    current = ""
    for sentence in SENTENCE_BOUNDARY.split(text):
        if len(sentence) > maximum:
            words = sentence.split()
            sentence = ""
            for word in words:
                candidate = f"{sentence} {word}".strip()
                if len(candidate) > maximum and sentence:
                    result.append(sentence)
                    sentence = word
                else:
                    sentence = candidate
            if sentence:
                if current:
                    result.append(current)
                    current = ""
                result.append(sentence)
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) > maximum and current:
            result.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        result.append(current)
    if any(not part or len(part) > maximum for part in result):
        raise ChunkExtractionError("plain-text block cannot be split within maximum length")
    return result


def _bounded_parts(
    blocks: list[tuple[str, str]], config: dict[str, Any], prefix_characters: int
) -> list[tuple[list[str], list[str]]]:
    target = config["bounds"]["target_characters"] - prefix_characters
    maximum = config["bounds"]["maximum_characters"] - prefix_characters
    if target <= 0 or maximum <= 0:
        raise ChunkExtractionError("heading path exceeds chunk bound")
    parts: list[tuple[list[str], list[str]]] = []
    texts: list[str] = []
    kinds: list[str] = []

    def flush() -> None:
        nonlocal texts, kinds
        if texts:
            parts.append((texts, kinds))
        texts, kinds = [], []

    for kind, text in blocks:
        if len(text) > maximum:
            if kind in {"code", "table"}:
                raise ChunkExtractionError(f"{kind} block exceeds maximum chunk length")
            candidates = _split_plain_text(text, maximum)
        else:
            candidates = [text]
        for candidate in candidates:
            projected = len("\n\n".join(texts + [candidate]))
            if texts and (projected > target or projected > maximum):
                flush()
            texts.append(candidate)
            kinds.append(kind)
            if len("\n\n".join(texts)) > maximum:
                raise ChunkExtractionError("chunk exceeds maximum length")
    flush()
    return parts


def _provenance(source: Path) -> str:
    relative = source.resolve().relative_to(DOCUMENTATION_ROOT.resolve()).as_posix()
    if relative.startswith("src/dita/"):
        return "published_reviewed_dita"
    if relative.startswith("src/generated/"):
        return "published_approved_generated_dita"
    raise ChunkExtractionError(f"unsupported chunk source provenance: {relative}")


def _topic_chunks(
    locale: str,
    topic_id: str,
    topic: dict[str, Any],
    manifest: dict[str, Any],
    identifiers: list[str],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    root = topic["_roots"][locale]
    source = Path(topic["_source_paths"][locale])
    source_hash = _sha256(source)
    output = topic["output"][locale]
    units = [("root", root)] + [
        (element.attrib["id"], element)
        for element in root.iter()
        if ANCHOR_PATTERN.fullmatch(element.attrib.get("id", ""))
    ]
    chunks: list[dict[str, Any]] = []
    for locator, unit in units:
        heading_path = _heading_path(root, unit)
        prefix_characters = len(heading_path[-1]) + 2 if heading_path else 0
        for ordinal, (texts, kinds) in enumerate(
            _bounded_parts(_blocks(unit, config), config, prefix_characters)
        ):
            text = "\n\n".join([*heading_path[-1:], *texts]).strip()
            if not text:
                continue
            if len(text) > config["bounds"]["maximum_characters"]:
                raise ChunkExtractionError(f"chunk text exceeds maximum: {locale}/{topic_id}/{locator}")
            chunk_id = f"ragc-v1:{locale}:{topic_id}:{locator}:{ordinal}"
            chunk = {
                    "chunk_id": chunk_id,
                    "chunk_schema_version": config["chunk_schema_version"],
                    "locale": locale,
                    "topic_id": topic_id,
                    "anchor_id_or_root": locator,
                    "ordinal": ordinal,
                    "guide_id": topic["guide_id"],
                    "published_url": f"/help/{output}" + ("" if locator == "root" else f"#{locator}"),
                    "source_dita_path": source.relative_to(REPOSITORY_ROOT).as_posix(),
                    "source_revision": manifest["artifact"]["source_revision"],
                    "source_sha256": source_hash,
                    "manifest_sha256": _sha256(Path(manifest["_path"])),
                    "documentation_version": manifest["artifact"]["documentation_version"],
                    "bpm_version": manifest["artifact"]["bpm_version"],
                    "provenance_class": _provenance(source),
                    "publication_state": "published",
                    "heading_path": heading_path,
                    "identifiers": identifiers,
                    "text_normalization_revision": config["text_normalization_revision"],
                    "content_kinds": list(dict.fromkeys(kinds)),
                    "text": text,
                    "character_count": len(text),
            }
            validate_retrieval_chunk(chunk)
            chunks.append(chunk)
    return chunks


def extract_from_site(site_root: Path) -> dict[str, Any]:
    config = _read_json(CONFIG_PATH)
    manifest_path = site_root / "manifest.json"
    manifest = _read_json(manifest_path)
    manifest["_path"] = str(manifest_path)
    if manifest.get("locales") != config["locales"]:
        raise ChunkExtractionError("published manifest locales do not match chunk contract")
    topics = build_docs._build_topics(site_root)
    target_map = _read_json(site_root / "ui-target-map.json")
    identifiers_by_topic = build_docs._target_identifiers_by_topic(target_map)
    chunks: list[dict[str, Any]] = []
    for topic_id, topic in sorted(topics.items()):
        if "_roots" not in topic:
            continue  # Guide landing pages are map shells, not DITA topics.
        for locale in config["locales"]:
            identifiers = sorted({topic_id, topic["dita_key"], *topic["anchors"], *sum(identifiers_by_topic.get(topic_id, {}).values(), [])})
            chunks.extend(_topic_chunks(locale, topic_id, topic, manifest, identifiers, config))
    chunks.sort(key=lambda item: (item["locale"], item["topic_id"], item["anchor_id_or_root"], item["ordinal"]))
    return {
        "schema_version": 1,
        "contract_id": config["contract_id"],
        "backlog_item": config["backlog_item"],
        "chunk_schema_version": config["chunk_schema_version"],
        "text_normalization_revision": config["text_normalization_revision"],
        "source_manifest_sha256": _sha256(manifest_path),
        "source_revision": manifest["artifact"]["source_revision"],
        "bpm_version": manifest["artifact"]["bpm_version"],
        "documentation_version": manifest["artifact"]["documentation_version"],
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def write_manifest(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    candidate = output.with_suffix(output.suffix + ".tmp")
    candidate.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, help="validated publish tree; otherwise build a temporary one")
    args = parser.parse_args()
    if args.site_root:
        payload = extract_from_site(args.site_root)
    else:
        with tempfile.TemporaryDirectory(prefix="bpm-rag-chunks-") as temporary:
            site_root = Path(temporary) / "site"
            build_docs.build_tree(site_root)
            payload = extract_from_site(site_root)
    write_manifest(payload, args.output)
    print(f"RAG chunk manifest: {args.output} ({payload['chunk_count']} chunks)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
