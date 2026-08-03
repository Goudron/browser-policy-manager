# BPM 0.9.3 Local Chat Target-Laptop Benchmark

Date: 2026-07-29

Backlog item: `BPM093-M6-03`

Status: **Completed comparative decision; this is not production-release approval.**

## Scope And Boundary

This record compares the M6-01 admitted local chat candidates on the actual x64 target laptop:
Intel Core i5-7200U (two physical cores/four logical threads) with no accelerator. It does not select
a production model, establish grounded-answer quality, or replace BPM's ordinary deterministic
documentation search. Those decisions remain in M6-04 and later tasks.

The measurement runner starts a direct `llama-cli` child only. It uses checksum-verified local
artifacts, `--offline`, `--device none`, Jinja chat templates, non-thinking generation, and stdio
IPC. It starts no listener, server, browser route, external provider, ordinary-search call, or
cross-locale retrieval. There is exactly one active conversation.

## Frozen Workload And Method

M6-02 supplies the candidate-neutral six-locale workload. Each candidate receives the same
reviewed same-locale source-data packet, fixed dialogue turns, generation settings, and a 96-token
maximum. The oracle remains outside the candidate prompt. M6-03 measures generation lifecycle
rather than retrieval relevance; M5 retains the retrieval-quality and active-generation evidence.

The direct CLI uses line-oriented simple I/O. The runner therefore sends exactly one canonical JSON
request line per model turn: instruction, source-data JSON Lines, dialogue turns, and question are
JSON string values, so a newline inside evidence or user content cannot be interpreted as another
CLI turn.

For every locale (`en`, `ru`, `de`, `zh-CN`, `fr`, `es-ES`), the accepted comparative-selection
protocol records one cold first answer, two warm first answers, and one warm dialogue answer. It runs
cancellation/unload once on the target host because that lifecycle behavior is locale-independent.
The runner writes one fsynced raw record per sample, retains interrupted output as a quarantined
partial file, and prints actual stdout progress after every selection sample. It also records start/load, prompt ingestion, time to first token,
decode throughput, complete-answer latency, process-tree RSS, CPU saturation as a percentage of all
four logical CPUs, artifact disk footprint, cancellation, and unload/restart.

The exact E5-base generation and the prepared workload are verified inputs for reproducibility and
footprint accounting. The benchmark never invokes the retrieval engine during a timed chat sample.

If direct `llama-cli` stops printing a prompt after `/clear`, the runner terminates that one session
and creates a sequential replacement. It primes and successfully clears the replacement before the
next warm sample, records the replacement count in raw evidence, and retries this recovery at most
twice. A failed recovery stops only the benchmark attempt; its fsynced raw records stay quarantined.

## Acceptance

Artifact disk at most 2.5 GiB, worker plus retrieval RSS at most 3.5 GiB, cold TTFT at most 30 s,
warm TTFT at most 10 s, complete-answer latency at most 60 s, and decode throughput at least
3 tokens/s are hard ceilings for every observed selection sample. A failure rejects the candidate
regardless of answer style or subsequent quality evidence. Swap movement is recorded before/after
as an operational diagnostic; it is not a release criterion and does not change a result.

## Results

The following table is completed from checksum-linked ignored records. Quality review is required
only for a candidate that passes the resource gate: it cannot overturn a hard rejection.

| Candidate | Cold worst TTFT | Warm worst TTFT | Worst completion | Median throughput | Grounded quality | Peak RSS | Artifact disk | Lifecycle | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3 0.6B Q8_0 | 21.288 s | 33.636 s | 82.781 s | 4.95 cold; 4.75 warm tokens/s | Not run: hard timing gate failed | 1.105 GiB | 1.181 GiB | Cancellation and unload/restart passed | **Fallback selected by the agreed comparison rule; not release-qualified.** Warm TTFT and completion limits failed. |
| Qwen3 1.7B Q8_0 | 52.071 s | Not run | 146.728 s | 1.7 tokens/s | Not run: hard rejection | 2.220 GiB | 1.708 GiB | Cancellation and unload/restart passed | **Rejected early.** Its first comparable English cold sample exceeded cold TTFT, completion, and throughput limits. |

Qwen3 0.6B completed the compact all-six-locale matrix (27 durable records, including the
locale-independent lifecycle records). It passed artifact-size, RSS, and throughput hard gates,
but failed the declared completion ceiling for English, the warm TTFT ceiling for every locale, and
the warm completion ceiling for Chinese and Spanish. Its report is `fail`; its raw-record SHA-256 is
`f6fb50fb153740b7c0f4bb53b8a84443d1024ecc1904a67f23ce46c28a56b6cf` and report SHA-256 is
`b0b252853586e685c77e76da68109fc03b3e885da19f96c396084cb2dafcf71f`.

Qwen3 1.7B passed the lifecycle checks, then its first identical English cold first-answer sample
measured 52.071 s TTFT, 146.728 s completion, and 1.7 tokens/s. Since every observed sample must
meet every hard gate, the candidate was rejected at that point; continuing the remaining
locale/dialogue matrix or conducting a quality review could not change the result. The fsynced
partial-record SHA-256 is `a20afb326cedaee1b6fb3c2b0c63cf1422d07256e18185bec8fdbdcffd244b27`.

The agreed relative-selection rule therefore chooses Qwen3 0.6B Q8_0, because Qwen3 1.7B is not
within the response-time budget. This is a comparative fallback decision only: no candidate meets
all M6-03 timing ceilings, so M6-04 must preserve the no-model/extractive fallback and record the
latency release blocker rather than claim that Qwen3 0.6B is qualified for production release.

The raw records and report are deliberately ignored under `documentation/.cache/bpm093-m6-03/`:
they may contain local paths, prompts, and candidate output and are not product runtime artifacts.
