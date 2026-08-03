# BPM 0.9.3 RAG Knowledge And Update Contract

Date: 2026-07-28

Backlog item: `BPM093-M2-04`

Status: **Accepted architecture contract; no RAG runtime, model, embeddings, chunks, or index is implemented by this record.**

## Decision

`documentation/config/rag-knowledge-and-update-contract-0.9.3.json` is the source contract for future knowledge ingestion and updates. It applies to all supported locales: `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`.

The existing deterministic lexical search contract remains the active runtime behavior. Chat RAG is a
separate, explicitly enabled path: it neither calls nor changes ordinary search, and ordinary search
has no AI/RAG dependency. This decision does not enable a model, model server, network access,
or model training; if the separate chat path is unavailable, it must fail closed to lexical search
without altering ordinary-search results.
generated RAG artifact, or product-facing assistant.

## Eligible Knowledge

Only published, reviewed, provenance-permitted DITA text may become local knowledge. It must be represented by a published locale manifest record, preserve its topic/anchor identity, and resolve to the current local `/help/{locale}/…` citation URL. Approved generated DITA may participate only when both its generator input/provenance and published output permit it. Language-neutral technical identifiers remain attached to their locale-specific source text; foreign-language prose is not a fallback.

The following are never knowledge sources: unpublished or restricted material, provenance-only CIS records, fixture data, generated answers, chats, prompts, model output, embeddings, vector indexes, web responses, BPM profiles/databases/logs, unreviewed screenshots, caches, telemetry, secrets, or private hosts. An answer may cite a published topic/anchor only — not a chunk, a vector, a score, or an answer generated earlier.

## Chunk And Provenance Model

Chunking projects published DITA into plain text while retaining title, short description, heading path, identifiers, locale, source URL, source revision, source and manifest SHA-256 values, documentation/BPM versions, and provenance class. It excludes markup, navigation chrome, scripts, unreviewed asset text, and generated answer text.

One chunk belongs to one locale and one published topic. A stable anchor or topic root is the preferred unit; longer units split only at deterministic sentence/block boundaries. The stable ID is:

```text
ragc-v1:{locale}:{topic_id}:{anchor_id_or_root}:{ordinal}
```

The ID deliberately does not contain source hashes or model details. A changed or removed source unit invalidates its old ID instead of letting unrelated text inherit it. The selected tokenizer, target length, overlap, heading handling, and text-normalization revision are explicit M5 inputs; they must not drift silently between builds.

## Embedding And Retrieval Compatibility

M2-04 selects no embedding model. M5 must bind every embedding/index set to one compatibility key: chunk-schema and normalization revisions; model ID and checksum/revision; dimension; dtype or quantization; vector normalization; distance metric; locale; and source-manifest SHA-256. A mixed key is invalid. Missing, stale, or incompatible artifacts make the chat abstain; they do not alter ordinary search.

Chat retrieval resolves the active chat locale and admits only chunks in that locale. It is not a
hybrid search path and may be less relevant than ordinary search, but it cannot display a factual
answer without accepted evidence and a resolvable local citation.

## Optional External Evidence

External evidence is disabled by default. A later M7/M8 implementation may use it only after
explicit user opt-in and a reviewed provider/scope policy. Local BPM evidence remains separate and
visible; external pages and provider responses never become local chunks, embeddings, indexes,
training data, or persistent chat knowledge. External claims require their own labelled external
citation and cannot be presented as local BPM documentation.

## Updates, Rebuilds, And Promotion

Published text, topic/anchor identity, manifest membership, locale/version, permitted identifiers, or provenance/review status invalidate affected chunks, embeddings, locale index, and integrity manifest. Chunker or normalization changes trigger a full rebuild of their locale/version scope; any embedding compatibility-key change triggers full re-embedding and re-indexing of that scope.

Chunks, embedding metadata/vectors, retrieval index, and integrity manifest are validated as one candidate set, then promoted atomically. A partial or failed set cannot replace the last known-good set. Future generated artifacts are checksummed and ignored build/install state, never hand-edited or committed as documentation source.

Changing only a chat model, prompt, answer/scope policy, UI copy, or optional web-provider setting does not re-index knowledge automatically. It instead reopens the corresponding answer, security, privacy, web, or UX gate.

## Re-indexing Is Not Training

An ordinary documentation update regenerates affected chunks, embeddings, and retrieval indexes; it does not modify base-model weights. Fine-tuning, LoRA/adapters, and training from documentation, chats, queries, retrieved text, web content, or telemetry are explicitly out of scope for 0.9.3.

Any future training proposal requires a separately approved backlog task, licensed data provenance and retention review, reproducible recipe/evaluation/rollback/supply-chain evidence, and fresh six-locale quality, privacy, security, resource, and release-gate approval. It cannot be smuggled into an index rebuild.

## Ownership And Next Evidence

M5 selects the chunker and embedding model and proves chunk/index compatibility, citation resolution, and atomic rebuild behavior. M6 selects the local runtime/model lifecycle. M7 proves grounded answers and abstention; M8 proves scope, privacy, and access boundaries. Until those tasks complete, this contract is architecture only and BPM093 release gates remain open.
