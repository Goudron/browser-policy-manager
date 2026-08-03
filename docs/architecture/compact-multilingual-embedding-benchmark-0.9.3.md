# BPM 0.9.3 Compact Multilingual Embedding Benchmark

Date: 2026-07-29

Backlog item: `BPM093-M5-03`

Status: **Rejected — no embedding model or artifact is selected.**

## Decision

Neither tested artifact satisfies the versioned six-locale retrieval gates. The selection summary is
`fail` with `selected: null`; BPM must not install either artifact, create embeddings, start a
worker, or proceed to vector-storage selection on its basis. The deterministic BPM documentation
search selected in M4 remains independent and fully available.

The evidence-gathering part of `BPM093-M5-03` is complete. Its selection acceptance is not met, so
`BPM093-M5-03A` is inserted before M5-04 to expand the shortlist and repeat this exact gate.

## Frozen Method

`documentation/tools/run_embedding_model_benchmark_0_9_3.py` implements
`documentation/config/embedding-model-benchmark-0.9.3.json`. It accepts only locally supplied,
checksum-verified files, sets offline environment guards, opens no listener, and records zero
network calls. Each candidate has a separate process so one ONNX allocator cannot inflate another
candidate's RSS.

Input was the canonical `rag-chunk-v1` manifest with 2,401 eligible published chunks: `en` 397,
`ru` 424, `de` 434, `zh-CN` 302, `fr` 427, and `es-ES` 417. Manifest SHA-256:
`5d2ce6bedcc2b78dc650e4f48731cbdd641053f46a6d6a5da4f84320744178d0`; source-manifest SHA-256:
`d03d0c680ad27f557ad38d6f07d710f19602811b7536b345ce3025e0a152e852`.

The runner expands reviewed answer templates to 16 independent retrieval questions per locale. It
embeds a locale's heading path plus chunk text, deduplicates chunks by topic before Top-5, and
evaluates English questions against all six locale indexes for cross-language Recall@5. Exact IDs
remain a lexical/hybrid requirement for M5-06, not an unsupported dense-only claim.

Every candidate uses attention-mask mean pooling followed by L2 normalization; cosine ordering is
the dot product of normalized vectors. The target is the i5-7200U, two-core/four-thread, 7.1 GiB
CPU-only baseline. ONNX Runtime uses two intra-op and one inter-op thread. Query P95 has five
warm-ups and 30 measured attempts per locale; RSS is sampled every 100 ms. A changing global swap
counter invalidates a run, as required by `BPM093-M2-02`.

Gates are per-locale Top-1 at least 0.70, Recall@5 at least 0.90, cross-language Recall@5 at least
0.75, query P95 at most 2 s, model plus direct runtime disk at most 0.5 GiB, and peak RSS at most
1.5 GiB. The disk/RSS gates are M5 embedding-component reserves, not a claim that the full future
assistant has passed the M6/M13 release ceilings.

## Immutable Candidates

| Candidate | Source and artifact | License / runtime | Input rule |
| --- | --- | --- | --- |
| `multilingual-e5-small-onnx-o4` | [`intfloat/multilingual-e5-small` revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`](https://huggingface.co/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3); `onnx/model_O4.onnx`, SHA-256 `4654c156f3e4171abc9c716cdb771bf9116455d15ac1aab364aeeede0e3205b0` | MIT; 384 dimensions; ONNX O4 float; generic CPU | `query: ` and `passage: ` prefixes. |
| `paraphrase-multilingual-minilm-l12-v2-onnx-quint8-avx2` | [`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/tree/e8f8c211226b894fcb81acc59f3b34ba3efd5f42); `onnx/model_quint8_avx2.onnx`, SHA-256 `98a01d88b7de996cdea58c32ca71208c09968d143798814b2ea09d3439dc334f` | Apache-2.0; 384 dimensions; INT8 AVX2 | No prefix; target CPU supports AVX2. |

Both used checksum-pinned `onnxruntime` 1.28.0 and `tokenizers` 0.23.1. This establishes a Linux
x86_64 CPU diagnostic runtime only; it does not select BPM's product runtime.

## Results

| Candidate | en Top-1 / R@5 | ru | de | zh-CN | fr | es-ES | Cross R@5 | P95 ms | Disk GiB | RSS GiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E5 ONNX O4 | 0.250 / 0.812 | 0.188 / 0.500 | 0.312 / 0.500 | 0.000 / 0.688 | 0.312 / 0.688 | 0.250 / 0.750 | 0.708 | 27.032 | 0.300 | 0.968 |
| MiniLM INT8 AVX2 | 0.062 / 0.500 | 0.375 / 0.562 | 0.000 / 0.375 | 0.062 / 0.250 | 0.250 / 0.438 | 0.188 / 0.500 | 0.479 | 22.869 | 0.184 | 1.014 |

Both candidates meet measured disk, RSS, and query-latency component gates. E5 is materially more
relevant than MiniLM but fails per-locale quality in all six locales and the cross-language floor.
MiniLM fails all quality gates and is not a resource-based substitute. There is no macro-average or
German/Chinese exception.

The precise global swap counters changed during both runs (E5: `6650273792` to `6698655744` bytes;
MiniLM: `6698336256` to `6698700800` bytes). Resource/quality values are diagnostics, but the
accepted protocol invalidates both runs for final selection independently of their quality failures.

## Re-entry

`BPM093-M5-03A` must nominate at least two new maintained, compact, immutable multilingual
artifacts and repeat this corpus, prefix/normalization, quality, resource, and clean-host evidence.
It may not weaken a locale gate, substitute a macro average, accept swap activity, or promote E5 or
MiniLM from this report. Only one passing exact artifact can unblock M5-04 and later RAG work.
