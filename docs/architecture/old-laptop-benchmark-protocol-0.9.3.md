# BPM 0.9.3 Old-Laptop Search And Local-Assistant Benchmark Protocol

Date: 2026-07-28

Backlog item: `BPM093-M2-02`

Status: **Accepted protocol; no candidate result is recorded yet.**

## Purpose And Baseline

This protocol makes search, retrieval, local-inference, cancellation, and unload results comparable before BPM selects an engine, embedding model, chat model, or runtime. It applies to every candidate and the current static-search control. A result omitting a required field, locale, scenario, or raw sample is not a selection result.

The target host is the maintainer baseline: Intel Core i5-7200U, two physical cores/four logical threads, 7.1 GiB RAM, CPU-only. No AVX-512, GPU, NPU, hosted inference, cloud search, account, or network dependency is permitted. The runner records actual CPU model, core count, total/available RAM, swap state, kernel/OS, architecture, storage filesystem/free space, CPU governor where readable, and AC-power state. A nonmatching host may support development diagnostics but cannot close a BPM093 resource gate.

## Frozen Candidate Inputs

Every run records BPM/package/runner/protocol revisions and timestamp; exact search, runtime/model/embedding versions, license, immutable source, SHA-256, quantization, context, threads, and launch flags; corpus/chunk/index schema/source/manifest hashes and byte counts; and fixture revision, query IDs, expected citations/dispositions, 160-token answer limit, seed/sampling parameters, and network-disabled state. Artifacts are explicitly installed beforehand: a measured scenario never downloads a model, updates a dependency, accepts terms, or fetches web evidence. Runs are native on the target host, not a container or VM.

## Corpus And Scenario Matrix

M2-03 supplies the frozen selection corpus: every locale has at least 40 search or retrieval queries and at least 24 answer/dialogue cases. It covers exact IDs, morphology, compounds, accents, aliases, typos, natural questions, Chinese segmentation, multi-topic questions, follow-ups, ambiguity, no-evidence, and off-topic inputs. Every candidate uses the identical fixture revision and source/index snapshot.

| Scenario | Input and measured end point |
| --- | --- |
| Lexical search | Exact ID, natural-language, typo/alias, CJK, and no-result query; submit invocation to rendered result or localized no-result status. |
| Retrieval | In-scope question after scope acceptance; retrieval invocation to final ranked candidates and citations. |
| First answer | Short in-scope question, maximum 160 generated tokens; send invocation to first visible decoded token and final cited completion. |
| Follow-up | One bounded contextual follow-up after a first answer; same 160-token cap and source requirement. |
| Abstain/refuse | No-evidence and off-topic input; disposition, worker-invocation counter, elapsed time, and zero provider calls. |
| Cancellation | Start a 160-token answer, request stop at first token (or one second if absent), then measure request-to-quiescence and retained children/RSS. |
| Unload/restart | Explicit unload, process termination, disabled idle RSS, and the next process-cold startup. |

The report separates exact-ID, retrieval, answer, refusal, and cancellation outcomes. It never hides a failed locale behind a macro average.

## Cold, Warm, And Controlled Conditions

`process-cold` means the relevant worker is stopped, model/index mappings are unloaded, no candidate child exists, and no request has been served since start. It does not drop Linux page cache, require root, or reboot: page-cache state is recorded for a normal local-user measurement. Cold startup is launch request to ready state; cold TTFT uses a fresh process-cold worker for each observation.

`warm` means a worker is ready and has completed one same-locale priming request with its selected index/model loaded. Warm retrieval/generation observations do not restart that worker. Search-only runs are cold/warm only when a candidate has a startup boundary; static browser search records its own documented load state.

Before every candidate block, reboot or record an equivalent clean-session reason; use AC power where available; close browsers, IDEs, sync clients, containers, updates, and nonessential apps; wait five idle minutes; and record one-minute CPU load, available RAM, swap activity, thermal state where readable, and free storage. Use the same scenario order for all candidates, rotating starting locale by candidate block. An observation is invalid only if an external process causes sustained CPU above 10% of all logical CPUs, swap changes, thermal throttling is observable, or the harness records process/network/fixture error. Keep invalid raw records with their reason; do not delete them silently.

## Sampling And Metrics

For each candidate, locale, state, and scenario run five unreported warm-up attempts followed by 30 measured attempts. P95 is nearest-rank 95th percentile of the 30 measurements (rank 29 after ascending sort); median is the midpoint of ranks 15 and 16. Do not mix warm-up/measurement samples or candidate versions.

| Metric | Definition and release ceiling/floor |
| --- | --- |
| Artifact disk | Apparent bytes and SHA-256 of chat/embedding models, runtime, lexical/chunk/vector indexes, and support files; total at most 2.5 GiB. |
| Startup | Monotonic interval from explicit startup request to ready state; excludes installation and corpus build. |
| Lexical render | Submit to browser result/no-result rendered; P95 at most 250 ms. |
| Retrieval | Scope acceptance to final hybrid candidates/citations; warm P95 at most 2 s. |
| TTFT | Answer send to first visible decoded token; warm P95 at most 10 s, process-cold P95 at most 30 s. |
| Throughput | Completion tokens divided by monotonic post-first-token duration; median at least 3 tokens/s. |
| Completion | Answer send to cited completion; P95 at most 60 s. |
| Peak RSS | Every 100 ms, sum `VmRSS` for benchmark-owned worker tree and retain per-process samples; conservative sum at most 3.5 GiB at one active conversation. |
| Cancellation | Stop request to worker quiescence, leaked-child count, post-stop RSS, and successful next request. |
| Unload | Explicit unload to no worker children and disabled-idle RSS, residual mapped files, and next cold-start result. |

Disabled mode is measured in a clean BPM session: it starts no AI worker, maps no model/index, and makes zero network requests after explicit installation. Resource compliance never compensates for a quality, grounding, scope, privacy, or safety failure.

## Harness And Evidence

M3/M6 must add a documented no-network benchmark runner before a candidate can be selected. Until then this required interface is a protocol, not an implemented command:

```text
benchmark-run --protocol BPM093-M2-02 --candidate <immutable-id> --state <process-cold|warm>
              --locale <locale> --scenario <scenario> --fixture <revision> --attempt <n>
```

The runner uses monotonic time, no shell interpolation, explicit browser-render timing where needed, 100-ms process-tree RSS sampling, and outbound-network blocking for local scenarios. It writes one newline-delimited JSON raw record per attempt plus a deterministic summary JSON. Records include host/candidate/input identity, all metrics, fixture/disposition/citation IDs, process IDs, network-call count, validity state, and invalid reason. Reports remain in an ignored benchmark evidence path; only reviewed compact summaries may be cited by later decisions.

Required future checks are M3 engine benchmarks, M5 retrieval, M6 runtime lifecycle/resources, M7 answer quality, M8 scope/privacy, and M13-06 through M13-08 release measurements. A missing harness, raw record, or host fingerprint fails the gate; it cannot be replaced by a manual timing claim.

## Result

This protocol freezes a fair CPU-only method before selection. It selects no engine/model, downloads no artifact, and asserts no resource or quality result.
