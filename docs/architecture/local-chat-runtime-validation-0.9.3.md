# BPM 0.9.3 Local Chat Runtime Validation

Backlog item: `BPM093-M6-07`
Status: implemented.

## What This Validation Proves

The selected Qwen3 0.6B Q8_0 worker accepts one UTF-8 structured request for each supported BPM
locale (`en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`). Its locale is copied exactly; there is no
translation, cross-locale retrieval, or English fallback in this layer. The immutable command keeps
Jinja, non-thinking mode, seed `0`, deterministic sampling and the explicit 512-token resource
maximum. It is not a word or paragraph target. The returned
display text must be nonempty UTF-8 and must not contain hidden `<think>` output.

`documentation/tools/run_local_chat_worker_validation_0_9_3.py run` is the one-pass real-artifact
probe. It starts one isolated worker, sends one compact local packet per locale, and emits flushed
stdout progress. Its ignored report contains only per-locale pass/fail, byte/character counts and
SHA-256 digests of output: it contains neither the questions, evidence nor model output. It does not
open a listener or call a network, retrieval, ordinary search, browser route, or web provider.

This is a runtime/transport proof, not a claim that an LLM answer is grounded. M5 accepts only
current citable same-locale evidence within the exact 2,048-token packing budget. M7 will connect
that evidence and validate claims/citations before any response is exposed to a user.

## Bounds And Recovery

The worker rejects unsupported locales, empty or oversized questions, oversized evidence, excess
dialogue, and packets exceeding its byte limit. It does not silently cut evidence because doing so
could break the evidence/citation relationship; M5 performs deterministic evidence selection before
worker invocation. Unit tests cover the command template, UTF-8 serialization, fixed sampling,
long-input rejection, one active request, cancellation, timeout, unload, corrupted/incompatible
artifacts and the no-model/disabled state.

For disabled, not-installed, incompatible, cancelled and crashed conditions, assistant readiness is
false while `lexical_search_ready` remains true. Core BPM readiness and the existing documentation
search remain independent. This task adds no HTTP endpoint, browser control, scope gate, retrieval
call, persistence or external-source capability.

The normative machine-readable contract is
`documentation/config/local-chat-runtime-validation-0.9.3.json`.
