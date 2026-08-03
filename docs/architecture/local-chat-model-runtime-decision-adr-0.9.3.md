# BPM 0.9.3 Local Chat Model And Runtime Decision ADR

Date: 2026-07-30

Backlog item: `BPM093-M6-04`

Status: **Qwen3 0.6B selected under the accepted best-effort latency policy.**

## Decision

`llama.cpp` `b9637` (`aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3`, MIT) remains the
only admitted local inference runtime. Its permitted boundary is an owner-managed direct child
process using stdio and `--offline`; `llama-server`, HTTP/TCP listeners, LAN binding, public model
APIs, tools, plugins, and function calling remain forbidden.

The M6-03 comparative rule selects `Qwen3-0.6B-Q8_0` as the lighter fallback candidate. It uses
the immutable official Apache-2.0 artifact
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`, the model's Jinja chat
template, and non-thinking mode. It is the only model eligible for later explicit opt-in
installation. This ADR still installs nothing and starts no worker or chat endpoint.

`Qwen3-1.7B-Q8_0` is rejected. Its official Apache-2.0 artifact is
`061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`.

The exact decision data, pins, and contract test are in
`documentation/config/local-chat-model-runtime-decision-0.9.3.json`.

## Measured Trade-Off

The selected fallback completed the compact M6-03 matrix for `en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`, including cancellation and unload/restart. It stayed within its artifact/RSS/throughput
gates, but its 33.636-second worst warm TTFT and 82.781-second worst completion breached the
10-second and 60-second limits. Its result is therefore `fail`, not an accepted performance pass.

The larger candidate passed the locale-independent lifecycle checks but its first identical English
cold first-answer sample measured 52.071 seconds TTFT, 146.728 seconds completion, and 1.7 tokens
per second. Those values breach three hard gates, so the remaining locale/dialogue matrix and
quality review were correctly not run: neither could overturn the rejection.

| Candidate | Comparative outcome | Release outcome |
| --- | --- | --- |
| Qwen3 0.6B Q8_0 | Lighter fallback after 1.7B rejection | Selected under M6-04A best-effort policy; timing values remain disclosed. |
| Qwen3 1.7B Q8_0 | Rejected at first comparable cold sample | Not eligible for quality comparison or release. |

The raw 0.6B matrix SHA-256 is
`f6fb50fb153740b7c0f4bb53b8a84443d1024ecc1904a67f23ce46c28a56b6cf`; its report SHA-256 is
`b0b252853586e685c77e76da68109fc03b3e885da19f96c396084cb2dafcf71f`. The 1.7B fsynced partial
record SHA-256 is `a20afb326cedaee1b6fb3c2b0c63cf1422d07256e18185bec8fdbdcffd244b27`.

## Fixed Inference Profile

The comparison profile is four inference and batch threads, 4,096 context tokens, batch size 512,
micro-batch size 128, a 160-token answer cap, temperature `0`, top-p `1`, top-k `1`, seed `0`,
the immutable Jinja template, and `/no_think`. The M12A release hardening reduces only the shipped
cap to 96 tokens after a target-host timeout; the historical comparison remains intact. It is not a
license to silently change context, quantization, or runtime flags to bypass the measured decision.

The output boundary must never display hidden reasoning, thought tags, raw template text, or other
non-display-safe model output. The model receives bounded evidence as data; it does not acquire BPM
facts, authorization, tools, files, processes, product APIs, or network access.

## Retrieval And Search Boundary

E5-base (`multilingual-e5-base-onnx-o4`, MIT) remains the accepted retrieval embedding decision.
It supplies only chat RAG: a normalized exact float32 scan of published chunks in the active user
locale. The chat model does not replace or improve ordinary search.

The deterministic BPM documentation search remains independent: it does not call RAG, embeddings,
a local model, or optional external search. Cross-locale retrieval is forbidden. External evidence
is disabled by default and, when later approved, must remain labelled and outside local chunks,
embeddings, indexes, and persistent knowledge.

## M6-04A Performance Policy And Fallback

The project maintainer selected M6-04A branch 2 on 2026-07-30: BPM accepts the measured Qwen3 0.6B
profile without a repeat benchmark. The M6-03 cold/warm TTFT, completion, and throughput limits are
therefore superseded only for this exact Qwen3 0.6B Q8_0, `llama.cpp` b9637, CPU-only profile.
Artifact disk, RSS, single-conversation, offline, verified-artifact, same-locale citation, search
independence, and all security/privacy/fallback requirements remain hard requirements.

The product promise is best effort local chat. BPM does not promise a target-laptop time to first
token or complete-answer deadline; it must disclose local CPU processing, remain non-blocking, and
provide cancellation when M6-06 adds the worker. The M6-03 failed timings remain historical facts:
the policy does not relabel the benchmark as passed. Qwen3 1.7B stays rejected, and the amendment
does not authorize a different model, quantization, runtime, or host scope.

No repeat benchmark is required for this decision. M6-05 may now implement an explicit verified
installation flow for the named 0.6B artifact. It still may not auto-download or auto-start it;
M6-06 separately owns the worker and chat route. Until the model is explicitly installed and
enabled, deterministic search and normal `/help/` navigation remain the no-model fallback. A future
extractive fallback may be added only with same-locale published citations and fail-closed behavior.

## Consequences

- M6-05 may implement only explicit verified installation of the pinned Qwen3 0.6B artifact; it
  must disclose the best-effort local-CPU policy and preserve removal/offline behavior.
- M6-06 owns worker activation and bounded lifecycle only. M7/M8 later own the controller/chat
  route, while M6-07 owns six-locale runtime behavior and output safety; this decision implements
  none of them.
- No model is trained on BPM documentation. RAG grounds generated answers through retrieved
  evidence and citations when a future approved runtime exists.
- The historical latency failure is not a reason to weaken ordinary search, retrieve across locales,
  silently access the web, or substitute an unpinned candidate.
