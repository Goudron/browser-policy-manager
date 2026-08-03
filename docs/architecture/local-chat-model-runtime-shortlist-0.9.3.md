# BPM 0.9.3 Local Chat Model And Runtime Shortlist

Date: 2026-07-29

Backlog item: `BPM093-M6-01`

Status: **Benchmark shortlist only; no model or runtime is selected, installed, started, or shipped.**

## Decision

M6 evaluates exactly one CPU runtime family: `llama.cpp` release `b9637`, pinned to commit
`aedb2a5e9ca3d4064148bbb919e0ddc0c1b70ab3`. The official Ubuntu x64 CPU archive has the published
SHA-256 `a50ee14f021a9d8e92e30f622f7e3be1318ee1125bb9a9ba8d2025388df48743` and the runtime is MIT
licensed. This admission is limited to an owner-managed child process with pipe/stdio IPC; it does
not permit `llama-server`, HTTP/TCP, LAN binding, a public model API, plugins, tools, or function
calling.

Two official Qwen GGUF artifacts are admitted for comparison. Both are Apache-2.0, Q8_0, have a
32,768-token upstream context, use the upstream Jinja chat template, and claim multilingual
instruction support. Their multilingual claim admits them to measurement only: the reviewed BPM
six-locale corpus must still prove quality independently in `en`, `ru`, `de`, `zh-CN`, `fr`, and
`es-ES`, without cross-locale fallback.

| Candidate | Immutable artifact | Size | Role |
| --- | --- | ---: | --- |
| `Qwen3-0.6B-Q8_0` | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` | 639,446,688 B | Smallest resource control. |
| `Qwen3-1.7B-Q8_0` | `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a` | 1,834,426,016 B | Larger answer-quality control. |

The benchmark uses Qwen non-thinking mode (`/no_think`). A later output boundary must suppress or
reject thought tags, hidden reasoning, raw template output, and any other non-display-safe model
content. The model does not acquire BPM facts, scope authority, tool access, files, processes, or
network access through this shortlist.

## Excluded Candidate

`google/gemma-3-1b-it` is deliberately **not** admitted. Google’s model card reports useful
multilingual scope and a 32K context for the 1B model, but the upstream Hugging Face repository is
manually gated under Gemma Terms of Use and does not provide an accepted upstream GGUF artifact for
this runtime. The terms impose redistribution obligations. No unofficial conversion may enter the
benchmark until a separate review establishes its source, conversion procedure, immutable hash,
license/redistribution compliance, and maintainer acceptance.

## Boundaries For The Next Tasks

M6-02 supplies the identical retrieved evidence, fixed dialogue turns and structured prompt to
each admitted candidate. M6-03 runs the old-laptop protocol on the actual i5-7200U: cold/warm
load, time to first token, throughput, complete answer, RSS, disk, cancellation, unload, and all
six locales. Every run remains local and offline after explicit verified artifact installation.

Only one chat model may be installed or mapped for a measured run, alongside E5-base, the active
retrieval generation and their direct runtime. The total 2.5 GiB artifact and 3.5 GiB worker plus
retrieval RSS ceilings remain hard gates. A missing source, revision, checksum, license/terms,
template, format, target compatibility, security condition, or locale result rejects the candidate;
there is no fallback to an unpinned model.

## Primary Sources Reviewed

- [llama.cpp b9637 release](https://github.com/ggml-org/llama.cpp/releases/tag/b9637) and its
  [MIT license](https://github.com/ggml-org/llama.cpp/blob/b9637/LICENSE).
- [Official Qwen3 0.6B GGUF card](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF) and
  [official Qwen3 1.7B GGUF card](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF).
- [Gemma 3 model card](https://ai.google.dev/gemma/docs/core/model_card_3) and
  [Gemma Terms of Use](https://ai.google.dev/gemma/terms).

The exact upstream revisions, artifact source URLs, checksums, sizes, terms and admission status
are machine-readable in `documentation/config/local-chat-model-runtime-shortlist-0.9.3.json`.
