# BPM 0.9.3 Embedding-Model Remediation Benchmark

Date: 2026-07-29

Backlog item: `BPM093-M5-03A`

Status: **Rejected — no embedding artifact is selected.**

## Decision

The expanded shortlist does not unblock vector-storage selection. The reproducible selection report
is `fail` with `selected: null`: neither candidate satisfies the six-locale retrieval gates, and
both measurements are invalid for final acceptance because the host swap counter changed. BPM must
not install either model as a product artifact, generate embedding indexes, or begin M5-04 from
this result. The selected deterministic documentation search remains fully independent and
available.

The quality failure is conclusive for this shortlist even without a clean-host rerun: every
candidate misses the per-locale quality floor and the cross-language floor. A clean-host rerun
could only remove the additional swap rejection; it could not turn the recorded scores into a
passing selection.

## Method and scope

The versioned contract is
`documentation/config/embedding-model-benchmark-m5-03a-0.9.3.json`, SHA-256
`432cc2f7cd82f6f929f5316ff597bdfc009095b2823cb1ac29b55e79955167f8`. It reuses the M5-03
published `rag-chunk-v1` input: 2,401 eligible chunks (`en` 397, `ru` 424, `de` 434, `zh-CN`
302, `fr` 427, `es-ES` 417), manifest SHA-256
`5d2ce6bedcc2b78dc650e4f48731cbdd641053f46a6d6a5da4f84320744178d0`, and 96 reviewed retrieval
questions (16 per locale). English answer questions are also evaluated against each locale index.

The runner is offline after explicit local artifact installation, performs no network calls, and
runs one candidate per process. It uses two ONNX intra-op threads and one inter-op thread, a
512-token maximum, attention-mask mean pooling, L2 normalization, topic deduplication before
Top-5, five warm-ups, 30 measured query attempts per locale, and 100-ms RSS sampling. It now
supplies only the ONNX inputs required by each model and, where declared, applies the model's
checksum-pinned post-pooling layer before normalization. In particular, DistilUSE uses its required
768-to-512 Dense+Tanh projection rather than an incompatible mean-pooled transformer output.

The retrieval gates remain Top-1 >= 0.70 and Recall@5 >= 0.90 in *each* locale, cross-language
Recall@5 >= 0.75, and P95 <= 2 s. Peak RSS remains <= 1.5 GiB. The remediation contract allocates
0.75 GiB, rather than the earlier 0.50 GiB, to the embedding artifact plus direct benchmark
runtime. This is an explicit component-budget correction that admits a 0.60-GiB retrieval encoder
for evaluation; it neither changes the quality gates nor relaxes the 2.5-GiB complete-assistant
release ceiling. No artifact is selected under that corrected allocation.

## Immutable candidates

| Candidate | Immutable source and artifact | Runtime rule |
| --- | --- | --- |
| `multilingual-e5-base-onnx-o4` | [`intfloat/multilingual-e5-base` revision `f5bd48cd75e61ca79c4cdffff9185cab1f07f4f0`](https://huggingface.co/intfloat/multilingual-e5-base/tree/f5bd48cd75e61ca79c4cdffff9185cab1f07f4f0), `onnx/model_O4.onnx`, SHA-256 `f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703` | MIT; 768 dimensions; generic CPU; `query: ` and `passage: ` prefixes. |
| `distiluse-base-multilingual-cased-v2-onnx-quint8-avx2` | [`sentence-transformers/distiluse-base-multilingual-cased-v2` revision `76a1ba57cb3d655b5196538484e0cfa9370317e4`](https://huggingface.co/sentence-transformers/distiluse-base-multilingual-cased-v2/tree/76a1ba57cb3d655b5196538484e0cfa9370317e4), `onnx/model_quint8_avx2.onnx`, SHA-256 `6a5852e0da9ca0e4532274b6c5eed71f9938fa8ff15e8345c6873a1969093f80` | Apache-2.0; AVX2 INT8; 512-dimensional post-projection; no prefixes. |

The diagnostic runtime pins ONNX Runtime 1.28.0, tokenizers 0.23.1, and safetensors 0.8.0 by wheel
checksum. It is benchmark tooling only, not a selected BPM runtime.

## Results

| Candidate | en T1 / R@5 | ru | de | zh-CN | fr | es-ES | Cross R@5 | P95 ms | Disk GiB | RSS GiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E5-base O4 | 0.125 / 0.750 | 0.375 / 0.812 | 0.375 / 0.688 | 0.312 / 0.625 | 0.125 / 0.812 | 0.250 / 0.688 | 0.740 | 123.839 | 0.598 | 1.367 |
| DistilUSE INT8 AVX2 | 0.188 / 0.562 | 0.312 / 0.750 | 0.125 / 0.375 | 0.125 / 0.375 | 0.062 / 0.500 | 0.188 / 0.438 | 0.583 | 93.927 | 0.195 | 0.799 |

Both candidates meet the component disk, memory, and query-latency limits. E5-base is more
relevant than DistilUSE, but it still fails both local metrics in every locale and misses the
cross-language floor. DistilUSE likewise fails both local metrics in every locale and the
cross-language floor. There is no macro-average, locale exception, or resource-only promotion.

## Validity and next gate

Swap changed during each measurement, so both reports are invalid for a final hardware acceptance:
E5-base changed from `7004344320` to `8701390848` bytes and DistilUSE from `7822442496` to
`8589799424` bytes. These changes are recorded rather than hidden; the quality and resource values
are diagnostic evidence only. The raw JSON reports remain ignored benchmark output.

`BPM093-M5-03B` first freezes the contract for same-locale, chat-only evidence retrieval;
`BPM093-M5-03C` then benchmarks candidates under it. Neither task calls, replaces, or compares
against the accepted M4 ordinary search, and neither evaluates cross-locale retrieval. The
maintainer has subsequently accepted E5-base for implementation under the separate versioned
decision record; M5-04 may proceed. Clean-host resource evidence, checksum/license provenance,
citation/abstention evidence, and proof that ordinary search is unaffected remain mandatory before
RAG can be enabled or packaged. Optional external evidence is a later opt-in path and never enters
the local vector corpus.
