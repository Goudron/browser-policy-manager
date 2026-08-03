# BPM 0.9.3 Exact Embedding Generation Contract

Date: 2026-07-29

Backlog item: `BPM093-M5-05`

Status: **Implemented; offline generation may use available host resources.**

## Implemented generation

`generate_chat_rag_exact_generations_0_9_3.py` creates `normalized-exact-f32-matrix-v1` generations
from a reviewed `rag-chunk-v1` manifest and a locally supplied, checksum-verified E5-base artifact.
It has no network client after installation and no ordinary-search call. It does not start a chat
worker or enable RAG.

For each of `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`, the generator sorts the eligible chunks by
stable chunk ID, embeds the exact `passage:` input, and writes a locale-private little-endian
float32 matrix, canonical citation metadata, and a locale manifest. The root manifest carries the
source-manifest hash, storage backend, all locale manifest hashes, and zero network/ordinary-search
calls. The compatibility key binds chunk schema and normalization, exact E5-base model checksum and
dimension, dtype/quantization, vector normalization, metric, locale, source manifest, and storage
backend.

## Activation and recovery

Generation happens in a private sibling staging directory. Every matrix byte count, SHA-256,
shape/dtype, locale, compatibility key, chunk order, metadata file, and locale manifest is verified
before the immutable generation directory is promoted. Only then does an atomic replacement of
`active-generation.json` select it. Symlinks, partial directories, stale/mixed keys, corrupt files,
or an invalid pointer are rejected; chat retrieval must abstain and M4 remains ready.

The ignored incremental cache is keyed by both the full compatibility key and the SHA-256 of the
exact passage input. Its vector bytes, sidecar hash, shape, finite values, and L2 norm are verified
before reuse. Invalid cache entries are re-embedded, never activated as evidence.

## Current host evidence

A fresh checksum-verified E5-base model and the exact 2,401-chunk six-locale manifest were prepared
on the current host. An earlier CPU-only generation was stopped before activation while the host had
approximately 8.8 GiB swap in use; no `active-generation.json` was written and its exact staging
directory was removed. That run remains a historical diagnostic only.

The maintainer resource-policy amendment permits available CPU, RAM, and operating-system swap for
offline vectorization. It does not train E5-base weights. The builder uses all available logical CPU
threads for this non-interactive work. It must still validate a full generation before atomic
activation; a partial local artifact is never accepted. Interactive chat P95/RSS, integrity,
grounding, security, and the remaining release gates stay in force.

## Progress and operator control

The generator writes flushed, real progress to stdout while it runs: verified-runtime preparation,
active locale, completed and total chunks, percentage, verified cache hits, and newly embedded
vectors. It updates at least each five percent and on locale completion; it does not fabricate an
ETA. The separate
`report_chat_rag_exact_generation_progress_0_9_3.py` observer can be used to inspect staging,
cache, activation, and an optional process PID without changing generated artifacts. Neither output
means an incomplete generation is active: only the verified atomic pointer does.
