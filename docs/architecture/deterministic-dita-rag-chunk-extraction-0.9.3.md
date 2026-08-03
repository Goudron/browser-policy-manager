# BPM 0.9.3 Deterministic DITA RAG Chunk Extraction

Backlog item: `BPM093-M5-01`

Status: **Implemented build-time artifact generator; no RAG runtime is enabled.**

## Boundary

`extract_rag_chunks_0_9_3.py` creates an ignored, versioned chunk manifest from a validated
six-locale DITA publish tree. It receives the published manifest, localized DITA topic roots, and
UI target map from the same build, then emits no model, embedding, retrieval index, listener, or
network request. The existing lexical documentation search remains independent and available.

Only a published topic represented by the manifest can produce a chunk. The extractor rejects a
source path outside reviewed DITA or approved generated DITA and labels each output with its source
provenance. Map-only guide landing shells are not DITA topics and therefore do not create semantic
chunks.

## Deterministic Unit And Chunk Rules

- A unit is exactly one locale and one topic, at either its `root` or one stable `a-*` anchor.
  Nested anchored units are excluded from the parent unit, so chunks never cross anchor boundaries.
- The extractor preserves heading path, short description, paragraphs, steps, tables, code/screen,
  examples, notes, and definitions as typed DITA blocks.
- Blocks are appended in source order up to the versioned target/max character bounds. Plain prose
  may split only at deterministic sentence then whitespace boundaries; oversized code or table
  blocks fail closed rather than being silently truncated or mixed with another unit.
- IDs are `ragc-v1:{locale}:{topic_id}:{anchor_id_or_root}:{ordinal}`. They depend solely on the
  stable unit locator and ordinal, never content hash or model identity.

Every chunk records its published `/help/{locale}/...` URL, topic/anchor, guide, heading path,
identifiers, locale/version, source path/revision/SHA-256, source-manifest SHA-256, provenance,
normalization revision, content kinds, text, and character count. JSON serialization is canonical
UTF-8 with sorted keys and a trailing newline, so identical sources give byte-identical manifests.

## Use And Verification

Run from the repository root:

```bash
./.venv/bin/python documentation/tools/extract_rag_chunks_0_9_3.py \
  --output documentation/reports/rag/chunks-0.9.3.json
```

Without `--site-root`, the tool builds an isolated temporary publish tree. Its output is an ignored
candidate artifact and is never hand-edited or committed. The focused contract test uses a compact
six-locale DITA fixture to prove deterministic bytes, schema/metadata, resolvable URL shape,
provenance, stable IDs, typed boundaries, and maximum length.

Against the validated BPM 0.9.3 development publish tree, the extractor produced 2,401 chunks for
`en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`; the largest was 2,394 characters against the 2,400
character maximum. The generated manifest is only local evidence and is not committed.

M5-02 owns fail-closed corpus exclusions beyond this structural published-source boundary. M5-05
may consume a chunk manifest only after model/vector selection and compatibility checks; ordinary
chunk extraction does not train or modify any model weights.
