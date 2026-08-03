# BPM 0.9.3 Chat RAG Vector Storage ADR

Date: 2026-07-29

Backlog item: `BPM093-M5-04`

Status: **Accepted for implementation.**

## Decision

BPM selects `normalized-exact-f32-matrix-v1` for the E5-base chat-only retrieval path. Each
activated generation contains one contiguous little-endian float32 matrix per locale, canonical
chunk-order metadata, and a checksummed compatibility/integrity manifest. Vectors are L2-normalized;
retrieval ranks the active locale's vectors by descending dot product, which is cosine ordering for
these vectors.

This is not a database server, daemon, hybrid retrieval path, or replacement for M4 ordinary
search. A chat may scan exactly one active locale; cross-locale merging or fallback is rejected.
The selected storage decision changes neither M4's lexical implementation nor its ranking or
availability.

The exact E5-base decision source is
`documentation/config/chat-rag-embedding-decision-0.9.3.json`, SHA-256
`537e1dc46dc7144987fc2512edda3c27858383b658b63216f5e0ca692cc8eba3`.

## Compared candidates

| Candidate | Result | Reason |
| --- | --- | --- |
| `normalized-exact-f32-matrix-v1` | Selected | Small locale-private corpus, deterministic byte/order control, no new native vector-database extension, and simple generation replacement/recovery. |
| `sqlite-vec` 0.1.10-alpha.4 | Rejected | Correct in the measured cases, but upstream declares it pre-v1 with breaking changes expected. It adds native extension, binding/ABI, database migration, and recovery obligations without a necessary performance or scale gain. |

The sqlite-vec candidate was the exact Linux x86_64 package
`sqlite-vec==0.1.10a4`, wheel SHA-256
`f1897fa54780aaee4ce216091a51193f6383060099325360163550836f803eff`; its loaded `vec0.so`
SHA-256 was `c6cc9fa91c6b69487798bdfb22ca46238d5e83eb227c679040c15edb335a21b5`.
It is dual-licensed MIT/Apache-2.0. The upstream project describes itself as a small vector-search
SQLite extension but explicitly warns that it is pre-v1 and may make breaking changes
([project README](https://github.com/asg017/sqlite-vec), [project site](https://alexgarcia.xyz/sqlite-vec/)).

## Measurement

`run_chat_rag_vector_storage_benchmark_0_9_3.py` generated deterministic 768-dimensional,
float32, L2-normalized vectors. It did not read product prose, a model, an index, or ordinary
search; it made zero network and ordinary-search calls. It measured the current 2,401 chunks and
a 10x 24,010-chunk growth fixture, preserving all six locale partitions and issuing 30 queries per
locale at each scale.

| Scale | Candidate | P95 query latency, maximum locale | Vector/database disk | Ordered Top-5 equality |
| --- | --- | ---: | ---: | --- |
| Current, 2,401 | Exact matrix | 0.801 ms | 7,375,872 bytes | Equal to sqlite-vec for every query |
| Current, 2,401 | sqlite-vec | 8.869 ms | 19,128,320 bytes | Equal to exact for every query |
| 10x, 24,010 | Exact matrix | 13.784 ms | 73,758,720 bytes (0.0687 GiB) | Equal to sqlite-vec for every query |
| 10x, 24,010 | sqlite-vec | 20.141 ms | 85,749,760 bytes (0.0799 GiB) | Equal to exact for every query |

The exact scan stays below the frozen 250-ms retrieval P95 and 0.25-GiB growth vector-artifact
ceilings. This is storage evidence, not an E5-base semantic-quality rerun: M5-03C/M5-03D own model
and clean-host selection evidence.

## Integrity, recovery, and scale boundary

M5-05 must write a complete candidate generation in private staging. It validates each matrix
shape/dtype/hash, locale, canonical chunk order, selected model compatibility key, manifest hash,
and citation targets before atomic promotion. A partial, corrupt, stale, mixed-key, or missing
generation is quarantined; the chat abstains and M4 remains ready. There is no in-place format
migration: a future storage/backend change gets a new compatibility key and a full replacement
generation while the last verified set stays active.

The selected exact-scan boundary covers the current corpus and the 10x fixture only. A future
growth or latency breach does not silently introduce approximate search: it requires a new
benchmark, supply-chain/platform/recovery review, migration plan, and approved backlog decision.

The original M5-03D no-swap gate is superseded by the maintainer resource-policy amendment. Offline
generation may use available RAM and swap. It does not waive the remaining integrity, grounding,
security, interactive-resource, and release gates, and it does not change M4 ordinary search.
