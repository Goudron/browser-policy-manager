# BPM 0.9.3 Local AI Pre-Implementation Guards

Date: 2026-07-28

Backlog item: `BPM093-M2-07`

Status: **Accepted contract guards; they validate planned inputs and do not implement an AI runtime.**

## Decision

`documentation/config/local-ai-preimplementation-guards-0.9.3.json` binds the accepted
six-locale evaluation corpus, RAG knowledge/update contract, security/privacy contract, and
availability/fallback contract into focused negative checks. Its test is
`documentation/tests/contract/test_local_ai_preimplementation_guards_0_9_3.py`.

The locale corpus is now accepted: the project maintainer's interactive acceptance on 2026-07-28 is
recorded for `en`, `ru`, `de`, `zh-CN`, `fr`, and `es-ES`. This is review evidence for using the
fixtures in later evaluation runners; it is not a result from those runners or a release-quality
claim.

## Guarded Rejections

| Guard | Rejected before implementation proceeds |
| --- | --- |
| Chunk identity | Missing `rag-chunk-v1`, required version/provenance/hash metadata, locale, or deterministic `ragc-v1` ID. |
| Locale evidence | Draft/missing/extra/cross-locale corpus review evidence. |
| Artifact ownership | Generated chunks, vectors, indexes, models, caches, reports, or conversations treated as committed source or incomplete manifest set. |
| Resources | More than 2.5 GiB artifacts, 3.5 GiB worker/retrieval RSS, one active generation, or one queued generation. |
| Startup/network | Model start without explicit install/verified artifacts/enablement; local-mode network request; implicit startup trigger; TCP/HTTP/LAN/public listener. |
| Assistant capability | Any callable model tool, BPM mutation/API access, shell/process/file/URL capability, plugin, MCP, or code interpreter. |
| Grounding | `answer` disposition without current resolved citation ID, published URL, and allowed source kind. |
| Availability | Unknown/unsupported state transition, false ready with partial artifacts, or lexical search depending on AI. |

## Execution Boundary

The guards use compact synthetic dicts to prove that an invalid contract input raises
`GuardViolation`. They do not start a model, create a route, download a file, call a network,
allocate a worker, run browser automation, or replace runtime validation. M5-M11 must turn each
guard into implementation-level evidence while preserving these failure rules.

## Result

The accepted M2 contracts now have an executable pre-implementation boundary. A future change that
weakens source provenance, locale review, artifact integrity, resource ceiling, no-network default,
tool prohibition, citations, state transition, or lexical fallback fails a focused test before a
local assistant can be claimed ready.
