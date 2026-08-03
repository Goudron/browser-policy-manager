# BPM 0.9.3 Active Chat-RAG Retrieval Validation

Date: 2026-07-29

Backlog item: `BPM093-M5-08`

Status: **Implemented; the active E5-base generation passes its retrieval, coverage, integrity, reproducibility, resource, and isolation checks.**

## Decision

`run_chat_rag_retrieval_validation_0_9_3.py` drives the production
`app.documentation.retrieval.ExactLocaleRetriever` using the checksum-selected local E5-base ONNX
encoder. It validates the active pointer and exact-generation manifests before measurement, then
compares the active metadata byte-for-byte with the reviewed current chunk manifest. It is an
offline documentation tool, not an application import or a chat endpoint.

The runner evaluates only the active user locale, retains only local `/help/<locale>/` citations,
and repeats each retrieval with the same vector to prove stable candidate order, scores, and
citations. It uses the accepted 20 answer/dialogue cases and four technical-identifier
no-evidence cases per locale. A no-evidence case is stopped before E5 encoding or retrieval when
its identifier is absent from that locale's active reviewed metadata.

The command has flushed stdout phases for contract/generation verification, every five evaluated
questions per locale, and every five latency samples. Its report is restricted to ignored
`documentation/.cache/bpm093-m5-08/`; no generated report or model artifact becomes source.

## Active Evidence

The validated generation is `raggen-v1-04855a9c62bd91230356`, built from source manifest
`d03d0c680ad27f557ad38d6f07d710f19602811b7536b345ce3025e0a152e852` and 2,401 approved chunks.
Every locale has exact chunk and topic coverage, with 155 current publishable topics in each
locale:

| Locale | Chunks | Evidence coverage@5 | Citation/no-evidence/reproducibility |
| --- | ---: | ---: | --- |
| `en` | 397 | 0.60 | 1.00 / 1.00 / 1.00 |
| `ru` | 424 | 0.60 | 1.00 / 1.00 / 1.00 |
| `de` | 434 | 0.55 | 1.00 / 1.00 / 1.00 |
| `zh-CN` | 302 | 0.50 | 1.00 / 1.00 / 1.00 |
| `fr` | 427 | 0.60 | 1.00 / 1.00 / 1.00 |
| `es-ES` | 417 | 0.55 | 1.00 / 1.00 / 1.00 |

The 30-sample warm P95 for E5 query encoding plus verified same-locale exact retrieval was at
most **325.24 ms**, below the 2,000 ms ceiling. Peak process RSS was **1.045 GiB**, below the
1.5 GiB ceiling. Model plus direct runtime was **0.598 GiB** and the active generation was
**0.011 GiB**, below their respective 0.75 GiB and 0.25 GiB ceilings. The host swap counter
increased by 766,496,768 bytes during this run; under the accepted resource-policy amendment this
is recorded diagnostic data, not a validity or release condition.

The report records zero network, ordinary-search, cross-locale retrieval, and answer-generation
calls. It does not compare chat retrieval against M4: RAG is a separate chat-only evidence path
and M4 remains the authoritative ordinary documentation search.

## Integrity And Recovery

The validation runner rejects a pointer whose root manifest differs, a generation that does not
derive from the current source manifest, metadata that does not exactly preserve published reviewed
chunks, incomplete locale/topic coverage, stale input chunks, or a changed checksum-pinned
contract/corpus. The production retriever independently verifies matrix byte size, hash, shape,
normalization, current version, reviewed provenance, metadata hash/order, and local citation shape
for every retrieval.

Focused runtime tests cover stale, corrupted, malformed, unreviewed, and no-evidence artifacts,
and evidence packing refuses stale, contradictory, unadmitted, or empty inputs. Their recovery is
chat abstention only: no ordinary-search fallback, M4 mutation, M4 import, or loss of M4
availability is permitted.

## Re-run Boundary

Use a verified local E5-base directory, its verified offline ONNX/tokenizer runtime, the current
reviewed chunk manifest, and the active generation root. For example:

```bash
PYTHONPATH=<verified-offline-runtime> .venv/bin/python \
  documentation/tools/run_chat_rag_retrieval_validation_0_9_3.py \
  --index-root documentation/.cache/bpm093-m5-05 \
  --model-dir <verified-e5-base-directory> \
  --chunks <current-reviewed-chunks.json> \
  --output documentation/.cache/bpm093-m5-08/retrieval-validation.json
```

Any DITA/chunk, locale, E5 artifact, exact-generation format, retrieval code, evidence contract,
runtime, or resource-ceiling change invalidates this evidence and requires a fresh run plus the
focused corruption/stale tests.
