# BPM 0.9.3 Same-Locale Chat RAG Embedding Benchmark

Date: 2026-07-29

Backlog item: `BPM093-M5-03C`

Status: **E5-base is accepted by the maintainer for implementation.**

## Decision

The C selector returned `fail` with `selected: null`. That factual result remains unchanged: it is
not a benchmark pass. On 2026-07-29, the project maintainer explicitly accepted the exact E5-base
artifact for implementation, based on its passing every measured gate except host swap stability.
The versioned acceptance record is
`documentation/config/chat-rag-embedding-decision-0.9.3.json`. M5-04 and subsequent implementation
work may use only that checksum-pinned artifact. This is not a comparison with the accepted M4
ordinary search: the benchmark made zero ordinary-search calls and does not change it.

`multilingual-e5-base-onnx-o4` passes every measured same-locale evidence, citation, no-evidence,
disk, RSS, and query-latency condition, but both candidate runs changed swap. The clean-host rule is
mandatory, so the result is provisional diagnostic evidence rather than a selectable artifact.
`multilingual-e5-small-onnx-o4` also fails the 0.50 evidence-coverage@5 floor in Russian and
German. It cannot be selected even on a clean host.

## Frozen method

The runner and contract are
`documentation/tools/run_chat_rag_embedding_benchmark_0_9_3.py` and
`documentation/config/chat-rag-embedding-benchmark-0.9.3.json`, SHA-256
`15d0146b5bf380b0710f930c5f769c96508e4cff426d508e1060aed92f8466b3`. It resolves each artifact
through checksum-pinned source contracts, accepts only locally supplied files, disables network
after installation, opens no listener, and runs one candidate per process.

Input is the current `rag-chunk-v1` manifest with 2,401 eligible published chunks: `en` 397, `ru`
424, `de` 434, `zh-CN` 302, `fr` 427, and `es-ES` 417. Manifest SHA-256:
`5d2ce6bedcc2b78dc650e4f48731cbdd641053f46a6d6a5da4f84320744178d0`; source-manifest SHA-256:
`d03d0c680ad27f557ad38d6f07d710f19602811b7536b345ce3025e0a152e852`.

For each active locale, the runner evaluates 16 local answer questions and four local dialogue
answer cases. It never issues a cross-language query. A retrieved chunk is accepted only when its
locale, topic ID, and `/help/{locale}/…` URL resolve. Four local unknown-identifier cases per locale
take the metadata-only `no_evidence` path without embedding or answer generation. No chat model is
run; `answer_generation_invocations`, `ordinary_search_calls`, `cross_locale_retrieval_calls`, and
`network_calls` are all zero in both reports.

The hard floors are per-locale evidence coverage@5 >= 0.50, citation resolution = 1.0,
no-evidence disposition = 1.0, P95 <= 2 seconds, artifact plus direct runtime disk <= 0.75 GiB,
and peak RSS <= 1.5 GiB. A changed swap counter invalidates selection. These retrieval numbers do
not authorize factual generation: M5-07/M7 still own grounding, claim validation, and abstention.

## Immutable candidates and results

| Candidate | en cov@5 / T1 | ru | de | zh-CN | fr | es-ES | Citation / no-evidence | P95 ms | Disk GiB | RSS GiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E5-small O4 | 0.65 / 0.20 | 0.40 / 0.15 | 0.40 / 0.25 | 0.55 / 0.00 | 0.55 / 0.25 | 0.60 / 0.20 | 1.00 / 1.00 | 35.724 | 0.300 | 0.822 |
| E5-base O4 | 0.60 / 0.10 | 0.65 / 0.30 | 0.60 / 0.30 | 0.55 / 0.25 | 0.70 / 0.10 | 0.55 / 0.20 | 1.00 / 1.00 | 181.304 | 0.598 | 1.276 |

E5-small is [`intfloat/multilingual-e5-small` revision
`614241f622f53c4eeff9890bdc4f31cfecc418b3`](https://huggingface.co/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3),
`onnx/model_O4.onnx`, SHA-256 `4654c156f3e4171abc9c716cdb771bf9116455d15ac1aab364aeeede0e3205b0`.
E5-base is [`intfloat/multilingual-e5-base` revision
`f5bd48cd75e61ca79c4cdffff9185cab1f07f4f0`](https://huggingface.co/intfloat/multilingual-e5-base/tree/f5bd48cd75e61ca79c4cdffff9185cab1f07f4f0),
`onnx/model_O4.onnx`, SHA-256 `f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703`.
Both use MIT-licensed artifacts, `query: ` / `passage: ` prefixes, attention-mask mean pooling, and
L2 normalization.

## Validity and re-entry

The host swap counters changed from `7840612352` to `8386805760` bytes for E5-small and from
`7942135808` to `8639713280` bytes for E5-base. The reports are therefore invalid for final
selection regardless of their diagnostic metrics. Raw reports remain ignored artifacts.

The original no-swap condition is superseded for selection and release by the explicit maintainer
resource-policy amendment. It remains historical diagnostic evidence only. Offline documentation
embedding/index construction may use available RAM and operating-system swap; it is not model
training. Interactive chat retrieval remains constrained by the measured P95/RSS ceilings, and M4
ordinary search remains unchanged.

## M5-03D attempt after reboot

The first D attempt was made on 2026-07-29 after a host reboot, using a fresh checksum-verified
E5-base artifact/runtime and a freshly generated 2,401-chunk manifest with the same source hash.
Swap was already non-zero at the baseline (`4,941,529,088` bytes) and changed to
`5,942,845,440` bytes within approximately 45 seconds. The no-swap hard gate had therefore failed
before valid quality/resource evidence could be collected, and the CPU-only process was stopped.
No partial report is represented as a passing selection. The versioned record is
`documentation/config/chat-rag-clean-host-validation-0.9.3.json`; it confirms zero network,
ordinary-search, cross-locale, and answer-generation calls. Under the later resource-policy
amendment, this failure is an operational diagnostic rather than a release blocker.
