# BPM 0.9.3 Same-Locale Chat Evidence Retrieval

Date: 2026-07-29

Backlog item: `BPM093-M5-06`

Status: **Implemented retrieval boundary; no chat endpoint or generative model yet.**

## Decision

`app/documentation/retrieval.py` implements `ExactLocaleRetriever`, a fail-closed local reader for
the atomically selected `normalized-exact-f32-matrix-v1` generation. Its caller must already have
an explicit enabled-chat decision and supply one finite, L2-normalized E5-base query vector. The
retriever neither loads nor starts E5-base, exposes HTTP, invokes a language model, creates a
worker, accesses the network, or imports build tooling. Those boundaries remain owned by later
tasks.

The retriever validates the active pointer, generation identifier, root and locale manifests,
selected E5-base checksum/dimension/normalization, matrix and metadata hashes, vector shape and
norms, canonical chunk order, current BPM/documentation version, and structurally local citation
targets before scanning. Any absent, partial, symlinked, corrupt, stale, mixed, incompatible, or
malformed artifact produces a stable unavailable reason. The caller must abstain; it must not
retry another locale, ordinary search, a generated answer, or web evidence.

## Locale, filters, and citations

One request scans exactly one of `en`, `ru`, `de`, `zh-CN`, `fr`, or `es-ES`. It never combines or
falls back across locales. An optional exact guide-id allowlist is applied only after the active
locale has been verified. Exact L2-normalized float32 dot products rank at most five candidates;
equal scores sort by stable `chunk_id` ascending.

Each returned evidence item carries published reviewed text, heading path, guide, current version,
stable chunk identity, and a local citation of the form `topic:<topic-id>` or
`topic:<topic-id>#<anchor>`, with its exact `/help/<locale>/...` URL and `source_kind=local`.
An empty candidate set is an explicit no-evidence outcome for M5-07's abstention/clarification
gate, not an answer or a fallback path.

## Generation compatibility

The generation metadata now includes the current BPM/documentation version plus the reviewed text
and heading path required for later evidence packing. It was rebuilt from the existing verified
2,401-vector cache and atomically activated as `raggen-v1-04855a9c62bd91230356`; the rebuild made
zero network or ordinary-search calls. These ignored local artifacts are runtime inputs only and
are never committed as product source.

The ordinary M4 search remains a separate deterministic browser implementation. It imports neither
this retriever nor the E5 artifact, and it remains available for every retriever result, including
unavailable and no-evidence states.
